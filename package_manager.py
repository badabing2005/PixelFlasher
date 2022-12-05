#!/usr/bin/env python

import clipboard
import darkdetect
import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from runtime import *


# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


# ============================================================================
#                               Class PackageManager
# ============================================================================
class PackageManager(wx.Dialog, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs, style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle("Manage Packages on the Device")
        self.packageCount = 0
        self.all_cb_clicked = False

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
        self.message_label.Label = ""
        self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        vSizer1.Add(message_sizer, 0, wx.EXPAND, 5)

        hSizer1 = wx.BoxSizer( wx.HORIZONTAL )
        self.all_checkbox = wx.CheckBox(panel1, wx.ID_ANY, u"Check / Uncheck All", wx.DefaultPosition, wx.DefaultSize, style=wx.CHK_3STATE)
        hSizer1.Add( (10, 0), 0, wx.EXPAND, 5 )
        hSizer1.Add(self.all_checkbox, 0, wx.EXPAND, 5)
        vSizer1.Add(hSizer1, 0, wx.EXPAND, 5)

        self.il = wx.ImageList(16, 16)

        self.idx1 = self.il.Add(images.Official_Small.GetBitmap())
        self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())

        self.list  = ListCtrl(panel1, -1, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLACK'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.EnableCheckBoxes(enable=True)
        itemDataMap = self.PopulateList()
        self.itemDataMap = itemDataMap
        listmix.ColumnSorterMixin.__init__(self, 5)

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

        self.disable_button = wx.Button(panel2, wx.ID_ANY, u"Disable", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_button.SetToolTip(u"Disable checked packages")
        self.disable_button.Enable(False)
        buttons_sizer.Add(self.disable_button, 0, wx.ALL, 20)

        self.enable_button = wx.Button(panel2, wx.ID_ANY, u"Enable", wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_button.SetToolTip(u"Enable checked packages")
        self.enable_button.Enable(False)
        buttons_sizer.Add(self.enable_button, 0, wx.ALL, 20)

        self.uninstall_button = wx.Button(panel2, wx.ID_ANY, u"Uninstall", wx.DefaultPosition, wx.DefaultSize, 0)
        self.uninstall_button.SetToolTip(u"Uninstall checked packages")
        self.uninstall_button.Enable(False)
        buttons_sizer.Add(self.uninstall_button, 0, wx.ALL, 20)

        self.install_apk_button = wx.Button(panel2, wx.ID_ANY, u"Install APK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_apk_button.SetToolTip(u"Install an APK on the device")
        buttons_sizer.Add(self.install_apk_button, 0, wx.ALL, 20)

        self.close_button = wx.Button(panel2, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0)
        self.close_button.SetToolTip(u"Closes this dialog")
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
        self.disable_button.Bind(wx.EVT_BUTTON, self.OnDisable)
        self.enable_button.Bind(wx.EVT_BUTTON, self.OnEnable)
        self.uninstall_button.Bind(wx.EVT_BUTTON, self.OnUninstall)
        self.install_apk_button.Bind(wx.EVT_BUTTON, self.OnInstallApk)
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
        info.Text = "Package"
        self.list.InsertColumn(0, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "Type"
        self.list.InsertColumn(1, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "Installed"
        self.list.InsertColumn(2, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "Enabled"
        self.list.InsertColumn(3, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "User 0"
        self.list.InsertColumn(4, info)

        device = get_phone()
        res = device.get_detailed_packages()
        if res == 0:
            # we got all the package
            # TODO: Add filter / search functionality
            self.packageCount = len(device.packages)
            self.message_label.Label = f"{self.packageCount} Packages"
            i = 0
            itemDataMap = {}
            items = device.packages.items()
            for key, data in items:
                index = self.list.InsertItem(self.list.GetItemCount(), key)
                if data.type != '':
                    itemDataMap[i + 1] = (key, data.type, data.installed, data.enabled, data.user0)
                    row = self.list.GetItem(index)
                    self.list.SetItem(index, 1, data.type)
                    self.list.SetItem(index, 2, str(data.installed))
                    self.list.SetItem(index, 3, str(data.enabled))
                    self.list.SetItem(index, 4, str(data.user0))
                    if data.type == 'System':
                        row.SetTextColour(wx.RED)
                    else:
                        if darkdetect.isLight():
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
        self.list.SetColumnWidth(0, -2)
        self.list.SetColumnWidth(1, -2)
        self.list.SetColumnWidth(2, -2)
        self.list.SetColumnWidth(3, -2)
        self.list.SetColumnWidth(4, -2)

        self.currentItem = 0
        return itemDataMap

    # -----------------------------------------------
    #          Function GetPackageDetails
    # -----------------------------------------------
    def GetPackageDetails(self, pkg):
        device = get_phone()
        package = device.packages[pkg]
        if package.details == '':
            details = device.package_details(pkg)
            package.details = details
        self.details.SetValue(package.details)

    # -----------------------------------------------
    #              Function Check_UncheckAll
    # -----------------------------------------------
    def Check_UncheckAll(self, state):
        # Set this so that we skip processing OnItemChecked, OnItemUnchecked events
        self.Set_all_cb_clicked (True)
        itemcount = self.list.GetItemCount()
        [self.list.CheckItem(item=i, check=state) for i in range(itemcount)]
        if state:
            print("checking all Packages\n")
            self.EnableDisableButton(True)
        else:
            print("Unchecking all Packages\n")
            self.EnableDisableButton(False)
        self.Set_all_cb_clicked (False)

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
        print(f"{event.Item.Text} is checked")
        self.Update_all_checkbox()

    # -----------------------------------------------
    #                  OnItemUnchecked
    # -----------------------------------------------
    def OnItemUncheck(self, event):
        if self.Get_all_cb_clicked():
            return
        print(f"{event.Item.Text} is unchecked")
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
                # print(f"{self.list.GetItem(index).Text} item is checked")
                i += 1
        # print(f"Checked items count: {i}")
        if i == 0:
            self.all_checkbox.Set3StateValue(0)
            self.EnableDisableButton(False)
        elif i == self.packageCount:
            self.all_checkbox.Set3StateValue(1)
            self.EnableDisableButton(True)
        else:
            self.all_checkbox.Set3StateValue(2)
            self.EnableDisableButton(True)

    # -----------------------------------------------
    #                  EnableDisableButton
    # -----------------------------------------------
    def EnableDisableButton(self, state):
        self.disable_button.Enable(state)
        self.enable_button.Enable(state)
        self.uninstall_button.Enable(state)

    # -----------------------------------------------
    #                  OnClose
    # -----------------------------------------------
    def OnClose(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Close.")
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  OnDisable
    # -----------------------------------------------
    def OnDisable(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Disable.")
        self.ApplyMultiAction('disable')

    # -----------------------------------------------
    #                  OnEnable
    # -----------------------------------------------
    def OnEnable(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Enable.")
        self.ApplyMultiAction('enable')

    # -----------------------------------------------
    #                  OnUninstall
    # -----------------------------------------------
    def OnUninstall(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Uninstall.")
        self.ApplyMultiAction('uninstall')

    # -----------------------------------------------
    #                  OnInstallApk
    # -----------------------------------------------
    def OnInstallApk(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Install APK.")
        with wx.FileDialog(self, "select APK file to install", '', '', wildcard="Android Applications (*.*.apk)|*.apk", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled apk install.")
                return
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                device = get_phone()
                if device:
                    device.install_apk(pathname, fastboot_included=True)
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            except IOError:
                wx.LogError(f"Cannot install file '{pathname}'.")

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
        #                     self.getColumnText(self.currentItem, 2)))
        self.GetPackageDetails(self.list.GetItemText(self.currentItem))
        self.all_checkbox.Set3StateValue(2)
        event.Skip()

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
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
    #                  OnGetItemsChecked
    # -----------------------------------------------
    def OnGetItemsChecked(self, event):
        itemcount = self.list.GetItemCount()
        itemschecked = [i for i in range(itemcount) if self.list.IsItemChecked(item=i)]
        print(f"Package: {itemschecked} is checked.")

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
            self.popupRefresh = wx.NewIdRef()
            self.popupCheckAllBoxes = wx.NewIdRef()
            self.popupUnCheckAllBoxes = wx.NewIdRef()
            self.popupCopyClipboard = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnPopupDisable, id=self.popupDisable)
            self.Bind(wx.EVT_MENU, self.OnPopupEnable, id=self.popupEnable)
            self.Bind(wx.EVT_MENU, self.OnPopupUninstall, id=self.popupUninstall)
            self.Bind(wx.EVT_MENU, self.OnPopupRefresh, id=self.popupRefresh)
            self.Bind(wx.EVT_MENU, self.OnCheckAllBoxes, id=self.popupCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnUnCheckAllBoxes, id=self.popupUnCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnCopyClipboard, id=self.popupCopyClipboard)

        # build the menu
        menu = wx.Menu()
        menu.Append(self.popupDisable, "Disable Package")
        menu.Append(self.popupEnable, "Enable Selected")
        menu.Append(self.popupUninstall, "Uninstall Package")
        menu.Append(self.popupRefresh, "Refresh")
        menu.Append(self.popupCheckAllBoxes, "Check All")
        menu.Append(self.popupUnCheckAllBoxes, "UnCheck All")
        menu.Append(self.popupCopyClipboard, "Copy to Clipboard")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  OnPopupDisable
    # -----------------------------------------------
    def OnPopupDisable(self, event):
        self.ApplySingleAction(self.currentItem, 'disable')

    # -----------------------------------------------
    #                  OnPopupEnable
    # -----------------------------------------------
    def OnPopupEnable(self, event):
        self.ApplySingleAction(self.currentItem, 'enable')

    # -----------------------------------------------
    #                  OnPopupUninstall
    # -----------------------------------------------
    def OnPopupUninstall(self, event):
        self.ApplySingleAction(self.currentItem, 'uninstall')

    # -----------------------------------------------
    #                  OnPopupRefresh
    # -----------------------------------------------
    def OnPopupRefresh(self, event):
        print("Popup three\n")
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)

    # -----------------------------------------------
    #                  OnCopyClipboard
    # -----------------------------------------------
    def OnCopyClipboard(self, event):
        item = self.list.GetItem(self.currentItem)
        clipboard.copy(item.Text)

    # -----------------------------------------------
    #          Function ApplySingleAction
    # -----------------------------------------------
    def ApplySingleAction(self, index, action):
        pkg = self.list.GetItem(index).Text
        type = self.list.GetItem(index, 1).Text
        # installed = self.list.GetItem(index, 2).Text
        # enabled = self.list.GetItem(index, 3).Text
        # user0 = self.list.GetItem(index, 4).Text
        if type == 'System':
            isSystem = True
        else:
            isSystem = False

        device = get_phone()
        res = device.get_detailed_packages()
        if res == 0:
            if action == "disable":
                print(f"Disabling {pkg} type: {type}...")
            elif action == "enable":
                print(f"Enabling {pkg} type: {type}...")
            elif action == "uninstall":
                print(f"Uninstalling {pkg} type: {type}...")
            device.package_action(pkg, action, isSystem)
            # TODO: update / refresh the item

    # -----------------------------------------------
    #          Function ApplyMultiAction
    # -----------------------------------------------
    def ApplyMultiAction(self, action):
        i = 0
        for index in range(self.list.GetItemCount()):
            if self.list.IsItemChecked(index):
                self.ApplySingleAction(index, action)
                i += 1
        print(f"Total count of package actions attempted: {i}")
