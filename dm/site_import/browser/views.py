from Products.Five.browser import BrowserView
from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
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
    self.objects_seen[hp.absolute_url] = ImportPage(hp, self)
    self.objects_seen[hp.absolute_url].create()
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
          if len(self.objects_seen.keys()) > 40:
            print "40 objects seen, breaking loop"
            break

          ro = RemoteObject(rlt.absolute_url)
          if ro.obj_type == 'Page':
            ip = ImportPage(ro, self)
            self.objects_seen[rlt.absolute_url] = ip
            ip.create()            
          elif ro.obj_type == 'Folder':
            import_obj = ImportFolder(ro, self)
            self.objects_seen[rlt.absolute_url] = import_obj
            import_obj.create()            
          elif ro.obj_type == 'Image':
            import_obj = ImportImage(ro, self)
            self.objects_seen[rlt.absolute_url] = import_obj
            import_obj.create()            
            continue # Nothing to crawl within an image 
          elif ro.obj_type == 'File':
            import_obj = ImportFile(ro, self)
            self.objects_seen[rlt.absolute_url] = import_obj
            import_obj.create()            
            continue # Nothing to crawl within a file
          else:
            print "%s appears to be a %s, no handler yet" % (ro.absolute_url, ro.obj_type)
	    self.objects_seen[rlt.absolute_url] = ImportObject(ro, self)
          self.crawl(ro)
      except HTTPError:
        continue


