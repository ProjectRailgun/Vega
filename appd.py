from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from .server import app

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
