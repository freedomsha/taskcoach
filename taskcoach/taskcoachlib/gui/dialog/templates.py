"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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
"""

import wx
from taskcoachlib.domain.task import Task
from taskcoachlib import persistence, operating_system
from taskcoachlib.i18n import _
from taskcoachlib.thirdparty.deltaTime import nlTimeExpression
from wx.lib import sized_controls


class TimeExpressionEntry(wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__defaultColor = self.GetBackgroundColour()
        self.__invalidColor = wx.Colour(255, 128, 128)

        # wx.EVT_TEXT(self, wx.ID_ANY, self._onTextChanged)
        self.Bind(wx.EVT_TEXT, wx.ID_ANY, self._onTextChanged)

    @staticmethod
    def isValid(value):
        if value:
            try:
                res = nlTimeExpression.parseString(value)
            except:
                return False  # pylint: disable=W0702
            return 'calculatedTime' in res
        return True  # Empty is valid.

    def _onTextChanged(self, event):
        event.Skip()
        self.SetBackgroundColour(self.__defaultColor if self.isValid(self.GetValue()) else self.__invalidColor)


class TemplatesDialog(sized_controls.SizedDialog):
    """Cette classe implémente une boîte de dialogue pour la gestion des modèles de tâches dans l'application Task Coach.
    
    Elle permet de visualiser, modifier et supprimer des modèles de tâches existants, ainsi que d'en créer de nouveaux.

Fonctionnalités principales

    Affichage d'une liste d'arborescence pour parcourir les modèles de tâches.
    Edition des propriétés d'un modèle de tâche sélectionné (sujet, dates de début, d'échéance, d'achèvement et de rappel).
    Suppression d'un modèle de tâche sélectionné.
    Déplacement d'un modèle de tâche vers le haut ou le bas dans la liste.
    Ajout d'un nouveau modèle de tâche.
    Sauvegarde des modifications apportées aux modèles de tâches.

Classes et méthodes utilisées

    TimeExpressionEntry : Une classe dérivée de wx.TextCtrl permettant la saisie et la validation d'expressions temporelles.
    createTemplateList : Crée la liste d'arborescence pour afficher les modèles de tâches.
    createTemplateEntries : Crée les champs d'édition pour les propriétés d'un modèle de tâche.
    enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection d'un modèle.
    appendTemplate : Ajoute un modèle de tâche et ses enfants à la liste d'arborescence.
    onValueChanged : Gère les modifications apportées aux champs d'édition d'un modèle de tâche.
    OnSelectionChanged : Gère la sélection d'un modèle de tâche dans la liste, met à jour les champs d'édition et active/désactive les boutons de suppression et de déplacement.
    onDelete : Supprime le modèle de tâche sélectionné.
    OnUp : Déplace le modèle de tâche sélectionné vers le haut dans la liste.
    OnDown : Déplace le modèle de tâche sélectionné vers le bas dans la liste.
    onAdd : Ajoute un nouveau modèle de tâche vide à la liste.
    ok : Sauvegarde les modifications apportées aux modèles de tâches lors de la validation de la boîte de dialogue.
    """
    def __init__(self, settings, *args, **kwargs):
        self.settings = settings
        self._changing = False
        super().__init__(style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                         *args, **kwargs)
        pane = self.GetContentsPane()
        pane.SetSizerType('vertical')
        self.createInterior(pane)
        self._buttonSizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetButtonSizer(self._buttonSizer)
        self.Fit()
        self.SetMinSize(self.GetSize())  # Current size is min size
        self._buttonSizer.GetAffirmativeButton().bind(wx.EVT_BUTTON, self.ok)
        self.CentreOnParent()

    def createInterior(self, pane):
        self.createTemplateList(pane)
        self.createTemplateEntries(pane)

    def createTemplateList(self, pane):
        panel = sized_controls.SizedPanel(pane)
        panel.SetSizerType('horizontal')
        panel.SetSizerProps(expand=True, proportion=1)
        self._templateList = wx.TreeCtrl(panel, style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE)
        self._templateList.SetMinSize((300, 200))
        self._templateList.SetSizerProps(expand=True, proportion=1)
        self._templateList.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged)
        self._templates = persistence.TemplateList(self.settings.pathToTemplatesDir())
        self._root = self._templateList.AddRoot('Root')
        for task in self._templates.tasks():
            item = self.appendTemplate(self._root, task)
            if operating_system.isMac():
                # See http://trac.wxwidgets.org/ticket/10085
                self._templateList.SetItemText(item, task.subject())
        self.createTemplateListButtons(panel)
        panel.Fit()

    def createTemplateListButtons(self, pane):
        panel = sized_controls.SizedPanel(pane)
        panel.SetSizerType('vertical')
        self._btnDelete = self.createButton(panel, 'cross_red_icon', self.onDelete, enable=False)
        self._btnUp = self.createButton(panel, 'arrow_up_icon', self.OnUp, enable=False)
        self._btnDown = self.createButton(panel, 'arrow_down_icon', self.OnDown, enable=False)
        self._btnAdd = self.createButton(panel, 'symbol_plus_icon', self.onAdd)
        panel.Fit()

    def createButton(self, parent, bitmapName, handler, enable=True):
        bitmap = wx.ArtProvider.GetBitmap(bitmapName, size=(32, 32))
        button = wx.BitmapButton(parent, bitmap=bitmap)
        button.Bind(wx.EVT_BUTTON, handler)
        button.Enable(enable)
        return button

    def createTemplateEntries(self, pane):
        panel = self._editPanel = sized_controls.SizedPanel(pane)
        panel.SetSizerType('form')
        panel.SetSizerProps(expand=True)
        label = wx.StaticText(panel, label=_('Subject'))
        label.SetSizerProps(valign='center')
        self._subjectCtrl = wx.TextCtrl(panel)
        label = wx.StaticText(panel, label=_('Planned start Date'))
        label.SetSizerProps(valign='center')
        self._plannedStartDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_('Due Date'))
        label.SetSizerProps(valign='center')
        self._dueDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_('Completion Date'))
        label.SetSizerProps(valign='center')
        self._completionDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_('Reminder'))
        label.SetSizerProps(valign='center')
        self._reminderDateTimeCtrl = TimeExpressionEntry(panel)
        self._taskControls = (self._subjectCtrl, self._plannedStartDateTimeCtrl, self._dueDateTimeCtrl,
                              self._completionDateTimeCtrl, self._reminderDateTimeCtrl)
        for ctrl in self._taskControls:
            ctrl.SetSizerProps(valign='center', expand=True)
            ctrl.Bind(wx.EVT_TEXT, self.onValueChanged)
        self.enableEditPanel(False)
        panel.Fit()

    def enableEditPanel(self, enable=True):
        for ctrl in self._taskControls:
            ctrl.Enable(enable)

    def appendTemplate(self, parentItem, task):
        # item = self._templateList.AppendItem(parentItem, task.subject(), data=wx.TreeItemData(task))
        item = self._templateList.Append(parentItem, task.subject(), data=task)
        for child in task.children():
            self.appendTemplate(item, child)
        return item

    def onValueChanged(self, event):
        event.Skip()
        if self._GetSelection().IsOk() and not self._changing:
            task = self._templateList.GetItemData(self._GetSelection()).GetData()
            task.setSubject(self._subjectCtrl.GetValue())
            for ctrl, name in [(self._plannedStartDateTimeCtrl, 'plannedstartdatetmpl'),
                               (self._dueDateTimeCtrl, 'duedatetmpl'),
                               (self._completionDateTimeCtrl, 'completiondatetmpl'),
                               (self._reminderDateTimeCtrl, 'remindertmpl')]:
                if TimeExpressionEntry.isValid(ctrl.GetValue()):
                    setattr(task, name, ctrl.GetValue() or None)

    def _GetSelection(self):
        return self._templateList.GetSelection()

    def OnSelectionChanged(self, event):  # pylint: disable=W0613
        self._changing = True
        try:
            selection = self._GetSelection()
            selectionOk = selection.IsOk() and selection != self._root
            selectionAtRoot = False
            if selectionOk:
                selectionAtRoot = (self._templateList.GetItemParent(selection) == self._root)
            self._btnDelete.Enable(selectionAtRoot)
            self._btnUp.Enable(selectionAtRoot and self._templateList.GetPrevSibling(selection).IsOk())
            self._btnDown.Enable(selectionAtRoot and self._templateList.GetNextSibling(selection).IsOk())
            self.enableEditPanel(selectionOk)
            if selectionOk:
                task = self._templateList.GetItemData(selection).GetData()
                if task is None:
                    for ctrl in self._taskControls:
                        ctrl.SetValue(u'')
                else:
                    self._subjectCtrl.SetValue(task.subject())
                    self._plannedStartDateTimeCtrl.SetValue(task.plannedstartdatetmpl or u'')
                    self._dueDateTimeCtrl.SetValue(task.duedatetmpl or u'')
                    self._completionDateTimeCtrl.SetValue(task.completiondatetmpl or u'')
                    self._reminderDateTimeCtrl.SetValue(task.remindertmpl or u'')
            else:
                for ctrl in self._taskControls:
                    ctrl.SetValue(u'')
        finally:
            self._changing = False

    def onDelete(self, event):  # pylint: disable=W0613
        task = self._templateList.GetItemData(self._GetSelection()).GetData()
        index = self._templates.tasks().index(task)
        self._templates.deleteTemplate(index)
        self._templateList.Delete(self._GetSelection())

    def OnUp(self, event):  # pylint: disable=W0613
        selection = self._GetSelection()
        prev = self._templateList.GetPrevSibling(selection)
        prev = self._templateList.GetPrevSibling(prev)
        task = self._templateList.GetItemData(selection).GetData()
        self._templateList.Delete(selection)
        if prev.IsOk():
            # item = self._templateList.InsertItem(self._root, prev, task.subject(), data=wx.TreeItemData(task))
            item = self._templateList.InsertItem(self._root, prev, task.subject(), data=task)
        else:
            # item = self._templateList.PrependItem(self._root, task.subject(), data=wx.TreeItemData(task))
            item = self._templateList.PrependItem(self._root, task.subject(), data=task)
        for child in task.children():
            self.appendTemplate(item, child)
        index = self._templates.tasks().index(task)
        self._templates.swapTemplates(index - 1, index)
        self._templateList.SelectItem(item)

    def OnDown(self, event):  # pylint: disable=W0613
        selection = self._GetSelection()
        next = self._templateList.GetNextSibling(selection)
        task = self._templateList.GetItemData(selection).GetData()
        self._templateList.Delete(selection)
        # item = self._templateList.InsertItem(self._root, next, task.subject(), data=wx.TreeItemData(task))
        item = self._templateList.InsertItem(self._root, next, task.subject(), data=task)
        for child in task.children():
            self.appendTemplate(item, child)
        index = self._templates.tasks().index(task)
        self._templates.swapTemplates(index, index + 1)
        self._templateList.SelectItem(item)

    def onAdd(self, event):  # pylint: disable=W0613
        template = Task(subject=_('New task template'))
        for name in ('plannedstartdatetmpl', 'duedatetmpl', 'completiondatetmpl',
                     'remindertmpl'):
            setattr(template, name, None)
        theTask = self._templates.addTemplate(template)
        self.appendTemplate(self._root, theTask)

    def ok(self, event):
        self._templates.save()
        event.Skip()
