Usage
=====

Installation
------------

Install the package from PyPI:

.. code-block:: console

   python3 -m pip install wikimedia-abusefilter-accounts

Basic usage
-----------

Get the accounts from one wiki:

.. code-block:: python

   from abusefilter_accounts import get_abuse_filter_accounts

   accounts = get_abuse_filter_accounts("enwiki")["enwiki"]

To check all open Wikimedia wikis:

.. code-block:: python

   accounts = get_abuse_filter_accounts()

The result is a dictionary keyed by wiki database name. Usernames are returned as strings with underscores replaced by spaces.

Selecting wikis
---------------

A wiki can be specified by its database name, hostname, or full URL:

.. code-block:: python

   get_abuse_filter_accounts("enwiki")
   get_abuse_filter_accounts("en.wikipedia.org")
   get_abuse_filter_accounts("https://en.wikipedia.org")

Several wikis can be passed at once:

.. code-block:: python

   accounts = get_abuse_filter_accounts([
       "enwiki",
       "de.wikipedia.org",
       "https://fr.wikipedia.org",
   ])

When no wikis are specified, the package checks the open wikis listed in
``meta_p.wiki``. When wikis are specified explicitly, only those wikis are checked.

Credentials
-----------

By default, the package uses the Toolforge MySQL configuration available in the environment.

To use a specific MySQL option file:

.. code-block:: python

   accounts = get_abuse_filter_accounts(
       "enwiki",
       cnf_file="/path/to/my.cnf",
   )

Example result
--------------

For example:

.. code-block:: python

   {
       "enwiki": ["Example Account"],
       "dewiki": [],
   }

The package identifies local sysop accounts that have no recorded revisions.
These are the accounts returned as abuse filter accounts.
