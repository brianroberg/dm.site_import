from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
from RemoteObject import (HTTPError, NotFoundError, RemoteLinkTarget,
                          RemoteObject)

class Crawler(object):

  def __init__(self, view_obj, site):
    self.view_obj = view_obj
    self.site = site

  def go(self):
    # There are some URLs we shouldn't try to retrieve because
    # they don't exist in Zope, or because they're Plone internal URLs
    # rather than content.
    self.skip_list = ['http://www.dm.org/donate', 
                      "http://%s/login_form" % self.site,
                      "http://%s/sitemap" % self.site,
                      "http://%s/search_form" % self.site]

    self.remove_events_and_news()

    hp = RemoteObject("http://%s/site-homepage" % self.site)

    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    self.objects_seen = {}
    self.objects_seen[hp.absolute_url] = ImportPage(hp, self.view_obj)
    self.objects_seen[hp.absolute_url].create()
    self.crawl(hp)
    
    return self.objects_seen

  def add(self, remote_obj):
    """Add a remote object to the local site."""

    # Check whether the object's parent has already been added.
    # If not, we need to add it first.
    parent_url = '/'.join(remote_obj.absolute_url.split('/')[:-1])
    if (len(remote_obj.relative_url) > 1) and self.needs_crawled(parent_url):
      self.add(RemoteObject(parent_url))

    if remote_obj.obj_type == 'Page':
      ip = ImportPage(remote_obj, self.view_obj)
      self.objects_seen[remote_obj.absolute_url] = ip
      ip.create()            
      self.crawl(remote_obj)
    elif remote_obj.obj_type == 'Folder':
      import_obj = ImportFolder(remote_obj, self.view_obj)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      self.crawl(remote_obj)
    elif remote_obj.obj_type == 'Image':
      import_obj = ImportImage(remote_obj, self.view_obj)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      # Nothing to crawl within an image
    elif remote_obj.obj_type == 'File':
      import_obj = ImportFile(remote_obj, self.view_obj)
      self.objects_seen[remote_obj.absolute_url] = import_obj
      import_obj.create()            
      # Nothing to crawl within a file
    else:
      print "%s appears to be a %s, no handler yet" % (remote_obj.absolute_url, remote_obj.obj_type)
      self.objects_seen[remote_obj.absolute_url] = ImportObject(remote_obj, self.view_obj)

  def already_exists(self, url):
    """Returns true if the URL identifies an already-existing object."""
    #import pdb; pdb.set_trace()
    return False

  def crawl(self, remote_obj):
    print "Running **crawl** on %s" % remote_obj.absolute_url
    targets = remote_obj.get_link_targets()
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

      #if 'mp3' in t:
      #  import pdb; pdb.set_trace()

      if self.needs_crawled(rlt.absolute_url):
	# limit extent of crawling during development
#	if len(self.objects_seen.keys()) > 100:
#	  print "100 objects seen, breaking loop"
#	  break

        try:
	  self.add(RemoteObject(rlt.absolute_url))
        except HTTPError:
          continue

  def get_relative_url_str(self, absolute_url):                                 
    """Return the relative URL string given the absolute URL."""
    url = absolute_url[len("http://%s" % self.get_site()) + 1:]
    return url

  def get_site(self):
    return self.site


  def needs_crawled(self, url):
    # TODO: Check to see if the object already exists in the new
    # site from a previous run of the script (i.e. check by
    # traversing to the URL).

    # Don't crawl if we've already seen the object in this run
    # of the script.
    if url in self.objects_seen:
      return False

    # Don't crawl if the URL is on a list of URLs to skip.
    if url in self.skip_list:
      return False

    # If the URL ends with any of these strings, don't crawl it.
    skip_suffixes = ['file_view']
    for s in skip_suffixes:
      if url[len(s) * -1:] == s:
	return False

    # Don't crawl if the object already exists in the new site 
    # (from a previous run of the script).
    if self.already_exists(url):
      return False 

    return True

  def remove_events_and_news(self):
    """Remove these folders in preparation for importing."""
    try:
      self.view_obj.context.manage_delObjects(['events', 'news'])
    except AttributeError:
      pass
