import hashlib
import os
import re
import sys
import traceback
import urlparse

from . import utils
from . import tickets

def main(url):
    
    try:
    
        # Parse the URL into scheme, path, and query.
        m = re.match(r'^(?:(\w+):)?(.*?)(?:/(.*?))?(?:\?(.*))?$', url)
        scheme, netloc, path, query = m.groups()
        query = urlparse.parse_qs(query, keep_blank_values=True) if query else {}
    
        # Parse the values.
        for k, v in query.items():
            if k == 'ids' or k.endswith('_ids'):
                v[:] = [int(x) for x in v[0].split(',')] if v[0] else []
                continue
            if k.endswith('_id'):
                v[:] = [int(x) for x in v]
            if len(v) == 1 and k not in ('cols', 'column_display_names'):
                query[k] = v[0]
    
        # Parse the path into an entrypoint.
        m = re.match(r'^([\w.]+):(\w+)$', netloc)
        if not m:
            print >>sys.stderr, 'entrypoint must be like "package.module:function"'
            exit(1)
        module_name, function_name = m.groups()
    
        # Load the module, and dispatch to the function.
        module = __import__(module_name, fromlist=['.'])
        function = getattr(module, function_name)
        function(**query)
    
    except Exception, e:
        try:
            exc_uuid, ticket_id, reply_id = tickets.ticket_exception(kwargs=query)
            utils.notify(
                title='SGAction Error',
                message='%s: %s\nReplied to Ticket %d [%s].' % (type(e).__name__, e, ticket_id, exc_uuid),
                sticky=True,
            )
        except Exception, e2:
            utils.notify(
                title='SGAction Fatal Error',
                message='Error while handling error:\n%r from %r\n---\n%s' % (e2, e, traceback.format_exc()),
                sticky=True,
            )
                

if __name__ == '__main__':
    main(sys.argv[1])
    
    