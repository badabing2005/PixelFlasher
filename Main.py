#!/usr/bin/env python

import argparse
import contextlib
import ctypes
import json
import locale
import math
import ntpath
import os
import sys
import time
import traceback
import webbrowser
import threading
from datetime import datetime, timedelta
from urllib.parse import urlparse

import darkdetect
import wx
import wx.adv
import wx.lib.agw.aui as aui
import wx.lib.inspection
import wx.lib.mixins.inspection
from packaging.version import parse

import images as images
import cProfile, pstats

with contextlib.suppress(Exception):
    ctypes.windll.shcore.SetProcessDpiAwareness(True)

from advanced_settings import AdvancedSettings
from backup_manager import BackupManager
from wifi import Wireless
from config import Config
from constants import *
from magisk_downloads import MagiskDownloads
from magisk_modules import MagiskModules
from pif_manager import PifManager
from message_box_ex import MessageBoxEx
from modules import (adb_kill_server, auto_resize_boot_list,
                     check_platform_tools, flash_phone, live_flash_boot_phone,
                     patch_boot_img, populate_boot_list, process_file,
                     select_firmware, set_flash_button_state)
from package_manager import PackageManager
from partition_manager import PartitionManager
from phone import get_connected_devices
from runtime import *

# see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
locale.setlocale(locale.LC_ALL, 'C')

# For troubleshooting, set inspector = True
inspector = False
dont_initialize = False
do_profiling = False

# Declare global_args at the global scope
global_args = None

# ============================================================================
#                               Class RedirectText
# ============================================================================
class RedirectText():
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl
        logfile = os.path.join(get_config_path(), 'logs', f"PixelFlasher_{datetime.now():%Y-%m-%d_%Hh%Mm%Ss}.log")
        self.logfile = open(logfile, "w", buffering=1, encoding="ISO-8859-1", errors="replace")
        set_logfile(logfile)

    def write(self,string):
        wx.CallAfter(self.out.AppendText, string)

        global global_args
        if hasattr(global_args, 'console') and global_args.console:
            # Print to console as well
            sys.__stdout__.write(string)

        if not self.logfile.closed:
            self.logfile.write(string)
            self.logfile.flush()

    # # noinspection PyMethodMayBeStatic
    # def flush(self):
    #     # noinspection PyStatementEffect
    #     None

    def flush(self):
        if not self.logfile.closed:
            self.logfile.flush()

    def close(self):
        if not self.logfile.closed:
            self.logfile.close()

# ============================================================================
#                               Class FilePickerComboBox
# ============================================================================
class FilePickerComboBox(wx.Panel):
    def __init__(self, parent, dialog_title="Select a file", wildcard="All files (*.*)|*.*"):
        super(FilePickerComboBox, self).__init__(parent)

        self.history_file = get_device_images_history_file_path()
        self.dialog_title = dialog_title
        self.wildcard = wildcard
        self.history = []

        self.combo_box = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.browse_button = wx.Button(self, wx.ID_ANY, 'Browse')

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.combo_box, 1, wx.EXPAND)
        sizer.Add(self.browse_button, 0, wx.EXPAND)
        self.SetSizer(sizer)

        self.browse_button.Bind(wx.EVT_BUTTON, self.on_browse)

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                    self.combo_box.SetItems(self.history)
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: encountered an exception during device_images_history_file loading.")
                print(f"Exception: {e}")
                print("Deleting the device_images_history_file to recover ...")
                os.remove(self.history_file)

    def on_browse(self, event):
        file_dialog = wx.FileDialog(self, self.dialog_title, wildcard=self.wildcard)
        if file_dialog.ShowModal() == wx.ID_OK:
            file_path = file_dialog.GetPath()
            if file_path not in self.history:
                self.history.insert(0, file_path)
                self.combo_box.Insert(file_path, 0)
                if len(self.history) > 16:
                    self.history.pop()
                if self.combo_box.Count > 16:
                    self.combo_box.Delete(self.combo_box.Count - 1)
            self.combo_box.SetValue(file_path)
            wx.PostEvent(self.combo_box, wx.CommandEvent(wx.EVT_COMBOBOX.typeId, self.combo_box.GetId()))

    def SetPath(self, path):
        if path and path != '' and path not in self.history:
            self.history.insert(0, path)
            self.combo_box.Insert(path, 0)
            if len(self.history) > 16:
                self.history.pop()
            if self.combo_box.Count > 16:
                self.combo_box.Delete(self.combo_box.Count - 1)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        self.combo_box.SetValue(path)

    def on_combo_box_change(self, event):
        path = event.GetString()
        if path == '':
            path = self.combo_box.GetValue()
        if not os.path.exists(path):
            self.history.remove(path)
            self.combo_box.Delete(self.combo_box.FindString(path))
        if path in self.history:
            self.history.remove(path)
            self.history.insert(0, path)
            self.combo_box.Delete(self.combo_box.FindString(path))
            self.combo_box.Insert(path, 0)
            self.combo_box.SetValue(path)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)

    def Bind(self, event, handler):
        if event == wx.EVT_FILEPICKER_CHANGED:
            self.handler = handler
            self.combo_box.Bind(wx.EVT_COMBOBOX, self._on_combo_box_change)

    def _on_combo_box_change(self, event):
        self.handler(event)
        self.on_combo_box_change(event)

    def GetPath(self):
        return self.combo_box.GetStringSelection()

    def SetToolTip(self, tooltip_text):
        self.combo_box.SetToolTip(tooltip_text)

# ============================================================================
#                               Class DropDownButton
# ============================================================================
class DropDownButton(wx.BitmapButton):
    def __init__(self, parent, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW):
        super().__init__(parent, id, bitmap, pos, size, style)
        self.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.popup_menu = wx.Menu()

    def OnButtonClick(self, event):
        self.PopupMenu(self.popup_menu)

    def AddLink(self, label, url, icon=None):
        item = self.popup_menu.Append(wx.ID_ANY, label)
        if icon:
            item.SetBitmap(icon)
        self.Bind(wx.EVT_MENU, lambda event, url=url: self.OnLinkSelected(event, url), item)

    def OnLinkSelected(self, event, url):
        # Handle the selected link here
        print(f"Selected link: {url}")
        open_device_image_download_link(url)

# ============================================================================
#                               Class GoogleImagesBaseMenu
# ============================================================================
class GoogleImagesBaseMenu(wx.Menu):
    BASE_MENU_ID_START = 5000

    def __init__(self, parent):
        super(GoogleImagesBaseMenu, self).__init__()

        self.parent = parent
        self.load_data()
        self.current_menu_id = self.BASE_MENU_ID_START

    def generate_unique_id(self):
        unique_id = self.current_menu_id
        self.current_menu_id += 1
        return unique_id

    def reset_menu_id(self):
        self.current_menu_id = self.BASE_MENU_ID_START

    def bind_download_event(self, menu, url):
        if menu is None:
            print(f"Error: menu is None when adding menu item for {url}")
            return
        unique_id = self.generate_unique_id()
        # next line is for debugging
        # menu.SetItemLabel(f"{menu.GetItemLabel()} ({unique_id})")
        def on_download_handler(event):
            self.on_download(url, event, unique_id)

        menu_id = menu.GetId()
        self.parent.Bind(wx.EVT_MENU, on_download_handler, id=menu_id)

    def load_data(self):
        json_file_path = os.path.join(get_config_path(), "google_images.json").strip()
        if not os.path.exists(json_file_path) or self.is_data_update_required():
            get_google_images()
            self.parent.config.google_images_last_checked = int(datetime.now().timestamp())
        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                self.data = json.load(json_file)
        except FileNotFoundError:
            print("google_images.json file not found.")
            self.data = {}

    def is_data_update_required(self):
        last_checked = self.parent.config.google_images_last_checked
        update_frequency = self.parent.config.google_images_update_frequency
        # don't check for updates if it is set to -1
        if update_frequency == -1:
            return False
        if last_checked is None:
            return True
        current_time = int(datetime.now().timestamp())
        update_threshold = current_time - (update_frequency * 24 * 60 * 60)
        return last_checked < update_threshold

    def on_download(self, url, event=None, unique_id=any):
        # debug(f"Download triggered for URL: {url}, Menu ID: {unique_id}")
        def download_completed(destination_path):
            self.parent.toast("Download Successful", f"File downloaded successfully: {url} and saved to {destination_path}")
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Download Successful", f"File downloaded successfully: {url} and saved to {destination_path}")
            # self.parent.firmware_picker.SetPath(destination_path)
            # self.parent.update_firmware_selection(destination_path)

        filename = os.path.basename(url)
        dialog = wx.FileDialog(None, "Save File", defaultFile=filename, wildcard="All files (*.*)|*.*", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            destination_path = dialog.GetPath()
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Starting background download for: {url} to be saved to {destination_path}\nplease be patient ...")
            download_thread = threading.Thread(target=download_file, args=(url, destination_path), kwargs={"callback": lambda: download_completed(destination_path)})
            download_thread.start()

# ============================================================================
#                               Class GoogleImagesMenu
# ============================================================================
class GoogleImagesMenu(GoogleImagesBaseMenu):
    def __init__(self, parent):
        super(GoogleImagesMenu, self).__init__(parent)

        try:
            self.phones_menu = wx.Menu()
            self.watches_menu = wx.Menu()
            device = get_phone()
            device_hardware = None
            device_firmware_date = None
            download_available = False
            phone_icon = images.phone_green_24.GetBitmap()
            watch_icon = images.watch_green_24.GetBitmap()
            device_icon = images.star_green_24.GetBitmap()
            if hasattr(self.parent, 'firmware_button') and self.parent.firmware_button:
                self.parent.firmware_button.SetBitmap(images.open_link_24.GetBitmap())

            if device:
                device_hardware = device.hardware
                device_firmware_date = device.firmware_date

            for device_id, device_data in self.data.items():
                device_label = device_data['label']
                device_type = device_data['type']
                device_menu = wx.Menu()
                device_download_flag = False

                for download_type in ['ota', 'factory']:
                    download_menu = wx.Menu()

                    for download_entry in reversed(device_data[download_type]):
                        version = download_entry['version']
                        sha256 = download_entry['sha256']
                        menu_label = f"{version} ({device_label})"
                        menu_id = self.generate_unique_id()
                        download_menu_item = download_menu.Append(menu_id, menu_label, sha256)
                        if download_menu_item is None:
                            print(f"Failed to create menu item with id {menu_id}, label {menu_label}, and sha256 {sha256}")
                        else:
                            download_date = download_entry['date']
                            # Set the background color and the icon for the current device. (background color is not working)
                            if device_id == device_hardware and device_firmware_date and download_date and int(download_date) > int(device_firmware_date):
                                download_menu_item.SetBackgroundColour((100, 155, 139, 255))
                                download_menu_item.SetBitmap(images.download_24.GetBitmap())
                                device_download_flag = True
                                download_available = True
                                device_icon = images.download_24.GetBitmap()
                                if device_type == "phone":
                                    phone_icon = images.download_24.GetBitmap()
                                elif device_type == "watch":
                                    watch_icon = images.download_24.GetBitmap()

                            url = download_entry['url']
                            self.bind_download_event(download_menu_item, url)

                    download_type_menu_item = device_menu.AppendSubMenu(download_menu, download_type.capitalize())
                    if download_type == "ota":
                        download_type_menu_item.SetBitmap(images.cloud_24.GetBitmap())
                    elif download_type == "factory":
                        download_type_menu_item.SetBitmap(images.factory_24.GetBitmap())

                    if device_download_flag:
                        download_type_menu_item.SetBitmap(images.download_24.GetBitmap())

                if device_type == 'phone':
                    device_menu_item = self.phones_menu.AppendSubMenu(device_menu, f"{device_id} ({device_label})")
                    # Set the background color and the icon for the current device. (background color is not working)
                    if device_id == device_hardware:
                        device_menu_item.SetBitmap(device_icon)
                        device_menu_item.SetBackgroundColour((100, 155, 139, 255))
                elif device_type == 'watch':
                    device_menu_item = self.watches_menu.AppendSubMenu(device_menu, f"{device_id} ({device_label})")
                    # Set the background color and the icon for the current device. (background color is not working)
                    if device_id == device_hardware:
                        device_menu_item.SetBitmap(device_icon)
                        device_menu_item.SetBackgroundColour((100, 155, 139, 255))

            phone_menu_item = self.AppendSubMenu(self.phones_menu, "Phones")
            phone_menu_item.SetBitmap(phone_icon)
            watches_menu_item = self.AppendSubMenu(self.watches_menu, "Watches")
            watches_menu_item.SetBitmap(watch_icon)

            if download_available:
                self.parent.toast("Updates are available", f"There are updates available for your device.\nCheck Google Images menu.")
                if hasattr(self.parent, 'firmware_button') and self.parent.firmware_button:
                    self.parent.firmware_button.SetBitmap(images.open_link_red_24.GetBitmap())

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while building Google Images Menu.")
            traceback.print_exc()

# ============================================================================
#                               Class GoogleImagesPopupMenu
# ============================================================================
class GoogleImagesPopupMenu(GoogleImagesBaseMenu):
    def __init__(self, parent, device=None, date_filter=None):
        super(GoogleImagesPopupMenu, self).__init__(parent)

        try:
            if device in self.data:
                device_data = self.data[device]

                submenu_ota = wx.Menu()
                submenu_factory = wx.Menu()
                download_flag = False

                for download_entry in reversed(device_data['ota']):
                    if download_entry['date'] is not None and (not date_filter or (date_filter is not None and int(download_entry['date']) >= int(date_filter))):
                        version = download_entry['version']
                        menu_label = f"{version} (OTA)"
                        menu_id = wx.NewId()
                        menu_item = submenu_ota.Append(menu_id, menu_label)
                        self.parent.Bind(wx.EVT_MENU, lambda event, u=download_entry['url']: self.on_download(u), menu_item)
                        if int(download_entry['date']) != int(date_filter):
                            menu_item.SetBitmap(images.download_24.GetBitmap())
                            download_flag = True

                for download_entry in reversed(device_data['factory']):
                    if download_entry['date'] is not None and (not date_filter or (date_filter is not None and int(download_entry['date']) >= int(date_filter))):
                        version = download_entry['version']
                        menu_label = f"{version} (Factory)"
                        menu_id = wx.NewId()
                        menu_item = submenu_factory.Append(menu_id, menu_label)
                        self.parent.Bind(wx.EVT_MENU, lambda event, u=download_entry['url']: self.on_download(u), menu_item)
                        if int(download_entry['date']) != int(date_filter):
                            menu_item.SetBitmap(images.download_24.GetBitmap())
                            download_flag = True

            with contextlib.suppress(Exception):
                ota_menu_item = self.AppendSubMenu(submenu_ota, "OTA")
                factory_menu_item = self.AppendSubMenu(submenu_factory, "Factory")
                if download_flag:
                    ota_menu_item.SetBitmap(images.download_24.GetBitmap())
                    factory_menu_item.SetBitmap(images.download_24.GetBitmap())
                else:
                    ota_menu_item.SetBitmap(images.cloud_24.GetBitmap())
                    factory_menu_item.SetBitmap(images.factory_24.GetBitmap())

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while building Google Images Popup Menu.")
            traceback.print_exc()

# ============================================================================
#                               Class PixelFlasher
# ============================================================================
class PixelFlasher(wx.Frame):
    def __init__(self, parent, title):
        config_file = get_config_file_path()
        self.config = Config.load(config_file)
        self.init_complete = False
        self.wipe = False
        set_config(self.config)
        init_db()
        wx.Frame.__init__(self, parent, -1, title, size=(self.config.width, self.config.height),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.SYSTEM_MENU | wx.CLOSE_BOX)

        # Base first run size on resolution.
        if self.config.first_run:
            x = int((self.CharWidth * self.config.width) / 11)
            y = int((self.CharHeight * self.config.height) / 25)
            self.SetSize(x, y)

        self.toolbar_flags = self.get_toolbar_config()

        self.Center()
        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        redirect_text = RedirectText(self.console_ctrl)
        sys.stdout = redirect_text
        sys.stderr = redirect_text

        # self.Centre(wx.BOTH)
        if self.config.pos_x and self.config.pos_y:
            self.SetPosition((self.config.pos_x,self.config.pos_y))

        self.resizing = False
        if not dont_initialize:
            self.initialize()
        set_window_shown(True)
        self.Show(True)

    # -----------------------------------------------
    #                  initialize
    # -----------------------------------------------
    def initialize(self):
        if do_profiling:
            profiler = cProfile.Profile()
            profiler.enable()
        t = f":{datetime.now():%Y-%m-%d %H:%M:%S}"
        print(f"PixelFlasher {VERSION} started on {t}")
        puml(f"{t};\n")
        puml(f"#palegreen:PixelFlasher {VERSION} started;\n")
        start = time.time()

        print(f"Platform: {sys.platform}")
        puml(f"note left:Platform: {sys.platform}\n")
        # check timezone
        timezone_offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        print(f"System Timezone: {time.tzname} Offset: {timezone_offset / 60 / 60 * -1}")
        print(f"Configuration Folder Path: {get_config_path()}")
        print(f"Configuration File Path: {get_config_file_path()}")

        puml(":Loading Configuration;\n")
        puml(f"note left: {get_config_path()}\n")
        # load verbose settings
        if self.config.verbose:
            self.verbose_checkBox.SetValue(self.config.verbose)
            set_verbose(self.config.verbose)
        if self.config.first_run:
            print("First Run: No previous configuration file is found.")
        else:
            print(f"{json.dumps(self.config.data, indent=4, sort_keys=True)}")
            puml("note right\n")
            puml(f"{json.dumps(self.config.data, indent=4, sort_keys=True)}\n")
            puml("end note\n")

        # enable / disable advanced_options
        if self.config.advanced_options:
            self._advanced_options_hide(False)
        else:
            self._advanced_options_hide(True)

        # check codepage
        print(f"System Default Encoding: {sys.getdefaultencoding()}")
        print(f"File System Encoding:    {sys.getfilesystemencoding()}")
        get_code_page()

        # delete specified libraries from the bundle
        print(f"Bundle Directory: {get_bundle_dir()}")
        delete_bundled_library(self.config.delete_bundled_libs)

        # Get Available Memory
        free_memory, total_memory = get_free_memory()
        formatted_free_memory = format_memory_size(free_memory)
        formatted_total_memory = format_memory_size(total_memory)
        print(f"Available Free Memory: {formatted_free_memory} / {formatted_total_memory}")

        # Get available free disk on system drive
        print(f"Available Free Disk on system drive: {str(get_free_space())} GB")
        print(f"Available Free Disk on PixelFlasher data drive: {str(get_free_space(get_config_path()))} GB\n")

        # load android_versions into a dict.
        with contextlib.suppress(Exception):
            with open('android_versions.json', 'r', encoding='ISO-8859-1', errors="replace") as file:
                android_versions = json.load(file)
            set_android_versions(android_versions)

        # load android_devices into a dict.
        with contextlib.suppress(Exception):
            with open('android_devices.json', 'r', encoding='ISO-8859-1', errors="replace") as file:
                android_devices = json.load(file)
            set_android_devices(android_devices)

        # load Magisk Package Name
        set_magisk_package(self.config.magisk)

        # load the low_mem settings
        set_low_memory(self.config.low_mem)

        # load Linux Shell
        set_linux_shell(self.config.linux_shell)

        # load firmware_has_init_boot
        set_firmware_has_init_boot(self.config.firmware_has_init_boot)

        # load rom_has_init_boot
        set_rom_has_init_boot(self.config.rom_has_init_boot)

        # extract firmware info
        if self.config.firmware_path and os.path.exists(self.config.firmware_path):
            self.firmware_picker.SetPath(self.config.firmware_path)
            firmware = ntpath.basename(self.config.firmware_path)
            filename, extension = os.path.splitext(firmware)
            extension = extension.lower()
            firmware = filename.split("-")
            if len(firmware) == 1:
                set_firmware_model(None)
                set_firmware_id(filename)
            else:
                try:
                    set_firmware_model(firmware[0])
                    if firmware[1] == 'ota' or firmware[0] == 'crDroidAndroid':
                        set_firmware_id(f"{firmware[0]}-{firmware[1]}-{firmware[2]}")
                        self.config.firmware_is_ota = True
                    else:
                        set_firmware_id(f"{firmware[0]}-{firmware[1]}")
                except Exception as e:
                    set_firmware_model(None)
                    set_firmware_id(filename)
            set_ota(self, self.config.firmware_is_ota)
            if self.config.check_for_firmware_hash_validity:
                if self.config.firmware_sha256:
                    print("Using previously stored firmware SHA-256 ...")
                    firmware_hash = self.config.firmware_sha256
                else:
                    print("Computing firmware SHA-256 ...")
                    firmware_hash = sha256(self.config.firmware_path)
                    self.config.firmware_sha256 = firmware_hash
                print(f"Firmware SHA-256: {firmware_hash}")
                self.firmware_picker.SetToolTip(f"SHA-256: {firmware_hash}")
                # Check to see if the first 8 characters of the checksum is in the filename, Google published firmwares do have this.
                if firmware_hash[:8] in self.config.firmware_path:
                    print(f"Expected to match {firmware_hash[:8]} in the firmware filename and did. This is good!")
                    puml(f"#CDFFC8:Checksum matches portion of the firmware filename {self.config.firmware_path};\n")
                    # self.toast("Firmware SHA256", "SHA256 of the selected file matches the segment in the filename.")
                    set_firmware_hash_validity(True)
                else:
                    print(f"WARNING: Expected to match {firmware_hash[:8]} in the firmware filename but didn't, please double check to make sure the checksum is good.")
                    puml("#orange:Unable to match the checksum in the filename;\n")
                    self.toast("Firmware SHA256", "WARNING! SHA256 of the selected file does not match segments in the filename.\nPlease double check to make sure the checksum is good.")
                    set_firmware_hash_validity(False)

        # check platform tools
        res_sdk = check_platform_tools(self)
        if res_sdk != -1:
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
            if self.config.rom_sha256:
                rom_hash = self.config.rom_sha256
            else:
                rom_hash = sha256(self.config.custom_rom_path)
                self.config.rom_sha256 = rom_hash
            self.custom_rom.SetToolTip(f"SHA-256: {rom_hash}")

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
        self.no_reboot_checkBox.SetValue(self.config.no_reboot)
        self.wipe_checkBox.SetValue(self.wipe)

        # get the image choice and update UI
        set_image_mode(self.image_choice.Items[self.image_choice.GetSelection()])

        # set the state of flash button.
        set_flash_button_state(self)

        self._update_custom_flash_options()

        if res_sdk != -1:
            print("\nLoading Device list ...")
            puml(":Loading device list;\n", True)
            print("This could take a while, please be patient.\n")

            debug("Populate device list")
            connected_devices = get_connected_devices()
            print(f"Discovered {len(connected_devices)} device(s) connected.")
            self.device_choice.AppendItems(connected_devices)
            d_list_string = '\n'.join(connected_devices)
            puml(f"note right\n{d_list_string}\nend note\n")

            # select configured device
            debug("select configured device")
            self._select_configured_device()
            self._refresh_ui()

        # check version if we are running the latest
        l_version = check_latest_version()
        if self.config.update_check and parse(VERSION) < parse(l_version):
            print(f"\nA newer PixelFlasher v{l_version} can be downloaded from:")
            print("https://github.com/badabing2005/PixelFlasher/releases/latest")
            from About import AboutDlg
            about = AboutDlg(self)
            about.ShowModal()
            about.Destroy()
        end = time.time()
        print(f"Load time: {math.ceil(end - start)} seconds")

        # set the ui fonts
        self.set_ui_fonts()

        # update widgets
        self.update_widget_states()

        self.spinner.Hide()
        self.spinner_label.Hide()
        self.init_complete = True

        if do_profiling:
            profiler.disable()
            stats = pstats.Stats(profiler).sort_stats('tottime')  # 'tottime' for total time
            stats.print_stats()

    # -----------------------------------------------
    #           enable_disable_radio_buttons
    # -----------------------------------------------
    def enable_disable_radio_button(self, name, state, selected=False, just_select=False):
        radio_buttons = self.mode_sizer.GetChildren()
        if isinstance(name, str):
            for child in radio_buttons:
                radio_button = child.GetWindow()
                if radio_button and radio_button.GetName() == f"mode-{name}":
                    if not just_select:
                        radio_button.Enable(state)
                    if state and selected:
                        radio_button.SetValue(True)

    # -----------------------------------------------
    #                  set_ui_fonts
    # -----------------------------------------------
    def set_ui_fonts(self):
        if self.config.customize_font:
            font = wx.Font(self.config.pf_font_size, family=wx.DEFAULT, style=wx.NORMAL, weight=wx.NORMAL, underline=False, faceName=self.config.pf_font_face)

            # device list
            self.device_choice.SetFont(font)

            # boot img list
            self.list.SetFont(font)
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(font)))

            # console
            self.console_ctrl.SetFont(font)
        else:
            font = wx.Font(9, family=wx.DEFAULT, style=wx.NORMAL, weight=wx.NORMAL, underline=False, faceName='Segoe UI')

            # device list
            self.device_choice.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))

            # boot img list
            self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'),wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10))))
            if sys.platform == "win32":
                self.list.SetFont(font)
            else:
                self.list.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))

            # console
            self.console_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
            if darkdetect.isLight():
                self.console_ctrl.SetBackgroundColour(wx.WHITE)
                self.console_ctrl.SetForegroundColour(wx.BLUE)
                self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        self._refresh_ui()

    # -----------------------------------------------
    #                  _set_icons
    # -----------------------------------------------
    def _set_icons(self):
        self.SetIcon(images.Icon_dark_256.GetIcon())

    # -----------------------------------------------
    #                  _build_status_bar
    # -----------------------------------------------
    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = f"Welcome to PixelFlasher {VERSION}"
        self.statusBar.SetStatusText(status_text, 0)

    # -----------------------------------------------
    #                  _build_toolbar
    # -----------------------------------------------
    def _build_toolbar(self, flags, destroy=False):
        try:
            if destroy:
                self.tb.Destroy()

            tb = self.CreateToolBar(flags)
            # tb = MultiLineToolbar(self, flags)  # Use the custom MultiLineToolbar class
            self.tb = tb

            tsize = (64, 64)
            null_bmp = wx.BitmapBundle(wx.NullBitmap)
            tb.SetToolBitmapSize(tsize)

            # Install APK
            if self.config.toolbar['visible']['install_apk']:
                tb.AddTool(toolId=5, label="Install APK", bitmap=images.install_apk_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Install APK on the device", longHelp="Install APK on the device", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=5)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=5)

            # Package Manager
            if self.config.toolbar['visible']['package_manager']:
                tb.AddTool(toolId=8, label="App Manager", bitmap=images.packages_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Package Manager", longHelp="Manage Apps / Packages", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=8)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=8)

            # separator
            if self.config.toolbar['visible']['install_apk'] or self.config.toolbar['visible']['package_manager']:
                tb.AddSeparator()

            # Shell
            if self.config.toolbar['visible']['adb_shell']:
                tb.AddTool(toolId=10, label="ADB Shell", bitmap=images.shell_64.GetBitmap(), bmpDisabled=images.shell_64_disabled.GetBitmap(), kind=wx.ITEM_NORMAL, shortHelp="Open ADB shell to the device.", longHelp="Open adb shell to the device", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=10)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=10)

            # Scrcpy
            if self.config.toolbar['visible']['scrcpy']:
                tb.AddTool(toolId=15, label="Scrcpy", bitmap=images.scrcpy_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Launch Screen Copy", longHelp="Launch Screen Copy", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=15)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=15)

            # Device Info
            if self.config.toolbar['visible']['device_info']:
                tb.AddTool(toolId=20, label="Device Info", bitmap=images.about_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Dump Full Device Info", longHelp="Dump Full Device Info", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=20)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=20)

            # Check Verity / Verification
            # if self.config.toolbar['visible']['check_verity']:
            #     tb.AddTool(toolId=30, label="Verify", bitmap=images.shield_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Check Verity / Verification status", longHelp="Check Verity / Verification status", clientData=None)
            #     self.Bind(wx.EVT_TOOL, self.OnToolClick, id=30)
            #     self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=30)

            # Partition Manager
            if self.config.toolbar['visible']['partition_manager'] and self.config.advanced_options:
                tb.AddTool(toolId=40, label="Partitions", bitmap=images.partition_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Partition Manager", longHelp="Partition Manager", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=40)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=40)

            # separator
            if self.config.toolbar['visible']['adb_shell'] or self.config.toolbar['visible']['scrcpy'] or self.config.toolbar['visible']['device_info'] or self.config.toolbar['visible']['check_verity'] or (self.config.toolbar['visible']['partition_manager'] and self.config.advanced_options):
                tb.AddSeparator()

            # Switch Slot
            if self.config.toolbar['visible']['switch_slot'] and self.config.advanced_options:
                tb.AddTool(toolId=100, label="Switch Slot", bitmap=images.switch_slot_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Switch to the other Slot", longHelp="Switch to the other Slot", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=100)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=100)
                # separator
                tb.AddSeparator()

            # Reboot to System
            if self.config.toolbar['visible']['reboot_system']:
                tb.AddTool(toolId=110, label="System", bitmap=images.reboot_system_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to System", longHelp="Reboot to System", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=110)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=110)

            # Reboot to Bootloader
            if self.config.toolbar['visible']['reboot_bootloader']:
                tb.AddTool(toolId=120, label="Bootloader", bitmap=images.reboot_bootloader_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to Bootloader", longHelp="Reboot to Bootloader", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=120)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=120)

            # Reboot to fastbootd
            if self.config.toolbar['visible']['reboot_fastbootd']:
                tb.AddTool(toolId=125, label="fastbootd", bitmap=images.reboot_fastbootd_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to userspace fastboot (fastbootd)", longHelp="Reboot to userspace fastboot (fastbootd)", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=125)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=125)

            # Reboot to Recovery
            if self.config.toolbar['visible']['reboot_recovery'] and self.config.advanced_options:
                tb.AddTool(toolId=130, label="Recovery", bitmap=images.reboot_recovery_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to Recovery", longHelp="Reboot to Recovery", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=130)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=130)

            # Reboot to Safe Mode
            if self.config.toolbar['visible']['reboot_safe_mode'] and self.config.advanced_options:
                tb.AddTool(toolId=140, label="Safe Mode", bitmap=images.reboot_safe_mode_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to Safe Mode", longHelp="Reboot to Safe Mode", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=140)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=140)

            # Reboot to Download
            if self.config.toolbar['visible']['reboot_download'] and self.config.advanced_options:
                tb.AddTool(toolId=150, label="Download", bitmap=images.reboot_download_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to Download Mode", longHelp="Reboot to Download Mode", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=150)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=150)

            # Reboot to Sideload
            if self.config.toolbar['visible']['reboot_sideload'] and self.config.advanced_options:
                tb.AddTool(toolId=160, label="Sideload", bitmap=images.reboot_sideload_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Reboot to Sideload Mode", longHelp="Reboot to Sideload Mode", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=160)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=160)

            # separator
            if self.config.toolbar['visible']['reboot_system'] or self.config.toolbar['visible']['reboot_bootloader'] or (self.config.toolbar['visible']['reboot_recovery'] and self.config.advanced_options) or (self.config.toolbar['visible']['reboot_safe_mode'] and self.config.advanced_options) or (self.config.toolbar['visible']['reboot_download'] and self.config.advanced_options) or (self.config.toolbar['visible']['reboot_sideload'] and self.config.advanced_options) or (self.config.toolbar['visible']['reboot_fastbootd'] and self.config.advanced_options):
                tb.AddSeparator()

            # Manage Magisk Settings (json file knows this and magisk_modules)
            if self.config.toolbar['visible']['magisk_modules']:
                tb.AddTool(toolId=200, label="Magisk", bitmap=images.magisk_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Manage Magisk modules and settings", longHelp="Manage Magisk modules and settings", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=200)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=200)

            # Download and Install Magisk Manager
            if self.config.toolbar['visible']['install_magisk']:
                tb.AddTool(toolId=210, label="Install Magisk", bitmap=images.install_magisk_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Download and Install Magisk Manager", longHelp="Download and Install Magisk Manager", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=210)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=210)

            # Magisk Backup Manager
            if self.config.toolbar['visible']['magisk_backup_manager']:
                tb.AddTool(toolId=220, label="Magisk Backup", bitmap=images.backup_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Magisk Backup Manager", longHelp="Magisk Backup Manager", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=220)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=220)

            # Pif Manager
            if self.config.toolbar['visible']['pif_manager']:
                tb.AddTool(toolId=225, label="Pif Manager", bitmap=images.pif_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Pif Manager", longHelp="Pif Manager", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=225)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=225)

            # SOS, Disable Magisk Modules
            if self.config.toolbar['visible']['sos'] and self.config.advanced_options:
                tb.AddTool(toolId=230, label="SOS", bitmap=images.sos_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp=u"Disable Magisk Modules\nThis button issues the following command:\n    adb wait-for-device shell magisk --remove-modules\nThis helps for cases where device bootloops due to incompatible magisk modules(YMMV).", longHelp="SOS", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=230)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=230)

            # separator
            if self.config.toolbar['visible']['magisk_modules'] or self.config.toolbar['visible']['install_magisk'] or self.config.toolbar['visible']['magisk_backup_manager'] or self.config.toolbar['visible']['pif_manager'] or (self.config.toolbar['visible']['sos'] and self.config.advanced_options):
                tb.AddSeparator()

            # Lock Bootloader
            if self.config.toolbar['visible']['lock_bootloader'] and self.config.advanced_options:
                tb.AddTool(toolId=300, label="Lock", bitmap=images.lock_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Lock Bootloader", longHelp="Lock Bootloader", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=300)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=300)

            # UnLock Bootloader
            if self.config.toolbar['visible']['unlock_bootloader'] and self.config.advanced_options:
                tb.AddTool(toolId=310, label="UnLock", bitmap=images.unlock_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="UnLock Bootloader\nCaution will wipe data", longHelp="UnLock Bootloader", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=310)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=310)

            # separator
            if (self.config.toolbar['visible']['lock_bootloader'] or self.config.toolbar['visible']['unlock_bootloader']) and self.config.advanced_options:
                tb.AddSeparator()

            tb.AddStretchableSpace()

            if self.config.toolbar['visible']['configuration']:
            # Configuration
                tb.AddTool(toolId=900, label="Settings", bitmap=images.settings_64.GetBitmap(), bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Settings", longHelp="Configuration Settings", clientData=None)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=900)
                self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=900)

            # Create Support
            support_bmp = wx.ArtProvider.GetBitmapBundle(wx.ART_HELP, wx.ART_TOOLBAR, tsize)
            tb.AddTool(toolId=910, label="Support", bitmap=support_bmp, bmpDisabled=null_bmp, kind=wx.ITEM_NORMAL, shortHelp="Create Support file", longHelp="Create Support file", clientData=None)
            self.Bind(wx.EVT_TOOL, self.OnToolClick, id=910)
            self.Bind(wx.EVT_TOOL_RCLICKED, self.OnToolRClick, id=910)

            # tb.EnableTool(10, False)  # False means disabled
            # self.disable_all_toolbar_tools(tb)

            tb.SetToolSeparation(10)
            a = tb.GetMargins()
            # tb.SetMargins(80, 80)
            b = tb.GetMargins()
            tb.Realize()

        except Exception as e:
            print("Exception occurred while building the toolbar:", e)
            traceback.print_exc()


    # -----------------------------------------------
    #          disable_all_toolbar_tools
    # -----------------------------------------------
    def disable_all_toolbar_tools(self, tb):
        tools_count = tb.GetToolsCount()
        for i in range(tools_count):
            tool = tb.GetToolByPos(i)
            tb.EnableTool(tool.GetId(), False)

    # -----------------------------------------------
    #                  OnToolClick
    # -----------------------------------------------
    def OnToolClick(self, event):
        # print("tool %s clicked\n" % event.GetId())
        id = event.GetId()
        if id == 5:
            self._on_install_apk(event)
        elif id == 8:
            self._on_package_manager(event)
        elif id == 10:
            self._on_adb_shell(event)
        elif id == 15:
            self._on_scrcpy(event)
        elif id == 20:
            self._on_device_info(event)
        # elif id == 30:
        #     self._on_verity_check(event)
        elif id == 40:
            self._on_partition_manager(event)
        elif id == 100:
            self._on_switch_slot(event)
        elif id == 110:
            self._on_reboot_system(event)
        elif id == 120:
            self._on_reboot_bootloader(event)
        elif id == 125:
            self._on_reboot_fastbootd(event)
        elif id == 130:
            self._on_reboot_recovery(event)
        elif id == 140:
            self._on_reboot_safemode(event)
        elif id == 150:
            self._on_reboot_download(event)
        elif id == 160:
            self._on_reboot_sideload(event)
        elif id == 200:
            self._on_magisk(event)
        elif id == 210:
            self._on_magisk_install(event)
        elif id == 220:
            self._on_backup_manager(event)
        elif id == 225:
            self._on_pif_manager(event)
        elif id == 230:
            self._on_sos(event)
        elif id == 300:
            self._on_lock_bootloader(event)
        elif id == 310:
            self._on_unlock_bootloader(event)
        elif id == 900:
            self._on_advanced_config(event)
        elif id == 910:
            self._on_support_zip(event)
        else:
            print(f"UNKNOWN tool id: {id}")

    # -----------------------------------------------
    #                  OnToolRClick
    # -----------------------------------------------
    def OnToolRClick(self, event):
        # print("tool %s right-clicked\n" % event.GetId())
        return

    # -----------------------------------------------
    #                  _on_device_info
    # -----------------------------------------------
    def _on_device_info(self, event):
        try:
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                print(f"Device Info:\n------------\n{device.device_info}")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting device info")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_pif_info
    # -----------------------------------------------
    def _on_pif_info(self, event):
        try:
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                print(f"Current device's Print:\n------------\n{device.current_device_print}\n------------\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting current device print")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_props_as_json
    # -----------------------------------------------
    def _on_props_as_json(self, event):
        try:
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                print(f"Current device's properties as json :\n------------\n{device.current_device_props_as_json}\n------------\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting current device properties as json")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_verity_check
    # -----------------------------------------------
    # def _on_verity_check(self, event):
    #     try:
    #         if self.config.device:
    #             self._on_spin('start')
    #             with contextlib.suppress(Exception):
    #                 device = get_phone()
    #                 verity = device.get_verity_verification('verity')
    #                 if verity != -1:
    #                     print(f"\n{verity}")
    #                 verification = device.get_verity_verification('verification')
    #                 if verification != -1:
    #                     print(f"\n{verification}")
    #     except Exception as e:
    #         print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while checking verity")
    #         traceback.print_exc()
    #     self._on_spin('stop')

    # -----------------------------------------------
    #                  _build_menu_bar
    # -----------------------------------------------
    def _build_menu_bar(self):
        # create the main menu object
        self.menuBar = wx.MenuBar()

        # Create the File menu
        file_menu = wx.Menu()

        # Create the Device menu
        device_menu = wx.Menu()

       # Create the Toolbar menu
        tb_menu = wx.Menu()

        # Create the Help menu
        help_menu = wx.Menu()

        # File Menu Items
        # ---------------
        # Settings Menu
        config_item = file_menu.Append(wx.ID_ANY, "Settings", "Settings")
        config_item.SetBitmap(images.settings_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_advanced_config, config_item)
        # seperator
        file_menu.AppendSeparator()
        # Exit Menu
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_ANY, "E&xit\tCtrl-Q", "Exit PixelFlasher")
        exit_item.SetBitmap(images.exit_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)

        # Device Menu Items
        # ----------------
        # Install APK
        self.install_apk = device_menu.Append(wx.ID_ANY, "Install APK", "Install APK")
        self.install_apk.SetBitmap(images.install_apk_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_install_apk, self.install_apk)
        # Bulk Install APK
        self.bulk_install_apk = device_menu.Append(wx.ID_ANY, "Bulk Install APK", "Bulk Install APK")
        self.bulk_install_apk.SetBitmap(images.install_apk_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_bulk_install_apk, self.bulk_install_apk)
        # Package Manager
        self.package_manager = device_menu.Append(wx.ID_ANY, "Package Manager", "Package Manager")
        self.package_manager.SetBitmap(images.packages_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_package_manager, self.package_manager)
        # seperator
        device_menu.AppendSeparator()
        # ADB Shell Menu
        self.shell_menu_item = device_menu.Append(wx.ID_ANY, "ADB Shell", "Open adb shell to the device")
        self.shell_menu_item.SetBitmap(images.shell_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_adb_shell, self.shell_menu_item)
        # Scrcpy Menu
        self.scrcpy_menu_item = device_menu.Append(wx.ID_ANY, "Scrcpy", "Launch Screen Copy")
        self.scrcpy_menu_item.SetBitmap(images.scrcpy_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_scrcpy, self.scrcpy_menu_item)
        # Device Info Menu
        self.device_info_menu_item = device_menu.Append(wx.ID_ANY, "Device Info", "Dump Full Device Info")
        self.device_info_menu_item.SetBitmap(images.about_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_device_info, self.device_info_menu_item)
        # Get PIF Print Menu
        self.pif_info_menu_item = device_menu.Append(wx.ID_ANY, "Pif Print", "Get current device's Pif print (osm0sis fork v5 format)")
        self.pif_info_menu_item.SetBitmap(images.json_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_pif_info, self.pif_info_menu_item)
        # Get Props as json Menu
        self.props_as_json_menu_item = device_menu.Append(wx.ID_ANY, "Props as Json", "Get current device's properties in json format")
        self.props_as_json_menu_item.SetBitmap(images.json_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_props_as_json, self.props_as_json_menu_item)
        # Dump Screen XML Menu
        self.xml_view_menu_item = device_menu.Append(wx.ID_ANY, "Dump Screen XML", "Use uiautomator to dump the screen view in xml")
        self.xml_view_menu_item.SetBitmap(images.xml_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_xml_view, self.xml_view_menu_item)
        # Cancel OTA Update Menu
        self.cancel_ota_menu_item = device_menu.Append(wx.ID_ANY, "Cancel OTA Update", "Cancels and Resets OTA updates by Google (Not PixelFlasher)")
        self.cancel_ota_menu_item.SetBitmap(images.cancel_ota_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_cancel_ota, self.cancel_ota_menu_item)
        # # Verity / Verification Menu
        # self.verity_menu_item = device_menu.Append(wx.ID_ANY, "Verity / Verification Status", "Check Verity / Verification Status")
        # self.verity_menu_item.SetBitmap(images.shield_24.GetBitmap())
        # self.Bind(wx.EVT_MENU, self._on_verity_check, self.verity_menu_item)
        # Partitions Manager
        self.partitions_menu = device_menu.Append(wx.ID_ANY, "Partitions Manager", "Backup / Erase Partitions")
        self.partitions_menu.SetBitmap(images.partition_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_partition_manager, self.partitions_menu)
        # seperator
        device_menu.AppendSeparator()
        # Switch Slot
        self.switch_slot_menu = device_menu.Append(wx.ID_ANY, "Switch Slot", "Switch to the other slow")
        self.switch_slot_menu.SetBitmap(images.switch_slot_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_switch_slot, self.switch_slot_menu)
        # seperator
        device_menu.AppendSeparator()
        # Reboot Submenu
        reboot = wx.Menu()
        self.reboot_system_menu = reboot.Append(wx.ID_ANY, "System")
        self.reboot_bootloader_menu = reboot.Append(wx.ID_ANY, "Bootloader")
        self.reboot_fastbootd_menu = reboot.Append(wx.ID_ANY, "Fastbootd")
        self.reboot_recovery_menu = reboot.Append(wx.ID_ANY, "Recovery")
        self.reboot_safe_mode_menu = reboot.Append(wx.ID_ANY, "Safe Mode")
        self.reboot_download_menu = reboot.Append(wx.ID_ANY, "Download")
        self.reboot_sideload_menu = reboot.Append(wx.ID_ANY, "Sideload")
        self.reboot_system_menu.SetBitmap(images.reboot_System_24.GetBitmap())
        self.reboot_bootloader_menu.SetBitmap(images.reboot_bootloader_24.GetBitmap())
        self.reboot_fastbootd_menu.SetBitmap(images.reboot_fastbootd_24.GetBitmap())
        self.reboot_recovery_menu.SetBitmap(images.reboot_recovery_24.GetBitmap())
        self.reboot_safe_mode_menu.SetBitmap(images.reboot_safe_mode_24.GetBitmap())
        self.reboot_download_menu.SetBitmap(images.reboot_download_24.GetBitmap())
        self.reboot_sideload_menu.SetBitmap(images.reboot_sideload_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_reboot_system, self.reboot_system_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_bootloader, self.reboot_bootloader_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_fastbootd, self.reboot_fastbootd_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_recovery, self.reboot_recovery_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_safemode, self.reboot_safe_mode_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_download, self.reboot_download_menu)
        self.Bind(wx.EVT_MENU, self._on_reboot_sideload, self.reboot_sideload_menu)
        self.reboot_menu = device_menu.Append(wx.ID_ANY, 'Reboot', reboot)
        self.reboot_menu.SetBitmap(images.reboot_24.GetBitmap())
        # Push File Submenu
        push_file = wx.Menu()
        self.push_file_to_tmp_menu = push_file.Append(wx.ID_ANY, "/data/local/tmp/")
        self.push_file_to_download_menu = push_file.Append(wx.ID_ANY, "/sdcard/Download/")
        self.push_file_to_tmp_menu.SetBitmap(images.push_24.GetBitmap())
        self.push_file_to_download_menu.SetBitmap(images.push_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_push_to_tmp, self.push_file_to_tmp_menu)
        self.Bind(wx.EVT_MENU, self._on_push_to_download, self.push_file_to_download_menu)
        self.push_menu = device_menu.Append(wx.ID_ANY, 'Push file to', push_file)
        self.push_menu.SetBitmap(images.push_cart_24.GetBitmap())
        # seperator
        device_menu.AppendSeparator()
        # Magisk Settings
        self.magisk_menu = device_menu.Append(wx.ID_ANY, "Magisk", "Manage Magisk modules and settings")
        self.magisk_menu.SetBitmap(images.magisk_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_magisk, self.magisk_menu)
        # Install Magisk
        self.install_magisk_menu = device_menu.Append(wx.ID_ANY, "Install Magisk", "Download and Install Magisk")
        self.install_magisk_menu.SetBitmap(images.install_magisk_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_magisk_install, self.install_magisk_menu)
        # Magisk Backup Manager
        self.magisk_backup_manager_menu = device_menu.Append(wx.ID_ANY, "Magisk Backup Manager", "Manage Magisk Backups")
        self.magisk_backup_manager_menu.SetBitmap(images.backup_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_backup_manager, self.magisk_backup_manager_menu)
        # Pif Manager
        self.pif_manager_menu = device_menu.Append(wx.ID_ANY, "Pif Manager", "Pif Backups")
        self.pif_manager_menu.SetBitmap(images.pif_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_pif_manager, self.pif_manager_menu)
        # SOS
        self.sos_menu = device_menu.Append(wx.ID_ANY, "SOS", "Disable Magisk Modules")
        self.sos_menu.SetBitmap(images.sos_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_sos, self.sos_menu)
        # seperator
        device_menu.AppendSeparator()
        # Lock Bootloader
        self.bootloader_lock_menu = device_menu.Append(wx.ID_ANY, "Lock Bootloader", "Lock Bootloader")
        self.bootloader_lock_menu.SetBitmap(images.lock_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_lock_bootloader, self.bootloader_lock_menu)
        # Unlock Bootloader
        self.bootloader_unlock_menu = device_menu.Append(wx.ID_ANY, "Unlock Bootloader", "Unlock Bootloader (Will wipe data)")
        self.bootloader_unlock_menu.SetBitmap(images.unlock_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_unlock_bootloader, self.bootloader_unlock_menu)

        # Toolbar Menu Items
        # ------------------
        # Top
        tb_top_item = tb_menu.Append(21010, 'Top', 'Top', wx.ITEM_RADIO)
        tb_top_item.SetBitmap(images.top_24.GetBitmap())
        if self.config.toolbar and self.config.toolbar['tb_position'] == 'top':
            tb_top_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, tb_top_item)
        # Left
        tb_left_item = tb_menu.Append(21020, 'Left', 'Left', wx.ITEM_RADIO)
        tb_left_item.SetBitmap(images.left_24.GetBitmap())
        if self.config.toolbar and self.config.toolbar['tb_position'] == 'left':
            tb_left_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, tb_left_item)
        # Right
        tb_right_item = tb_menu.Append(21030, 'Right', 'Right', wx.ITEM_RADIO)
        tb_right_item.SetBitmap(images.right_24.GetBitmap())
        if self.config.toolbar and self.config.toolbar['tb_position'] == 'right':
            tb_right_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, tb_right_item)
        # Bottom
        tb_bottom_item = tb_menu.Append(21040, 'Bottom', 'Bottom', wx.ITEM_RADIO)
        tb_bottom_item.SetBitmap(images.bottom_24.GetBitmap())
        if self.config.toolbar and self.config.toolbar['tb_position'] == 'bottom':
            tb_bottom_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, tb_bottom_item)
        # separator
        tb_menu.AppendSeparator()
        # Checkboxes
        self.tb_show_text_item = tb_menu.Append(21100, "Show Button Text", "Show Button Text", wx.ITEM_CHECK)
        if self.config.toolbar and self.config.toolbar['tb_show_text']:
            self.tb_show_text_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, self.tb_show_text_item)
        self.tb_show_button_item = tb_menu.Append(21200, "Show Button Icon", "Show Button Icon", wx.ITEM_CHECK)
        if self.config.toolbar and self.config.toolbar['tb_show_icons']:
            self.tb_show_button_item.Check()
        self.Bind(wx.EVT_MENU, self._on_tb_update, self.tb_show_button_item)
        # separator
        # Show / Hide Buttons Menu
        tb_buttons_menu = wx.Menu()
        tb_buttons_menu.Append(5, "Install APK", "", wx.ITEM_CHECK).SetBitmap(images.install_apk_24.GetBitmap())
        tb_buttons_menu.Append(8, "Package Manager", "", wx.ITEM_CHECK).SetBitmap(images.packages_24.GetBitmap())
        tb_buttons_menu.Append(10, "ADB Shell", "", wx.ITEM_CHECK).SetBitmap(images.shell_24.GetBitmap())
        tb_buttons_menu.Append(15, "Scrcpy", "", wx.ITEM_CHECK).SetBitmap(images.scrcpy_24.GetBitmap())
        tb_buttons_menu.Append(20, "Device Info", "", wx.ITEM_CHECK).SetBitmap(images.about_24.GetBitmap())
        # tb_buttons_menu.Append(30, "Verity Verification Status", "", wx.ITEM_CHECK).SetBitmap(images.shield_24.GetBitmap())
        tb_buttons_menu.Append(40, "Partitions Manager", "", wx.ITEM_CHECK).SetBitmap(images.partition_24.GetBitmap())
        tb_buttons_menu.Append(100, "Switch Slot", "", wx.ITEM_CHECK).SetBitmap(images.switch_slot_24.GetBitmap())
        tb_buttons_menu.Append(110, "Reboot System", "", wx.ITEM_CHECK).SetBitmap(images.reboot_System_24.GetBitmap())
        tb_buttons_menu.Append(120, "Reboot Bootloader", "", wx.ITEM_CHECK).SetBitmap(images.reboot_bootloader_24.GetBitmap())
        tb_buttons_menu.Append(125, "Reboot Fastbootd", "", wx.ITEM_CHECK).SetBitmap(images.reboot_fastbootd_24.GetBitmap())
        tb_buttons_menu.Append(130, "Reboot Recovery", "", wx.ITEM_CHECK).SetBitmap(images.reboot_recovery_24.GetBitmap())
        tb_buttons_menu.Append(140, "Reboot Safe Mode", "", wx.ITEM_CHECK).SetBitmap(images.reboot_safe_mode_24.GetBitmap())
        tb_buttons_menu.Append(150, "Reboot Download", "", wx.ITEM_CHECK).SetBitmap(images.reboot_download_24.GetBitmap())
        tb_buttons_menu.Append(160, "Reboot Sideload", "", wx.ITEM_CHECK).SetBitmap(images.reboot_sideload_24.GetBitmap())
        tb_buttons_menu.Append(200, "Magisk", "", wx.ITEM_CHECK).SetBitmap(images.magisk_24.GetBitmap())
        tb_buttons_menu.Append(210, "Install Magisk", "", wx.ITEM_CHECK).SetBitmap(images.install_magisk_24.GetBitmap())
        tb_buttons_menu.Append(220, "Magisk Backup Manager", "", wx.ITEM_CHECK).SetBitmap(images.backup_24.GetBitmap())
        tb_buttons_menu.Append(225, "Pif Manager", "", wx.ITEM_CHECK).SetBitmap(images.pif_24.GetBitmap())
        tb_buttons_menu.Append(230, "SOS", "", wx.ITEM_CHECK).SetBitmap(images.sos_24.GetBitmap())
        tb_buttons_menu.Append(300, "Lock Bootloader", "", wx.ITEM_CHECK).SetBitmap(images.lock_24.GetBitmap())
        tb_buttons_menu.Append(310, "Unlock Bootloader", "", wx.ITEM_CHECK).SetBitmap(images.unlock_24.GetBitmap())
        tb_buttons_menu.Append(900, "Configuration", "", wx.ITEM_CHECK).SetBitmap(images.settings_24.GetBitmap())
        tb_buttons_menu.Bind(wx.EVT_MENU, self._on_button_menu)
        tb_menu.AppendSubMenu(tb_buttons_menu, "Show / Hide Buttons")

        # update tb_buttons_menu items based on config.
        tb_buttons_menu.Check(5, self.config.toolbar['visible']['install_apk'])
        tb_buttons_menu.Check(8, self.config.toolbar['visible']['package_manager'])
        tb_buttons_menu.Check(10, self.config.toolbar['visible']['adb_shell'])
        tb_buttons_menu.Check(15, self.config.toolbar['visible']['scrcpy'])
        tb_buttons_menu.Check(20, self.config.toolbar['visible']['device_info'])
        # tb_buttons_menu.Check(30, self.config.toolbar['visible']['check_verity'])
        tb_buttons_menu.Check(40, self.config.toolbar['visible']['partition_manager'])
        tb_buttons_menu.Check(100, self.config.toolbar['visible']['switch_slot'])
        tb_buttons_menu.Check(110, self.config.toolbar['visible']['reboot_system'])
        tb_buttons_menu.Check(120, self.config.toolbar['visible']['reboot_bootloader'])
        tb_buttons_menu.Check(125, self.config.toolbar['visible']['reboot_fastbootd'])
        tb_buttons_menu.Check(130, self.config.toolbar['visible']['reboot_recovery'])
        tb_buttons_menu.Check(140, self.config.toolbar['visible']['reboot_safe_mode'])
        tb_buttons_menu.Check(150, self.config.toolbar['visible']['reboot_download'])
        tb_buttons_menu.Check(160, self.config.toolbar['visible']['reboot_sideload'])
        tb_buttons_menu.Check(200, self.config.toolbar['visible']['magisk_modules'])
        tb_buttons_menu.Check(210, self.config.toolbar['visible']['install_magisk'])
        tb_buttons_menu.Check(220, self.config.toolbar['visible']['magisk_backup_manager'])
        tb_buttons_menu.Check(225, self.config.toolbar['visible']['pif_manager'])
        tb_buttons_menu.Check(230, self.config.toolbar['visible']['sos'])
        tb_buttons_menu.Check(300, self.config.toolbar['visible']['lock_bootloader'])
        tb_buttons_menu.Check(310, self.config.toolbar['visible']['unlock_bootloader'])
        tb_buttons_menu.Check(900, self.config.toolbar['visible']['configuration'])

        # Help Menu Items
        # ---------------
        # Report an issue
        self.issue_item = help_menu.Append(wx.ID_ANY, 'Report an Issue', 'Report an Issue')
        self.issue_item.SetBitmap(images.bug_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.issue_item)
        # # Feature Request
        self.feature_item = help_menu.Append(wx.ID_ANY, 'Feature Request', 'Feature Request')
        self.feature_item.SetBitmap(images.feature_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.feature_item)
        # # Project Home
        self.project_page_item = help_menu.Append(wx.ID_ANY, 'PixelFlasher Project Page', 'PixelFlasher Project Page')
        self.project_page_item.SetBitmap(images.github_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.project_page_item)
        # Community Forum
        self.forum_item = help_menu.Append(wx.ID_ANY, 'PixelFlasher Community (Forum)', 'PixelFlasher Community (Forum)')
        self.forum_item.SetBitmap(images.forum_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.forum_item)
        # seperator
        help_menu.AppendSeparator()
        # Links Submenu
        links = wx.Menu()
        self.linksMenuItem1 = links.Append(wx.ID_ANY, "Homeboy76\'s Guide")
        self.linksMenuItem2 = links.Append(wx.ID_ANY, "V0latyle\'s Guide")
        self.linksMenuItem3 = links.Append(wx.ID_ANY, "roirraW\'s Guide")
        links.AppendSeparator()
        self.linksMenuItem4 = links.Append(wx.ID_ANY, "osm0sis\'s PlayIntegrityFork")
        self.linksMenuItem5 = links.Append(wx.ID_ANY, "chiteroman\'s PlayIntegrityFix")
        self.linksMenuItem8 = links.Append(wx.ID_ANY, "TheFreeman193\'s Play Integrity Fix Props Collection")
        links.AppendSeparator()
        self.linksMenuItem6 = links.Append(wx.ID_ANY, "Get the Google USB Driver")
        self.linksMenuItem7 = links.Append(wx.ID_ANY, "Android Security Update Bulletins")
        links.AppendSeparator()
        self.linksMenuItem9 = links.Append(wx.ID_ANY, "Full OTA Images for Pixel Phones / Tablets")
        self.linksMenuItem10 = links.Append(wx.ID_ANY, "Factory Images for Pixel Phones / Tablets")
        self.linksMenuItem11 = links.Append(wx.ID_ANY, "Full OTA Images for Pixel Watches")
        self.linksMenuItem12 = links.Append(wx.ID_ANY, "Factory Images for Pixel Watches")
        links.AppendSeparator()
        self.linksMenuItem13 = links.Append(wx.ID_ANY, "Full OTA Images for Pixel Beta 14")
        self.linksMenuItem14 = links.Append(wx.ID_ANY, "Factory Images for Pixel Beta 14")
        self.linksMenuItem1.SetBitmap(images.guide_24.GetBitmap())
        self.linksMenuItem2.SetBitmap(images.guide_24.GetBitmap())
        self.linksMenuItem3.SetBitmap(images.guide_24.GetBitmap())
        self.linksMenuItem4.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem5.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem6.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem7.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem8.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem9.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem10.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem11.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem12.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem13.SetBitmap(images.open_link_24.GetBitmap())
        self.linksMenuItem14.SetBitmap(images.open_link_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem1)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem2)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem3)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem4)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem5)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem6)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem7)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem8)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem9)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem10)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem11)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem12)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem13)
        self.Bind(wx.EVT_MENU, self._on_link_clicked, self.linksMenuItem14)
        links_item = help_menu.Append(wx.ID_ANY, 'Links', links)
        links_item.SetBitmap(images.open_link_24.GetBitmap())
        # seperator
        help_menu.AppendSeparator()
        # Open configuration Folder
        config_folder_item = help_menu.Append(wx.ID_ANY, 'Open Configuration Folder', 'Open Configuration Folder')
        config_folder_item.SetBitmap(images.folder_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_open_config_folder, config_folder_item)
        if get_config_path() != get_sys_config_path():
            # Open pf_home
            pf_home_item = help_menu.Append(wx.ID_ANY, 'Open PixelFlasher Working Directory', 'Open PixelFlasher Working Directory')
            pf_home_item.SetBitmap(images.folder_24.GetBitmap())
            self.Bind(wx.EVT_MENU, self._on_open_pf_home, pf_home_item)
        # Create sanitized support.zip
        support_zip_item = help_menu.Append(wx.ID_ANY, 'Create a Sanitized support.zip', 'Create a Sanitized support.zip')
        support_zip_item.SetBitmap(images.support_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_support_zip, support_zip_item)
        # seperator
        help_menu.AppendSeparator()
        # update check
        update_item = help_menu.Append(wx.ID_ANY, 'Check for New Version', 'Check for New Version')
        update_item.SetBitmap(images.update_check_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_help_about, update_item)
        # seperator
        help_menu.AppendSeparator()
        # About
        about_item = help_menu.Append(wx.ID_ANY, '&About PixelFlasher', 'About')
        about_item.SetBitmap(images.about_24.GetBitmap())
        self.Bind(wx.EVT_MENU, self._on_help_about, about_item)

        # Add the File menu to the menu bar
        self.menuBar.Append(file_menu, "&File")
        # Add the Device menu to the menu bar
        self.menuBar.Append(device_menu, "&Device")
        # Create an instance of GoogleImagesMenu
        self.google_images_menu = GoogleImagesMenu(self)
        # Append GoogleImagesMenu to the menu bar
        self.menuBar.Append(self.google_images_menu, "Google Images")
        # Add the Toolbar menu to the menu bar
        self.menuBar.Append(tb_menu, "&Toolbar")
        # Add the Help menu to the menu bar
        self.menuBar.Append(help_menu, '&Help')
        # Add the Test menu to the menu bar
        if self.config.dev_mode:
            test_menu = wx.Menu()
            test1_item = test_menu.Append(wx.ID_ANY, "Test1", "Test1")
            self.Bind(wx.EVT_MENU, self.Test, test1_item)
            self.menuBar.Append(test_menu, '&Test')

        self.SetMenuBar(self.menuBar)

    # -----------------------------------------------
    #                  get_toolbar_flags
    # -----------------------------------------------
    def get_toolbar_config(self):
        # Read the configuration settings from self.config or use default values
        if not self.config:
            # Configuration is not available, use default values
            position = 'right'
            show_text = True
            show_icons = True
        else:
            # Configuration is available, use values from the config
            position = self.config.toolbar['tb_position']
            show_text = self.config.toolbar['tb_show_text']
            show_icons = self.config.toolbar['tb_show_icons']

        flag_pos = 0  # Initialize the position flags to 0
        if position == "top":
            flag_pos = wx.TB_HORIZONTAL | wx.TB_TOP
        elif position == "bottom":
            flag_pos = wx.TB_HORIZONTAL | wx.TB_BOTTOM
        elif position == "left":
            flag_pos = wx.TB_VERTICAL | wx.TB_LEFT
        elif position == "right":
            flag_pos = wx.TB_VERTICAL | wx.TB_RIGHT

        # Combine the flags using bitwise OR
        flags = flag_pos | wx.TB_FLAT | wx.TB_DOCKABLE

        # Check the configuration settings for text and icons
        if show_text:
            flags |= wx.TB_TEXT
        if not show_icons:
            flags |= wx.TB_NOICONS

        return flags

    # -----------------------------------------------
    #                  _on_button_menu
    # -----------------------------------------------
    def _on_button_menu(self, event):
        button_id = event.GetId()
        button_visible = event.IsChecked()
        # print(f"button_id: {button_id} checked: {button_visible}")
        # Handle the logic to show/hide the button in the toolbar based on the button_id and button_visible
        if button_id == 5:
            self.config.toolbar['visible']['install_apk'] = button_visible
        if button_id == 8:
            self.config.toolbar['visible']['package_manager'] = button_visible
        if button_id == 10:
            self.config.toolbar['visible']['adb_shell'] = button_visible
        if button_id == 15:
            self.config.toolbar['visible']['scrcpy'] = button_visible
        if button_id == 20:
            self.config.toolbar['visible']['device_info'] = button_visible
        # if button_id == 30:
        #     self.config.toolbar['visible']['check_verity'] = button_visible
        if button_id == 40:
            self.config.toolbar['visible']['partition_manager'] = button_visible
        if button_id == 100:
            self.config.toolbar['visible']['switch_slot'] = button_visible
        if button_id == 110:
            self.config.toolbar['visible']['reboot_system'] = button_visible
        if button_id == 120:
            self.config.toolbar['visible']['reboot_bootloader'] = button_visible
        if button_id == 125:
            self.config.toolbar['visible']['reboot_fastbootd'] = button_visible
        if button_id == 130:
            self.config.toolbar['visible']['reboot_recovery'] = button_visible
        if button_id == 140:
            self.config.toolbar['visible']['reboot_safe_mode'] = button_visible
        if button_id == 150:
            self.config.toolbar['visible']['reboot_download'] = button_visible
        if button_id == 160:
            self.config.toolbar['visible']['reboot_sideload'] = button_visible
        if button_id == 200:
            self.config.toolbar['visible']['magisk_modules'] = button_visible
        if button_id == 210:
            self.config.toolbar['visible']['install_magisk'] = button_visible
        if button_id == 220:
            self.config.toolbar['visible']['magisk_backup_manager'] = button_visible
        if button_id == 225:
            self.config.toolbar['visible']['pif_manager'] = button_visible
        if button_id == 230:
            self.config.toolbar['visible']['sos'] = button_visible
        if button_id == 300:
            self.config.toolbar['visible']['lock_bootloader'] = button_visible
        if button_id == 310:
            self.config.toolbar['visible']['unlock_bootloader'] = button_visible
        if button_id == 900:
            self.config.toolbar['visible']['configuration'] = button_visible

        self.toolbar_flags = self.get_toolbar_config()
        # Rebuild the toolbar with the updated flags
        self._build_toolbar(self.toolbar_flags, True)

    # -----------------------------------------------
    #                  _on_tb_update
    # -----------------------------------------------
    def _on_tb_update(self, event):
        clicked_item_id = event.GetId()
        # print(f"Clicked item ID: {clicked_item_id}")

        if clicked_item_id == 21010:
            self.config.toolbar['tb_position'] = 'top'
        elif clicked_item_id == 21020:
            self.config.toolbar['tb_position'] = 'left'
        elif clicked_item_id == 21030:
            self.config.toolbar['tb_position'] = 'right'
        elif clicked_item_id == 21040:
            self.config.toolbar['tb_position'] = 'bottom'
        elif clicked_item_id == 21100:
            # Button Text
            self.config.toolbar['tb_show_text'] = event.IsChecked()
            if not event.IsChecked():
                self.config.toolbar['tb_show_icons'] = True
                self.tb_show_button_item.Check(True)
        elif clicked_item_id == 21200:
            # Button icon
            self.config.toolbar['tb_show_icons'] = event.IsChecked()
            if not event.IsChecked():
                self.config.toolbar['tb_show_text'] = True
                self.tb_show_text_item.Check(True)

        self.toolbar_flags = self.get_toolbar_config()
        # Rebuild the toolbar with the updated flags
        self._build_toolbar(self.toolbar_flags, True)

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
        advanced_setting_dialog = AdvancedSettings(parent=self)
        advanced_setting_dialog.CentreOnParent(wx.BOTH)
        print("Entering Advanced Configuration ...")
        res = advanced_setting_dialog.ShowModal()
        advanced_setting_dialog.Destroy()
        if res == wx.ID_OK:
            # self.Freeze()
            # show / hide advanced settings
            self._advanced_options_hide(not self.config.advanced_options)
            populate_boot_list(self)
            set_flash_button_state(self)
            self.toolbar_flags = self.get_toolbar_config()
            # Rebuild the toolbar with the updated flags
            self._build_toolbar(self.toolbar_flags, True)
            self.update_widget_states()
            # self.Thaw()

    # -----------------------------------------------
    #                  _on_package_manager
    # -----------------------------------------------
    def _on_package_manager(self, event):
        # load labels if not already loaded
        if not get_labels() and os.path.exists(get_labels_file_path()):
            with open(get_labels_file_path(), "r", encoding='ISO-8859-1', errors="replace") as f:
                set_labels(json.load(f))
        self._on_spin('start')
        print("Launching Package Manager ...\n")
        try:
            dlg = PackageManager(self)
        except Exception:
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Closing Package Manager ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_install_apk
    # -----------------------------------------------
    def _on_install_apk(self, event):
        device = get_phone()
        if not device:
            print("ERROR: Please select a device before attempting APK Installation")
            self.toast("APK Install", "ERROR: Please select a device before attempting APK Installation.")
            return

        with wx.FileDialog(self, "Select APK file to install", '', '', wildcard="Android Applications (*.*.apk)|*.apk", style=wx.FD_OPEN) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            print(f"\nSelected {pathname} for installation.")
            try:
                dlg = wx.MessageDialog(None, "Do you want to set the ownership to Play Store Market?\nNote: Android auto apps require that they be installed from the Play Market.",'APK Installation',wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
            except Exception:
                traceback.print_exc()
                return
            result = dlg.ShowModal()
            try:
                self._on_spin('start')
                if result == wx.ID_YES:
                    puml("note right:Set ownership to Play Store;\n")
                    device.install_apk(pathname, fastboot_included=True, owner_playstore=True)
                elif result == wx.ID_NO:
                    device.install_apk(pathname, fastboot_included=True)
                else:
                    puml("note right:Cancelled APK installation;\n")
                    print("User cancelled apk installation.")
            except IOError:
                traceback.print_exc()
                wx.LogError(f"Cannot install file '{pathname}'.")
            self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_bulk_install_apk
    # -----------------------------------------------
    def _on_bulk_install_apk(self, event):
        try:
            with wx.DirDialog(self, "Select folder to bulk install APKs", style=wx.DD_DEFAULT_STYLE) as folderDialog:
                if folderDialog.ShowModal() == wx.ID_CANCEL:
                    print("User cancelled folder selection.")
                    return
                selected_folder = folderDialog.GetPath()

            self._on_spin('start')
            device = get_phone()
            if device:
                apk_files = [file for file in os.listdir(selected_folder) if file.endswith(".apk")]
                show_playstore_prompt = True
                for apk_file in apk_files:
                    if show_playstore_prompt:
                        dlg = wx.MessageDialog(None, "Do you want to set the ownership to Play Store Market?\nNote: This will apply to all the current bulk apks.\n(Android auto apps require that they be installed from the Play Market.)",'Set Play Market',wx.YES_NO | wx.ICON_EXCLAMATION)
                        result = dlg.ShowModal()
                        if result != wx.ID_YES:
                            owner_playstore = False
                        else:
                            owner_playstore = True
                        show_playstore_prompt = False
                    apk_path = os.path.join(selected_folder, apk_file)
                    res = device.install_apk(apk_path, fastboot_included=True, owner_playstore=owner_playstore)
                    if res.returncode != 0:
                        print(f"Return Code: {res.returncode}.")
                        print(f"Stdout: {res.stdout}")
                        print(f"Stderr: {res.stderr}")
                        print("Aborting ...\n")
                        self._on_spin('stop')
                        return res
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while installing APKs")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_move_end
    # -----------------------------------------------
    def _on_move_end(self, event):
        if self.resizing:
            # Perform the action only if resizing is complete
            self.resizing = False
            auto_resize_boot_list(self)
        event.Skip()

    # -----------------------------------------------
    #                  _on_close
    # -----------------------------------------------
    def _on_close(self, event):
        self.config.pos_x, self.config.pos_y = self.GetPosition()
        self.config.save(get_config_file_path())
        puml("#palegreen:Exit PixelFlasher;\nend\n@enduml\n")
        wx.Exit()

    # -----------------------------------------------
    #                  _on_resize
    # -----------------------------------------------
    def _on_resize(self, event):
        self.resizing = True
        self.config.width = self.Rect.Width
        self.config.height = self.Rect.Height

        self.Layout()
        event.Skip(True)

    # -----------------------------------------------
    #                  _on_link_clicked
    # -----------------------------------------------
    def _on_link_clicked(self, event):
        try:
            self._on_spin('start')
            clicked_id = event.GetId()

            # A dictionary mapping menu item IDs to tuples containing URL and link description
            link_info = {
                self.issue_item.GetId(): ('https://github.com/badabing2005/PixelFlasher/issues/new', "Report an Issue"),
                self.feature_item.GetId(): ('https://github.com/badabing2005/PixelFlasher/issues/new', "Feature Request"),
                self.project_page_item.GetId(): ('https://github.com/badabing2005/PixelFlasher', "PixelFlasher Project Page"),
                self.forum_item.GetId(): ('https://forum.xda-developers.com/t/pixelflasher-gui-tool-that-facilitates-flashing-updating-pixel-phones.4415453/', "PixelFlasher Community (Forum)"),
                self.linksMenuItem1.GetId(): ('https://xdaforums.com/t/guide-november-6-2023-root-pixel-8-pro-unlock-bootloader-pass-safetynet-both-slots-bootable-more.4638510/#post-89128833/', "Homeboy76's Guide"),
                self.linksMenuItem2.GetId(): ('https://forum.xda-developers.com/t/guide-root-pixel-6-oriole-with-magisk.4356233/', "V0latyle's Guide"),
                self.linksMenuItem3.GetId(): ('https://forum.xda-developers.com/t/december-5-2022-tq1a-221205-011-global-012-o2-uk-unlock-bootloader-root-pixel-7-pro-cheetah-safetynet.4502805/', "roirraW's Guide"),
                self.linksMenuItem4.GetId(): ('https://github.com/osm0sis/PlayIntegrityFork', "osm0sis's PlayIntegrityFork"),
                self.linksMenuItem5.GetId(): ('https://github.com/chiteroman/PlayIntegrityFix', "chiteroman's PlayIntegrityFix"),
                self.linksMenuItem6.GetId(): ('https://developer.android.com/studio/run/win-usb?authuser=1%2F', "Get the Google USB Driver"),
                self.linksMenuItem7.GetId(): ('https://source.android.com/docs/security/bulletin/', "Android Security Update Bulletins"),
                self.linksMenuItem8.GetId(): ('https://github.com/TheFreeman193/PIFS', "TheFreeman193's Play Integrity Fix Props Collection"),
                self.linksMenuItem9.GetId(): (FULL_OTA_IMAGES_FOR_PIXEL_DEVICES, "Full OTA Images for Pixel Phones, Tablets"),
                self.linksMenuItem10.GetId(): (FACTORY_IMAGES_FOR_PIXEL_DEVICES, "Factory Images for Pixel Phones, Tablets"),
                self.linksMenuItem11.GetId(): (FULL_OTA_IMAGES_FOR_WATCH_DEVICES, "Full OTA Images for Pixel Watches"),
                self.linksMenuItem12.GetId(): (FACTORY_IMAGES_FOR_WATCH_DEVICES, "Factory Images for Pixel Watches"),
                self.linksMenuItem13.GetId(): (FULL_OTA_IMAGES_FOR_BETA, "Full OTA Images for Pixel Beta 14"),
                self.linksMenuItem14.GetId(): (FACTORY_IMAGES_FOR_BETA, "Factory Images for Pixel Beta 14"),
            }

            if clicked_id in link_info:
                url, description = link_info[clicked_id]
                webbrowser.open_new(url)
                print(f"Open Link {description} {url}")
                puml(f":Open Link;\nnote right\n=== {description}\n[[{url}]]\nend note\n", True)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown menu item clicked")

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a link")
            traceback.print_exc()

        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_open_config_folder
    # -----------------------------------------------
    def _on_open_config_folder(self, event):
        try:
            self._on_spin('start')
            open_folder(self, get_sys_config_path())
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening configuration folder")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_open_pf_home
    # -----------------------------------------------
    def _on_open_pf_home(self, event):
        try:
            self._on_spin('start')
            open_folder(self, get_config_path())
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening PixelFlasher working directory")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_support_zip
    # -----------------------------------------------
    def _on_support_zip(self, event):
        timestr = time.strftime('%Y-%m-%d_%H-%M-%S')
        with wx.FileDialog(self, "Save support file", '', f"support_{timestr}.zip", wildcard="Support files (*.zip)|*.zip",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                config_path = get_config_path()
                support_zip = os.path.join(config_path, 'support.zip')
                self._on_spin('start')
                create_support_zip()
                debug(f"Saving support file to: {pathname}")
                with open(support_zip, "rb") as binaryfile :
                    with open(pathname, 'wb') as file:
                        byte_array = binaryfile.read()
                        file.write(byte_array)
                print(f"Saved support file to: {pathname}")
            except IOError:
                wx.LogError(f"Cannot save current data in file '{pathname}'.")
                traceback.print_exc()
            self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_exit_app
    # -----------------------------------------------
    def _on_exit_app(self, event):
        self.config.save(get_config_file_path())
        self.Close(True)

    # -----------------------------------------------
    #                  OnColClick
    # -----------------------------------------------
    def OnColClick(self, event):
        column = event.GetColumn() + 1
        current_sort_column = self.config.boot_sort_column

        # Determine the sort column and direction based on the clicked column
        if current_sort_column == column:
            # Same column clicked, toggle the sorting direction
            sorting_direction = 'DESC' if self.config.boot_sorting_direction == 'ASC' else 'ASC'
        else:
            # Different column clicked, default sorting direction is ASC
            sorting_direction = 'ASC'

        self.config.boot_sort_column = column
        self.config.boot_sorting_direction = sorting_direction

        populate_boot_list(self, sortColumn=column, sorting_direction=sorting_direction)

    # -----------------------------------------------
    #                  toast
    # -----------------------------------------------
    def toast(self, title, message):
        if self.config.show_notifications:
            notification = wx.adv.NotificationMessage(title, message, parent=None, flags=wx.ICON_INFORMATION)
            notification.SetIcon(images.Icon_dark_256.GetIcon())
            notification.Show()

    # -----------------------------------------------
    #                  _on_xml_view
    # -----------------------------------------------
    def _on_xml_view(self, event):
        self._on_spin('start')
        timestr = time.strftime('%Y-%m-%d_%H-%M-%S')
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Dump Screen Xml")
        with wx.FileDialog(self, "Dump Screen Xml", '', f"screen_dump_{timestr}.xml", wildcard="Screen Dump (*.xml)|*.xml",
                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            pathname = fileDialog.GetPath()
            device = get_phone()
            device.ui_action(f"/data/local/tmp/screen_dump_{timestr}.xml", pathname)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_cancel_ota
    # -----------------------------------------------
    def _on_cancel_ota(self, event):
        self._on_spin('start')
        timestr = time.strftime('%Y-%m-%d_%H-%M-%S')
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel OTA Update")
        device = get_phone()
        device.reset_ota_update()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  Test
    # -----------------------------------------------
    def Test(self, event):
        print("Entrering Test function (used during development only) ...")
        # device = get_phone()
        # device.dump_props()

    # -----------------------------------------------
    #                  _advanced_options_hide
    # -----------------------------------------------
    def _advanced_options_hide(self, value):
        self.Freeze()
        if value:
            # flash options
            self.flash_both_slots_checkBox.Hide()
            self.disable_verity_checkBox.Hide()
            self.disable_verification_checkBox.Hide()
            self.fastboot_force_checkBox.Hide()
            self.fastboot_verbose_checkBox.Hide()
            self.temporary_root_checkBox.Hide()
            self.wipe_checkBox.Hide()
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
            self.paste_selection.Hide()
            a = self.mode_radio_button.Name
            # if we're turning off advanced options, and the current mode is customFlash, change it to dryRun
            if self.mode_radio_button.Name == 'mode-customFlash' and self.mode_radio_button.GetValue():
                if get_ota():
                    self.enable_disable_radio_button('OTA', True, selected=True, just_select=True)
                    self.config.flash_mode = 'OTA'
                else:
                    #self.mode_radio_button.PreviousInGroup.SetValue(True)
                    self.enable_disable_radio_button('dryRun', True, selected=True, just_select=True)
                    self.config.flash_mode = 'dryRun'
        else:
            # flash options
            self.flash_both_slots_checkBox.Show()
            self.disable_verity_checkBox.Show()
            self.disable_verification_checkBox.Show()
            self.fastboot_force_checkBox.Show()
            self.fastboot_verbose_checkBox.Show()
            self.temporary_root_checkBox.Show()
            self.wipe_checkBox.Show()
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
            self.paste_selection.Show()
        self.Thaw()
        self._refresh_ui()

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        wx.YieldIfNeeded()
        if state == 'start':
            self.spinner.Show()
            self.spinner_label.Show()
            self.support_button.Hide()
            self.spinner.Start()
            self.spinner.Refresh()
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        else:
            self.spinner.Stop()
            self.spinner.Hide()
            self.spinner_label.Hide()
            self.support_button.Show()
            self.spinner.Refresh()
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

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
        self.Thaw()
        self.Refresh()

    # -----------------------------------------------
    #                  _print_device_details
    # -----------------------------------------------
    def _print_device_details(self, device):
        m_version = 0
        m_app_version = 0
        message = ''
        print('')
        message += f"Selected Device on {datetime.now():%Y-%m-%d %H:%M:%S}:\n"
        message += f"    Device ID:                       {device.id}\n"
        message += f"    Device Model:                    {device.hardware}\n"
        message += f"    Device Active Slot:              {device.active_slot}\n"
        message += f"    Device Mode:                     {device.true_mode}\n"
        with contextlib.suppress(Exception):
            android_devices = get_android_devices()
            android_device = android_devices[device.hardware]
            if android_device:
                message += f"    Device:                          {android_device['device']}\n"
                message += f"    Device Version End Date:         {android_device['android_version_end_date']}\n"
                message += f"    Device Secuity Update End Date:  {android_device['security_update_end_date']}\n"
        message += f"    Has init_boot partition:         {device.has_init_boot}\n"
        message += f"    Device Bootloader Version:       {device.get_prop('version-bootloader', 'ro.bootloader')}\n"
        if device.mode == 'adb':
            message += f"    Device is Rooted:                {device.rooted}\n"
            message += f"    Device Build:                    {device.build}\n"
            message += f"    Device API Level:                {device.api_level}\n"
            with contextlib.suppress(Exception):
                android_versions = get_android_versions()
                android_version = android_versions[device.api_level]
                message += f"    Android Version:                 {android_version['Version']}\n"
                message += f"    Android Name:                    {android_version['Name']}\n"
                message += f"    Android Codename:                {android_version['Codename']}\n"
                message += f"    Android Release Date:            {android_version['Release date']}\n"
                message += f"    Android Latest Update:           {android_version['Latest update']}\n"
            message += f"    Device Architecture:             {device.architecture}\n"
            message += f"    Device Kernel Version:           {device.get_prop('ro.kernel.version')}\n"
            message += f"    sys_oem_unlock_allowed:          {device.get_prop('sys.oem_unlock_allowed')}\n"
            message += f"    ro.boot.flash.locked:            {device.ro_boot_flash_locked}\n"
            message += f"    ro.boot.vbmeta.device_state:     {device.get_prop('ro.boot.vbmeta.device_state')}\n"
            # message += f"    vendor.boot.vbmeta.device_state: {device.get_prop('vendor.boot.vbmeta.device_state')}\n"
            message += f"    ro.product.first_api_level:      {device.get_prop('ro.product.first_api_level')}\n"
            # message += f"    ro.boot.warranty_bit:            {device.get_prop('ro.boot.warranty_bit')}\n"
            message += f"    ro.boot.veritymode:              {device.get_prop('ro.boot.veritymode')}\n"
            message += f"    ro.boot.verifiedbootstate:       {device.get_prop('ro.boot.verifiedbootstate')}\n"
            # message += f"    vendor.boot.verifiedbootstate:   {device.get_prop('vendor.boot.verifiedbootstate')}\n"
            # message += f"    ro.warranty_bit:                 {device.get_prop('ro.warranty_bit')}\n"
            message += f"    ro.secure:                       {device.get_prop('ro.secure')}\n"
            message += f"    ro.zygote:                       {device.get_prop('ro.zygote')}\n"
            message += f"    ro.vendor.product.cpu.abilist:   {device.get_prop('ro.vendor.product.cpu.abilist')}\n"
            message += f"    ro.vendor.product.cpu.abilist32: {device.get_prop('ro.vendor.product.cpu.abilist32')}\n"
            if device.rooted:
                message += self.get_vbmeta(device)
            m_app_version = device.magisk_app_version
            message += f"    Magisk Manager Version:          {m_app_version}\n"
            if m_app_version:
                message += f"    Magisk Path:                     {device.magisk_path}\n"
                message += f"        Checked for Package:         {self.config.magisk}\n"
        elif device.mode == 'f.b':
            message += f"    Device Unlocked:                 {device.unlocked}\n"
            if not device.unlocked:
                message += f"    Device Unlockable:               {device.unlock_ability}\n"
            message += f"    slot-retry-count:a:              {device.get_prop('slot-retry-count:a')}\n"
            message += f"    slot-unbootable:a:               {device.get_prop('slot-unbootable:a')}\n"
            message += f"    slot-successful:a:               {device.get_prop('slot-successful:a')}\n"
            message += f"    slot-retry-count:b:              {device.get_prop('slot-retry-count:b')}\n"
            message += f"    slot-unbootable:b:               {device.get_prop('slot-unbootable:b')}\n"
            message += f"    slot-successful:b:               {device.get_prop('slot-successful:b')}\n"
        if device.rooted:
            m_version = device.magisk_version
            message += f"    Magisk Version:                  {m_version}\n"
            message += f"    Magisk Config SHA1:              {device.magisk_sha1}\n"
            message += "    Magisk Modules:\n"
            message += f"{device.magisk_modules_summary}\n"
            message += f"{device.get_battery_details()}\n"
        else:
            print('')
        print(message)
        puml(f"note right\n{message}\nend note\n")
        self._check_for_bad_magisk(m_version, m_app_version)

    # -----------------------------------------------
    #                  get_vbmeta
    # -----------------------------------------------
    def get_vbmeta(self, device, message=''):
        try:
            if device.vbmeta is None:
                message += f"    vbmeta:                          UNKNOWN\n"
            elif device.vbmeta.type == 'none':
                message += f"    vbmeta:                          Not Present\n"
            else:
                alert = ''
                message += f"    vbmeta type:                     {device.vbmeta.type}\n"
                if device.vbmeta.type == 'ab':
                    message += f"    Slot A Verity:                   {enabled_disabled(device.vbmeta.verity_a)}\n"
                    message += f"    Slot A Verification:             {enabled_disabled(device.vbmeta.verification_a)}\n"
                    message += f"    Slot B Verity:                   {enabled_disabled(device.vbmeta.verity_b)}\n"
                    message += f"    Slot B Verification:             {enabled_disabled(device.vbmeta.verification_b)}\n"
                    if ( device.vbmeta.verity_a != device.vbmeta.verity_b ) or ( device.vbmeta.verification_a != device.vbmeta.verification_b ):
                        alert += "    WARNING! WARNING! WARNING!       Slot a verity / verification does not match slot b verity / verification"
                else:
                    message += f"    Verity:                          {enabled_disabled(device.vbmeta.verity_a)}\n"
                    message += f"    Verification:                    {enabled_disabled(device.vbmeta.verification_a)}\n"
                # self.config.disable_verification is a disable flag, which is the inverse of device.vbmeta.verification
                if ( device.vbmeta.verity_a == self.config.disable_verity ) or ( device.vbmeta.verity_b == self.config.disable_verity ):
                    alert += "    WARNING! WARNING! WARNING!       There is a mismatch of currently selected vbmeta verity state and device's verity state\n"
                if ( device.vbmeta.verification_a == self.config.disable_verification ) or ( device.vbmeta.verification_b == self.config.disable_verification ):
                    alert += "    WARNING! WARNING! WARNING!       There is a mismatch of currently selected vbmeta verification state and device's verification state\n"
                    alert += "                                     This has a device wipe implications, please double check.\n"
                message += alert
                if alert != '':
                    self.toast("vbmeta Warning!", alert)
            return message
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered while getting vbmeta data.")
            traceback.print_exc()

    # -----------------------------------------------
    #                  _check_for_bad_magisk
    # -----------------------------------------------
    def _check_for_bad_magisk(self, m_version, m_app_version):
            bad_m_version = False
            bad_m_app_version = False
            if m_version in KNOWN_BAD_MAGISKS:
                bad_m_version = True
                print(f"WARNING! Problematic Magisk Version:         {m_version} is installed. Advised not to use this version.")
            if m_app_version in KNOWN_BAD_MAGISKS:
                bad_m_app_version = True
                print(f"WARNING! Problematic Magisk Manager Version: {m_app_version} is installed. Advised not to use this version.")

            if bad_m_version and bad_m_app_version:
                dlg = wx.MessageDialog(None, f"Magisk Version: {m_version} is detected.\nMagisk Manager Version: {m_app_version} is detected.\n\nThese versions of Magisk are known to have issues.\nRecommendation: Install stable version or one that is known to be good.",'Problematic Magisk Versions.',wx.OK | wx.ICON_EXCLAMATION)
                puml(f"#red:Magisk Version: {m_version} is detected\nMagisk Manager Version: {m_app_version} is detected;\n")
                puml("note right:These versions of Magisk are known to have problems.")
                result = dlg.ShowModal()
            elif bad_m_version:
                dlg = wx.MessageDialog(None, f"Magisk Version: {m_version} is detected.\nThis version of Magisk is known to have issues.\nRecommendation: Install stable version or one that is known to be good.",'Problematic Magisk Version.',wx.OK | wx.ICON_EXCLAMATION)
                puml(f"#red:Magisk Version: {m_version} is detected;\n")
                puml("note right:This version of Magisk is known to have problems.")
                result = dlg.ShowModal()
            elif bad_m_app_version:
                dlg = wx.MessageDialog(None, f"Magisk Manager Version: {m_app_version} is detected.\nThis version of Magisk Manager is known to have issues.\nRecommendation: Install stable version or one that is known to be good.",'Problematic Magisk Manager Version.',wx.OK | wx.ICON_EXCLAMATION)
                puml(f"#red:Magisk Manager Version: {m_app_version} is detected;\n")
                puml("note right:This version of Magisk Manager is known to have problems;\n")
                result = dlg.ShowModal()

    # -----------------------------------------------
    #                  _update_custom_flash_options
    # -----------------------------------------------
    def _update_custom_flash_options(self):
        boot = get_boot()
        image_mode = get_image_mode()
        image_path = get_image_path()
        if self.config.flash_mode != 'customFlash':
            self.flash_radio_button.Enable(False)
            self.live_boot_radio_button.Enable(False)
            return
        self.live_boot_radio_button.Enable(False)
        self.flash_radio_button.Enable(False)
        self.flash_button.Enable(False)
        with contextlib.suppress(Exception):
            if image_path:
                filename, extension = os.path.splitext(image_path)
                extension = extension.lower()
                if image_mode == 'boot':
                    if extension == '.img':
                        self.live_boot_radio_button.Enable(True)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .img")
                elif image_mode in ['image', 'SIDELOAD']:
                    if extension == '.zip':
                        self.live_boot_radio_button.Enable(False)
                        self.flash_radio_button.Enable(True)
                        self.flash_button.Enable(True)
                        self.flash_radio_button.SetValue(True)
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .zip")
                elif extension == '.img':
                    self.live_boot_radio_button.Enable(False)
                    self.flash_radio_button.Enable(True)
                    self.flash_button.Enable(True)
                    self.flash_radio_button.SetValue(True)
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Selected file is not of type .img")

    # -----------------------------------------------
    #                  _select_configured_device
    # -----------------------------------------------
    def _select_configured_device(self):
        try:
            if self.config.device:
                count = 0
                for device in get_phones():
                    if device.id == self.config.device:
                        self.device_choice.Select(count)
                        set_phone_id(device.id)
                        puml(f":Select Device;\n", True)
                        self._print_device_details(device)
                        self.update_google_images_menu()
                    count += 1
            elif self.device_choice.StringSelection:
                device = self.device_choice.StringSelection
                # replace multiple spaces with a single space and then split on space
                id = ' '.join(device.split())
                id = id.split()
                id = id[2]
                self.config.device = id
                for device in get_phones():
                    if device.id == id:
                        set_phone_id(device.id)
                        puml(f":Select Device;\n", True)
                        self._print_device_details(device)
                        self.update_google_images_menu()
            else:
                set_phone_id(None)
                self.device_label.Label = "ADB Connected Devices"
            if self.device_choice.StringSelection == '':
                set_phone_id(None)
                self.device_label.Label = "ADB Connected Devices"
                self.config.device = None
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} No Device is selected!")
                puml(f":Select Device;\nnote right:No Device is selected!\n")
            self._reflect_slots()
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function _select_configured_device")
            traceback.print_exc()

    # -----------------------------------------------
    #                  refresh_device
    # -----------------------------------------------
    def refresh_device(self, look_for_device=None):
        print("Updating connected devices ...")
        if look_for_device:
            selected_device_id = look_for_device
        else:
            selected_device = self.device_choice.StringSelection
            selected_device_id = None
            if selected_device:
                # selected_device_id = selected_device.split()[2]
                selected_device_id = self.config.device
        self.device_choice.Clear()
        phones = get_phones()
        for device in phones:
            if device:
                device_details = device.get_device_details()
                self.device_choice.Append(device_details)
                if selected_device_id and device.id == selected_device_id:
                    self.device_choice.SetStringSelection(device_details)  # Select the matching device ID
                    self._select_configured_device()
        self._reflect_slots()
        self.update_widget_states()

    # -----------------------------------------------
    #                  _reflect_slots
    # -----------------------------------------------
    def _reflect_slots(self):
        device = get_phone()
        if device:
            if device.active_slot == 'a':
                self.device_label.Label = "ADB Connected Devices\nCurrent Active Slot: [A]"
                self.update_slot_image('a')
                set_a_only(False)
            elif device.active_slot == 'b':
                self.device_label.Label = "ADB Connected Devices\nCurrent Active Slot: [B]"
                set_a_only(False)
                self.update_slot_image('b')
            else:
                self.device_label.Label = "ADB Connected Devices"
                set_a_only(True)
                self.update_slot_image('none')
            self.update_rooted_image(device.rooted)
        else:
            self.device_label.Label = "ADB Connected Devices"
            self.update_slot_image('none')
            self.update_rooted_image(False)

    #-----------------------------------------------------------------------------
    #                          evaluate_condition
    #-----------------------------------------------------------------------------
    # Define the rules engine
    def evaluate_condition(self, condition):
        try:
            if condition == 'device_attached':
                device_id = get_phone_id()
                if device_id:
                    return True
                return False

            elif condition == 'device_mode_adb':
                device = get_phone()
                if device and device.mode == 'adb':
                    return True
                return False

            elif condition == 'device_is_rooted':
                device = get_phone()
                if device and device.rooted:
                    return True
                return False

            elif condition == 'mode_is_not_ota':
                if self.config.flash_mode != 'OTA':
                    return True
                return False

            elif condition == 'custom_flash':
                if self.config.flash_mode == 'customFlash':
                    return True
                return False

            elif condition == 'custom_rom':
                if self.config.custom_rom:
                    return True
                return False

            elif condition == 'custom_rom_selected':
                if self.config.custom_rom_path and os.path.exists(self.config.custom_rom_path):
                    return True
                return False

            elif condition == 'firmware_selected':
                if self.config.firmware_path and os.path.exists(self.config.firmware_path):
                    return True
                return False

            elif condition == 'not_custom_flash':
                if self.config.flash_mode != 'customFlash':
                    return True
                return False

            elif condition == 'dual_slot':
                device = get_phone()
                if device and device.active_slot in ['a', 'b']:
                    return True
                return False

            elif condition == 'slot_a':
                device = get_phone()
                if device and device.active_slot == 'a':
                    return True
                return False

            elif condition == 'slot_b':
                device = get_phone()
                if device and device.active_slot =='b':
                    return True
                return False

            elif condition == 'has_magisk_modules':
                device = get_phone()
                if device.magisk_modules_summary == '':
                    return False
                return True

            elif condition == 'boot_is_selected':
                boot = get_boot()
                if boot:
                    return True
                return False

            elif condition == 'valid_paste':
                image_mode = self.image_choice.Items[self.image_choice.GetSelection()]
                if image_mode in ['boot', 'init_boot']:
                    boot = get_boot()
                    if boot:
                        return True
                elif image_mode in ["vbmeta", "bootloader", "radio", "image"]:
                    return True
                return False

            elif condition == 'boot_is_patched':
                boot = get_boot()
                if boot and boot.is_patched == 1:
                    return True
                return False

            elif condition == 'boot_is_not_patched':
                boot = get_boot()
                if boot and boot.is_patched == 1:
                    return False
                return True

            elif condition == 'custom_image_selected':
                image_path = get_image_path()
                if image_path:
                    return True
                return False

            elif condition == 'custom_image_mode_is_boot':
                image_mode = get_image_mode()
                if image_mode == 'boot':
                    return True
                return False

            elif condition == 'firmware_is_ota':
                return get_ota()

            elif condition == 'firmware_is_not_ota':
                return not get_ota()

            elif condition == 'sdk_ok':
                return get_sdk_state()

            elif condition == 'no_rule':
                return True

            elif condition == 'scrcpy_path_is_set':
                if self.config.scrcpy['path'] != '' and os.path.exists(self.config.scrcpy['path']):
                    return True
                return False

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while evaluating a rule")
            traceback.print_exc()

    #-----------------------------------------------------------------------------
    #                                   update_widget_states
    #-----------------------------------------------------------------------------
    def update_widget_states(self):
        try:
            widget_conditions = {
                self.sos_menu:                          ['no_rule'],
                self.reboot_menu:                       ['device_attached'],
                self.reboot_recovery_menu:              ['device_attached'],
                self.reboot_bootloader_menu:            ['device_attached'],
                self.reboot_fastbootd_menu:             ['device_attached'],
                self.reboot_system_menu:                ['device_attached'],
                self.shell_menu_item:                   ['device_attached'],
                self.scrcpy_menu_item:                  ['device_attached', 'scrcpy_path_is_set'],
                self.device_info_menu_item:             ['device_attached'],
                self.pif_info_menu_item:                ['device_attached'],
                self.props_as_json_menu_item:           ['device_attached'],
                self.xml_view_menu_item:                ['device_attached'],
                self.cancel_ota_menu_item:              ['device_attached'],
                self.push_menu:                         ['device_attached'],
                self.push_file_to_tmp_menu:             ['device_attached'],
                self.push_file_to_download_menu:        ['device_attached'],
                self.bootloader_unlock_menu:            ['device_attached'],
                self.bootloader_lock_menu:              ['device_attached'],
                self.install_magisk_menu:               ['device_attached'],
                self.partitions_menu:                   ['device_attached'],
                self.install_apk:                       ['device_attached'],
                self.bulk_install_apk:                  ['device_attached'],
                self.package_manager:                   ['device_attached'],
                self.no_reboot_checkBox:                ['device_attached'],
                self.image_file_picker:                 ['custom_flash'],
                self.image_choice:                      ['custom_flash'],
                self.custom_rom:                        ['custom_rom'],
                self.scan_button:                       ['sdk_ok'],
                self.wifi_adb:                          ['sdk_ok'],
                self.device_choice:                     ['sdk_ok'],
                self.process_firmware:                  ['firmware_selected'],
                self.delete_boot_button:                ['boot_is_selected'],
                self.boot_folder_button:                ['boot_is_selected'],
                self.firmware_folder_button:            ['boot_is_selected'],
                self.live_boot_button:                  ['device_attached', 'boot_is_selected'],
                self.flash_boot_button:                 ['device_attached', 'boot_is_selected'],
                self.paste_selection:                   ['device_attached','custom_flash', 'valid_paste'],
                self.patch_custom_boot_button:          ['device_attached', 'device_mode_adb'],
                self.reboot_download_menu:              ['device_attached', 'device_mode_adb'],
                self.reboot_sideload_menu:              ['device_attached'],
                self.switch_slot_menu:                  ['device_attached', 'dual_slot'],
                self.process_rom:                       ['custom_rom', 'custom_rom_selected'],
                self.magisk_menu:                       ['device_attached', 'device_mode_adb'],
                self.magisk_backup_manager_menu:        ['device_attached', 'device_mode_adb', 'device_is_rooted'],
                self.pif_manager_menu:                  ['device_attached', 'device_mode_adb'],
                self.reboot_safe_mode_menu:             ['device_attached', 'device_mode_adb', 'device_is_rooted'],
                # self.verity_menu_item:                  ['device_attached', 'device_mode_adb', 'device_is_rooted'],
                self.disable_verity_checkBox:           ['device_attached'],
                self.disable_verification_checkBox:     ['device_attached'],
                self.flash_both_slots_checkBox:         ['device_attached', 'mode_is_not_ota', 'dual_slot'],
                self.flash_to_inactive_slot_checkBox:   ['device_attached', 'mode_is_not_ota', 'dual_slot'],
                self.fastboot_force_checkBox:           ['device_attached', 'mode_is_not_ota', 'dual_slot'],
                self.wipe_checkBox:                     ['device_attached', 'custom_flash'],
                self.temporary_root_checkBox:           ['not_custom_flash', 'boot_is_patched', 'boot_is_selected'],
                self.patch_boot_button:                 ['device_attached', 'device_mode_adb', 'boot_is_selected', 'boot_is_not_patched'],
                # Special handling of non-singular widgets
                'mode_radio_button.OTA':                ['firmware_selected', 'firmware_is_ota'],
                'mode_radio_button.keepData':           ['firmware_selected', 'firmware_is_not_ota'],
                'mode_radio_button.wipeData':           ['firmware_selected', 'firmware_is_not_ota'],
                'mode_radio_button.dryRun':             ['firmware_selected', 'firmware_is_not_ota'],
                # Toolbar tools handling by ID
                5:                                      ['device_attached'],                                            # Install APK
                8:                                      ['device_attached'],                                            # Package Manager
                10:                                     ['device_attached'],                                            # Shell
                15:                                     ['device_attached', 'scrcpy_path_is_set'],                      # Scrcpy
                20:                                     ['device_attached'],                                            # Device Info
                # 30:                                     ['device_attached', 'device_mode_adb', 'device_is_rooted'],     # Check Verity Verification
                40:                                     ['device_attached'],                                            # Partition Manager
                100:                                    ['device_attached', 'dual_slot'],                               # Switch Slot
                110:                                    ['device_attached'],                                            # Reboot System
                120:                                    ['device_attached'],                                            # Reboot Bootloader
                125:                                    ['device_attached'],                                            # Reboot Fastbootd
                130:                                    ['device_attached'],                                            # Reboot Recovery
                140:                                    ['device_attached', 'device_mode_adb', 'device_is_rooted'],     # Reboot Safe Mode
                150:                                    ['device_attached', 'device_mode_adb'],                         # Reboot Download
                160:                                    ['device_attached'],                                            # Reboot Sideload
                200:                                    ['device_attached', 'device_mode_adb'],                         # Magisk Modules
                210:                                    ['device_attached'],                                            # Magisk Install
                220:                                    ['device_attached', 'device_mode_adb', 'device_is_rooted'],     # Magisk Backup Manager
                225:                                    ['device_attached', 'device_mode_adb'],                         # Pif Manager
                230:                                    ['no_rule'],                                                    # SOS
                300:                                    ['device_attached'],                                            # Lock
                310:                                    ['device_attached'],                                            # Unock
            }

            for widget, conditions in widget_conditions.items():
                # Evaluate conditions for the widget using the rules engine
                enable_widget = all(self.evaluate_condition(condition) for condition in conditions)

                # Set the state of the widget
                if isinstance(widget, int):
                    # Check if the widget is a toolbar tool ID
                    tool_id = widget
                    enable_tool = all(self.evaluate_condition(condition) for condition in conditions)
                    self.tb.EnableTool(tool_id, enable_tool)
                elif isinstance(widget, str):
                    # Handle special case for Flash Mode Radio Button Widget
                    if widget.startswith('mode_radio_button'):
                        name = widget.split('.')[1]
                        self.enable_disable_radio_button(name, enable_widget)
                else:
                    # Handle normal widget objects
                    widget.Enable(enable_widget)

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while updating widgets.")
            traceback.print_exc()

    # -----------------------------------------------
    #                  _on_select_device
    # -----------------------------------------------
    def _on_select_device(self, event):
        try:
            self._on_spin('start')
            choice = event.GetEventObject()
            device = choice.GetString(choice.GetSelection())
            # replace multiple spaces with a single space and then split on space
            d_id = ' '.join(device.split())
            if d_id:
                d_id = d_id.split()
                d_id = d_id[2]
                self.config.device = d_id
                for device in get_phones():
                    wx.YieldIfNeeded()
                    if device.id == d_id:
                        set_phone_id(device.id)
                        self._print_device_details(device)
                        self.update_google_images_menu()
                self._reflect_slots()
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while selecting a device")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_scan
    # -----------------------------------------------
    def _on_scan(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Scan")
            print("==============================================================================")
            if get_adb():
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Scanning for Devices ...")
                puml(":Scan for Devices;\n")
                self._on_spin('start')
                connected_devices = get_connected_devices()
                self.device_choice.SetItems(connected_devices)
                d_list_string = '\n'.join(connected_devices)
                puml(f"note right\n{d_list_string}\nend note\n")
                if self.device_choice.Count == 0:
                    self.device_choice.SetSelection(-1)
                    print("No Devices found.")
                    puml(f"note right:No Devices are found\n")
                    self.toast("Scan", "No devices are found..")
                    self._on_spin('stop')
                    return
                print(f"{self.device_choice.Count} Device(s) are found.")
                self._select_configured_device()
                self._on_spin('stop')
                if self.device_choice.StringSelection == '':
                    # Popup the devices dropdown
                    self.device_choice.Popup()
                    self.toast("Scan", f"Select your device from the list of {self.device_choice.Count} found devices.")
            else:
                print("Please set Android Platform Tools Path first.")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while scanning")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_select_platform_tools
    # -----------------------------------------------
    def _on_select_platform_tools(self, event):
        try:
            self._on_spin('start')
            self.config.platform_tools_path = event.GetPath().replace("'", "")
            check_platform_tools(self)
            if get_sdk_version():
                self.platform_tools_label.SetLabel(f"Android Platform Tools\nVersion {get_sdk_version()}")
            else:
                self.platform_tools_label.SetLabel("Android Platform Tools")
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while selecting platform tools")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #            update_firmware_selection
    # -----------------------------------------------
    def update_firmware_selection(self, path):
        try:
            if not os.path.exists(path):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: file {path} does not exist")
                return -1
            self.config.firmware_path = path.replace("'", "")
            checksum = select_firmware(self)
            if len(checksum) == 64:
                self.config.firmware_sha256 = checksum
            else:
                self.config.firmware_sha256 = None
            self.firmware_picker.SetToolTip(f"SHA-256: {checksum}")
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while selecting firmware")
            traceback.print_exc()

    # -----------------------------------------------
    #                  _on_select_firmware
    # -----------------------------------------------
    def _on_select_firmware(self, event):
        # path = event.GetPath()
        path = self.firmware_picker.GetPath()
        if not path:
            # User cancelled the selecteion
            return
        self._on_spin('start')
        self.update_firmware_selection(path)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_process_firmware
    # -----------------------------------------------
    def _on_process_firmware(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Process firmware")
            print("==============================================================================")
            self._on_spin('start')
            if self.config.firmware_path:
                process_file(self, 'firmware')
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing firmware")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_process_rom
    # -----------------------------------------------
    def _on_process_rom(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Process ROM")
            print("==============================================================================")
            self._on_spin('start')
            if self.config.custom_rom_path:
                process_file(self, 'rom')
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing rom")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_image_choice
    # -----------------------------------------------
    def _on_image_choice(self, event):
        try:
            self._on_spin('start')
            choice = event.GetEventObject()
            set_image_mode(choice.GetString(choice.GetSelection()))
            self._update_custom_flash_options()
            self.update_widget_states()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while choosing an image")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_image_select
    # -----------------------------------------------
    def _on_image_select(self, event):
        try:
            self._on_spin('start')
            image_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(image_path)
            extension = extension.lower()
            if extension in ['.zip', '.img']:
                set_image_path(image_path)
                self._update_custom_flash_options()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Custom image file {image_path} is selected.")
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {image_path} is not img or zip file.")
                self.image_file_picker.SetPath('')
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while selecting an image")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_select_custom_rom
    # -----------------------------------------------
    def _on_select_custom_rom(self, event):
        try:
            self._on_spin('start')
            custom_rom_path = event.GetPath().replace("'", "")
            filename, extension = os.path.splitext(custom_rom_path)
            extension = extension.lower()
            puml(":Select ROM File;\n", True)
            if extension in ['.zip', '.tgz', '.tar']:
                self.config.custom_rom_path = custom_rom_path
                rom_file = ntpath.basename(custom_rom_path)
                set_custom_rom_id(os.path.splitext(rom_file)[0])
                rom_hash = sha256(self.config.custom_rom_path)

                if len(rom_hash) == 64:
                    self.config.rom_sha256 = rom_hash
                else:
                    self.config.rom_sha256 = None
                self.custom_rom.SetToolTip(f"SHA-256: {rom_hash}")
                print(f"Selected ROM {rom_file} SHA-256: {rom_hash}")
                puml(f"note right\n{rom_file}\nSHA-256: {rom_hash}\nend note\n")
                populate_boot_list(self)
                self.update_widget_states()
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {custom_rom_path} is not a valid archive.")
                puml("#red:The selected ROM file is not valid;\n")
                self.custom_rom.SetPath('')
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while selecting rom")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_mode_changed
    # -----------------------------------------------
    def _on_mode_changed(self, event):
        self.mode_radio_button = event.GetEventObject()
        self.wipe = False
        self.wipe_checkBox.SetValue(False)
        if self.mode_radio_button.GetValue():
            self.config.flash_mode = self.mode_radio_button.mode
            print(f"Flash mode changed to: {self.config.flash_mode}")
            puml(f":Flash mode change;\n", True)
            puml(f"note right:{self.config.flash_mode}\n")
            self.update_widget_states()
        if self.config.flash_mode != 'customFlash':
            set_flash_button_state(self)
        self._update_custom_flash_options()

    # -----------------------------------------------
    #                  _on_flash_both_slots
    # -----------------------------------------------
    def _on_flash_both_slots(self, event):
        self.flash_both_slots_checkBox = event.GetEventObject()
        status = self.flash_both_slots_checkBox.GetValue()
        print(f"Flash Option: Flash Both Slots {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Flash Both Slots {status}\n")
        self.config.flash_both_slots = status
        if status:
            self.config.flash_to_inactive_slot = not status
            self.flash_to_inactive_slot_checkBox.SetValue(not status)

    # -----------------------------------------------
    #                  _on_flash_to_inactive_slot
    # -----------------------------------------------
    def _on_flash_to_inactive_slot(self, event):
        self.flash_to_inactive_slot_checkBox = event.GetEventObject()
        status = self.flash_to_inactive_slot_checkBox.GetValue()
        print(f"Flash Option: Flash to Inactive Slot {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Flash to Inactive Slot {status}\n")
        self.config.flash_to_inactive_slot = status
        if status:
            self.config.flash_both_slots = not status
            self.flash_both_slots_checkBox.SetValue(not status)

    # -----------------------------------------------
    #                  _on_disable_verity
    # -----------------------------------------------
    def _on_disable_verity(self, event):
        self._on_spin('start')
        self.disable_verity_checkBox = event.GetEventObject()
        status = self.disable_verity_checkBox.GetValue()
        print(f"Flash Option: Disable Verity {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Disable Verity {status}\n")
        self.config.disable_verity = status
        self.vbmeta_alert(show_alert=False)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_disable_verification
    # -----------------------------------------------
    def _on_disable_verification(self, event):
        self._on_spin('start')
        self.disable_verification_checkBox = event.GetEventObject()
        status = self.disable_verification_checkBox.GetValue()
        print(f"Flash Option: Disable Verification {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Disable Verification {status}\n")
        self.config.disable_verification = status
        self.vbmeta_alert(show_alert=True)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  vbmeta_alert
    # -----------------------------------------------
    def vbmeta_alert(self, show_alert=False):
        device = get_phone()
        if self.init_complete:
            device.get_vbmeta_details()
        alert = self.get_vbmeta(device)
        if show_alert and "WARNING!" in alert:
            try:
                dlg = MessageBoxEx(parent=None, title="vbmeta issue.", message=f"Warning!\n{alert}", button_texts=["OK"], default_button=1)
                puml(f"note right\nDialog\n====\nWarning!\n{alert}\nend note\n")
                dlg.CentreOnParent(wx.BOTH)
                result = dlg.ShowModal()
                dlg.Destroy()
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                traceback.print_exc()
        print(alert)

    # -----------------------------------------------
    #                  _on_fastboot_force
    # -----------------------------------------------
    def _on_fastboot_force(self, event):
        self.fastboot_force_checkBox = event.GetEventObject()
        status = self.fastboot_force_checkBox.GetValue()
        print(f"Flash Option: Force {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Force {status}\n")
        self.config.fastboot_force = status

    # -----------------------------------------------
    #                  _on_fastboot_verbose
    # -----------------------------------------------
    def _on_fastboot_verbose(self, event):
        self.fastboot_verbose_checkBox = event.GetEventObject()
        status = self.fastboot_verbose_checkBox.GetValue()
        print(f"Flash Option: Verbose {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Verbose {status}\n")
        self.config.fastboot_verbose = status

    # -----------------------------------------------
    #                  _on_temporary_root
    # -----------------------------------------------
    def _on_temporary_root(self, event):
        self._on_temporary_root_checkBox = event.GetEventObject()
        status = self._on_temporary_root_checkBox.GetValue()
        print(f"Flash Option: Temporary Root {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Temporary Root {status}\n")
        self.config.temporary_root = status

    # -----------------------------------------------
    #                  _on_no_reboot
    # -----------------------------------------------
    def _on_no_reboot(self, event):
        self._on_no_reboot_checkBox = event.GetEventObject()
        status = self._on_no_reboot_checkBox.GetValue()
        print(f"Flash Option: No Reboot {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:No Reboot {status}\n")
        self.config.no_reboot = status

    # -----------------------------------------------
    #                  _on_wipe
    # -----------------------------------------------
    def _on_wipe(self, event):
        self._on_wipe_checkBox = event.GetEventObject()
        status = self._on_wipe_checkBox.GetValue()
        print(f"Flash Option: Wipe {status}")
        puml(":Flash Option change;\n", True)
        puml(f"note right:Wipe {status}\n")
        self.wipe = status

    # -----------------------------------------------
    #                  _on_verbose
    # -----------------------------------------------
    def _on_verbose(self, event):
        self.verbose_checkBox = event.GetEventObject()
        status = self.verbose_checkBox.GetValue()
        print(f"Console Verbose: {status}")
        puml(":Console Verbose;\n", True)
        puml(f"note right:{status}\n")
        self.config.verbose = status
        set_verbose(status)

    # -----------------------------------------------
    #                  _on_reboot_recovery
    # -----------------------------------------------
    def _on_reboot_recovery(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Recovery")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_recovery()
                    if res != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to recovery")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to recovery")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_reboot_download
    # -----------------------------------------------
    def _on_reboot_download(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Download")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_download()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to download")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to download")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_reboot_sideload
    # -----------------------------------------------
    def _on_reboot_sideload(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Sideload")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_sideload()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to sideload")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to sideload")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_reboot_safemode
    # -----------------------------------------------
    def _on_reboot_safemode(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Safe Mode")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_safemode()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to safe mode")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to safe mode")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  select_file_and_push
    # -----------------------------------------------
    def select_file_and_push(self, destination):
        try:
            with wx.FileDialog(self, "Select file to push", '', '', wildcard="All files (*.*)|*.*", style=wx.FD_OPEN) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    print("User cancelled file push.")
                    return
                selected_file = fileDialog.GetPath()

            self._on_spin('start')
            device = get_phone()
            if device:
                # push the file
                res = device.push_file(selected_file, destination, False)
                if res != 0:
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}")
                    print(f"Stderr: {res.stderr}")
                    print("Aborting ...\n")
                    self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
                    return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_push_to_tmp
    # -----------------------------------------------
    def _on_push_to_tmp(self, event):
        self.select_file_and_push('/data/local/tmp/')

    # -----------------------------------------------
    #                  _on_push_to_download
    # -----------------------------------------------
    def _on_push_to_download(self, event):
        self.select_file_and_push('/sdcard/Download')

    # -----------------------------------------------
    #                  _on_reboot_system
    # -----------------------------------------------
    def _on_reboot_system(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot System")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_system()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_reboot_bootloader
    # -----------------------------------------------
    def _on_reboot_bootloader(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Bootloader")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_bootloader(fastboot_included = True)
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_reboot_fastbootd
    # -----------------------------------------------
    def _on_reboot_fastbootd(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Reboot Fastbootd")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    res = device.reboot_fastboot()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to fastbootd")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to fatsbootd")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_lock_bootloader
    # -----------------------------------------------
    def _on_lock_bootloader(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Lock Bootloader")
        print("==============================================================================")
        if not self.config.device:
            return
        title = "Lock Bootloader"
        message = "         WARNING!!! WARNING!!! WARNING!!!\n\n"
        message += "NEVER, EVER LOCK THE BOOTLOADER WITHOUT REVERTING\n"
        message += "TO STOCK FIRMWARE OR YOUR PHONE WILL BE BRICKED!!!\n\n"
        message += "       THIS WILL WIPE YOUR DEVICE DATA!!!\n\n"
        message += "Do you want to continue to Lock the device bootloader?\n"
        message += "       Press OK to continue or CANCEL to abort.\n"
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        set_message_box_title(title)
        set_message_box_message(message)
        try:
            dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=['OK', 'CANCEL'], default_button=2)
        except Exception:
            traceback.print_exc()
            return
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()

        if result == 1:
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
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        set_message_box_title(title)
        set_message_box_message(message)
        dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=['OK', 'CANCEL'], default_button=2)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()

        if result == 1:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        else:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Aborting ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

        try:
            self._on_spin('start')
            device = get_phone()
            if device:
                res = device.lock_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while locking bootloader")
            # only reboot if no_reboot is not selected
            if not self.config.no_reboot:
                print("echo rebooting to system ...\n")
                if device:
                    res = device.reboot_system()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while locking bootloader")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_unlock_bootloader
    # -----------------------------------------------
    def _on_unlock_bootloader(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Unlock Bootloader")
        print("==============================================================================")
        if not self.config.device:
            return
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
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        set_message_box_title(title)
        set_message_box_message(message)
        dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=['OK', 'CANCEL'], default_button=2)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()

        if result == 1:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        else:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Aborting ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

        try:
            self._on_spin('start')
            device = get_phone()
            if device:
                res = device.unlock_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while unlocking bootloader")
            if not self.config.no_reboot:
                print("echo rebooting to system ...\n")
                if device:
                    res = device.reboot_system()
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while unlocking bootloader")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_sos
    # -----------------------------------------------
    def _on_sos(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated SOS")
        print("==============================================================================")
        if not self.config.device:
            return
        title = "Disable Magisk Modules"
        message = "WARNING!!! This is an experimental feature to attempt disabling magisk modules.\n\n"
        message += "You would only need to do this if your device is bootlooping due to\n"
        message += "incompatible magisk modules, this is not guaranteed to work in all cases (YMMV).\n"
        message += "\nNote: Pressing OK button will invoke a script that will wait forever to detect the device.\n"
        message += "If your device is not detected PixelFlasher will appear hung.\n"
        message += "In such cases, killing the adb process will resume to normalcy.\n\n"
        message += "                        Press OK to continue or CANCEL to abort.\n"
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {title}")
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        set_message_box_title(title)
        set_message_box_message(message)
        dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=['OK', 'CANCEL'], default_button=1)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()

        if result == 1:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        else:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Aborting ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

        self._on_spin('start')
        device = get_phone()
        device.disable_magisk_modules()
        time.sleep(5)
        self.device_choice.SetItems(get_connected_devices())
        self._select_configured_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_adb_shell
    # -----------------------------------------------
    def _on_adb_shell(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated ADB Shell")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                device.open_shell()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting adb shell")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_scrcpy
    # -----------------------------------------------
    def _on_scrcpy(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Scrcpy")
            print("==============================================================================")
            if self.config.device:
                self._on_spin('start')
                device = get_phone()
                if device:
                    device.scrcpy()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while launching scrcpy")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_magisk
    # -----------------------------------------------
    def _on_magisk(self, event):
        self._on_spin('start')
        try:
            dlg = MagiskModules(parent=self, config=self.config)
        except Exception:
            traceback.print_exc()
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Aborting Magisk Modules Management ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_pif_manager
    # -----------------------------------------------
    def _on_pif_manager(self, event):
        # load xiaomi if not already loaded
        if not get_xiaomi() and os.path.exists(get_xiaomi_file_path()):
            with open(get_xiaomi_file_path(), "r", encoding='ISO-8859-1', errors="replace") as f:
                set_xiaomi(json.load(f))
        # load favorite_pifs if not already loaded
        if not get_favorite_pifs() and os.path.exists(get_favorite_pifs_file_path()):
            with open(get_favorite_pifs_file_path(), "r", encoding='ISO-8859-1', errors="replace") as f:
                set_favorite_pifs(json.load(f))
        self._on_spin('start')
        print("Launching Pif Manager ...\n")

        try:
            dlg = PifManager(parent=self, config=self.config)
        except Exception:
            traceback.print_exc()
            self._on_spin('stop')
            return
        self._on_spin('stop')
        result = dlg.Show()

    # -----------------------------------------------
    #                  _on_magisk_install
    # -----------------------------------------------
    def _on_magisk_install(self, event):
        self._on_spin('start')
        try:
            dlg = MagiskDownloads(self)
        except Exception:
            traceback.print_exc()
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Aborting Magisk Installation ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_backup_manager
    # -----------------------------------------------
    def _on_backup_manager(self, event):
        # device = get_phone()
        # device.get_magisk_backups()
        self._on_spin('start')
        try:
            dlg = BackupManager(self)
        except Exception:
            traceback.print_exc()
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Closing Backup Manager ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_partition_manager
    # -----------------------------------------------
    def _on_partition_manager(self, event):
        self._on_spin('start')
        try:
            dlg = PartitionManager(self)
        except Exception:
            traceback.print_exc()
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print("Closing Partition Manager ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_switch_slot
    # -----------------------------------------------
    def _on_switch_slot(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Switch Slot")
            print("==============================================================================")
            if not self.config.device:
                return
            device = get_phone()
            self._on_spin('start')
            if device.active_slot not in ['a', 'b']:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown slot, is your device dual slot?")
                self._on_spin('stop')
                return
            print(f"User clicked on Switch Slot: Current Slot: [{device.active_slot}]")
            self.vbmeta_alert(show_alert=True)
            device.switch_slot()
            if device:
                res = device.switch_slot()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while switching slot")
            if not self.config.no_reboot and device:
                res = device.reboot_system()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to system")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while switching slot")
            traceback.print_exc()
        self.refresh_device()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _open_sdk_link
    # -----------------------------------------------
    def _open_sdk_link(self, event):
        try:
            self._on_spin('start')
            print("Launching browser for SDK download URL: https://developer.android.com/studio/releases/platform-tools.html")
            webbrowser.open_new('https://developer.android.com/studio/releases/platform-tools.html')
            puml(f":Open SDK Link;\nnote right\n=== Android Platform Tools\n[[https://developer.android.com/studio/releases/platform-tools.html]]\nend note\n", True)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening skd link")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_wifi_manager
    # -----------------------------------------------
    def _on_wifi_manager(self, event):
        self._on_spin('start')
        try:
            print("Opening Wireless Manager ...\n")
            dlg = Wireless(self)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while loading wifi screen.")
            traceback.print_exc()
            self._on_spin('stop')
            return
        dlg.CentreOnParent(wx.BOTH)
        self._on_spin('stop')
        result = dlg.ShowModal()
        if result != wx.ID_OK:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            print("Closing Wireless Manager ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()

    # -----------------------------------------------
    #                  _on_adb_kill_server
    # -----------------------------------------------
    def _on_adb_kill_server(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated ADB Kill")
            print("==============================================================================")
            dlg = wx.MessageDialog(None, "This will invoke the command adb kill-server.\nAre you sure want to continue?",'ADB Kill Server',wx.YES_NO | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled Killing ADB server.")
                return
            print("User pressed ok kill ADB server")
            puml(":Kill ADB Server;\n", True)
            self._on_spin('start')
            adb_kill_server(self)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while killing adb server")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_custom_rom
    # -----------------------------------------------
    def _on_custom_rom(self, event):
        self.custom_rom_checkbox = event.GetEventObject()
        status = self.custom_rom_checkbox.GetValue()
        self.config.custom_rom = status
        if status:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Enabled Custom ROM")
            puml(":Custom ROM: ON;\n", True)
        else:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Disabled Custom ROM")
            puml(":Custom ROM: OFF;\n", True)
        populate_boot_list(self)
        self.update_widget_states()

    # -----------------------------------------------
    #                  _on_show_all_boot
    # -----------------------------------------------
    def _on_show_all_boot(self, event):
        self.show_all_boot_checkBox = event.GetEventObject()
        status = self.show_all_boot_checkBox.GetValue()
        self.config.show_all_boot = status
        print("Show All Boot Images")
        puml(":Show all boot images;\n", True)
        populate_boot_list(self)

    # -----------------------------------------------
    #                  _on_boot_selected
    # -----------------------------------------------
    def _on_boot_selected(self, event):
        x,y = event.GetPosition()
        row,flags = self.list.HitTest((x,y))
        boot = None
        for i in range (0, self.list.ItemCount):
            # deselect all items
            self.list.Select(i, 0)
            item = self.list.GetItem(i)
            # reset colors
            if sys.platform == "win32":
                 item.SetTextColour(wx.BLACK)
            elif darkdetect.isDark():
                item.SetTextColour(wx.WHITE)
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
                    BOOT.patch_method,
                    BOOT.magisk_version,
                    BOOT.hardware,
                    BOOT.is_odin,
                    BOOT.epoch as boot_date,
                    PACKAGE.id as package_id,
                    PACKAGE.boot_hash as package_boot_hash,
                    PACKAGE.type as package_type,
                    PACKAGE.package_sig,
                    PACKAGE.file_path as package_path,
                    PACKAGE.epoch as package_date,
                    BOOT.is_stock_boot,
                    BOOT.is_init_boot,
                    BOOT.patch_source_sha1
                FROM BOOT
                JOIN PACKAGE_BOOT
                    ON BOOT.id = PACKAGE_BOOT.boot_id
                    AND BOOT.boot_hash LIKE ?
                JOIN PACKAGE
                    ON PACKAGE.id = PACKAGE_BOOT.package_id;
            """
            with con:
                data = con.execute(sql, (query,))
                package_boot_count = 0
                for row in data:
                    boot.boot_id = row[0]
                    boot.boot_hash = row[1]
                    boot.boot_path = row[2]
                    boot.is_patched = row[3]
                    boot.patch_method = row[4]
                    boot.magisk_version = row[5]
                    boot.hardware = row[6]
                    boot.is_odin = row[7]
                    boot.boot_epoch = row[8]
                    boot.package_id = row[9]
                    boot.package_boot_hash = row[10]
                    boot.package_type = row[11]
                    boot.package_sig = row[12]
                    boot.package_path = row[13]
                    boot.package_epoch = row[14]
                    boot.is_stock_boot = row[15]
                    boot.is_init_boot = row[16]
                    boot.patch_source_sha1 = row[17]
                    package_boot_count += 1
            self.config.boot_id = boot.boot_id
            self.config.selected_boot_md5 = boot.boot_hash
            print("Selected Boot:")
            puml(":Select Boot;\n", True)
            message = f"    File:                  {os.path.basename(urlparse(boot.boot_path).path)}\n"
            message += f"    Path:                  {boot.boot_path}\n"
            message += f"    SHA1:                  {boot.boot_hash}\n"
            if boot.is_patched == 1:
                patched = True
                message += f"    Patched:               {patched}\n"
                if boot.patch_method:
                    message += f"    Patched Method:        {boot.patch_method}\n"
                if boot.patch_source_sha1:
                    message += f"    Patch Source SHA1:     {boot.patch_source_sha1}\n"
                message += f"    Patched With Magisk:   {boot.magisk_version}\n"
                message += f"    Patched on Device:     {boot.hardware}\n"
            else:
                patched = False
                message += f"    Patched:               {patched}\n"
            ts = datetime.fromtimestamp(boot.boot_epoch)
            if boot.is_odin == 1:
                message += f"    Samsung Boot:          True\n"
            if boot.is_stock_boot == 0:
                message += f"    Stock Boot:            False\n"
            elif boot.is_stock_boot == 1:
                message += f"    Stock Boot:            True\n"
            if boot.is_init_boot == 0:
                message += f"    Init Boot:             False\n"
            elif boot.is_init_boot == 1:
                message += f"    Init Boot:             True\n"
            message += f"    Date:                  {ts.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"    Firmware Fingerprint:  {boot.package_sig}\n"
            message += f"    Firmware:              {boot.package_path}\n"
            message += f"    Type:                  {boot.package_type}\n"
            if package_boot_count > 1:
                message += f"\nINFO: Multiple PACKAGE_BOOT records found for {boot.boot_hash}."
            print(f"{message}\n")
            puml(f"note right\n{message}\nend note\n")
        else:
            self.config.boot_id = None
            self.config.selected_boot_md5 = None
            if self.list.ItemCount == 0 :
                if self.config.firmware_path:
                    print("\nPlease Process the firmware!")
            else:
                print("\nPlease select a boot/init_boot!")
        set_boot(boot)
        set_flash_button_state(self)
        self._update_custom_flash_options()
        self.update_widget_states()

    # -----------------------------------------------
    #                  _on_delete_boot
    # -----------------------------------------------
    def _on_delete_boot(self, event):
        self._on_spin('start')
        boot = get_boot()
        if boot.boot_id and boot.package_id:
            print("Delete boot image button is pressed.")
            puml(":Delete boot image;\n", True)
            print(f"Deleting boot record,  ID:{boot.boot_id}  Boot_ID:{boot.boot_hash[:8]} ...")
            puml(f"note right\nID:{boot.boot_id}\nBoot_ID:{boot.boot_hash[:8]}\nend note\n")
            con = get_db()
            con.execute("PRAGMA foreign_keys = ON")
            con.commit()

            # Delete PACKAGE_BOOT record
            sql = """
                DELETE FROM PACKAGE_BOOT
                WHERE boot_id = ? AND package_id = ?;
            """
            try:
                with con:
                    data = con.execute(sql, (boot.boot_id, boot.package_id))
                con.commit()
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                puml("#red:Encountered an error;\n", True)
                traceback.print_exc()
                print("Aborting ...")
                set_boot(None)
                populate_boot_list(self)
                self._on_spin('stop')
                return

            # Check to see if this is the last entry for the boot_id, if it is,
            try:
                cursor = con.cursor()
                cursor.execute("SELECT * FROM PACKAGE_BOOT WHERE boot_id = ?", (boot.boot_id,))
                data = cursor.fetchall()
                if len(data) == 0:
                    # delete the boot from db
                    sql = """
                        DELETE FROM BOOT
                        WHERE id = ?;
                    """
                    try:
                        with con:
                            data = con.execute(sql, (boot.boot_id,))
                        con.commit()
                        print(f"Cleared db entry for BOOT: {boot.boot_id}")
                        # delete the boot file
                        print(f"Deleting Boot file: {boot.boot_path} ...")
                        if os.path.exists(boot.boot_path):
                            os.remove(boot.boot_path)
                            boot_dir = os.path.dirname(boot.boot_path)
                            # if deleting init_boot.img and boot.img exists, delete that as well
                            boot_img_path = os.path.join(boot_dir, 'boot.img')
                            if boot.is_init_boot and os.path.exists(boot_img_path):
                                print(f"Deleting {boot_img_path} ...")
                                os.remove(boot_img_path)
                        else:
                            print(f"Warning: Boot file: {boot.boot_path} does not exist")
                    except Exception as e:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                        puml("#red:Encountered an error;\n", True)
                        traceback.print_exc()
                        print("Aborting ...")
                        set_boot(None)
                        populate_boot_list(self)
                        self._on_spin('stop')
                        return
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                puml("#red:Encountered an error;\n", True)
                traceback.print_exc()
                print("Aborting ...")
                set_boot(None)
                populate_boot_list(self)
                self._on_spin('stop')
                return

            # Check to see if this is the last entry for the package_id, if it is,
            # delete the package from db and output a message that a firmware should be selected.
            # Also delete unpacked files from factory_images cache
            try:
                cursor = con.cursor()
                cursor.execute("SELECT * FROM PACKAGE_BOOT WHERE package_id = ?", (boot.package_id,))
                data = cursor.fetchall()
                if len(data) == 0:
                    delete_package = True
                    # see if there are magisk_patched* files in the directory
                    boot_dir = os.path.dirname(boot.boot_path)
                    files = get_filenames_in_dir(boot_dir)
                    for file in files:
                        # if magisk* exists, we shouldn't delete the package
                        if file.startswith('magisk_patched'):
                            delete_package = False
                            break
                    if delete_package:
                        sql = """
                            DELETE FROM PACKAGE
                            WHERE id = ?;
                        """
                        with con:
                            data = con.execute(sql, (boot.package_id,))
                        con.commit()
                        print(f"Cleared db entry for PACKAGE: {boot.package_path}")
                        config_path = get_config_path()
                        package_path = os.path.join(config_path, 'factory_images', boot.package_sig)
                        with contextlib.suppress(Exception):
                            print(f"Deleting Firmware cache for: {package_path} ...")
                            delete_all(package_path)
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                puml("#red:Encountered an error;\n", True)
                traceback.print_exc()
                print("Aborting ...")
                set_boot(None)
                populate_boot_list(self)
                self._on_spin('stop')
                return

            set_boot(None)
            populate_boot_list(self)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_boot_folder
    # -----------------------------------------------
    def _on_boot_folder(self, event):
        try:
            self._on_spin('start')
            boot = get_boot()
            if boot:
                open_folder(self, boot.boot_path, True)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening boot folder")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_firmware_folder
    # -----------------------------------------------
    def _on_firmware_folder(self, event):
        try:
            self._on_spin('start')
            boot = get_boot()
            if boot:
                config_path = get_config_path()
                working_dir = os.path.join(config_path, 'factory_images', boot.package_sig)
                open_folder(self, working_dir, False)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening firmware folder")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_live_boot
    # -----------------------------------------------
    def _on_live_boot(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Live boot")
            print("==============================================================================")
            self._on_spin('start')
            live_flash_boot_phone(self, 'Live')
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while live booting")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_flash_boot
    # -----------------------------------------------
    def _on_flash_boot(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Flash Boot")
            print("==============================================================================")
            self._on_spin('start')
            live_flash_boot_phone(self, 'Flash')
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while flashing boot")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_paste_selection
    # -----------------------------------------------
    def _on_paste_selection(self, event):
        config_path = get_config_path()
        factory_images = os.path.join(config_path, 'factory_images')
        package_sig = get_firmware_id()
        package_dir_full = os.path.join(factory_images, package_sig)
        image_mode = self.image_choice.Items[self.image_choice.GetSelection()]
        flag = True
        if image_mode in ['boot', 'init_boot']:
            boot = get_boot()
            if boot and boot.boot_path:
                pasted_filename = boot.boot_path
        elif image_mode == "vbmeta":
            pasted_filename = find_file_by_prefix(package_dir_full, "vbmeta.img")
        elif image_mode == "bootloader":
            pasted_filename = find_file_by_prefix(package_dir_full, "bootloader-")
        elif image_mode == "radio":
            pasted_filename = find_file_by_prefix(package_dir_full, "radio-")
        elif image_mode == "image":
            pasted_filename = find_file_by_prefix(package_dir_full, "image-")
        else:
            print("Nothing to paste!")
            flag = False
            return
        if flag and os.path.exists(pasted_filename):
            print(f"Pasted {pasted_filename} to custom flash")
            puml(f":Paste boot path;\nnote right:{pasted_filename};\n", True)
            self.image_file_picker.SetPath(pasted_filename)
            set_image_path(pasted_filename)
            self._update_custom_flash_options()
            set_flash_button_state(self)
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: file: {pasted_filename} Not Found.")

    # -----------------------------------------------
    #                  _on_patch_boot
    # -----------------------------------------------
    def _on_patch_boot(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Patch boot")
            print("==============================================================================")
            self._on_spin('start')
            patch_boot_img(self, False)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while patching boot")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_patch_custom_boot
    # -----------------------------------------------
    def _on_patch_custom_boot(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Custom Patch boot")
            print("==============================================================================")
            self._on_spin('start')
            patch_boot_img(self, True)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while patching custom boot")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_flash
    # -----------------------------------------------
    def _on_flash(self, event):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Flash Pixel Phone.")
            print("==============================================================================")
            self.spinner_label.Label = "Please be patient ...\n\nDuring this process:\n ! Do not touch the device\n ! Do not unplug your device"
            self._on_spin('start')
            self.flash_button.Enable(False)
            res = flash_phone(self)
            if res == -1:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} INFO: Flashing was aborted.")
                print("This could be user initiated or a problem encountered during flashing.")
                device = get_phone()
                if device:
                    mode = device.get_device_state()
                    print(f"Current device mode: {mode}")
                print("You might need to manually reboot your device.\n")
                self.refresh_device()
            self._on_spin('stop')
            self.flash_button.Enable(True)
            self.update_widget_states()
            self.spinner_label.Label = "Please be patient ..."
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while flashing")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_clear
    # -----------------------------------------------
    def _on_clear(self, event):
        self.console_ctrl.SetValue("")
        puml(":Clear Console Logs;\n", True)

    # -----------------------------------------------
    #                  update_slot_image
    # -----------------------------------------------
    def update_slot_image(self, slot):
        try:
            slot_image = self.slot_image.GetBitmap()
            slot_image_height = 0
            rooted_image = self.rooted_image.GetBitmap()
            rooted_image_height = 0
            if slot == "a":
                self.slot_image.SetBitmap(images.slot_a_48.GetBitmap())
            elif slot == "b":
                self.slot_image.SetBitmap(images.slot_b_48.GetBitmap())
            else:
                self.slot_image.SetBitmap(wx.NullBitmap)  # Set the bitmap to None
            with contextlib.suppress(Exception):
                slot_image_height = slot_image.GetHeight()
            with contextlib.suppress(Exception):
                rooted_image_height = rooted_image.GetHeight()
            # only refresh UI if the current slot height and current rooted height are 0 and we need to change the image to 64 pixels
            if slot_image_height == 0 and rooted_image_height == 0 and slot !=  'none':
                self._refresh_ui()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while updating slot image")
            traceback.print_exc()

    # -----------------------------------------------
    #                  update_rooted_image
    # -----------------------------------------------
    def update_rooted_image(self, is_rooted=False):
        try:
            rooted_image = self.rooted_image.GetBitmap()
            rooted_image_height = 0
            slot_image = self.slot_image.GetBitmap()
            slot_image_height = 0
            if is_rooted:
                self.rooted_image.SetBitmap(images.rooted.GetBitmap())
            else:
                self.rooted_image.SetBitmap(wx.NullBitmap)  # Set the bitmap to None
            with contextlib.suppress(Exception):
                slot_image_height = slot_image.GetHeight()
            with contextlib.suppress(Exception):
                rooted_image_height = rooted_image.GetHeight()
            # only refresh UI if the current slot height and current rooted height are 0 and we need to change the image to 64 pixels
            if rooted_image_height == 0 and slot_image_height == 0 and is_rooted:
                self._refresh_ui()
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while updating root image")
            traceback.print_exc()

    # -----------------------------------------------
    #                  _on_show_device_download
    # -----------------------------------------------
    def _on_show_device_download(self, event):
        device = get_phone()
        if not device:
            return
        menu = GoogleImagesPopupMenu(self, device=device.hardware, date_filter=device.firmware_date)
        self.PopupMenu(menu)

    #-----------------------------------------------------------------------------
    #                                   _init_ui
    #-----------------------------------------------------------------------------
    def _init_ui(self):
        # -----------------------------------------------
        #                  _add_mode_radio_button
        # -----------------------------------------------
        def _add_mode_radio_button(sizer, index, flash_mode, label, tooltip):
            style = wx.RB_GROUP if index == 0 else 0
            self.mode_radio_button = wx.RadioButton(panel, name=f"mode-{flash_mode}", label=f"{label}", style=style)
            self.mode_radio_button.Bind(wx.EVT_RADIOBUTTON, self._on_mode_changed)
            self.mode_radio_button.mode = flash_mode
            if flash_mode == self.config.flash_mode:
                self.mode_radio_button.SetValue(True)
            else:
                self.mode_radio_button.SetValue(False)
            self.mode_radio_button.SetToolTip(tooltip)
            sizer.Add(self.mode_radio_button)
            sizer.AddSpacer(10)

        # ==============
        # UI Setup Here
        # ==============
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(orient=wx.VERTICAL)

        fgs1 = wx.FlexGridSizer(cols=2, vgap=10, hgap=10)

        # Add the toolbar
        self._build_toolbar(self.toolbar_flags)

        # 1st row widgets, Android platform tools
        self.platform_tools_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"Android Platform Tools")
        self.sdk_link = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.sdk_link.SetBitmap(bitmap=images.open_link_24.GetBitmap())
        self.sdk_link.SetToolTip("Download Latest Android Platform-Tools")
        self.platform_tools_picker = wx.DirPickerCtrl(parent=panel, id=wx.ID_ANY, style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
        self.platform_tools_picker.SetToolTip("Select Android Platform-Tools Folder\nWhere adb and fastboot are located.")
        platform_tools_label_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        platform_tools_label_sizer.Add(window=self.platform_tools_label, proportion=0, flag=wx.ALL, border=5)
        platform_tools_label_sizer.AddStretchSpacer()
        platform_tools_label_sizer.Add(window=self.sdk_link, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        self.sdk_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.sdk_sizer.Add(window=self.platform_tools_picker, proportion=1, flag=wx.EXPAND)

        # 2nd row widgets, Connected Devices
        self.device_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"ADB Connected Devices")
        self.device_label.SetToolTip(u"Double click this label to issue the command:\nadb kill-server")
        self.wifi_adb = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.wifi_adb.SetBitmap(images.wifi_adb_24.GetBitmap())
        self.wifi_adb.SetToolTip(u"Open wireless manager dialog.")
        adb_label_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        adb_label_sizer.Add(window=self.device_label, proportion=0, flag=wx.ALL, border=5)
        adb_label_sizer.AddStretchSpacer()
        adb_label_sizer.Add(window=self.wifi_adb, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        self.device_choice = wx.ComboBox(parent=panel, id=wx.ID_ANY, value=wx.EmptyString, pos=wx.DefaultPosition, size=wx.DefaultSize, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.device_choice.SetSelection(-1)
        self.device_choice.SetFont(font=wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        device_tooltip = "[root status] [device mode] [device id] [device model] [device firmware]\n\n"
        device_tooltip += "✓ Rooted with Magisk.\n"
        device_tooltip += "✗ Probably Not Root (Magisk Tools not found).\n"
        device_tooltip += "?  Unable to determine the root status.\n\n"
        device_tooltip += "(adb) device is in adb mode\n"
        device_tooltip += "(f.b) device is in fastboot mode\n"
        device_tooltip += "(sid) device is in sideload mode\n"
        device_tooltip += "(rec) device is in recovery mode\n"
        self.device_choice.SetToolTip(device_tooltip)
        self.scan_button = wx.Button(parent=panel, label=u"Scan")
        self.scan_button.SetToolTip(u"Scan for Devices\nPlease manually select the device after the scan is completed.")
        self.scan_button.SetBitmap(images.scan_24.GetBitmap())
        device_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        device_sizer.Add(window=self.device_choice, proportion=1, flag=wx.EXPAND)
        device_sizer.Add(window=self.scan_button, flag=wx.LEFT, border=5)

        # 3rd row Reboot buttons, device related buttons
        # removed

        # 4th row, empty row, static line
        self.slot_image = wx.StaticBitmap(panel, pos=(0, 0))
        self.slot_image.SetBitmap(wx.NullBitmap)
        self.rooted_image = wx.StaticBitmap(panel, pos=(0, 0))
        self.rooted_image.SetBitmap(wx.NullBitmap)
        slot_root_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        slot_root_sizer.Add(window=self.slot_image, proportion=0, flag=wx.ALL, border=0)
        slot_root_sizer.Add(window=self.rooted_image, proportion=0, flag=wx.ALL, border=0)
        self.staticline1 = wx.StaticLine(parent=panel, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LI_HORIZONTAL)
        self.staticline1.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))

        # 5th row widgets, firmware file
        firmware_label = wx.StaticText(parent=panel, label=u"Device Image")
        self.firmware_button = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.firmware_button.SetBitmap(images.open_link_24.GetBitmap())
        self.firmware_button.SetToolTip(u"Download image file for current Pixel device.")
        # self.firmware_picker = wx.FilePickerCtrl(parent=panel, id=wx.ID_ANY, path=wx.EmptyString, message=u"Select a file", wildcard=u"Factory Image files (*.zip;*.tgz;*.tar)|*.zip;*.tgz;*.tar", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.FLP_USE_TEXTCTRL)
        self.firmware_picker = FilePickerComboBox(parent=panel, dialog_title="Select a file", wildcard="Factory Image files (*.zip;*.tgz;*.tar)|*.zip;*.tgz;*.tar")
        self.firmware_picker.SetToolTip(u"Select Pixel Firmware")
        self.process_firmware = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Process", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.process_firmware.SetBitmap(images.process_file_24.GetBitmap())
        self.process_firmware.SetToolTip(u"Process the firmware file and extract the boot.img")
        firmware_label_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        firmware_label_sizer.Add(window=firmware_label, proportion=0, flag=wx.ALL, border=5)
        firmware_label_sizer.AddStretchSpacer(1)
        firmware_label_sizer.Add(window=self.firmware_button, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        self.firmware_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.firmware_sizer.Add(window=self.firmware_picker, proportion=1, flag=wx.EXPAND)
        self.firmware_sizer.Add(window=self.process_firmware, flag=wx.LEFT, border=5)

        # 6th row widgets, custom_rom
        self.custom_rom_checkbox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Apply Custom ROM", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.custom_rom_checkbox.SetToolTip(u"Caution: Make sure you read the selected ROM documentation.\nThis might not work for your ROM")
        self.custom_rom = wx.FilePickerCtrl(parent=panel, id=wx.ID_ANY, path=wx.EmptyString, message=u"Select a file", wildcard=u"ROM files (*.zip;*.tgz;*.tar)|*.zip;*.tgz;*.tar", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.FLP_USE_TEXTCTRL)
        self.custom_rom.SetToolTip(u"Select Custom ROM")
        self.process_rom = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Process", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.process_rom.SetBitmap(images.process_file_24.GetBitmap())
        self.process_rom.SetToolTip(u"Process the ROM file and extract the boot.img")
        custom_rom_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        custom_rom_sizer.Add(window=self.custom_rom, proportion=1, flag=wx.EXPAND)
        custom_rom_sizer.Add(window=self.process_rom, flag=wx.LEFT, border=5)

        # 7th row widgets, boot.img related widgets
        self.select_boot_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"Select a boot/init_boot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.show_all_boot_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Show All boot/init_boot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.show_all_boot_checkBox.SetToolTip(u"Show all boot/init_boot even if it is\nnot part of the selected firmware or ROM")
        # list control
        if self.CharHeight > 20:
            self.il = wx.ImageList(24, 24)
            self.idx1 = self.il.Add(images.patched_24.GetBitmap())
        else:
            self.il = wx.ImageList(16, 16)
            self.idx1 = self.il.Add(images.patched_16.GetBitmap())
        self.list = wx.ListCtrl(parent=panel, id=-1, size=(-1, self.CharHeight * 6), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.list.InsertColumn(0, 'SHA1  ', wx.LIST_FORMAT_LEFT, width=-1)
        self.list.InsertColumn(1, 'Source SHA1  ', wx.LIST_FORMAT_LEFT, width=-1)
        self.list.InsertColumn(2, 'Package Fingerprint  ', wx.LIST_FORMAT_LEFT, width=-1)
        self.list.InsertColumn(3, 'Patched with Magisk  ', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(4, 'Patch Method  ', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(5, 'Patched on Device  ', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(6, 'Date  ', wx.LIST_FORMAT_LEFT, -1)
        self.list.InsertColumn(7, 'Package Path  ', wx.LIST_FORMAT_LEFT, -1)
        self.list.SetHeaderAttr(wx.ItemAttr(wx.Colour('BLUE'), wx.Colour('DARK GREY'), wx.Font(wx.FontInfo(10).Bold())))
        if sys.platform != "win32":
            self.list.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
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
        self.list.SetColumnWidth(7, -2)
        grow_column(self.list, 7, 20)
        # Initialize column width to header column size
        column_widths = []
        for i in range(self.list.GetColumnCount()):
            column_widths.append(self.list.GetColumnWidth(i))
        # Create a new list (will be by value and not by reference)
        self.boot_column_widths = list(column_widths)
        self.flash_boot_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Flash Boot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.flash_boot_button.SetBitmap(images.flash_24.GetBitmap())
        self.flash_boot_button.SetToolTip(u"Flash just the selected item")
        self.patch_boot_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Patch", pos=wx.DefaultPosition, size=self.flash_boot_button.BestSize, style=0)
        self.patch_boot_button.SetBitmap(images.patch_24.GetBitmap())
        self.patch_boot_button.SetToolTip(u"Patch the selected item")
        self.patch_custom_boot_button = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.patch_custom_boot_button.SetBitmap(images.custom_patch_24.GetBitmap())
        self.patch_custom_boot_button.SetToolTip(u"Custom Patch\n\nSelect a file from disk to patch, and then save the patched file to disk.\nUse this if you want to patch a manually extracted boot image.")
        self.delete_boot_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Delete", pos=wx.DefaultPosition, size=self.flash_boot_button.BestSize, style=0)
        self.delete_boot_button.SetBitmap(images.delete_24.GetBitmap())
        self.delete_boot_button.SetToolTip(u"Delete the selected item")
        self.boot_folder_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Open Folder", pos=wx.DefaultPosition, size=self.flash_boot_button.BestSize, style=0)
        self.boot_folder_button.SetBitmap(images.folder_24.GetBitmap())
        self.boot_folder_button.SetToolTip(u"Open boot files folder.")
        self.firmware_folder_button = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.firmware_folder_button.SetBitmap(images.folder_24.GetBitmap())
        self.firmware_folder_button.SetToolTip(u"Open Working Directory\n\nOpens the firmware working directory.\nUse this if you want to manually run commands from the working directory")
        self.live_boot_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Live Boot", pos=wx.DefaultPosition, size=self.flash_boot_button.BestSize, style=0)
        self.live_boot_button.SetBitmap(images.boot_24.GetBitmap())
        self.live_boot_button.SetToolTip(u"Live boot to the selected item")
        boot_label_v_sizer = wx.BoxSizer(wx.VERTICAL)
        boot_label_v_sizer.Add(window=self.select_boot_label, flag=wx.ALL, border=0)
        boot_label_v_sizer.AddSpacer(10)
        boot_label_v_sizer.Add(window=self.show_all_boot_checkBox, flag=wx.ALL, border=0)
        patch_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        patch_sizer.Add(window=self.patch_boot_button, proportion=1, flag=wx.EXPAND)
        patch_sizer.Add(window=self.patch_custom_boot_button, flag=wx.LEFT, border=5)
        folder_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        folder_sizer.Add(window=self.boot_folder_button, proportion=1, flag=wx.EXPAND)
        folder_sizer.Add(window=self.firmware_folder_button, flag=wx.LEFT, border=5)
        image_buttons_sizer = wx.BoxSizer(orient=wx.VERTICAL)
        image_buttons_sizer.Add(patch_sizer, proportion=1, flag=wx.LEFT, border=5)
        image_buttons_sizer.Add(self.delete_boot_button, proportion=1, flag=wx.LEFT, border=5)
        image_buttons_sizer.Add(folder_sizer, proportion=1, flag=wx.LEFT, border=5)
        image_buttons_sizer.Add(self.live_boot_button, proportion=1, flag=wx.LEFT, border=5)
        image_buttons_sizer.Add(self.flash_boot_button, proportion=1, flag=wx.LEFT, border=5)
        list_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        list_sizer.Add(self.list, proportion=1, flag=wx.ALL|wx.EXPAND)
        list_sizer.Add(image_buttons_sizer, proportion=0, flag=wx.ALL|wx.EXPAND)

        # 8th row widgets (Flash Mode)
        mode_label = wx.StaticText(panel, label=u"Flash Mode")
        self.mode_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        # _add_mode_radio_button(sizer, index, flash_mode, label, tooltip)
        _add_mode_radio_button(sizer=self.mode_sizer, index=0, flash_mode='keepData', label="Keep Data", tooltip="Data will be kept intact.")
        _add_mode_radio_button(sizer=self.mode_sizer, index=1, flash_mode='wipeData', label="WIPE all data", tooltip="CAUTION: This will wipe your data")
        _add_mode_radio_button(sizer=self.mode_sizer, index=2, flash_mode='dryRun', label="Dry Run", tooltip="Dry Run, no flashing will be done.\nThe phone will reboot to fastboot and then\nback to normal.\nThis is for testing.")
        _add_mode_radio_button(sizer=self.mode_sizer, index=3, flash_mode='OTA', label="Full OTA", tooltip="Flash full OTA, and have the choice of flashing patched image(s).")
        _add_mode_radio_button(sizer=self.mode_sizer, index=4, flash_mode='customFlash', label="Custom Flash", tooltip="Custom Flash, Advanced option to flash a single file.\nThis will not flash the factory image.\It will flash the single selected file.")


        # 9th row widgets (custom flash)
        self.live_boot_radio_button = wx.RadioButton(parent=panel, id=wx.ID_ANY, label=u"Live Boot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.RB_GROUP)
        self.live_boot_radio_button.Enable(False)
        self.live_boot_radio_button.SetToolTip(u"Live Boot to selected boot / init_boot")
        self.flash_radio_button = wx.RadioButton(parent=panel, id=wx.ID_ANY, label=u"Flash", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.flash_radio_button.SetValue(True)
        self.flash_radio_button.Enable(False)
        self.flash_radio_button.SetToolTip(u"Flashes the selected boot / init_boot")
        custom_advanced_options_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        custom_advanced_options_sizer.Add(window=self.live_boot_radio_button, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        custom_advanced_options_sizer.Add(window=self.flash_radio_button, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        # 2nd column
        # https://android.googlesource.com/platform/system/core/+/refs/heads/master/fastboot/fastboot.cpp#144
        image_choices = [ u"boot", u"init_boot", u"bootloader", u"cache", u"dtbo", u"dts", u"odm", u"odm_dlkm", u"product", u"pvmfw", u"radio", u"recovery", u"super", u"super_empty", u"system", u"system_dlkm", u"system_ext", u"system_other", u"userdata", u"vbmeta", u"vbmeta_system", u"vbmeta_vendor", u"vendor", u"vendor_boot", u"vendor_dlkm", u"vendor_kernel_boot", u"vendor_other", u"image", u"SIDELOAD" ]
        self.image_choice = wx.Choice(parent=panel, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, choices=image_choices, style=0)
        self.image_choice.SetSelection(-1)
        self.image_file_picker = wx.FilePickerCtrl(parent=panel, id=wx.ID_ANY, path=wx.EmptyString, message=u"Select a file", wildcard=u"Flashable files (*.img;*.zip)|*.img;*.zip", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.FLP_USE_TEXTCTRL)
        self.paste_selection = wx.BitmapButton(parent=panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.paste_selection.SetBitmap(images.paste_24.GetBitmap())
        self.paste_selection.SetToolTip(u"Depending on the flash selection, paste the appropriate path as custom image.")
        custom_flash_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        custom_flash_sizer.Add(window=self.image_choice, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        custom_flash_sizer.Add(window=self.image_file_picker, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        custom_flash_sizer.Add(window=self.paste_selection, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)


        # 10th row widgets, Flash options
        self.advanced_options_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"Flash Options")
        self.flash_to_inactive_slot_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Flash to inactive slot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.flash_to_inactive_slot_checkBox.SetToolTip(u"This option when checked will flash to the alternate slot (inactive).\nKeeping the current slot intact.")
        self.flash_both_slots_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Flash to both slots", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.flash_both_slots_checkBox.SetToolTip(u"This option when checked will flash to both slots.")
        self.disable_verity_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Disable Verity", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.disable_verity_checkBox.SetToolTip(u"Disables Verity")
        self.disable_verification_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Disable Verification", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.disable_verification_checkBox.SetToolTip(u"Disables Verification")
        self.fastboot_force_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Force", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.fastboot_force_checkBox.SetToolTip(u"Force a flash operation that may be unsafe (will wipe your data)")
        self.fastboot_verbose_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Verbose", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.fastboot_verbose_checkBox.SetToolTip(u"Set fastboot option to verbose")
        self.temporary_root_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Temporary Root", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.temporary_root_checkBox.SetToolTip(u"This option when enabled will not flash patched boot\nInstead it will flash unpatched boot.img, but boot to Live Patched boot\nHandy to test if Magisk will cause a bootloop.\n\nPlease be aware that this temporary root will not survive a subsequent reboot.\nIf you want to make this permanent, just Flash Boot the patched boot image.")
        self.no_reboot_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"No reboot", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.no_reboot_checkBox.SetToolTip(u"Do not reboot after flashing\nThis is useful if you want to perform other actions before reboot.")
        self.wipe_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Wipe", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.wipe_checkBox.SetToolTip(u"This will invoke data wipe operation at the end of custom flashing.\nOne use case would be when disabling verification for the first time.")
        self.advanced_options_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.advanced_options_sizer.Add(window=self.flash_to_inactive_slot_checkBox, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        self.advanced_options_sizer.Add(window=self.flash_both_slots_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.disable_verity_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.disable_verification_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.fastboot_force_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.fastboot_verbose_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.temporary_root_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.no_reboot_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.advanced_options_sizer.Add(window=self.wipe_checkBox, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)

        # 11th row widgets, Flash button
        self.flash_button = wx.Button(parent=panel, id=-1, label="Flash Pixel Phone", pos=wx.DefaultPosition, size=wx.Size(-1, 50))
        self.flash_button.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.flash_button.SetToolTip(u"Flashes the selected device with chosen flash options.")
        self.flash_button.SetBitmap(images.flash_32.GetBitmap())

        # 12th row widgets, console
        console_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"Console", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spinner = wx.ActivityIndicator(panel, -1, size=(100, 100), style=0)
        self.spinner_label = wx.StaticText(parent=panel, id=wx.ID_ANY, label=u"Please be patient ...", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spinner_label.SetForegroundColour((255,0,0))
        self.spinner_label.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.support_button = wx.Button(parent=panel, id=wx.ID_ANY, label=u"Support", size=wx.Size(-1, 50), style=0)
        self.support_button.SetBitmap(images.support_24.GetBitmap())
        self.support_button.SetBitmapMargins(wx.Size(10, -1))
        self.support_button.SetToolTip(u"Create sanitized support.zip file\nAll sensitive data is redacted.\n\nThis if absolutely required when asking for help.")
        console_v_sizer = wx.BoxSizer(orient=wx.VERTICAL)
        console_v_sizer.Add(console_label, flag=wx.ALL, border=0)
        console_v_sizer.AddSpacer(40)
        console_v_sizer.Add(self.spinner, flag=wx.LEFT, border=50)
        console_v_sizer.AddSpacer(20)
        console_v_sizer.Add(self.spinner_label, flag=wx.ALL, border=0)
        console_v_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=0)
        console_v_sizer.Add(self.support_button, proportion=0, flag=wx.ALL|wx.EXPAND, border=0)
        self.console_ctrl = wx.TextCtrl(parent=panel, id=wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, pos=wx.DefaultPosition, size=wx.DefaultSize)
        self.console_ctrl.SetMinSize((400, 200)) # set a minimum size of 400 x 200 pixels
        set_console_widget(self.console_ctrl)
        if not self.config.customize_font:
            self.spinner_label.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
            self.console_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            if darkdetect.isLight():
                self.console_ctrl.SetBackgroundColour(wx.WHITE)
                self.console_ctrl.SetForegroundColour(wx.BLUE)
                self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        # 13th row widgets, debug and clear button
        self.verbose_checkBox = wx.CheckBox(parent=panel, id=wx.ID_ANY, label=u"Debug", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.verbose_checkBox.SetToolTip(u"Enable Debug Messages in the console.")
        clear_button = wx.Button(parent=panel, id=-1, label="Clear Console", pos=wx.DefaultPosition)

        # add the rows to flexgrid
        fgs1.AddMany([
                    (platform_tools_label_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (self.sdk_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (adb_label_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (device_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # removed
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    slot_root_sizer, (self.staticline1, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.EXPAND|wx.TOP, 5),
                    (firmware_label_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (self.firmware_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (self.custom_rom_checkbox, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (custom_rom_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (boot_label_v_sizer, 0, wx.EXPAND), (list_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    (mode_label, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (self.mode_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (custom_advanced_options_sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), (custom_flash_sizer, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                    (self.advanced_options_label, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5), self.advanced_options_sizer,
                    (wx.StaticText(panel, label="")), (self.flash_button, 1, wx.EXPAND),
                    # (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    (console_v_sizer, 0, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND),
                    (self.verbose_checkBox), (clear_button, 1, wx.EXPAND)])

        # this makes the second column expandable (index starts at 0)
        fgs1.AddGrowableCol(1, 1)

        row_count = fgs1.EffectiveRowsCount
        # this makes the console row expandable (index starts at 0)
        fgs1.AddGrowableRow(row_count - 2, 1)

        # add flexgrid to vbox
        vbox.Add(fgs1, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        # set the panel
        panel.SetSizer(vbox)

        # Connect Events
        self.device_choice.Bind(wx.EVT_COMBOBOX, self._on_select_device)
        self.scan_button.Bind(wx.EVT_BUTTON, self._on_scan)
        self.firmware_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_select_firmware)
        self.platform_tools_picker.Bind(wx.EVT_DIRPICKER_CHANGED, self._on_select_platform_tools)
        self.device_label.Bind(wx.EVT_LEFT_DCLICK, self._on_adb_kill_server)
        self.sdk_link.Bind(wx.EVT_BUTTON, self._open_sdk_link)
        self.wifi_adb.Bind(wx.EVT_BUTTON, self._on_wifi_manager)
        self.custom_rom_checkbox.Bind(wx.EVT_CHECKBOX, self._on_custom_rom)
        self.custom_rom.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_select_custom_rom)
        self.disable_verification_checkBox.Bind(wx.EVT_CHECKBOX, self._on_disable_verification)
        self.flash_both_slots_checkBox.Bind(wx.EVT_CHECKBOX, self._on_flash_both_slots)
        self.flash_to_inactive_slot_checkBox.Bind(wx.EVT_CHECKBOX, self._on_flash_to_inactive_slot)
        self.no_reboot_checkBox.Bind(wx.EVT_CHECKBOX, self._on_no_reboot)
        self.wipe_checkBox.Bind(wx.EVT_CHECKBOX, self._on_wipe)
        self.disable_verity_checkBox.Bind(wx.EVT_CHECKBOX, self._on_disable_verity)
        self.fastboot_force_checkBox.Bind(wx.EVT_CHECKBOX, self._on_fastboot_force)
        self.fastboot_verbose_checkBox.Bind(wx.EVT_CHECKBOX, self._on_fastboot_verbose)
        self.temporary_root_checkBox.Bind(wx.EVT_CHECKBOX, self._on_temporary_root)
        self.flash_button.Bind(wx.EVT_BUTTON, self._on_flash)
        self.verbose_checkBox.Bind(wx.EVT_CHECKBOX, self._on_verbose)
        clear_button.Bind(wx.EVT_BUTTON, self._on_clear)
        self.image_file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self._on_image_select)
        self.image_choice.Bind(wx.EVT_CHOICE, self._on_image_choice)
        self.list.Bind(wx.EVT_LEFT_DOWN, self._on_boot_selected)
        self.patch_boot_button.Bind(wx.EVT_BUTTON, self._on_patch_boot)
        self.patch_custom_boot_button.Bind(wx.EVT_BUTTON, self._on_patch_custom_boot)
        self.delete_boot_button.Bind(wx.EVT_BUTTON, self._on_delete_boot)
        self.boot_folder_button.Bind(wx.EVT_BUTTON, self._on_boot_folder)
        self.firmware_folder_button.Bind(wx.EVT_BUTTON, self._on_firmware_folder)
        self.live_boot_button.Bind(wx.EVT_BUTTON, self._on_live_boot)
        self.flash_boot_button.Bind(wx.EVT_BUTTON, self._on_flash_boot)
        self.process_firmware.Bind(wx.EVT_BUTTON, self._on_process_firmware)
        self.process_rom.Bind(wx.EVT_BUTTON, self._on_process_rom)
        self.show_all_boot_checkBox.Bind(wx.EVT_CHECKBOX, self._on_show_all_boot)
        self.paste_selection.Bind(wx.EVT_BUTTON, self._on_paste_selection)
        self.support_button.Bind(wx.EVT_BUTTON, self._on_support_zip)
        self.list.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_SIZE, self._on_resize)
        self.Bind(wx.EVT_MOVE_END, self._on_move_end)
        self.Bind(wx.EVT_BUTTON, self._on_show_device_download, self.firmware_button)

        # Update UI
        self.Layout()


    # -----------------------------------------------
    #                  update_google_images_menu
    # -----------------------------------------------
    def update_google_images_menu(self):
        self.google_images_menu.reset_menu_id()
        menu_index = self.menuBar.FindMenu("Google Images")
        self.menuBar.Remove(menu_index)
        self.google_images_menu = GoogleImagesMenu(self)
        self.menuBar.Insert(menu_index, self.google_images_menu, "Google Images")
        self.Refresh()
        self.Update()


# ============================================================================
#                               Class MySplashScreen
# ============================================================================
class MySplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        wx.adv.SplashScreen.__init__(self, images.Splash_dark.GetBitmap(), wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 20000, None, -1, wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER)
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
        with contextlib.suppress(Exception):
            self.Hide()
        if self.__fc.IsRunning():
            self.Raise()


# ============================================================================
#                               Class App
# ============================================================================
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def __init__(self, global_args, *args, **kwargs):
        self.global_args = global_args
        super(App, self).__init__(*args, **kwargs)

    def OnInit(self):
        # see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
        self.ResetLocale()
        wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("PixelFlasher")
        print(f"global_args.config: {self.global_args.config}")

        if self.global_args.config:
            init_config_path(self.global_args.config)
        else:
            init_config_path()

        t = f"{datetime.now():%Y-%m-%d_%Hh%Mm%Ss}"
        pumlfile = os.path.join(get_config_path(), 'puml', f"PixelFlasher_{t}.puml")
        set_pumlfile(pumlfile)
        puml(f"@startuml {t}\nscale 2\nstart\n", False, "w")
        puml("<style>\n  note {\n    FontName Courier\n    FontSize 10\n  }\n</style>\n")

        if inspector:
            frame = PixelFlasher(None, "PixelFlasher")
            # frame.SetClientSize(frame.FromDIP(wx.Size(MAIN_WIDTH, MAIN_HEIGHT)))
            # frame.SetClientSize(wx.Size(MAIN_WIDTH, MAIN_HEIGHT))
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
#                               Class GlobalArgs
# ============================================================================
class GlobalArgs():
    pass


# ============================================================================
#                               Function parse_arguments
# ============================================================================
def parse_arguments():
    # sourcery skip: inline-immediately-returned-variable
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-c", "--config", help="Path to the configuration file")
    parser.add_argument("-l", "--console", action="store_true", help="Log to console as well")
    args  = parser.parse_args()
    return args


# ============================================================================
#                    Function _open_device_image_download_link
# ============================================================================
def open_device_image_download_link(url):
    try:
        with contextlib.suppress(Exception):
            device = get_phone()
            if device:
                hardware = device.hardware
            else:
                hardware = ''
        print(f"Launching browser for Google image download URL: {url}#{hardware}")
        webbrowser.open_new(f"{url}#{hardware}")
        puml(f":Open Link;\nnote right\n=== {hardware} Firmware Link\n[[{url}#{hardware}]]\nend note\n", True)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening firmware link")
        traceback.print_exc()

# ============================================================================
#                               Function ask
# ============================================================================
def ask(parent=None, message='', default_value=''):
    dlg = wx.TextEntryDialog(parent, message, value=default_value)
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    return result


# ============================================================================
#                               Function Main
# ============================================================================
def main():
    # Parse the command-line arguments and store them in the global object
    global global_args
    try:
        global_args = parse_arguments()
    except SystemExit:
        # Handle the case where parsing arguments fails
        print("Failed to parse command-line arguments.")
        return

    app = App(global_args, False)
    if inspector:
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    __name__ = 'Main'
    main()

