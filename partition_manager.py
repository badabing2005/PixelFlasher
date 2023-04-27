#!/usr/bin/env python

import json

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
#                               Class PartitionManager
# ============================================================================
class PartitionManager(wx.Dialog, listmix.ColumnSorterMixin):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs, style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle("Partition Manager")
        self.partitionCount = 0
        self.all_cb_clicked = False
        self.downloadFolder = None
        self.abort = False
        self.device = get_phone()
        if not self.device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return -1

        warning_sizer = wx.BoxSizer(wx.HORIZONTAL)
        warning_text = '''WARNING!
This is advanced feature.
Unless you know what you are doing,
you should not be touching this.

YOU AND YOU ALONE ARE RESPONSIBLE FOR ANYTHING THAT HAPPENS TO YOUR DEVICE.
THIS TOOL IS CODED WITH THE EXPRESS ASSUMPTION THAT YOU ARE FAMILIAR WITH
ADB, MAGISK, ANDROID, ROOT AND PARTITION MANIPULATION.
IT IS YOUR RESPONSIBILITY TO ENSURE THAT YOU KNOW WHAT YOU ARE DOING.
'''
        # warning label
        self.warning_label = wx.StaticText(self, wx.ID_ANY, warning_text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_HORIZONTAL)
        self.warning_label.Wrap(-1)
        self.warning_label.SetForegroundColour(wx.Colour(255, 0, 0))

        # static line
        staticline = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)

        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = ""
        self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        self.all_checkbox = wx.CheckBox(self, wx.ID_ANY, u"Check / Uncheck All", wx.DefaultPosition, wx.DefaultSize, style=wx.CHK_3STATE)

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

        self.erase_button = wx.Button(self, wx.ID_ANY, u"Erase", wx.DefaultPosition, wx.DefaultSize, 0)
        self.erase_button.SetToolTip(u"Erase checked partitions")
        self.erase_button.Enable(False)

        self.dump_partition = wx.Button(self, wx.ID_ANY, u"Dump / Backup", wx.DefaultPosition, wx.DefaultSize, 0)
        self.dump_partition.SetToolTip(u"Dumps / Backups the checked partitions")
        self.dump_partition.Enable(False)


        self.close_button = wx.Button(self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0)
        self.close_button.SetToolTip(u"Closes this dialog")

        vSizer = wx.BoxSizer(wx.VERTICAL)
        warning_sizer.Add(self.warning_label, 1, wx.ALL, 10)
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        hSizer1 = wx.BoxSizer( wx.HORIZONTAL )
        hSizer1.Add( (10, 0), 0, wx.EXPAND, 10 )
        hSizer1.Add(self.all_checkbox, 0, wx.EXPAND, 10)
        hSizer1.Add( (0, 0), 1, wx.EXPAND, 10 )
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        buttons_sizer.Add(self.erase_button, 0, wx.ALL, 20)
        buttons_sizer.Add(self.dump_partition, 0, wx.ALL, 20)
        buttons_sizer.Add(self.close_button, 0, wx.ALL, 20)
        buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        vSizer.Add(warning_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(staticline, 0, wx.EXPAND, 5)
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
        self.erase_button.Bind(wx.EVT_BUTTON, self.OnErase)
        self.dump_partition.Bind(wx.EVT_BUTTON, self.OnDump)
        self.close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
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
        info.Text = "Partition"
        self.list.InsertColumn(0, info)

        res = self.device.get_partitions()
        itemDataMap = {}
        if res != -1:
            self.partitionCount = len(res)
            self.message_label.Label = f"{self.partitionCount} Partitions"
            for i, key in enumerate(res):
                if key != '':
                    index = self.list.InsertItem(self.list.GetItemCount(), key)
                    itemDataMap[i + 1] = (key)
                    row = self.list.GetItem(index)
                    self.list.SetItem(row)
                    self.list.SetItemData(index, i + 1)
                    # hide image
                    self.list.SetItemColumnImage(i, 0, -1)
            self.partitionCount = i
            self.message_label.Label = f"{str(i)} Partitions"
        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)

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
        if state and self.device.rooted:
            print("checking all Partitions\n")
            self.EnableDisableButton(True)
        else:
            print("Unchecking all Partitions\n")
            self.EnableDisableButton(False)
        self.Set_all_cb_clicked (False)

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
        elif i == self.partitionCount:
            self.all_checkbox.Set3StateValue(1)
            if self.device.rooted:
                self.EnableDisableButton(True)
        else:
            self.all_checkbox.Set3StateValue(2)
            if self.device.rooted:
                self.EnableDisableButton(True)

    # -----------------------------------------------
    #                  EnableDisableButton
    # -----------------------------------------------
    def EnableDisableButton(self, state):
        self.erase_button.Enable(state)
        self.dump_partition.Enable(state)

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
    #                  OnErase
    # -----------------------------------------------
    def OnErase(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Erase.")
        self.ApplyMultiAction('erase')

    # -----------------------------------------------
    #                  Erase
    # -----------------------------------------------
    def Erase(self, partition):
        if not self.device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return
        dlg = wx.MessageDialog(None, f"You have selected to ERASE partition: {partition}\nAre you sure want to continue?", f"Erase Partition: {partition}",wx.YES_NO | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        if result != wx.ID_YES:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled erasing  partition: {partition}.")
            return
        self.device.erase_partition(partition)

    # -----------------------------------------------
    #                  OnDump
    # -----------------------------------------------
    def OnDump(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed on Dump / Backup Partition")
        self.ApplyMultiAction('dump')

    # -----------------------------------------------
    #                  Dump
    # -----------------------------------------------
    def Dump(self, partition, multiple = False):
        if not self.device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return

        # delete existing partition dump if it exists on the phone
        path = f"/data/local/tmp/{partition}.img"
        res = self.device.delete(path)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to delete old partition image from the phone;\n}\n")
            return

        # partition dump on the phone
        res, file_path = self.device.dump_partition(file_path=path, partition=partition)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to dump partition on the phone;\n}\n")
            return

        if multiple:
            if not self.downloadFolder:
                with wx.DirDialog(None, "Choose a directory where all the partition dumps should be saved.", style=wx.DD_DEFAULT_STYLE) as folderDialog:
                    if folderDialog.ShowModal() == wx.ID_CANCEL:
                        print("User Cancelled dumping partitions (option: folder).")
                        self.abort = True
                        return     # the user changed their mind
                    self.downloadFolder = folderDialog.GetPath()
                    print(f"Selected Download Directory: {self.downloadFolder}")
            pathname =  os.path.join(self.downloadFolder, f"{partition}.img")
        else:
            with wx.FileDialog(self, "Dump partition", '', f"{partition}.img", wildcard="IMG files (*.img)|*.img", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    print(f"User Cancelled dumping partition: {partition}")
                    return     # the user changed their mind
                pathname = fileDialog.GetPath()
        try:
            if self.device:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                print(f"Dump partition to: {pathname}")
                self.device.pull_file(path, pathname)
                res = self.device.delete(path)
        except IOError:
            wx.LogError(f"Cannot save img file '{pathname}'.")
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))


    # -----------------------------------------------
    #                  GetListCtrl
    # -----------------------------------------------
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

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
        if not hasattr(self, "popupErase"):
            self.popupErase = wx.NewIdRef()
            self.popupDump = wx.NewIdRef()
            self.popupCheckAllBoxes = wx.NewIdRef()
            self.popupUnCheckAllBoxes = wx.NewIdRef()
            self.popupCopyClipboard = wx.NewIdRef()

            self.Bind(wx.EVT_MENU, self.OnpopupErase, id=self.popupErase)
            self.Bind(wx.EVT_MENU, self.OnPopupDump, id=self.popupDump)
            self.Bind(wx.EVT_MENU, self.OnCheckAllBoxes, id=self.popupCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnUnCheckAllBoxes, id=self.popupUnCheckAllBoxes)
            self.Bind(wx.EVT_MENU, self.OnCopyClipboard, id=self.popupCopyClipboard)

        # build the menu
        menu = wx.Menu()
        menu.Append(self.popupErase, "Erase Partition")
        menu.Append(self.popupDump, "Dump Partition")
        menu.Append(self.popupCheckAllBoxes, "Check All")
        menu.Append(self.popupUnCheckAllBoxes, "UnCheck All")
        menu.Append(self.popupCopyClipboard, "Copy to Clipboard")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  OnpopupErase
    # -----------------------------------------------
    def OnpopupErase(self, event):
        if self.device.rooted:
            self.ApplySingleAction(self.currentItem, 'erase')

    # -----------------------------------------------
    #                  OnPopupDump
    # -----------------------------------------------
    def OnPopupDump(self, event):
        if self.device.rooted:
            self.ApplySingleAction(self.currentItem, 'dump')

    # -----------------------------------------------
    #                  OnCopyClipboard
    # -----------------------------------------------
    def OnCopyClipboard(self, event):
        item = self.list.GetItem(self.currentItem)
        clipboard.copy(item.Text)

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
    #          Function ApplySingleAction
    # -----------------------------------------------
    def ApplySingleAction(self, index, action, fromMulti = False):
        partition = self.list.GetItem(index).Text

        if not self.device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return
        if action == "erase":
            print(f"Erasing {partition} ...")
            self.Erase(partition)
        elif action == "dump":
            print(f"Dumping {partition} ...")
            self.Dump(partition, fromMulti)
        return

    # -----------------------------------------------
    #          Function ApplyMultiAction
    # -----------------------------------------------
    def ApplyMultiAction(self, action):
        i = 0
        count = self.GetItemsCheckedCount()
        multi = False
        if count > 1:
            print(f"Processing {count} items ...")
            multi = True
        if action == 'dump':
            self.downloadFolder = None
        for index in range(self.list.GetItemCount()):
            if self.abort:
                self.abort = False
                break
            if self.list.IsItemChecked(index):
                self.ApplySingleAction(index, action, multi)
                i += 1
        print(f"Total count of partition actions attempted: {i}")

