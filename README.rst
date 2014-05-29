django-cms-redirects
=================
A django app that lets you store simple redirects in a database and handles the redirecting for you.  Integrated with Django CMS to allow you to link directly to a page object.  Based off django.contrib.redirects.

Dependancies
============

- django
- django-cms

Getting Started
=============

To get started simply install using ``pip``:
::
    pip install django-cms-redirects

Add the following to your installed apps:

::
	INSTALLED_APPS = (
		...
	    'cms',
	    'cms_redirects',
        'taggit',
        'taggit_autosuggest',
	)

If you are using South (rather than Django 1.7s built-in migration system), you should add this setting:

::
    SOUTH_MIGRATION_MODULES = {
        'taggit': 'taggit.south_migrations',
    }

Run a ``python manage.py migrate``.

Add 'cms_redirects.middleware.RedirectFallbackMiddleware' to your MIDDLEWARE_CLASSES setting.

Add the following line to your project's urls.py file:

::
	(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),

Usage
=============

All usage is done through the admin.

Providing a ``redirect from`` value for the source and either a ``redirect to`` or a ``page`` for the destination will result in a 301 redirect

Providing a ``redirect from`` value for the source and NO destination will result in a 410



