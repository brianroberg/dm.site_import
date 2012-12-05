from bs4 import BeautifulSoup
import httplib
import re
import urlparse

class HTTPError(Exception):
  pass

class NotFoundError(HTTPError):
  pass

class OffsiteError(HTTPError):
  pass

class RemoteResource:

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
      msg = "Server at %s returned 404 for resource %s" % (self.site, self)
      raise NotFoundError, msg
    elif r.status != 200:
      try:
	msg = "Server at %s returned error status %s for resource %s" % (self.site, r.status, self)
      except AttributeError:
        msg = "Server returned error status %s" % r.status
      raise HTTPError, msg
    return r.read()

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

    # Check whether this is an offsite link.
    netloc = urlparse.urlparse(link).netloc 
    if netloc and (netloc != site):
      msg = "Resource %s not part of site %s" % (link, site)
      raise OffsiteError, msg

    self.conn = httplib.HTTPConnection(site)
    request_url = urlparse.urljoin(full_url,
                                   'absolute_url',
                                   allow_fragments=False)
    self.conn.request('GET', request_url)
                      
    self.absolute_url = self.get_http_response()

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

    # Retrieve the title and id (which we'll call "shortname")
    title_and_id = self.make_http_request('title_and_id')
    match = re.match('(.*)(\s+)\((.*)\)', title_and_id)
    self.title = match.group(1).strip()
    self.shortname = match.group(3).strip()
    
    self.obj_type = self.make_http_request('Type')

    if self.obj_type in ['News Item', 'Page']:
      self.soup = BeautifulSoup(self.get_cooked_body())
    elif self.obj_type in ['Folder', 'Large Folder']:
      self.soup = BeautifulSoup(self.get_folder_body())
    elif self.obj_type in ['File', 'Image', 'Plone Site']:
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

  def get_link_targets(self):
    return [link.get('href') for link in self.get_links()]

  def get_links(self):
    try:
      return [link for link in self.soup.find_all('a')]
    except AttributeError, msg:
      print "obj_type = %s" % self.obj_type
      raise AttributeError, msg

  def get_site(self):
    return urlparse.urlparse(self.absolute_url).netloc

  def make_http_request(self, suffix=""):
    #print "make_http_request: url = %s, suffix = %s" % (self.absolute_url, suffix)
    self.conn.request('GET', "%s/%s" % (self.absolute_url, suffix))
    return self.get_http_response()
