``django-deployment`` is a very simple way for you create the files needed to
deploy your project with apache (or with template mods, any mod_wsgi platform)

Requirements
============

``django-deployment`` requires Django 1.0 or later.  The application is intended
work with any versions of the Django framework, but has only been tested with
1.4 and above.

Installation
============

Download ``django-deployment`` using **one** of the following methods:

easy_install
------------

You can download the package from the `CheeseShop <http://pypi.python.org/pypi/django-deployment/>`_ or use::

    easy_install django-deployment

to download and install ``django-deployment``.

Package Download
----------------

Download the latest ``.tar.gz`` file from the downloads section and extract it
somewhere you'll remember.  Use ``python setup.py install`` to install it.

Checkout from GitHub
--------------------

Execute the following command, and make sure you're checking ``django-deployment``
out somewhere on the ``PYTHONPATH``::

    git clone git://github.com/mark0978/django-deployment.git

Verifying Installation
----------------------

The easiest way to ensure that you have successfully installed ``django-deployment``
is to execute a command such as::

    python -c "import deployment; print deployment.get_version()"

If that command completes with some sort of version number, you're probably
good to go.  If you see error output, you need to check your installation (I'd
start with your ``PYTHONPATH``).

Configuration
=============

First of all, you must add this project to your list of ``INSTALLED_APPS`` in
``settings.py``::

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        ...
        'deployment',
        ...
    )

Next, install make sure that your have a PROJECT_ROOT in your settings.py file
PROJECT_ROOT should point at the root of the project, not the root of the
virtualenv, although thru the templated output, you can control where production
static files come from.  For a typical 1.4 Django install, it would look
something like this:

import os
PROJECT_ROOT = os.path.abspath(os.path.split(os.path.dirname(__file__))[0])


Customizing deployment
----------------

All of the output is written into the PROJECT_ROOT/deploy folder using templates
in the deployment folder.  If you want to modify the templates, I'd recommend
copying the originals from the app templates folder into your own project
templates folder and making the changes there.  That way you get your templates
under your source control.
