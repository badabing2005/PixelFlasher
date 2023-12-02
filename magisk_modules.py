#!/usr/bin/env python

import wx
import wx.lib.mixins.listctrl as listmix
import traceback
import html
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

    def CopySelectedText(self):
        selection = self.SelectionToText()
        if selection:
            data = wx.TextDataObject()
            data.SetText(selection)
            clipboard = wx.Clipboard.Get()
            clipboard.Open()
            clipboard.SetData(data)
            clipboard.Close()

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
        wx.Dialog.__init__(self, *args, **kwargs, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=(1600, 1200))
        self.SetTitle("Manage Magisk")
        self.pif_json_path = PIF_JSON_PATH

        # Instance variable to store current selected module
        self.module = None
        self.pi_app = 'gr.nikolasspyr.integritycheck'
        self.coords = Coords()

        # Message label
        self.message_label = wx.StaticText(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.message_label.Wrap(-1)
        self.message_label.Label = "When you press the OK button, the Modules with checkbox selected will be enabled and the rest will be disabled."
        if sys.platform == "win32":
            self.message_label.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.message_label.SetForegroundColour(wx.Colour(255, 0, 0))

        # Module label
        self.modules_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"Magisk Modules")
        self.modules_label.SetToolTip(u"Enable / Disable Magisk modules")
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.modules_label.SetFont(font)

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
        self.html = HtmlWindow(self, wx.ID_ANY, size=(-1, 254))
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

        # UnInstall module button
        self.uninstall_module_button = wx.Button(self, wx.ID_ANY, u"Uninstall Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.uninstall_module_button.SetToolTip(u"Uninstall magisk module.")
        self.uninstall_module_button.Enable(False)

        # Play Integrity Fix button
        self.pif_button = wx.Button(self, wx.ID_ANY, u"Install Pif Module", wx.DefaultPosition, wx.DefaultSize, 0)
        self.pif_button.SetToolTip(u"Install Play Integrity Fix module.")

        # Edit pif.json button
        self.edit_pif_button = wx.Button(self, wx.ID_ANY, u"Edit pif.json", wx.DefaultPosition, wx.DefaultSize, 0)
        self.edit_pif_button.SetToolTip(u"Edit pif.json.")
        self.edit_pif_button.Enable(False)

        # Kill  gms button
        self.kill_gms_button = wx.Button(self, wx.ID_ANY, u"Kill Google GMS", wx.DefaultPosition, wx.DefaultSize, 0)
        self.kill_gms_button.SetToolTip(u"Kill Google GMS process, required after pif edit to avoid a reboot.")
        self.kill_gms_button.Enable(False)
        self.kill_gms_button.Show(False)

        # Process build.prop button
        self.process_build_prop_button = wx.Button(self, wx.ID_ANY, u"Process build.prop", wx.DefaultPosition, wx.DefaultSize, 0)
        self.process_build_prop_button.SetToolTip(u"Process build.prop to extract pif.json.")

        # option button PI Selectedion
        self.pi_option = wx.RadioBox(self, choices=["Play Integrity API Checker", "Simple Play Integrity Checker", "TB Checker"], style=wx.RA_VERTICAL)

        # Play Integrity API Checkerbutton
        self.pi_checker_button = wx.Button(self, wx.ID_ANY, u"Play Integrity Check", wx.DefaultPosition, wx.DefaultSize, 0)
        self.pi_checker_button.SetToolTip(u"Play Integrity API Checker\nNote: Need to install app from Play store.")

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
        button_width = self.pi_option.GetSize()[0] + 10
        self.install_module_button.SetMinSize((button_width, -1))
        self.update_module_button.SetMinSize((button_width, -1))
        self.uninstall_module_button.SetMinSize((button_width, -1))
        self.pif_button.SetMinSize((button_width, -1))
        self.edit_pif_button.SetMinSize((button_width, -1))
        self.kill_gms_button.SetMinSize((button_width, -1))
        self.process_build_prop_button.SetMinSize((button_width, -1))
        self.pi_checker_button.SetMinSize((button_width, -1))
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
        self.add_magisk_details()

        # Sizers
        message_sizer = wx.BoxSizer(wx.HORIZONTAL)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        message_sizer.Add(self.message_label, 0, wx.ALL, 20)
        message_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        h_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        h_buttons_sizer.Add(self.ok_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        v_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        v_buttons_sizer.Add(self.install_module_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.update_module_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.uninstall_module_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.pif_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.systemless_hosts_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.enable_zygisk_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.disable_zygisk_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.enable_denylist_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.disable_denylist_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.AddStretchSpacer()
        v_buttons_sizer.Add(self.process_build_prop_button, 0, wx.RIGHT, 10)
        v_buttons_sizer.Add(self.edit_pif_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.kill_gms_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.pi_option, 0, wx.ALL, 5)
        v_buttons_sizer.Add(self.pi_checker_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 10)

        modules_sizer = wx.BoxSizer(wx.VERTICAL)
        modules_sizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 10)
        modules_sizer.Add(self.html, 0, wx.EXPAND | wx.ALL, 10)

        outside_modules_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outside_modules_sizer.Add(modules_sizer, 1, wx.EXPAND | wx.ALL, 0)
        outside_modules_sizer.Add(v_buttons_sizer, 0, wx.EXPAND | wx.ALL, 0)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(message_sizer, 0, wx.EXPAND, 5)
        vSizer.Add(self.modules_label, 0, wx.LEFT, 10)
        vSizer.Add(outside_modules_sizer, 1, wx.EXPAND, 0)
        vSizer.Add(management_label, 0, wx.LEFT, 10)
        vSizer.Add(h_buttons_sizer, 0, wx.EXPAND, 5)

        self.SetSizer(vSizer)
        self.SetMinSize((400, 300))
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self.onOk)
        self.install_module_button.Bind(wx.EVT_BUTTON, self.onInstallModule)
        self.update_module_button.Bind(wx.EVT_BUTTON, self.onUpdateModule)
        self.uninstall_module_button.Bind(wx.EVT_BUTTON, self.onUninstallModule)
        self.pif_button.Bind(wx.EVT_BUTTON, self.onInstallPif)
        self.edit_pif_button.Bind(wx.EVT_BUTTON, self.onEditPifProp)
        self.kill_gms_button.Bind(wx.EVT_BUTTON, self.onKillGms)
        self.process_build_prop_button.Bind(wx.EVT_BUTTON, self.onProcessBuildProp)
        self.pi_checker_button.Bind(wx.EVT_BUTTON, self.onPiChecker)
        self.systemless_hosts_button.Bind(wx.EVT_BUTTON, self.onSystemlessHosts)
        self.enable_zygisk_button.Bind(wx.EVT_BUTTON, self.onEnableZygisk)
        self.disable_zygisk_button.Bind(wx.EVT_BUTTON, self.onDisableZygisk)
        self.enable_denylist_button.Bind(wx.EVT_BUTTON, self.onEnableDenylist)
        self.disable_denylist_button.Bind(wx.EVT_BUTTON, self.onDisableDenylist)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.list)
        self.pi_option.Bind(wx.EVT_RADIOBOX, self.onPiSelection)
        self.html.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        self.list.Bind(wx.EVT_LEFT_DOWN, self.onModuleSelection)

        # Autosize the dialog
        # self.list.PostSizeEventToParent()
        # self.SetSizerAndFit(vSizer)
        # a = self.list.GetViewRect()
        # self.SetSize(vSizer.MinSize.Width + 120, vSizer.MinSize.Height + 140)

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
        self.pi_checker_button.Enable(False)

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
                if module.id == "playintegrityfix" and "Play Integrity" in module.name:
                    if module.name == "Play Integrity Fork":
                        self.pif_json_path = '/data/adb/modules/playintegrityfix/custom.pif.json'
                    self.pif_button.Enable(False)
                    self.check_pif_json()
                    self.edit_pif_button.Enable(True)
                    self.kill_gms_button.Enable(True)
                    self.pi_checker_button.Enable(True)

                # disable Systemless Hosts button if it is already installed.
                if module.id == "hosts" and module.name == "Systemless Hosts":
                    self.systemless_hosts_button.Enable(False)

                self.list.SetItemColumnImage(i, 0, -1)
                with contextlib.suppress(Exception):
                    if module.updateAvailable:
                        self.list.SetItemColumnImage(i, 0, 0)

                self.list.SetItem(index, 1, module.name)
                if module.version == '':
                    self.list.SetItem(index, 2, module.versionCode)
                else:
                    self.list.SetItem(index, 2, module.version)
                self.list.SetItem(index, 3, module.description)

                if module.state == 'enabled':
                    self.list.CheckItem(index, check=True)
                elif module.state == 'remove':
                    self.list.SetItemTextColour(index, wx.LIGHT_GREY)

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
    #                  add_magisk_details
    # -----------------------------------------------
    def add_magisk_details(self):
        device = get_phone()
        if not device:
            return

        data = f"Magisk Manager Version:  {device.magisk_app_version}\n"
        if device.rooted:
            data += f"Magisk Version:          {device.magisk_version}\n"
        data += "\nMagisk Modules"
        self.modules_label.SetLabel(data)

    # -----------------------------------------------
    #                  check_pif_json
    # -----------------------------------------------
    def check_pif_json(self):
        device = get_phone()
        if not device.rooted:
            return
        # check for presence of pif.json
        res, tmp = device.check_file(self.pif_json_path, True)
        if res == 1:
            # pif.json exists, change button to Edit
            self.edit_pif_button.SetLabel("Edit pif.json")
            self.edit_pif_button.SetToolTip(u"Edit pif.json.")
        elif res == 0:
            # pif.json does not exits, change button to create
            self.edit_pif_button.SetLabel("Create pif.json")
            self.edit_pif_button.SetToolTip(u"Create and upload pif.json.")

    # -----------------------------------------------
    #                  onPiSelection
    # -----------------------------------------------
    def onPiSelection(self, event):
        option = event.GetString()

        if option == "Play Integrity API Checker":
            print("Play Integrity API Checker option selected")
            self.pi_app = 'gr.nikolasspyr.integritycheck'

        elif option == "Simple Play Integrity Checker":
            print("Simple Play Integrity Checker option selected")
            self.pi_app = 'com.henrikherzig.playintegritychecker'

        elif option == "TB Checker":
            print("TB Checker option selected")
            self.pi_app = 'krypton.tbsafetychecker'

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  onModuleSelection
    # -----------------------------------------------
    def onModuleSelection(self, event):
        x,y = event.GetPosition()
        row,flags = self.list.HitTest((x,y))
        if row == -1:
            self.uninstall_module_button.Enable(False)
            self.uninstall_module_button.SetLabel('Uninstall Module')
        else:
            self.uninstall_module_button.Enable(True)
            if self.list.GetItemTextColour(row) == wx.LIGHT_GREY:
                self.uninstall_module_button.SetLabel('Restore Module')
            else:
                self.uninstall_module_button.SetLabel('Uninstall Module')
        event.Skip()

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
        self._on_spin('start')
        device.magisk_enable_zygisk(True)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onDisableZygisk
    # -----------------------------------------------
    def onDisableZygisk(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Disable Zygisk")
        self._on_spin('start')
        device.magisk_enable_zygisk(False)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onEnableDenylist
    # -----------------------------------------------
    def onEnableDenylist(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Enable Denylist")
        self._on_spin('start')
        device.magisk_enable_denylist(True)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onDisableDenylist
    # -----------------------------------------------
    def onDisableDenylist(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Disable Denylist")
        self._on_spin('start')
        device.magisk_enable_denylist(False)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onSystemlessHosts
    # -----------------------------------------------
    def onSystemlessHosts(self, e):
        device = get_phone()
        if not device.rooted:
            return
        print("Add Systemless Hosts")
        self._on_spin('start')
        device.magisk_add_systemless_hosts()
        self.refresh_modules()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onInstallPif
    # -----------------------------------------------
    def onInstallPif(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            url = check_module_update(PIF_UPDATE_URL)
            self._on_spin('start')
            print(f"Installing Play Integrity Fix module URL: {url} ...")
            downloaded_file_path = download_file(url)
            device.install_magisk_module(downloaded_file_path)
            self.refresh_modules()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Play Integrity Fix module installation.")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onKillGms
    # -----------------------------------------------
    def onKillGms(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            self._on_spin('start')
            print("Killing Google GMS  ...")
            res = device.perform_package_action(pkg='com.google.android.gms.unstable', action='killall')
            if res.returncode != 0:
                print("Error killing GMS.")
            else:
                print("Killing Google GMS succeeded.")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during killing GMS.")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onEditPifProp
    # -----------------------------------------------
    def onEditPifProp(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            self._on_spin('start')
            config_path = get_config_path()
            pif_prop = os.path.join(config_path, 'tmp', 'pif.json')
            if self.edit_pif_button.GetLabel() == "Edit pif.json":
                # pull the file
                res = device.pull_file(self.pif_json_path, pif_prop, True)
                if res != 0:
                    print("Aborting ...\n")
                    # puml("#red:Failed to pull pif.prop from the phone;\n}\n")
                    self._on_spin('stop')
                    return
            else:
                # we need to create one.
                with open(pif_prop, 'w') as file:
                    pass
            dlg = FileEditor(self.Parent, pif_prop, "json", width=1200, height=400)
            dlg.CenterOnParent()
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                # get the contents of modified pif.json
                with open(pif_prop, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    contents = f.read()
                print(f"\npif.prep file has been modified!")
                # push the file
                res = device.push_file(pif_prop, self.pif_json_path, True)
                if res != 0:
                    print("Aborting ...\n")
                    # puml("#red:Failed to push pif.json from the phone;\n}\n")
                    self._on_spin('stop')
                    return -1

                print("Killing Google GMS  ...")
                res = device.perform_package_action(pkg='com.google.android.gms.unstable', action='killall')
                if res.returncode != 0:
                    print("Error killing GMS.")
                else:
                    print("Killing Google GMS succeeded.")

                self.check_pif_json()
            else:
                print("User cancelled editing pif.json file.")
                puml(f"note right\nCancelled and Aborted\nend note\n")
                self._on_spin('stop')
                return -1
            self.check_pif_json()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during pip edit process.")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onUninstallModule
    # -----------------------------------------------
    def onUninstallModule(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            id = self.list.GetItem(self.currentItem, 0).Text
            name = self.list.GetItem(self.currentItem, 1).Text
            modules = device.get_magisk_detailed_modules()
            self._on_spin('start')
            for i in range(0, self.list.ItemCount, 1):
                if modules[i].dirname == id:
                    if modules[i].state == 'remove':
                        print(f"Restoring Module {name} ...")
                        res = device.restore_magisk_module(modules[i].dirname)
                    else:
                        print(f"Uninstalling Module {name} ...")
                        res = device.uninstall_magisk_module(modules[i].dirname)
                    if res == 0:
                        modules[i].state = 'remove'
                        self.refresh_modules()
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to remove module: {modules[i].name}")
                    break
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules uninstall")
            traceback.print_exc()
        self._on_spin('stop')

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
                self._on_spin('start')
                print(f"Downloading Magisk Module: {name} URL: {url} ...")
                downloaded_file_path = download_file(url)
                device.install_magisk_module(downloaded_file_path)
            self.refresh_modules()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules update")
            traceback.print_exc()
        self._on_spin('stop')

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
                self._on_spin('start')
                device.install_magisk_module(pathname)
                self.refresh_modules()
            except IOError:
                wx.LogError(f"Cannot install module file '{pathname}'.")
                traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  get_pi_app_coords
    # -----------------------------------------------
    def get_pi_app_coords(self):
        try:
            device = get_phone()
            if not device.rooted:
                return
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Getting coordinates for {self.pi_app}")

            # pull view
            config_path = get_config_path()
            pi_app_xml = os.path.join(config_path, 'tmp', 'pi_app.xml')

            # Do this to find out the string to look for
            # return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml)

            if self.pi_app == 'gr.nikolasspyr.integritycheck':
                return  device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "CHECK", False)

            elif self.pi_app == 'com.henrikherzig.playintegritychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Make Play Integrity Request", False)

            elif self.pi_app == 'krypton.tbsafetychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Run Play Integrity Check", False)

        except IOError:
            traceback.print_exc()

    # -----------------------------------------------
    #                  onPiChecker
    # -----------------------------------------------
    def onPiChecker(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Play Integrity API Checker.")
            self._on_spin('start')

            # We need to kill TB Checker to make sure we read fresh values
            if self.pi_option.Selection == 2:
                res = device.perform_package_action(self.pi_app, 'kill', False)

            # launch the app
            res = device.perform_package_action(self.pi_app, 'launch', False)
            if res == -1:
                print(f"Error: during launching app {self.pi_app}.")
                self._on_spin('stop')
                return -1

            # See if we have coordinates saved
            coords = self.coords.query_entry(device.id, self.pi_app)
            if coords is None:
                # Get coordinates for the first time
                coords = self.get_pi_app_coords()
                if coords is not None and coords != -1:
                    # update coords.json
                    self.coords.update_entry(device.id, self.pi_app, coords)
                else:
                    print("Error: Could not get coordinates.")
                    self._on_spin('stop')
                    return -1

            # Click on coordinates
            res = device.click(coords)
            if res == -1:
                print(f"Error: during tapping {self.pi_app}.")
                self._on_spin('stop')
                return -1

            # pull view
            config_path = get_config_path()
            pi_xml = os.path.join(config_path, 'tmp', 'pi.xml')
            res = device.ui_action('/data/local/tmp/pi.xml', pi_xml)
            if res == -1:
                print(f"Error: during uiautomator {self.pi_app}.")
                self._on_spin('stop')
                return -1

            # extract result
            time.sleep(2)
            if self.pi_option.Selection == 0:
                time.sleep(5)
                res = process_pi_xml(pi_xml)
            if self.pi_option.Selection == 1:
                res = process_pi_xml2(pi_xml)
            if self.pi_option.Selection == 2:
                time.sleep(5)
                res = process_pi_xml3(pi_xml)
            if res == -1:
                print(f"Error: during processing the response from {self.pi_app}.")
                self._on_spin('stop')
                return -1

            pi_print_html = f"<pre>{html.escape(res)}</pre>"
            self.html.SetPage(pi_print_html)

        except IOError:
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onProcessBuildProp
    # -----------------------------------------------
    def onProcessBuildProp(self, e):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Process build.prop")
        with wx.FileDialog(self, "select build.prop file to process", '', '', wildcard="build.prop files (*.*.prop)|*.prop", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled processing build.prop")
                return
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for processing.")
            try:
                self._on_spin('start')
                with open(pathname, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    content = f.readlines()

                contentList = [x.strip().split('#')[0].split('=', 1) for x in content if '=' in x.split('#')[0]]
                contentDict = dict(contentList)
                for k, v in contentList:
                    for x in v.split('$')[1:]:
                        key = re.findall(r'\w+', x)[0]
                        v = v.replace(f'${key}', contentDict[key])
                    contentDict[k] = v.strip()

                # PRODUCT
                keys = ['ro.product.name', 'ro.product.system.name', 'ro.product.product.name']
                ro_product_name = get_first_match(contentDict, keys)

                # DEVICE
                keys = ['ro.product.device', 'ro.product.system.device', 'ro.product.product.device']
                ro_product_device = get_first_match(contentDict, keys)

                # MANUFACTURER
                keys = ['ro.product.manufacturer', 'ro.product.system.manufacturer', 'ro.product.product.manufacturer']
                ro_product_manufacturer = get_first_match(contentDict, keys)

                # BRAND
                keys = ['ro.product.brand', 'ro.product.system.brand', 'ro.product.product.brand']
                ro_product_brand = get_first_match(contentDict, keys)

                # MODEL
                keys = ['ro.product.model', 'ro.product.system.model', 'ro.product.product.model']
                ro_product_model = get_first_match(contentDict, keys)

                # FINGERPRINT
                keys = ['ro.build.fingerprint', 'ro.system.build.fingerprint', 'ro.product.build.fingerprint']
                ro_build_fingerprint = get_first_match(contentDict, keys)

                # SECURITY_PATCH
                keys = ['ro.build.version.security_patch']
                ro_build_version_security_patch = get_first_match(contentDict, keys)

                # FIRST_API_LEVEL
                keys = ['ro.product.first_api_level', 'ro.board.first_api_level', 'ro.board.api_level', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.vendor.build.version.sdk', 'ro.product.build.version.sdk']
                ro_product_first_api_level = get_first_match(contentDict, keys)
                if ro_product_first_api_level and int(ro_product_first_api_level) > 32:
                    ro_product_first_api_level = '32'

                if ro_build_fingerprint is None:
                    keys = ['ro.build.version.release']
                    ro_build_version_release = get_first_match(contentDict, keys)

                    keys = ['ro.build.id']
                    ro_build_id = get_first_match(contentDict, keys)

                    keys = ['ro.build.version.incremental']
                    ro_build_version_incremental = get_first_match(contentDict, keys)

                    keys = ['ro.build.type']
                    ro_build_type = get_first_match(contentDict, keys)

                    keys = ['ro.build.tags']
                    ro_build_tags = get_first_match(contentDict, keys)

                    ro_build_fingerprint = f"{ro_product_brand}/{ro_product_name}/{ro_product_device}:{ro_build_version_release}/{ro_build_id}/{ro_build_version_incremental}:{ro_build_type}/{ro_build_tags}"

                donor_print = "{\n"
                donor_print += f"    \"PRODUCT\" : \"{ro_product_name}\",\n"
                donor_print += f"    \"DEVICE\" : \"{ro_product_device}\",\n"
                donor_print += f"    \"MANUFACTURER\" : \"{ro_product_manufacturer}\",\n"
                donor_print += f"    \"BRAND\" : \"{ro_product_brand}\",\n"
                donor_print += f"    \"MODEL\" : \"{ro_product_model}\",\n"
                donor_print += f"    \"FINGERPRINT\" : \"{ro_build_fingerprint}\",\n"
                donor_print += f"    \"SECURITY_PATCH\" : \"{ro_build_version_security_patch}\",\n"
                donor_print += f"    \"FIRST_API_LEVEL\" : \"{ro_product_first_api_level}\"\n"
                donor_print += "}"

                donor_print_html = f"<pre>{html.escape(donor_print)}</pre>"
                self.html.SetPage(donor_print_html)

                # print(donor_print)

            except IOError:
                wx.LogError(f"Cannot process file: '{pathname}'.")
                traceback.print_exc()
        self._on_spin('stop')


    # -----------------------------------------------
    #                  onContextMenu
    # -----------------------------------------------
    def onContextMenu(self, event):
        menu = wx.Menu()
        copy_item = menu.Append(wx.ID_COPY, "Copy")
        select_all_item = menu.Append(wx.ID_SELECTALL, "Select All")
        self.Bind(wx.EVT_MENU, self.onCopy, copy_item)
        self.Bind(wx.EVT_MENU, self.onSelectAll, select_all_item)

        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  onCopy
    # -----------------------------------------------
    def onCopy(self, event):
        self.html.CopySelectedText()

    # -----------------------------------------------
    #                  onSelectAll
    # -----------------------------------------------
    def onSelectAll(self, event):
        self.html.SelectAll()

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

    # ----------------------------------------------------------------------------
    #                               extract_prop
    # ----------------------------------------------------------------------------
    def extract_prop(self, search, match):
        try:
            l,r = match.rsplit("=", 1)
            return r.strip()
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract_prop for {search}")
            return ''

    # ----------------------------------------------------------------------------
    #                               refresh_modules
    # ----------------------------------------------------------------------------
    def refresh_modules(self):
        # self.Freeze()
        self.list.ClearAll()
        self.PopulateList(True)
        # self.Thaw
