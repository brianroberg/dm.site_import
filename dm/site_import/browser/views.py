from Products.Five.browser import BrowserView
from RemoteObject import HTTPError, NotFoundError, RemoteObject

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
    hp = RemoteObject(site, '', '/site-homepage')
    self.objects_seen[hp.absolute_url] = ImportObject(hp.absolute_url)

    targets = hp.get_link_targets()
    for t in targets:
      try:
        obj = RemoteObject(site, '', t)
        if obj.absolute_url not in self.objects_seen:
          self.objects_seen[obj.absolute_url] = ImportObject(obj.absolute_url)
      except HTTPError:
        continue
    return self.objects_seen.keys()


class ImportObject:

  def __init__(self, absolute_url):
    self.absolute_url = absolute_url
