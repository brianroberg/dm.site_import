from Products.Five.browser import BrowserView
from Crawler import Crawler
from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage, ImportCollection)
from RemoteObject import (HTTPError, NotFoundError, RemoteLinkTarget,
                          RemoteObject)
import config

class DMSiteImportView(BrowserView):

  def __call__(self):
    self.remove_events_and_news()

    #starting_url = 'http://www.dm.org/about-us/our-staff/drippsb'
    #starting_url = 'http://gettysburg.dm.org/audio-archive/fall-2012-jesus-is-better-matthews-gospel/jesus-is-better-matthews-gospel'
    #starting_url = 'http://gettysburg.dm.org'
    starting_url = 'http://www.dm.org'

    crawler = Crawler(starting_url)
    import_objects = crawler.get_import_objects()

    urls = import_objects.keys()
    urls.sort()

    for url in urls:
      remote_obj = import_objects[url]
      if remote_obj.obj_type == 'Page':
        # The sitemap is a special case: it's helpful to crawl
        # it, but we don't want to import it.
        if remote_obj.shortname == 'sitemap':
          continue
        import_obj = ImportPage(remote_obj, self)
        import_obj.create()
      # Plone 4 has only one folder type.
      elif remote_obj.obj_type in ['Folder', 'Large Folder']:
        import_obj = ImportFolder(remote_obj, self)
        import_obj.create()
      elif remote_obj.obj_type == 'Image':
        import_obj = ImportImage(remote_obj, self)
        import_obj.create()
      elif remote_obj.obj_type == 'File':
        import_obj = ImportFile(remote_obj, self)
        import_obj.create()
      elif remote_obj.obj_type == 'Link':
        import_obj = ImportLink(remote_obj, self)
        import_obj.create()
      elif remote_obj.obj_type == 'Collection':
        import_obj = ImportCollection(remote_obj, self)
        import_obj.create()
      elif remote_obj.obj_type == 'Plone Site':
        pass
      else:
        msg = 'Unknown type "%s" for remote object at %s' % (remote_obj.obj_type, remote_obj.absolute_url)
        raise ValueError, msg



  def remove_events_and_news(self):
    """Remove these folders in preparation for importing."""
    try:
      self.context.manage_delObjects(['events', 'news'])
    except AttributeError:
      pass
