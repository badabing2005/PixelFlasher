#!/usr/bin/env python

import wx
import wx.lib.mixins.listctrl as listmix
import traceback
import images as images
import darkdetect
import markdown
import wx.html
import webbrowser
from file_editor import FileEditor
from runtime import *


# ============================================================================
#                               Class HtmlWindow
# ============================================================================
class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

# ============================================================================
#                               Class ListCtrl
# ============================================================================
class ListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
#                               Class MagiskModules
# ============================================================================
class MagiskModules(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle("Manage Magisk")

        # Instance variable to store current selected module
        self.module = None

        # Message label
        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "When you press the OK button, the Modules with checkbox selected will be enabled and the rest will be disabled."
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.message_label.SetForegroundColour(wx.Colour(255, 0, 0))

        # Module label
        modules_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"Magisk Modules")
        modules_label.SetToolTip(u"Enable / Disable Magisk modules")

        # Modules list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.download_24.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.download_16.GetBitmap())
        self.list  = ListCtrl(self, -1, size=(-1, self.CharHeight * 18), style = wx.LC_REPORT | wx.LC_SINGLE_SEL )
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # Change Log
        # self.html = HtmlWindow(self, wx.ID_ANY, size=(-1, -1))
        self.html = HtmlWindow(self, wx.ID_ANY)
        if darkdetect.isDark():
            black_html = "<!DOCTYPE html>\n<html><body style=\"background-color:#1e1e1e;\"></body></html>"
            self.html.SetPage(black_html)
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.html.SetStandardFonts()

        # Ok button
        self.ok_button = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)

        # Install module button
        self.install_module_button = wx.Button(self, wx.ID_ANY, u"Install Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.install_module_button.SetToolTip(u"Install magisk module.")

        # update module button
        self.update_module_button = wx.Button(self, wx.ID_ANY, u"Update Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.update_module_button.SetToolTip(u"Update magisk module.")
        self.update_module_button.Enable(False)

        # Play Integrity Fix button
        self.pif_button = wx.Button(self, wx.ID_ANY, u"Install Pif Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.pif_button.SetToolTip(u"Install Play Integrity Fix module.")

        # option button json / prop
        json_prop_option_button = wx.RadioBox(self, choices=["json", "prop"], style=wx.RA_SPECIFY_COLS)
        json_prop_option_button.Enable(False)

        # Edit pif.json button
        self.edit_pif_button = wx.Button(self, wx.ID_ANY, u"Edit pif.json", wx.DefaultPosition, wx.DefaultSize, 0)
        self.edit_pif_button.SetToolTip(u"Edit pif.json.")
        self.edit_pif_button.Enable(False)

        # Kill  gms button
        self.kill_gms_button = wx.Button(self, wx.ID_ANY, u"Kill Google GMS", wx.DefaultPosition, wx.DefaultSize, 0)
        self.kill_gms_button.SetToolTip(u"Kill Google GMS process, required after pif edit to avoid a reboot.")
        self.kill_gms_button.Enable(False)

        # Systemless hosts button
        self.systemless_hosts_button = wx.Button(self, wx.ID_ANY, u"Systemless Hosts", wx.DefaultPosition, wx.DefaultSize, 0)
        self.systemless_hosts_button.SetToolTip(u"Add Systemless Hosts Module.")

        # Enable zygisk button
        self.enable_zygisk_button = wx.Button(self, wx.ID_ANY, u"Enable Zygisk", wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_zygisk_button.SetToolTip(u"Enable Magisk zygisk (requires reboot)")

        # Disable zygisk button
        self.disable_zygisk_button = wx.Button(self, wx.ID_ANY, u"Disable Zygisk", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_zygisk_button.SetToolTip(u"Disable Magisk zygisk (requires reboot)")

        # Enable denlylist button
        self.enable_denylist_button = wx.Button(self, wx.ID_ANY, u"Enable Denylist", wx.DefaultPosition, wx.DefaultSize, 0)
        self.enable_denylist_button.SetToolTip(u"Enable Magisk denylist")

        # Disable denylist button
        self.disable_denylist_button = wx.Button(self, wx.ID_ANY, u"Disable Denylist", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_denylist_button.SetToolTip(u"Disable Magisk denylist")

        # Cancel button
        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)

        # Make the buttons the same size
        button_width = self.systemless_hosts_button.GetSize()[0] + 10
        self.install_module_button.SetMinSize((button_width, -1))
        self.update_module_button.SetMinSize((button_width, -1))
        self.pif_button.SetMinSize((button_width, -1))
        self.edit_pif_button.SetMinSize((button_width, -1))
        self.kill_gms_button.SetMinSize((button_width, -1))
        self.systemless_hosts_button.SetMinSize((button_width, -1))
        self.enable_zygisk_button.SetMinSize((button_width, -1))
        self.disable_zygisk_button.SetMinSize((button_width, -1))
        self.enable_denylist_button.SetMinSize((button_width, -1))
        self.disable_denylist_button.SetMinSize((button_width, -1))

        # Label for managing denylist and SU Permissions
        management_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"To manage denylist or to manage SU permissions, use PixelFlasher's App Manager feature.")
        management_label.SetToolTip(u"Use Pixelflasher's App Manager functionality to add/remove items to denylist or su permissions.")
        font = management_label.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        management_label.SetFont(font)

        # populate the list
        self.PopulateList()

        # Sizers
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        list_sizer.Add(self.list, 1, wx.ALL, 10)

        h_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        h_buttons_sizer.Add(self.ok_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        v_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        v_buttons_sizer.Add(self.install_module_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.update_module_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.pif_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.systemless_hosts_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.enable_zygisk_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.disable_zygisk_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.enable_denylist_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.disable_denylist_button, 0, wx.ALL, 10)
        v_buttons_sizer.AddSpacer(90)
        v_buttons_sizer.Add(json_prop_option_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=0)
        v_buttons_sizer.Add(self.edit_pif_button, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.kill_gms_button, 0, wx.ALL, 10)


        modules_sizer = wx.BoxSizer(wx.VERTICAL)
        modules_sizer.Add(list_sizer, 2, wx.EXPAND, 5)
        modules_sizer.Add(self.html, 1, wx.EXPAND | wx.ALL, 10)

        outside_modules_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outside_modules_sizer.Add(modules_sizer, 1, wx.EXPAND | wx.ALL, 0)
        outside_modules_sizer.Add(v_buttons_sizer, 0, wx.ALL, 0)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(modules_label, 0, wx.LEFT, 10)
        vSizer.Add(outside_modules_sizer, 1, wx.EXPAND, 0)
        vSizer.Add(management_label, 0, wx.LEFT, 10)
        vSizer.Add(h_buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self.onOk)
        self.install_module_button.Bind(wx.EVT_BUTTON, self.onInstallModule)
        self.update_module_button.Bind(wx.EVT_BUTTON, self.onUpdateModule)
        self.pif_button.Bind(wx.EVT_BUTTON, self.onInstallPif)
        self.edit_pif_button.Bind(wx.EVT_BUTTON, self.onEditPifProp)
        self.kill_gms_button.Bind(wx.EVT_BUTTON, self.onKillGms)
        self.systemless_hosts_button.Bind(wx.EVT_BUTTON, self.onSystemlessHosts)
        self.enable_zygisk_button.Bind(wx.EVT_BUTTON, self.onEnableZygisk)
        self.disable_zygisk_button.Bind(wx.EVT_BUTTON, self.onDisableZygisk)
        self.enable_denylist_button.Bind(wx.EVT_BUTTON, self.onEnableDenylist)
        self.disable_denylist_button.Bind(wx.EVT_BUTTON, self.onDisableDenylist)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.list)
        json_prop_option_button.Bind(wx.EVT_RADIOBOX, self.onJsonProp_selected)

        # Autosize the dialog
        self.list.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)
        a = self.list.GetViewRect()
        self.SetSize(vSizer.MinSize.Width + 120, vSizer.MinSize.Height + 140)

        print("\nOpening Magisk Modules Manager ...")

    # -----------------------------------------------
    #              Function PopulateList
    # -----------------------------------------------
    def PopulateList(self, refresh=False):
        device = get_phone()
        if not device.rooted:
            return
        modules = device.get_magisk_detailed_modules(refresh)

        self.pif_button.Enable(True)
        self.edit_pif_button.Enable(False)
        self.kill_gms_button.Enable(False)

        self.list.InsertColumn(0, 'ID', width = -1)
        self.list.InsertColumn(1, 'Name', width = -1)
        self.list.InsertColumn(2, 'Version', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(3, 'Description', wx.LIST_FORMAT_LEFT,  -1)
        if sys.platform == "win32":
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))

        self.list.EnableCheckBoxes()

        if modules:
            i = 0
            for module in modules:
                if module.id == '':
                    if len(modules) == 1:
                        continue
                    else:
                        index = self.list.InsertItem(i, module.dirname)
                else:
                    index = self.list.InsertItem(i, module.id)

                # disable pif button if it is already installed.
                if module.id == "playintegrityfix" and module.name == "Play Integrity Fix":
                    self.pif_button.Enable(False)
                    self.check_pif_json()
                    self.edit_pif_button.Enable(True)
                    self.kill_gms_button.Enable(True)

                # disable Systemless Hosts button if it is already installed.
                if module.id == "hosts" and module.name == "Systemless Hosts":
                    self.systemless_hosts_button.Enable(False)

                if module.updateAvailable:
                    self.list.SetItemColumnImage(i, 0, 0)
                else:
                    self.list.SetItemColumnImage(i, 0, -1)

                self.list.SetItem(index, 1, module.name)
                if module.version == '':
                    self.list.SetItem(index, 2, module.versionCode)
                else:
                    self.list.SetItem(index, 2, module.version)
                self.list.SetItem(index, 3, module.description)

                if module.state == 'enabled':
                    self.list.CheckItem(index, check=True)
                i += 1

        self.list.SetColumnWidth(0, -2)
        grow_column(self.list, 0, 20)
        self.list.SetColumnWidth(1, -2)
        grow_column(self.list, 1, 20)
        self.list.SetColumnWidth(2, -2)
        grow_column(self.list, 2, 20)
        self.list.SetColumnWidth(3, -2)
        grow_column(self.list, 3, 20)

    # -----------------------------------------------
    #                  check_pif_json
    # -----------------------------------------------
    def check_pif_json(self):
        device = get_phone()
        if not device.rooted:
            return
        # check for presence of pif.json
        res, tmp = device.check_file("/data/adb/modules/playintegrityfix/pif.json", True)
        if res == 1:
            # pif.json exists, change button to Edit
            self.edit_pif_button.SetLabel("Edit pif.json")
            self.edit_pif_button.SetToolTip(u"Edit pif.json.")
        elif res == 0:
            # pif.json does not exits, change button to create
            self.edit_pif_button.SetLabel("Create pif.json")
            self.edit_pif_button.SetToolTip(u"Create and upload pif.json.")

    # -----------------------------------------------
    #                  onJsonProp_selected
    # -----------------------------------------------
    def onJsonProp_selected(self, event):
        option = event.GetString()
        if option == "json":
            print("JSON option selected")
        elif option == "prop":
            print("Prop option selected")

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  onItemSelected
    # -----------------------------------------------
    def onItemSelected(self, event):
        self.currentItem = event.Index
        device = get_phone()
        if not device.rooted:
            return
        print(f"Magisk Module {self.list.GetItemText(self.currentItem)} is selected.")
        # puml(f":Select Magisk Module {self.list.GetItemText(self.currentItem)};\n")

        # Get the module object for the selected item
        modules = device.get_magisk_detailed_modules(refresh=False)
        self.module = modules[self.currentItem]
        self.html.SetPage('')
        if self.module.updateAvailable:
            self.update_module_button.Enable(True)
            if self.module.updateDetails.changelog:
                changelog_md = f"# Change Log:\n{self.module.updateDetails.changelog}"
                # convert markdown to html
                changelog_html = markdown.markdown(changelog_md)
                self.html.SetPage(changelog_html)
        else:
            self.update_module_button.Enable(False)
        event.Skip()

    # -----------------------------------------------
    #                  onCancel
    # -----------------------------------------------
    def onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    # -----------------------------------------------
    #                  onEnableZygisk
    # -----------------------------------------------
    def onEnableZygisk(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Enable Zygisk")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        device.magisk_enable_zygisk(True)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onDisableZygisk
    # -----------------------------------------------
    def onDisableZygisk(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Disable Zygisk")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        device.magisk_enable_zygisk(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onEnableDenylist
    # -----------------------------------------------
    def onEnableDenylist(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Enable Denylist")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        device.magisk_enable_denylist(True)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onDisableDenylist
    # -----------------------------------------------
    def onDisableDenylist(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Disable Denylist")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        device.magisk_enable_denylist(False)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onSystemlessHosts
    # -----------------------------------------------
    def onSystemlessHosts(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Add Systemless Hosts")
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        device.magisk_add_systemless_hosts()
        self.list.ClearAll()
        self.PopulateList(True)
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onInstallPif
    # -----------------------------------------------
    def onInstallPif(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            url = check_module_update(PIF_UPDATE_URL)
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            print(f"Installing Play Integrity Fix module URL: {url} ...")
            downloaded_file_path = download_file(url)
            device.install_magisk_module(downloaded_file_path)
            self.list.ClearAll()
            self.PopulateList(True)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Play Integrity Fix module installation.")
            traceback.print_exc()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onKillGms
    # -----------------------------------------------
    def onKillGms(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            print("Killing Google GMS  ...")
            res = device.perform_package_action(pkg='com.google.android.gms.unstable', action='killall')
            if res.returncode != 0:
                print("Error killing GMS.")
            else:
                print("Killing Google GMS succeeded.")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during killing GMS.")
            traceback.print_exc()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onEditPifProp
    # -----------------------------------------------
    def onEditPifProp(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            config_path = get_config_path()
            pif_prop = os.path.join(config_path, 'tmp', 'pif.json')
            if self.edit_pif_button.GetLabel() == "Edit pif.json":
                # pull the file
                res = device.pull_file("/data/adb/modules/playintegrityfix/pif.json", pif_prop, True)
                if res != 0:
                    print("Aborting ...\n")
                    # puml("#red:Failed to pull pif.prop from the phone;\n}\n")
                    self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
                    return
            else:
                # we need to create one.
                with open(pif_prop, 'w') as file:
                    pass
            dlg = FileEditor(self, pif_prop, "json", width=1200, height=400)
            dlg.CenterOnParent()
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                # get the contents of modified pif.json
                with open(pif_prop, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    contents = f.read()
                print(f"\npif.prep file has been modified!")
                # push the file
                res = device.push_file(pif_prop, "/data/adb/modules/playintegrityfix/pif.json", True)
                if res != 0:
                    print("Aborting ...\n")
                    # puml("#red:Failed to push pif.json from the phone;\n}\n")
                    self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
                    return -1
                self.check_pif_json()
            else:
                print("User cancelled editing pif.json file.")
                puml(f"note right\nCancelled and Aborted\nend note\n")
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
                return -1
            self.check_pif_json()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during pip edit process.")
            traceback.print_exc()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onUpdateModule
    # -----------------------------------------------
    def onUpdateModule(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            id = self.list.GetItem(self.currentItem, 0).Text
            name = self.list.GetItem(self.currentItem, 1).Text
            print(f"Updating Module {name} ...")
            if self.module and self.module.updateAvailable and self.module.updateDetails and (self.module.id and self.module.id == id) and (self.module.name and self.module.name == name):
                url = self.module.updateDetails.zipUrl
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                print(f"Downloading Magisk Module: {name} URL: {url} ...")
                downloaded_file_path = download_file(url)
                device.install_magisk_module(downloaded_file_path)
                self.list.ClearAll()
                self.PopulateList(True)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules update")
            traceback.print_exc()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onInstallModule
    # -----------------------------------------------
    def onInstallModule(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Install Module.")
        with wx.FileDialog(self, "select Module file to install", '', '', wildcard="Magisk Modules (*.*.zip)|*.zip", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled module install.")
                return
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
                device.install_magisk_module(pathname)
                self.list.ClearAll()
                self.PopulateList(True)
            except IOError:
                wx.LogError(f"Cannot install module file '{pathname}'.")
                traceback.print_exc()
        self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    # -----------------------------------------------
    #                  onOk
    # -----------------------------------------------
    def onOk(self, e):
        device = get_phone()
        if not device.rooted:
            self.EndModal(wx.ID_OK)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        modules = device.get_magisk_detailed_modules()
        for i in range(0, self.list.ItemCount, 1):
            if modules[i].state == 'enabled':
                module_state = True
            else:
                module_state = False
            list_state = self.list.IsItemChecked(i)

            if list_state == module_state:
                print(f"Module: {modules[i].name:<36} state has not changed,   Nothing to do. [Kept {modules[i].state.upper()}]")
            elif list_state:
                print(f"Module: {modules[i].name:<36} state has changed,       ENABLING  the module ...")
                res = device.enable_magisk_module(modules[i].dirname)
                if res == 0:
                    modules[i].state = 'enabled'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
            else:
                print(f"Module: {modules[i].name:<36} state has changed,       DISABLING the module ...")
                res = device.disable_magisk_module(modules[i].dirname)
                if res == 0:
                    modules[i].state = 'disbled'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to disable module: {modules[i].name}")
        print('')
        self.EndModal(wx.ID_OK)

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
