class ObjectAlreadyExistsError(ValueError):
  pass

class ImportObject(object):

  def __init__(self, remote_obj, view_obj):
    self.absolute_url = remote_obj.absolute_url
    self.relative_url = remote_obj.relative_url
    self.remote_obj = remote_obj
    self.view_obj = view_obj

  def create(self):
    print "Running create() for %s %s" % (self.type_name,
                                          self.absolute_url)
    if len(self.relative_url) > 1:
      relative_url_str = '/'.join(self.relative_url[:-1])
      container = self.view_obj.context.unrestrictedTraverse(relative_url_str)
    else:
      container = self.view_obj.context
    if self.remote_obj.shortname in container.objectIds():
      raise ObjectAlreadyExistsError
    else:
      container.invokeFactory(self.type_name,
			      self.remote_obj.shortname)
      self.site_obj = container[self.remote_obj.shortname]
      self.site_obj.setTitle(self.remote_obj.title)


class ImportCollection(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Collection'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      query = []
      if hasattr(self.remote_obj, 'type_criterion'):
        query.append({
          'i': 'portal_type',
          'o': 'plone.app.querystring.operation.selection.is',
          'v': self.remote_obj.type_criterion})
      if hasattr(self.remote_obj, 'relative_path_criterion'):
        query.append({
          'i': 'path',
          'o': 'plone.app.querystring.operation.string.relativePath',
          'v': self.remote_obj.relative_path_criterion})

      # If we've found any search criteria, apply them now.
      if query:
        self.site_obj.setQuery(query)

      if hasattr(self.remote_obj, 'sort_criterion_str'):
        self.site_obj.setSort_on(self.remote_obj.sort_criterion_str)
      self.site_obj.reindexObject()

class ImportFile(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'File'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      self.site_obj.setFile(self.remote_obj.file_data)
      self.site_obj.reindexObject()


class ImportFolder(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Folder'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      if self.remote_obj.default_page:
        self.site_obj.setDefaultPage(self.remote_obj.default_page)
      self.site_obj.reindexObject()


class ImportImage(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Image'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      self.site_obj.setImage(self.remote_obj.image)
      self.site_obj.reindexObject()


class ImportPage(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Document'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      self.site_obj.setText(self.remote_obj.get_cooked_body())
      self.site_obj.reindexObject()
