from psycogreen.gevent import patch_psycopg; patch_psycopg(); del patch_psycopg
from gevent.monkey import patch_all; patch_all(); del patch_all
from server import app as application
