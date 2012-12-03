from bs4 import BeautifulSoup
from Products.Five.browser import BrowserView
import httplib

class DMSiteImportView(BrowserView):

  def __call__(self):

    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    self.objects_seen = {}

    site = 'www.dm.org'
    hp = RemoteObject(site, '', '/site-homepage')
    self.objects_seen[hp.absolute_url] = hp

    targets = hp.get_link_targets()
    for t in targets:
      try:
        obj = RemoteObject(site, '', t)
        if obj.absolute_url not in self.objects_seen:
          self.objects_seen[obj.absolute_url] = obj
      except HTTPError:
        continue
    return self.objects_seen.keys()

    #page = '/site-homepage'
    #return "Return value is %s." % self.is_already_retrieved('', page)

  def is_already_retrieved(self, base_url, page):
    url = self.make_http_request(base_url, page, 'absolute_url')
    if url in self.objects_seen.keys():
      return True
    else:
      return False
    
	


class ImportObject:

  def __init__(self, absolute_url):
    self.absolute_url = absolute_url
    
class HTTPError(Exception):
  pass

class NotFoundError(HTTPError):
  pass


class RemoteObject:

  def __init__(self, site, base_url, link):
    self.site = site
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
