'''
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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

import wx
from taskcoachlib.i18n import _


class KeychainPasswordWidget(wx.Dialog):
    def __init__(self, domain, username, *args, **kwargs):
        super(KeychainPasswordWidget, self).__init__(*args, **kwargs)

        self.domain = domain
        self.username = username

        pnl = wx.Panel(self, wx.ID_ANY)
        hsz = wx.BoxSizer(wx.HORIZONTAL)
        hsz.Add(wx.StaticText(pnl, wx.ID_ANY, _('Password:')), 0, wx.ALL, 3)

        from taskcoachlib.thirdparty.keyring import get_password
        password = get_password(domain, username)
        self.password = (password or '').decode('UTF-8')
        self.passwordField = wx.TextCtrl(pnl, wx.ID_ANY, self.password, style=wx.TE_PASSWORD)
        hsz.Add(self.passwordField, 1, wx.ALL, 3)

        vsz = wx.BoxSizer(wx.VERTICAL)
        vsz.Add(hsz, 0, wx.ALL|wx.EXPAND, 3)
        self.keepInKeychain = wx.CheckBox(pnl, wx.ID_ANY, _('Store in keychain'))
        self.keepInKeychain.SetValue(bool(password))
        vsz.Add(self.keepInKeychain, 0, wx.ALL|wx.EXPAND, 3)

        hsz = wx.BoxSizer(wx.HORIZONTAL)
        btnOK = wx.Button(pnl, wx.ID_ANY, _('OK'))
        hsz.Add(btnOK, 0, wx.ALL, 3)
        btnCancel = wx.Button(pnl, wx.ID_ANY, _('Cancel'))
        hsz.Add(btnCancel, 0, wx.ALL, 3)
        vsz.Add(hsz, 0, wx.ALL|wx.ALIGN_CENTRE, 3)

        pnl.SetSizer(vsz)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(pnl, 1, wx.EXPAND|wx.ALL, 3)
        self.SetSizer(sz)
        self.Fit()

        wx.EVT_BUTTON(btnOK, wx.ID_ANY, self.OnOK)
        wx.EVT_BUTTON(btnCancel, wx.ID_ANY, self.OnCancel)

        self.SetDefaultItem(btnOK)

    def OnOK(self, event):
        self.password = self.passwordField.GetValue()
        from taskcoachlib.thirdparty.keyring import set_password
        if self.keepInKeychain.GetValue():
            set_password(self.domain, self.username, self.password.encode('UTF-8'))
        else:
            set_password(self.domain, self.username, '')
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)


def GetPassword(domain, username, reset=False):
    try:
        from taskcoachlib.thirdparty.keyring import set_password
    except:
        # Keychain unavailable.
        return wx.GetPasswordFromUser(_('Please enter your password.'), domain) or None

    if reset:
        set_password(domain, username, '')

    dlg = KeychainPasswordWidget(domain, username, None, wx.ID_ANY, _('Please enter your password'))
    try:
        dlg.CentreOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.password
    finally:
        dlg.Destroy()