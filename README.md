# wikimedia-abusefilter-accounts

Find abuse filter accounts across Wikimedia wikis. This is handy for reports and scripts that need the real local sysop list without counting these accounts as normal admins.

## Install

```bash
python3 -m pip install wikimedia-abusefilter-accounts
```

## Use it

Get the accounts from one wiki:

```python
from abusefilter_accounts import get_abuse_filter_accounts

accounts = get_abuse_filter_accounts("enwiki")["enwiki"]
```

Or get them from every open wiki:

```python
from abusefilter_accounts import get_abuse_filter_accounts

accounts = get_abuse_filter_accounts()
```

One wiki can be a db name, host, or full URL:

```python
get_abuse_filter_accounts("enwiki")
get_abuse_filter_accounts("en.wikipedia.org")
get_abuse_filter_accounts("https://en.wikipedia.org")
```

Get several wikis the same way:

```python
get_abuse_filter_accounts(["enwiki", "de.wikipedia.org", "https://fr.wikipedia.org"])
```

Use a separate MySQL option file when needed:

```python
get_abuse_filter_accounts("enwiki", cnf_file="/path/to/my.cnf")
```

## Result

The result is a dictionary keyed by wiki db name. Usernames are normal strings, and `_` is changed to a space.

```python
{
    "enwiki": ["Example Account"],
    "dewiki": [],
}
```

When no wikis are given, the package reads `meta_p.wiki` and uses the db names where `is_closed = 0`. When wikis are given, only those wikis are queried. Duplicate db names are processed once.

## Credentials

When `cnf_file` is supplied, that file is used for every database connection. Otherwise the package checks `~/replica.my.cnf` first and then `~/.my.cnf`. When neither exists, normal `toolforge.connect()` handling is used.

## How it finds them

For each wiki, the package looks for an active local `sysop` account with no revisions. These are the accounts the package treats as abuse filter accounts.
