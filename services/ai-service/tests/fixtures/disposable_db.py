"""Reject test reset unless PGDATA is within one explicit tmpfs root."""
import json
import posixpath
import sys

try:
    container = json.load(sys.stdin)[0]
    mounts = container['HostConfig'].get('Tmpfs') or {}
    env = dict(item.split('=', 1) for item in container['Config']['Env'] if '=' in item)
    data = posixpath.normpath(env.get('PGDATA', ''))
    safe = any(root in mounts and (data == root or data.startswith(root + '/'))
               for root in ('/pgdata', '/var/lib/postgresql/data'))
    # Docker may omit --tmpfs entries from Mounts. Combine the declarations with
    # actual mount overlays; an explicit bind/volume at the same path wins.
    effective = {posixpath.normpath(root): 'tmpfs' for root in mounts}
    effective.update({posixpath.normpath(mount['Destination']): mount['Type']
                      for mount in container['Mounts']})
    actual = list(effective.items())
    covering = [(destination, kind) for destination, kind in actual
                if data == destination or data.startswith(destination + '/')]
    safe = safe and bool(covering) and max(covering, key=lambda item: len(item[0]))[1] == 'tmpfs'
    safe = safe and not any(kind != 'tmpfs' and destination.startswith(data + '/')
                            for destination, kind in actual)
except (ValueError, KeyError, TypeError, IndexError):
    safe = False
sys.exit(0 if safe else 1)
