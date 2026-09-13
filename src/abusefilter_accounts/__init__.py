"""find abuse filter accounts on Wikimedia wikis."""

__version__ = "0.1.0"
__all__ = ["get_abuse_filter_accounts"]

import os
from pathlib import Path
from typing import Iterable, Optional, Union

import toolforge


_OPEN_WIKIS_QUERY = "SELECT dbname FROM wiki WHERE is_closed = 0 ORDER BY dbname"

_ABUSE_FILTER_ACCOUNTS_QUERY = """
SELECT u.user_name
FROM user_groups ug
JOIN user u ON ug.ug_user = u.user_id
WHERE ug.ug_group = 'sysop'
AND (ug.ug_expiry IS NULL OR ug.ug_expiry > DATE_FORMAT(UTC_TIMESTAMP(), '%Y%m%d%H%i%s'))
AND NOT EXISTS (
    SELECT 1
    FROM revision_userindex r
    JOIN actor a ON r.rev_actor = a.actor_id
    WHERE a.actor_user = u.user_id
)
ORDER BY u.user_name
"""


def get_abuse_filter_accounts(
    wikis: Optional[Union[str, Iterable[str]]] = None,
    cnf_file: Optional[Union[str, os.PathLike[str]]] = None,
) -> dict[str, list[str]]:
    """find abuse filter accounts on selected Wikimedia wikis.

    :param wikis: one wiki db name, host, or url; an iterable of them; or none for all open wikis.
    :param cnf_file: mysql option file to use instead of the default credential files.
    :return: a dictionary mapping each processed wiki db name to matching account names.
    """
    if cnf_file is not None:
        read_default_file = str(Path(cnf_file).expanduser())
        if not os.path.isfile(read_default_file):
            raise FileNotFoundError(read_default_file)
    elif os.path.isfile(os.path.expanduser("~/replica.my.cnf")):
        read_default_file = os.path.expanduser("~/replica.my.cnf")
    elif os.path.isfile(os.path.expanduser("~/.my.cnf")):
        read_default_file = os.path.expanduser("~/.my.cnf")
    else:
        read_default_file = None

    connection_options = {"read_default_file": read_default_file} if read_default_file else {}

    if wikis is None:
        conn = toolforge.connect("meta_p", **connection_options)
        try:
            with conn.cursor() as cur:
                cur.execute(_OPEN_WIKIS_QUERY)
                wikis = [row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0] for row in cur.fetchall()]
        finally:
            conn.close()
    elif isinstance(wikis, str):
        wikis = [wikis]
    elif isinstance(wikis, (bytes, bytearray)):
        raise TypeError("wikis must contain wiki db names, hosts, or urls as strings")

    db_names = []
    for wiki in wikis:
        if not isinstance(wiki, str):
            raise TypeError("wikis must contain wiki db names, hosts, or urls as strings")
        wiki = wiki.strip()
        if not wiki:
            raise ValueError("wiki names, hosts, and urls cannot be empty")
        try:
            dbname = toolforge.dbname(wiki)
        except toolforge.UnknownDatabaseError:
            if any(value in wiki for value in (".", "/", ":")):
                raise
            dbname = wiki
        if dbname not in db_names:
            db_names.append(dbname)

    results = {}

    for dbname in db_names:
        conn = toolforge.connect(dbname, **connection_options)
        try:
            with conn.cursor() as cur:
                cur.execute(_ABUSE_FILTER_ACCOUNTS_QUERY)
                results[dbname] = [
                    (row[0].decode("utf-8") if isinstance(row[0], bytes) else row[0]).replace("_", " ")
                    for row in cur.fetchall()
                ]
        finally:
            conn.close()

    return results
