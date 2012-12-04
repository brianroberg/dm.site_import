from bs4 import BeautifulSoup
import httplib
import urlparse

class HTTPError(Exception):
  pass

class NotFoundError(HTTPError):
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
      msg = "Server at %s returned error status %s for resource %s" % (self.site, r.status, self.absolute_url)
      raise HTTPError, msg
    return r.read()


class RemoteLinkTarget(RemoteResource):

  def __init__(self, site, base_url, link):
    self.site = site
    self.link = link
    full_url = urlparse.urljoin(base_url, link)
    print "full_url = %s" % full_url

    self.conn = httplib.HTTPConnection(site)
    self.conn.request('GET', "%s/absolute_url" % (full_url))
    self.absolute_url = self.get_http_response()


class RemoteObject(RemoteResource):

  def __init__(self, absolute_url):
    site = urlparse.urlparse(absolute_url).netloc
    self.conn = httplib.HTTPConnection(site)
    self.absolute_url = absolute_url

    self.obj_type = self.make_http_request('Type')

    if self.obj_type == 'Page':
      self.soup = BeautifulSoup(self.get_cooked_body())

  def get_cooked_body(self):
    return self.make_http_request('CookedBody')

  def make_http_request(self, suffix=""):
    self.conn.request('GET', "%s/%s" % (self.absolute_url, suffix))
    return self.get_http_response()

  def get_link_targets(self):
    return [link.get('href') for link in self.get_links()]

  def get_links(self):
    return [link for link in self.soup.find_all('a')]

