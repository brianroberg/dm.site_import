from Products.Five.browser import BrowserView
from Crawler import Crawler

class DMSiteImportView(BrowserView):

  def __call__(self):

    #site = 'www.dm.org'
    site = 'gettysburg.dm.org'

    crawler = Crawler(self, site)
    objects_seen = crawler.go()


    return "\n".join(self.objects_seen.keys())

