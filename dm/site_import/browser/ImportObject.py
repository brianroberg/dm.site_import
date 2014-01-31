from zExceptions import BadRequest
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
import urllib

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
      relative_url_str = urllib.unquote('/'.join(self.relative_url[:-1]))
      container = self.view_obj.context.unrestrictedTraverse(relative_url_str)
    else:
      container = self.view_obj.context
    if self.remote_obj.shortname in container.objectIds():
      raise ObjectAlreadyExistsError
    else:
      try:
        container.invokeFactory(self.type_name, self.remote_obj.shortname)
      except BadRequest:
        self.remote_obj.shortname = "%s-RENAMED" % self.remote_obj.shortname
        if self.remote_obj.shortname in container.objectIds():
          raise ObjectAlreadyExistsError
        container.invokeFactory(self.type_name, self.remote_obj.shortname)

      self.site_obj = container[self.remote_obj.shortname]
      self.site_obj.setTitle(self.remote_obj.title)

      if hasattr(self.remote_obj, 'description'):
        self.site_obj.setDescription(self.remote_obj.description)
      if hasattr(self.remote_obj, 'creator'):
        self.site_obj.setCreators(self.remote_obj.creator,)
      if hasattr(self.remote_obj, 'creation_date'):
        self.site_obj.setCreationDate(self.remote_obj.creation_date)
      if hasattr(self.remote_obj, 'modification_date'):
        self.site_obj.setModificationDate(self.remote_obj.modification_date)
      if hasattr(self.remote_obj, 'exclude_from_nav'):
        self.site_obj.setExcludeFromNav(self.remote_obj.exclude_from_nav)
      if hasattr(self.remote_obj, 'review_state'):
        self.set_review_state(self.remote_obj.review_state)

      
  def reindex(self):
    """Call reindexObject on the site_obj without resetting mod date."""
    #od = self.site_obj.__dict__
    #od['notifyModified'] = lambda *args: None
    self.site_obj.indexObject()
    #del od['notifyModified']

  def set_review_state(self, target_state):
    # For now we'll assume the object is in the "private" state
    # since that's how it's created.
    portal_catalog = getToolByName(self.site_obj, 'portal_catalog')
    obj_path = '/'.join(self.site_obj.getPhysicalPath())
    results = portal_catalog(path={ "query": obj_path, 'depth': 0})
    rid = results[0].getRID()
    starting_state = portal_catalog._catalog.getIndex('review_state').getEntryForObject(rid, default=[])
    print "%s, current state is %s, target is %s" % (self.remote_obj.absolute_url, starting_state, target_state)
    #import pdb; pdb.set_trace()
    
    if starting_state == target_state:
      print 'already at target state %s, returning' % target_state
      return

    # For simple publication workflow (public sites)
    if starting_state == 'private':
      if target_state == 'published':
        print 'applying "publish" transition'
        self.apply_workflow_transition('publish')
        return
      if target_state == 'pending':
        print 'applying "submit" transition'
        self.apply_workflow_transition('submit')
        return
      else:
        print 'ERROR: no target state match for %s!' % self.absolute_url

    # I don't think this block is needed.
    elif starting_state == 'internal':
      if target_state == 'private':
        print 'applying "hide" transition'
        self.apply_workflow_transition('hide')
        return
      if target_state == 'internally_published':
        print 'applying "publish_internally" transition'
        self.apply_workflow_transition('publish_internally')
        return

    # For intranet workflow (staff site)
    #if starting_state == 'private':
    #  if target_state in ['internal', 'internally_published']:
    #    print 'applying "show_internally" transition'
    #    self.apply_workflow_transition('show_internally')
    #  if target_state == 'internally_published':
    #    print 'applying "publish_internally" transition'
    #    self.apply_workflow_transition('publish_internally')
    #    return
    #  else:
    #    print 'no target state match for %s!' % self.absolute_url
    #elif starting_state == 'internal':
    #  if target_state == 'private':
    #    print 'applying "hide" transition'
    #    self.apply_workflow_transition('hide')
    #    return
    #  if target_state == 'internally_published':
    #    print 'applying "publish_internally" transition'
    #    self.apply_workflow_transition('publish_internally')
    #    return
    else:
      'Unhandled starting state "%s" for %s' % (starting_state, self.absolute_url)





  def apply_workflow_transition(self, transition):
    workflowTool = getToolByName(self.view_obj, 'portal_workflow')
    try:
      workflowTool.doActionFor(self.site_obj, transition)
    except WorkflowException:
      print "WORKFLOW TRANSITION ERROR applying transition %s to %s" % (transition, self.absolute_url)


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
      self.reindex()

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
      self.site_obj.setFilename(self.remote_obj.shortname)
      self.reindex()


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
      # Check whether the folder has a default page. 'default_page'
      # attribute must be both present and non-empty.
      if (hasattr(self.remote_obj, 'default_page') and
          self.remote_obj.default_page):
        self.site_obj.setDefaultPage(self.remote_obj.default_page)
      else:
        self.site_obj.setDefaultPage(objectId = None)
      self.reindex()


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
      self.reindex()


class ImportLink(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'Link'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      self.site_obj.setRemoteUrl(self.remote_obj.link_target)
      self.reindex()

class ImportNewsItem(ImportObject):

  def __init__(self, remote_obj, view_obj):
    self.type_name = 'News Item'
    ImportObject.__init__(self, remote_obj, view_obj)

  def create(self):
    try:
      ImportObject.create(self)
    except ObjectAlreadyExistsError:
      print "%s already exists, exiting create()" % self.remote_obj.shortname
    else:
      #self.site_obj.setText(self.remote_obj.soup)
      self.site_obj.setText(self.remote_obj.get_cooked_body())
      self.site_obj.setImageCaption(self.remote_obj.caption)
      self.reindex()

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
      self.reindex()
