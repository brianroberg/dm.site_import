from Products.Five.browser import BrowserView

class DMSiteImportView(BrowserView):

  def __call__(self):
    print 'Hello, world!'
    print "title = %s" % self.context.Title()
	

