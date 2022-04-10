#!/usr/bin/env python

import wx
import wx.adv
import wx.lib.inspection
import wx.lib.mixins.inspection

import sys
import os
import images as images
import locale
import ntpath
import json
from datetime import datetime
from modules import debug

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except:
    pass

from runtime import *
from config import Config
from config import VERSION
from phone import get_connected_devices
from modules import check_platform_tools
from modules import prepare_package
from modules import flash_phone
from modules import select_firmware
from modules import set_flash_button_state
from advanced_settings import AdvancedSettings

# see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
locale.setlocale(locale.LC_ALL, 'C')


# ============================================================================
#                               Class RedirectText
# ============================================================================
class RedirectText():
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl
        logfile = os.path.join(get_config_path(), 'logs', f"PixelFlasher_{datetime.now():%Y-%m-%d_%Hh%Mm%Ss}.log")
        self.logfile = open(logfile, "w")
        set_logfile(logfile)

    def write(self,string):
        self.out.WriteText(string)
        if self.logfile.closed:
            pass
        else:
            self.logfile.write(string)


# ============================================================================
#                               Class PixelFlasher
# ============================================================================
class PixelFlasher(wx.Frame):
    def __init__(self, parent, title):
        init_config_path()
        config_file = get_config_file_path()
        self.config = Config.load(config_file)
        set_magisk_package(self.config.magisk)
        wx.Frame.__init__(self, parent, -1, title, size=(self.config.width, self.config.height),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        check_platform_tools(self)

        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)
        sys.stderr = RedirectText(self.console_ctrl)

        # self.Centre(wx.BOTH)
        if self.config.pos_x and self.config.pos_y:
            self.SetPosition((self.config.pos_x,self.config.pos_y))

        self.Show(True)

        #------------------------------------
        # stuff after the window is displayed
        print(f"PixelFlasher {VERSION} started on {datetime.now():%Y-%m-%d %H:%M:%S}")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    f.close()
            except Exception as e:
                print(e)
                pass
            debug(f"Loading configuration file: {config_file} ...")
            debug(f"{json.dumps(data, indent=4, sort_keys=True)}")

        # set the state of flash button.
        set_flash_button_state(self)
        self._update_custom_flash_options()

        # print sdk path / version
        print(f"Android Platform Tools: {self.config.platform_tools_path}")
        print(f"SDK Version: {get_sdk_version()}")

        # print selected device.
        device = get_phone()
        if device:
            self._print_device_details(device)
        else:
            print("No device is selected.")


    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = "Welcome to PixelFlasher %s" % VERSION
        self.statusBar.SetStatusText(status_text, 0)

    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit PixelFlasher")
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)
        self.menuBar.Append(file_menu, "&File")

        # Advanced Config Menu
        config_item = file_menu.Append(wx.ID_ANY, "Advanced Configuration", "Advanced Configuration")
        self.Bind(wx.EVT_MENU, self._on_advanced_config, config_item)

        # Help menu
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ABOUT, '&About PixelFlasher', 'About')
        self.Bind(wx.EVT_MENU, self._on_help_about, help_item)
        self.menuBar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menuBar)

    def _on_close(self, event):
        self.config.pos_x, self.config.pos_y = self.GetPosition()
        self.config.save(get_config_file_path())
        wx.Exit()

    def _on_resize(self, event):
        self.config.width = self.Rect.Width
        self.config.height = self.Rect.Height
        event.Skip(True)

    # Menu methods
    def _on_exit_app(self, event):
        self.config.save(get_config_file_path())
        self.Close(True)

    def _on_help_about(self, event):
        from About import AboutDlg
        about = AboutDlg(self)
        about.ShowModal()
        about.Destroy()

    def _on_advanced_config( self, event ):
        advanced_setting_dialog = AdvancedSettings(self)
        advanced_setting_dialog.CentreOnParent(wx.BOTH)
        res = advanced_setting_dialog.ShowModal()
        if res == wx.ID_OK:
            self.config.advanced_options = get_advanced_options()
        advanced_setting_dialog.Destroy()
        # show / hide advanced settings
        self._advanced_options_hide(not get_advanced_options())
        set_flash_button_state(self)

    def _advanced_options_hide(self, value):
        if value:
            # flash options
            self.advanced_options_label.Hide()
            self.flash_both_slots_checkBox.Hide()
            self.disable_verity_checkBox.Hide()
            self.disable_verification_checkBox.Hide()
            self.fastboot_verbose_checkBox.Hide()
            # slot options
            self.a_radio_button.Hide()
            self.b_radio_button.Hide()
            self.reboot_recovery_button.Hide()
            self.set_active_slot_button.Hide()
            # ROM options
            self.custom_rom_checkbox.Hide()
            self.custom_rom.Hide()
            # Custom Flash Radio Button
            # if we're turning off advanced options, and the current mode is customFlash, hide, it
            self.mode_radio_button.LastInGroup.Hide()
            # Custom Flash Image options
            self.live_boot_radio_button.Hide()
            self.flash_radio_button.Hide()
            self.image_choice.Hide()
            self.image_file_picker.Hide()
            a = self.mode_radio_button.Name
            # if we're turning off advanced options, and the current mode is customFlash, change it to dryRun
            if self.mode_radio_button.Name == 'mode-customFlash' and self.mode_radio_button.GetValue():
                self.mode_radio_button.PreviousInGroup.SetValue(True)
                self.config.flash_mode = 'dryRun'
        else:
            # flash options
            self.advanced_options_label.Show()
            self.flash_both_slots_checkBox.Show()
            self.disable_verity_checkBox.Show()
            self.disable_verification_checkBox.Show()
            self.fastboot_verbose_checkBox.Show()
            # slot options
            self.a_radio_button.Show()
            self.b_radio_button.Show()
            self.reboot_recovery_button.Show()
            self.set_active_slot_button.Show()
            # ROM options
            self.custom_rom_checkbox.Show()
            self.custom_rom.Show()
            # Custom Flash Radio Button
            self.mode_radio_button.LastInGroup.Show()
            # Custom Flash Image options
            self.live_boot_radio_button.Show()
            self.flash_radio_button.Show()
            self.image_choice.Show()
            self.image_file_picker.Show()
        # Update UI (need to do this resize to get the UI properly refreshed.)
        self.Update()
        self.Layout()
        w, h = self.Size
        h = h + 100
        self.Size = (w, h)
        h = h - 100
        self.Size = (w, h)
        self.Refresh()

    def _print_device_details(self, device):
        print(f"Selected Device:")
        print(f"    Device ID:          {device.id}")
        print(f"    Device Model:       {device.hardware}")
        print(f"    Device is Rooted:   {device.rooted}")
        print(f"    Device Build:       {device.build}")
        print(f"    Device Active Slot: {device.active_slot}")
        print(f"    Device Mode:        {device.mode}")
        if device.unlocked:
            print(f"    Device Unlocked:{device.magisk_version}")
        if device.rooted:
            print(f"    Magisk Version:     {device.magisk_version}")
            print(f"    Magisk Modules:")
            s1 = device.magisk_modules
            s2 = "\n                        "
            print(f"                        {s2.join(s1)}")
        else:
            print('')

    def _update_custom_flash_options(self):
        image_mode = get_image_mode()
        image_path = get_image_path()
        if self.config.flash_mode == 'customFlash':
            self.image_file_picker.Enable(True)
            self.image_choice.Enable(True)
        else:
            # disable custom_flash_options
            self.flash_radio_button.Enable(False)
            self.live_boot_radio_button.Enable(False)
            self.image_file_picker.Enable(False)
            self.image_choice.Enable(False)
            return
        self.live_boot_radio_button.Enable(False)
        self.flash_radio_button.Enable(False)
        self.flash_button.Enable(False)
        try:
            if image_path:
                filename, extension = os.path.splitext(image_path)
                extension = extension.lower()
                if image_mode == 'boot':
                    if extension == '.img':
                        self.live_boot_radio_button.Enable(True)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                    else:
                        print("\nERROR: Selected file is not of type .img")
                elif image_mode == 'image':
                    if extension == '.zip':
                        self.live_boot_radio_button.Enable(False)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                        self.flash_radio_button.SetValue( True )
                    else:
                        print("\nERROR: Selected file is not of type .zip")
                else:
                    if extension == '.img':
                        self.live_boot_radio_button.Enable(False)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                        self.flash_radio_button.SetValue( True )
                    else:
                        print("\nERROR: Selected file is not of type .img")
        except:
            pass


    #-----------------------------------------------------------------------------
    #                                   _init_ui
    #-----------------------------------------------------------------------------
    def _init_ui(self):
        def _add_mode_radio_button(sizer, index, flash_mode, label, tooltip):
            style = wx.RB_GROUP if index == 0 else 0
            self.mode_radio_button = wx.RadioButton(panel, name="mode-%s" % flash_mode, label="%s" % label, style=style)
            self.mode_radio_button.Bind(wx.EVT_RADIOBUTTON, _on_mode_changed)
            self.mode_radio_button.mode = flash_mode
            if flash_mode == self.config.flash_mode:
                self.mode_radio_button.SetValue(True)
            else:
                self.mode_radio_button.SetValue(False)
            self.mode_radio_button.SetToolTip(tooltip)
            sizer.Add(self.mode_radio_button)
            sizer.AddSpacer(10)

        def _select_configured_device(self):
            count = 0
            if self.config.device:
                for device in get_phones():
                    if device.id == self.config.device:
                        self.device_choice.Select(count)
                        set_phone(device)
                    count += 1
            if self.device_choice.StringSelection == '':
                set_phone(None)
                self.device_label.Label = "ADB Connected Devices"
                self.config.device = None
            _reflect_slots(self)

        def _on_select_device(event):
            choice = event.GetEventObject()
            device = choice.GetString(choice.GetSelection())
            # replace multiple spaces with a single space and then split on space
            id = ' '.join(device.split())
            id = id.split()
            id = id[2]
            self.config.device = id
            for device in get_phones():
                if device.id == id:
                    set_phone(device)
                    self._print_device_details(device)
            _reflect_slots(self)

        def _reflect_slots(self):
            device = get_phone()
            if device:
                if device.active_slot == 'a':
                    self.device_label.Label = "ADB Connected Devices\nCurrent Active Slot: [A]"
                    self.a_radio_button.Enable(False)
                    self.b_radio_button.Enable(True)
                    self.b_radio_button.SetValue(True)
                    self.set_active_slot_button.Enable(True)
                elif device.active_slot == 'b':
                    self.device_label.Label = "ADB Connected Devices\nCurrent Active Slot: [B]"
                    self.a_radio_button.Enable(True)
                    self.b_radio_button.Enable(False)
                    self.a_radio_button.SetValue(True)
                    self.set_active_slot_button.Enable(True)
                else:
                    self.device_label.Label = "ADB Connected Devices"
                    self.a_radio_button.Enable(False)
                    self.b_radio_button.Enable(False)
                    self.a_radio_button.SetValue(False)
                    self.b_radio_button.SetValue(False)
                    self.set_active_slot_button.Enable(False)
            else:
                self.device_label.Label = "ADB Connected Devices"
                self.a_radio_button.Enable(False)
                self.b_radio_button.Enable(False)
                self.a_radio_button.SetValue(False)
                self.b_radio_button.SetValue(False)
                self.set_active_slot_button.Enable(False)

        def _on_reload(event):
            if get_adb():
                print("")
                wait = wx.BusyCursor()
                self.device_choice.SetItems(get_connected_devices())
                self.config.device = None
                del wait
            else:
                print("Please set Android Platform Tools Path first.")

        def _on_select_platform_tools(event):
            wait = wx.BusyCursor()
            self.config.platform_tools_path = event.GetPath().replace("'", "")
            check_platform_tools(self)
            if get_sdk_version():
                self.platform_tools_label.SetLabel(f"Android Platform Tools\nVersion {get_sdk_version()}")
            else:
                self.platform_tools_label.SetLabel("Android Platform Tools")
            del wait

        def _on_select_firmware(event):
            self.config.firmware_path = event.GetPath().replace("'", "")
            wait = wx.BusyCursor()
            select_firmware(self)
            del wait

        def _on_image_choice( event ):
            wait = wx.BusyCursor()
            choice = event.GetEventObject()
            set_image_mode(choice.GetString(choice.GetSelection()))
            self._update_custom_flash_options()
            del wait

        def _on_image_select( event ):
            wait = wx.BusyCursor()
            image_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(image_path)
            extension = extension.lower()
            if extension == '.zip' or extension == '.img':
                set_image_path(image_path)
                self._update_custom_flash_options()
            else:
                print(f"\nERROR: The selected file {image_path} is not img or zip file.")
                self.image_file_picker.SetPath('')
            del wait

        def _on_select_custom_rom(event):
            wait = wx.BusyCursor()
            custom_rom_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(custom_rom_path)
            extension = extension.lower()
            if extension == '.zip':
                self.config.custom_rom_path = custom_rom_path
                rom_file = ntpath.basename(custom_rom_path)
                set_custom_rom_id(os.path.splitext(rom_file)[0])
            else:
                print(f"\nERROR: The selected file {custom_rom_path} is not a zip file.")
                self.custom_rom.SetPath('')
            del wait

        def _on_mode_changed(event):
            self.mode_radio_button = event.GetEventObject()
            if self.mode_radio_button.GetValue():
                self.config.flash_mode = self.mode_radio_button.mode
                print(f"Flash mode changed to: {self.config.flash_mode}")
            if self.config.flash_mode != 'customFlash':
                set_flash_button_state(self)
            self._update_custom_flash_options()

        def _on_patch_boot(event):
            patch_checkBox = event.GetEventObject()
            status = patch_checkBox.GetValue()
            self.config.patch_boot = status

        def _on_flash_both_slots(event):
            self.patch_checkBox = event.GetEventObject()
            status = self.flash_both_slots_checkBox.GetValue()
            self.config.flash_both_slots = status

        def _on_disable_verity(event):
            self.patch_checkBox = event.GetEventObject()
            status = self.disable_verity_checkBox.GetValue()
            self.config.disable_verity = status

        def _on_disable_verification(event):
            patch_checkBox = event.GetEventObject()
            status = self.disable_verification_checkBox.GetValue()
            self.config.disable_verification = status

        def _on_fastboot_verbose(event):
            patch_checkBox = event.GetEventObject()
            status = self.fastboot_verbose_checkBox.GetValue()
            self.config.fastboot_verbose = status

        def _on_verbose(event):
            self.verbose_checkBox = event.GetEventObject()
            status = self.verbose_checkBox.GetValue()
            self.config.verbose = status
            set_verbose(status)

        def _on_reboot_recovery(event):
            wait = wx.BusyCursor()
            device = get_phone()
            device.reboot_recovery()
            del wait

        def _on_reboot_system(event):
            wait = wx.BusyCursor()
            device = get_phone()
            device.reboot_system()
            del wait

        def _on_reboot_bootloader(event):
            wait = wx.BusyCursor()
            device = get_phone()
            device.reboot_bootloader(fastboot_included = True)
            del wait

        def _on_set_active_slot(event):
            wait = wx.BusyCursor()
            if self.a_radio_button.GetValue():
                slot = 'a'
            elif self.b_radio_button.GetValue():
                slot = 'b'
            else:
                print("\nERROR: Please first select a slot.")
                del wait
                return
            device = get_phone()
            device.set_active_slot(slot)
            del wait

        def _on_custom_rom(event):
            self.custom_rom_checkbox = event.GetEventObject()
            status = self.custom_rom_checkbox.GetValue()
            self.config.custom_rom = status
            if status:
                self.custom_rom.Enable()
            else:
                self.custom_rom.Disable()

        def _on_prepare(event):
            wait = wx.BusyCursor()
            prepare_package(self)
            del wait

        def _on_flash(event):
            wait = wx.BusyCursor()
            flash_phone(self)
            del wait

        def _on_clear(event):
            self.console_ctrl.SetValue("")


        # ==============
        # UI Setup Here
        # ==============
        panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.VERTICAL)

        NUMROWS = 15
        fgs1 = wx.FlexGridSizer(NUMROWS, 2, 10, 10)

        # 1st row widgets, firmware file
        firmware_label = wx.StaticText(panel, label=u"Pixel Phone Factory Image")
        self.firmware_picker = wx.FilePickerCtrl(panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"Factory Image files (*.zip)|*.zip", wx.DefaultPosition, wx.DefaultSize , style=wx.FLP_USE_TEXTCTRL)
        self.firmware_picker.SetToolTip(u"Select Pixel Firmware")

        # 2nd row widgets, Android platfom tools
        self.platform_tools_label = wx.StaticText(panel, label=u"Android Platform Tools")
        self.platform_tools_picker = wx.DirPickerCtrl(panel, style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
        self.platform_tools_picker.SetToolTip(u"Select Android Platform-Tools Folder\nWhere adb and fastboot are located.")

        # 3rd row widgets, Connected Devices
        self.device_label = wx.StaticText(panel, label=u"ADB Connected Devices")
        self.device_choice = wx.Choice(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, [], 0 )
        self.device_choice.SetSelection(0)
        self.device_choice.SetFont( wx.Font( 9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Consolas" ) )
        reload_button = wx.Button(panel, label=u"Reload")
        reload_button.SetToolTip(u"Reload adb device list")
        device_sizer = wx.BoxSizer(wx.HORIZONTAL)
        device_sizer.Add(self.device_choice, 1, wx.EXPAND)
        device_sizer.Add(reload_button, flag=wx.LEFT, border=5)

        # 4th row Reboot buttons
        active_slot_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.a_radio_button = wx.RadioButton( panel, wx.ID_ANY, u"A", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.b_radio_button = wx.RadioButton( panel, wx.ID_ANY, u"B", wx.DefaultPosition, wx.DefaultSize, 0 )
        active_slot_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        active_slot_sizer.Add( self.a_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
        active_slot_sizer.Add( self.b_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
        self.reboot_recovery_button = wx.Button( panel, wx.ID_ANY, u" Reboot to Recovery  ", wx.DefaultPosition, wx.DefaultSize, 0 )
        reboot_system_button = wx.Button( panel, wx.ID_ANY, u"Reboot to System", wx.DefaultPosition, wx.DefaultSize, 0 )
        reboot_bootloader_button = wx.Button( panel, wx.ID_ANY, u"Reboot to Bootloader", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.set_active_slot_button = wx.Button( panel, wx.ID_ANY, u"Set Active Slot", wx.DefaultPosition, wx.DefaultSize, 0 )
        reboot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reboot_sizer.Add(self.set_active_slot_button, 1, wx.RIGHT, 10)
        # reboot_sizer.Add( ( 5, 0), 0, 0, 5 )
        reboot_sizer.Add(self.reboot_recovery_button, 1, wx.RIGHT, 10)
        reboot_sizer.Add(reboot_system_button, 1, wx.RIGHT, 5)
        reboot_sizer.Add(reboot_bootloader_button, 1, wx.LEFT, 5)
        reboot_sizer.Add( ( reload_button.Size.Width + 5, 0), 0, wx.EXPAND )

        # 5th row, empty row, static line
        self.staticline1 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        self.staticline2 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        self.staticline2.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )

        # 6th row widgets, custom_rom
        self.custom_rom_checkbox = wx.CheckBox( panel, wx.ID_ANY, u"Apply Custom ROM", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.custom_rom_checkbox.SetValue(self.config.custom_rom)
        self.custom_rom_checkbox.SetToolTip(u"Caution: Make sure you read the selected ROM documentation.\nThis might not work for your ROM")
        self.custom_rom = wx.FilePickerCtrl(panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"ROM files (*.zip)|*.zip", wx.DefaultPosition, wx.DefaultSize , style=wx.FLP_USE_TEXTCTRL)
        self.custom_rom.SetToolTip(u"Select Custom ROM")

        # 7th row widgets
        patch_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Patch boot.img\nusing Magisk", wx.DefaultPosition, wx.DefaultSize, 0 )
        patch_checkBox.SetValue(self.config.patch_boot)
        patch_checkBox.SetToolTip(u"This requires Magisk installed on the phone")
        prepare_button = wx.Button(panel, -1, "Prepare Package", wx.DefaultPosition, wx.Size( -1,50 ))
        prepare_button.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
        prepare_button.SetToolTip(u"Prepares a Patched Factory Image for later Flashing")

        # 8th row, empty row, static line
        self.staticline3 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        self.staticline4 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )

        # 9th row widgets
        mode_label = wx.StaticText(panel, label=u"Flash Mode")
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # _add_mode_radio_button(sizer, index, flash_mode, label, tooltip)
        _add_mode_radio_button(mode_sizer, 0, 'keepData', "Keep Data", "Data will be kept intact.")
        _add_mode_radio_button(mode_sizer, 1, 'wipeData', "WIPE all data", "CAUTION: This will wipe your data")
        _add_mode_radio_button(mode_sizer, 2, 'dryRun', "Dry Run", "Dry Run, no flashing will be done.\nThe phone will reboot to fastboot and then\nback to normal.\nThis is for testing.")
        _add_mode_radio_button(mode_sizer, 3, 'customFlash', "Custom Flash", "Custom Flash, Advanced option to flash a single file.\nThis will not flash the prepared package.\It will flash the single selected file.")

        # 10th row widgets (custom flash)
        custom_advanced_options_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.live_boot_radio_button = wx.RadioButton( panel, wx.ID_ANY, u"Live Boot", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.live_boot_radio_button.Enable( False )
        self.live_boot_radio_button.SetToolTip( u"Live Boot to selected boot.img" )
        self.flash_radio_button = wx.RadioButton( panel, wx.ID_ANY, u"Flash", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.flash_radio_button.SetValue( True )
        self.flash_radio_button.Enable( False )
        self.flash_radio_button.SetToolTip( u"Flashes the selected boot.img" )
        custom_advanced_options_sizer.Add( self.live_boot_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0 )
        custom_advanced_options_sizer.Add( self.flash_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0 )
        # 2nd column
        custom_flash_sizer = wx.BoxSizer( wx.HORIZONTAL )
        image_choices = [ u"boot", u"vbmeta", u"recovery", u"radio", u"bootloader", u"dtbo", u"vendor", u"vendor_dlkm", u"image" ]
        self.image_choice = wx.Choice( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, image_choices, 0 )
        self.image_choice.SetSelection( 0 )
        custom_flash_sizer.Add( self.image_choice, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
        self.image_file_picker = wx.FilePickerCtrl( panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"Flashable files (*.img;*.zip)|*.img;*.zip", wx.DefaultPosition, wx.DefaultSize, wx.FLP_USE_TEXTCTRL )
        custom_flash_sizer.Add( self.image_file_picker, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0 )

        # 11th row widgets, Flash options
        self.advanced_options_label = wx.StaticText(panel, label=u"Flash Options")
        self.flash_both_slots_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Flash on both slots", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.disable_verity_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Disable Verity", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.disable_verification_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Disable Verification", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.fastboot_verbose_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Verbose", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.fastboot_verbose_checkBox.SetToolTip( u"set fastboot option to verbose" )
        self.advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.advanced_options_sizer.Add(self.flash_both_slots_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.disable_verity_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.disable_verification_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.fastboot_verbose_checkBox)
        self.advanced_options_sizer.AddSpacer(10)

        # 12th row widgets, Flash button
        self.flash_button = wx.Button(panel, -1, "Flash Pixel Phone", wx.DefaultPosition, wx.Size( -1,50 ))
        self.flash_button.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
        self.flash_button.SetToolTip(u"Flashes (with Flash Mode Settings) the selected phone with the prepared Image.")

        # 13th row, empty row, static line
        self.staticline5 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        self.staticline6 = wx.StaticLine( panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )

        # 14th row widgets, console
        console_label = wx.StaticText(panel, label=u"Console")
        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY )
        self.console_ctrl.SetFont(wx.Font(8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.WHITE)
        self.console_ctrl.SetForegroundColour(wx.BLUE)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        # 15th row widgets, verbose and clear button
        self.verbose_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Verbose", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.verbose_checkBox.SetToolTip(u"Enable Verbose Messages")
        clear_button = wx.Button(panel, -1, "Clear Console")

        # add the rows to flexgrid
        fgs1.AddMany([
                    (firmware_label, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (self.firmware_picker, 1, wx.EXPAND),
                    (self.platform_tools_label, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (self.platform_tools_picker, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (self.device_label, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (device_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (active_slot_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5 ), (reboot_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    self.staticline1, (self.staticline2, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND|wx.TOP, 20 ),
                    (self.custom_rom_checkbox, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (self.custom_rom, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (patch_checkBox, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (prepare_button, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    self.staticline3, (self.staticline4, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND|wx.TOP, 20 ),
                    (mode_label, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (mode_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (custom_advanced_options_sizer, 0, wx.ALIGN_CENTER_VERTICAL, 5 ), (custom_flash_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    self.advanced_options_label, self.advanced_options_sizer,
                    (wx.StaticText(panel, label="")), (self.flash_button, 1, wx.EXPAND),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    self.staticline5, (self.staticline6, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND|wx.TOP, 20 ),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND),
                    (self.verbose_checkBox), (clear_button, 1, wx.EXPAND)])
        # this makes the second column expandable (index starts at 0)
        fgs1.AddGrowableCol(1, 1)
        # this makes the console row expandable (index starts at 0)
        fgs1.AddGrowableRow(NUMROWS - 2, 1)

        # add flexgrid to hbox
        hbox.Add(fgs1, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)

        # set the panel
        panel.SetSizer(hbox)

        # Connect Events
        self.device_choice.Bind(wx.EVT_CHOICE, _on_select_device)
        reload_button.Bind(wx.EVT_BUTTON, _on_reload)
        self.firmware_picker.Bind(wx.EVT_FILEPICKER_CHANGED, _on_select_firmware)
        self.platform_tools_picker.Bind(wx.EVT_DIRPICKER_CHANGED, _on_select_platform_tools)
        self.custom_rom_checkbox.Bind( wx.EVT_CHECKBOX, _on_custom_rom )
        self.custom_rom.Bind(wx.EVT_FILEPICKER_CHANGED, _on_select_custom_rom)
        self.disable_verification_checkBox.Bind( wx.EVT_CHECKBOX, _on_disable_verification )
        patch_checkBox.Bind( wx.EVT_CHECKBOX, _on_patch_boot )
        prepare_button.Bind(wx.EVT_BUTTON, _on_prepare)
        self.flash_both_slots_checkBox.Bind( wx.EVT_CHECKBOX, _on_flash_both_slots )
        self.disable_verity_checkBox.Bind( wx.EVT_CHECKBOX, _on_disable_verity )
        self.fastboot_verbose_checkBox.Bind( wx.EVT_CHECKBOX, _on_fastboot_verbose )
        self.flash_button.Bind(wx.EVT_BUTTON, _on_flash)
        self.verbose_checkBox.Bind(wx.EVT_CHECKBOX, _on_verbose)
        clear_button.Bind(wx.EVT_BUTTON, _on_clear)
        self.reboot_recovery_button.Bind(wx.EVT_BUTTON, _on_reboot_recovery)
        reboot_system_button.Bind(wx.EVT_BUTTON, _on_reboot_system)
        reboot_bootloader_button.Bind(wx.EVT_BUTTON, _on_reboot_bootloader)
        self.set_active_slot_button.Bind(wx.EVT_BUTTON, _on_set_active_slot)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_SIZE, self._on_resize)
        self.image_file_picker.Bind( wx.EVT_FILEPICKER_CHANGED, _on_image_select )
        self.image_choice.Bind( wx.EVT_CHOICE, _on_image_choice )

        # initial setup
        self.SetSize(self.config.width, self.config.height)

        # Populate device list
        self.device_choice.AppendItems(get_connected_devices())

        # select configured device
        _select_configured_device(self)
        device_tooltip = '''[root status] [device mode] [device id] [device model] [device firmware]

✓ Rooted with Magisk.
✗ Probably Not Root (Magisk Tools not found).
?  Unable to determine the root status.

(adb) device is in adb mode
(f.b) device is in fastboot mode
'''
        self.device_choice.SetToolTip(device_tooltip)

        # extract firmware info
        if self.config.firmware_path:
            if os.path.exists(self.config.firmware_path):
                self.firmware_picker.SetPath(self.config.firmware_path)
                firmware = ntpath.basename(self.config.firmware_path)
                firmware = firmware.split("-")
                try:
                    set_firmware_model(firmware[0])
                    set_firmware_id(firmware[0] + "-" + firmware[1])
                except Exception as e:
                    set_firmware_model(None)
                    set_firmware_id(None)

        # load platform tools value
        if self.config.platform_tools_path and get_adb() and get_fastboot():
            self.platform_tools_picker.SetPath(self.config.platform_tools_path)

        # if adb is found, display the version
        if get_sdk_version():
            self.platform_tools_label.SetLabel(f"Android Platform Tools\nVersion {get_sdk_version()}")

        # load custom_rom settings
        if self.config.custom_rom_path:
            if os.path.exists(self.config.custom_rom_path):
                self.custom_rom.SetPath(self.config.custom_rom_path)
                set_custom_rom_id(os.path.splitext(ntpath.basename(self.config.custom_rom_path))[0])
        if self.config.custom_rom:
            self.custom_rom.Enable()
        else:
            self.custom_rom.Disable()

        # set the flash mode
        mode = self.config.flash_mode

        # set flash option
        self.flash_both_slots_checkBox.SetValue(self.config.flash_both_slots)
        self.disable_verity_checkBox.SetValue(self.config.disable_verity)
        self.disable_verification_checkBox.SetValue(self.config.disable_verification)
        self.fastboot_verbose_checkBox.SetValue(self.config.fastboot_verbose)

        # enable / disable advanced_options
        set_advanced_options(self.config.advanced_options)
        if self.config.advanced_options:
            self._advanced_options_hide(False)
        else:
            self._advanced_options_hide(True)

        # enable / disable flash button
        if get_firmware_id():
            if os.path.exists(os.path.join(get_firmware_id(), "Package_Ready.json")):
                self.flash_button.Enable()
            else:
                self.flash_button.Disable()

        # load verbose settings
        if self.config.verbose:
            self.verbose_checkBox.SetValue(self.config.verbose)
            set_verbose(self.config.verbose)

        # get the image choice and update UI
        set_image_mode(self.image_choice.Items[self.image_choice.GetSelection()])
        self._update_custom_flash_options()

        # Update UI
        self.Layout()

# ============================================================================
#                               Class App
# ============================================================================
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        # see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
        self.ResetLocale()
        # wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("PixelFlasher")

        frame = PixelFlasher(None, "PixelFlasher")
        # frame.SetClientSize(frame.FromDIP(wx.Size(WIDTH, HEIGHT)))
        # frame.SetClientSize(wx.Size(WIDTH, HEIGHT))
        frame.Show()
        return True


# ============================================================================
#                               Function Main
# ============================================================================
def main():
    app = App(False)
    # For troubleshooting, uncomment next line to launch WIT
    # wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    __name__ = 'Main'
    main()

