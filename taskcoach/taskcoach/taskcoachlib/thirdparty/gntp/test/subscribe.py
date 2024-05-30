# -*- coding: utf-8 -*-
# Simple script to test sending UTF8 text with the GrowlNotifier class
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
logging.basicConfig(level=logging.DEBUG)
from gntp.notifier import GrowlNotifier
import platform

growl = GrowlNotifier(notifications=['Testing'],password='password',hostname='ayu')
growl.subscribe(platform.node(),platform.node(),12345)
