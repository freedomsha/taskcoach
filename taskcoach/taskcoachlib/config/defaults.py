'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, wx
from taskcoachlib import meta


defaults = { \
'view': { \
    'statusbar': 'True',
    'toolbar': '(22, 22)',
    'mainviewer': '0',               # Index of active viewer in main window
    'effortviewerintaskeditor': '0', # Index of active effort viewer in task editor
    'tasktreelistviewercount': '1',  # Number of task tree list viewers in main window
    'categoryviewercount': '1',      # Number of category viewers in main window
    'noteviewercount': '0',          # Number of note viewers in main window
    'effortlistviewercount': '0',    # Number of effort viewers in main window
    'language': 'en_US',
    'categoryfiltermatchall': 'False',
    'descriptionpopups': 'True',
    # The next three options are used in the effort dialog to populate the
    # drop down menu with start and stop times.
    'efforthourstart': '8',          # Earliest time, i.e. start of working day
    'efforthourend': '18',           # Last time, i.e. end of working day
    'effortminuteinterval': '15',    # Generate times with this interval
    'perspective': '',               # The layout of the viewers in the main window
    'tabbedmainwindow': 'False'},
'tasktreelistviewer': { \
    'title': '',
    'treemode': 'True',
    'sortby': 'dueDate',
    'sortascending': 'True',
    'sortbystatusfirst': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'columns': "['startDate', 'dueDate']",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28}",
    'columnautoresizing': 'True',
    'tasksdue': 'Unlimited',
    'hidecompletedtasks': 'False',
    'hideinactivetasks': 'False',
    'hideactivetasks': 'False',
    'hideoverduetasks': 'False',
    'hideoverbudgettasks': 'False',
    'hidecompositetasks': 'False' },
'categoryviewer': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False' },
'noteviewer': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28}",
    'columnautoresizing': 'True' },
'noteviewerintaskeditor': {
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'columns': "['subject']",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False' },
'effortlistviewer': { \
    'title': '',
    'aggregation': 'details', # 'details' (default), 'day', 'week', or 'month'
    'columns': "['timeSpent', 'revenue']",
    'columnsalwaysvisible': "['period', 'task']",
    'columnwidths': "{}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False' },
'effortviewerintaskeditor': { \
    'aggregation': 'details', # 'details' (default), 'day', 'week', or 'month'
    'columns': "['timeSpent', 'revenue']",
    'columnsalwaysvisible': "['period', 'task']",
    'columnwidths': "{}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False' },
'window': { \
    'size': '(700, 500)', # Default size of the main window
    'position': '(-1, -1)', # Position of the main window, undefined by default
    'iconized': 'False', # Don't start up iconized by default
    'maximized': 'False', # Don't start up maximized by default
    'starticonized': 'WhenClosedIconized', # 'Never', 'Always', 'WhenClosedIconized'
    'splash': 'True', # Show a splash screen while starting up
    'hidewheniconized': 'False', # Don't hide the window from the task bar
    'hidewhenclosed': 'False', # Close window quits the application
    'tips': 'True', # Show tips after starting up
    'tipsindex': '0', # Start at the first tip
    'blinktaskbariconwhentrackingeffort': 'True' },
'file': { \
    'recentfiles': '[]',
    'maxrecentfiles': '4',
    'lastfile': '',
    'autosave': 'False',
    'backup': 'False',
    'saveinifileinprogramdir': 'False',
    'attachmentbase': '' },
'color': { \
    'activetasks': '(0, 0, 0)',
    'completedtasks': '(0, 255, 0)',
    'overduetasks': '(255, 0, 0)',
    'inactivetasks': '(192, 192, 192)',
    'duetodaytasks': '(255, 128, 0)' },
'editor': { \
    'maccheckspelling': 'True' },
'version': { \
    'python': '', # Filled in by the Settings class when saving the settings
    'wxpython': '', # Idem
    'pythonfrozen': '', # Idem
    'current': meta.data.version,
    'notified': meta.data.version,
    'notify': 'True' },
'behavior': { \
    'markparentcompletedwhenallchildrencompleted': 'True' },
'feature': { \
    'notes': 'True' }}

minimum = { \
'view': { \
    'tasktreelistviewercount': '1' }
}
