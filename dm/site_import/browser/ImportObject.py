class ImportObject(object):

  def __init__(self, remote_obj, view_obj):
    self.absolute_url = remote_obj.absolute_url
    self.relative_url = remote_obj.relative_url
    print "relative_url = %s" % str(self.relative_url)
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

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Folder'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    ImportObject.create(self)
    self.site_obj.reindexObject()


class ImportImage(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Image'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    ImportObject.create(self)
    self.site_obj.setImage(self.remote_obj.image)
    self.site_obj.reindexObject()


class ImportPage(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Document'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    ImportObject.create(self)
    self.site_obj.setText(self.remote_obj.get_cooked_body())
    self.site_obj.reindexObject()
