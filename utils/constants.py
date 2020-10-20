# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
episode_regex_tuple = (
    u'第(\d+)話',
    u'第(\d+)话',
    u'第(\d+)集',
    u'第(\d+)回',
    u'【(\d+)(?:v\d)?(?:\s?END)?】',
    '\[(\d+)(?:v\d)?(?:\s?END)?\]',
    '\s(\d{2,})\s',
    '\s(\d+)$',
    '[.\s]Ep(\d+)[.\s]',
    '\.S\d{1,2}E(\d{1,2})\.',
    ' - (\d+) ',
)
