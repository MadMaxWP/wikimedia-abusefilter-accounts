Usage
=====

Installation
------------

Install the package from PyPI:

.. code-block:: console

   python3 -m pip install wikimedia-abusefilter-accounts

Using it
--------

The common case is just two lines:

.. code-block:: python

   from abusefilter_accounts import get_abuse_filter_accounts
   accounts = get_abuse_filter_accounts("enwiki")["enwiki"]

``accounts`` is a list of matching usernames.

Get matching accounts from every open wiki:

.. code-block:: python

   from abusefilter_accounts import get_abuse_filter_accounts
   accounts = get_abuse_filter_accounts()

One wiki can be a db name, host, or full URL:

.. code-block:: python

   get_abuse_filter_accounts("enwiki")
   get_abuse_filter_accounts("en.wikipedia.org")
   get_abuse_filter_accounts("https://en.wikipedia.org")

Get several wikis the same way:

.. code-block:: python

   get_abuse_filter_accounts(["enwiki", "de.wikipedia.org", "https://fr.wikipedia.org"])

Use a separate MySQL option file when needed:

.. code-block:: python

   get_abuse_filter_accounts("enwiki", cnf_file="/path/to/my.cnf")

Result
------

The result is a dictionary keyed by wiki db name. Usernames are returned as normal strings, and `_` is changed to a space.

.. code-block:: python

   {
       "enwiki": ["Example Account"],
       "dewiki": [],
   }

Wiki selection
--------------

When ``wikis`` is omitted, the package reads ``meta_p.wiki`` and uses the db names where ``is_closed = 0``.

When ``wikis`` is one string, it selects one wiki. An iterable selects several. Each item can be a db name, a host, or a full wiki URL.

When wikis are passed explicitly, only those wikis are queried. Duplicate db names are processed once.

Credentials
-----------

When ``cnf_file`` is supplied, that MySQL option file is used for every connection. Otherwise the package checks ``~/replica.my.cnf`` first and then ``~/.my.cnf``. When neither exists, normal ``toolforge.connect()`` handling is used.

How it finds them
------------------

For each wiki, the package looks for an active local ``sysop`` account with no revisions. Those are the accounts this package treats as abuse filter accounts.

Connections
-----------

Only one wiki database connection is used at a time. The cursor is closed when its query is finished, and the connection is closed before the next wiki is processed.
