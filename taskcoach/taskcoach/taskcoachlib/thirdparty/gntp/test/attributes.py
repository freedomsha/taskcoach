#!/usr/bin/env python
# Simple manual test to make sure that attributes do not
# accumulate in the base classes
# https://github.com/kfdm/gntp/issues/10

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import gntp
import gntp.notifier

a = gntp.notifier.GrowlNotifier(notifications=['A'])
b = gntp.notifier.GrowlNotifier(notifications=['B'])

a.notify('A','A','A',sticky=True)
b.notify('B','B','B')
