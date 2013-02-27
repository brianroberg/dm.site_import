from Products.Five.browser import BrowserView
from Crawler import Crawler

class DMSiteImportView(BrowserView):


  def __call__(self):


    #site = 'www.dm.org'
    self.site = 'gettysburg.dm.org'
    crawler = Crawler(self, self.site)
    objects_seen = crawler.go()


    return "\n".join(objects_seen.keys())

