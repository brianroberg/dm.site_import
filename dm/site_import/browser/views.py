from bs4 import BeautifulSoup
from Products.Five.browser import BrowserView
import httplib

class DMSiteImportView(BrowserView):

  def __call__(self):
    print 'Hello, world!'
    site = 'www.dm.org'
    page = '/site-homepage'
    return self.get_cooked_body(site, page)
	
  def get_cooked_body(self, site, page):
    conn = httplib.HTTPConnection(site)
    conn.request('GET', "%s/CookedBody" % page)
    r = conn.getresponse()
    return r.read()
