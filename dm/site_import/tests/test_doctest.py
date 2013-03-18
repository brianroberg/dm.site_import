import unittest
import doctest

#from zope.testing import doctestunit
#from zope.component import testing, eventtesting

from Testing import ZopeTestCase as ztc

from dm.site_import.tests import base
from dm.site_import.browser.Crawler import Crawler
from dm.site_import.browser.ImportObject import (ImportObject, ImportFile,
                                                 ImportFolder, ImportImage,
                                                 ImportPage)
from dm.site_import.browser.RemoteObject import (HTTPError, NotFoundError,
                                                 RemoteLinkTarget,
                                                 RemoteObject, RemoteResource)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTests([
    unittest.makeSuite(CrawlerTesting),
    unittest.makeSuite(RemoteObjectTesting)
  ])
  return suite

if __name__ == '__main__':
  unittest.main(defaultTest='test_suite')
    

class CrawlerTesting(unittest.TestCase):

  def testContainsSkipStringAtAt(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/@@foobar'
    self.assertTrue(crawler.contains_skip_string(url))

  def testContainsSkipStringResource(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/++resource++foobar'
    self.assertTrue(crawler.contains_skip_string(url))

  def testNeedsCrawledAuthorSiteImport(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/author/siteimport'
    self.assertFalse(crawler.needs_crawled(url))

  def testNeedsCrawledLogout(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/logout'
    self.assertFalse(crawler.needs_crawled(url))

  def testNeedsCrawledPloneMemberprefsPanel(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/plone_memberprefs_panel'
    self.assertFalse(crawler.needs_crawled(url))

  def testNeedsCrawledSearchForm(self):
    crawler = Crawler('http://www.dm.org/site-homepage')
    url = 'http://www.dm.org/search_form'
    self.assertFalse(crawler.needs_crawled(url))



class RemoteObjectTesting(unittest.TestCase):

    def testAbsoluteUrl(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.absolute_url, 'http://www.dm.org/site-homepage')

    def testAbsoluteUrlDoubled(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage/site-homepage')
      self.assertEqual(remote_obj.absolute_url, 'http://www.dm.org/site-homepage')

    def testAbsoluteUrlDoubleDouble(self):
      remote_obj = RemoteObject('http://www.dm.org/about-us/our-staff/about-us/our-staff')
      self.assertEqual(remote_obj.absolute_url, 'http://www.dm.org/about-us/our-staff')

    def test_strip_plone_suffix_large(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_large'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_preview(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_preview'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_mini(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_mini'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_thumb(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_thumb'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_tile(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_tile'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_icon(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_icon'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_listing(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/image_listing'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_trailing_slash(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_no_change(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_view(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertEqual(remote_obj.strip_plone_suffix('http://www.dm.org/foo.jpg/view'), 'http://www.dm.org/foo.jpg')

    def test_is_valid_url(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertTrue(remote_obj.is_valid_url('http://www.dm.org'))
      self.assertFalse(remote_obj.is_valid_url(''))
      self.assertFalse(remote_obj.is_valid_url('<!DOCTYPE html>'))
