import unittest
import doctest

#from zope.testing import doctestunit
#from zope.component import testing, eventtesting

from Testing import ZopeTestCase as ztc

from dm.site_import.tests import base
from dm.site_import.browser.ImportObject import (ImportObject, ImportFile,
                                                 ImportFolder, ImportImage,
                                                 ImportPage)
from dm.site_import.browser.RemoteObject import (HTTPError, NotFoundError,
                                                 RemoteLinkTarget,
                                                 RemoteObject)


def test_suite():
#    return unittest.TestSuite([
#
#        # Demonstrate the main content types
#        ztc.ZopeDocFileSuite(
#            'README.txt', package='dm.site_import',
#            test_class=base.FunctionalTestCase,
#            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
#                doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
#
#        ])
      suite = unittest.TestSuite()
      suite.addTests([
          unittest.makeSuite(RemoteObjectTesting)
      ])
      return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

class RemoteObjectTesting(unittest.TestCase):

    def testAbsoluteUrl(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.absolute_url, 'http://www.dm.org/site-homepage')
