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
    return hp.absolute_url

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
    

class NotFoundError(Exception):
  pass


class RemoteObject:

  def __init__(self, site, base_url, link):
    self.conn = httplib.HTTPConnection(site)
    self.conn.request('GET', "%s/%s/absolute_url" % (base_url, link))
    r = self.conn.getresponse()
    self.absolute_url = r.read()

  def get_cooked_body(self):
    return self.make_http_request('CookedBody')

  def make_http_request(self, suffix=""):
    self.conn.request('GET', "%s/%s" % (self.absolute_url, suffix))
    r = self.conn.getresponse()
    if r.status == 404:
      msg = "Server at %s returned 404 for page %s" % (site, page)
      raise NotFoundError, msg
    return r.read()
