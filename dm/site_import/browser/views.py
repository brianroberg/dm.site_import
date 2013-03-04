from Products.Five.browser import BrowserView
from Crawler import Crawler
from ImportObject import (ImportObject, ImportFile, ImportFolder, 
                          ImportImage, ImportPage)
from RemoteObject import (HTTPError, NotFoundError, RemoteLinkTarget,
                          RemoteObject)
import config

class DMSiteImportView(BrowserView):

  def __call__(self):
    self.remove_events_and_news()

    return "username = %s, password = %s" % (config.username, config.password)

    starting_url = 'http://gettysburg.dm.org/site-homepage'

    crawler = Crawler()
    import_objects = crawler.get_import_objects(starting_url)

    urls = import_objects.keys()
    urls.sort()

    for url in urls:
      remote_obj = import_objects[url]
      if remote_obj.obj_type == 'Page':
	import_obj = ImportPage(remote_obj, self)
	import_obj.create()
      elif remote_obj.obj_type == 'Folder':
	import_obj = ImportFolder(remote_obj, self)
	import_obj.create()
      elif remote_obj.obj_type == 'Image':
	import_obj = ImportImage(remote_obj, self)
	import_obj.create()
      elif remote_obj.obj_type == 'File':
	import_obj = ImportFile(remote_obj, self)
	import_obj.create()



  def remove_events_and_news(self):
    """Remove these folders in preparation for importing."""
    try:
      self.context.manage_delObjects(['events', 'news'])
    except AttributeError:
      pass
