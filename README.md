# wikimedia-abusefilter-accounts

Find abuse filter accounts across Wikimedia wikis. This can be useful for reports and scripts that need to work with local sysop accounts without counting these accounts as regular admins.

## Install

```bash
python3 -m pip install wikimedia-abusefilter-accounts
```

## Usage

Get the accounts from one wiki:

```python
from abusefilter_accounts import get_abuse_filter_accounts

accounts = get_abuse_filter_accounts("enwiki")["enwiki"]
```

Get them from all open Wikimedia wikis:

```python
from abusefilter_accounts import get_abuse_filter_accounts

accounts = get_abuse_filter_accounts()
```

A wiki can be given as a database name, hostname, or full URL:

```python
get_abuse_filter_accounts("enwiki")
get_abuse_filter_accounts("en.wikipedia.org")
get_abuse_filter_accounts("https://en.wikipedia.org")
```

You can also pass several wikis:

```python
accounts = get_abuse_filter_accounts([
    "enwiki",
    "de.wikipedia.org",
    "https://fr.wikipedia.org",
])
```

To use a specific MySQL option file:

```python
accounts = get_abuse_filter_accounts(
    "enwiki",
    cnf_file="/path/to/my.cnf",
)
```

## Result

The result is a dictionary keyed by wiki database name:

```python
{
    "enwiki": ["Example Account"],
    "dewiki": [],
}
```

Usernames are returned as strings, with underscores replaced by spaces.

When no wikis are provided, the package checks the open wikis listed in `meta_p.wiki`. When wikis are provided, only those wikis are checked.

## Credentials

By default, the package uses the MySQL configuration available to Toolforge.

When `cnf_file` is provided, that file is used instead. Otherwise, the package checks `~/replica.my.cnf` first and then `~/.my.cnf`.

## How it works

For each wiki, the package finds active local `sysop` accounts with no recorded revisions. These are the accounts returned as abuse filter accounts.

## Limitations

This package needs access to Wikimedia replica databases, so it only works in Wikimedia environments such as Toolforge, PAWS, or Cloud VPS.

## Documentation

Full documentation is available at:

https://wikimedia-abusefilter-accounts.readthedocs.io/
