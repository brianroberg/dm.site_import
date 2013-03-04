from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
from RemoteObject import (HTTPError, NotFoundError, RemoteLinkTarget,
                          RemoteObject)
import urlparse

class Crawler(object):

  def __init__(self):
    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    self.objects_seen = {}


  def get_import_objects(self, starting_url):

    # Extract the site name from the starting URL.
    site = urlparse.urlparse(starting_url).netloc 

    # TODO: There are some URLs we shouldn't try to retrieve because
    # they don't exist in Zope, e.g. dm.org/donate. I could hard-code
    # those URLs here.
    self.skip_list = ['http://www.dm.org/donate', 
                      "http://%s/login_form" % site,
                      "http://%s/object_copy" % site,
                      "http://%s/sitemap" % site,
                      "http://%s/search_form" % site]

    start_page = RemoteObject(starting_url)
    self.objects_seen[start_page.absolute_url] = start_page
    self.crawl(start_page)

    return self.objects_seen


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

      if self.needs_crawled(rlt.absolute_url):
	# limit extent of crawling during development
#	if len(self.objects_seen.keys()) > 100:
#	  print "100 objects seen, breaking loop"
#	  break

        # Create a RemoteObject to represent the piece of content we're
        # looking at.
        remote_obj = RemoteObject(rlt.absolute_url)

        #try:
	#self.objects_seen[rlt.absolute_url] = RemoteObject(rlt.absolute_url)
        self.queue(RemoteObject(rlt.absolute_url))
        #except HTTPError:
        #  continue

  def queue(self, remote_obj):
    print "queue on %s" % remote_obj.absolute_url
    # Check whether the object's parent has already been added.
    # If not, we need to add it first.
    parent_url = '/'.join(remote_obj.absolute_url.split('/')[:-1])
    if (len(remote_obj.relative_url) > 1) and self.needs_crawled(parent_url):
      self.queue(RemoteObject(parent_url))

    self.objects_seen[remote_obj.absolute_url] = remote_obj

    # Pages and Folders should be crawled further.
    if remote_obj.obj_type in ['Page', 'Folder']:
      self.crawl(remote_obj)


  def needs_crawled(self, url):
    #import pdb; pdb.set_trace()
    if url in self.objects_seen:
      return False
    if url in self.skip_list:
      return False
    # If the URL ends with any of these strings, don't crawl it.
    skip_suffixes = ['file_view']
    for s in skip_suffixes:
      if url[len(s) * -1:] == s:
	return False
    return True

