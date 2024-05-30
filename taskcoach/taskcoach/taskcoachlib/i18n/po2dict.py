#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""Generate python dictionaries catalog from textual translation description.

This program converts a textual Uniforum-style message catalog (.po file) into
a python dictionary

Based on msgfmt.py by Martin v. Löwis <loewis@informatik.hu-berlin.de>

"""
from __future__ import print_function

from io import open
import sys
import re
import os

MESSAGES = {}
STRINGS = set()

# pylint: disable=W0602,W0603


def add(id_, string, fuzzy):
    """Add a non-fuzzy translation to the dictionary."""
    global MESSAGES
    if not fuzzy and string:
        MESSAGES[id_] = string
    STRINGS.add(id_)


def generatedict():
    """Return the generated dictionary"""
    global MESSAGES
    metadata = MESSAGES['']
    del MESSAGES['']
    encoding = re.search(r'charset=(\S*)\n', metadata).group(1)
    return "# -*- coding: %s -*-\n# This is generated code - do not edit\nencoding = '%s'\ndict = %s" % (encoding,
                                                                                                         encoding,
                                                                                                         MESSAGES)


def make(filename, outfile=None):
    ident = 1
    strin = 2
    msgid = msgstr = ""  # if not defined
    global MESSAGES
    MESSAGES = {}

    # Compute .py name from .po name and arguments
    if filename.endswith('.po'):
        infile = filename
    else:
        infile = filename + '.po'
    if outfile is None:
        outfile = os.path.splitext(infile)[0] + '.py'

    try:
        lines = open(infile, "r").readlines()
    except IOError as msg:
        print(msg, file=sys.stderr)
        sys.exit(1)

    section = None
    fuzzy = 0

    # Parse the catalog
    lno = 0
    for line in lines:
        lno += 1
        # If we get a comment line after a msgstr, this is a new entry
        if line[0] == '#' and section is strin:
            add(msgid, msgstr, fuzzy)  # pylint: disable=E0601  Local variable might be referenced before assignment
            section = None
            fuzzy = 0
        # Record a fuzzy mark
        if line[:2] == '#,' and line.find('fuzzy'):
            fuzzy = 1
        # Skip comments
        if line[0] == '#':
            continue
        # Now we are in a msgid section, output previous section
        if line.startswith('msgid'):
            if section is strin:
                add(msgid, msgstr, fuzzy)
            section = ident
            line = line[5:]
            msgid = msgstr = ''
        # Now we are in a msgstr section
        elif line.startswith('msgstr'):
            section = strin
            line = line[6:]
        # Skip empty lines
        line = line.strip()
        if not line:
            continue
        # XXX: Does this always follow Python escape semantics? # pylint: disable=W0511
        line = eval(line)
        if section == ident:
            msgid += line
        elif section == strin:
            msgstr += line
        else:
            # print >> sys.stderr, 'Syntax error on %s:%d' % (infile, lno),
            #      'before:'
            # print >> sys.stderr, line
            print('Syntax error on %s:%d' % (infile, lno),
                  'before:', file=sys.stderr)
            print(line, file=sys.stderr)
            sys.exit(1)
    # Add last entry
    if section == strin:
        add(msgid, msgstr, fuzzy)

    # Compute output
    output = bytes(generatedict(), 'utf-8')  # génération du fichier en binaire

    try:
        open(outfile, "wb").write(output)  # ! fichier binaire, utiliser des données de type bytes
    except IOError as msg:
        print(msg, file=sys.stderr)

    return outfile
