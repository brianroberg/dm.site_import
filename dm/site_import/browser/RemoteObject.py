from bs4 import BeautifulSoup
import httplib

class HTTPError(Exception):
  pass

class NotFoundError(HTTPError):
  pass

class RemoteObject:

  def __init__(self, site, base_url, link):
    self.site = site

    # TODO: Do proper preparation of the relative URL, including making
    # use of base_url.
    if link[0] == '/':
      self.page = link[1:]
    else:
      self.page = link

    self.conn = httplib.HTTPConnection(site)
    self.conn.request('GET', "%s/%s/absolute_url" % (base_url, link))
    self.absolute_url = self.get_http_response()

    self.obj_type = self.make_http_request('Type')

    if self.obj_type == 'Page':
      self.soup = BeautifulSoup(self.get_cooked_body())

  def get_cooked_body(self):
    return self.make_http_request('CookedBody')

  def get_http_response(self):
    r = self.conn.getresponse()
    # TODO: add base_url to error message
    if r.status == 404:
      msg = "Server at %s returned 404 for page %s" % (self.site, self.page)
      raise NotFoundError, msg
    elif r.status != 200:
      msg = "Server at %s returned error status %s for page %s" % (self.site, r.status, self.page)
      raise HTTPError, msg
    return r.read()


  def get_link_targets(self):
    return [link.get('href') for link in self.get_links()]

  def get_links(self):
    return [link for link in self.soup.find_all('a')]

  def make_http_request(self, suffix=""):
    self.conn.request('GET', "%s/%s" % (self.absolute_url, suffix))
    return self.get_http_response()
