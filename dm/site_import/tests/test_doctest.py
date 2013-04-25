import unittest
import datetime
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
                                                 OffsiteError,
                                                 RemoteObject, RemoteResource,
                                                 extract_datetime,
                                                 extract_index_url,
                                                 extract_sort_criterion,
                                                 strip_plone_suffix)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTests([
    unittest.makeSuite(CrawlerTesting),
    unittest.makeSuite(RemoteObjectTesting),
    unittest.makeSuite(RemoteLinkTargetTesting),
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


class RemoteLinkTargetTesting(unittest.TestCase):
  def setUp(self):
    self.site = 'www.dm.org'
    self.base_url = 'http://www.dm.org/'

  def test_is_offsite_link_our_staff(self):
    link = 'about-us/our-staff'
    rlt = RemoteLinkTarget(self.site, self.base_url, link)
    self.assertFalse(rlt.is_offsite_link())

  def test_is_offsite_link_regonline(self):
    link = 'http://www.regonline.com'
    with self.assertRaises(OffsiteError):
      rlt = RemoteLinkTarget(self.site, self.base_url, link)

  def test_is_offsite_link_gettysburg(self):
    link = 'http://gettysburg.dm.org/site-homepage'
    with self.assertRaises(OffsiteError):
      rlt = RemoteLinkTarget(self.site, self.base_url, link)



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

    def test_extract_datetime_page_returns_none(self):
      self.assertEqual(extract_datetime('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'), None)

    def test_extract_datetime_normal(self):
      date_str = '2013/04/24 15:00:00'
      date_obj = datetime.datetime(2013, 04, 24, 15, 00, 00)
      self.assertEqual(extract_datetime(date_str), date_obj)


    def test_extract_index_url_http(self):
      self.assertEqual(extract_index_url('http://www.dm.org'),
                       'www.dm.org')
      
    def test_extract_index_url_https(self):
      self.assertEqual(extract_index_url('https://www.dm.org'),
                       'www.dm.org')

    def test_extract_index_url_path(self):
      full_url = 'https://www.dm.org/about-us/our-staff'
      self.assertEqual(extract_index_url(full_url),
                       'www.dm.org/about-us/our-staff')

    def test_extract_index_url_query(self):
      full_url = 'https://www.dm.org/about-us/our-staff?arg=1'
      self.assertEqual(extract_index_url(full_url),
                       'www.dm.org/about-us/our-staff')



    def test_extract_sort_criterion_effective(self):
      criterion_id = 'crit__effective_ATSortCriterion'
      self.assertEqual(extract_sort_criterion(criterion_id),
                       'effective')

    def test_extract_sort_criterion_error(self):
      criterion_id = 'foobar'
      with self.assertRaises(ValueError):
        extract_sort_criterion(criterion_id)
      
    def test_extract_sort_criterion_modified(self):
      criterion_id = 'crit__modified_ATSortCriterion'
      self.assertEqual(extract_sort_criterion(criterion_id),
                       'modified')

    def test_get_local_roles_about_us(self):
      # This folder doesn't have any local roles
      url = 'http://www.dm.org/about-us/'
      correct_roles = ()
      remote_obj = RemoteObject(url)
      self.assertEqual(remote_obj.get_local_roles(), correct_roles)

    def test_get_local_roles_aseyevv(self):
      # This folder is owned by Vadim and Jenny
      url = 'http://www.dm.org/about-us/our-staff/aseyevv'
      correct_roles = ('aseyevj', ('Owner',)), ('aseyevv', ('Owner',))
      remote_obj = RemoteObject(url)
      self.assertEqual(remote_obj.get_local_roles(), correct_roles)


    def test_strip_plone_suffix_large(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_large'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_preview(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_preview'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_mini(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_mini'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_thumb(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_thumb'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_tile(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_tile'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_icon(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_icon'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_listing(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/image_listing'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_trailing_slash(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_no_change(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg'), 'http://www.dm.org/foo.jpg')

    def test_strip_plone_suffix_view(self):
      self.assertEqual(strip_plone_suffix('http://www.dm.org/foo.jpg/view'), 'http://www.dm.org/foo.jpg')

    def test_is_valid_url(self):
      remote_obj = RemoteObject('http://www.dm.org/site-homepage')
      self.assertTrue(remote_obj.is_valid_url('http://www.dm.org'))
      self.assertFalse(remote_obj.is_valid_url(''))
      self.assertFalse(remote_obj.is_valid_url('<!DOCTYPE html>'))
