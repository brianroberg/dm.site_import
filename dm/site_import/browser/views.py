from Products.Five.browser import BrowserView
from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
from RemoteObject import (HTTPError, NotFoundError, RemoteLinkTarget,
                          RemoteObject)
from collections import deque

class DMSiteImportView(BrowserView):

  def __call__(self):

    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    self.objects_seen = {}

    # TODO: There are some URLs we shouldn't try to retrieve because
    # they don't exist in Zope, e.g. dm.org/donate. I could hard-code
    # those URLs here.
    self.skip_list = ['http://www.dm.org/donate']

    self.remove_events_and_news()

    site = 'www.dm.org'
    hp = RemoteObject('http://www.dm.org/site-homepage')
    self.objects_seen[hp.absolute_url] = ImportPage(hp, self)
    self.objects_seen[hp.absolute_url].create()
    self.crawl(hp)

    return "\n".join(self.objects_seen.keys())

  def add(self, remote_obj):
    """Add a remote object to the local site."""

    #import pdb; pdb.set_trace()

    # Check whether the object's parent has already been added.
    # If not, we need to add it first.
    parent_url = '/'.join(remote_obj.absolute_url.split('/')[:-1])
    if (len(remote_obj.relative_url) > 1) and self.needs_crawled(parent_url):
      self.add(RemoteObject(parent_url))

    if remote_obj.obj_type == 'Page':
      ip = ImportPage(remote_obj, self)
      self.objects_seen[remote_obj.absolute_url] = ip
      ip.create()            
      self.crawl(remote_obj)
    elif remote_obj.obj_type == 'Folder':
      import_obj = ImportFolder(remote_obj, self)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      self.crawl(remote_obj)
    elif remote_obj.obj_type == 'Image':
      import_obj = ImportImage(remote_obj, self)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      # Nothing to crawl within an image
    elif remote_obj.obj_type == 'File':
      import_obj = ImportFile(remote_obj, self)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      # Nothing to crawl within a file
    else:
      print "%s appears to be a %s, no handler yet" % (remote_obj.absolute_url, remote_obj.obj_type)
      self.objects_seen[remote_obj.absolute_url] = ImportObject(remote_obj, self)

  def crawl(self, remote_obj):
    print "Running **crawl** on %s" % remote_obj.absolute_url
    targets = deque(remote_obj.get_link_targets())
    # We will crawl not only this object, but also:
    #    1. Any objects above it in the containment hierarchy
    #    2. Any objects it links to

    for t in targets:
      if not t:
        continue
      try:
        rlt = RemoteLinkTarget(remote_obj.get_site(),
			       remote_obj.absolute_url, t)
      except (HTTPError, ValueError):
        continue

      if self.needs_crawled(rlt.absolute_url):
	# limit extent of crawling during development
#	if len(self.objects_seen.keys()) > 100:
#	  print "100 objects seen, breaking loop"
#	  break

        try:
	  self.add(RemoteObject(rlt.absolute_url))
        except HTTPError:
          continue

  def needs_crawled(self, url):
    #import pdb; pdb.set_trace()
    if url in self.objects_seen:
      return False
    if url in self.skip_list:
      return False
    # If the URL ends with any of these strings, don't crawl it.
    skip_suffixes = ['file_view', 'folder_contents']
    for s in skip_suffixes:
      if url[len(s) * -1:] == s:
	return False
    return True

  def remove_events_and_news(self):
    """Remove these folders in preparation for importing."""
    try:
      self.context.manage_delObjects(['events', 'news'])
    except AttributeError:
      pass
