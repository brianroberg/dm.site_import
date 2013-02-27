from bs4 import BeautifulSoup
import httplib
import re
import urllib
import urlparse

class HTTPError(Exception):
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

  def get_http_response(self):
    r = self.conn.getresponse()
    # TODO: add base_url to error message
    if r.status == 404:
      try:
	msg = "Server at %s returned 404 for resource %s" % (self.site, self)
      except AttributeError:
        msg = "Server returned error status %s" % r.status
      raise NotFoundError, msg
    elif r.status >= 300:
      try:
	msg = "Server at %s returned error status %s for resource %s" % (self.site, r.status, self)
      except AttributeError:
        msg = "Server returned error status %s" % r.status
      raise HTTPError, msg
    return r.read()


  def strip_plone_suffix(self, url):
    """Return URL with any Plone-specific suffixes removed."""
    suffixes = ['/image_large', '/image_preview', '/image_mini',
                '/image_thumb', '/image_tile', '/image_icon',
                '/image_listing', '/view']
    # First strip off a trailing slash if it's there.
    if url[-1] == '/':
      url = url[:-1]

    for s in suffixes:
      if url[len(s) * -1:] == s:

        return url[:len(s) * -1]

    # If we make it down here, return the URL as-is.
    return url


  def is_valid_url(self, url):
    parse_result = urlparse.urlparse(url)
    if parse_result.netloc == '':
      return False
    if parse_result.scheme[:4] != 'http':
      return False
    return True


class RemoteLinkTarget(RemoteResource):
  """Represents a link we've found on the remote site."""

  def __init__(self, site, base_url, link):
    self.site = site
    self.link = link
    full_url = urlparse.urljoin(base_url, link, allow_fragments=False)

    # Filter the URL we've constructed to remove any Plone-specific
    # suffixes.
    full_url = self.strip_plone_suffix(full_url)

    # Check whether this is an offsite link.
    netloc = urlparse.urlparse(link).netloc 
    if netloc and (netloc != site):
      msg = "Resource %s not part of site %s" % (link, site)
      raise OffsiteError, msg

    request_url = "%s/absolute_url" % full_url

    # TODO: Factor this out to unify it with the make_http_request version.
    # Check whether we've already looked up this absolute url.
    if request_url not in RemoteResource.http_requests:
      self.conn = httplib.HTTPConnection(site)
      self.conn.request('GET', request_url)
      self.absolute_url = self.get_http_response()
      RemoteResource.http_requests[request_url] = self.absolute_url
    else:
      self.absolute_url = RemoteResource.http_requests[request_url]

    if not self.is_valid_url(self.absolute_url):
      raise ValueError, "Invalid URL %s" % self.absolute_url


class RemoteObject(RemoteResource):
  """A piece of content retrieved from the remote site."""

  def __init__(self, absolute_url):
    site = urlparse.urlparse(absolute_url).netloc
    self.conn = httplib.HTTPConnection(site)
    self.absolute_url = absolute_url
    if not self.is_valid_url(self.absolute_url):
      raise ValueError, "Invalid URL %s" % self.absolute_url[:256]

    # Remove certain Plone-specific suffixes which we should ignore.
    self.absolute_url = self.strip_plone_suffix(self.absolute_url)

    relative_url_str = self.make_http_request('virtual_url_path')
    self.relative_url = relative_url_str.split('/')

    # Retrieve the title and id (which we'll call "shortname")
    self.title = self.make_http_request('Title')
    self.shortname = urllib.unquote(self.relative_url[-1])
    self.obj_type = self.make_http_request('Type')
    # Sometimes calling /Type on images returns "Plone Site," so
    # if that's what came back, double-check.
    if self.obj_type == 'Plone Site':
      img_types = ['image/jpeg', 'image/png', 'image/gif']
      if self.make_http_request('getContentType') in img_types:
        self.obj_type = 'Image'
    if self.obj_type in ['News Item', 'Page']:
      self.soup = BeautifulSoup(self.get_cooked_body())
    elif self.obj_type in ['Folder', 'Large Folder']:
      self.soup = BeautifulSoup(self.get_folder_body())
      self.default_page = self.make_http_request('getDefaultPage')
    elif self.obj_type == 'Image':
      self.image = self.make_http_request('image')
    elif self.obj_type == 'File':
      self.file_data = self.make_http_request('getFile')
    elif self.obj_type == 'Plone Site':
      self.soup = BeautifulSoup('')
    # TODO: fix this. collections should be able to report their
    # contents.  But there's an old error in the site that prevents
    # folder_contents from working.
    elif self.obj_type == 'Collection':
      self.soup = BeautifulSoup('')

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

  def get_site(self):
    return urlparse.urlparse(self.absolute_url).netloc

  def make_http_request(self, suffix=""):
    request_url = "%s/%s" % (self.absolute_url, suffix)
    if request_url not in RemoteResource.http_requests:
      self.conn.request('GET', request_url)
      response = self.get_http_response()
      RemoteResource.http_requests[request_url] = response
      return response
    else:
      return RemoteResource.http_requests[request_url]

