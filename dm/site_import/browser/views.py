from Products.Five.browser import BrowserView
from RemoteObject import HTTPError, NotFoundError, RemoteLinkTarget, RemoteObject

class DMSiteImportView(BrowserView):

  def __call__(self):

    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    # TODO: There are some URLs we shouldn't try to retrieve because
    # they don't exist in Zope, e.g. dm.org/donate. I could hard-code
    # those URLs here.
    self.objects_seen = {}

    site = 'www.dm.org'
    hp = RemoteObject('http://www.dm.org/site-homepage')
    self.objects_seen[hp.absolute_url] = ImportObject(hp.absolute_url)
    self.crawl(hp)

    return "\n".join(self.objects_seen.keys())

  def crawl(self, remote_obj):
    targets = remote_obj.get_link_targets()
    for t in targets:
      if not t:
        continue
      try:
        rlt = RemoteLinkTarget(remote_obj.get_site(),
                               remote_obj.absolute_url, t)
        if rlt.absolute_url not in self.objects_seen:
          # limit extent of crawling during development
          if len(self.objects_seen.keys()) > 100:
            print "100 objects seen, breaking loop"
            break

          self.objects_seen[rlt.absolute_url] = ImportObject(rlt.absolute_url)
          self.crawl(RemoteObject(rlt.absolute_url))
      except HTTPError:
        continue


class ImportObject:

  def __init__(self, absolute_url):
    self.absolute_url = absolute_url
