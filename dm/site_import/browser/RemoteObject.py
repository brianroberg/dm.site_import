from bs4 import BeautifulSoup
from datetime import datetime
import config
import cPickle
import httplib
import re
import requests
import shelve
import string
import urllib
import urlparse

def extract_datetime(date_str):
  # First make sure the string we've received consists entirely
  # of printable characters.
  if not set(date_str).issubset(set(string.printable)):
    msg = 'Value passed to extract_datetime contained unprintable characters.'
    raise ValueError, msg

  if date_str[:21] == '<!DOCTYPE html PUBLIC':
    return None
  pattern = '(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})'
  match = re.match(pattern, date_str)
  if match:
    return datetime.strptime(match.group(), '%Y/%m/%d %H:%M:%S')
  else:
    msg = 'Regexp match failure for date string "%s"' % date_str
    raise ValueError, msg
  


# TODO: Test this function and then use it so that we don't
# crawl every URL twice!
def extract_index_url(url):
  o = urlparse.urlparse(url)
  return "%s%s" % (o.netloc, o.path)

def extract_sort_criterion(criterion_id):
  crit_id = criterion_id
  match = re.search('__([a-zA-Z]*)_', crit_id)
  if match:
    return match.group(1)
  else:
    msg = 'Unable to find sort criterion in string "%s"' % crit_id
    raise ValueError, msg


def is_whole_page(s):
  if s[:21] == '<!DOCTYPE html PUBLIC':
    return True
  else:
    return False


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
  # A simple cache to store results of HTTP requests.
  # Pre-load with a few URLs that don't return the correct
  # thing on their own.
  http_requests = shelve.open('http_requests', protocol=2)
  d = {'staff.dm.org/help_desk/staff_addresses/index_html/Type': 'Page',
       'staff.dm.org/help_desk/staff_birthdays/index_html/Type': 'Page',
       'staff.dm.org/teams/mentors/for-mentors-only/support_stats/Type': 'Page',
       'staff.dm.org/teams/mentors/for-mentors-only/Type': 'Folder',
       'staff.dm.org/teams/presidents/manuals/operations/human-resources/payroll/quarterly_taxes/pa_sales_tax/Type': 'Page',
       'staff.dm.org/teams/presidents/systems/wiki/systems-wiki/getSortCriterion': '<ATSortCriterion at crit__modified_ATSortCriterion>',
       'staff.dm.org/teams/candidate_staff/candidate-staff-list/Type': 'Page',
       'www.dm.org/give/paypal/choose-fund-preference/Type': 'Page',
       'www.dm.org/join/staff/apply/app/index_html/Type': 'Page',
       'www.dm.org/index_html/Type': 'Page',
       'www.dm.org/random_img/Type': 'Image'}
  for url in d.keys():
    if not http_requests.has_key(url):
      http_requests[url] = d[url]
    
  form_folders = []

  def __str__(self):
    if isinstance(self, RemoteObject):
      return "RemoteObject at %s" % self.absolute_url
    elif isinstance(self, RemoteLinkTarget):
      return "RemoteLinkTarget at %s" % self.link
    else:
      return "unknown RemoteResource object"

  def get_index_url(self):
    return extract_index_url(self.absolute_url)
  
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
    if not RemoteResource.http_requests.has_key(extract_index_url(request_url)):
      r = self.session.request(method, request_url, verify=False)

      # If the site has redirected us to the login page, log in
      # using credentials stored in the config module. Also force
      # login for the sitemap on the staff site.
      if (('require_login' in r.url or
          request_url == 'https://staff.dm.org/sitemap/CookedBody') or
          is_whole_page(r.content)):
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
        raise HTTPError, msg

      RemoteResource.http_requests[extract_index_url(request_url)] = r.content
      return r.content
    else:
      return RemoteResource.http_requests[extract_index_url(request_url)]


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

    if self.is_offsite_link():
      msg = "Resource %s not part of site %s" % (self.link, self.site)
      raise OffsiteError, msg

    # Set the absolute URL to the linked URL as a first
    # approximation. (It needs to be set to something in order
    # to call make_http_request to look up the real absolute_url.
    self.absolute_url = full_url
    self.absolute_url = self.make_http_request('absolute_url')

    if not self.is_valid_url(self.absolute_url):
      raise ValueError, "Invalid URL %s" % self.absolute_url

  def is_offsite_link(self):
    # Check whether this is an offsite link.
    netloc = urlparse.urlparse(self.link).netloc 
    if netloc and (netloc != self.site):
      return True
    return False


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
    self.shortname = urllib.unquote(self.relative_url[-1])

    # Handle the sitemap specially because trying to retrieve
    # metadata on it doesn't seem to produce anything useful.
    # We don't need all its metadata because we're only crawling
    # it, not importing it.
    if self.shortname == 'sitemap':
      self.obj_type = 'Page'
      self.soup = BeautifulSoup(self.get_cooked_body())
      # Explicitly exit __init__
      return None

    # Retrieve the title and id (which we'll call "shortname")
    try:
      self.title = self.make_http_request('Title')
    except HTTPError:
      try:
        self.title = self.make_http_request('title_or_id')
      except HTTPError:
        # Allow the title to be blank.
        self.title = ''

    # Retrieve other metadata
    self.creator = self.make_http_request('Creator')
    cdate_str = self.make_http_request('created')
    self.creation_date = extract_datetime(cdate_str)
    mdate_str = self.make_http_request('modified')
    self.modification_date = extract_datetime(mdate_str)
    

    # Shortcuts for known filename extensions
    if self.shortname[-4:].lower() in ['.jpg', '.png', '.gif']:
      self.obj_type = 'Image'
    elif self.shortname[-4:].lower() in (['.pdf', '.odt', '.ods',
                                          '.mp3', '.doc']):
      self.obj_type = 'File'

    # If no shortcuts matched, look up the type explicitly.
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
    if self.obj_type == 'Page':
      self.soup = BeautifulSoup(self.get_cooked_body())
    elif self.obj_type == 'News Item':
      #self.text = self.make_http_request('getText')
      #self.soup = BeautifulSoup(self.text)
      self.soup = BeautifulSoup(self.get_cooked_body())
      self.caption = self.make_http_request('getImageCaption')
    elif self.obj_type in ['Folder', 'Large Folder']:
      self.soup = BeautifulSoup(self.make_http_request('view'))
      self.soup = self.soup.select('#region-content')[0]
      self.default_page = self.make_http_request('getDefaultPage')
    elif self.obj_type == 'Image':
      try:
        self.image = self.make_http_request('image')
      # We'll get TooManyRedirects if an image is saved as a File object,
      # which has happened at times but we'd like to correct.
      except requests.TooManyRedirects:
        print "TooManyRedirects raised while trying to access %s/%s" % (self.absolute_url, 'image')
        self.image = self.make_http_request('getFile')
    elif self.obj_type == 'File':
      self.file_data = self.make_http_request('getFile')
      pass
    elif self.obj_type == 'Link':
      self.link_target = self.make_http_request('getRemoteUrl')
    # TODO: fix this. collections should be able to report their
    # contents.  But there's an old error in the site that prevents
    # folder_contents from working.
    elif self.obj_type == 'Collection':
      self.soup = BeautifulSoup(self.make_http_request('view'))
      self.soup = self.soup.select('#region-content')[0]
      search_criteria_str = self.make_http_request('listSearchCriteria')

      # Transform the string into a list of criterion IDs.
      crit_ids = re.findall('at (\S+)>', search_criteria_str)
      crit_ids = [crit_id.split('/')[-1] for crit_id in crit_ids]

      for crit_id in crit_ids:

        # Type
        if crit_id == 'crit__Type_ATPortalTypeCriterion':
          try:
            url = "%s/Value" % crit_id
            result = self.make_http_request(url)
            self.type_criterion = eval(result)
          except SyntaxError:
            msg = "Error eval'ing result of %s/%s. Result = %s" % (self.absolute_url, url, result)
            raise SyntaxError, msg

          if len(self.type_criterion) > 1:
            self.type_criteria = self.type_criterion
            self.type_criterion = self.type_criterion[0]

        # Relative Path
        elif crit_id == 'crit__path_ATRelativePathCriterion':
          self.relative_path_criterion = self.make_http_request("%s/getRelativePath" % crit_id)

        # Creation Date
        elif crit_id == 'crit__created_ATFriendlyDateCriteria':
          self.relative_date_value = self.make_http_request("%s/Value" % crit_id)

        else:
          print "**** Collection %s has a criterion I don't know how to handle: %s" % (self.absolute_url, crit_id)
          import pdb; pdb.set_trace()

          
      criteria = self.make_http_request('listCriteria')
      if is_whole_page(criteria):
        self.log_in("https://%s/login_form" % self.get_site())
        criteria = self.make_http_request('listCriteria')
      if criteria:
        pattern = '<ATSortCriterion at .*>'
        match_obj = re.search(pattern, criteria)
        if match_obj:
          sort_criterion_id = match_obj.group()

        self.sort_criterion_str = extract_sort_criterion(sort_criterion_id)



    elif self.obj_type == 'Form Folder':
      print "Found a form folder at %s" % self.absolute_url
      RemoteResource.form_folders.append(self.absolute_url)
      print "Total form folders: %s" % len(RemoteResource.form_folders)
    elif self.obj_type == 'Plone Site':
      # We already matched this above, so nothing more to do.
      pass
    elif self.obj_type[:21] == '<!DOCTYPE html PUBLIC':
      print "/Type seems to have returned a whole HTML page for URL %s" % self.absolute_url
      import pdb; pdb.set_trace()
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

  def get_local_roles(self):
    return eval(self.make_http_request('site_import_get_local_roles'))
