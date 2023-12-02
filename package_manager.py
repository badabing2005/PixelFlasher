#!/usr/bin/env python

import gettext
import json
import math
import time

import pyperclip
import darkdetect
import traceback
import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from runtime import *

from datetime import datetime, timedelta

_ = gettext.gettext

# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


# ============================================================================
#                               Class SuPermissionDialog
# ============================================================================
class SuPermissionDialog(wx.Dialog):
    def __init__(self, parent, pkg, uid, label=None):
        super().__init__(parent, title=_("Set SU Permission"))
        self.pkg = pkg
        self.uid = uid

        # Label
        if label is not None:
            label_text = wx.StaticText(self, label=label)
        else:
            label_text = wx.StaticText(self, label=_("Enter SU Permission details:"))
        font = label_text.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label_text.SetFont(font)

        # Checkbox for notification
        self.notification_checkbox = wx.CheckBox(self, label=_("Enable Notification"))

        # Checkbox for logging
        self.logging_checkbox = wx.CheckBox(self, label=_("Enable Logging"))

        # Dropdown for Until
        until_choices = [_('Forever'), _('10 mins'), _('20 mins'), _('30 mins'), _('60 mins')]
        self.until_dropdown = wx.ComboBox(self, choices=until_choices, style=wx.CB_DROPDOWN| wx.CB_READONLY)
        # Set "Forever" as the default selection
        self.until_dropdown.SetSelection(0)

        # Buttons
        allow_button = wx.Button(self, label=_("Allow"))
        deny_button = wx.Button(self, label=_("Deny"))
        revoke_button = wx.Button(self, label=_("Revoke"))
        cancel_button = wx.Button(self, label=_("Cancel"))

        # Bind buttons to functions
        allow_button.Bind(wx.EVT_BUTTON, self.OnAllow)
        deny_button.Bind(wx.EVT_BUTTON, self.OnDeny)
        revoke_button.Bind(wx.EVT_BUTTON, self.OnRevoke)
        cancel_button.Bind(wx.EVT_BUTTON, self.OnCancel)

        # Sizer to arrange the elements
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label_text, 0, wx.ALL, 10)
        sizer.Add(self.notification_checkbox, 0, wx.ALL, 10)
        sizer.Add(self.logging_checkbox, 0, wx.ALL, 10)
        sizer.Add(self.until_dropdown, 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(allow_button, 0, wx.ALL, 10)
        button_sizer.Add(deny_button, 0, wx.ALL, 10)
        button_sizer.Add(revoke_button, 0, wx.ALL, 10)
        button_sizer.Add(cancel_button, 0, wx.ALL, 10)

        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(sizer)

    def OnAllow(self, event):
        until_text = self.until_dropdown.GetValue()
        until = self.ComputeEpoch(until_text)
        notification = self.notification_checkbox.GetValue()
        logging = self.logging_checkbox.GetValue()
        print(_(f"Allow button clicked. Until: %s, Notification: %s, Logging: %s, Epoch: %s") % (until_text, notification, logging, until))
        device = get_phone()
        device.magisk_update_su(uid=self.uid, policy='allow', logging=logging, notification=notification, until=until)
        self.EndModal(wx.ID_CANCEL)

    def OnDeny(self, event):
        until_text = self.until_dropdown.GetValue()
        until = self.ComputeEpoch(until_text)
        notification = self.notification_checkbox.GetValue()
        logging = self.logging_checkbox.GetValue()
        print(_(f"Deny button clicked. Until:  %s, Notification: %s, Logging: %s, Epoch: %s") % (until_text, notification, logging, until))
        device = get_phone()
        device.magisk_update_su(uid=self.uid, policy='deny', logging=logging, notification=notification, until=until)
        self.EndModal(wx.ID_CANCEL)

    def OnRevoke(self, event):
        until_text = _('Revoke')
        until = self.ComputeEpoch(until_text)
        print(_(f"Revoke button clicked. Until: %s, Notification: 1, Logging: 1, Epoch: %s") % (until_text, until))
        device = get_phone()
        device.magisk_update_su(uid=self.uid, policy='deny', logging=1, notification=1, until=until)
        self.EndModal(wx.ID_CANCEL)

    def OnCancel(self, event):
        print(_("Cancel button clicked"))
        self.EndModal(wx.ID_CANCEL)

    def ComputeEpoch(self, until):
        # Compute the epoch value based on the 'until' dropdown choice
        now = datetime.now()
        if until == _('Forever'):
            return 0
        elif until == _('10 mins'):
            future = now + timedelta(minutes=10)
        elif until == _('20 mins'):
            future = now + timedelta(minutes=20)
        elif until == _('30 mins'):
            future = now + timedelta(minutes=30)
        elif until == _('60 mins'):
            future = now + timedelta(minutes=60)
        elif until == _('Revoke'):
            future = now - timedelta(minutes=1)
        else:
            return 0

        return int(future.timestamp())


# ============================================================================
#                               Class PackageManager
# ============================================================================
class PackageManager(wx.Dialog, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs, style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle(_("Manage Packages on the Device"))
        self.package_count = 0
        self.all_cb_clicked = False
        self.device = get_phone()
        self.download_folder = None
        self.abort = False
        res = self.device.get_detailed_packages()
        if res == 0:
            self.packages = self.device.packages
            self.package_count = len(self.packages)
            #items = self.device.packages.items()
        else:
            self.packages = {}
            self.package_count = 0

        if not self.device:
            print(_(f"\n%s ERROR: You must first select a valid device.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return -1

        splitter = wx.SplitterWindow(self, -1)
        splitter.SetMinimumPaneSize(400)
        panel1 = wx.Panel(splitter, -1)
        panel2 = wx.Panel(splitter, -1)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(splitter, 1, wx.EXPAND)

        vSizer1 = wx.BoxSizer(wx.VERTICAL)
        vSizer2 = wx.BoxSizer(wx.VERTICAL)

        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.message_label = wx.StaticText(panel1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = _(f"%s Packages") % self.package_count
        self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.searchCtrl = wx.SearchCtrl(panel1, style=wx.TE_PROCESS_ENTER)
        self.searchCtrl.ShowCancelButton(True)

        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer1.Add(message_sizer, 0, wx.EXPAND, 5)

        hSizer1 = wx.BoxSizer( wx.HORIZONTAL )
        self.all_checkbox = wx.CheckBox(panel1, wx.ID_ANY, _(u"Check / Uncheck All"), wx.DefaultPosition, wx.DefaultSize, style=wx.CHK_3STATE)

        self.button_get_names = wx.Button( panel1, wx.ID_ANY, _(u"Get All Application Names"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.button_get_names.SetToolTip(_(u"Extracts App names, and caches them for faster loading in the future.\nNOTE: This could take a while."))
        hSizer1.Add( (10, 0), 0, wx.EXPAND, 5 )
        hSizer1.Add(self.all_checkbox, 0, wx.EXPAND, 5)
        hSizer1.Add( (0, 0), 1, wx.EXPAND, 5 )
        hSizer1.Add(self.searchCtrl, 1, wx.EXPAND)
        hSizer1.Add( (0, 0), 1, wx.EXPAND, 5 )
        hSizer1.Add( self.button_get_names, 0, wx.RIGHT, 28 )
        vSizer1.Add(hSizer1, 0, wx.EXPAND, 5)

        self.il = wx.ImageList(16, 16)

        self.idx1 = self.il.Add(images.official_16.GetBitmap())
        self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())

        self.list  = ListCtrl(panel1, -1, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLACK'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.EnableCheckBoxes(enable=True)
        listmix.ColumnSorterMixin.__init__(self, 8)

        vSizer1.Add(self.list , 1, wx.ALL|wx.EXPAND, 5)

        panel1.SetSizer(vSizer1)
        panel1.Layout()
        panel1.Centre(wx.BOTH)

        # Panel 2
        self.details = wx.TextCtrl(panel2, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL, size=(-1, -1))
        if sys.platform == "win32":
            self.details.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))

        vSizer2.Add(self.details , 1, wx.EXPAND, 5)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        self.disable_button = wx.Button(panel2, wx.ID_ANY, _(u"Disable"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_button.SetToolTip(_(u"Disable checked packages"))
        self.disable_button.Enable(False)
        buttons_sizer.Add(self.disable_button, 0, wx.ALL, 20)

        self.enable_button = wx.Button(panel2, wx.ID_ANY, _(u"Enable"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_button.SetToolTip(_(u"Enable checked packages"))
        self.enable_button.Enable(False)
        buttons_sizer.Add(self.enable_button, 0, wx.ALL, 20)

        self.uninstall_button = wx.Button(panel2, wx.ID_ANY, _(u"Uninstall"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.uninstall_button.SetToolTip(_(u"Uninstall checked packages"))
        self.uninstall_button.Enable(False)
        buttons_sizer.Add(self.uninstall_button, 0, wx.ALL, 20)

        self.add_to_deny_button = wx.Button(panel2, wx.ID_ANY, _(u"Add to Denylist"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.add_to_deny_button.SetToolTip(_(u"Add package to Magisk Denylist"))
        self.add_to_deny_button.Enable(False)
        buttons_sizer.Add(self.add_to_deny_button, 0, wx.ALL, 20)

        self.rm_from_deny_button = wx.Button(panel2, wx.ID_ANY, _(u"Remove from Denylist"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.rm_from_deny_button.SetToolTip(_(u"Remove package from Magisk Denylist"))
        self.rm_from_deny_button.Enable(False)
        buttons_sizer.Add(self.rm_from_deny_button, 0, wx.ALL, 20)

        self.install_apk_button = wx.Button(panel2, wx.ID_ANY, _(u"Install APK"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_apk_button.SetToolTip(_(u"Install an APK on the device"))
        buttons_sizer.Add(self.install_apk_button, 0, wx.ALL, 20)

        self.bulk_install_apk_button = wx.Button(panel2, wx.ID_ANY, _(u"Bulk Install APK"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.bulk_install_apk_button.SetToolTip(_(u"Bulk Install APKs by selecting a folder."))
        buttons_sizer.Add(self.bulk_install_apk_button, 0, wx.ALL, 20)

        self.download_apk_button = wx.Button(panel2, wx.ID_ANY, _(u"Download APK"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.download_apk_button.SetToolTip(_(u"Extract and download APK"))
        self.download_apk_button.Enable(False)
        buttons_sizer.Add(self.download_apk_button, 0, wx.ALL, 20)

        self.export_list_button = wx.Button(panel2, wx.ID_ANY, _(u"Export List"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.export_list_button.SetToolTip(_(u"Export the package list in CSV format"))
        buttons_sizer.Add(self.export_list_button, 0, wx.ALL, 20)

        self.close_button = wx.Button(panel2, wx.ID_ANY, _(u"Close"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.close_button.SetToolTip(_(u"Closes this dialog"))
        buttons_sizer.Add(self.close_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer2.Add(buttons_sizer, 0, wx.EXPAND, 5)

        panel2.SetSizer(vSizer2)
        panel2.Layout()
        panel2.Centre(wx.BOTH)

        splitter.SplitHorizontally(panel1, panel2)

        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        self.SetSize(vSizer.MinSize.Width + 80, vSizer.MinSize.Height + 620)

        # Connect Events
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.button_get_names.Bind(wx.EVT_BUTTON, self.OnGetAllNames)
        self.disable_button.Bind(wx.EVT_BUTTON, self.OnDisable)
        self.enable_button.Bind(wx.EVT_BUTTON, self.OnEnable)
        self.uninstall_button.Bind(wx.EVT_BUTTON, self.OnUninstall)
        self.add_to_deny_button.Bind(wx.EVT_BUTTON, self.OnAddToDeny)
        self.rm_from_deny_button.Bind(wx.EVT_BUTTON, self.OnRmFromDeny)
        self.install_apk_button.Bind(wx.EVT_BUTTON, self.OnInstallApk)
        self.bulk_install_apk_button.Bind(wx.EVT_BUTTON, self.OnBulkInstallApk)
        self.download_apk_button.Bind(wx.EVT_BUTTON, self.OnDownloadApk)
        self.export_list_button.Bind(wx.EVT_BUTTON, self.OnExportList)
        self.close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.list.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnItemCheck)
        self.list.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnItemUncheck)
        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)
        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        self.all_checkbox.Bind(wx.EVT_CHECKBOX, self.OnAllCheckbox)

        self.Refresh()

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self):
        info = wx.ListItem()
        info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.Image = -1
        info.Align = 0
        info.Width = -1
        info.SetWidth(-1)
        info.Text = _("Package")
        self.list.InsertColumn(0, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("Type")
        self.list.InsertColumn(1, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("Installed")
        self.list.InsertColumn(2, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("Enabled")
        self.list.InsertColumn(3, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("User 0")
        self.list.InsertColumn(4, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("Denylist")
        self.list.InsertColumn(5, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("UID")
        self.list.InsertColumn(6, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = _("Name")
        self.list.InsertColumn(7, info)

        itemDataMap = {}
        query = self.searchCtrl.GetValue().lower()
        if self.packages:
            i = 0
            items = self.packages.items()
            for key, data in items:
                alltext = f"{key.lower()} {str(data.label.lower())}"
                if query.lower() in alltext:
                    index = self.list.InsertItem(self.list.GetItemCount(), key)
                    if data.type:
                        itemDataMap[i + 1] = (key, data.type, data.installed, data.enabled, data.user0, data.magisk_denylist, data.uid, data.label)
                        row = self.list.GetItem(index)
                        self.list.SetItem(index, 1, data.type)
                        self.list.SetItem(index, 2, str(data.installed))
                        self.list.SetItem(index, 3, str(data.enabled))
                        self.list.SetItem(index, 4, str(data.user0))
                        self.list.SetItem(index, 5, str(data.magisk_denylist))
                        self.list.SetItem(index, 6, str(data.uid))
                        self.list.SetItem(index, 7, str(data.label))
                        if data.type == 'System':
                            row.SetTextColour(wx.RED)
                        elif darkdetect.isLight():
                            row.SetTextColour(wx.BLUE)
                        else:
                            row.SetTextColour(wx.CYAN)
                        if not data.enabled:
                            row.SetTextColour(wx.LIGHT_GREY)
                        self.list.SetItem(row)
                        self.list.SetItemData(index, i + 1)
                    # hide image
                    self.list.SetItemColumnImage(i, 0, -1)
                    i += 1
            res = self.device.push_aapt2()
            self.message_label.Label = _(f"%s / %s Packages") % (str(i), self.package_count)
        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 2, 20)
        self.list.SetColumnWidth(3, -2)
        grow_column(self.list, 3, 20)
        self.list.SetColumnWidth(4, -2)
        grow_column(self.list, 4, 20)
        self.list.SetColumnWidth(5, -2)
        grow_column(self.list, 5, 20)
        self.list.SetColumnWidth(6, -2)
        grow_column(self.list, 6, 20)
        self.list.SetColumnWidth(7, 200)
        grow_column(self.list, 7, 20)

        self.currentItem = 0
        if itemDataMap:
            return itemDataMap
        else:
            return -1

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
        col = event.GetColumn()
        if col == -1:
            return # clicked outside any column.
        rowid = self.list.GetColumn(col)
        print(_(f"Sorting on Column %s") % rowid.GetText())
        event.Skip()

    # -----------------------------------------------
    #          Function GetPackageDetails
    # -----------------------------------------------
    def GetPackageDetails(self, pkg, skip_details = False, ):
        package = self.packages[pkg]
        labels = get_labels()
        if package.details == '':
            package.details, package.path2 = self.device.get_package_details(pkg)
        elif package.path2 == '':
            package.path2 = self.device.get_path_from_details(package.details)
        path = package.path or package.path2
        if package.label == '':
            if path == '':
                path = self.device.get_package_path(pkg, False)
                if path != -1:
                    package.path = path
            label, icon = self.device.get_package_label(pkg, path)
            if label != -1:
                package.label = label
                package.icon = icon
                self.list.SetItem(self.currentItem, 7, label)
                row_as_list = list(self.itemDataMap[self.currentItem + 1])
                row_as_list[7] = label
                self.itemDataMap[self.currentItem + 1] = row_as_list
                labels[pkg] = label
                set_labels(labels)
        if not skip_details:
            path = package.path or package.path2
            self.details.SetValue(_(f"Application Name: %s\nApplication Path: %s\nApplication Icon: %s\n\n%s") % (package.label, path, package.icon, package.details))

    # -----------------------------------------------
    #              Function Check_UncheckAll
    # -----------------------------------------------
    def Check_UncheckAll(self, state):
        # Set this so that we skip processing OnItemChecked, OnItemUnchecked events
        self.Set_all_cb_clicked (True)
        itemcount = self.list.GetItemCount()
        [self.list.CheckItem(item=i, check=state) for i in range(itemcount)]
        if state:
            print(_("checking all Packages\n"))
            self.EnableDisableButton(True)
        else:
            print(_("Unchecking all Packages\n"))
            self.EnableDisableButton(False)
        self.Set_all_cb_clicked (False)

    # -----------------------------------------------
    #                  onSearch
    # -----------------------------------------------
    def OnSearch(self, event):
        query = self.searchCtrl.GetValue()
        print(_(f"Searching for: %s") % query)
        self.Refresh()

    # -----------------------------------------------
    #                  onCancel
    # -----------------------------------------------
    def OnCancel(self, event):
        self.searchCtrl.SetValue("")
        self.Refresh()

    # -----------------------------------------------
    #                  OnAllCheckbox
    # -----------------------------------------------
    def OnAllCheckbox(self, event):
        cb = event.GetEventObject()
        # print("\t3StateValue: %s\n" % cb.Get3StateValue())
        if cb.Get3StateValue() == 2:
            cb.Set3StateValue(2)
            self.Check_UncheckAll(False)
        elif cb.Get3StateValue() == 1:
            self.Check_UncheckAll(True)
        elif cb.Get3StateValue() == 0:
            self.Check_UncheckAll(False)

    # -----------------------------------------------
    #                  OnItemChecked
    # -----------------------------------------------
    def OnItemCheck(self, event):
        if self.Get_all_cb_clicked():
            return
        print(_(f"%s is checked") % event.Item.Text)
        self.Update_all_checkbox()

    # -----------------------------------------------
    #                  OnItemUnchecked
    # -----------------------------------------------
    def OnItemUncheck(self, event):
        if self.Get_all_cb_clicked():
            return
        print(_(f"%s is unchecked") % event.Item.Text)
        self.Update_all_checkbox()

    # -----------------------------------------------
    #         Function Get_all_cb_clicked
    # -----------------------------------------------
    def Get_all_cb_clicked(self):
        return self.all_cb_clicked

    # -----------------------------------------------
    #         Function Set_all_cb_clicked
    # -----------------------------------------------
    def Set_all_cb_clicked(self, value):
        self.all_cb_clicked = value

    # -----------------------------------------------
    #          Function Update_all_checkbox
    # -----------------------------------------------
    def Update_all_checkbox(self):
        i = 0
        for index in range(self.list.GetItemCount()):
            if self.list.IsItemChecked(index):
                # print(_(f"{self.list.GetItem(index).Text} item is checked")
                i += 1
        # print(_(f"Checked items count: {i}")
        if i == 0:
            self.all_checkbox.Set3StateValue(0)
            self.EnableDisableButton(False)
        elif i == self.package_count:
            self.all_checkbox.Set3StateValue(1)
            self.EnableDisableButton(True)
        else:
            self.all_checkbox.Set3StateValue(2)
            self.EnableDisableButton(True)

    # -----------------------------------------------
    #         Function GetItemsCheckedCount
    # -----------------------------------------------
    def GetItemsCheckedCount(self):
        checked_count = 0
        for i in range(self.list.GetItemCount()):
            if self.list.IsItemChecked(i):
                checked_count += 1
        return checked_count

    # -----------------------------------------------
    #                  EnableDisableButton
    # -----------------------------------------------
    def EnableDisableButton(self, state):
        self.disable_button.Enable(state)
        self.enable_button.Enable(state)
        self.uninstall_button.Enable(state)
        self.add_to_deny_button.Enable(state)
        self.rm_from_deny_button.Enable(state)
        self.download_apk_button.Enable(state)

    # -----------------------------------------------
    #                  OnClose
    # -----------------------------------------------
    def OnClose(self, e):
        print(_(f"%s User Pressed Close.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        labels = get_labels()
        if (labels):
            with open(get_labels_file_path(), "w", encoding='ISO-8859-1', errors="replace") as f:
                # Write the dictionary to the file in JSON format
                json.dump(labels, f, indent=4)
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  OnDisable
    # -----------------------------------------------
    def OnDisable(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Disable.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.ApplyMultiAction('disable')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnEnable
    # -----------------------------------------------
    def OnEnable(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Enable.")) % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ApplyMultiAction('enable')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnUninstall
    # -----------------------------------------------
    def OnUninstall(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Uninstall.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.ApplyMultiAction('uninstall')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnAddToDeny
    # -----------------------------------------------
    def OnAddToDeny(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Add To Denylist.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.ApplyMultiAction('add-to-denylist')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnRmFromDeny
    # -----------------------------------------------
    def OnRmFromDeny(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Remove Denylist.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.ApplyMultiAction('rm-from-denylist')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnInstallApk
    # -----------------------------------------------
    def OnInstallApk(self, e):
        print(_(f"%s User Pressed Install APK.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with wx.FileDialog(self, _("select APK file to install"), '', '', wildcard=_("Android Applications (*.*.apk)|*.apk"), style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print(_("User cancelled apk install."))
                return
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(_(f"\nSelected %s for installation.") % pathname)
            dlg = wx.MessageDialog(None, _("Do you want to set the ownership to Play Store Market?\nNote: Android auto apps require that they be installed from the Play Market."),_('Set Play Market'),wx.YES_NO | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            try:
                self._on_spin('start')
                if self.device:
                    if result != wx.ID_YES:
                        self.device.install_apk(pathname, fastboot_included=True)
                    else:
                        puml(("note right:Set ownership to Play Store;\n"))
                        self.device.install_apk(pathname, fastboot_included=True, owner_playstore=True)
                self._on_spin('stop')
            except IOError:
                traceback.print_exc()
                wx.LogError(_(f"Cannot install file '%s'.") % pathname)
                self._on_spin('stop')

    # -----------------------------------------------
    #                  OnBulkInstallApk
    # -----------------------------------------------
    def OnBulkInstallApk(self, event):
        try:
            with wx.DirDialog(self, _("Select folder to bulk install APKs"), style=wx.DD_DEFAULT_STYLE) as folderDialog:
                if folderDialog.ShowModal() == wx.ID_CANCEL:
                    print(_("User cancelled folder selection."))
                    return
                selected_folder = folderDialog.GetPath()

            self._on_spin('start')
            device = get_phone()
            if device:
                apk_files = [file for file in os.listdir(selected_folder) if file.endswith(".apk")]
                show_playstore_prompt = True
                for apk_file in apk_files:
                    if show_playstore_prompt:
                        dlg = wx.MessageDialog(None, _("Do you want to set the ownership to Play Store Market?\nNote: This will apply to all the current bulk apks.\n(Android auto apps require that they be installed from the Play Market.)"),_('Set Play Market'),wx.YES_NO | wx.ICON_EXCLAMATION)
                        result = dlg.ShowModal()
                        if result != wx.ID_YES:
                            owner_playstore = False
                        else:
                            owner_playstore = True
                        show_playstore_prompt = False
                    apk_path = os.path.join(selected_folder, apk_file)
                    res = device.install_apk(apk_path, fastboot_included=True, owner_playstore=owner_playstore)
                    if res.returncode != 0:
                        print(_(f"Return Code: %s.") % res.returncode)
                        print(_(f"Stdout: %s") % res.stdout)
                        print(_(f"Stderr: %s") % res.stderr)
                        print(_("Aborting ...\n"))
                        self._on_spin('stop')
                        return res
        except Exception as e:
            print(_(f"\n%s ERROR: Encountered an error while installing APKs") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnGetAllNames
    # -----------------------------------------------
    def OnGetAllNames(self, e):
        self._on_spin('start')
        start = time.time()
        print(_(f"%s User Pressed Get All Application Names") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        labels = get_labels()
        for i in range(self.list.GetItemCount()):
            pkg = self.list.GetItemText(i)
            package = self.device.packages[pkg]
            if package.label == '':
                if package.path == '':
                    pkg_path = self.device.get_package_path(pkg, True)
                    if pkg_path == -1:
                        continue
                    package.path = pkg_path
                label, icon = self.device.get_package_label(pkg, package.path)
                if label != -1:
                    package.label = label
                    package.icon = icon
                    self.list.SetItem(i, 7, label)
                    row_as_list = list(self.itemDataMap[i + 1])
                    row_as_list[7] = label
                    self.itemDataMap[i + 1] = row_as_list
                    labels[pkg] = label
        set_labels(labels)
        end = time.time()
        print(_(f"App names extraction time: %s seconds") % math.ceil(end - start))
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnExportList
    # -----------------------------------------------
    def OnExportList(self, e):
        self._on_spin('start')
        start = time.time()
        print(_(f"%s User Pressed Export List") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with wx.FileDialog(self, _("Export Package list"), '', f"packages_{self.device.hardware}.csv", wildcard=_("Package list (*.csv)|*.csv"),
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            content = "package,type,installed,enabled,user0,denylist,uid,name\n"
            for i in range(self.list.GetItemCount()):
                package = self.list.GetItemText(i)
                type = self.list.GetItemText(i, 1)
                installed = self.list.GetItemText(i, 2)
                enabled = self.list.GetItemText(i, 3)
                user0 = self.list.GetItemText(i, 4)
                denylist = self.list.GetItemText(i, 5)
                uid = self.list.GetItemText(i, 6)
                name = self.list.GetItemText(i, 7)
                content += f"{package},{type},{installed},{enabled},{user0},{denylist},{uid},{name}\n"
            with open(pathname, "w", newline="\n") as f:
                f.write(content)
        end = time.time()
        print(_(f"Export Package List time: %s seconds") % math.ceil(end - start))
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnDownloadApk
    # -----------------------------------------------
    def OnDownloadApk(self, e):
        self._on_spin('start')
        print(_(f"%s User Pressed Download APK.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.ApplyMultiAction('download')
        self._on_spin('stop')

    # -----------------------------------------------
    #                  DownloadApk
    # -----------------------------------------------
    def DownloadApk(self, pkg, multiple = False):
        if not self.device:
            print(_(f"\n%s ERROR: You must first select a valid device.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return
        package = self.device.packages[pkg]
        path = package.path or package.path2
        if path == '':
            path = self.device.get_package_path(pkg, True)
            if path != -1:
                package.path = path
        if path == '':
            print(_(f"\n%s ERROR: Unable to get apk path for %s") % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pkg))
            print(_("Aborting download ..."))
            return
        label = package.label
        label = self.getColumnText(self.currentItem, 7)
        if multiple:
            if not self.download_folder:
                with wx.DirDialog(None, _("Choose a directory where all apks should be saved."), style=wx.DD_DEFAULT_STYLE) as folderDialog:
                    if folderDialog.ShowModal() == wx.ID_CANCEL:
                        print(_("User Cancelled saving packages (option: folder)."))
                        self.abort = True
                        return     # the user changed their mind
                    self.download_folder = folderDialog.GetPath()
                    print(_(f"Selected Download Directory: %s") % self.download_folder)
            pathname =  os.path.join(self.download_folder, f"{pkg}.apk")
        else:
            with wx.FileDialog(self, _("Download APK file"), '', f"{pkg}.apk", wildcard=_("APK files (*.apk)|*.apk"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    print(_(f"User Cancelled saving package: %s") % pkg)
                    return     # the user changed their mind
                pathname = fileDialog.GetPath()
        try:
            if self.device:
                print(_(f"Downloading apk file to: %s") % pathname)
                self.device.pull_file(path, pathname)
        except IOError:
            traceback.print_exc()
            wx.LogError(_(f"Cannot save apk file %s'.") % pathname)

    # -----------------------------------------------
    #                  GetListCtrl
    # -----------------------------------------------
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # -----------------------------------------------
    #                  GetSortImages
    # -----------------------------------------------
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    # -----------------------------------------------
    #                  OnRightDown
    # -----------------------------------------------
    def OnRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        # print("x, y = %s\n" % str((x, y)))
        item, flags = self.list.HitTest((x, y))
        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)
        event.Skip()

    # -----------------------------------------------
    #                  getColumnText
    # -----------------------------------------------
    def getColumnText(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()

    # -----------------------------------------------
    #                  OnItemSelected
    # -----------------------------------------------
    def OnItemSelected(self, event):
        self.currentItem = event.Index
        # print("OnItemSelected: %s, %s, %s, %s\n" %
        #                    (self.currentItem,
        #                     self.list.GetItemText(self.currentItem),
        #                     self.getColumnText(self.currentItem, 1),
        #                     self.getColumnText(self.currentItem, 2),
        #                     self.getColumnText(self.currentItem, 3),
        #                     self.getColumnText(self.currentItem, 4),
        #                     self.getColumnText(self.currentItem, 5)))
        self.GetPackageDetails(self.list.GetItemText(self.currentItem))
        event.Skip()

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
        col = event.GetColumn()
        if col == -1:
            return # clicked outside any column.
        rowid = self.list.GetColumn(col)
        print(_(f"Sorting on Column %s") % rowid.GetText())
        event.Skip()

    # -----------------------------------------------
    #                  OnCheckAllBoxes
    # -----------------------------------------------
    def OnCheckAllBoxes(self, event):
        self.Check_UncheckAll(True)

    # -----------------------------------------------
    #                  OnUnCheckAllBoxes
    # -----------------------------------------------
    def OnUnCheckAllBoxes(self, event):
        self.Check_UncheckAll(False)

    # -----------------------------------------------
    #                  OnRightClick
    # -----------------------------------------------
    def OnRightClick(self, event):
        # print("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupDisable"):
            self.popupDisable = wx.NewIdRef()
            self.popupEnable = wx.NewIdRef()
            self.popupUninstall = wx.NewIdRef()
            self.popupAddToDeny = wx.NewIdRef()
            self.popupRmFromDeny = wx.NewIdRef()
            self.popupDownload = wx.NewIdRef()
            self.popupLaunch = wx.NewIdRef()
            self.popupKill = wx.NewIdRef()
            self.popupClearData = wx.NewIdRef()
            self.popupRefresh = wx.NewIdRef()
            self.popupCheckAllBoxes = wx.NewIdRef()
            self.popupUnCheckAllBoxes = wx.NewIdRef()
            self.popupCopyClipboard = wx.NewIdRef()
            self.popupSuPermission = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnPopupDisable, id=self.popupDisable)
            self.Bind(wx.EVT_MENU, self.OnPopupEnable, id=self.popupEnable)
            self.Bind(wx.EVT_MENU, self.OnPopupUninstall, id=self.popupUninstall)
            self.Bind(wx.EVT_MENU, self.OnPopupAddToDeny, id=self.popupAddToDeny)
            self.Bind(wx.EVT_MENU, self.OnPopupRmFromDeny, id=self.popupRmFromDeny)
            self.Bind(wx.EVT_MENU, self.OnPopupDownload, id=self.popupDownload)
            self.Bind(wx.EVT_MENU, self.OnPopupLaunch, id=self.popupLaunch)
            self.Bind(wx.EVT_MENU, self.OnPopupKill, id=self.popupKill)
            self.Bind(wx.EVT_MENU, self.OnPopupClearData, id=self.popupClearData)
            self.Bind(wx.EVT_MENU, self.OnPopupRefresh, id=self.popupRefresh)
            self.Bind(wx.EVT_MENU, self.OnCheckAllBoxes, id=self.popupCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnUnCheckAllBoxes, id=self.popupUnCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnCopyClipboard, id=self.popupCopyClipboard)
            self.Bind(wx.EVT_MENU, self.OnSuPermission, id=self.popupSuPermission)

        # build the menu
        menu = wx.Menu()
        disableItem = menu.Append(self.popupDisable, _("Disable Package"))
        enableItem = menu.Append(self.popupEnable, _("Enable Package"))
        uninstallItem = menu.Append(self.popupUninstall, _("Uninstall Package"))
        downloadItem = menu.Append(self.popupDownload, _("Download Package"))
        launchItem = menu.Append(self.popupLaunch, _("Launch Package"))
        killItem = menu.Append(self.popupKill, _("Kill Application"))
        clearItem = menu.Append(self.popupClearData, _("Clear Application Data"))
        # Add a separator
        menu.AppendSeparator()
        refreshItem = menu.Append(self.popupRefresh, _("Refresh"))
        checkItem = menu.Append(self.popupCheckAllBoxes, _("Check All"))
        unCheckItem = menu.Append(self.popupUnCheckAllBoxes, _("UnCheck All"))
        clipboardItem=menu.Append(self.popupCopyClipboard, _("Copy to Clipboard"))
        # Add a separator
        menu.AppendSeparator()
        addDenyItem = menu.Append(self.popupAddToDeny, _("Add Package to Magisk Denylist"))
        removeDenyItem = menu.Append(self.popupRmFromDeny, _("Remove Package from Magisk Denylist"))
        suPermissionItem = menu.Append(self.popupSuPermission, _("SU Permission ..."))

        # set icons
        disableItem.SetBitmap(images.disable_24.GetBitmap())
        enableItem.SetBitmap(images.enable_24.GetBitmap())
        uninstallItem.SetBitmap(images.uninstall_24.GetBitmap())
        downloadItem.SetBitmap(images.download_24.GetBitmap())
        launchItem.SetBitmap(images.launch_24.GetBitmap())
        killItem.SetBitmap(images.kill_24.GetBitmap())
        clearItem.SetBitmap(images.clear_24.GetBitmap())
        refreshItem.SetBitmap(images.scan_24.GetBitmap())
        checkItem.SetBitmap(images.check_24.GetBitmap())
        unCheckItem.SetBitmap(images.uncheck_24.GetBitmap())
        clipboardItem.SetBitmap(images.clipboard_24.GetBitmap())
        addDenyItem.SetBitmap(images.magisk_24.GetBitmap())
        removeDenyItem.SetBitmap(images.magisk_24.GetBitmap())
        suPermissionItem.SetBitmap(images.magisk_24.GetBitmap())

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  OnPopupDisable
    # -----------------------------------------------
    def OnPopupDisable(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'disable')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupEnable
    # -----------------------------------------------
    def OnPopupEnable(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'enable')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupUninstall
    # -----------------------------------------------
    def OnPopupUninstall(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'uninstall')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupAddToDeny
    # -----------------------------------------------
    def OnPopupAddToDeny(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'add-to-denylist')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnSuPermission
    # -----------------------------------------------
    def OnSuPermission(self, event):
        self._on_spin('start')
        index = self.currentItem
        pkg = self.list.GetItem(index).Text
        uid = self.list.GetItem(index, 6).Text
        label = self.list.GetItem(index, 7).Text
        text = _(f"Set SU Permission for: %s %s %s") % (pkg, uid, label)
        print(f"{text} ...")

        # Popup a small dialog to display SU Permission selection
        dialog = SuPermissionDialog(self, pkg=pkg, uid=uid, label=text)
        if dialog.ShowModal() != wx.ID_OK:
            print(_("User pressed Cancel"))
        dialog.Destroy()

        # self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupRmFromDeny
    # -----------------------------------------------
    def OnPopupRmFromDeny(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'rm-from-denylist')
        self.RefreshPackages()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupDownload
    # -----------------------------------------------
    def OnPopupDownload(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'download')
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupLaunch
    # -----------------------------------------------
    def OnPopupLaunch(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'launch')
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupKill
    # -----------------------------------------------
    def OnPopupKill(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'kill')
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupClearData
    # -----------------------------------------------
    def OnPopupClearData(self, event):
        self._on_spin('start')
        self.ApplySingleAction(self.currentItem, 'clear-data')
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupRefresh
    # -----------------------------------------------
    def OnPopupRefresh(self, event):
        self._on_spin('start')
        self.RefreshPackages
        self._on_spin('stop')

    # -----------------------------------------------
    #                  OnPopupRefresh
    # -----------------------------------------------
    def RefreshPackages(self):
        res = self.device.get_detailed_packages()
        if res == 0:
            self.packages = self.device.packages
            self.package_count = len(self.packages)
        else:
            self.package_count = 0
        self.Refresh()

    # -----------------------------------------------
    #                  OnCopyClipboard
    # -----------------------------------------------
    def OnCopyClipboard(self, event):
        item = self.list.GetItem(self.currentItem)
        pyperclip.copy(item.Text)

    # -----------------------------------------------
    #                  Function Refresh
    # -----------------------------------------------
    def Refresh(self):
        self.list.Freeze()
        print(_("Refreshing the packages ...\n"))
        self._on_spin('start')
        self.list.ClearAll()
        itemDataMap = self.PopulateList()
        if itemDataMap != -1:
            self.itemDataMap = itemDataMap
        self._on_spin('stop')
        self.list.Thaw()

    # -----------------------------------------------
    #          Function ApplySingleAction
    # -----------------------------------------------
    def ApplySingleAction(self, index, action, fromMulti = False, counter = ''):
        pkg = self.list.GetItem(index).Text
        type = self.list.GetItem(index, 1).Text
        label = self.list.GetItem(index, 7).Text
        # installed = self.list.GetItem(index, 2).Text
        # enabled = self.list.GetItem(index, 3).Text
        # user0 = self.list.GetItem(index, 4).Text
        # magisk_denylist = self.list.GetItem(index, 5).Text
        # uid = self.list.GetItem(index, 6).Text
        # label = self.list.GetItem(index, 7).Text
        if type == 'System':
            isSystem = True
        else:
            isSystem = False

        if not self.device:
            print(_(f"\n%s ERROR: You must first select a valid device.") % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return
        # res = self.device.get_detailed_packages()
        if action == "disable":
            print(_(f"Disabling %s%s type: %s...") % (counter, pkg, type))
        elif action == "enable":
            print(_(f"Enabling %s%s type: %s...") % (counter, pkg, type))
        elif action == "uninstall":
            print(_(f"Uninstalling %s%s type: %s...") % (counter, pkg, type))
        elif action == "add-to-denylist":
            print(_(f"Adding %s%s type: %s to Magisk Denylist...") % (counter, pkg, type))
        elif action == "rm-from-denylist":
            print(_(f"Removing %s%s type: %s from Magisk Denylist...") % (counter, pkg, type))
        elif action == "launch":
            print(_(f"Launching %s%s type: %s...") % (counter, pkg, type))
        elif action == "kill":
            print(_(f"Killing %s%s type: %s...") % (counter, pkg, type))
        elif action == "clear-data":
            print(_(f"Clearing %sdata for %s type: %s...") % (counter, pkg, type))
        elif action == "download":
            print(_(f"Downloading %s%s Label: %s...") % (counter, pkg, label))
            self.DownloadApk(pkg, fromMulti)
            return
        self.device.perform_package_action(pkg, action, isSystem)
        # TODO: update / refresh the item

    # -----------------------------------------------
    #          Function ApplyMultiAction
    # -----------------------------------------------
    def ApplyMultiAction(self, action):
        i = 0
        count = self.GetItemsCheckedCount()
        multi = False
        if count > 1:
            print(_(f"Processing {count} items ..."))
            multi = True
        if action == 'download':
            self.download_folder = None
        for index in range(self.list.GetItemCount()):
            if self.abort:
                self.abort = False
                break
            if self.list.IsItemChecked(index):
                self.ApplySingleAction(index, action, multi, f"{i}/{count} ")
                i += 1
        print(_(f"Total count of package actions attempted: %s") % i)

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        wx.YieldIfNeeded()
        if state == 'start':
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            self.Parent._on_spin('start')
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.Parent._on_spin('stop')
