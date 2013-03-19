from bs4 import BeautifulSoup
import config
import httplib
import re
import requests
import urllib
import urlparse


def extract_sort_criterion(criterion_id):
  cid = criterion_id
  match = re.search('__([a-z]*)_', cid)
  if match:
    return match.group(1)
  else:
    msg = 'Unable to find sort criterion in string "%s"' % cid
    raise ValueError, msg

def strip_plone_suffix(url):
  """Return URL with any Plone-specific suffixes removed."""
  suffixes = ['/document_view', '/download', '/folder_contents',
              '/image_large', '/image_preview',
              '/image_mini', '/image_thumb', '/image_tile',
              '/image_icon', '/image_listing', '/view']
  # First strip off a trailing slash if it's there.
  if url[-1] == '/':
    url = url[:-1]

  for s in suffixes:
    if url[len(s) * -1:] == s:

      return url[:len(s) * -1]

  # If we make it down here, return the URL as-is.
  return url

class HTTPError(Exception):
  pass

class AuthRequiredError(HTTPError):
  pass

class BadRequestError(HTTPError):
  pass

class NotFoundError(HTTPError):
  pass

class OffsiteError(HTTPError):
  pass

class RemoteResource:
  http_requests = {}

  def __str__(self):
    if isinstance(self, RemoteObject):
      return "RemoteObject at %s" % self.absolute_url
    elif isinstance(self, RemoteLinkTarget):
      return "RemoteLinkTarget at %s" % self.link
    else:
      return "unknown RemoteResource object"


  def get_site(self):
    return urlparse.urlparse(self.absolute_url).netloc


  def log_in(self, auth_url):
    """Authenticates within the current HTTP session. Returns
       nothing (works by side effect)."""
    # TODO: Determine if all of these parameters are necessary.
    payload = {'__ac_name': config.username,
               '__ac_password': config.password,
               'came_from': '',
               'cookies_enabled': '',
               'form.submitted': 1,
               'js_enabled': 0,
               'login_name': '',
               'pwd_empty': 0,
               'submit': 'Log in'}
    auth_r = self.session.post(auth_url, payload, verify=False)
    return None


  def make_http_request(self, suffix="", method="GET"):
    # Validate the method.  GET and POST currently supported.
    if method.upper() not in ['GET', 'POST']:
      raise ValueError, 'Unsupported method "%s"' % method

    request_url = "%s/%s" % (self.absolute_url, suffix)

    # Check whether we've already made this request. If so, use the
    # result we got last time instead of making it again.
    if request_url not in RemoteResource.http_requests:
      try:
        r = self.session.request(method, request_url, verify=False)
      except requests.TooManyRedirects:
        print "TooManyRedirects raised while trying to access %s" % request_url
        import pdb; pdb.set_trace()

      # If the site has redirected us to the login page, log in
      # using credentials stored in the config module. Also force
      # login for the sitemap on the staff site.
      if ('require_login' in r.url or
          request_url == 'https://staff.dm.org/sitemap/CookedBody'):
        self.log_in("https://%s/login_form" % self.get_site())
        r = self.session.request(method, request_url, verify=False)
      if r.status_code == 404:
        msg = "Server returned error status %s attempting to load URL %s" % (r.status_code, r.url)
        raise NotFoundError, msg
      elif r.status_code == 400:
        msg = "Server returned error status %s" % r.status_code
        raise BadRequestError, msg
      elif r.status_code >= 300:
        msg = "Server returned error status %s" % r.status_code
        import pdb; pdb.set_trace()
        raise HTTPError, msg

      RemoteResource.http_requests[request_url] = r.content
      return r.content
    else:
      return RemoteResource.http_requests[request_url]




  def is_valid_url(self, url):
    parse_result = urlparse.urlparse(url)
    if parse_result.netloc == '':
      return False
    if parse_result.scheme[:4] != 'http':
      return False
    return True


class RemoteLinkTarget(RemoteResource):
  """Represents a link we've found on the remote site."""

  def __init__(self, site, base_url, link, session = None):
    self.site = site
    self.link = link
    full_url = urlparse.urljoin(base_url, link, allow_fragments=False)
    if session:
      self.session = session
    else:
      self.session = requests.Session()

    # Filter the URL we've constructed to remove any Plone-specific
    # suffixes.
    full_url = strip_plone_suffix(full_url)

    # Check whether this is an offsite link.
    netloc = urlparse.urlparse(link).netloc 
    if netloc and (netloc != site):
      msg = "Resource %s not part of site %s" % (link, site)
      raise OffsiteError, msg

    # Set the absolute URL to the linked URL as a first
    # approximation. (It needs to be set to something in order
    # to call make_http_request to look up the real absolute_url.
    self.absolute_url = full_url
    self.absolute_url = self.make_http_request('absolute_url')

    if not self.is_valid_url(self.absolute_url):
      raise ValueError, "Invalid URL %s" % self.absolute_url


class RemoteObject(RemoteResource):
  """A piece of content retrieved from the remote site."""

  def __init__(self, url, session = None):
    if session:
      self.session = session
    else:
      self.session = requests.Session()

    # Set the absolute URL to the parameter URL as a first
    # approximation. (It needs to be set to something in order
    # to call make_http_request to look up the real absolute_url.
    self.absolute_url = url
    self.absolute_url = self.make_http_request('absolute_url')
    if not self.is_valid_url(self.absolute_url):
      raise ValueError, "Invalid URL %s" % self.absolute_url[:256]

    # Remove certain Plone-specific suffixes which we should ignore.
    self.absolute_url = strip_plone_suffix(self.absolute_url)

    relative_url_str = self.make_http_request('virtual_url_path')
    self.relative_url = relative_url_str.split('/')

    # Retrieve the title and id (which we'll call "shortname")
    self.title = self.make_http_request('Title')
    self.shortname = urllib.unquote(self.relative_url[-1])
    
    # Handle the sitemap specially because calling '/Type' on it
    # returns the sitemap itself rather than a useful type.
    if self.shortname == 'sitemap':
      self.obj_type = 'Page'
    else:
      self.obj_type = self.make_http_request('Type')

    # Sometimes calling /Type on images returns "Plone Site," so
    # if that's what came back, double-check.
    if self.obj_type == 'Plone Site':
      img_types = ['image/jpeg', 'image/png', 'image/gif']
      try:
        if self.make_http_request('getContentType') in img_types:
          self.obj_type = 'Image'
      except NotFoundError:
        self.soup = BeautifulSoup(self.make_http_request('view'))
    if self.obj_type in ['News Item', 'Page']:
      self.soup = BeautifulSoup(self.get_cooked_body())
    elif self.obj_type in ['Folder', 'Large Folder']:
      self.soup = BeautifulSoup(self.make_http_request('view'))
      self.soup = self.soup.select('#region-content')[0]
      self.default_page = self.make_http_request('getDefaultPage')
    elif self.obj_type == 'Image':
      self.image = self.make_http_request('image')
    elif self.obj_type == 'File':
      pass
    #  self.file_data = self.make_http_request('getFile')
    #elif self.obj_type == 'Plone Site':
    # TODO: fix this. collections should be able to report their
    # contents.  But there's an old error in the site that prevents
    # folder_contents from working.
    elif self.obj_type == 'Collection':
      self.soup = BeautifulSoup(self.make_http_request('view'))
      self.soup = self.soup.select('#region-content')[0]
      search_criteria_str = self.make_http_request('listSearchCriteria')
      
      # Content Type criteria always have a certain ID.
      type_id = 'crit__Type_ATPortalTypeCriterion'
      if type_id in search_criteria_str: 
        self.type_criterion = self.make_http_request("%s/getRawValue" % type_id)
      # Path criteria always have a certain ID.
      path_id = 'crit__path_ATRelativePathCriterion'
      if path_id in search_criteria_str: 
        self.path_criterion = self.make_http_request("%s/getRelativePath" % path_id)
      sort_criterion_id = self.make_http_request('getSortCriterion')
      self.sort_criterion_str = extract_sort_criterion(sort_criterion_id)
      import pdb; pdb.set_trace()
    elif self.obj_type == 'Plone Site':
      # We already matched this above, so nothing more to do.
      pass
    else:
      msg = "Unrecognized object type '%s' for URL %s" % (self.obj_type, self.absolute_url)
      raise ValueError, msg


  def get_cooked_body(self):
    return self.make_http_request('CookedBody')

  def get_folder_body(self):
    return self.make_http_request('folder_contents')

        

  def get_images(self):
    return [image for image in self.soup.find_all('img')]

  def get_link_targets(self):
    """Return a list of URLs linked to in the remote object."""
    targets = [link.get('href') for link in self.get_links()]
    targets.extend([image.get('src') for image in self.get_images()])
    return targets

  def get_links(self):
    try:
      return [link for link in self.soup.find_all('a')]
    except AttributeError, msg:
      print "obj_type = %s" % self.obj_type
      raise AttributeError, msg


