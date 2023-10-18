#!/usr/bin/env python

import contextlib
import copy
import fnmatch
import math
import ntpath
import os
import shutil
import sqlite3 as sl
import sys
import tempfile
import time
from datetime import datetime
from urllib.parse import urlparse

import wx
from packaging.version import parse
from platformdirs import *

from constants import *
from file_editor import FileEditor
from magisk_downloads import MagiskDownloads
from message_box_ex import MessageBoxEx
from payload_dumper import extract_payload
from phone import get_connected_devices
from runtime import *


# ============================================================================
#                               Class FlashFile
# ============================================================================
class FlashFile():
    def __init__(self, linenum = '', platform = '', type = '', command = '', action = '', arg1 = '', arg2 = ''):
        # Instance variables
        self.linenum = linenum
        self.platform = platform
        self.type = type
        self.command = command
        self.action = action
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def full_line(self):
        response = f"{self.command} {self.action} {self.arg1} {self.arg2}"
        return response.strip()

    @property
    def sync_line(self):
        if self.type in ['init', 'sleep']:
            response = self.type
        elif self.type in ['path', 'if_block']:
            # don't include
            response = ''
        else:
            response = f"{self.command} {self.action} {self.arg1} {self.arg2}"
        return response.strip()


# ============================================================================
#                               Function check_platform_tools
# ============================================================================
def check_platform_tools(self):
    if sys.platform == "win32":
        adb_binary = 'adb.exe'
        fastboot_binary = 'fastboot.exe'
    else:
        adb_binary = 'adb'
        fastboot_binary = 'fastboot'
    if self.config.platform_tools_path:
        adb = os.path.join(self.config.platform_tools_path, adb_binary)
        fastboot = os.path.join(self.config.platform_tools_path, fastboot_binary)
        if os.path.exists(fastboot) and os.path.exists(adb):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Selected Platform Tools Path:\n{self.config.platform_tools_path}.")
            adb = os.path.join(self.config.platform_tools_path, adb_binary)
            fastboot = os.path.join(self.config.platform_tools_path, fastboot_binary)
            set_adb(adb)
            set_fastboot(fastboot)
            set_adb_sha256(sha256(adb))
            set_fastboot_sha256(sha256(fastboot))
            res = identify_sdk_version(self)
            print(f"SDK Version:      {get_sdk_version()}")
            print(f"Adb SHA256:       {get_adb_sha256()}")
            print(f"Fastboot SHA256:  {get_fastboot_sha256()}")
            puml(f":Selected Platform Tools;\nnote left: {self.config.platform_tools_path}\nnote right:{get_sdk_version()}\n")
            if res == -1:
                return -1
            set_android_product_out(self.config.platform_tools_path)
            return
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected path {self.config.platform_tools_path} does not have adb and or fastboot")
            puml(f"#red:Selected Platform Tools;\nnote left: {self.config.platform_tools_path}\nnote right:The selected path does not have adb and or fastboot\n")
            self.config.platform_tools_path = None
            set_adb(None)
            set_fastboot(None)

    if not self.config.platform_tools_path:
        print("Looking for Android Platform Tools in system PATH environment ...")
        adb = which(adb_binary)
        if adb:
            folder_path = os.path.dirname(adb)
            print(f"Found Android Platform Tools in {folder_path}")
            adb = os.path.join(folder_path, adb_binary)
            fastboot = os.path.join(folder_path, fastboot_binary)
            set_adb(adb)
            set_fastboot(fastboot)
            set_adb_sha256(sha256(adb))
            if os.path.exists(get_fastboot()):
                self.config.platform_tools_path = folder_path
                res = identify_sdk_version(self)
                set_fastboot_sha256(sha256(fastboot))
                print(f"SDK Version:      {get_sdk_version()}")
                print(f"Adb SHA256:       {get_adb_sha256()}")
                print(f"Fastboot SHA256:  {get_fastboot_sha256()}")
                if res == -1:
                    return -1
                set_android_product_out(self.config.platform_tools_path)
                return
            else:
                print(f"fastboot is not found in: {self.config.platform_tools_path}")
                self.config.platform_tools_path = None
                set_adb(None)
                set_fastboot(None)
        else:
            print("Android Platform Tools is not found.")
    with contextlib.suppress(Exception):
        if self.config.platform_tools_path:
            self.platform_tools_picker.SetPath(self.config.platform_tools_path)
            set_android_product_out(self.config.platform_tools_path)
        else:
            self.platform_tools_picker.SetPath('')
            return -1


# ============================================================================
#                               Function set_android_product_out
# ============================================================================
def set_android_product_out(sdk_path):
    # add the SDK path to to ANDROID_PRODUCT_OUT env
    env_vars = get_env_variables()
    env_vars["ANDROID_PRODUCT_OUT"] = f"{sdk_path}"
    set_env_variables(env_vars)


# ============================================================================
#                               Function populate_boot_list
# ============================================================================
def populate_boot_list(self, sortColumn=None, sorting_direction='ASC'):
    self.list.DeleteAllItems()
    con = get_db()
    con.execute("PRAGMA foreign_keys = ON")
    con.commit()
    sql = """
        SELECT
            BOOT.id as boot_id,
            BOOT.boot_hash,
            BOOT.file_path as boot_path,
            BOOT.is_patched,
            BOOT.patch_method,
            BOOT.magisk_version,
            BOOT.hardware,
            BOOT.epoch as boot_date,
            PACKAGE.id as package_id,
            PACKAGE.boot_hash as package_boot_hash,
            PACKAGE.type as package_type,
            PACKAGE.package_sig,
            PACKAGE.file_path as package_path,
            PACKAGE.epoch as package_date,
            BOOT.is_odin,
            PACKAGE.full_ota
        FROM BOOT
        JOIN PACKAGE_BOOT
            ON BOOT.id = PACKAGE_BOOT.boot_id
        JOIN PACKAGE
            ON PACKAGE.id = PACKAGE_BOOT.package_id
    """
    # Apply filter if show all is not selected
    parameters = []
    if not self.config.show_all_boot:
        rom_path = ''
        firmware_path = ''
        if self.config.custom_rom and self.config.advanced_options:
            rom_path = self.config.custom_rom_path
        if self.config.firmware_path:
            firmware_path = self.config.firmware_path
        sql += """
            WHERE
                (BOOT.is_patched = 0 AND PACKAGE.file_path IN (?, ?))
                OR
                (BOOT.is_patched = 1 AND PACKAGE.boot_hash IN (
                    SELECT PACKAGE.boot_hash
                    FROM BOOT
                    JOIN PACKAGE_BOOT
                        ON BOOT.id = PACKAGE_BOOT.boot_id
                    JOIN PACKAGE
                        ON PACKAGE.id = PACKAGE_BOOT.package_id
                    WHERE
                        (BOOT.is_patched = 0 AND PACKAGE.file_path IN (?, ?))
                ))
        """
        parameters.extend([firmware_path, rom_path, firmware_path, rom_path])

    # Clear the previous sort order arrows
    for i in range(self.list.GetColumnCount()):
        col = self.list.GetColumn(i)
        col_text = col.Text.rstrip(" ▲▼")
        col.SetImage(-1)
        col.SetText(f"{col_text}  ")
        self.list.SetColumn(i, col)

    # Order the query results based on the sortColumn and sorting_direction if provided
    if sortColumn is not None:
        # Set the sort order arrow for the current column
        col = self.list.GetColumn(sortColumn - 1)
        col_text = col.Text.strip()
        if sorting_direction == 'ASC':
            col.SetText(f"{col_text} ▲")
            col.SetImage(-1)
        elif sorting_direction == 'DESC':
            col.SetText(f"{col_text} ▼")
            col.SetImage(-1)
        self.list.SetColumn(sortColumn - 1, col)

        # Get the column name based on the sortColumn number
        column_map = {
            1: 'BOOT.boot_hash',
            2: 'PACKAGE.boot_hash',
            3: 'PACKAGE.package_sig',
            4: 'BOOT.magisk_version',
            5: 'BOOT.patch_method',
            6: 'BOOT.hardware',
            7: 'BOOT.epoch',
            8: 'PACKAGE.file_path'
        }
        column_name = column_map.get(sortColumn, '')
        if column_name:
            sql += f" ORDER BY {column_name} {sorting_direction};"
    else:
        # Add default sorting
        sql += " ORDER BY BOOT.is_patched ASC, BOOT.epoch ASC;"

    with con:
        data = con.execute(sql, parameters)
        i = 0
        full_ota = None
        for row in data:
            boot_hash = row[1][:8] or ''
            package_boot_hash = row[9][:8] or ''
            package_sig = row[11] or ''
            patched_with_magisk_version = str(row[5]) or ''
            patch_method = row[4] or ''
            hardware = row[6] or ''
            ts = datetime.fromtimestamp(row[7])
            boot_date = ts.strftime('%Y-%m-%d %H:%M:%S')
            package_path = row[12] or ''
            if self.config.firmware_path == package_path:
                full_ota = row[15]

            index = self.list.InsertItem(i, boot_hash)                     # boot_hash (SHA1)
            self.list.SetItem(index, 1, package_boot_hash)                 # package_boot_hash (Source SHA1)
            self.list.SetItem(index, 2, package_sig)                       # package_sig (Package Fingerprint)
            self.list.SetItem(index, 3, patched_with_magisk_version)       # patched with magisk_version
            self.list.SetItem(index, 4, patch_method)                      # patched_method
            self.list.SetItem(index, 5, hardware)                          # hardware
            self.list.SetItem(index, 6, boot_date)                         # boot_date
            self.list.SetItem(index, 7, package_path)                      # package_path
            if row[3]:
                self.list.SetItemColumnImage(i, 0, 0)
            else:
                self.list.SetItemColumnImage(i, 0, -1)
            i += 1
        if i > 0 and full_ota is not None:
            set_ota(self, bool(full_ota))

    auto_resize_boot_list(self)

    # disable buttons
    self.config.boot_id = None
    self.config.selected_boot_md5 = None
    if self.list.ItemCount == 0 :
        if self.config.firmware_path:
            print("\nPlease Process the firmware!")
    else:
        print("\nPlease select a boot image!")
    self.update_widget_states()
    # we need to do this, otherwise the focus goes on the next control, which is a radio button, and undesired.
    self.process_firmware.SetFocus()


# ============================================================================
#                               Function auto_resize_boot_list
# ============================================================================
def auto_resize_boot_list(self):
    # auto size columns to largest text, including the header (except the last column)
    cw = 0
    column_widths = copy.deepcopy(self.boot_column_widths)
    for i in range(self.list.ColumnCount - 1):
        self.list.SetColumnWidth(i, -1)  # Set initial width to -1 (default)
        width = self.list.GetColumnWidth(i)
        self.list.SetColumnWidth(i, -2)  # Auto-size column width to largest text
        width = max(width, self.list.GetColumnWidth(i), column_widths[i])  # Get the maximum width
        if width > column_widths[i]:
            column_widths[i] = width  # Store / update the width in the array
        self.list.SetColumnWidth(i, width)  # Set the column width
        cw += width

    # Set the last column width to the available room
    available_width = self.list.BestVirtualSize.Width - cw - 10
    self.list.SetColumnWidth(self.list.ColumnCount - 1, available_width)


# ============================================================================
#                               Function identify_sdk_version
# ============================================================================
def identify_sdk_version(self):
    sdk_version = None
    set_sdk_state(False)
    # Let's grab the adb version
    with contextlib.suppress(Exception):
        if get_adb():
            theCmd = f"\"{get_adb()}\" --version"
            response = run_shell(theCmd)
            if response.stdout:
                # Split lines based on mixed EOL formats
                lines = re.split(r'\r?\n', response.stdout)
                for line in lines:
                    if 'Version' in line:
                        sdk_version = line.split()[1]
                        set_sdk_version(sdk_version)
                        # If version is old treat it as bad SDK
                        sdkver = sdk_version.split("-")[0]
                        if parse(sdkver) < parse(SDKVERSION) or (sdkver in ('34.0.0', '34.0.1', '34.0.2', '34.0.3')):
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Detected old or problematic Android Platform Tools version {sdk_version}")
                            # confirm if you want to use older version
                            dlg = wx.MessageDialog(None, f"You have an old or problematic Android platform Tools version {sdk_version}\nYou are strongly advised to update to the latest known good version to avoid any issues.\n(Android Platform-Tools version 33.0.3 is known to be good).\n\nAre you sure want to continue?",'Bad Android Platform Tools',wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
                            result = dlg.ShowModal()
                            puml(f"#red:Selected Platform Tools;\nnote left: {self.config.platform_tools_path}\nnote right:ERROR: Detected old or problematic Android Platform Tools version {sdk_version}\n")
                            if result == wx.ID_YES:
                                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User accepted the bad version {sdk_version} of Android platform tools.")
                                set_sdk_state(True)
                                puml("#red:User wanted to proceed regardless;\n")
                            else:
                                print("Bad Android platform tools is not accepted. For your protection, disabling device selection.")
                                print("Please update Android SDK.\n")
                                break
                        # 34.01 is still broken, skip the whitelisted binaries
                        # elif sdkver == '34.0.1' and (
                        #             get_adb_sha256() not in (
                        #                 '30c68c1c1a9814a724f47ca544f273b8097263677383046ddb7a0e8c26f7dc60',
                        #                 'bfd5ea39c672b8f0f51796d6fe5439f152e86eafbba9f402d3abda802050e956',
                        #                 '9d8e3e278b4415416b5da6f94f752e808f8a71fa8397bb6a765c1b44bb807bb2')
                        #             or get_fastboot_sha256() not in (
                        #                 'd765b626aa5b54d9d226eb1a915657c6197379835bde67742f9a2832c8c5c2a9',
                        #                 'e8e6b8f4e8d69401967d16531308b48f144202e459662eae656a0c6e68c2741f',
                        #                 '29c66b605521dea3c3e32f3b1fd7c30a1637ec3eb729820a48bd6827e4659a20')):
                        #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected Android Platform Tools version {sdkver} has known issues, please select another version.")
                        #     puml(f"#red:Android Platform Tools version {sdkver} has known issues;\n")
                        #     dlg = wx.MessageDialog(None, f"Android Platform Tools version {sdkver} has known issues, please select another version.",f"Android Platform Tools {sdkver}",wx.OK | wx.ICON_EXCLAMATION)
                        #     result = dlg.ShowModal()
                        #     break
                        else:
                            set_sdk_state(True)
            elif response.stderr:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {response.stderr}")

    self.update_widget_states()
    if get_sdk_state():
        return

    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android Platform Tools version is not available or is too old.")
    print("                           For your protection, disabling device selection.")
    print("                           Please select valid Android SDK.\n")
    puml("#pink:For your protection, disabled device selection;\n")
    self.config.device = None
    self.device_choice.SetItems([''])
    self.device_choice.Select(-1)
    return -1


# ============================================================================
#                               Function get_flash_settings
# ============================================================================
def get_flash_settings(self):
    message = ''
    isPatched = ''

    p_custom_rom = self.config.custom_rom and self.config.advanced_options
    p_custom_rom_path = self.config.custom_rom_path
    boot = get_boot()
    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
        return

    message += f"Android SDK Version:    {get_sdk_version()}\n"
    message += f"Device:                 {self.config.device} {device.hardware} {device.build}\n"
    message += f"Factory Image:          {self.config.firmware_path}\n"
    if p_custom_rom :
        message += f"Custom Rom:             {str(p_custom_rom)}\n"
        message += f"Custom Rom File:        {p_custom_rom_path}\n"
        rom_file = ntpath.basename(p_custom_rom_path)
        set_custom_rom_file(rom_file)
    message += f"\nBoot image:             {boot.boot_hash[:8]} / {boot.package_boot_hash[:8]} \n"
    message += f"                        From: {boot.package_path}\n"
    if boot.is_patched:
        if boot.patch_method:
            message += f"                        Patched with Magisk {boot.magisk_version} on {boot.hardware} method: {boot.patch_method}\n"
        else:
            message += f"                        Patched with Magisk {boot.magisk_version} on {boot.hardware}\n"
    message += f"\nFlash Mode:             {self.config.flash_mode}\n"
    message += "\n"
    return message


# ============================================================================
#                               Function wifi_adb_connect
# ============================================================================
def wifi_adb_connect(self, value, disconnect = False):
    if disconnect:
        command = 'disconnect'
    else:
        command = 'connect'
    print(f"Remote ADB {command}ing: {value}")
    if get_adb():
        puml(":Wifi ADB;\n", True)
        if ':' in value:
            ip,port = value.split(':')
        else:
            ip = value.strip()
            port = '5555'
        theCmd = f"\"{get_adb()}\" {command} {ip}:{port}"
        res = run_shell(theCmd)
        puml(f"note right\n=== {command} to: {ip}:{port}\nend note\n")
        if res.returncode == 0 and 'cannot' not in res.stdout and 'failed' not in res.stdout:
            print(f"ADB {command}ed: {ip}:{port}")
            puml(f"#palegreen:Succeeded;\n")
            self.device_choice.SetItems(get_connected_devices())
            self._select_configured_device()
            if not disconnect:
                print(f"Please select the device: {ip}:{port}")
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not {command} {ip}:{port}\n")
            print(f"{res.stderr}")
            print(f"{res.stdout}")
            puml(f"#red:**Failed**\n{res.stderr}\n{res.stdout};\n")
            return -1


# ============================================================================
#                               Function adb_kill_server
# ============================================================================
def adb_kill_server(self):
    if get_adb():
        print("Invoking adb kill-server ...")
        puml(":adb kill-server;\n", True)
        theCmd = f"\"{get_adb()}\" kill-server"
        res = run_shell(theCmd)
        if res.returncode == 0:
            print("returncode: 0")
            puml(f"#palegreen:Succeeded;\n")
            self.device_choice.SetItems(get_connected_devices())
            self._select_configured_device()
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not kill adb server.\n")
            print(f"{res.stderr}")
            print(f"{res.stdout}")
            puml(f"#red:**Failed**\n{res.stderr}\n{res.stdout};\n")
            return -1
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Missing Android platform tools.\n")
        puml(f"#red:Missing Android platform tools;\n")
        return -1


# ============================================================================
#                               Function set_flash_button_state
# ============================================================================
def set_flash_button_state(self):
    try:
        boot = get_boot()
        if self.config.firmware_path and os.path.exists(boot.package_path):
            self.flash_button.Enable()
        else:
            self.flash_button.Disable()
    except Exception:
        self.flash_button.Disable()


# ============================================================================
#                               Function select_firmware
# ============================================================================
def select_firmware(self):
    puml(":Selecting Firmware;\n", True)
    firmware = ntpath.basename(self.config.firmware_path)
    filename, extension = os.path.splitext(firmware)
    extension = extension.lower()
    if extension in ['.zip', '.tgz', '.tar']:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} The following firmware is selected:\n{firmware}")
        firmware_hash = sha256(self.config.firmware_path)
        print(f"Selected Firmware {firmware} SHA-256: {firmware_hash}")
        puml(f"note right\n{firmware}\nSHA-256: {firmware_hash}\nend note\n")

        # Check to see if the first 8 characters of the checksum is in the filename, Google published firmwares do have this.
        if firmware_hash[:8] in firmware:
            print(f"Expected to match {firmware_hash[:8]} in the filename and did. This is good!")
            puml(f"#CDFFC8:Checksum matches portion of the filename {firmware};\n")
            set_firmware_hash_validity(True)
        else:
            print(f"WARNING: Expected to match {firmware_hash[:8]} in the filename but didn't, please double check to make sure the checksum is good.")
            puml("#orange:Unable to match the checksum in the filename;\n")
            set_firmware_hash_validity(False)

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
                    self.config.firmware_is_ota = False
            except Exception as e:
                set_firmware_model(None)
                set_firmware_id(filename)
        set_ota(self, self.config.firmware_is_ota)
        if get_firmware_id():
            set_flash_button_state(self)
        else:
            self.flash_button.Disable()
        populate_boot_list(self)
        self.update_widget_states()
        return firmware_hash
    else:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {firmware} is not a valid archive file.")
        puml("#red:The selected firmware is not valid;\n")
        self.config.firmware_path = None
        self.firmware_picker.SetPath('')
        return 'Select Pixel Firmware'


# ============================================================================
#                               Function process_file
# ============================================================================
def process_file(self, file_type):
    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}         Processing {file_type} file ...")
    print("==============================================================================")
    puml(f"#cyan:Process {file_type};\n", True)
    config_path = get_config_path()
    path_to_7z = get_path_to_7z()
    boot_images = os.path.join(config_path, get_boot_images_dir())
    tmp_dir_full = os.path.join(config_path, 'tmp')
    con = get_db()
    con.execute("PRAGMA foreign_keys = ON")
    con.commit()
    cursor = con.cursor()
    start_1 = time.time()
    checksum = ''
    is_odin = False
    is_init_boot = False
    is_stock_boot = False

    is_payload_bin = False
    factory_images = os.path.join(config_path, 'factory_images')
    if file_type == 'firmware':
        is_stock_boot = True
        file_to_process = self.config.firmware_path
        puml(f"note right:{file_to_process}\n")
        package_sig = get_firmware_id()
        package_dir_full = os.path.join(factory_images, package_sig)
        found_flash_all_bat = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="flash-all.bat", nested=False)
        found_flash_all_sh = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="flash-all.sh", nested=False)
        found_boot_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="boot.img", nested=True)
        found_init_boot_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="init_boot.img", nested=True)
        found_vbmeta_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="vbmeta.img", nested=True)
        found_boot_img_lz4 = ''
        set_firmware_has_init_boot(False)
        set_ota(self, False)
        if found_init_boot_img:
            set_firmware_has_init_boot(True)
            is_init_boot = True
        if found_flash_all_bat and found_flash_all_sh and get_firmware_hash_validity():
            # assume Pixel factory file
            print("Detected Pixel firmware")
            image_file_path = os.path.join(package_dir_full, f"image-{package_sig}.zip")
            # Unzip the factory image
            debug(f"Unzipping Image: {file_to_process} into {package_dir_full} ...")
            theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{factory_images}\" \"{file_to_process}\""
            debug(theCmd)
            res = run_shell2(theCmd)
        elif found_boot_img or found_init_boot_img:
            print(f"Detected Non Pixel firmware, with: {found_boot_img} {found_init_boot_img}")
            # Check if the firmware file starts with image-* and warn the user or abort
            firmware_file_name = os.path.basename(file_to_process)
            if firmware_file_name.startswith('image-'):
                title = "Possibly extracted firmware."
                message =  f"WARNING: It looks like you have extracted the firmware file.\nand selected the image zip from it.\n\n"
                message += f"You should not extract the file, please select the downloaded firmware file instead\n\n"
                message += f"If this is not the case, and you want to continue with this selection\n"
                message += "Click OK to accept and continue.\n"
                message += "or Hit CANCEL to abort."
                print(f"\n*** Dialog ***\n{message}\n______________\n")
                puml("#orange:WARNING;\n", True)
                puml(f"note right\n{message}\nend note\n")
                dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
                result = dlg.ShowModal()
                if result != wx.ID_OK:
                    print("User pressed cancel.")
                    puml("#pink:User Pressed Cancel to abort;\n")
                    print("Aborting ...\n")
                    return
                print("User pressed ok.")
                puml(":User Pressed OK to continue;\n")
            image_file_path = file_to_process
        elif check_zip_contains_file(file_to_process, "payload.bin", get_low_memory()):
            is_payload_bin = True
            set_ota(self, True)
            if get_firmware_hash_validity() and get_ota():
                print("Detected OTA file")
            else:
                print("Detected a firmware, with payload.bin")
        else:
            # -------------------------
            # Samsung firmware handling
            # -------------------------
            # Get file list from zip
            file_list = get_zip_file_list(file_to_process)
            patterns = {
                'AP': 'AP_*.tar.md5',
                'BL': 'BL_*.tar.md5',
                'HOME_CSC': 'HOME_CSC_*.tar.md5',
                'CSC': 'CSC_*.tar.md5',
            }
            found_ap = ''
            found_bl = ''
            found_csc = ''
            found_home_csc = ''
            # see if we find AP_*.tar.md5, if yes set is_samsung flag
            for file in file_list:
                if not found_ap and fnmatch.fnmatch(file, patterns['AP']):
                    # is_odin = 1
                    is_odin = True
                    print(f"Found {file} file.")
                    found_ap = file
                if not found_bl and fnmatch.fnmatch(file, patterns['BL']):
                    print(f"Found {file} file.")
                    found_bl = file
                if not found_home_csc and fnmatch.fnmatch(file, patterns['HOME_CSC']):
                    print(f"Found {file} file.")
                    found_home_csc = file
                if not found_csc and fnmatch.fnmatch(file, patterns['CSC']):
                    print(f"Found {file} file.")
                    found_csc = file

            # TODO check settings, see if offer samsung extraction options is enabled
            # if yes, offer list of found files to extract
            if found_ap:
                # assume Samsung firmware
                print("Detected Samsung firmware")
                image_file_path = os.path.join(package_dir_full, found_ap)
                # Unzip the factory image
                debug(f"Unzipping Image: {file_to_process} into {package_dir_full} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{package_dir_full}\" \"{file_to_process}\""
                debug(theCmd)
                res = run_shell2(theCmd)
                # see if there is boot.img.lz4 in AP file
                found_boot_img_lz4 = check_archive_contains_file(archive_file_path=image_file_path, file_to_check="boot.img.lz4", nested=False)
                if found_boot_img_lz4:
                    print(f"Extracting boot.img.lz4 from {found_ap} ...")
                    puml(f":Extract boot.img.lz4;\n")
                    theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{package_dir_full}\" \"{image_file_path}\" boot.img.lz4"
                    debug(f"{theCmd}")
                    res = run_shell(theCmd)
                    # expect ret 0
                    if res.returncode != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract boot.img.lz4")
                        print(res.stderr)
                        puml("#red:ERROR: Could not extract boot.img.lz4;\n")
                        print("Aborting ...\n")
                        return
                    else:
                        # unpack boot.img.lz4
                        print("Unpacking boot.img.lz4 ...")
                        puml(f":Unpack boot.img.lz4;\n")
                        unpack_lz4(os.path.join(package_dir_full, 'boot.img.lz4'), os.path.join(package_dir_full, 'boot.img'))
                        # Check if it exists
                        if os.path.exists(os.path.join(package_dir_full, 'boot.img')):
                            found_boot_img = 'boot.img'
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not unpack boot.img.lz4")
                            puml("#red:ERROR: Could not unpack boot.img.lz4;\n")
                            print("Aborting ...\n")
                            return
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find boot.img.lz4")
                    puml("#red:ERROR: Could not find boot.img.lz4;\n")
                    print("Aborting ...\n")
                    return
            else:
                print("Detected Unsupported firmware file.")
                print("Aborting ...")
                return
    else:
        file_to_process = self.config.custom_rom_path
        found_boot_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="boot.img", nested=False)
        found_init_boot_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="init_boot.img", nested=False)
        found_vbmeta_img = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="vbmeta.img", nested=False)
        set_rom_has_init_boot(False)
        if found_init_boot_img:
            set_rom_has_init_boot(True)
            is_init_boot = True
        elif check_zip_contains_file(file_to_process, "payload.bin", get_low_memory()):
            print("Detected a ROM, with payload.bin")
            is_payload_bin = True
        package_sig = get_custom_rom_id()
        package_dir_full = os.path.join(factory_images, package_sig)
        image_file_path = file_to_process
        puml(f"note right:{image_file_path}\n")

    # delete all files in tmp folder to make sure we're dealing with new files only.
    delete_all(tmp_dir_full)

    if is_payload_bin:
        # extract the payload.bin into a temporary directory
        is_stock_boot = True
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = temp_dir.name
        print(f"Extracting payload.bin from {file_to_process} ...")
        puml(":Extract payload.bin;\n")
        theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{file_to_process}\" payload.bin"
        debug(f"{theCmd}")
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract payload.bin.")
            print(res.stderr)
            puml("#red:ERROR: Could not extract payload.bin;\n")
            print("Aborting ...\n")
            return
        # extract boot.img, init_boot.img, vbmeta.img from payload.bin, ...
        payload_file_path = os.path.join(temp_dir_path, "payload.bin")
        if not os.path.exists(package_dir_full):
            os.makedirs(package_dir_full, exist_ok=True)
        if self.config.extra_img_extracts:
            extract_payload(payload_file_path, out=package_dir_full, diff=False, old='old', images='boot,vbmeta,init_boot,dtbo,super_empty,vendor_boot,vendor_kernel_boot')
            if os.path.exists(os.path.join(package_dir_full, 'dtbo.img')):
                dtbo_img_file = os.path.join(package_dir_full, 'dtbo.img')
                shutil.copy(dtbo_img_file, os.path.join(tmp_dir_full, 'dtbo.img'), follow_symlinks=True)
            if os.path.exists(os.path.join(package_dir_full, 'super_empty.img')):
                super_empty_img_file = os.path.join(package_dir_full, 'super_empty.img')
                shutil.copy(super_empty_img_file, os.path.join(tmp_dir_full, 'super_empty.img'), follow_symlinks=True)
            if os.path.exists(os.path.join(package_dir_full, 'vendor_boot.img')):
                vendor_boot_img_file = os.path.join(package_dir_full, 'vendor_boot.img')
                shutil.copy(vendor_boot_img_file, os.path.join(tmp_dir_full, 'vendor_boot.img'), follow_symlinks=True)
            if os.path.exists(os.path.join(package_dir_full, 'vendor_kernel_boot.img')):
                vendor_kernel_boot_img_file = os.path.join(package_dir_full, 'vendor_kernel_boot.img')
                shutil.copy(vendor_kernel_boot_img_file, os.path.join(tmp_dir_full, 'vendor_kernel_boot.img'), follow_symlinks=True)
        else:
            extract_payload(payload_file_path, out=package_dir_full, diff=False, old='old', images='boot,vbmeta,init_boot')
        if os.path.exists(os.path.join(package_dir_full, 'boot.img')):
            boot_img_file = os.path.join(package_dir_full, 'boot.img')
            shutil.copy(boot_img_file, os.path.join(tmp_dir_full, 'boot.img'), follow_symlinks=True)
            boot_file_name = 'boot.img'
        if os.path.exists(os.path.join(package_dir_full, 'init_boot.img')):
            boot_img_file = os.path.join(package_dir_full, 'init_boot.img')
            shutil.copy(boot_img_file, os.path.join(tmp_dir_full, 'init_boot.img'), follow_symlinks=True)
            boot_file_name = 'init_boot.img'
            found_init_boot_img = 'True' # This is intentionally a string, all we care is for it to not evalute to False
            is_init_boot = True
    else:
        if is_odin:
            shutil.copy(os.path.join(package_dir_full, 'boot.img'), os.path.join(tmp_dir_full, 'boot.img'), follow_symlinks=True)
        if not os.path.exists(image_file_path):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The firmware file did not have the expected structure / contents.")
            if file_type == 'firmware':
                print(f"Please check {self.config.firmware_path} to make sure it is a valid factory image file.")
                puml("#red:The selected firmware is not valid;\n")
            print("Aborting ...\n")
            return

        files_to_extract = ''
        if found_boot_img:
            boot_file_name = 'boot.img'
            files_to_extract += 'boot.img '
        if found_init_boot_img:
            boot_file_name = 'init_boot.img'
            files_to_extract += 'init_boot.img '
            is_init_boot = True
        if found_vbmeta_img:
            files_to_extract += 'vbmeta.img '
        files_to_extract = files_to_extract.strip()

        if not is_odin:
            if not files_to_extract:
                print(f"Nothing to extract from {file_type}")
                print("Aborting ...")
                puml("#red:Nothing to extract from {file_type};\n")
                return

            print(f"Extracting {boot_file_name} from {image_file_path} ...")
            puml(f":Extract {boot_file_name};\n")
            theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{tmp_dir_full}\" \"{image_file_path}\" {files_to_extract}"
            debug(f"{theCmd}")
            res = run_shell(theCmd)
            # expect ret 0
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {boot_file_name}.")
                print(res.stderr)
                puml(f"#red:ERROR: Could not extract {boot_file_name};\n")
                print("Aborting ...\n")
                return

    # sometimes the return code is 0 but no file to extract, handle that case.
    # also handle the case of extraction from payload.bin
    boot_img_file = os.path.join(tmp_dir_full, boot_file_name)
    if not os.path.exists(boot_img_file):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {boot_file_name}, ")
        print(f"Please make sure the file: {image_file_path} has {boot_file_name} in it.")
        puml(f"#red:ERROR: Could not extract {boot_file_name};\n")
        print("Aborting ...\n")
        return

    # get the checksum of the boot_file_name
    checksum = sha1(os.path.join(boot_img_file))
    print(f"sha1 of {boot_file_name}: {checksum}")
    puml(f"note right:sha1 of {boot_file_name}: {checksum}\n")

    # if a matching boot_file_name is not found, store it.
    cached_boot_img_dir_full = os.path.join(boot_images, checksum)
    cached_boot_img_path = os.path.join(cached_boot_img_dir_full, boot_file_name)
    print(f"Checking for cached copy of {boot_file_name}")
    if not os.path.exists(cached_boot_img_dir_full):
        os.makedirs(cached_boot_img_dir_full, exist_ok=True)
    if not os.path.exists(cached_boot_img_path):
        print(f"Cached copy of {boot_file_name} with sha1: {checksum} is not found.")
        print(f"Copying {boot_img_file} to {cached_boot_img_dir_full}")
        shutil.copy(boot_img_file, cached_boot_img_dir_full, follow_symlinks=True)
        if found_init_boot_img:
            # we need to copy boot.img for Pixel 7, 7P, 7a so that we can do live boot.
            shutil.copy(os.path.join(tmp_dir_full, 'boot.img'), cached_boot_img_dir_full, follow_symlinks=True)
    else:
        print(f"Found a cached copy of {file_type} {boot_file_name} sha1={checksum}")
    if found_vbmeta_img and os.path.exists(package_dir_full):
        # we copy vbmeta.img so that we can do selective vbmeta verity / verification patching.
        shutil.copy(os.path.join(tmp_dir_full, 'vbmeta.img'), package_dir_full, follow_symlinks=True)

    # Let's see if we have a record for the firmware/rom being processed
    print(f"Checking DB entry for PACKAGE: {file_to_process}")
    package_id = 0
    cursor.execute(f"SELECT ID, boot_hash FROM PACKAGE WHERE package_sig = '{package_sig}' AND file_path = '{file_to_process}'")
    data = cursor.fetchall()
    if len(data) > 0:
        package_id = data[0][0]
        print(f"Found a previous {file_type} PACKAGE record id={package_id} for package_sig: {package_sig} Firmware: {file_to_process}")
        print(f"Package ID: {package_id}")
    else:
        # create PACKAGE db record
        print(f"Creating DB entry for PACKAGE: {file_to_process}")
        sql = 'INSERT INTO PACKAGE (boot_hash, type, package_sig, file_path, epoch, full_ota ) values(?, ?, ?, ?, ?, ?) ON CONFLICT (file_path) DO NOTHING'
        data = checksum, file_type, package_sig, file_to_process, time.time(), self.config.firmware_is_ota
        try:
            cursor.execute(sql, data)
            con.commit()
            package_id = cursor.lastrowid
            print(f"Package ID: {package_id}")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
            print(e)

    # Let's see if we already have an entry for the BOOT
    print(f"Checking DB entry for BOOT: {checksum}")
    boot_id = 0
    cursor.execute(f"SELECT ID FROM BOOT WHERE boot_hash = '{checksum}'")
    data = cursor.fetchall()
    if len(data) > 0:
        boot_id = data[0][0]
        print(f"Found a previous BOOT record id={boot_id} for boot_hash: {checksum}")
        print(f"Boot_ID: {boot_id}")
    else:
        # create BOOT db record
        print(f"Creating DB entry for BOOT: {checksum}")
        sql = 'INSERT INTO BOOT (boot_hash, file_path, is_patched, magisk_version, hardware, epoch, patch_method, is_odin, is_stock_boot, is_init_boot) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (boot_hash) DO NOTHING'
        data = checksum, cached_boot_img_path, 0, '', '', time.time(), '', is_odin, is_stock_boot, is_init_boot
        try:
            cursor.execute(sql, data)
            con.commit()
            boot_id = cursor.lastrowid
            print(f"Boot ID: {boot_id}")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
            print(e)

    # Let's see if we already have an entry for the PACKAGE_BOOT
    print(f"Checking DB entry for PACKAGE_BOOT: package_id = '{package_id}' AND boot_id = '{boot_id}")
    cursor.execute(f"SELECT package_id, boot_id FROM PACKAGE_BOOT WHERE package_id = '{package_id}' AND boot_id = '{boot_id}'")
    data = cursor.fetchall()
    if len(data) > 0:
        package_boot_id = data[0][0]
        print(f"Found a previous PACKAGE_BOOT record for package_id: {package_id},  boot_id: {boot_id}")
        print(f"Package_Boot row id: {package_boot_id}")
    else:
    # create PACKAGE_BOOT db record
        print(f"Creating PACKAGE_BOOT record, package_id: {package_id} boot_id: {boot_id}")
        sql = 'INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch) values(?, ?, ?) ON CONFLICT (package_id, boot_id) DO NOTHING'
        data = package_id, boot_id, time.time()
        try:
            cursor.execute(sql, data)
            con.commit()
            package_boot_id = cursor.lastrowid
            print(f"Package_Boot row id: {package_boot_id}")
        except Exception as e:
            print(f"Record PACKAGE_BOOT record, package_id: {package_id} boot_id: {boot_id} already exists")

    set_db(con)
    populate_boot_list(self)
    end_1 = time.time()
    print(f"Process {file_type} time: {math.ceil(end_1 - start_1)} seconds")
    print("------------------------------------------------------------------------------\n")


# ============================================================================
#                               Function process_flash_all_file
# ============================================================================
def process_flash_all_file(filepath):
    cwd = os.getcwd()
    flash_file_lines = []
    with open(filepath) as fp:
        #1st line, platform
        line = fp.readline()
        if line[:9] == "@ECHO OFF":
            filetype = 'bat'
        elif line[:9] == "#!/bin/sh":
            filetype = 'sh'
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unexpected first line: {line} in file: {filepath}")
        flash = FlashFile(1, platform = filetype, type = "init", command = line.strip())
        flash_file_lines.append(flash)

        cnt = 1
        in_if_block = False
        if_block_data = ''
        while line:
            line = fp.readline()

            #---------------------------------
            # Line that should not be captured
            if line.strip() == '':
                # blank line, ignore it
                continue
            elif line[:2] == "::":
                # comment line windows, ignore it
                continue
            elif line[:1] == "#":
                # comment line Linux, ignore it
                continue
            elif line[:10] == "pause >nul":
                # pause line, ignore it
                continue
            elif line[:4] == "exit":
                # exit line, ignore it
                continue
            elif line[:26] == "echo Press any key to exit":
                # exit line, ignore it
                continue

            #-----------------------
            # line that are relevant
            elif line[:4] == "if !":
                # if line to check fastboot version, grab it differently (all as one block)
                in_if_block = True
                if_block_data += line
                continue
            elif line[:7] == "  echo ":
                # part of the previous if, grab it differently (all as one block)
                if in_if_block:
                    if_block_data += line
                continue
            elif line[:6] == "  exit":
                # part of the previous if, grab it differently (all as one block)
                if in_if_block:
                    if_block_data += line
                continue
            elif line[:2] == "fi":
                # part of the previous if, grab it differently (all as one block)
                if in_if_block:
                    if_block_data += line
                in_if_block = False
                flash = FlashFile(cnt, platform = filetype, type = "if_block", command = if_block_data.strip())
                flash_file_lines.append(flash)
                continue
            elif line[:5] == "PATH=":
                flash = FlashFile(cnt, platform = filetype, type = "path", command = line.strip())
                flash_file_lines.append(flash)
                continue

            elif line[:5] == "ping " or line[:6] == "sleep ":
                flash = FlashFile(cnt, platform = filetype, type = "sleep", command = line.strip())
                flash_file_lines.append(flash)
                continue

            elif line[:8] == "fastboot":
                parts = line.split()
                if parts[1] == 'flash':
                    flash = FlashFile(cnt, platform = filetype, type = "fastboot", command = "fastboot", action = "flash", arg1 = parts[2], arg2 = parts[3])
                    flash_file_lines.append(flash)
                    continue
                elif parts[1] == 'reboot-bootloader':
                    flash = FlashFile(cnt, platform = filetype, type = "fastboot", command = "fastboot", action = "reboot-bootloader")
                    flash_file_lines.append(flash)
                    continue
                elif parts[1] == '-w' and parts[2] == 'update':
                    flash = FlashFile(cnt, platform = filetype, type = "fastboot", command = "fastboot", action = "-w update", arg1 = parts[3])
                    flash_file_lines.append(flash)
                    continue
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR! Encountered an unexpected fastboot line while parsing {filepath}")
                    print(line)
                    return "ERROR"

            #-----------------
            # Unexpected lines
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR! Encountered an unexpected line while parsing {filepath}")
                print(line)
                return "ERROR"

            cnt += 1
        return flash_file_lines


# ============================================================================
#                               Function ui_action
# ============================================================================
def ui_action(device, dump_file, local_file, look_for):
    # Get uiautomator dump of view1
    # the_view = "view1.xml"
    res = device.uiautomator_dump(dump_file)
    if res == -1:
        puml("#red:Failed to uiautomator dump;\n}\n")
        return -1

    # Pull dump_file
    print(f"Pulling {dump_file} from the phone to: {local_file} ...")
    res = device.pull_file(dump_file, local_file)
    if res != 0:
        puml("#red:Failed to pull uiautomator dump from the phone;\n}\n")
        return -1

    # get bounds
    coords = get_ui_cooridnates(local_file, look_for)

    # Check for Display being locked again
    if not device.is_display_unlocked():
        print("ERROR: The device display is Locked!\n")
        return -1

    # Click on coordinates
    res = device.click(coords)
    if res == -1:
        puml("#red:Failed to click;\n}\n")
        return -1

    # Sleep 2 seconds
    print("Sleeping 2 seconds to make sure the view is loaded ...")
    time.sleep(2)

    # Check for Display being locked again
    if not device.is_display_unlocked():
        print("ERROR: The device display is Locked!\n")
        return -1


# ============================================================================
#                               Function drive_magisk (TODO)
# ============================================================================
def drive_magisk(self, boot_file_name):
    print("UI Automator is broken, until Google fixes it, this feature is disabled.")
    return -1
    # start = time.time()
    # print("")
    # print("==============================================================================")
    # print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Driving Magisk ")
    # print("==============================================================================")

    # device = get_phone()
    # config_path = get_config_path()

    # if not device.is_display_unlocked():
    #     title = "Display is Locked!"
    #     message =  "ERROR: Your phone display is Locked.\n\n"
    #     message += "Make sure you unlock your display\n"
    #     message += "And set the display timeout to at least 1 minute.\n\n"
    #     message += "After doing so, Click OK to accept and continue.\n"
    #     message += "or Hit CANCEL to abort."
    #     print(f"\n*** Dialog ***\n{message}\n______________\n")
    #     dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
    #     result = dlg.ShowModal()
    #     if result == wx.ID_OK:
    #         print("User pressed ok.")
    #         if not device.is_display_unlocked():
    #             print("ERROR: The device display is still Locked!\nAborting ...\n")
    #             return -1
    #     else:
    #         print("User pressed cancel.")
    #         print("Aborting ...\n")
    #         return -1

    # # First stop magisk in case it is running
    # device.stop_magisk()

    # # Launch Magisk
    # device.perform_package_action(get_magisk_package(), 'launch', False)

    # res = ui_action(device, f"{self.config.phone_path}/view1.xml", os.path.join(config_path, 'tmp', 'view1.xml'), "Install")
    # if res == -1:
    #     return -1

    # res = ui_action(device, f"{self.config.phone_path}/view2.xml", os.path.join(config_path, 'tmp', 'view2.xml'), "Select and Patch a File")
    # if res == -1:
    #     return -1

    # res = ui_action(device, f"{self.config.phone_path}/view3.xml", os.path.join(config_path, 'tmp', 'view3.xml'), "Search this phone")
    # if res == -1:
    #     return -1

    # res = ui_action(device, f"{self.config.phone_path}/view4.xml", os.path.join(config_path, 'tmp', 'view4.xml'), "LET'S GO")
    # if res == -1:
    #     return -1

    # res = ui_action(device, f"{self.config.phone_path}/view5.xml", os.path.join(config_path, 'tmp', 'view5.xml'), "com.topjohnwu.magisk:id/action_save")
    # if res == -1:
    #     return -1

    # # TODO
    # return -1
    # # # Get uiautomator dump of view1
    # # the_view = "view1.xml"
    # # dump_file = f"{self.config.phone_path}/{the_view}"
    # # res = device.uiautomator_dump(dump_file)
    # # if res == -1:
    # #     print("Aborting ...\n")
    # #     puml("#red:Failed to uiautomator dump;\n}\n")
    # #     return -1

    # # # Pull view1.xml
    # # view_file = os.path.join(config_path, 'tmp', the_view)
    # # print(f"Pulling {dump_file} from the phone to: {view_file} ...")
    # # res = device.pull_file(dump_file, view_file)
    # # if res != 0:
    # #     print("Aborting ...\n")
    # #     puml("#red:Failed to pull uiautomator dump from the phone;\n}\n")
    # #     return

    # # # get view1 bounds / click coordinates
    # # coords = get_ui_cooridnates(view_file, "Install")

    # # # Check for Display being locked again
    # # if not device.is_display_unlocked():
    # #     print("ERROR: The device display is Locked!\nAborting ...\n")
    # #     return -1

    # # # # Click on coordinates of `Install`
    # # # # For Pixel 6 this would be: adb shell input tap 830 417
    # # # theCmd = f"\"{get_adb()}\" -s {device.id} shell input tap {coords}"
    # # # debug(theCmd)
    # # # res = run_shell(theCmd)

    # # # Click on coordinates of `Install`
    # # # For Pixel 6 this would be: adb shell input tap 830 417
    # # res = device.click(coords)
    # # if res == -1:
    # #     print("Aborting ...\n")
    # #     puml("#red:Failed to click;\n}\n")
    # #     return -1

    # # # Sleep 2 seconds
    # # print("Sleeping 2 seconds to make sure the view is loaded ...")
    # # time.sleep(2)

    # # # Check for Display being locked again
    # # if not device.is_display_unlocked():
    # #     print("ERROR: The device display is Locked!\nAborting ...\n")
    # #     return -1

    # # Get uiautomator dump of view2
    # dump_file = f"{self.config.phone_path}/view2.xml"
    # res = device.uiautomator_dump(dump_file)
    # if res == -1:
    #     print("Aborting ...\n")
    #     puml("#red:Failed to uiautomator dump;\n}\n")
    #     return -1

    # # Pull view2.xml
    # view2 = os.path.join(config_path, 'tmp', 'view2.xml')
    # print(f"Pulling {dump_file} from the phone to: {view2} ...")
    # res = device.pull_file(dump_file, view2)
    # if res != 0:
    #     print("Aborting ...\n")
    #     puml("#red:Failed to pull uiautomator dump from the phone;\n}\n")
    #     return

    # # Pull view2.xml
    # view2 = os.path.join(config_path, 'tmp', 'view2.xml')
    # print(f"Pulling {self.config.phone_path}/view2.xml from the phone ...")
    # theCmd = f"\"{get_adb()}\" -s {device.id} pull {self.config.phone_path}/view2.xml \"{view2}\""
    # debug(theCmd)
    # res = run_shell(theCmd)
    # # expect ret 0
    # if res.returncode == 1:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull {view2} from phone.")
    #     print(res.stderr)
    #     print("Aborting ...\n")
    #     return -1

    # # get view2 bounds / click coordinates
    # coords = get_ui_cooridnates(view2, "Select and Patch a File")

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Click on coordinates of `Select and Patch a File`
    # # For Pixel 6 this would be: adb shell input tap 540 555
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input tap {coords}"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 2 seconds
    # print("Sleeping 2 seconds to make sure the view is loaded ...")
    # time.sleep(2)

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Get uiautomator dump of view3
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell uiautomator dump {self.config.phone_path}/view3.xml"
    # debug(theCmd)
    # res = run_shell(theCmd)
    # if res.returncode != 0:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: uiautomator dump failed.")
    #     print(res.stderr)
    #     return -1

    # # Pull view3.xml
    # view3 = os.path.join(config_path, 'tmp', 'view3.xml')
    # print(f"Pulling {self.config.phone_path}/view3.xml from the phone ...")
    # theCmd = f"\"{get_adb()}\" -s {device.id} pull {self.config.phone_path}/view3.xml \"{view3}\""
    # debug(theCmd)
    # res = run_shell(theCmd)
    # # expect ret 0
    # if res.returncode == 1:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull {view3} from phone.")
    #     print(res.stderr)
    #     print("Aborting ...\n")
    #     return -1

    # # get view3 bounds / click coordinates
    # coords = get_ui_cooridnates(view3, "Search this phone")

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Click on coordinates of `Search this phone`
    # # For Pixel 6 this would be: adb shell input tap 574 210
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input tap {coords}"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 2 seconds
    # print("Sleeping 2 seconds to make sure the view is loaded ...")
    # time.sleep(2)

    # # Type the boot_file_name to search for it
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input text {boot_file_name}"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 1 seconds
    # print("Sleeping 1 seconds to make sure the view is loaded ...")
    # time.sleep(1)

    # # Hit Enter to search
    # print("Hitting Enter to search")
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input keyevent 66"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 1 seconds
    # print("Sleeping 1 seconds to make sure the view is loaded ...")
    # time.sleep(1)

    # # Hit Enter to Select it
    # print("Hitting Enter to select")
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input keyevent 66"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 2 seconds
    # print("Sleeping 2 seconds to make sure the view is loaded ...")
    # time.sleep(2)

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Get uiautomator dump of view4
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell uiautomator dump {self.config.phone_path}/view4.xml"
    # debug(theCmd)
    # res = run_shell(theCmd)
    # if res.returncode != 0:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: uiautomator dump failed.")
    #     print(res.stderr)
    #     return -1

    # # Pull view4.xml
    # view4 = os.path.join(config_path, 'tmp', 'view4.xml')
    # print(f"Pulling {self.config.phone_path}/view4.xml from the phone ...")
    # theCmd = f"\"{get_adb()}\" -s {device.id} pull {self.config.phone_path}/view4.xml \"{view4}\""
    # debug(theCmd)
    # res = run_shell(theCmd)
    # # expect ret 0
    # if res.returncode == 1:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull {view4} from phone.")
    #     print(res.stderr)
    #     print("Aborting ...\n")
    #     return -1

    # # get view4 bounds / click coordinates
    # coords = get_ui_cooridnates(view4, "LET'S GO")

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Click on coordinates of `LET'S GO`
    # # For Pixel 6 this would be: adb shell input tap 839 417
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input tap {coords}"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # Sleep 2 seconds
    # print("Sleeping 2 seconds to make sure the view is loaded ...")
    # time.sleep(2)

    # # Sleep 10 seconds
    # print("Sleeping 10 seconds to make sure Patching is completed ...")
    # time.sleep(10)

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Get uiautomator dump of view5
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell uiautomator dump {self.config.phone_path}/view5.xml"
    # debug(theCmd)
    # res = run_shell(theCmd)
    # if res.returncode != 0:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: uiautomator dump failed.")
    #     print(res.stderr)
    #     return -1

    # # Pull view5.xml
    # view5 = os.path.join(config_path, 'tmp', 'view5.xml')
    # print(f"Pulling {self.config.phone_path}/view5.xml from the phone ...")
    # theCmd = f"\"{get_adb()}\" -s {device.id} pull {self.config.phone_path}/view5.xml \"{view5}\""
    # debug(theCmd)
    # res = run_shell(theCmd)
    # # expect ret 0
    # if res.returncode == 1:
    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull {view5} from phone.")
    #     print(res.stderr)
    #     print("Aborting ...\n")
    #     return -1

    # # get view5 bounds / click coordinates (Save button)
    # coords = get_ui_cooridnates(view5, "com.topjohnwu.magisk:id/action_save")

    # # Check for Display being locked again
    # if not device.is_display_unlocked():
    #     print("ERROR: The device display is Locked!\nAborting ...\n")
    #     return -1

    # # Click on coordinates of `com.topjohnwu.magisk:id/action_save`
    # # For Pixel 6 this would be: adb shell input tap 1010 198
    # theCmd = f"\"{get_adb()}\" -s {device.id} shell input tap {coords}"
    # debug(theCmd)
    # res = run_shell(theCmd)

    # # get view5 bounds / click coordinates (All Done)
    # coords = None
    # coords = get_ui_cooridnates(view5, "- All done!")
    # if coords:
    #     print("\nIt looks liks Patching was successful.")
    # else:
    #     print("\nIt looks liks Patching was not successful.")

    # end = time.time()
    # print(f"Magisk Version: {device.magisk_version}")
    # print(f"Driven Patch time: {math.ceil(end - start)} seconds")
    # print("------------------------------------------------------------------------------\n")


# ============================================================================
#                               Function manual_magisk
# ============================================================================
def manual_magisk(self, boot_file_name):
    start = time.time()
    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Manual Patching ")
    print("==============================================================================")

    device = get_phone()

    if not device.is_display_unlocked():
        title = "Display is Locked!"
        message =  "ERROR: Your phone display is Locked.\n\n"
        message += "Make sure you unlock your display\n"
        message += "And set the display timeout to at least 1 minute.\n\n"
        message += "After doing so, Click OK to accept and continue.\n"
        message += "or Hit CANCEL to abort."
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            print("User pressed ok.")
            if not device.is_display_unlocked():
                print("ERROR: The device display is still Locked!\nAborting ...\n")
                return -1
        else:
            print("User pressed cancel.")
            print("Aborting ...\n")
            return -1

    # First stop magisk in case it is running
    device.stop_magisk()

    # Launch Magisk
    device.perform_package_action(self.config.magisk, 'launch', False)

    # Message Dialog Here to Patch Manually
    title = "Manual Patching"
    buttons_text = ["Done creating the patch, continue", "Cancel"]
    message = '''
## Magisk should now be running on your phone

_If it is not, you  can try starting in manually._

Please follow these steps in Magisk.

- Click on **Install** or **Upgrade** in the section under **Magisk** block (Not App)
- Click on **Select and patch a file**
'''
    message += f"- Select `{boot_file_name}` in `{self.config.phone_path}` \n"
    message += '''
- Then hit **Let's go**

When done creating the patch in Magisk <br/>
Click on **Done creating the patch, continue** button <br/>
or hit the **Cancel** button to abort.

'''
    dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=buttons_text, default_button=1, disable_buttons=[], is_md=True, size=[800,400])
    dlg.CentreOnParent(wx.BOTH)
    result = dlg.ShowModal()
    dlg.Destroy()
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
    if result == 2:
        print("Aborting ...")
        return -1
    # find the newly created file and return
    theCmd = f"\"{get_adb()}\" -s {device.id} shell ls -t {self.config.phone_path}/magisk_patched-* | head -1"
    res = run_shell(theCmd)
    if res.returncode == 0 and res.stderr == '':
        return os.path.basename(res.stdout.strip())
    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {res.stdout}\n{res.stderr}\n")
    return -1


# ============================================================================
#                               Function patch_boot_img
# ============================================================================
def patch_boot_img(self, custom_patch = False):
    recovery = 'false'
    custom_text = ""
    if custom_patch:
        custom_text = "Custom "
    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Patching {custom_text}boot")
    print("==============================================================================")
    puml(f"#cyan:Create {custom_text}Patch;\n", True)
    puml("partition \"**Create Patch**\" {\n")

    # get device
    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
        print("Aborting ...\n")
        puml("#red:Valid device is not selected;\n}\n")
        return
    else:
        print(f"Patching on device: {device.hardware}")

    if custom_patch:
        with wx.FileDialog(self, "boot / init_boot image to create patch from.", '', '', wildcard="Images (*.*.img)|*.img", style=wx.FD_OPEN) as fileDialog:
            puml(":Select boot image to patch;\n")
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled backup creation.")
                puml("#pink:User Cancelled;\n}\n")
                return
            # save the current contents in the file
            file_to_patch = fileDialog.GetPath()
            file_sha1 = sha1(file_to_patch)
            print(f"\nSelected {file_to_patch} for patching with SHA1 of {file_sha1}")
            puml(f"note right\nSelected {file_to_patch} for patching with SHA1 of {file_sha1}\nend note\n")
    else:
        # Make sure boot image is selected
        if not self.config.boot_id:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select a boot image.")
            print("Aborting ...\n")
            puml("#red:Valid boot image is not selected;\n}\n")
            return

    # Make sure platform-tools is set and adb and fastboot are found
    if not self.config.platform_tools_path:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select Android Platform Tools (ADB)")
        print("Aborting ...\n")
        puml("#red:Valid Anroid Platform Tools is not selected;\n}\n")
        return

    # Make sure the phone is in adb mode.
    if device.mode != 'adb':
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device: {device.id} is not in adb mode.")
        print("Perhaps a Scan is necessary?")
        print("Aborting ...\n")
        puml("#red:Device is not in ADB mode;\n}\n")
        return

    start = time.time()

    config_path = get_config_path()
    factory_images = os.path.join(config_path, 'factory_images')
    if custom_patch:
        boot_path = file_to_patch
        boot_file_name = os.path.basename(boot_path)
        filename, extension = os.path.splitext(boot_file_name)
        stock_sha1 = file_sha1[:8]
        boot_img = f"{filename}_{stock_sha1}.img"
        magisk_patched_img = f"magisk_patched_{file_sha1[:8]}.img"
        package_dir_full = os.path.join(factory_images, get_firmware_id())
        is_odin = 0
    else:
        boot = get_boot()
        boot_path = boot.boot_path
        boot_file_name = os.path.basename(boot_path)
        filename, extension = os.path.splitext(boot_file_name)
        stock_sha1 = boot.boot_hash[:8]
        boot_img = f"{filename}_{stock_sha1}.img"
        magisk_patched_img = f"magisk_patched_{boot.boot_hash[:8]}.img"
        package_dir_full = os.path.join(factory_images, boot.package_sig)
        is_odin = boot.is_odin
    boot_images = os.path.join(config_path, get_boot_images_dir())
    tmp_dir_full = os.path.join(config_path, 'tmp')

    # delete all files in tmp folder to make sure we're dealing with new files only.
    delete_all(tmp_dir_full)

    # check if boot_file_name got extracted (if not probably the zip does not have it)
    if not os.path.exists(boot_path):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You have selected the Patch option, however boot file is not found.")
        puml("#red:Cannot patch an already patched file;\n")
        print("Aborting ...\n}\n")
        return

    if not custom_patch:
        # Extract phone model from boot.package_sig and warn the user if it is not from the current phone model
        package_sig = boot.package_sig.split("-")
        try:
            firmware_model = package_sig[0]
        except Exception as e:
            firmware_model = None
        if not (len(device.hardware) >= 3 and device.hardware in firmware_model):
            title = "Boot Model Mismatch"
            message =  f"WARNING: Your phone model is: {device.hardware}\n\n"
            message += f"The selected {boot_file_name} is from: {boot.package_sig}\n\n"
            message += f"Please make sure the {boot_file_name} file you are trying to patch,\n"
            message += f"is for the selected device: {device.id}\n\n"
            message += "Click OK to accept and continue.\n"
            message += "or Hit CANCEL to abort."
            print(f"\n*** Dialog ***\n{message}\n______________\n")
            puml("#orange:WARNING;\n", True)
            puml(f"note right\n{message}\nend note\n")
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
                puml(":User Pressed OK to continue;\n")
            else:
                print("User pressed cancel.")
                puml("#pink:User Pressed Cancel to abort;\n}\n")
                print("Aborting ...\n")
                return

    # delete existing boot_img from phone
    res = device.delete(f"{self.config.phone_path}/{boot_img}")
    if res != 0:
        print("Aborting ...\n")
        puml("#red:Failed to delete old boot image from the phone;\n}\n")
        return

    # check if delete worked.
    print("Making sure file is not on the phone ...")
    res, tmp = device.check_file(f"{self.config.phone_path}/{boot_img}")
    if res != 0:
        print("Aborting ...\n")
        puml("#red:Failed to delete old boot image from the phone;\n}\n")
        return

    # delete existing magisk_patched from phone
    res = device.delete(f"{self.config.phone_path}/magisk_patched*.img")
    if res != 0:
        puml("#red:Failed to delete old magisk_patched.img;\n")
        print("Aborting ...\n}\n")
        return

    # check if delete worked.
    print("Making sure file is not on the phone ...")
    res, tmp = device.check_file(f"{self.config.phone_path}/magisk_patched*.img")
    if res != 0:
        puml("#red:Failed to delete old magisk_patched.img;\n")
        print("Aborting ...\n}\n")
        return

    # Transfer boot image to the phone
    res = device.push_file(f"{boot_path}", f"{self.config.phone_path}/{boot_img}")
    if res != 0:
        puml("#red:Failed to transfer the boot file to the phone;\n")
        print("Aborting ...\n}\n")
        return

    # check if transfer worked.
    res, tmp = device.check_file(f"{self.config.phone_path}/{boot_img}")
    if res != 1:
        print("Aborting ...\n")
        puml("#red:Failed to transfer the boot file to the phone;\n}\n")
        return

    #------------------------------------
    # Check to see if Magisk is installed
    #------------------------------------
    print("Looking for Magisk Manager app ...")
    puml(":Checking Magisk Manager;\n")
    magisk_app_version = device.get_uncached_magisk_app_version()
    magisk_version = device.magisk_version
    is_rooted = device.rooted

    # If the device is not reporting rooted, and adb shell access is not granted
    # Display a warning and abort.
    if self.config.magisk not in ['', 'com.topjohnwu.magisk', 'io.github.vvb2060.magisk', 'io.github.huskydg.magisk'] and not is_rooted:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: It looks like you have a hidden Magisk Manager, and have not allowed root access to adb shell")
        print("Patching can not be performed, to correct this, either grant root access to adb shell (recommended) or unhide Magisk Manager.")
        print("And try again.")
        print("Aborting ...\n")
        puml("#red:Hidden Magisk and root isnot granted;\n}\n")
        return

    # ==========================================
    # Sub Function       patch_script
    # ==========================================
    def patch_script(patch_method):
        print("Creating pf_patch.sh script ...")
        if self.config.use_busybox_shell:
            # busybox_shell_cmd = "export ASH_STANDALONE=1; /data/adb/magisk/busybox ash"
            busybox_shell_cmd = "/data/adb/magisk/busybox ash"
        else:
            busybox_shell_cmd = ""
        if patch_method == "rooted":
            patch_label = "rooted Magisk"
            script_path = "/data/adb/magisk/pf_patch.sh"
            exec_cmd = f"\"{get_adb()}\" -s {device.id} shell \"su -c \'cd /data/adb/magisk; {busybox_shell_cmd} ./pf_patch.sh\'\""
            with_version = device.magisk_version
            with_version_code = device.magisk_version_code
            perform_as_root = True
        elif patch_method == "app":
            patch_label = "Magisk App"
            path_to_busybox = os.path.join(get_bundle_dir(),'bin', f"busybox_{device.architecture}")
            script_path = "/data/local/tmp/pf_patch.sh"
            if is_rooted:
                exec_cmd = f"\"{get_adb()}\" -s {device.id} shell \"su -c \'{busybox_shell_cmd} /data/local/tmp/pf_patch.sh\'\""
            else:
                exec_cmd = f"\"{get_adb()}\" -s {device.id} shell {busybox_shell_cmd} /data/local/tmp/pf_patch.sh"
            with_version = device.get_uncached_magisk_app_version()
            with_version_code = device.magisk_app_version_code
            perform_as_root = False
        elif patch_method == "other":
            patch_label = "Other Magisk App"
            path_to_busybox = os.path.join(get_bundle_dir(),'bin', f"busybox_{device.architecture}")
            script_path = "/data/local/tmp/pf_patch.sh"
            exec_cmd = f"\"{get_adb()}\" -s {device.id} shell {busybox_shell_cmd} /data/local/tmp/pf_patch.sh"
            perform_as_root = False
            # select the Magisk to use for patching
            with wx.FileDialog(self, "Select Magisk Application", '', '', wildcard="Images (*.*.apk)|*.apk", style=wx.FD_OPEN) as fileDialog:
                puml(":Other Magisk Application for patch use ;\n")
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    print("User cancelled.")
                    puml("#pink:User Cancelled;\n")
                    return -1
                other_magisk = fileDialog.GetPath()
                print(f"\nSelected {other_magisk} for patch use.")
                puml(f"note right\nSelected {other_magisk} for patch use.\nend note\n")
            # Transfer user Magisk app to the phone
            res = device.push_file(f"\"{other_magisk}\"", '/sdcard/Download/Magisk-Uploaded.apk', with_su=perform_as_root)
            if res != 0:
                print("Aborting ...\n")
                puml("#red:Failed to transfer Magisk Application to the phone;\n")
                return -1
            with_version = "Other"
            with_version_code = "Other"
        else:
            print(f"ERROR: Unsupported patch method: {patch_method}")
            puml("#red:Unsupported patch method;\n")
            return -1

        set_patched_with(with_version)
        puml(f":Patching with {patch_label}: {with_version};\n", True)

        dest = os.path.join(config_path, 'tmp', 'pf_patch.sh')
        with open(dest.strip(), "w", encoding="ISO-8859-1", errors="replace", newline='\n') as f:
            data = " #!/system/bin/sh\n"
            data += " ##############################################################################\n"
            data += f" # PixelFlasher {VERSION} patch script using {patch_label} {with_version}\n"
            data += " ##############################################################################\n"
            data += f"MAGISK_VERSION=\"{with_version_code}\"\n"
            data += f"STOCK_SHA1={stock_sha1}\n"
            data += f"RECOVERYMODE={recovery}\n"
            if patch_method == "other":
                magisk_path = '/sdcard/Download/Magisk-Uploaded.apk'
            else:
                magisk_path = device.magisk_path
            data += f"MAGISK_PATH={magisk_path}\n"

            if patch_method == "app" or patch_method == "other":
                data += f"ARCH={device.architecture}\n"
                data += f"cp {magisk_path} /data/local/tmp/pf.zip\n"
                data += "cd /data/local/tmp\n"
                data += "rm -rf pf\n"
                data += "mkdir pf\n"
                data += "cd pf\n"
                data += "../busybox unzip -o ../pf.zip\n"
                data += "cd assets\n"
                data += "for FILE in ../lib/$ARCH/lib*.so; do\n"
                data += "    NEWNAME=$(echo $FILE | sed -En 's/.*\/lib(.*)\.so/\\1/p')\n"
                data += "    cp $FILE $NEWNAME\n"
                data += "done\n"
                if device.architecture == "x86_64":
                    data += "cp ../lib/x86/libmagisk32.so magisk32\n"
                elif device.architecture == "arm64-v8a" and (device.ro_zygote != "zygote64" or "zygote64_32" in with_version.lower()):
                    data += "cp ../lib/armeabi-v7a/libmagisk32.so magisk32\n"
                data += "chmod 755 *\n"
                data += "if [[ -f \"/data/local/tmp/pf/assets/magisk32\" ]]; then\n"
                data += "    PATCHING_MAGISK_VERSION=$(/data/local/tmp/pf/assets/magisk32 -c)\n"
                data += "    echo \"PATCHING_MAGISK_VERSION: $PATCHING_MAGISK_VERSION\"\n"
                data += "elif [[ -f \"/data/local/tmp/pf/assets.magisk64\" ]]; then\n"
                data += "    PATCHING_MAGISK_VERSION=$(/data/local/tmp/pf/assets/magisk64 -c)\n"
                data += "    echo \"PATCHING_MAGISK_VERSION: $PATCHING_MAGISK_VERSION\"\n"
                data += "fi\n"

            data += "SYSTEM_ROOT=false\n"
            data += "SYSTEM_AS_ROOT=false\n"
            data += "grep \' / \' /proc/mounts | grep -qv \'rootfs\' && SYSTEM_ROOT=true\n"
            data += "grep \' / \' /proc/mounts | grep -qv \'rootfs\' && SYSTEM_AS_ROOT=true\n"
            data += ". ./util_functions.sh\n"
            data += 'get_flags\n'
            data += "echo -------------------------\n"
            data += "echo \"SYSTEM_ROOT:       $SYSTEM_ROOT\"\n"
            data += "echo \"SYSTEM_AS_ROOT:    $SYSTEM_AS_ROOT\"\n"
            data += "echo \"KEEPVERITY:        $KEEPVERITY\"\n"
            data += "echo \"KEEPFORCEENCRYPT:  $KEEPFORCEENCRYPT\"\n"
            data += "echo \"RECOVERYMODE:      $RECOVERYMODE\"\n"
            data += "echo \"PATCHVBMETAFLAG:   $PATCHVBMETAFLAG\"\n"
            data += "echo \"ISENCRYPTED:       $ISENCRYPTED\"\n"
            data += "echo \"VBMETAEXIST:       $VBMETAEXIST\"\n"
            data += "echo \"LEGACYSAR:         $LEGACYSAR\"\n"
            data += "export KEEPVERITY KEEPFORCEENCRYPT RECOVERYMODE PATCHVBMETAFLAG ISENCRYPTED VBMETAEXIST SYSTEM_ROOT SYSTEM_AS_ROOT LEGACYSAR\n"
            data += "echo -------------------------\n"
            data += "echo \"Creating a patch ...\"\n"
            data += "./magiskboot cleanup\n"
            data += f"./boot_patch.sh /sdcard/Download/{boot_img}\n"
            data += "PATCH_SHA1=$(./magiskboot sha1 new-boot.img | cut -c-8)\n"
            data += "echo \"PATCH_SHA1:     $PATCH_SHA1\"\n"
            data += "PATCH_FILENAME=magisk_patched_${MAGISK_VERSION}_${STOCK_SHA1}_${PATCH_SHA1}.img\n"
            data += "echo \"PATCH_FILENAME: $PATCH_FILENAME\"\n"

            if patch_method == "app" or patch_method == "other":
                data += "cp -f /data/local/tmp/pf/assets/new-boot.img /sdcard/Download/${PATCH_FILENAME}\n"
                # if we're rooted, copy the stock boot.img to /data/adb/magisk/stock_boot.img so that magisk can backup
                if perform_as_root:
                    data += "cp -f /data/local/tmp/pf/assets/stock_boot.img /data/adb/magisk/stock_boot.img\n"
                    # TODO see if we need to update the config SHA1
            else:
                data += "mv new-boot.img /sdcard/Download/${PATCH_FILENAME}\n"

            data += "if [[ -s /sdcard/Download/${PATCH_FILENAME} ]]; then\n"
            data += "	echo $PATCH_FILENAME > /data/local/tmp/pf_patch.log\n"
            data += "	if [[ -n \"$PATCHING_MAGISK_VERSION\" ]]; then echo $PATCHING_MAGISK_VERSION >> /data/local/tmp/pf_patch.log; fi\n"
            data += "else\n"
            data += "	echo \"ERROR: Patching failed!\"\n"
            data += "fi\n\n"
            data += "echo \"Cleaning up ...\"\n"
            # intentionally not including \n
            data += "rm -f /data/local/tmp/pf_patch.sh"

            if patch_method == "app" or patch_method == "other":
                data += " /data/local/tmp/pf.zip /data/local/tmp/new-boot.img /data/local/tmp/busybox\n"
                data += "rm -rf /data/local/tmp/pf\n"
            data += "\n"

            f.write(data)
            puml(f"note right\nPatch Script\n====\n{data}\nend note\n")

        print("PixelFlasher patching script contents:")
        print(f"___________________________________________________\n{data}")
        print("___________________________________________________\n")

        # Transfer extraction script to the phone
        res = device.push_file(f"{dest}", script_path, with_su=perform_as_root)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to transfer Patch Script to the phone;\n")
            return -1

        # set the permissions.
        res = device.set_file_permissions(script_path, "755", perform_as_root)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to set the executable bit on patch script;\n")
            return -1

        if patch_method == "app" or patch_method == "other":
            # Transfer busybox to the phone
            res = device.push_file(f"{path_to_busybox}", "/data/local/tmp/busybox")
            if res != 0:
                print("Aborting ...\n")
                puml("#red:Failed to transfer busybox to the phone;\n")
                return -1

            # set the permissions.
            res = device.set_file_permissions("/data/local/tmp/busybox", "755")
            if res != 0:
                print("Aborting ...\n")
                puml("#red:Failed to set the executable bit on busybox;\n")
                return -1

        #------------------------------------
        # Execute the pf_patch.sh script
        #------------------------------------
        print("Executing the pf_patch.sh script ...")
        print(f"PixelFlasher Patching phone with {patch_label}: {with_version}")
        puml(":Executing the patch script;\n")
        debug(f"exec_cmd: {exec_cmd}")
        res = run_shell2(exec_cmd)

        # get the patched_filename
        print("Checking patch log: /data/local/tmp/pf_patch.log ...")
        res = device.file_content("/data/local/tmp/pf_patch.log")
        if res == -1:
            print("Aborting ...\n")
            puml("#red:Failed to pull pf_patch.log from the phone;\n")
            return -1
        else:
            lines = res.split("\n")
            magisk_patched_img = lines[0] if len(lines) > 0 else ""
            if patch_method == "other":
                set_patched_with(lines[1]) if len(lines) > 1 else ""

        # delete pf_patch.log from phone
        res = device.delete("/data/local/tmp/pf_patch.log", perform_as_root)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to delete pf_patch.log from the phone;\n")
            return -1

        return magisk_patched_img

    # -------------------------------
    # Patching decision
    # -------------------------------
    m_version = 0
    m_app_version = 0
    with contextlib.suppress(Exception):
        m_version = int(magisk_version.split(':')[1])
    with contextlib.suppress(Exception):
        m_app_version = int(magisk_app_version.split(':')[1])
    print(f"  Magisk Manager Version: {m_app_version}")
    print(f"  Magisk Version:         {m_version}")
    puml(f"note right\nMagisk Manager Version: {m_app_version}\nMagisk Version:         {m_version}\nend note\n")

    # Temporary workaround for rooted Magisk Delta, don't ever recommend it.
    if is_rooted and self.config.magisk != 'io.github.huskydg.magisk':
        method = 1  # rooted
        # disable app method if app is not found or is hidden.
        if not magisk_app_version or ( self.config.magisk not in ['', 'com.topjohnwu.magisk', 'io.github.vvb2060.magisk', 'io.github.huskydg.magisk'] ):
            disabled_buttons = [2, 3, 4]
        elif magisk_version and magisk_app_version:
            disabled_buttons = [3]
            if magisk_version != magisk_app_version:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Magisk Version is different than Magisk Manager version")
                puml("#orange:WARNING: Magisk Version is different than Magisk Manager version;\n")
                if m_version < m_app_version:
                    method = 2  # app
    elif magisk_app_version:
        method = 2  # app
        disabled_buttons = [1, 3]
    else:
        disabled_buttons = [1, 3]
        print("Unable to find magisk on the phone, perhaps it is hidden?")
        puml("#orange:Magisk not found;\n")
        # Message to Launch Manually and Patch
        title = "Magisk Manager is not detected."
        message =  f"WARNING: Magisk Manager [{self.config.magisk}] is not found on the phone\n\n"
        message += "This could be either because it is hidden, or it is not installed (most likely not installed)\n\n"
        message += "If it is installed and hidden, then you should abort and then unhide it.\n"
        message += "If Magisk is not installed, PixelFlasher can install it for you and use it for patching.\n\n"
        message += "WARNING: Do not install Magisk again if it is currently hidden.\n"
        message += "Do you want PixelFlasher to download and install Magisk?\n"
        message += "You will be given a choice of Magisk Version to install.\n\n"
        message += "Click OK to continue with Magisk installation.\n"
        message += "or Hit CANCEL to abort."
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        puml(f"note right\nDialog\n====\n{message}\nend note\n")
        dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            # ok to download and install
            print("User pressed ok.")
            puml(":User Pressed OK;\nnote right:Proceed to Magisk download and install\n")
            dlg = MagiskDownloads(self)
            dlg.CentreOnParent(wx.BOTH)
            result = dlg.ShowModal()
            if result != wx.ID_OK:
                # User cancelled out of Magisk Installation
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel, out of Magisk download and install.")
                puml(":User Pressed Cancel;\n}\n")
                print("Aborting ...\n")
                dlg.Destroy()
                return
            dlg.Destroy()
            try:
                magisk_app_version = device.get_uncached_magisk_app_version()
                if magisk_app_version:
                    # Magisk Manager is installed
                    print(f"Found Magisk Manager version {magisk_app_version} on the phone.")
                    puml(f":Found Magisk Manager;\nnote right:version {magisk_app_version}\n", True)
                    method = 2  # app
                else:
                    print("Magisk Manager is still not detected.\n\Aborting ...\n")
                    puml("#red:Magisk Manager is still not detected;\nnote right:Abort\n}\n", True)
                    return
            except Exception:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed Magisk is still not detected.")
                puml("#red:Magisk Manager is still not detected;\nnote right:Abort\n}\n", True)
                print("Aborting ...\n")
                return
        else:
            # not ok to download and install, (Magisk is hidden option)
            print("User pressed cancel for downloading and installing Magisk.")
            puml(":User Pressed Cancel;\n}\n")
            print("Aborting ...\n")
            return

    # -------------------------------
    # Call the patch option
    # Let the user select with Guidance
    # -------------------------------
    if self.config.offer_patch_methods:
        title = "Patching decision"
        buttons_text = ["Use Rooted Magisk", "Use Magisk Application", "Use UIAutomator", "Manual", "Other Magisk", "Cancel"]
        buttons_text[method -1] += " (Recommended)"
        if self.config.show_recovery_patching_option:
            checkboxes=["Recovery"]
        else:
            checkboxes=None

        message = '''
**PixelFlasher** can create a patch by utilizing different methods.<br/>

This is a summary of available methods.<br/>

1. If already rooted, and root access is granted to adb, PixelFlasher can utilize magisk in /data/adb/magisk (core Magisk) and create a patch without user interaction.<br/>

2. If Magisk application is not hidden, PixelFlasher can unpack it and utilize it to create a patch without user interaction.<br/>

3. PixelFlasher can programatically control (using UIAutomator) the user interface of the installed Magisk and click on buttons to create a patch.
   This method is not supported on all phones, and is prone to problems due to timing issues, screen being locked, or user interacting with the screen while PixelFlasher is creating a patch.
   This method is usually not recommended.<br/>

4. PixelFlasher can transfer the stock file to /sdcard/Download/ (can be customized), Launch Magisk, and prompt the user to select the file and create a patch.
   PixelFlasher will wait for the user to complete the task and then hit OK to continue.
   This method involves user interaction hence it is also not recommended, and it is only kept for power users.<br/>

5. PixelFlasher can create a patch from a Magisk App (apk) that you select and provide without installing the app.
   This is handy when you want to create a patch using Magisk that is different than what is currently installed.
   One common usecase would be when you want to create a patch with an older version of Magisk.

Depending on the state of your phone (root, Magisk versions, Magisk hidden ...)
PixelFlasher will offer available choices and recommend the best method to utilize for patching.
Unless you know what you're doing, it is recommended that you take the default suggested selection.
'''
        message += f"<pre>Core Magisk Version:          {m_version}\n"
        message += f"Magisk Application Version:   {m_app_version}\n"
        message += f"Recommended Patch method:     Method {method}</pre>\n"
        clean_message = message.replace("<br/>", "").replace("</pre>", "").replace("<pre>", "")
        print(f"\n*** Dialog ***\n{clean_message}\n______________\n")
        puml(":Dialog;\n", True)
        puml(f"note right\n{clean_message}\nend note\n")
        dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=buttons_text, default_button=method, disable_buttons=disabled_buttons, is_md=True, size=[800,660], checkbox_labels=checkboxes)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()
        dlg.Destroy()
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
        puml(f":User Pressed {buttons_text[result - 1]};\n")

        method = result
        if method == 6:
            puml("}\n")
            print("Aborting ...\n")
            return
        checkbox_values = get_dlg_checkbox_values()
        if checkbox_values is not None:
            if checkbox_values[0]:
                recovery = 'true'
            else:
                recovery = 'false'
            print(f"Recovery: {recovery}")

    # Perform the patching
    if method == 1:
        patch_method = 'root'
        magisk_patched_img = patch_script("rooted")
    elif method == 2:
        patch_method = 'app'
        magisk_patched_img = patch_script("app")
    elif method == 3:
        patch_method = 'ui-auto'
        set_patched_with(device.magisk_app_version)
        magisk_patched_img = drive_magisk(self, boot_file_name=boot_img)
    elif method == 4:
        patch_method = 'manual'
        set_patched_with(device.magisk_app_version)
        magisk_patched_img = manual_magisk(self, boot_file_name=boot_img)
    elif method == 5:
        patch_method = 'other'
        set_patched_with("Other")
        magisk_patched_img = patch_script("other")
    else:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unexepected patch method.")
        puml("#red:Unexpected patch method;\nnote right:Abort\n}\n", True)
        print("Aborting ...\n")
        return
    if magisk_patched_img == -1:
        print("Aborting ...\n")
        puml("#red:Failed to patch\n}\n", True)
        return

    # -------------------------------
    # Validation Checks
    # -------------------------------
    # abort if patching failed
    if magisk_patched_img == -1:
        puml("}\n")
        return

    # check if magisk_patched_img got created.
    print(f"\nLooking for {magisk_patched_img} in {self.config.phone_path} ...")
    res, magisk_patched = device.check_file(f"{self.config.phone_path}/{magisk_patched_img}")
    if res != 1:
        print("Aborting ...\n")
        puml("#red:Failed to find magisk_patched on the phone;\n}\n")
        return

    # Transfer back magisk_patched.img
    print(f"Pulling {magisk_patched} from the phone to: {magisk_patched_img} ...")
    magisk_patched_img_file = os.path.join(tmp_dir_full, magisk_patched_img)
    res = device.pull_file(magisk_patched, f"\"{magisk_patched_img_file}\"")
    if res != 0:
        print("Aborting ...\n")
        puml("#red:Failed to pull magisk_patched from the phone;\n}\n")
        return

    # get the checksum of the magisk_patched.img
    print(f"Getting SHA1 of {magisk_patched_img_file} ...")
    checksum = sha1(os.path.join(magisk_patched_img_file))
    print(f"SHA1 of {magisk_patched_img} file: {checksum}")

    # get source boot_file_name sha1
    print(f"\nGetting SHA1 of source {boot_file_name} ...")
    boot_sha1_long = sha1(boot_path)
    boot_sha1 = boot_sha1_long[:8]
    print(f"Source {boot_file_name}'s SHA1 is: {boot_sha1_long}")

    # check to make sure the patch sha1 is not the same as the source (stock) sha1
    if checksum == boot_sha1_long:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Patching failed, magisk_patched SHA1 is the same as the stock SHA1")
        puml("#red:Patching failed;\nnote right:magisk_patched SHA1 is the same as the stock SHA1\n}\n", True)
        print("Aborting ...\n")
        return

    # if rooted, get magisk's stored sha1 from it's config.
    if is_rooted:
        print("Getting SHA1 from Magisk config ...")
        magisk_sha1 = device.magisk_sha1
        print(f"Magisk Config's SHA1 is:   {magisk_sha1}")
        # compare it to the original boot_file_name file's sha1
        # print(f"Comparing source {boot_file_name} SHA1 with Magisk's config SHA1 (they should match) ...")
        # if boot_sha1_long != magisk_sha1:
        #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Something is wrong Magisk config has the wrong SHA1 ...")
        #     # fix it
        #     # res = device.update_magisk_config(boot_sha1_long)
        # else:
        #     print(f"Good: Both SHA1s: {boot_sha1_long} match.")
        # see if we have a Magisk backup
        print(f"\nChecking to see if Magisk made a backup of the source {boot_file_name}")
        magisk_backups = device.magisk_backups
        if magisk_backups and boot_sha1_long in magisk_backups:
            print("Good: Magisk has made a backup")
            puml("#lightgreen:Magisk Backup: Success;\n")
        else:
            print(f"Magisk has NOT made a backup of the source {boot_file_name}")
            print("Triggering Magisk to create a backup ...")
            # Trigger Magisk to make a backup
            res = device.run_magisk_migration(boot_sha1_long)
            # if return is -2, then copy boot.img to stock_boot.img
            if res == -2 and is_rooted:
                # copy stock_boot from Downloads folder it already exists, and do it as su if rooted
                stock_boot_path = '/data/adb/magisk/stock_boot.img'
                print(f"Copying {boot_img} to {stock_boot_path} ...")
                res = device.su_cp_on_device(f"/sdcard/Download/{boot_img}", stock_boot_path)
                if res != 0:
                    print("Aborting Backup ...\n")
                else:
                    # rerun the migration.
                    print("Triggering Magisk migration again to create a backup ...")
                    res = device.run_magisk_migration(boot_sha1_long)
                    print(f"\nChecking to see if Magisk made a backup of the source {boot_file_name}")
                    magisk_backups = device.magisk_backups
                    if magisk_backups and boot_sha1_long in magisk_backups:
                        print("Good: Magisk has made a backup")
                        puml("#lightgreen:Magisk Backup: Success;\n")
                    else:
                        print("It looks like backup was not made.")

    # Extract sha1 from the patched image
    print(f"\nExtracting SHA1 from {magisk_patched_img} ...")
    puml(f":Extract from {magisk_patched_img};\n", True)
    patched_sha1 = extract_sha1(magisk_patched_img_file, 40)
    if patched_sha1:
        print(f"SHA1 embedded in {magisk_patched_img_file} is: {patched_sha1}")
        print(f"Comparing source {boot_file_name} SHA1 with SHA1 embedded in {patched_sha1} (they should match) ...")
        if patched_sha1 != boot_sha1_long:
            max_name_length = max(len(magisk_patched_img), len(boot_file_name))
            # Left justify the filenames with spaces
            padded_magisk_patched_img = magisk_patched_img.ljust(max_name_length)
            padded_boot_file_name = boot_file_name.ljust(max_name_length)
            print("\nNOTICE: The two SHA1s did not match.")
            print(f"        {padded_magisk_patched_img} extracted sha1: {patched_sha1}")
            print(f"        {padded_boot_file_name}           sha1: {boot_sha1_long}")
            print("This could be normal due to compression\nChecking match confidence level.")
            puml(f"#cyan:SHA1 mismatch;\n")
            puml(f"note right\n")
            puml(f"{padded_magisk_patched_img} extracted sha1: {patched_sha1}\n")
            puml(f"{padded_boot_file_name}           sha1: {boot_sha1_long}\n")
            puml("end note\n")
            confidence = compare_sha1(patched_sha1, boot_sha1_long)
            print(f"The confidence level is: {confidence * 100}%")
            puml(f":Confidence level: {confidence * 100}%;\n")
            if confidence < 0.5:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Something is wrong with the patched file SHA1, we got a low match confidence.\n")
                print("Please compare the two sha1 strings and decide for yourself if this is acceptable to use.")
                puml(f"#red:ERROR: Something is wrong with the patched file\nSHA1: {patched_sha1}\nExpected SHA1: {boot_sha1};\n", True)
                #return
            else:
                print("Acceptable!")
        else:
            print(f"Good: Both SHA1s: {patched_sha1} match.\n")
            puml(f"note right:SHA1 {patched_sha1} matches the expected value\n")
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} NOTICE: The patched image file does not contain source boot's SHA1")
        print("                            This is normal for older devices, but newer deviced should have it.")
        print("                            If you have a newer device, please double check if everything is ok.\n ")
        puml("#orange:The patched image file does not contain source boot's SHA1;\n")
        puml(f"note right\nThis is normal for older devices, but newer deviced should have it.\nend note\n")


    if not custom_patch:
        # if a matching magisk_patched.img is not found, store it.
        cached_boot_img_dir_full = os.path.join(boot_images, boot.boot_hash)
        cached_boot_img_path = os.path.join(cached_boot_img_dir_full, magisk_patched_img)
        debug(f"Checking for cached copy of {boot_file_name}")
        if not os.path.exists(cached_boot_img_path):
            debug(f"Cached copy of {magisk_patched_img} with sha1: {checksum} is not found.")
            debug(f"Copying {magisk_patched_img_file} to {cached_boot_img_dir_full}")
            shutil.copy(magisk_patched_img_file, cached_boot_img_dir_full, follow_symlinks=True)
        else:
            debug(f"Found a cached copy of magisk_patched.img sha1={checksum}\n")

        # create BOOT db record
        con = get_db()
        con.execute("PRAGMA foreign_keys = ON")
        con.commit()
        cursor = con.cursor()
        sql = 'INSERT INTO BOOT (boot_hash, file_path, is_patched, magisk_version, hardware, epoch, patch_method, is_odin, is_stock_boot, is_init_boot, patch_source_sha1) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (boot_hash) DO NOTHING'
        data = (checksum, cached_boot_img_path, 1, get_patched_with(), device.hardware, time.time(), patch_method, False, False, boot.is_init_boot, boot_sha1_long)
        debug(f"Creating BOOT record, boot_hash: {checksum}")
        try:
            cursor.execute(sql, data)
            con.commit()
            boot_id = cursor.lastrowid
            debug(f"DB BOOT record ID: {boot_id}")
        except Exception as e:
            boot_id = 0
        # if we didn't insert in BOOT, see if we have a record for the boot being processed in case we need to insert a record into PACKAGE_BOOT
        if boot_id == 0:
            cursor.execute(f"SELECT ID FROM BOOT WHERE boot_hash = '{checksum}'")
            data = cursor.fetchall()
            if len(data) > 0:
                boot_id = data[0][0]
                debug(f"Found a previous BOOT record id={boot_id} for boot_hash: {checksum}\n")
            else:
                boot_id = 0
                debug(f"ERROR: Something went wrong while inserting BOOT record id={boot_id} for boot_hash: {checksum}\n")

        # create PACKAGE_BOOT db record
        if boot.package_id > 0 and boot_id > 0:
            debug(f"Creating PACKAGE_BOOT record, package_id: {boot.package_id} boot_id: {boot_id}")
            sql = 'INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch) values(?, ?, ?) ON CONFLICT (package_id, boot_id) DO NOTHING'
            data = (boot.package_id, boot_id, time.time())
            try:
                cursor.execute(sql, data)
                con.commit()
                package_boot_id = cursor.lastrowid
                debug(f"DB Package_Boot record ID: {package_boot_id}\n")
            except Exception as e:
                package_boot_id = 0

        set_db(con)
    else:
        # Display save as dialog to save the patched file
        with wx.FileDialog(self, "Save Patched Magisk File", '', f"{magisk_patched_img}", wildcard="Image files (*.img)|*.img", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print(f"User Cancelled saving: {magisk_patched_img}")
                return     # the user changed their mind
            shutil.copy(magisk_patched_img_file, fileDialog.GetPath(), follow_symlinks=True)

    # if Samsung firmware, create boot.tar
    if is_odin == 1 or self.config.create_boot_tar:
        print(f"Creating boot.tar from patched boot.img ...")
        puml(f":Create boot.tar;\n")
        shutil.copy(magisk_patched_img_file, os.path.join(tmp_dir_full, 'boot.img'), follow_symlinks=True)
        create_boot_tar(tmp_dir_full)
        if os.path.exists(os.path.join(tmp_dir_full, 'boot.tar')):
            print("boot.tar file created.")
            print(f"copying boot.tar to {package_dir_full} directory ...")
            shutil.copy(os.path.join(tmp_dir_full, 'boot.tar'), os.path.join(package_dir_full, 'boot.tar'), follow_symlinks=True)
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create boot.tar file")
            puml("#red:ERROR: Could not create boot.tar;\n")

    end = time.time()
    print(f"\nMagisk Version: {get_patched_with()}")
    print(f"Patch time: {math.ceil(end - start)} seconds")
    print("------------------------------------------------------------------------------\n")
    puml(f"#cee7ee:End {custom_text}Patching;\n", True)
    puml(f"note right:Patch time: {math.ceil(end - start)} seconds\n")
    puml("}\n")

    populate_boot_list(self)


# ============================================================================
#                               Function live_flash_boot_phone
# ============================================================================
def live_flash_boot_phone(self, option):
    puml(f"#cyan:{option} Boot;\n", True)
    puml(f"partition \"**{option} Boot**\"")
    puml(" {\n")
    if not get_adb():
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android Platform Tools must be set.")
        puml("#red:Valid Anroid Platform Tools is not selected;\n}\n")
        return

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
        puml("#red:Valid device is not selected;\n}\n")
        return

    if device.hardware in KNOWN_INIT_BOOT_DEVICES and option == 'Live':
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Live booting Pixel 7 or Pixel 7p or Pixel 7a is not supported yet.")
        puml("#red:Live booting Pixel 7 or Pixel 7p or Pixel 7a is not supported yet;\n}\n")
        return

    boot = get_boot()
    if boot:
        if boot.is_patched:
            firmware_model = boot.hardware
        else:
            # Extract phone model from boot.package_sig
            package_sig_array = boot.package_sig.split("-")
            try:
                firmware_model = package_sig_array[0]
            except Exception as e:
                firmware_model = None
        # Warn the user if it is not from the current phone model
        if not (len(device.hardware) >= 3 and device.hardware in firmware_model):
            title = f"{option} Boot"
            message =  f"ERROR: Your phone model is: {device.hardware}\n\n"
            message += f"The selected Boot is for: {boot.hardware}\n\n"
            message += "Unless you know what you are doing, if you continue flashing\n"
            message += "you risk bricking your device, proceed only if you are absolutely\n"
            message += "certian that this is what you want, you have been warned.\n\n"
            message += "Click OK to accept and continue.\n"
            message += "or Hit CANCEL to abort."
            print(f"\n*** Dialog ***\n{message}\n______________\n")
            puml("#orange:WARNING;\n", True)
            puml(f"note right\n{message}\nend note\n")
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
                puml(":User Pressed OK to continue;\n")
            else:
                print("User pressed cancel.")
                puml("#pink:User Pressed Cancel to abort;\n}\n")
                print("Aborting ...\n")
                return
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to access boot object, aborting ...\n")
        puml("#red:Unable to access boot object\n}\n")
        return

    # Make sure boot exists
    if boot.boot_path:
        title = f"{option} Boot"
        message  = f"Live/Flash Boot Options:\n\n"
        message += f"Option:                 {option}\n"
        message += f"Boot Hash:              {boot.boot_hash}\n"
        message += f"Hardware:               {device.hardware}\n"
        if boot.is_patched == 1:
            message += "Patched:                Yes\n"
            message += f"With Magisk:            {boot.magisk_version}\n"
            if boot.patch_method:
                message += f"Patched Method:         {boot.patch_method}\n"
            message += f"Original boot.img from: {boot.package_sig}\n"
            message += f"Original boot.img Hash: {boot.package_boot_hash}\n"
        else:
            message += "Patched:                No\n"
        message += f"Custom Flash Options:   {self.config.advanced_options}\n"
        # don't allow inactive slot flashing
        message += "Flash To Inactive Slot: False\n"
        message += f"Flash Both Slots:       {self.config.flash_both_slots}\n"
        message += f"Verbose Fastboot:       {self.config.fastboot_verbose}\n"
        message += "boot.img path:\n"
        message += f"  {boot.boot_path}\n"
        message += "\nClick OK to accept and continue.\n"
        message += "or Hit CANCEL to abort."
        print(f"\n*** Dialog ***\n{message}\n______________\n")
        puml(f":{option} Boot;\n", True)
        puml(f"note right\nDialog\n====\n{message}\nend note\n")
        set_message_box_title(title)
        set_message_box_message(message)
        dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=['OK', 'CANCEL'], default_button=1)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()
        if result == 1:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
            puml(":User Pressed OK to continue;\n")
        else:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
            puml("#pink:User Pressed Cancel to abort;\n}\n")
            print("Aborting ...\n")
            dlg.Destroy()
            return
        dlg.Destroy()
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to get boot.img path, aborting ...\n")
        puml("#red:Unable to get boot image path;\n}\n")
        return

    if device.mode == 'adb':
        device.reboot_bootloader()
        print("Waiting 10 seconds ...")
        puml(":Sleep 10 seconds;\n")
        time.sleep(10)
        self.device_choice.SetItems(get_connected_devices())
        self._select_configured_device()

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to detect the device.")
        print("You can try scanning for devices and selecting your device (it should be in bootloader mode).")
        print(f"and then press the same {option} button again.")
        puml("#red:Valid device is not detected;\n")
        puml(f"note right\nYou can try scanning for devices and selecting your device (it should be in bootloader mode).\nand then press the same {option} button again.\nend note\n")
        puml("}\n")
        return

    if device.mode == 'f.b' and get_fastboot():
        startFlash = time.time()
        print("")
        print("==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Flashing / Live Booting\n     {boot.boot_path} ...")
        print("==============================================================================")
        puml(":Flashing / Live Booting;\n", True)
        puml(f"note right:File: {boot.boot_path};\n")
        # if device.hardware in KNOWN_INIT_BOOT_DEVICES:
        #     # Pixel 7 and 7P need a special command to Live Boot.
        #     # https://forum.xda-developers.com/t/td1a-220804-031-factory-image-zip-is-up-unlock-bootloader-root-pixel-7-pro-cheetah-limited-safetynet-all-relevant-links.4502805/post-87571843
        #     kernel = os.path.join(os.path.dirname(boot.boot_path), "boot.img")
        #     if os.path.exists(kernel):
        #         theCmd = f"\"{get_fastboot()}\" -s {device.id} boot \"{kernel}\" \"{boot.boot_path}\""
        #     else:
        #         print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Missing Kernel {kernel} ...\n")
        #         print(f"Aborting ...\n")
        #         return
        # else:
        fastboot_options = ''
        slot = ''
        if option == 'Flash':
            # don't allow inactive slot flashing
            # if self.config.flash_to_inactive_slot:
            #     fastboot_options += '--slot other '
            if self.config.advanced_options:
                if self.config.flash_both_slots:
                    fastboot_options += '--slot all '
                if self.config.fastboot_verbose:
                    fastboot_options += '--verbose '
            fastboot_options += 'flash '
        if device.hardware in KNOWN_INIT_BOOT_DEVICES:
            theCmd = f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} init_boot \"{boot.boot_path}\""
        else:
            theCmd = f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} boot \"{boot.boot_path}\""
        debug(theCmd)
        res = run_shell(theCmd)
        if res.returncode != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {option} boot failed!")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            print("Aborting ...\n")
            puml("#red:{option} Boot failed!;\n}\n")
            puml("}\n")
            return
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Done!")
        endFlash = time.time()
        print(f"Flashing elapsed time: {math.ceil(endFlash - startFlash)} seconds")
        print("------------------------------------------------------------------------------\n")
        done_flashing = True
        # clear the selected device option
        set_phone(None)
        self.device_label.Label = "ADB Connected Devices"
        self.config.device = None
        self.device_choice.SetItems([''])
        self.device_choice.Select(-1)
        # Live automatically reboots, so we can only control the Flash one.
        if option == 'Flash' and not self.config.no_reboot:
            puml(":Reboot to System;\n")
            device.reboot_system()
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device {device.id} not in bootloader mode.")
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Aborting ...\n")
        puml("#red:Device is not in bootloader mode;\n}\n")

    puml(f"#cee7ee:End {option} Boot;\n", True)
    if done_flashing:
        puml(f"note right:Flashing elapsed time: {math.ceil(endFlash - startFlash)} seconds\n")
    puml("}\n")
    return


# ============================================================================
#                               Function flash_phone
# ============================================================================
def flash_phone(self):
    puml("#cyan:Flash Firmware;\n", True)
    puml("partition \"**Flash Firmware**\" {\n")
    if not get_adb():
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android Platform Tools must be set.")
        puml("#red:Android Platform Tools is not set;\n}\n")
        return

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid adb device.")
        puml("#red:Valid device is not selected;\n}\n")
        return

    cwd = os.getcwd()
    config_path = get_config_path()
    factory_images = os.path.join(config_path, 'factory_images')

    if self.config.advanced_options and self.config.flash_mode == 'customFlash':
        image_mode = get_image_mode()
        package_dir_full = os.path.join(config_path, 'tmp')
    else:
        package_sig = get_firmware_id()
        if not package_sig:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a factory firmware file.")
            puml("#red:Factory firmware is not selected;\n}\n")
            return

        if (
            get_firmware_model() in ['raven', 'oriole', 'bluejay']
            and device.api_level
            and int(device.api_level) < 33
            and not (self.config.advanced_options and self.config.flash_both_slots)
        ):
            title = "Tensor device not on Android 13 or higher"
            message =  f"WARNING: Your phone OS version is lower than Android 13.\n\n"
            message += f"If you are upgrading to Android 13 or newer,\n"
            message += "make sure you at least flash the bootloader to both slots.\n"
            message += "The Android 13 update for Pixel 6, Pixel 6 Pro, and the Pixel 6a contains\n"
            message += "a bootloader update that increments the anti-roll back version for the bootloader.\n"
            message += "This prevents the device from rolling back to previous vulnerable versions of the bootloader.\n"
            message += "After flashing an Android 13 build on these devices\n"
            message += "you will not be able to flash and boot older Android 12 builds.\n\n"
            message += "Selecting the option 'Flash to both slots'\n"
            message += "Will take care of that.\n\n"
            message += "Click OK to continue as is.\n"
            message += "or Hit CANCEL to abort and change options."
            puml(":API < 33 and device is Tensor;\n")
            puml(f"note right\nDialog\n====\n{message}\nend note\n")
            print(f"\n*** Dialog ***\n{message}\n______________\n")
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
                puml(":User Pressed OK;\n")
            else:
                print("User pressed cancel.")
                print("Aborting ...\n")
                puml("#pink:User Pressed Cancel to abort;\n}\n")
                return

        package_dir_full = os.path.join(factory_images, package_sig)
        boot = get_boot()

    message = ''

    # if advanced options is set, and we have flash options ...
    fastboot_options = ''
    fastboot_options2 = ''
    sideload_options = ''
    if self.config.advanced_options:
        if self.config.flash_both_slots:
            fastboot_options += '--slot all '
        if self.config.disable_verity:
            fastboot_options += '--disable-verity '
            fastboot_options2 += '--disable-verity '
            sideload_options += '--disable-verity '
        if self.config.disable_verification:
            fastboot_options += '--disable-verification '
            fastboot_options2 += '--disable-verification '
            sideload_options += '--disable-verification '
        if self.config.fastboot_verbose:
            fastboot_options += '--verbose '
            fastboot_options2 += '--verbose '
            sideload_options += '--verbose '
        if self.config.fastboot_force:
            fastboot_options2 += '--force '
        if self.config.flash_mode == 'OTA':
            fastboot_options = sideload_options
        message = f"Custom Flash Options:   {self.config.advanced_options}\n"
        if self.config.flash_mode == 'customFlash' and image_mode == 'SIDELOAD':
            message += "   ATTENTION!           Flash Options Don\'t apply to Sideloading. (Except: No Reboot)\n"
        else:
            message = f"Custom Flash Options:   {self.config.advanced_options}\n"
            message += f"Disable Verity:         {self.config.disable_verity}\n"
            message += f"Disable Verification:   {self.config.disable_verification}\n"
            if self.config.flash_mode != 'OTA':
                message += f"Flash Both Slots:       {self.config.flash_both_slots}\n"
                message += f"Force:                  {self.config.fastboot_force}\n"
            message += f"Verbose Fastboot:       {self.config.fastboot_verbose}\n"
            message += f"Temporary Root:         {self.config.temporary_root}\n"
            message += f"No Reboot:              {self.config.no_reboot}\n"
            message += f"Wipe:                   {self.wipe}\n"
    if self.config.flash_mode != 'OTA':
        message += f"Flash To Inactive Slot: {self.config.flash_to_inactive_slot}\n"

    if sys.platform == "win32":
        flash_pf_file = os.path.join(package_dir_full, "flash-pf.bat")
        if self.config.force_codepage:
            cp = str(self.config.custom_codepage)
            if cp == '':
                cp = None
        else:
            cp = get_system_codepage()
        if cp:
            first_line = f"chcp {cp}\n@ECHO OFF\n"
        else:
            first_line = f"@ECHO OFF\n"
        if self.config.advanced_options and self.config.flash_mode == 'customFlash':
            version_sig = f":: This is a generated file by PixelFlasher v{VERSION}\n:: cd {package_dir_full}\n:: Android Platform Tools Version: {get_sdk_version()}\n\n"
        else:
            version_sig = f":: This is a generated file by PixelFlasher v{VERSION}\n:: cd {package_dir_full}\n:: pf_boot.img: {boot.boot_path}\n:: Android Platform Tools Version: {get_sdk_version()}\n\n"
    else:
        flash_pf_file = os.path.join(package_dir_full, "flash-pf.sh")
        first_line = "#!/bin/sh\n"
        if self.config.advanced_options and self.config.flash_mode == 'customFlash':
            version_sig = f"# This is a generated file by PixelFlasher v{VERSION}\n# cd {package_dir_full}\n# Android Platform Tools Version: {get_sdk_version()}\n\n"
        else:
            version_sig = f"# This is a generated file by PixelFlasher v{VERSION}\n# cd {package_dir_full}\n# pf_boot.img: {boot.boot_path}\n# Android Platform Tools Version: {get_sdk_version()}\n\n"

    # delete previous flash-pf.bat file if it exists
    if os.path.exists(flash_pf_file):
        os.remove(flash_pf_file)

    #-------------------------------
    # if we are in custom Flash mode
    #-------------------------------
    if self.config.advanced_options and self.config.flash_mode == 'customFlash':
        if self.config.flash_to_inactive_slot:
            fastboot_options += '--slot other '
        if image_mode and get_image_path():
            title = "Advanced Flash Options"
            # create flash-pf.bat based on the custom options.
            f = open(flash_pf_file.strip(), "w", encoding="ISO-8859-1", errors="replace")
            data = first_line
            if sys.platform == "win32":
                data += "PATH=%PATH%;\"%SYSTEMROOT%\System32\"\n"
            # Sideload
            if image_mode == 'SIDELOAD':
                msg  = "\nADB Sideload:           "
                data += f"\"{get_adb()}\" -s {device.id} sideload \"{get_image_path()}\"\n"
            else:
                data += version_sig
                if image_mode == 'image':
                    action = "update"
                    msg  = f"\nFlash {image_mode:<18}"
                elif image_mode == 'boot' and self.live_boot_radio_button.Value:
                    action = "boot"
                    msg  = "\nLive Boot to:           "
                    if device.hardware in KNOWN_INIT_BOOT_DEVICES:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Live booting Pixel 7 or Pixel 7p or Pixel 7a are not supported yet.")
                        puml("#orange:Live booting Pixel 7 or Pixel 7p or Pixel 7a are not supported yet;\n}\n")
                        return
                else:
                    action = f"flash {image_mode}"
                    msg  = f"\nFlash {image_mode:<18}"
                data += f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} {action} \"{get_image_path()}\"\n"
                if self.wipe:
                    data += "\necho wiping userdata ...\n"
                    data += f"\"{get_fastboot()}\" -s {device.id} -w\n"
                # only reboot if no_reboot is not selected
                if not self.config.no_reboot:
                    data += "\necho rebooting to system ...\n"
                    data += f"\"{get_fastboot()}\" -s {device.id} reboot"

            f.write(data)
            f.close()
            message += f"{msg}{get_image_path()}\n\n"
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: No image file is selected.")
            puml("#red:Image file is not selected;\n}\n")
            return

    #---------------------------
    # do the standard flash mode
    #---------------------------
    else:
        add_echo =''
        # check for boot file
        if not os.path.exists(boot.boot_path):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot file: {boot.boot_path} is not found.")
            print("Aborting ...\n")
            puml("#red:boot file is not found;\n}\n")
            return
        else:
            # copy boot file to package directory, but first delete an old one to be sure
            pf = os.path.join(package_dir_full, "pf_boot.img")
            if os.path.exists(pf):
                os.remove(pf)
            debug(f"Copying {boot.boot_path} to {pf}")
            shutil.copy(boot.boot_path, pf, follow_symlinks=True)
        if not os.path.exists(pf):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} boot file: {pf} is not found.")
            print("Aborting ...\n")
            puml("#red:boot file is not found;\n}\n")
            return

        # check for rom file (if not OTA)
        if self.config.custom_rom and self.config.advanced_options and self.config.flash_mode != 'OTA':
            if not os.path.exists(self.config.custom_rom_path):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: ROM file: {self.config.custom_rom_path} is not found.")
                print("Aborting ...\n")
                puml("#red:ROM file is not found;\n}\n")
                return
            else:
                # copy ROM file to package directory, but first delete an old one to be sure
                rom_file = ntpath.basename(self.config.custom_rom_path)
                set_custom_rom_file(rom_file)
                rom = os.path.join(package_dir_full, rom_file)
                if os.path.exists(rom):
                    os.remove(rom)
                debug(f"Copying {self.config.custom_rom_path} to {rom}")
                shutil.copy(self.config.custom_rom_path, rom, follow_symlinks=True)
            if not os.path.exists(rom):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ROM file: {rom} is not found.")
                print("Aborting ...\n")
                puml("#red:ROM file is not found;\n}\n")
                return

        # Make sure Phone model matches firmware model
        if not (len(device.hardware) >= 3 and device.hardware in get_firmware_model()):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android device model {device.hardware} does not match firmware Model {get_firmware_model()}")
            puml(f"#orange:Hardware does not match firmware;\n")
            puml(f"note right\nAndroid device model {device.hardware}\nfirmware Model {get_firmware_model()}\nend note\n")

            title = "Device / Firmware Mismatch"
            message =  f"ERROR: Your phone model is: {device.hardware}\n\n"
            message += f"The selected firmware is for: {get_firmware_model()}\n\n"
            message += "Unless you know what you are doing, if you continue flashing\n"
            message += "you risk bricking your device, proceed only if you are absolutely\n"
            message += "certian that this is what you want, you have been warned.\n\n"
            message += "Click OK to accept and continue.\n"
            message += "or Hit CANCEL to abort."
            print(f"\n*** Dialog ***\n{message}\n______________\n")
            puml(":Dialog;\n")
            puml(f"note right\n{message}\nend note\n")
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
                puml(":User Pressed OK;\n")
            else:
                print("User pressed cancel.")
                print("Aborting ...\n")
                puml("#pink:User Pressed Cancel to abort;\n}\n")
                return

        # ----------
        # If OTA
        # ----------
        if self.config.flash_mode == 'OTA':
            indent = "    "
            if sys.platform == "win32" and cp:
                data = "@echo off\n"
                data += "setlocal enabledelayedexpansion\n"
                data += f"chcp {cp}\n"
                data += f":: This is a generated file by PixelFlasher v{VERSION}\n"
                data += f":: cd {package_dir_full}\n"
                data += f":: pf_boot.img: {boot.boot_path}\n"
                data += f":: Android Platform Tools Version: {get_sdk_version()}\n\n"
                data += f"set \"ACTIVE_SLOT={device.active_slot}\"\n"
                data += "echo Current Active Slot is: [%ACTIVE_SLOT%]\n"
                sleep_line = "ping -n 5 127.0.0.1 >nul\n"

                slot_check_lines = "\necho Reading current slot value ...\n"
                slot_check_lines += f"for /f \"tokens=2 delims=: \" %%a in ('call \"{get_fastboot()}\" -s {device.id} getvar current-slot 2^>^&1 ^| findstr /c:\"current-slot\"') do (\n"
                slot_check_lines += "    set \"CURRENT_SLOT=%%a\"\n"
                slot_check_lines += ")\n"
                slot_check_lines += "echo Current slot: [%CURRENT_SLOT%]\n\n"
                slot_check_lines += "echo Comparing the current slot with the previous active slot ...\n"
                slot_check_lines += "if \"%CURRENT_SLOT%\"==\"%ACTIVE_SLOT%\" (\n"
                slot_check_lines += "    echo \"Current slot is the same as the previous slot.\"\n"
                slot_check_lines += "    echo \"It appears that OTA flashing did not properly switch slots.\"\n"
                slot_check_lines += "    echo \"Aborting ...\"\n"
                slot_check_lines += ") else (\n"
                slot_check_lines += "    echo \"Current slot has changed, this is good.\"\n"
            else:
                data = f"# This is a generated file by PixelFlasher v{VERSION}\n"
                data += f"# cd {package_dir_full}\n"
                data += f"# pf_boot.img: {boot.boot_path}\n"
                data += f"# Android Platform Tools Version: {get_sdk_version()}\n\n"
                sleep_line = "sleep 5\n"
                data += f"ACTIVE_SLOT=\"{device.active_slot}\"\n"
                data += "echo Current Active Slot is: [$ACTIVE_SLOT]\n"

                slot_check_lines = "\necho Reading current slot value ...\n"
                slot_check_lines += f"output=$(\"{get_fastboot()}\" -s {device.id} getvar current-slot 2>&1)\n"
                slot_check_lines += "CURRENT_SLOT=$(echo \"$output\" | grep -oP 'current-slot:\s*\K\S+')\n"
                slot_check_lines += "echo Current slot: [$CURRENT_SLOT]\n\n"
                slot_check_lines += "echo Comparing the current slot with the previous active slot ...\n"
                slot_check_lines += "if [ \"$CURRENT_SLOT\" = \"$ACTIVE_SLOT\" ]; then\n"
                slot_check_lines += "    echo \"Current slot is the same as the previous slot.\"\n"
                slot_check_lines += "    echo \"It appears that OTA flashing did not properly switch slots.\"\n"
                slot_check_lines += "    echo \"Aborting ...\"\n"
                slot_check_lines += "else\n"
                slot_check_lines += "    echo \"Current slot has changed, this is good.\"\n"

            data += f"\"{get_adb()}\" -s {device.id} sideload \"{self.config.firmware_path}\"\n"

        # ----------
        # If not OTA
        # ----------
        else:
            indent = ""
            # Check if the patch file is made by Magsik Zygote64_32
            if "zygote64_32" in boot.magisk_version.lower():
                # Check we have Magisk Zygote64_32 rooted system already
                warn = False
                if device.rooted:
                    # Warn if current firmware is the same as the one being flashed and wipe is not selected.
                    if device.build.lower() in package_sig and not self.config.flash_mode == 'Wipe':
                        warn = True
                elif not self.config.flash_mode == 'Wipe':
                    warn = True
                if warn:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Wipe is required.")
                    print("Aborting ...\n")
                    puml("#red:Error WARNING, wipe is required;\n}\n")
                    # dialog to accept / abort
                    title = "Wipe is required."
                    buttons_text = ["Continue Flashing (I know what I'm doing)", "Cancel (Recommended)"]
                    message = '''
The selected patch is created by [Magisk Zygote64_32](https://github.com/Namelesswonder/magisk-files).<br/>

**PixelFlasher** detected a condition where a wipe is necessary to avoid bootloops.<br/>
You can learn about it [here](https://forum.xda-developers.com/t/magisk-magisk-zygote64_32-enabling-32-bit-support-for-apps.4521029/post-88504869
) and [here](https://forum.xda-developers.com/t/magisk-magisk-zygote64_32-enabling-32-bit-support-for-apps.4521029/)<br/>

You have not selected the **Wipe Data** option.<br/>

It is strongly recomended that you Cancel and abort flashing, choose the **Wipe Data** option before continuing to flash.<br/>

If you insist to continue, you can press the **Continue** button, otherwise please press the **Cancel** button.<br/>
'''
                    clean_message = message.replace("<br/>", "")
                    print(f"\n*** Dialog ***\n{clean_message}\n______________\n")
                    puml(":Dialog;\n", True)
                    puml(f"note right\n{clean_message}\nend note\n")
                    dlg = MessageBoxEx(parent=self, title=title, message=message, button_texts=buttons_text, default_button=2, is_md=True, size=[700,400])
                    dlg.CentreOnParent(wx.BOTH)
                    result = dlg.ShowModal()
                    dlg.Destroy()
                    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
                    puml(f":User Pressed {buttons_text[result - 1]};\n")
                    if result == 2:
                        puml("}\n")
                        print("Aborting ...\n")
                        return

            # Process flash_all files
            flash_all_win32 = process_flash_all_file(os.path.join(package_dir_full, "flash-all.bat"))
            if (flash_all_win32 == 'ERROR'):
                print("Aborting ...\n")
                puml("#red:Error processing flash_all.bat file;\n}\n")
                return
            flash_all_linux = process_flash_all_file(os.path.join(package_dir_full, "flash-all.sh"))
            if (flash_all_linux == 'ERROR'):
                print("Aborting ...\n")
                puml("#red:Error processing flash_all.sh file;\n}\n")
                return
            s1 = ''
            s2 = ''
            for f in flash_all_win32:
                if f.sync_line:
                    s1 += f"{f.sync_line}\n"
            for f in flash_all_linux:
                if f.sync_line:
                    s2 += f"{f.sync_line}\n"
            # check to see if we have consistent linux / windows files
            if s1 != s2:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Found inconsistency between flash-all.bat and flash-all.sh files.")
                puml("#yellow:Found an inconsistency between bat and sh files;\n")
                debug(f"bat file:\n{s1}")
                debug(f"\nsh file\n{s2}\n")

            if sys.platform == "win32" and cp:
                data = f"chcp {cp}\n"
            else:
                data = ''
            if self.config.flash_mode == 'dryRun':
                add_echo = 'echo '

            if sys.platform == "win32":
                flash_all_file = flash_all_win32
            else:
                flash_all_file = flash_all_linux
            for f in flash_all_file:
                if f.type == 'init':
                    data += f"{f.full_line}\n"
                    if sys.platform == "win32":
                        data += f":: This is a generated file by PixelFlasher v{VERSION}\n"
                        data += f":: cd {package_dir_full}\n"
                        data += f":: pf_boot.img: {boot.boot_path}\n"
                        data += f":: Android Platform Tools Version: {get_sdk_version()}\n\n"
                    else:
                        data += f"# This is a generated file by PixelFlasher v{VERSION}\n"
                        data += f"# cd {package_dir_full}\n"
                        data += f"# pf_boot.img: {boot.boot_path}\n"
                        data += f"# Android Platform Tools Version: {get_sdk_version()}\n\n"
                    if self.config.flash_to_inactive_slot:
                        data += "\necho Switching active slot to the other ...\n"
                        data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} --set-active=other\n"
                    continue
                if f.type in ['sleep']:
                    sleep_line = f"{f.full_line}\n"
                    data += f"{f.full_line}\n"
                    continue
                if f.type in ['path']:
                    data += f"{f.full_line}\n"
                    continue
                if f.action == 'reboot-bootloader':
                    data += f"\"{get_fastboot()}\" -s {device.id} {f.action} {f.arg1} {f.arg2}\n"
                    continue
                if f.action == 'flash':
                    data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options} {f.action} {f.arg1} {f.arg2}\n"
                    continue
                if f.action == '-w update':
                    action = '--skip-reboot update'
                    arg1 = f.arg1
                    if self.config.flash_mode == 'wipeData':
                        action = '--skip-reboot -w update'
                    if self.config.custom_rom and self.config.advanced_options:
                        arg1 = f"\"{get_custom_rom_file()}\""
                    data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options2} {action} {arg1}\n"
                    # flash on each slot separately
                    # https://forum.xda-developers.com/t/psa-do-not-try-to-boot-into-the-old-slot-after-updating-only-one-slot-to-android-13-unlocking-the-pixel-6-pro-bootloader-central-repository.4352027/post-87309913
                    if self.config.advanced_options and self.config.flash_both_slots:
                        data += "\necho Switching active slot to the other ...\n"
                        data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} --set-active=other\n"
                        data += "\necho rebooting to bootloader ...\n"
                        data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} reboot bootloader\n"
                        data += "\necho Sleeping 5-10 seconds ...\n"
                        data += sleep_line
                        data += sleep_line
                        data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options2} {action} {arg1}\n"
                    # echo add testing of fastbootd mode if we are in dry run mode and sdk < 34
                    sdk_version_components = get_sdk_version().split('.')
                    sdk_major_version = int(sdk_version_components[0])
                    if self.config.flash_mode == 'dryRun' and sdk_major_version < 34:
                        data += "\necho This is a test for fastbootd mode ...\n"
                        data += "echo This process will wait for fastbootd indefinitly until it responds ...\n"
                        data += "echo WARNING! if your device does not boot to fastbootd PixelFlasher will hang and you would have to kill it.. ...\n"
                        data += "echo rebooting to fastbootd ...\n"
                        data += f"\"{get_fastboot()}\" -s {device.id} reboot fastboot\n"
                        data += "\necho It looks like fastbootd worked.\n"

        # ---------------
        # OTA and Factory
        # ---------------
        # add the boot.img flashing
        data += "\necho rebooting to bootloader ...\n"
        if self.config.flash_mode == 'OTA':
            data += f"\"{get_adb()}\" -s {device.id} reboot bootloader\n"
        else:
            data += f"\"{get_fastboot()}\" -s {device.id} reboot bootloader\n"
        data += "\necho Sleeping 5-10 seconds ...\n"
        data += sleep_line
        data += sleep_line

        # are we doing temporary root?
        if self.config.temporary_root and boot.is_patched:
            data += "\necho Live booting to pf_boot for temporary root ...\n"
            data += f"{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options} boot pf_boot.img\n"
        else:
            if not boot.is_stock_boot:
                pf_flash = f"{indent}echo flashing pf_boot ...\n"
                if boot.is_init_boot or device.hardware in KNOWN_INIT_BOOT_DEVICES:
                    pf_flash += f"{indent}{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options} flash init_boot pf_boot.img\n"
                else:
                    pf_flash += f"{indent}{add_echo}\"{get_fastboot()}\" -s {device.id} {fastboot_options} flash boot pf_boot.img\n"

                if self.config.flash_mode == 'OTA':
                    data += slot_check_lines
                    # flash vbmeta if disabling verity / verification
                    if self.config.disable_verity or self.config.disable_verification:
                        data += "\n    echo flashing vbmeta ...\n"
                        data += f"    \"{get_fastboot()}\" -s {device.id} {fastboot_options} flash vbmeta vbmeta.img\n"
                    data += pf_flash
                    if sys.platform == "win32":
                        data += ")\n"
                    else:
                        data += "fi\n"
                else:
                    data += f"\n{pf_flash}"

            # only reboot if no_reboot is not selected
            if not self.config.no_reboot:
                data += "\necho rebooting to system ...\n"
                data += f"\"{get_fastboot()}\" -s {device.id} reboot"

        fin = open(flash_pf_file, "wt", encoding="ISO-8859-1", errors="replace")
        fin.write(data)
        fin.close()

        title = "Flash Options"
        message = get_flash_settings(self) + message + '\n'

    #----------------------------------------
    # common part for package or custom flash
    #----------------------------------------
    # make the sh script executable
    if sys.platform != "win32":
        theCmd = f"chmod 755 \"{flash_pf_file}\""
        debug(theCmd)
        res = run_shell(theCmd)
        if res.returncode != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set the permissions on {flash_pf_file}")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            print("Aborting ...\n")
            puml("#red:Could not set the permissions on flash script;\n}\n")
            return

    message += "\nNote: Pressing OK button will invoke a script that will utilize\n"
    if self.config.advanced_options and self.config.flash_mode == 'customFlash' and image_mode == 'SIDELOAD':
        message += "adb command, this could possibly take a long time and PixelFlasher\n"
        message += "will appear frozen. PLEASE BE PATIENT and don\'t interrupt the process.\n\n"
    else:
        message += "fastboot commands, this could possibly take a long time and PixelFlasher\n"
        message += "will appear frozen. PLEASE BE PATIENT. \n"
        message += "In case it takes excessively long, it could possibly be due to improper or\n"
        message += "bad fasboot drivers.\n"
        message += "In such cases, killing the fastboot process will resume to normalcy.\n\n"
    message += "Do you want to continue to flash with the above options?\n"
    message += "You can also choose to edit the script before continuing,\nin case you want to customize it.(Only choose this if you know what you are doing)\n\n"
    message += "Press OK to continue or CANCEL to abort.\n"
    print(f"\n*** Dialog ***\n{message}\n______________\n")
    print(f"The script content that will be executed:")
    print(f"___________________________________________________\n{data}")
    print("___________________________________________________\n")
    puml(":Dialog;\n", True)
    puml(f"note right\n{message}\nend note\n")
    puml(":Script;\n")
    puml(f"note right\nFlash Script\n====\n{data}\nend note\n")
    try:
        dlg = MessageBoxEx(parent=None, title=title, message=message, button_texts=["OK", "Edit script before continuing", "Cancel"], default_button=1)
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()
        dlg.Destroy()
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(e)

    if result == 1: # OK
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
        puml(":User Pressed OK;\n")
        # continue flashing
    elif result == 2: # Edit
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Edit Script.")
        puml("#pink:User Pressed Edit Script;\n}\n")
        dlg = FileEditor(self, flash_pf_file)
        dlg.CenterOnParent()
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            # get the contents of modified flash_pf_file
            with open(flash_pf_file, 'r', encoding='ISO-8859-1', errors="replace") as f:
                contents = f.read()
            print(f"\nflash_pf file has been modified!")
            print(f"The modified script content that will be executed:")
            print(f"___________________________________________________\n{contents}")
            print("___________________________________________________\n")
            puml(f"note right\nModified Script\n====\n{contents}\nend note\n")
            # continue flashing
        else:
            print("User cancelled editing flash_phone file.")
            puml(f"note right\nCancelled and Aborted\nend note\n")
            return
    elif result == 3: # Cancel
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
        print("Aborting ...\n")
        puml("#pink:User Pressed Cancel;\n}\n")
        return

    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Flashing Phone    ")
    print("==============================================================================")
    startFlash = time.time()
    puml(":Start Flashing;\n", True)
    print(f"Android Platform Tools Version: {get_sdk_version()}")
    puml(f"note right\nPixelFlasher {VERSION}\nAndroid Platform Tools Version: {get_sdk_version()}\nend note\n")

    # If we're doing Sideload image flashing or OTA
    if self.config.flash_mode == 'OTA' or (self.config.advanced_options and self.config.flash_mode == 'customFlash' and image_mode == 'SIDELOAD'):
        device.reboot_sideload()
        print("Waiting 20 seconds ...")
        time.sleep(20)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Flashing device {device.id} ...")
        puml(f":Flashing device {device.id};\n", True)
        theCmd = flash_pf_file
        os.chdir(package_dir_full)
        debug(f"Running in Directory: {package_dir_full}")
        theCmd = f"\"{theCmd}\""
        debug(theCmd)
        run_shell2(theCmd)
        if self.config.flash_mode != 'OTA' and not self.config.no_reboot:
            time.sleep(5)
            device.reboot_system()
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Done!")
        endFlash = time.time()
        print(f"Flashing elapsed time: {math.ceil(endFlash - startFlash)} seconds")
        print("------------------------------------------------------------------------------\n")
        os.chdir(cwd)
        puml("#cee7ee:End Flashing;\n", True)
        puml(f"note right:Flash time: {math.ceil(endFlash - startFlash)} seconds;\n")
        puml("}\n")
        # clear the selected device option
        set_phone(None)
        self.device_label.Label = "ADB Connected Devices"
        self.config.device = None
        self.device_choice.SetItems([''])
        self.device_choice.Select(-1)
        return

    if device.mode == 'adb':
        device.reboot_bootloader()
        print("Waiting 10 seconds ...")
        time.sleep(10)
        # device.refresh_phone_mode()
        self.device_choice.SetItems(get_connected_devices())
        self._select_configured_device()

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to detect the device.")
        puml("#red:Valid device is not detected;\n}\n")
        # let's try one more time just in case
        print("Waiting 10 seconds ...")
        time.sleep(10)
        self.device_choice.SetItems(get_connected_devices())
        self._select_configured_device()
        device = get_phone()
        if not device:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to detect the device.")
            puml("#red:Valid device is not detected;\n}\n")
        return

    if not (device.unlocked or (self.config.advanced_options and self.config.flash_mode == 'customFlash' and image_mode == 'SIDELOAD')):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Bootloader is locked, can't flash.")
        print("Aborting ...\n")
        puml("#red:Bootloader is locked, can't flash;\n}\n")
        return

    # some images need to be flashed in fastbootd mode
    # note: system and vendor, typically get flashed to both slots. '--skip-secondary' will not flash secondary slots in flashall/update
    # TODO check which Pixels and newer support fastbootd, Probably Pixel 5 and newer.
    if self.config.advanced_options and self.config.flash_mode == 'customFlash' and get_image_mode() in ['super','product','system','system_dlkm','system_ext','vendor','vendor_dlkm']:
        device.reboot_fastboot()
        print("Waiting 5 seconds ...")
        time.sleep(5)

    # if in bootloader mode, Start flashing
    if device.mode == 'f.b' and get_fastboot():
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Flashing device {device.id} ...")
        puml(f":Flashing device {device.id};\n", True)
        # confirm for wipe data
        if self.config.flash_mode == 'wipeData':
            print("Flash Mode: Wipe Data")
            puml(f":Flash Mode: Wipe Data;\n")
            dlg = wx.MessageDialog(None, "You have selected to WIPE data\nAre you sure want to continue?",'Wipe Data',wx.YES_NO | wx.ICON_EXCLAMATION)
            puml(f"note right\nDialog\n====\nYou have selected to WIPE data\nAre you sure want to continue?\nend note\n")
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled flashing.")
                puml("#pink:User cancelled flashing;\n}\n")
                return
        # confirm for wipe flag
        if self.config.advanced_options and self.wipe:
            print("Flash Option: Wipe")
            dlg = wx.MessageDialog(None, "You have selected the flash option: Wipe\nThis will wipe your data\nAre you sure want to continue?",'Flash option: Wipe',wx.YES_NO | wx.ICON_EXCLAMATION)
            puml(f"note right\nDialog\n====\nYou have selected the flash option: Wipe\nThis will wipe your data\nAre you sure want to continue?\nend note\n")
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled flashing.")
                puml("#pink:User cancelled flashing;\n}\n")
                return
        # confirm for force flag
        elif self.config.advanced_options and self.config.fastboot_force:
            print("Flash Option: Force")
            dlg = wx.MessageDialog(None, "You have selected the flash option: Force\nThis will wipe your data\nAre you sure want to continue?",'Flash option: Force',wx.YES_NO | wx.ICON_EXCLAMATION)
            puml(f"note right\nDialog\n====\nYou have selected the flash option: Force\nThis will wipe your data\nAre you sure want to continue?\nend note\n")
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled flashing.")
                puml("#pink:User cancelled flashing;\n}\n")
                return

        theCmd = flash_pf_file
        os.chdir(package_dir_full)
        theCmd = f"\"{theCmd}\""
        debug(theCmd)
        run_shell2(theCmd)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Done!")
        endFlash = time.time()
        print(f"Flashing elapsed time: {math.ceil(endFlash - startFlash)} seconds")
        print("------------------------------------------------------------------------------\n")
        puml("#cee7ee:End Flashing;\n", True)
        puml(f"note right:Flash time: {math.ceil(endFlash - startFlash)} seconds;\n")
        puml("}\n")
        os.chdir(cwd)
        # clear the selected device option
        set_phone(None)
        self.device_label.Label = "ADB Connected Devices"
        self.config.device = None
        self.device_choice.SetItems([''])
        self.device_choice.Select(-1)
        if self.config.advanced_options and self.config.flash_mode == 'customFlash':
            print("\nNote: The device is intentionally kept in bootloader mode\nin case you want to flash or do more things before booting to system.\nYou can reboot to system by pressing the button in PixelFlasher, or on your phone.\n")
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device {device.id} not in bootloader mode.")
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Aborting ...\n")
        puml("#red:Device is not in bootloader mode;\n}\n")

