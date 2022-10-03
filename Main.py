#!/usr/bin/env python

import contextlib
import ctypes
import json
import locale
import math
import ntpath
import os
import sys
import time
import webbrowser
from datetime import datetime

import darkdetect
import wx
import wx.adv
import wx.lib.inspection
import wx.lib.mixins.inspection
from packaging.version import parse

import images as images

with contextlib.suppress(Exception):
    ctypes.windll.shcore.SetProcessDpiAwareness(True)

from advanced_settings import AdvancedSettings
from config import VERSION, Config
from magisk_downloads import MagiskDownloads
from magisk_modules import MagiskModules
from message_box import MessageBox
from modules import (check_platform_tools, create_support_zip, debug,
                     delete_all, flash_phone, get_code_page, live_boot_phone,
                     patch_boot_img, populate_boot_list, process_file,
                     select_firmware, set_flash_button_state)
from phone import get_connected_devices
from runtime import *

# see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
locale.setlocale(locale.LC_ALL, 'C')

# For troubleshooting, set inspector = True
inspector = False


# ============================================================================
#                               Class RedirectText
# ============================================================================
class RedirectText():
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl
        logfile = os.path.join(get_config_path(), 'logs', f"PixelFlasher_{datetime.now():%Y-%m-%d_%Hh%Mm%Ss}.log")
        self.logfile = open(logfile, "w", buffering=1, encoding="ISO-8859-1")
        set_logfile(logfile)

    def write(self,string):
        wx.CallAfter(self.out.AppendText, string)
        if not self.logfile.closed:
            self.logfile.write(string)

    # noinspection PyMethodMayBeStatic
    def flush(self):
        # noinspection PyStatementEffect
        None


# ============================================================================
#                               Class PixelFlasher
# ============================================================================
class PixelFlasher(wx.Frame):
    def __init__(self, parent, title):
        init_config_path()
        config_file = get_config_file_path()
        init_db()
        self.config = Config.load(config_file)
        wx.Frame.__init__(self, parent, -1, title, size=(self.config.width, self.config.height),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)

        # Base first run size on resolution.
        if self.config.first_run:
            x = int((self.CharWidth * self.config.width) / 11)
            y = int((self.CharHeight * self.config.height) / 25)
            self.SetSize(x, y)

        self.Center()
        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)
        sys.stderr = RedirectText(self.console_ctrl)

        # self.Centre(wx.BOTH)
        if self.config.pos_x and self.config.pos_y:
            self.SetPosition((self.config.pos_x,self.config.pos_y))

        self.initialize()
        self.Show(True)

    # -----------------------------------------------
    #                  initialize
    # -----------------------------------------------
    def initialize(self):
        print(f"PixelFlasher {VERSION} started on {datetime.now():%Y-%m-%d %H:%M:%S}")
        start = time.time()

        # load verbose settings
        if self.config.verbose:
            self.verbose_checkBox.SetValue(self.config.verbose)
            set_verbose(self.config.verbose)
        if self.config.first_run:
            print("First Run: No previous configuration file is found.")
        else:
            print(f"{json.dumps(self.config.data, indent=4, sort_keys=True)}")

        # enable / disable advanced_options
        set_advanced_options(self.config.advanced_options)
        if self.config.advanced_options:
            self._advanced_options_hide(False)
        else:
            self._advanced_options_hide(True)

        # check codepage
        print(f"System Default Encoding: {sys.getdefaultencoding()}")
        print(f"File System Encoding:    {sys.getfilesystemencoding()}")
        get_code_page()

        # load custom codepage settings
        set_codepage_setting(self.config.force_codepage)
        if self.config.force_codepage:
            set_codepage_value(self.config.custom_codepage)

        # load Magisk Package Name
        set_magisk_package(self.config.magisk)

        # extract firmware info
        if self.config.firmware_path and os.path.exists(self.config.firmware_path):
            self.firmware_picker.SetPath(self.config.firmware_path)
            firmware = ntpath.basename(self.config.firmware_path)
            filename, extension = os.path.splitext(firmware)
            extension = extension.lower()
            firmware = filename.split("-")
            try:
                set_firmware_model(firmware[0])
                set_firmware_id(f"{firmware[0]}-{firmware[1]}")
            except Exception as e:
                set_firmware_model(None)
                set_firmware_id(None)

        # check platform tools
        check_platform_tools(self)

        # load platform tools value
        if self.config.platform_tools_path and get_adb() and get_fastboot():
            self.platform_tools_picker.SetPath(self.config.platform_tools_path)

        # if adb is found, display the version
        if get_sdk_version():
            self.platform_tools_label.SetLabel(f"Android Platform Tools\nVersion {get_sdk_version()}")

        # load custom_rom settings
        self.custom_rom_checkbox.SetValue(self.config.custom_rom)
        if self.config.custom_rom_path and os.path.exists(self.config.custom_rom_path):
            self.custom_rom.SetPath(self.config.custom_rom_path)
            set_custom_rom_id(os.path.splitext(ntpath.basename(self.config.custom_rom_path))[0])
        if self.config.custom_rom:
            self.custom_rom.Enable()
            self.process_rom.Enable()
        else:
            self.custom_rom.Disable()
            self.process_rom.Disable()

        # refresh boot.img list
        populate_boot_list(self)

        # set the flash mode
        mode = self.config.flash_mode

        # set flash option
        self.flash_both_slots_checkBox.SetValue(self.config.flash_both_slots)
        self.flash_to_inactive_slot_checkBox.SetValue(self.config.flash_to_inactive_slot)
        self.disable_verity_checkBox.SetValue(self.config.disable_verity)
        self.disable_verification_checkBox.SetValue(self.config.disable_verification)
        self.fastboot_force_checkBox.SetValue(self.config.fastboot_force)
        self.fastboot_verbose_checkBox.SetValue(self.config.fastboot_verbose)
        self.temporary_root_checkBox.SetValue(self.config.temporary_root)

        # get the image choice and update UI
        set_image_mode(self.image_choice.Items[self.image_choice.GetSelection()])

        # set the state of flash button.
        set_flash_button_state(self)

        self._update_custom_flash_options()

        print("\nLoading Device list ...")
        print("This could take a while, please be patient.\n")

        debug("Populate device list")
        self.device_choice.AppendItems(get_connected_devices())

        # select configured device
        debug("select configured device")
        self._select_configured_device()
        self._refresh_ui()

        # enable / disable update_check
        set_update_check(self.config.update_check)
        # check version if we are running the latest
        l_version = check_latest_version()
        if get_update_check() and parse(VERSION) < parse(l_version):
            print(f"\nA newer PixelFlasher v{l_version} can be downloaded from:")
            print("https://github.com/badabing2005/PixelFlasher/releases/latest")
            from About import AboutDlg
            about = AboutDlg(self)
            about.ShowModal()
            about.Destroy()
        end = time.time()
        print(f"Load time: {math.ceil(end - start)} seconds")
        self.spinner.Hide()
        self.spinner_label.Hide()

    # -----------------------------------------------
    #                  _set_icons
    # -----------------------------------------------
    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    # -----------------------------------------------
    #                  _build_status_bar
    # -----------------------------------------------
    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = f"Welcome to PixelFlasher {VERSION}"
        self.statusBar.SetStatusText(status_text, 0)

    # -----------------------------------------------
    #                  _build_menu_bar
    # -----------------------------------------------
    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        self.menuBar.Append(file_menu, "&File")
        # Advanced Config Menu
        config_item = file_menu.Append(wx.ID_ANY, "Advanced Configuration", "Advanced Configuration")
        config_item.SetBitmap(images.Advanced_Config.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_advanced_config, config_item)
        # seperator
        file_menu.AppendSeparator()
        # Install APK
        self.install_apk = file_menu.Append(wx.ID_ANY, "Install APK", "Install APK")
        self.install_apk.SetBitmap(images.InstallApk.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_install_apk, self.install_apk)
        # seperator
        file_menu.AppendSeparator()
        # Exit Menu
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit PixelFlasher")
        exit_item.SetBitmap(images.Exit.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)

        # Help menu
        help_menu = wx.Menu()
        self.menuBar.Append(help_menu, '&Help')
        # Report an issue
        issue_item = help_menu.Append(wx.ID_ANY, 'Report an Issue', 'Report an Issue')
        issue_item.SetBitmap(images.Bug.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_report_an_issue, issue_item)
        # # Feature Request
        feature_item = help_menu.Append(wx.ID_ANY, 'Feature Request', 'Feature Request')
        feature_item.SetBitmap(images.Feature.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_feature_request, feature_item)
        # # Project Home
        project_page_item = help_menu.Append(wx.ID_ANY, 'PixelFlasher Project Page', 'PixelFlasher Project Page')
        project_page_item.SetBitmap(images.Github.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_project_page, project_page_item)
        # Community Forum
        forum_item = help_menu.Append(wx.ID_ANY, 'PixelFlasher Community (Forum)', 'PixelFlasher Community (Forum)')
        forum_item.SetBitmap(images.Forum.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_forum, forum_item)
        # seperator
        help_menu.AppendSeparator()
        # Guide 1
        guide1_item = help_menu.Append(wx.ID_ANY, 'Homeboy76\'s Guide', 'Homeboy76\'s Guide')
        guide1_item.SetBitmap(images.Guide.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_guide1, guide1_item)
        # Guide 2
        guide2_item = help_menu.Append(wx.ID_ANY, 'V0latyle\'s Guide', 'V0latyle\'s Guide')
        guide2_item.SetBitmap(images.Guide.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_guide2, guide2_item)
        # seperator
        help_menu.AppendSeparator()
        if sys.platform == "win32":
            # Open configuration Folder
            config_folder_item = help_menu.Append(wx.ID_ANY, 'Open Configuration Folder', 'Open Configuration Folder')
            config_folder_item.SetBitmap(images.Config_Folder.GetBitmap())
            self.Bind(wx.EVT_MENU, self._on_open_config_folder, config_folder_item)
        # Create sanitized support.zip
        support_zip_item = help_menu.Append(wx.ID_ANY, 'Create a Sanitized support.zip', 'Create a Sanitized support.zip')
        support_zip_item.SetBitmap(images.Support_Zip.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_support_zip, support_zip_item)
        # seperator
        help_menu.AppendSeparator()
        # update check
        update_item = help_menu.Append(wx.ID_ANY, 'Check for New Version', 'Check for New Version')
        update_item.SetBitmap(images.Update_Check.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_help_about, update_item)
        # seperator
        help_menu.AppendSeparator()
        # About
        about_item = help_menu.Append(wx.ID_ABOUT, '&About PixelFlasher', 'About')
        about_item.SetBitmap(images.About.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_help_about, about_item)

        self.SetMenuBar(self.menuBar)

    # -----------------------------------------------
    #                  _on_close
    # -----------------------------------------------
    def _on_close(self, event):
        self.config.pos_x, self.config.pos_y = self.GetPosition()
        self.config.save(get_config_file_path())
        wx.Exit()

    # -----------------------------------------------
    #                  _on_resize
    # -----------------------------------------------
    def _on_resize(self, event):
        self.config.width = self.Rect.Width
        self.config.height = self.Rect.Height
        # auto size list columns to largest text, make the last column expand to the available room
        event.Skip(True)
        # TODO See if we can resize boot.img columns on frame resize
        # populate_boot_list(self)
        # cw = 0
        # for i in range (0, self.list.ColumnCount - 1):
        #     self.list.SetColumnWidth(i, -2)
        #     cw += self.list.GetColumnWidth(i)
        # self.list.SetColumnWidth(self.list.ColumnCount - 1, self.list.BestVirtualSize.Width - cw)

    # -----------------------------------------------
    #                  _on_report_an_issue
    # -----------------------------------------------
    # Menu methods
    def _on_report_an_issue(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://github.com/badabing2005/PixelFlasher/issues/new')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_feature_request
    # -----------------------------------------------
    def _on_feature_request(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://github.com/badabing2005/PixelFlasher/issues/new')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_project_page
    # -----------------------------------------------
    def _on_project_page(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://github.com/badabing2005/PixelFlasher')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_forum
    # -----------------------------------------------
    def _on_forum(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://forum.xda-developers.com/t/pixelflasher-gui-tool-that-facilitates-flashing-updating-pixel-phones.4415453/')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_guide1
    # -----------------------------------------------
    def _on_guide1(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://forum.xda-developers.com/t/guide-root-pixel-6-with-magisk.4388733/')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_guide2
    # -----------------------------------------------
    def _on_guide2(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        webbrowser.open_new('https://forum.xda-developers.com/t/guide-root-pixel-6-oriole-with-magisk.4356233/')
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_open_config_folder
    # -----------------------------------------------
    def _on_open_config_folder(self, event):
        wait = wx.BusyCursor()
        self._on_spin('start')
        if sys.platform == "win32":
            os.system(f"start {get_config_path()}")
        self._on_spin('stop')
        del wait

    # -----------------------------------------------
    #                  _on_support_zip
    # -----------------------------------------------
    def _on_support_zip(self, event):
        with wx.FileDialog(self, "Save support file", '', 'support.zip', wildcard="Support files (*.zip)|*.zip",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                config_path = get_config_path()
                support_zip = os.path.join(config_path, 'support.zip')
                create_support_zip()
                debug(f"Saving support file to: {pathname}")
                with open(support_zip, "rb") as binaryfile :
                    with open(pathname, 'wb') as file:
                        byte_array = binaryfile.read()
                        file.write(byte_array)
                        file.close()
            except IOError:
                wx.LogError(f"Cannot save current data in file '{pathname}'.")

    # -----------------------------------------------
    #                  _on_exit_app
    # -----------------------------------------------
    def _on_exit_app(self, event):
        self.config.save(get_config_file_path())
        self.Close(True)

    # -----------------------------------------------
    #                  _on_help_about
    # -----------------------------------------------
    def _on_help_about(self, event):
        from About import AboutDlg
        about = AboutDlg(self)
        about.ShowModal()
        about.Destroy()

    # -----------------------------------------------
    #                  _on_advanced_config
    # -----------------------------------------------
    def _on_advanced_config(self, event):
        advanced_setting_dialog = AdvancedSettings(self)
        advanced_setting_dialog.CentreOnParent(wx.BOTH)
        res = advanced_setting_dialog.ShowModal()
        if res == wx.ID_OK:
            self.config.advanced_options = get_advanced_options()
            self.config.update_check = get_update_check()
            self.config.force_codepage = get_codepage_setting()
            self.config.custom_codepage = get_codepage_value()
            self.config.magisk = get_magisk_package()
        advanced_setting_dialog.Destroy()
        # show / hide advanced settings
        self._advanced_options_hide(not get_advanced_options())
        populate_boot_list(self)
        set_flash_button_state(self)

    # -----------------------------------------------
    #                  _on_install_apk
    # -----------------------------------------------
    def _on_install_apk(self, event):
        with wx.FileDialog(self, "select APK file to install", '', '', wildcard="Android Applications (*.*.apk)|*.apk", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                if device:
                    device.install_apk(pathname, fastboot_included=True)
                self._on_spin('stop')
                del wait
            except IOError:
                wx.LogError(f"Cannot install file '{pathname}'.")

    # -----------------------------------------------
    #                  _advanced_options_hide
    # -----------------------------------------------
    def _advanced_options_hide(self, value):
        self.Freeze()
        if value:
            # flash options
            self.advanced_options_label.Hide()
            self.flash_both_slots_checkBox.Hide()
            self.flash_to_inactive_slot_checkBox.Hide()
            self.disable_verity_checkBox.Hide()
            self.disable_verification_checkBox.Hide()
            self.fastboot_force_checkBox.Hide()
            self.fastboot_verbose_checkBox.Hide()
            self.temporary_root_checkBox.Hide()
            # slot options
            self.a_radio_button.Hide()
            self.b_radio_button.Hide()
            self.reboot_recovery_button.Hide()
            self.set_active_slot_button.Hide()
            self.sos_button.Hide()
            self.lock_bootloader.Hide()
            self.unlock_bootloader.Hide()
            # ROM options
            self.custom_rom_checkbox.Hide()
            self.custom_rom.Hide()
            self.process_rom.Hide()
            # Custom Flash Radio Button
            # if we're turning off advanced options, and the current mode is customFlash, hide, it
            self.mode_radio_button.LastInGroup.Hide()
            # Custom Flash Image options
            self.live_boot_radio_button.Hide()
            self.flash_radio_button.Hide()
            self.image_choice.Hide()
            self.image_file_picker.Hide()
            self.paste_boot.Hide()
            a = self.mode_radio_button.Name
            # if we're turning off advanced options, and the current mode is customFlash, change it to dryRun
            if self.mode_radio_button.Name == 'mode-customFlash' and self.mode_radio_button.GetValue():
                self.mode_radio_button.PreviousInGroup.SetValue(True)
                self.config.flash_mode = 'dryRun'
        else:
            # flash options
            self.advanced_options_label.Show()
            self.flash_both_slots_checkBox.Show()
            self.flash_to_inactive_slot_checkBox.Show()
            self.disable_verity_checkBox.Show()
            self.disable_verification_checkBox.Show()
            self.fastboot_force_checkBox.Show()
            self.fastboot_verbose_checkBox.Show()
            self.temporary_root_checkBox.Show()
            # slot options
            self.a_radio_button.Show()
            self.b_radio_button.Show()
            self.reboot_recovery_button.Show()
            self.set_active_slot_button.Show()
            self.sos_button.Show()
            self.lock_bootloader.Show()
            self.unlock_bootloader.Show()
            # ROM options
            self.custom_rom_checkbox.Show()
            self.custom_rom.Show()
            self.process_rom.Show()
            # Custom Flash Radio Button
            self.mode_radio_button.LastInGroup.Show()
            # Custom Flash Image options
            self.live_boot_radio_button.Show()
            self.flash_radio_button.Show()
            self.image_choice.Show()
            self.image_file_picker.Show()
            self.paste_boot.Show()
        self.Thaw()
        self._refresh_ui()

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        if state == 'start':
            self.spinner.Show()
            self.spinner_label.Show()
            self.spinner.Start()
        else:
            self.spinner.Stop()
            self.spinner.Hide()
            self.spinner_label.Hide()

    # -----------------------------------------------
    #                  _refresh_ui
    # -----------------------------------------------
    def _refresh_ui(self):
        # Update UI (need to do this resize to get the UI properly refreshed.)
        self.Freeze()
        self.Update()
        self.Layout()
        w, h = self.Size
        h = h + 100
        self.Size = (w, h)
        h = h - 100
        self.Size = (w, h)
        self.Refresh()
        self.Thaw()

    # -----------------------------------------------
    #                  _print_device_details
    # -----------------------------------------------
    def _print_device_details(self, device):
        print(f"\nSelected Device on {datetime.now():%Y-%m-%d %H:%M:%S}:")
        print(f"    Device ID:                       {device.id}")
        print(f"    Device Model:                    {device.hardware}")
        print(f"    Device Active Slot:              {device.active_slot}")
        print(f"    Device Mode:                     {device.true_mode}")
        if device.mode == 'adb':
            print(f"    Device is Rooted:                {device.rooted}")
            print(f"    Device Build:                    {device.build}")
            print(f"    Device API Level:                {device.api_level}")
            print(f"    Device Architecture:             {device.architecture}")
            print(f"    Device Bootloader Version:       {device.bootloader_version}")
            print(f"    Magisk Manager Version:          {device.magisk_app_version}")
        if device.mode == 'f.b':
            print(f"    Device Unlocked:                 {device.unlocked}")
        if device.rooted:
            print(f"    Magisk Version:                  {device.magisk_version}")
            print("    Magisk Modules:")
            print(f"{device.magisk_modules_summary}")
        else:
            print('')

    # -----------------------------------------------
    #                  _update_custom_flash_options
    # -----------------------------------------------
    def _update_custom_flash_options(self):
        boot = get_boot()
        if not boot:
            self.paste_boot.Enable(False)
        image_mode = get_image_mode()
        image_path = get_image_path()
        if self.config.flash_mode == 'customFlash':
            self.temporary_root_checkBox.Enable(False)
            self.image_file_picker.Enable(True)
            self.image_choice.Enable(True)
            if boot:
                self.paste_boot.Enable(True)
        else:
            # disable custom_flash_options
            if boot and boot.is_patched == 1:
                self.temporary_root_checkBox.Enable(True)
            else:
                self.temporary_root_checkBox.Enable(False)
            self.flash_radio_button.Enable(False)
            self.live_boot_radio_button.Enable(False)
            self.image_file_picker.Enable(False)
            self.image_choice.Enable(False)
            self.paste_boot.Enable(False)
            return
        self.live_boot_radio_button.Enable(False)
        self.flash_radio_button.Enable(False)
        self.flash_button.Enable(False)
        with contextlib.suppress(Exception):
            if image_path:
                filename, extension = os.path.splitext(image_path)
                extension = extension.lower()
                if image_mode == 'boot':
                    if boot:
                        self.paste_boot.Enable(True)
                    if extension == '.img':
                        self.live_boot_radio_button.Enable(True)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .img")
                elif image_mode in ['image', 'SIDELOAD']:
                    self.paste_boot.Enable(False)
                    if extension == '.zip':
                        self.live_boot_radio_button.Enable(False)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                        self.flash_radio_button.SetValue(True)
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .zip")
                else:
                    self.paste_boot.Enable(False)
                    if extension == '.img':
                        self.live_boot_radio_button.Enable(False)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                        self.flash_radio_button.SetValue(True)
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .img")
            elif image_mode == 'boot':
                if boot:
                    self.paste_boot.Enable(True)
            else:
                self.paste_boot.Enable(False)

    # -----------------------------------------------
    #                  _select_configured_device
    # -----------------------------------------------
    def _select_configured_device(self):
        if self.config.device:
            count = 0
            for device in get_phones():
                if device.id == self.config.device:
                    self.device_choice.Select(count)
                    set_phone(device)
                    self._print_device_details(device)
                count += 1
        elif self.device_choice.StringSelection != '':
            device = self.device_choice.StringSelection
            # replace multiple spaces with a single space and then split on space
            id = ' '.join(device.split())
            id = id.split()
            id = id[2]
            self.config.device = id
            for device in get_phones():
                if device.id == id:
                    set_phone(device)
                    self._print_device_details(device)
        else:
            set_phone(None)
            self.device_label.Label = "ADB Connected Devices"
        if self.device_choice.StringSelection == '':
            set_phone(None)
            self.device_label.Label = "ADB Connected Devices"
            self.config.device = None
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} No Device is selected!")
        self._reflect_slots()

    # -----------------------------------------------
    #                  _reflect_slots
    # -----------------------------------------------
    def _reflect_slots(self):
        device = get_phone()
        if device:
            self.reboot_recovery_button.Enable(True)
            self.reboot_bootloader_button.Enable(True)
            self.reboot_system_button.Enable(True)
            self.info_button.Enable(True)
            self.unlock_bootloader.Enable(True)
            self.lock_bootloader.Enable(True)
            self.install_magisk_button.Enable(True)
            self.install_apk.Enable(True)
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
            if device.magisk_modules_summary == '':
                self.magisk_button.Enable(False)
            else:
                self.magisk_button.Enable(True)
        else:
            self.device_label.Label = "ADB Connected Devices"
            self.a_radio_button.Enable(False)
            self.b_radio_button.Enable(False)
            self.a_radio_button.SetValue(False)
            self.b_radio_button.SetValue(False)
            self.set_active_slot_button.Enable(False)
            self.reboot_recovery_button.Enable(False)
            self.reboot_bootloader_button.Enable(False)
            self.reboot_system_button.Enable(False)
            self.info_button.Enable(False)
            self.magisk_button.Enable(False)
            self.unlock_bootloader.Enable(False)
            self.lock_bootloader.Enable(False)
            self.install_magisk_button.Enable(False)
            self.install_apk.Enable(False)

    #-----------------------------------------------------------------------------
    #                                   _init_ui
    #-----------------------------------------------------------------------------
    def _init_ui(self):
        def _add_mode_radio_button(sizer, index, flash_mode, label, tooltip):
            style = wx.RB_GROUP if index == 0 else 0
            self.mode_radio_button = wx.RadioButton(panel, name=f"mode-{flash_mode}", label=f"{label}", style=style)
            self.mode_radio_button.Bind(wx.EVT_RADIOBUTTON, _on_mode_changed)
            self.mode_radio_button.mode = flash_mode
            if flash_mode == self.config.flash_mode:
                self.mode_radio_button.SetValue(True)
            else:
                self.mode_radio_button.SetValue(False)
            self.mode_radio_button.SetToolTip(tooltip)
            sizer.Add(self.mode_radio_button)
            sizer.AddSpacer(10)

        # -----------------------------------------------
        #                  _on_select_device
        # -----------------------------------------------
        def _on_select_device(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            choice = event.GetEventObject()
            device = choice.GetString(choice.GetSelection())
            # replace multiple spaces with a single space and then split on space
            d_id = ' '.join(device.split())
            d_id = d_id.split()
            d_id = d_id[2]
            self.config.device = d_id
            for device in get_phones():
                if device.id == d_id:
                    set_phone(device)
                    self._print_device_details(device)
            self._reflect_slots()
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_scan
        # -----------------------------------------------
        def _on_scan(event):
            if get_adb():
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Scanning for Devices ...")
                wait = wx.BusyCursor()
                self._on_spin('start')
                self.device_choice.SetItems(get_connected_devices())
                if self.device_choice.Count > 0:
                    print(f"{self.device_choice.Count} Device(s) are found.")
                else:
                    print("No Devices found.")
                self._select_configured_device()
                self._on_spin('stop')
                del wait
            else:
                print("Please set Android Platform Tools Path first.")

        # -----------------------------------------------
        #                  _on_select_platform_tools
        # -----------------------------------------------
        def _on_select_platform_tools(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            self.config.platform_tools_path = event.GetPath().replace("'", "")
            check_platform_tools(self)
            if get_sdk_version():
                self.platform_tools_label.SetLabel(f"Android Platform Tools\nVersion {get_sdk_version()}")
            else:
                self.platform_tools_label.SetLabel("Android Platform Tools")
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_select_firmware
        # -----------------------------------------------
        def _on_select_firmware(event):
            self.config.firmware_path = event.GetPath().replace("'", "")
            wait = wx.BusyCursor()
            self._on_spin('start')
            select_firmware(self)
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_process_firmware
        # -----------------------------------------------
        def _on_process_firmware(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            if self.config.firmware_path:
                process_file(self, 'firmware')
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_process_rom
        # -----------------------------------------------
        def _on_process_rom(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            if self.config.custom_rom_path:
                process_file(self, 'rom')
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_image_choice
        # -----------------------------------------------
        def _on_image_choice(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            choice = event.GetEventObject()
            set_image_mode(choice.GetString(choice.GetSelection()))
            self._update_custom_flash_options()
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_image_select
        # -----------------------------------------------
        def _on_image_select(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            image_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(image_path)
            extension = extension.lower()
            if extension == '.zip' or extension == '.img':
                set_image_path(image_path)
                self._update_custom_flash_options()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Custom image file {image_path} is selected.")
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {image_path} is not img or zip file.")
                self.image_file_picker.SetPath('')
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_select_custom_rom
        # -----------------------------------------------
        def _on_select_custom_rom(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            custom_rom_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(custom_rom_path)
            extension = extension.lower()
            if extension == '.zip':
                self.config.custom_rom_path = custom_rom_path
                rom_file = ntpath.basename(custom_rom_path)
                set_custom_rom_id(os.path.splitext(rom_file)[0])
                populate_boot_list(self)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {custom_rom_path} is not a zip file.")
                self.custom_rom.SetPath('')
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_mode_changed
        # -----------------------------------------------
        def _on_mode_changed(event):
            self.mode_radio_button = event.GetEventObject()
            if self.mode_radio_button.GetValue():
                self.config.flash_mode = self.mode_radio_button.mode
                print(f"Flash mode changed to: {self.config.flash_mode}")
            if self.config.flash_mode != 'customFlash':
                set_flash_button_state(self)
            self._update_custom_flash_options()

        # -----------------------------------------------
        #                  _on_flash_both_slots
        # -----------------------------------------------
        def _on_flash_both_slots(event):
            self.flash_both_slots_checkBox = event.GetEventObject()
            status = self.flash_both_slots_checkBox.GetValue()
            self.config.flash_both_slots = status
            if status:
                self.config.flash_to_inactive_slot = not status
                self.flash_to_inactive_slot_checkBox.SetValue(not status)

        # -----------------------------------------------
        #                  _on_flash_to_inactive_slot
        # -----------------------------------------------
        def _on_flash_to_inactive_slot(event):
            self.flash_to_inactive_slot_checkBox = event.GetEventObject()
            status = self.flash_to_inactive_slot_checkBox.GetValue()
            self.config.flash_to_inactive_slot = status
            if status:
                self.config.flash_both_slots_checkBox = not status
                self.flash_both_slots_checkBox.SetValue(not status)

        # -----------------------------------------------
        #                  _on_disable_verity
        # -----------------------------------------------
        def _on_disable_verity(event):
            self.disable_verity_checkBox = event.GetEventObject()
            status = self.disable_verity_checkBox.GetValue()
            self.config.disable_verity = status

        # -----------------------------------------------
        #                  _on_disable_verification
        # -----------------------------------------------
        def _on_disable_verification(event):
            self.disable_verification_checkBox = event.GetEventObject()
            status = self.disable_verification_checkBox.GetValue()
            self.config.disable_verification = status

        # -----------------------------------------------
        #                  _on_fastboot_force
        # -----------------------------------------------
        def _on_fastboot_force(event):
            self.fastboot_force_checkBox = event.GetEventObject()
            status = self.fastboot_force_checkBox.GetValue()
            self.config.fastboot_force = status

        # -----------------------------------------------
        #                  _on_fastboot_verbose
        # -----------------------------------------------
        def _on_fastboot_verbose(event):
            self.fastboot_verbose_checkBox = event.GetEventObject()
            status = self.fastboot_verbose_checkBox.GetValue()
            self.config.fastboot_verbose = status

        # -----------------------------------------------
        #                  _on_temporary_root
        # -----------------------------------------------
        def _on_temporary_root(event):
            self._on_temporary_root_checkBox = event.GetEventObject()
            status = self._on_temporary_root_checkBox.GetValue()
            self.config.temporary_root = status

        # -----------------------------------------------
        #                  _on_verbose
        # -----------------------------------------------
        def _on_verbose(event):
            self.verbose_checkBox = event.GetEventObject()
            status = self.verbose_checkBox.GetValue()
            self.config.verbose = status
            set_verbose(status)

        # -----------------------------------------------
        #                  _on_reboot_recovery
        # -----------------------------------------------
        def _on_reboot_recovery(event):
            if self.config.device:
                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.reboot_recovery()
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_reboot_system
        # -----------------------------------------------
        def _on_reboot_system(event):
            if self.config.device:
                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.reboot_system()
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_reboot_bootloader
        # -----------------------------------------------
        def _on_reboot_bootloader(event):
            if self.config.device:
                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.reboot_bootloader(fastboot_included = True)
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_lock_bootloader
        # -----------------------------------------------
        def _on_lock_bootloader(event):
            if self.config.device:
                title = "Lock Bootloader"
                message = "         WARNING!!! WARNING!!! WARNING!!!\n\n"
                message += "NEVER, EVER LOCK THE BOOTLOADER WITHOUT REVERTING\n"
                message += "TO STOCK FIRMWARE OR YOUR PHONE WILL BE BRICKED!!!\n\n"
                message += "       THIS WILL WIPE YOUR DEVICE DATA!!!\n\n"
                message += "Do you want to continue to Lock the device bootloader?\n"
                message += "       Press OK to continue or CANCEL to abort.\n"
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
                print(message)
                set_message_box_title(title)
                set_message_box_message(message)
                dlg = MessageBox(self)
                dlg.CentreOnParent(wx.BOTH)
                result = dlg.ShowModal()

                if result == wx.ID_OK:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
                else:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                    print("Aborting ...\n")
                    dlg.Destroy()
                    return
                dlg.Destroy()

                title = "Lock Bootloader"
                message = "WARNING!!! THIS WILL ERASE ALL USER DATA FROM THE DEVICE\n\n"
                message += "Make sure you first read either of the guides linked in the help menu.\n"
                message += "Failing to follow the proper steps could potentially brick your phone.\n"
                message += "\nNote: Pressing OK button will invoke a script that will utilize\n"
                message += "fastboot commands, if your PC fastboot drivers are not propely setup,\n"
                message += "fastboot will wait forever, and PixelFlasher will appear hung.\n"
                message += "In such cases, killing the fastboot process will resume to normalcy.\n\n"
                message += "      Do you want to continue to Lock the device bootloader?\n"
                message += "              Press OK to continue or CANCEL to abort.\n"
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
                print(message)
                set_message_box_title(title)
                set_message_box_message(message)
                dlg = MessageBox(self)
                dlg.CentreOnParent(wx.BOTH)
                result = dlg.ShowModal()

                if result == wx.ID_OK:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
                else:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                    print("Aborting ...\n")
                    dlg.Destroy()
                    return
                dlg.Destroy()

                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.lock_bootloader()
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_unlock_bootloader
        # -----------------------------------------------
        def _on_unlock_bootloader(event):
            if self.config.device:
                title = "Unlock Bootloader"
                message = "WARNING!!! THIS WILL ERASE ALL USER DATA FROM THE DEVICE\n\n"
                message += "Make sure you first read either of the guides linked in the help menu.\n"
                message += "Failing to follow the proper steps could potentially brick your phone.\n"
                message += "\nNote: Pressing OK button will invoke a script that will utilize\n"
                message += "fastboot commands, if your PC fastboot drivers are not propely setup,\n"
                message += "fastboot will wait forever, and PixelFlasher will appear hung.\n"
                message += "In such cases, killing the fastboot process will resume to normalcy.\n\n"
                message += "      Do you want to continue to Unlock the device bootloader?\n"
                message += "              Press OK to continue or CANCEL to abort.\n"
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
                print(message)
                set_message_box_title(title)
                set_message_box_message(message)
                dlg = MessageBox(self)
                dlg.CentreOnParent(wx.BOTH)
                result = dlg.ShowModal()

                if result == wx.ID_OK:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
                else:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                    print("Aborting ...\n")
                    dlg.Destroy()
                    return
                dlg.Destroy()

                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.unlock_bootloader()
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_sos
        # -----------------------------------------------
        def _on_sos(event):
            if self.config.device:
                title = "Disable Magisk Modules"
                message = "WARNING!!! This is an experimental feature to attempt disabling magisk modules.\n\n"
                message += "You would only need to do this if your device is bootlooping due to\n"
                message += "incompatible magisk modules, this is not guaranteed to work in all cases (YMMV).\n"
                message += "\nNote: Pressing OK button will invoke a script that will wait forever to detect the device.\n"
                message += "If your device is not detected PixelFlasher will appear hung.\n"
                message += "In such cases, killing the adb process will resume to normalcy.\n\n"
                message += "              Press OK to continue or CANCEL to abort.\n"
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
                print(message)
                set_message_box_title(title)
                set_message_box_message(message)
                dlg = MessageBox(self)
                dlg.CentreOnParent(wx.BOTH)
                result = dlg.ShowModal()

                if result == wx.ID_OK:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
                else:
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                    print("Aborting ...\n")
                    dlg.Destroy()
                    return
                dlg.Destroy()

                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                device.disable_magisk_modules()
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_device_info
        # -----------------------------------------------
        def _on_device_info(event):
            if self.config.device:
                wait = wx.BusyCursor()
                self._on_spin('start')
                device = get_phone()
                print(f"Device Info:\n------------\n{device.device_info}")
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _on_magisk_modules
        # -----------------------------------------------
        def _on_magisk_modules(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            dlg = MagiskModules(self)
            dlg.CentreOnParent(wx.BOTH)
            self._on_spin('stop')
            del wait
            result = dlg.ShowModal()
            if result != wx.ID_OK:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                print("Aborting Magisk Modules Management ...\n")
                dlg.Destroy()
                return
            dlg.Destroy()

        # -----------------------------------------------
        #                  _on_magisk_install
        # -----------------------------------------------
        def _on_magisk_install(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            dlg = MagiskDownloads(self)
            dlg.CentreOnParent(wx.BOTH)
            self._on_spin('stop')
            del wait
            result = dlg.ShowModal()
            if result != wx.ID_OK:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                print("Aborting Magisk Installation ...\n")
                dlg.Destroy()
                return
            dlg.Destroy()

        # -----------------------------------------------
        #                  _on_set_active_slot
        # -----------------------------------------------
        def _on_set_active_slot(event):
            if self.config.device:
                wait = wx.BusyCursor()
                self._on_spin('start')
                if self.a_radio_button.GetValue():
                    slot = 'a'
                elif self.b_radio_button.GetValue():
                    slot = 'b'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Please first select a slot.")
                    self._on_spin('stop')
                    del wait
                    return
                device = get_phone()
                device.set_active_slot(slot)
                time.sleep(5)
                self.device_choice.SetItems(get_connected_devices())
                self._select_configured_device()
                self._on_spin('stop')
                del wait

        # -----------------------------------------------
        #                  _open_firmware_link
        # -----------------------------------------------
        def _open_firmware_link(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            with contextlib.suppress(Exception):
                device = get_phone()
                hardware = device.hardware
            webbrowser.open_new(f"https://developers.google.com/android/images#{hardware}")
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _open_sdk_link
        # -----------------------------------------------
        def _open_sdk_link(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            webbrowser.open_new('https://developer.android.com/studio/releases/platform-tools.html')
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_custom_rom
        # -----------------------------------------------
        def _on_custom_rom(event):
            self.custom_rom_checkbox = event.GetEventObject()
            status = self.custom_rom_checkbox.GetValue()
            self.config.custom_rom = status
            if status:
                self.custom_rom.Enable()
                self.process_rom.Enable()
                populate_boot_list(self)
            else:
                self.custom_rom.Disable()
                self.process_rom.Disable()
                populate_boot_list(self)

        # -----------------------------------------------
        #                  _on_show_all_boot
        # -----------------------------------------------
        def _on_show_all_boot(event):
            self.show_all_boot_checkBox = event.GetEventObject()
            status = self.show_all_boot_checkBox.GetValue()
            self.config.show_all_boot = status
            populate_boot_list(self)

        # -----------------------------------------------
        #                  _on_boot_selected
        # -----------------------------------------------
        def _on_boot_selected(event):
            x,y = event.GetPosition()
            row,flags = self.list.HitTest((x,y))
            boot = None
            for i in range (0, self.list.ItemCount):
                # deselect all items
                self.list.Select(i, 0)
                item = self.list.GetItem(i)
                # reset colors
                if sys.platform != "win32":
                    if darkdetect.isDark():
                        item.SetTextColour(wx.WHITE)
                else:
                    item.SetTextColour(wx.BLACK)
                self.list.SetItem(item)
            if row != -1:
                boot = Boot()
                self.list.Select(row)
                item = self.list.GetItem(row)
                if sys.platform == "win32":
                    item.SetTextColour(wx.BLUE)
                self.list.SetItem(item)
                boot.boot_hash = self.list.GetItemText(row, col=0)
                # get the raw data from db, listctrl is just a formatted display
                con = get_db()
                con.execute("PRAGMA foreign_keys = ON")
                query = f"{boot.boot_hash}%"
                sql = """
                    SELECT
                        BOOT.id as boot_id,
                        BOOT.boot_hash,
                        BOOT.file_path as boot_path,
                        BOOT.is_patched,
                        BOOT.magisk_version,
                        BOOT.hardware,
                        BOOT.epoch as boot_date,
                        PACKAGE.id as package_id,
                        PACKAGE.boot_hash as package_boot_hash,
                        PACKAGE.type as package_type,
                        PACKAGE.package_sig,
                        PACKAGE.file_path as package_path,
                        PACKAGE.epoch as package_date
                    FROM BOOT
                    JOIN PACKAGE_BOOT
                        ON BOOT.id = PACKAGE_BOOT.boot_id
                        AND BOOT.boot_hash LIKE '%s'
                    JOIN PACKAGE
                        ON PACKAGE.id = PACKAGE_BOOT.package_id;
                """ % query
                with con:
                    data = con.execute(sql)
                    i = 0
                    for row in data:
                        boot.boot_id = row[0]
                        boot.boot_hash = row[1]
                        boot.boot_path = row[2]
                        boot.is_patched = row[3]
                        boot.magisk_version = row[4]
                        boot.hardware = row[5]
                        boot.boot_epoch = row[6]
                        boot.package_id = row[7]
                        boot.package_boot_hash = row[8]
                        boot.package_type = row[9]
                        boot.package_sig = row[10]
                        boot.package_path = row[11]
                        boot.package_epoch = row[12]
                        i += 1
                    if i > 1:
                        debug("INFO: Duplicate PACKAGE_BOOT records found")
                self.config.boot_id = boot.boot_id
                self.config.selected_boot_md5 = boot.boot_hash
                self.delete_boot_button.Enable(True)
                self.live_boot_button.Enable(True)
                if boot.magisk_version == '':
                    self.patch_boot_button.Enable(True)
                    print(f"\nSelected Boot: {boot.boot_hash} from image: {boot.package_path}" )
                else:
                    self.patch_boot_button.Enable(False)
                    print(f"\nSelected Patched Boot: {boot.boot_hash} from image: {boot.package_path}" )
                debug(f"boot.img Path: {boot.boot_path}" )
            else:
                self.config.boot_id = None
                self.config.selected_boot_md5 = None
                self.patch_boot_button.Enable(False)
                self.delete_boot_button.Enable(False)
                self.live_boot_button.Enable(False)
                self.paste_boot.Enable(False)
                if self.list.ItemCount == 0 :
                    if self.config.firmware_path:
                        print("\nPlease Process the firmware!")
                else:
                    print("\nPlease select a boot.img!")
            set_boot(boot)
            set_flash_button_state(self)
            self._update_custom_flash_options()

        # -----------------------------------------------
        #                  _on_delete_boot
        # -----------------------------------------------
        def _on_delete_boot(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            boot = get_boot()
            if boot.boot_id and boot.package_id:
                print(f"Deleting boot record,  ID:{boot.boot_id}  Boot_ID:{boot.boot_hash[:8]} ...")
                con = get_db()
                con.execute("PRAGMA foreign_keys = ON")
                con.commit()
                sql = """
                    DELETE FROM PACKAGE_BOOT
                    WHERE boot_id = '%s' AND package_id = '%s';
                """ % (boot.boot_id, boot.package_id)
                try:
                    with con:
                        data = con.execute(sql)
                    con.commit()
                except Exception as e:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                    print(e)
                sql = """
                    DELETE FROM BOOT
                    WHERE id = '%s';
                """ % boot.boot_id
                try:
                    with con:
                        data = con.execute(sql)
                    con.commit()
                except Exception as e:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                    print(e)
                # Check to see if this is the last entry for the package_id, if it is,
                # delete the package from db and output a message that a firmware should be selected.
                # Also delete unpacked files from factory_images cache
                try:
                    cursor = con.cursor()
                    cursor.execute(f"SELECT * FROM PACKAGE_BOOT WHERE package_id = '{boot.package_id}'")
                    data = cursor.fetchall()
                    if len(data) == 0:
                        sql = """
                            DELETE FROM PACKAGE
                            WHERE id = '%s';
                        """ % boot.package_id
                        with con:
                            data = con.execute(sql)
                        con.commit()
                        print(f"Cleared db entry for: {boot.package_path}")
                        config_path = get_config_path()
                        tmp = os.path.join(config_path, 'factory_images', boot.package_sig)
                        print(f"Deleting Firmware cache for: {tmp} ...")
                        delete_all(tmp)
                except Exception as e:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                    print(e)
                con.commit()

                # delete the boot file
                print(f"Deleting Boot file: {boot.boot_path} ...")
                if os.path.exists(boot.boot_path):
                    os.remove(boot.boot_path)
                set_boot(None)
                populate_boot_list(self)
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_live_boot
        # -----------------------------------------------
        def _on_live_boot(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            live_boot_phone(self)
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_paste_boot
        # -----------------------------------------------
        def _on_paste_boot(event):
            boot = get_boot()
            if boot:
                if boot.boot_path:
                    print(f"Pasted {boot.boot_path} to custom flash")
                    self.image_file_picker.SetPath(boot.boot_path)
                    set_image_path(boot.boot_path)
                    set_flash_button_state(self)

        # -----------------------------------------------
        #                  _on_patch_boot
        # -----------------------------------------------
        def _on_patch_boot(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            patch_boot_img(self)
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_flash
        # -----------------------------------------------
        def _on_flash(event):
            wait = wx.BusyCursor()
            self._on_spin('start')
            flash_phone(self)
            self._on_spin('stop')
            del wait

        # -----------------------------------------------
        #                  _on_clear
        # -----------------------------------------------
        def _on_clear(event):
            self.console_ctrl.SetValue("")

        # ==============
        # UI Setup Here
        # ==============
        panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.VERTICAL)

        NUMROWS = 13
        fgs1 = wx.FlexGridSizer(NUMROWS, 2, 10, 10)

        # 1st row widgets, Android platfom tools
        self.platform_tools_label = wx.StaticText(panel, label=u"Android Platform Tools")
        self.sdk_link = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.sdk_link.SetBitmap(images.Open_Link.GetBitmap())
        self.sdk_link.SetToolTip(u"Download Latest Android Platform-Tools")
        self.platform_tools_picker = wx.DirPickerCtrl(panel, style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
        self.platform_tools_picker.SetToolTip(u"Select Android Platform-Tools Folder\nWhere adb and fastboot are located.")
        platform_tools_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        platform_tools_label_sizer.Add(self.platform_tools_label, 1, wx.EXPAND)
        platform_tools_label_sizer.Add(self.sdk_link, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=24)
        self.sdk_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sdk_sizer.Add(self.platform_tools_picker, 1, wx.EXPAND)

        # 2nd row widgets, Connected Devices
        self.device_label = wx.StaticText(panel, label=u"ADB Connected Devices")
        self.device_choice = wx.Choice(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, [], 0)
        self.device_choice.SetSelection(0)
        self.device_choice.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        device_tooltip = "[root status] [device mode] [device id] [device model] [device firmware]\n\n"
        device_tooltip += "✓ Rooted with Magisk.\n"
        device_tooltip += "✗ Probably Not Root (Magisk Tools not found).\n"
        device_tooltip += "?  Unable to determine the root status.\n\n"
        device_tooltip += "(adb) device is in adb mode\n"
        device_tooltip += "(f.b) device is in fastboot mode\n"
        device_tooltip += "(sid) device is in sideload mode\n"
        device_tooltip += "(rec) device is in recovery mode\n"
        self.device_choice.SetToolTip(device_tooltip)
        self.scan_button = wx.Button(panel, label=u"Scan")
        self.scan_button.SetToolTip(u"Scan for Devices\nPlease manually select the device after the scan is completed.")
        self.scan_button.SetBitmap(images.Scan.GetBitmap())
        self.scan_button.Enable(False)
        device_tooltip = "[root status] [device mode] [device id] [device model] [device firmware]\n\n"
        device_sizer = wx.BoxSizer(wx.HORIZONTAL)
        device_sizer.Add(self.device_choice, 1, wx.EXPAND)
        device_sizer.Add(self.scan_button, flag=wx.LEFT, border=5)

        # 3rd row Reboot buttons, device related buttons
        self.a_radio_button = wx.RadioButton(panel, wx.ID_ANY, u"A", wx.DefaultPosition, wx.DefaultSize, 0)
        self.b_radio_button = wx.RadioButton(panel, wx.ID_ANY, u"B", wx.DefaultPosition, wx.DefaultSize, 0)
        active_slot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        active_slot_sizer.Add((0, 0), 1, wx.EXPAND, 10)
        active_slot_sizer.Add(self.a_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        active_slot_sizer.Add(self.b_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        self.reboot_recovery_button = wx.Button(panel, wx.ID_ANY, u" Reboot to Recovery  ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reboot_recovery_button.SetToolTip(u"Reboot to Recovery")
        self.reboot_system_button = wx.Button(panel, wx.ID_ANY, u"Reboot to System", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reboot_system_button.SetToolTip(u"Reboot to System")
        self.reboot_bootloader_button = wx.Button(panel, wx.ID_ANY, u"Reboot to Bootloader", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reboot_bootloader_button.SetToolTip(u"Reboot to Bootloader")
        self.set_active_slot_button = wx.Button(panel, wx.ID_ANY, u"Set Active Slot", wx.DefaultPosition, wx.DefaultSize, 0)
        self.set_active_slot_button.SetToolTip(u"Sets Active Slot to the selected A or B slot")
        self.info_button = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.info_button.SetBitmap(images.About.GetBitmap())
        self.info_button.SetToolTip(u"Dump Full Device Info")
        self.magisk_button = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.magisk_button.SetBitmap(images.Magisk.GetBitmap())
        self.magisk_button.SetToolTip(u"Manage Magisk Modules.")
        self.install_magisk_button = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.install_magisk_button.SetBitmap(images.InstallMagisk.GetBitmap())
        self.install_magisk_button.SetToolTip(u"Download and Install Magisk Manager")
        self.sos_button = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.sos_button.SetBitmap(images.Sos.GetBitmap())
        self.sos_button.SetToolTip(u"Disable Magisk Modules\nThis button issues the following command:\n    adb wait-for-device shell magisk --remove-modules\nThis helps for cases where device bootloops due to incompatible magisk modules(YMMV).")
        self.lock_bootloader = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.lock_bootloader.SetBitmap(images.Lock.GetBitmap())
        self.lock_bootloader.SetToolTip(u"Lock Bootloader\nCaution Will Wipe Data")
        self.unlock_bootloader = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.unlock_bootloader.SetBitmap(images.Unlock.GetBitmap())
        self.unlock_bootloader.SetToolTip(u"Unlock Bootloader\nCaution Will Wipe Data")
        # reboot_sizer.Add((5, 0), 0, 0, 5)
        reboot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reboot_sizer.Add(self.set_active_slot_button, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
        reboot_sizer.Add(self.reboot_recovery_button, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
        reboot_sizer.Add(self.reboot_system_button, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        reboot_sizer.Add(self.reboot_bootloader_button, 1, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        reboot_sizer.Add(self.info_button, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=10)
        reboot_sizer.Add(self.magisk_button, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)
        reboot_sizer.Add(self.install_magisk_button, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)
        reboot_sizer.Add(self.sos_button, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)
        reboot_sizer.Add(self.lock_bootloader, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        reboot_sizer.Add(self.unlock_bootloader, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        reboot_sizer.Add((self.scan_button.Size.Width + 5, 0), 0, wx.EXPAND)

        # 4th row, empty row, static line
        self.staticline1 = wx.StaticLine(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.staticline2 = wx.StaticLine(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.staticline2.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))

        # 5th row widgets, firmware file
        firmware_label = wx.StaticText(panel, label=u"Pixel Phone Factory Image")
        self.firmware_link = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.firmware_link.SetBitmap(images.Open_Link.GetBitmap())
        self.firmware_link.SetToolTip(u"Download Pixel Firmware")
        self.firmware_picker = wx.FilePickerCtrl(panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"Factory Image files (*.zip)|*.zip", wx.DefaultPosition, wx.DefaultSize , style=wx.FLP_USE_TEXTCTRL)
        self.firmware_picker.SetToolTip(u"Select Pixel Firmware")
        self.process_firmware = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.process_firmware.SetBitmap(images.Process_File.GetBitmap())
        self.process_firmware.SetToolTip(u"Process the firmware file and extract the boot.img")
        firmware_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        firmware_label_sizer.Add(firmware_label, 1, wx.EXPAND)
        firmware_label_sizer.Add(self.firmware_link, flag=wx.LEFT, border=5)
        self.firmware_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.firmware_sizer.Add(self.firmware_picker, 1, wx.EXPAND)
        self.firmware_sizer.Add(self.process_firmware, flag=wx.LEFT, border=5)

        # 6th row widgets, custom_rom
        self.custom_rom_checkbox = wx.CheckBox(panel, wx.ID_ANY, u"Apply Custom ROM", wx.DefaultPosition, wx.DefaultSize, 0)
        self.custom_rom_checkbox.SetToolTip(u"Caution: Make sure you read the selected ROM documentation.\nThis might not work for your ROM")
        self.custom_rom = wx.FilePickerCtrl(panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"ROM files (*.zip)|*.zip", wx.DefaultPosition, wx.DefaultSize , style=wx.FLP_USE_TEXTCTRL)
        self.custom_rom.SetToolTip(u"Select Custom ROM")
        self.process_rom = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.process_rom.SetBitmap(images.Process_File.GetBitmap())
        self.process_rom.SetToolTip(u"Process the ROM file and extract the boot.img")
        custom_rom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_rom_sizer.Add(self.custom_rom, 1, wx.EXPAND)
        custom_rom_sizer.Add(self.process_rom, flag=wx.LEFT, border=5)

        # 7th row widgets, boot.img related widgets
        self.select_boot_label = wx.StaticText(panel, label=u"Select a boot.img")
        self.show_all_boot_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Show All boot.img", wx.DefaultPosition, wx.DefaultSize, 0)
        self.show_all_boot_checkBox.SetToolTip(u"Show all boot.img even if it is\nnot part of the selected firmware or ROM")
        # list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.Patched.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.Patched_Small.GetBitmap())
        self.list  = wx.ListCtrl(panel, -1, size=(-1, self.CharHeight * 6), style = wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.InsertColumn(0, 'SHA1', wx.LIST_FORMAT_LEFT, width = -1)
        self.list.InsertColumn(1, 'Source SHA1', wx.LIST_FORMAT_LEFT, width = -1)
        self.list.InsertColumn(2, 'Package Fingerprint', wx.LIST_FORMAT_LEFT, width = -1)
        self.list.InsertColumn(3, 'Patched with Magisk', wx.LIST_FORMAT_LEFT,  -1)
        self.list.InsertColumn(4, 'Patched on Device', wx.LIST_FORMAT_LEFT,  -1)
        self.list.InsertColumn(5, 'Date', wx.LIST_FORMAT_LEFT,  -1)
        self.list.InsertColumn(6, 'Package Path', wx.LIST_FORMAT_LEFT,  -1)
        self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10))))
        if sys.platform != "win32":
            self.list.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        self.list.SetColumnWidth(0, -2)
        self.list.SetColumnWidth(1, -2)
        self.list.SetColumnWidth(2, -2)
        self.list.SetColumnWidth(3, -2)
        self.list.SetColumnWidth(4, -2)
        self.list.SetColumnWidth(5, -2)
        self.list.SetColumnWidth(6, -2)
        self.patch_boot_button = wx.Button(panel, wx.ID_ANY, u"Patch", wx.DefaultPosition, wx.DefaultSize, 0)
        self.patch_boot_button.SetBitmap(images.Patch.GetBitmap())
        self.patch_boot_button.SetToolTip(u"Patch Selected boot.img")
        self.delete_boot_button = wx.Button(panel, wx.ID_ANY, u"Delete", wx.DefaultPosition, wx.DefaultSize, 0)
        self.delete_boot_button.SetBitmap(images.Delete.GetBitmap())
        self.delete_boot_button.SetToolTip(u"Delete Selected boot.img")
        self.live_boot_button = wx.Button(panel, wx.ID_ANY, u"Live Boot", wx.DefaultPosition, wx.DefaultSize, 0)
        self.live_boot_button.SetBitmap(images.Boot.GetBitmap())
        self.live_boot_button.SetToolTip(u"Live boot the selected boot.img")
        label_v_sizer = wx.BoxSizer(wx.VERTICAL)
        label_v_sizer.Add(self.select_boot_label, flag=wx.ALL)
        label_v_sizer.AddSpacer(10)
        label_v_sizer.Add(self.show_all_boot_checkBox, flag=wx.ALL)
        image_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        image_buttons_sizer.Add(self.patch_boot_button, proportion=1, flag=wx.LEFT|wx.BOTTOM, border=5)
        image_buttons_sizer.Add(self.delete_boot_button, proportion=1, flag=wx.LEFT|wx.TOP, border=5)
        image_buttons_sizer.Add(self.live_boot_button, proportion=1, flag=wx.LEFT|wx.TOP, border=5)
        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        list_sizer.Add(self.list, 1, wx.ALL|wx.EXPAND)
        list_sizer.Add(image_buttons_sizer, 0, wx.ALL|wx.EXPAND)
        list_sizer.Add((self.sdk_link.BestSize.Width + 5, 0), 0, wx.EXPAND)

        # 8th row widgets
        mode_label = wx.StaticText(panel, label=u"Flash Mode")
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # _add_mode_radio_button(sizer, index, flash_mode, label, tooltip)
        _add_mode_radio_button(mode_sizer, 0, 'keepData', "Keep Data", "Data will be kept intact.")
        _add_mode_radio_button(mode_sizer, 1, 'wipeData', "WIPE all data", "CAUTION: This will wipe your data")
        _add_mode_radio_button(mode_sizer, 2, 'dryRun', "Dry Run", "Dry Run, no flashing will be done.\nThe phone will reboot to fastboot and then\nback to normal.\nThis is for testing.")
        _add_mode_radio_button(mode_sizer, 3, 'customFlash', "Custom Flash", "Custom Flash, Advanced option to flash a single file.\nThis will not flash the factory image.\It will flash the single selected file.")

        # 9th row widgets (custom flash)
        self.live_boot_radio_button = wx.RadioButton(panel, wx.ID_ANY, u"Live Boot", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.live_boot_radio_button.Enable(False)
        self.live_boot_radio_button.SetToolTip(u"Live Boot to selected boot.img")
        self.flash_radio_button = wx.RadioButton(panel, wx.ID_ANY, u"Flash", wx.DefaultPosition, wx.DefaultSize, 0)
        self.flash_radio_button.SetValue(True)
        self.flash_radio_button.Enable(False)
        self.flash_radio_button.SetToolTip(u"Flashes the selected boot.img")
        custom_advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_advanced_options_sizer.Add(self.live_boot_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        custom_advanced_options_sizer.Add(self.flash_radio_button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        # 2nd column
        image_choices = [ u"boot", u"bootloader", u"dtbo", u"product", u"radio", u"recovery", u"super_empty", u"system", u"system_ext", u"system_other", u"vbmeta", u"vbmeta_system", u"vbmeta_vendor", u"vendor", u"vendor_boot", u"vendor_dlkm", u"image", u"SIDELOAD" ]
        self.image_choice = wx.Choice(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, image_choices, 0)
        self.image_choice.SetSelection(0)
        self.image_file_picker = wx.FilePickerCtrl(panel, wx.ID_ANY, wx.EmptyString, u"Select a file", u"Flashable files (*.img;*.zip)|*.img;*.zip", wx.DefaultPosition, wx.DefaultSize, wx.FLP_USE_TEXTCTRL)
        self.paste_boot = wx.BitmapButton(panel, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|0)
        self.paste_boot.SetBitmap(images.Paste.GetBitmap())
        self.paste_boot.SetToolTip(u"Paste the selected boot.img as custom image.")
        custom_flash_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_flash_sizer.Add(self.image_choice, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        custom_flash_sizer.Add(self.image_file_picker, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        custom_flash_sizer.Add(self.paste_boot, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)

        # 10th row widgets, Flash options
        self.advanced_options_label = wx.StaticText(panel, label=u"Flash Options")
        self.flash_both_slots_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Flash to both slots", wx.DefaultPosition, wx.DefaultSize, 0)
        self.flash_to_inactive_slot_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Flash to inactive slot", wx.DefaultPosition, wx.DefaultSize, 0)
        self.flash_to_inactive_slot_checkBox.SetToolTip(u"This option when checked will flash to the alterante slot (inactive).\nKeeping the current slot intact.")
        self.disable_verity_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Disable Verity", wx.DefaultPosition, wx.DefaultSize, 0)
        self.disable_verification_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Disable Verification", wx.DefaultPosition, wx.DefaultSize, 0)
        self.fastboot_force_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Force", wx.DefaultPosition, wx.DefaultSize, 0)
        self.fastboot_force_checkBox.SetToolTip(u"Force a flash operation that may be unsafe (will wipe your data)")
        self.fastboot_verbose_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Verbose", wx.DefaultPosition, wx.DefaultSize, 0)
        self.fastboot_verbose_checkBox.SetToolTip(u"set fastboot option to verbose")
        self.temporary_root_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Temporary Root", wx.DefaultPosition, wx.DefaultSize, 0)
        self.temporary_root_checkBox.SetToolTip(u"This option when enabled will not flash patched boot.img\nInstead it will flash unpatched boot.img, but boot to Live Patched boot.img\nHandy to test if magisk will cause a bootloop.\n\nPlease be aware that factory image will be flashed, and if you reboot\nthe device will be unrooted.\nIf you want to make this permanent, just flash the patched boot.img")
        self.advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.advanced_options_sizer.Add(self.flash_both_slots_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.flash_to_inactive_slot_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.disable_verity_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.disable_verification_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.fastboot_force_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.fastboot_verbose_checkBox)
        self.advanced_options_sizer.AddSpacer(10)
        self.advanced_options_sizer.Add(self.temporary_root_checkBox)
        self.advanced_options_sizer.AddSpacer(10)

        # 11th row widgets, Flash button
        self.flash_button = wx.Button(panel, -1, "Flash Pixel Phone", wx.DefaultPosition, wx.Size(-1,50))
        self.flash_button.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.flash_button.SetToolTip(u"Flashes the selected device with chosen flash options.")
        self.flash_button.SetBitmap(images.Flash.GetBitmap())

        # 12th row widgets, console
        console_label = wx.StaticText(panel, label=u"Console")
        self.spinner = wx.ActivityIndicator(panel, size=(100, 100))
        self.spinner_label = wx.StaticText(panel, label=u"Please be patient ...")
        self.spinner_label.SetForegroundColour((255,165,0))
        self.spinner_label.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        console_v_sizer = wx.BoxSizer(wx.VERTICAL)
        console_v_sizer.Add(console_label, flag=wx.ALL)
        console_v_sizer.AddSpacer(40)
        console_v_sizer.Add(self.spinner, flag=wx.LEFT, border=50)
        console_v_sizer.AddSpacer(20)
        console_v_sizer.Add(self.spinner_label, flag=wx.ALL)
        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.console_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        if darkdetect.isLight():
            self.console_ctrl.SetBackgroundColour(wx.WHITE)
            self.console_ctrl.SetForegroundColour(wx.BLUE)
            self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        # 13th row widgets, verbose and clear button
        self.verbose_checkBox = wx.CheckBox(panel, wx.ID_ANY, u"Verbose", wx.DefaultPosition, wx.DefaultSize, 0)
        self.verbose_checkBox.SetToolTip(u"Enable Verbose Messages in the console.")
        clear_button = wx.Button(panel, -1, "Clear Console")

        # add the rows to flexgrid
        fgs1.AddMany([
                    (platform_tools_label_sizer, 0, wx.ALIGN_CENTER_VERTICAL, 5), (self.sdk_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (self.device_label, 0, wx.ALIGN_CENTER_VERTICAL, 5), (device_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (active_slot_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (reboot_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    self.staticline1, (self.staticline2, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND|wx.TOP, 20),
                    (firmware_label_sizer, 0, wx.ALIGN_CENTER_VERTICAL, 5), (self.firmware_sizer, 1, wx.EXPAND),
                    (self.custom_rom_checkbox, 0, wx.ALIGN_CENTER_VERTICAL, 5), (custom_rom_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (label_v_sizer, 1, wx.EXPAND), (list_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    (mode_label, 0, wx.ALIGN_CENTER_VERTICAL, 5), (mode_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (custom_advanced_options_sizer, 0, wx.ALIGN_CENTER_VERTICAL, 5), (custom_flash_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    self.advanced_options_label, self.advanced_options_sizer,
                    (wx.StaticText(panel, label="")), (self.flash_button, 1, wx.EXPAND),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    (console_v_sizer, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND),
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
        self.scan_button.Bind(wx.EVT_BUTTON, _on_scan)
        self.firmware_picker.Bind(wx.EVT_FILEPICKER_CHANGED, _on_select_firmware)
        self.firmware_link.Bind(wx.EVT_BUTTON, _open_firmware_link)
        self.platform_tools_picker.Bind(wx.EVT_DIRPICKER_CHANGED, _on_select_platform_tools)
        self.sdk_link.Bind(wx.EVT_BUTTON, _open_sdk_link)
        self.custom_rom_checkbox.Bind(wx.EVT_CHECKBOX, _on_custom_rom)
        self.custom_rom.Bind(wx.EVT_FILEPICKER_CHANGED, _on_select_custom_rom)
        self.disable_verification_checkBox.Bind(wx.EVT_CHECKBOX, _on_disable_verification)
        self.flash_both_slots_checkBox.Bind(wx.EVT_CHECKBOX, _on_flash_both_slots)
        self.flash_to_inactive_slot_checkBox.Bind(wx.EVT_CHECKBOX, _on_flash_to_inactive_slot)
        self.disable_verity_checkBox.Bind(wx.EVT_CHECKBOX, _on_disable_verity)
        self.fastboot_force_checkBox.Bind(wx.EVT_CHECKBOX, _on_fastboot_force)
        self.fastboot_verbose_checkBox.Bind(wx.EVT_CHECKBOX, _on_fastboot_verbose)
        self.temporary_root_checkBox.Bind(wx.EVT_CHECKBOX, _on_temporary_root)
        self.flash_button.Bind(wx.EVT_BUTTON, _on_flash)
        self.verbose_checkBox.Bind(wx.EVT_CHECKBOX, _on_verbose)
        clear_button.Bind(wx.EVT_BUTTON, _on_clear)
        self.reboot_recovery_button.Bind(wx.EVT_BUTTON, _on_reboot_recovery)
        self.reboot_system_button.Bind(wx.EVT_BUTTON, _on_reboot_system)
        self.reboot_bootloader_button.Bind(wx.EVT_BUTTON, _on_reboot_bootloader)
        self.info_button.Bind(wx.EVT_BUTTON, _on_device_info)
        self.magisk_button.Bind(wx.EVT_BUTTON, _on_magisk_modules)
        self.install_magisk_button.Bind(wx.EVT_BUTTON, _on_magisk_install)
        self.sos_button.Bind(wx.EVT_BUTTON, _on_sos)
        self.lock_bootloader.Bind(wx.EVT_BUTTON, _on_lock_bootloader)
        self.unlock_bootloader.Bind(wx.EVT_BUTTON, _on_unlock_bootloader)
        self.set_active_slot_button.Bind(wx.EVT_BUTTON, _on_set_active_slot)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_SIZE, self._on_resize)
        self.image_file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, _on_image_select)
        self.image_choice.Bind(wx.EVT_CHOICE, _on_image_choice)
        self.list.Bind(wx.EVT_LEFT_DOWN, _on_boot_selected)
        self.patch_boot_button.Bind(wx.EVT_BUTTON, _on_patch_boot)
        self.delete_boot_button.Bind(wx.EVT_BUTTON, _on_delete_boot)
        self.live_boot_button.Bind(wx.EVT_BUTTON, _on_live_boot)
        self.process_firmware.Bind(wx.EVT_BUTTON, _on_process_firmware)
        self.process_rom.Bind(wx.EVT_BUTTON, _on_process_rom)
        self.show_all_boot_checkBox.Bind(wx.EVT_CHECKBOX, _on_show_all_boot)
        self.paste_boot.Bind(wx.EVT_BUTTON, _on_paste_boot)

        # Update UI
        self.Layout()


# ============================================================================
#                               Class MySplashScreen
# ============================================================================
class MySplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        wx.adv.SplashScreen.__init__(self, images.Splash.GetBitmap(), wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 20000, None, -1, wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.__fc = wx.CallLater(1000, self._show_main)

    def _on_close(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.__fc.IsRunning():
            self.__fc.Stop()
            self._show_main()

    def _show_main(self):
        frame = PixelFlasher(None, "PixelFlasher")
        frame.Show()
        try:
            self.Hide()
        except:
            pass
        if self.__fc.IsRunning():
            self.Raise()


# ============================================================================
#                               Class App
# ============================================================================
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        # see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
        self.ResetLocale()
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("PixelFlasher")

        if inspector:
            frame = PixelFlasher(None, "PixelFlasher")
            # frame.SetClientSize(frame.FromDIP(wx.Size(WIDTH, HEIGHT)))
            # frame.SetClientSize(wx.Size(WIDTH, HEIGHT))
            frame.Show()
        else:
            # Create and show the splash screen.  It will then create and
            # show the main frame when it is time to do so.  Normally when
            # using a SplashScreen you would create it, show it and then
            # continue on with the application's initialization, finally
            # creating and showing the main application window(s).  In
            # this case we have nothing else to do so we'll delay showing
            # the main frame until later (see ShowMain above) so the users
            # can see the SplashScreen effect.
            #
            splash = MySplashScreen()
            splash.Show()
        return True


# ============================================================================
#                               Function Main
# ============================================================================
def main():
    app = App(False)
    if inspector:
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    __name__ = 'Main'
    main()

