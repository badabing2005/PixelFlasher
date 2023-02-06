#!/usr/bin/env python

import gzip
import json
import shutil

import clipboard
import wx
import wx.html
import wx.lib.mixins.listctrl as listmix
import wx.lib.wxpTag

import images as images
from modules import extract_sha1, sha1
from runtime import *


# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


# ============================================================================
#                               Class BackupManager
# ============================================================================
class BackupManager(wx.Dialog, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs, style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle("Magisk Backup Manager")
        self.backupCount = 0
        self.all_cb_clicked = False
        self.device = get_phone()
        if not self.device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return

        self.sha1 = self.device.magisk_sha1
        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = self.sha1
        self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        self.all_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Check / Uncheck All", wx.DefaultPosition, wx.DefaultSize, style=wx.CHK_3STATE)

        self.searchCtrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.searchCtrl.ShowCancelButton(True)

        self.il = wx.ImageList(16, 16)
        self.idx1 = self.il.Add(images.Official_Small.GetBitmap())
        self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())

        self.list  = ListCtrl(self, -1, size=(-1, -1), style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_NONE)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLACK'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.EnableCheckBoxes(enable=True)
        itemDataMap = self.PopulateList()
        if itemDataMap != -1:
            self.itemDataMap = itemDataMap
        listmix.ColumnSorterMixin.__init__(self, 6)

        self.delete_button = wx.Button(self, wx.ID_ANY, u"Delete", wx.DefaultPosition, wx.DefaultSize, 0)
        self.delete_button.SetToolTip(u"Delete checked backups")
        self.delete_button.Enable(False)

        self.add_backup_button = wx.Button(self, wx.ID_ANY, u"Add Backup from Computer", wx.DefaultPosition, wx.DefaultSize, 0)
        self.add_backup_button.SetToolTip(u"Select a boot.img and create a backup from it.\nWARNING! No verification is done if the selected file is stock boot image or even for the correct device.")

        self.auto_backup_button = wx.Button(self, wx.ID_ANY, u"Auto Create Backup", wx.DefaultPosition, wx.DefaultSize, 0)
        self.auto_backup_button.SetToolTip(u"Checks current boot partition,\nFf it is a Magisk Patched with SHA1\nand the boot.img is available, then it\nAutomatically creates a backup of boot image.")

        self.close_button = wx.Button(self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0)
        self.close_button.SetToolTip(u"Closes this dialog")

        vSizer = wx.BoxSizer(wx.VERTICAL)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        hSizer1 = wx.BoxSizer( wx.HORIZONTAL )
        hSizer1.Add( (10, 0), 0, wx.EXPAND, 10 )
        hSizer1.Add(self.all_checkbox, 0, wx.EXPAND, 10)
        hSizer1.Add( (0, 0), 1, wx.EXPAND, 10 )
        hSizer1.Add(self.searchCtrl, 1, wx.RIGHT, 10)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        buttons_sizer.Add(self.delete_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.add_backup_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.auto_backup_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.close_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(hSizer1, 0, wx.EXPAND, 10)
        vSizer.Add(self.list , 1, wx.ALL|wx.EXPAND, 10)
        vSizer.Add(buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        self.SetSize(vSizer.MinSize.Width + 80, vSizer.MinSize.Height + 400)

        # Connect Events
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.delete_button.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.add_backup_button.Bind(wx.EVT_BUTTON, self.OnAddBackup)
        self.auto_backup_button.Bind(wx.EVT_BUTTON, self.OnAutoBackup)
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
        info.Text = "SHA1"
        self.list.InsertColumn(0, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "Date"
        self.list.InsertColumn(1, info)

        info.Align = wx.LIST_FORMAT_LEFT # 0
        info.Text = "Firmware"
        self.list.InsertColumn(2, info)

        res = self.device.get_magisk_backups()
        itemDataMap = {}
        query = self.searchCtrl.GetValue().lower()
        if res == 0:
            self.backupCount = len(self.device.backups)
            self.message_label.Label = f"{self.backupCount} Backups\n{self.sha1}"
            i = 0
            items = self.device.backups.items()
            for key, data in items:
                alltext = f"{key.lower()} {str(data.firmware.lower())}"
                if query.lower() in alltext:
                    index = self.list.InsertItem(self.list.GetItemCount(), key)
                    if data.value != '':
                        itemDataMap[i + 1] = (key, data.date, data.firmware)
                        row = self.list.GetItem(index)
                        self.list.SetItem(index, 1, data.date)
                        self.list.SetItem(index, 2, str(data.firmware))
                        if self.sha1 != '' and self.sha1 == data.value:
                            row.SetTextColour(wx.RED)
                        self.list.SetItem(row)
                        self.list.SetItemData(index, i + 1)
                    # hide image
                    self.list.SetItemColumnImage(i, 0, -1)
                    i += 1
            self.message_label.Label = f"{str(i)} / {self.backupCount} Backups\n{self.sha1}"
        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 1, 20)

        self.currentItem = 0
        if itemDataMap:
            return itemDataMap
        else:
            return -1

    # -----------------------------------------------
    #              Function Check_UncheckAll
    # -----------------------------------------------
    def Check_UncheckAll(self, state):
        # Set this so that we skip processing OnItemChecked, OnItemUnchecked events
        self.Set_all_cb_clicked (True)
        itemcount = self.list.GetItemCount()
        [self.list.CheckItem(item=i, check=state) for i in range(itemcount)]
        if state:
            print("checking all Backups\n")
            self.EnableDisableButton(True)
        else:
            print("Unchecking all Backups\n")
            self.EnableDisableButton(False)
        self.Set_all_cb_clicked (False)

    # -----------------------------------------------
    #                  onSearch
    # -----------------------------------------------
    def OnSearch(self, event):
        query = self.searchCtrl.GetValue()
        print(f"Searching for: {query}")
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
        elif i == self.backupCount:
            self.all_checkbox.Set3StateValue(1)
            self.EnableDisableButton(True)
        else:
            self.all_checkbox.Set3StateValue(2)
            self.EnableDisableButton(True)

    # -----------------------------------------------
    #                  EnableDisableButton
    # -----------------------------------------------
    def EnableDisableButton(self, state):
        self.delete_button.Enable(state)

    # -----------------------------------------------
    #                  OnClose
    # -----------------------------------------------
    def OnClose(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Close.")
        labels = get_labels()
        if (labels):
            with open(get_labels_file_path(), "w") as f:
                # Write the dictionary to the file in JSON format
                json.dump(labels, f, indent=4)
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  OnDelete
    # -----------------------------------------------
    def OnDelete(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Delete.")
        i = 0
        for index in range(self.list.GetItemCount()):
            if self.list.IsItemChecked(index):
                self.DeleteBackup(index, False)
                i += 1
        self.Refresh()
        print(f"Total count of backups deleted: {i}")

    # -----------------------------------------------
    #                  DeleteBackup
    # -----------------------------------------------
    def DeleteBackup(self, index, do_refresh = True):
        sha1 = self.list.GetItem(index).Text
        print(f"Deleting backup {sha1}")
        self.device.delete(f"/data/magisk_backup_{sha1}/", True, True)
        if do_refresh:
            self.Refresh()

    # -----------------------------------------------
    #                  OnAddBackup
    # -----------------------------------------------
    def OnAddBackup(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed on Add Backup")
        with wx.FileDialog(self, "boot / init_boot image to create backup of.", '', '', wildcard="Images (*.*.img)|*.img", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled backup creation.")
                return
            # save the current contents in the file
            file_to_backup = fileDialog.GetPath()
            file_sha1 = sha1(file_to_backup)
            print(f"\nSelected {file_to_backup} for backup with SHA1 of {file_sha1}")
            try:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                res = self.device.push_file(f"{file_to_backup}", '/data/adb/magisk/stock_boot.img', True)
                if res != 0:
                    print("Aborting ...\n")
                    return
                # run the migration.
                res = self.device.run_magisk_migration(file_sha1)
                print("Checking to see if Magisk made a backup.")
                magisk_backups = self.device.magisk_backups
                if magisk_backups and file_sha1 in magisk_backups:
                    print("Good: Magisk has made a backup")
                else:
                    print("It looks like Magisk did not make a backup.\nTrying an alternate approach ...")
                    self.ZipAndPush(file_to_backup, file_sha1)
                    if res != 0:
                        print("Aborting ...\n")
                        return

                # Refresh the list
                self.Refresh()

                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            except Exception as e:
                print(f"Cannot backup file '{file_to_backup}'.")

    # -----------------------------------------------
    #                  ZipAndPush
    # -----------------------------------------------
    def ZipAndPush(self, file_to_backup, file_sha1):
        print(f"Zipping {file_to_backup} ...")
        backup_file = os.path.join(get_config_path(), 'tmp', 'boot.img.gz')
        with open(file_to_backup, 'rb') as f_in:
            with gzip.open(backup_file, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
        if not os.path.exists(backup_file):
            print(f"ERROR: Coud not create {backup_file}")
            return -1
        # mkdir the directory with su
        res = self.device.create_dir(f"/data/magisk_backup_{file_sha1}", True)
        if res != 0:
            return -1
        # Transfer the file with su
        res = self.device.push_file(f"{backup_file}", f"/data/magisk_backup_{file_sha1}/boot.img.gz", True)
        if res != 0:
            return -1

    # -----------------------------------------------
    #                  OnAutoBackup
    # -----------------------------------------------
    def OnAutoBackup(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed on Auto Create Backup")

        config_path = get_config_path()
        if self.sha1:
            patched_sha1 = self.sha1
        else:
            # extract the current slot's boot.img
            res, file_path = self.device.dump_boot()
            if res != 0:
                print("Aborting ...\n")
                return
            # pull the file locally
            extracted_boot = os.path.join(config_path, 'tmp', 'extracted_boot.img')
            res = self.device.pull_file(file_path, extracted_boot)
            if res != 0:
                print("Aborting ...\n")
                return
            # extract the sha1
            print("Extracting SHA1 from dumped partition ...")
            patched_sha1 = extract_sha1(extracted_boot, 40)
            print(f"Source SHA1 embedded in dumped partition is: {patched_sha1}")

        if patched_sha1:
            try:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                print(f"Checking to see if we have a copy of {patched_sha1} ...")
                source_init_boot = os.path.join(config_path, get_boot_images_dir(), patched_sha1, 'init_boot.img')
                source_boot = os.path.join(config_path, get_boot_images_dir(), patched_sha1, 'boot.img')
                if os.path.exists(source_init_boot):
                    print(f"Found {source_init_boot}, creating backup ...")
                    file_to_backup = source_init_boot
                elif os.path.exists(source_boot):
                    print(f"Found {source_boot}, creating backup ...")
                    file_to_backup = source_boot
                else:
                    print(f"ERROR: Did not find a local copy of source boot / init_boot with SHA1 of {patched_sha1}")
                    print("Cannot create automatic backup file, you can still manually select and create one.")
                    print("Aborting ...")

                res = self.device.push_file(f"{file_to_backup}", '/data/adb/magisk/stock_boot.img', True)
                if res != 0:
                    print("Aborting ...\n")
                    return
                # run the migration.
                res = self.device.run_magisk_migration(patched_sha1)
                print("Checking to see if Magisk made a backup.")
                magisk_backups = self.device.magisk_backups
                if magisk_backups and patched_sha1 in magisk_backups:
                    print("Good: Magisk has made a backup")
                else:
                    print("It looks like Magisk did not make a backup.\nTrying an alternate approach ...")
                    self.ZipAndPush(file_to_backup, patched_sha1)
                    if res != 0:
                        print("Aborting ...\n")
                        return

                # Refresh the list
                self.Refresh()
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            except Exception as e:
                print("Cannot create automatic backup file, you can still manually select and create one.")
                print("Aborting ...")
                return
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The dumped partition does not contain source boot's SHA1")
            print("This is normal for older devices, but newer deviced should have it.")
            print("Cannot create automatic backup file, you can still manually select and create one.")
            print("Aborting ...")
            return

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
        # self.GetPackageDetails(self.list.GetItemText(self.currentItem))
        # self.all_checkbox.Set3StateValue(2)
        event.Skip()

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
        col = event.GetColumn()
        if col == -1:
            return # clicked outside any column.
        rowid = self.list.GetColumn(col)
        print(f"Sorting on Column {rowid.GetText()}")
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
        if not hasattr(self, "popupDelete"):
            self.popupDelete = wx.NewIdRef()
            self.popupRefresh = wx.NewIdRef()
            self.popupCheckAllBoxes = wx.NewIdRef()
            self.popupUnCheckAllBoxes = wx.NewIdRef()
            self.popupCopyClipboard = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnpopupDelete, id=self.popupDelete)
            self.Bind(wx.EVT_MENU, self.OnPopupRefresh, id=self.popupRefresh)
            self.Bind(wx.EVT_MENU, self.OnCheckAllBoxes, id=self.popupCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnUnCheckAllBoxes, id=self.popupUnCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnCopyClipboard, id=self.popupCopyClipboard)

        # build the menu
        menu = wx.Menu()
        menu.Append(self.popupDelete, "Delete Backup")
        menu.Append(self.popupRefresh, "Refresh")
        menu.Append(self.popupCheckAllBoxes, "Check All")
        menu.Append(self.popupUnCheckAllBoxes, "UnCheck All")
        menu.Append(self.popupCopyClipboard, "Copy to Clipboard")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  OnpopupDelete
    # -----------------------------------------------
    def OnpopupDelete(self, event):
        self.DeleteBackup(self.currentItem)

    # -----------------------------------------------
    #                  OnPopupRefresh
    # -----------------------------------------------
    def OnPopupRefresh(self, event):
        self.Refresh()

    # -----------------------------------------------
    #                  OnCopyClipboard
    # -----------------------------------------------
    def OnCopyClipboard(self, event):
        item = self.list.GetItem(self.currentItem)
        clipboard.copy(item.Text)

    # -----------------------------------------------
    #                  Function Refresh
    # -----------------------------------------------
    def Refresh(self):
        print("Refreshing the backups ...\n")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
