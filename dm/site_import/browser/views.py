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

    targets = hp.get_link_targets()
    for t in targets:
      try:
        rlt = RemoteLinkTarget(site, hp.absolute_url, t)
        if rlt.absolute_url not in self.objects_seen:
          self.objects_seen[rlt.absolute_url] = ImportObject(rlt.absolute_url)
      except HTTPError:
        continue
    return self.objects_seen.keys()


class ImportObject:

  def __init__(self, absolute_url):
    self.absolute_url = absolute_url
