class ImportObject(object):

  def __init__(self, remote_obj, view_obj):
    self.absolute_url = remote_obj.absolute_url
    self.remote_obj = remote_obj
    self.view_obj = view_obj

  def create(self):
    print "Running create() for %s %s" % (self.type_name,
                                          self.absolute_url)
    self.view_obj.context.invokeFactory(self.type_name,
                                        self.remote_obj.shortname)
    self.site_obj = self.view_obj.context[self.remote_obj.shortname]
    self.site_obj.setTitle(self.remote_obj.title)

class ImportFile(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'File'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    ImportObject.create(self)
    self.site_obj.setFile(self.remote_obj.file_data)
    self.site_obj.reindexObject()


class ImportFolder(ImportObject):

  def create(self):
    print "Running create() for ImportFolder %s" % self.absolute_url
    self.view_obj.context.invokeFactory('Folder', self.remote_obj.shortname)
    obj = self.view_obj.context[self.remote_obj.shortname]
    obj.setTitle(self.remote_obj.title)
    obj.reindexObject()

class ImportImage(ImportObject):

  def create(self):
    print "Running create() for ImportImage %s" % self.absolute_url
    self.view_obj.context.invokeFactory('Image', self.remote_obj.shortname)
    obj = self.view_obj.context[self.remote_obj.shortname]
    obj.setTitle(self.remote_obj.title)
    obj.setImage(self.remote_obj.image)
    obj.reindexObject()


class ImportPage(ImportObject):

  def create(self):
    print "Running create() for ImportPage %s" % self.absolute_url
    self.view_obj.context.invokeFactory('Document', self.remote_obj.shortname)
    obj = self.view_obj.context[self.remote_obj.shortname]
    obj.setTitle(self.remote_obj.title)
    obj.setText(self.remote_obj.get_cooked_body())
    obj.reindexObject()
