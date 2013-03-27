from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
from RemoteObject import (BadRequestError, HTTPError, NotFoundError,
                          RemoteLinkTarget, RemoteObject,
                          extract_index_url)
import requests
import urlparse

class Crawler(object):

  def __init__(self, starting_url):
    # Dictionary to keep track of what objects we've already seen.
    # Each value is an Import Object.
    # Each key is the object's absolute_url (as returned in the
    # original site).
    self.objects_seen = {}

    # HTTP session, created here so that it can persist across all
    # the RemoteLinkTargets and RemoteObjects we'll be creating.
    self.session = requests.Session()

    self.starting_url = starting_url

    # Extract the site name from the starting URL.
    site = urlparse.urlparse(starting_url).netloc 

    # TODO: There are some URLs we shouldn't try to retrieve because
    # they don't exist in Zope, e.g. dm.org/donate. I could hard-code
    # those URLs here.
    self.skip_list = ['http://www.dm.org/donate']

  def get_import_objects(self):

    start_page = RemoteObject(self.starting_url, session = self.session)
    self.objects_seen[start_page.get_index_url()] = start_page
    self.crawl(start_page)

    return self.objects_seen

  def contains_skip_string(self, url):
    # There are some string patterns in URLs which tell us
    # right away that we don't want to follow the link.
    skip_strings = ['@@', '++resource++', 'createObject?',
                    'support_stats_entry_form']
    for s in skip_strings:
      if s in url:
        return True
    return False


  def crawl(self, remote_obj):
    print "Running **crawl** on %s" % remote_obj.absolute_url
    targets = remote_obj.get_link_targets()
    # We will crawl not only this object, but also:
    #    1. Any objects above it in the containment hierarchy
    #    2. Any objects it links to
    #    3. The default view (e.g. of a folder), if set

    # If a default view is set, add it to the list of targets
    # to evaluate.
    if hasattr(remote_obj, 'default_page'):
      targets.append(remote_obj.default_page)

    for t in targets:
      if not t:
        continue
      if self.contains_skip_string(t):
        continue
      if not self.needs_crawled(t):
        continue

      
      try:
        rlt = RemoteLinkTarget(remote_obj.get_site(),
                               remote_obj.absolute_url, t,
                               session = self.session)
      except (HTTPError, ValueError):
        continue

      if self.needs_crawled(rlt.absolute_url):
        # limit extent of crawling during development
        #if len(self.objects_seen.keys()) > 50:
        #  print "50 objects seen, breaking loop"
        #  break

        # Create a RemoteObject to represent the piece of content we're
        # looking at.
        try:
          remote_obj = RemoteObject(rlt.absolute_url,
                                    session = self.session)
          self.queue(remote_obj)
        except NotFoundError:
          print "Error 404 following link to %s on %s" % (rlt.absolute_url, remote_obj.absolute_url)
        except BadRequestError:
          print "Error 400 following link to %s on %s" % (rlt.absolute_url, remote_obj.absolute_url)



  def queue(self, remote_obj):
    # Check whether the object's parent has already been added.
    # If not, we need to add it first.
    parent_url = '/'.join(remote_obj.absolute_url.split('/')[:-1])
    if (len(remote_obj.relative_url) > 1) and self.needs_crawled(parent_url):
      self.queue(RemoteObject(parent_url, session = self.session))

    self.objects_seen[remote_obj.get_index_url()] = remote_obj
    print "*** %s *** %s" % (len(self.objects_seen.keys()),
                             remote_obj.absolute_url)

    # Pages and Folders should be crawled further.
    if remote_obj.obj_type in ['Page', 'Folder']:
      self.crawl(remote_obj)


  def needs_crawled(self, url):
    if extract_index_url(url) in self.objects_seen:
      return False
    if url in self.skip_list:
      return False
    
    # If the URL ends with any of these strings, don't crawl it.
    skip_suffixes = ['atct_edit',
                     'application.png',
                     'audio.png',
                     'author',
                     'author/siteimport',
                     'contact-info',
                     'content_status_history',
                     'dashboard',
                     'doc.png',
                     '#documentContent',
                     'document_icon.gif',
                     '/edit',
                     'file_view',
                     'folder_constraintypes_form',
                     'folder_factories',
                     'folder_icon.gif',
                     'Form.gif',
                     'html.png',
                     'image_icon.gif',
                     'info_icon.gif',
                     'link_icon.gif',
                     'lock_icon.gif',
                     'login_form',
                     'logo.jpg',
                     'logout',
                     'mail_password_form',
                     'newsitem_icon.gif',
                     'object_copy',
                     'ods.png',
                     'odt.png',
                     'pdf.png',
                     'pdf_icon.gif',
                     'plone_control_panel',
                     'plone_memberprefs_panel',
                     '#portlet-navigation-tree',
                     'RSS',
                     'search_form',
                     'select_default_view',
                     'sendto_form',
                     'spinner.gif',
                     'topic_icon.gif',
                     'user.gif',
                     'video.png',
                     'xls.png',
                     'zip.png']
    for s in skip_suffixes:
      if url[len(s) * -1:] == s:
        return False


    # If the URL has passed all the above tests, then give the
    # thumbs-up to crawl.
    return True

