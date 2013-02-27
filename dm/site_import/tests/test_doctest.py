import unittest
import doctest

#from zope.testing import doctestunit
#from zope.component import testing, eventtesting

from Testing import ZopeTestCase as ztc

from dm.site_import.tests import base
from dm.site_import.browser.views import DMSiteImportView
from dm.site_import.browser.ImportObject import (ImportObject, ImportFile,
                                                 ImportFolder, ImportImage,
                                                 ImportPage)
from dm.site_import.browser.RemoteObject import (HTTPError, NotFoundError,
                                                 RemoteLinkTarget,
                                                 RemoteObject, RemoteResource)


def test_suite():
      suite = unittest.TestSuite()
      suite.addTests([
          unittest.makeSuite(RemoteObjectTesting)
      ])
      return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')


class RemoteObjectTesting(unittest.TestCase):

    def setUp(self):
      self.remote_obj = RemoteObject('http://www.dm.org/site-homepage')

    def testAbsoluteUrl(self):
      self.assertEqual(self.remote_obj.absolute_url, 'http://www.dm.org/site-homepage')

    def test_get_relative_url_str_simple(self):
      self.assertEqual(self.remote_obj.get_relative_url_str(),
                       'site-homepage')

      
    def test_strip_plone_suffix_large(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_large'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_preview(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_preview'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_mini(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_mini'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_thumb(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_thumb'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_tile(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_tile'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_icon(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_icon'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_listing(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_listing'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_trailing_slash(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_no_change(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_view(self):
      self.assertEqual(self.remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/view'), 'http://www.dm.org/foo.jpg')

    def test_is_valid_url(self):
      self.assertTrue(self.remote_obj.is_valid_url('http://www.dm.org'))
      self.assertFalse(self.remote_obj.is_valid_url(''))
      self.assertFalse(self.remote_obj.is_valid_url('<!DOCTYPE html>'))
