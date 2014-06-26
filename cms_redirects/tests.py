from django.test import TestCase
from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from cms.api import create_page, publish_page
from cms_redirects.models import CMSRedirect


@override_settings(APPEND_SLASH=False)
class TestRedirects(TestCase):

    def setUp(self):

        self.site = Site.objects.get_current()

        self.page = create_page(title='Hello world!',
                                # TODO we're assuming here that at least one template exists
                                # in the settings file.
                                template=settings.CMS_TEMPLATES[0][0],
                                language='en'
                                )

        self.user = User.objects.create_user('test_user', 'test@example.com', 'test_user')
        self.user.is_superuser = True
        self.user.save()

        publish_page(self.page, self.user)

    def test_301_page_redirect(self):
        r_301_page = CMSRedirect(site=self.site,
                                 page=self.page,
                                 old_path='/301_page.php')
        r_301_page.save()

        response = self.client.get('/301_page.php')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response._headers['location'][1], 'http://testserver/')

    def test_302_page_redirect(self):
        r_302_page = CMSRedirect(site=self.site,
                                 page=self.page,
                                 old_path='/302_page.php',
                                 response_code='302')
        r_302_page.save()

        response = self.client.get('/302_page.php')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1], 'http://testserver/')

    def test_301_path_redirect(self):
        r_301_path = CMSRedirect(site=self.site,
                                 new_path='/',
                                 old_path='/301_path.php')
        r_301_path.save()

        response = self.client.get('/301_path.php')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response._headers['location'][1], 'http://testserver/')

    def test_302_path_redirect(self):
        r_302_path = CMSRedirect(site=self.site,
                                 new_path='/',
                                 old_path='/302_path.php',
                                 response_code='302')
        r_302_path.save()

        response = self.client.get('/302_path.php')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1], 'http://testserver/')

    def test_410_redirect(self):
        r_410 = CMSRedirect(site=self.site,
                            old_path='/410.php',
                            response_code='302')
        r_410.save()

        response = self.client.get('/410.php')
        self.assertEqual(response.status_code, 410)

    def test_redirect_can_ignore_query_string(self):
        """
        Set up a redirect as in the generic 301 page case, but then try to get this page with
        a query string appended.  Succeed nonetheless.
        """
        r_301_page = CMSRedirect(site=self.site,
                                 page=self.page,
                                 old_path='/301_page.php')
        r_301_page.save()

        response = self.client.get('/301_page.php?this=is&a=query&string')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response._headers['location'][1], 'http://testserver/')


@override_settings(APPEND_SLASH=False)
class TestValidators(TestCase):

    """Redirects are sanity-checked before they get saved."""

    def setUp(self):

        self.site = Site.objects.get_current()

        self.page = create_page(title='Hello world!',
                                # TODO we're assuming here that at least one template exists
                                # in the settings file.
                                template=settings.CMS_TEMPLATES[0][0],
                                language='en'
                                )

        self.user = User.objects.create_user('test_user', 'test@example.com', 'test_user')
        self.user.is_superuser = True
        self.user.save()

        publish_page(self.page, self.user)

    def test_path_or_page(self):
        """The redirect target should be a path or a page."""
        redirect = CMSRedirect(site=self.site,
                               old_path='/old_path/',
                               new_path='/new_path/',
                               page=self.page)
        self.assertRaisesMessage(ValidationError,
                                 'You can redirect to either a CMS page, or to a path, but not both.',
                                 redirect.full_clean)

    def test_loop_to_path(self):
        """Avoid infinite loops."""
        redirect = CMSRedirect(site=self.site,
                               old_path='/old_path/',
                               new_path='/old_path/')
        self.assertRaisesMessage(ValidationError,
                                 'You cannot redirect back to same path.',
                                 redirect.full_clean)

    def test_loop_to_page(self):
        """Avoid infinite loops."""

        # The django-cms always sets the first page created as having path '/'.
        # This does not matter in other tests, but here we want a 'real' url so
        # the easiest thing to do is to create a second page for our test.
        self.page2 = create_page(title='Loop to page',
                                 template=settings.CMS_TEMPLATES[0][0],
                                 language='en'
                                 )
        publish_page(self.page2, self.user)

        redirect = CMSRedirect(site=self.site,
                               old_path='/loop-to-page',
                               page=self.page2)
        self.assertRaisesMessage(ValidationError,
                                 'You cannot redirect back to same path.',
                                 redirect.full_clean)

    def test_redirect_to_redirect(self):
        """A redirect cannot point to another redirect."""
        redirect1 = CMSRedirect(site=self.site,
                                old_path='/path1/',
                                new_path='/path2/')
        redirect1.save()

        redirect2 = CMSRedirect(site=self.site,
                                old_path='/path2/',
                                new_path='/path3/')
        self.assertRaisesMessage(ValidationError,
                                 'Another redirect already points to /path2/',
                                 redirect2.full_clean)

        redirect2 = CMSRedirect(site=self.site,
                                old_path='/path3/',
                                new_path='/path1/')
        self.assertRaisesMessage(ValidationError,
                                 '/path1/ would point to another redirect.',
                                 redirect2.full_clean)

    def test_not_homepage(self):
        """Do not allow admin users to redirect the site's homepage - could cause a lot of pain!"""
        redirect = CMSRedirect(site=self.site,
                               old_path='/',
                               new_path='/new_path/')
        self.assertRaisesMessage(ValidationError,
                                 "You cannot redirect the site's homepage.",
                                 redirect.full_clean)

    def test_start_slash(self):
        """The old path should always start with a slash."""
        redirect = CMSRedirect(site=self.site,
                               old_path='old_path',
                               new_path='/new_path/')
        self.assertRaisesMessage(ValidationError,
                                 "The old path should always start with a slash.",
                                 redirect.full_clean)

    def test_not_admin(self):
        """Do not allow redirecting to/from pages in the admin site."""
        admin_root = reverse('admin:index')
        redirect = CMSRedirect(site=self.site,
                               old_path=admin_root,
                               new_path='/new_path/')

        self.assertRaisesMessage(ValidationError,
                                 "You cannot redirect to or from the admin site.",
                                 redirect.full_clean)

        redirect.old_path = admin_root + 'some_page/'
        self.assertRaisesMessage(ValidationError,
                                 "You cannot redirect to or from the admin site.",
                                 redirect.full_clean)

        redirect = CMSRedirect(site=self.site,
                               old_path='/old_path/',
                               new_path=admin_root)

        self.assertRaisesMessage(ValidationError,
                                 "You cannot redirect to or from the admin site.",
                                 redirect.full_clean)

        redirect.new_path = admin_root + 'some_page/'
        self.assertRaisesMessage(ValidationError,
                                 "You cannot redirect to or from the admin site.",
                                 redirect.full_clean)
