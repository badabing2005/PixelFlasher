#!/usr/bin/env python

import os
import subprocess
import re
import wx
import json
import time
import shutil
import ntpath
import sys
import math
import hashlib
import sqlite3 as sl

from config import VERSION
from runtime import *
from platformdirs import *
from message_box import MessageBox
from datetime import datetime
from phone import get_connected_devices

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
            identify_sdk_version(self)
            print(f"SDK Version: {get_sdk_version()}")
            return
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected path {self.config.platform_tools_path} does not have adb and or fastboot")
            self.config.platform_tools_path = None
            set_adb(None)
            set_fastboot(None)

    if not self.config.platform_tools_path:
        print("Looking for Android Platform Tools in system PATH environment ...")
        adb = which(adb_binary)
        if adb:
            folder_path = os.path.dirname(adb)
            print("Found Android Platform Tools in %s" % folder_path)
            adb = os.path.join(folder_path, adb_binary)
            fastboot = os.path.join(folder_path, fastboot_binary)
            set_adb(adb)
            set_fastboot(fastboot)
            if os.path.exists(get_fastboot()):
                self.config.platform_tools_path = folder_path
                identify_sdk_version(self)
                print(f"SDK Version: {get_sdk_version()}")
            else:
                print(f"fastboot is not found in: {self.config.platform_tools_path}")
                self.config.platform_tools_path = None
                set_adb(None)
                set_fastboot(None)
        else:
            print("Android Platform Tools is not found.")
    try:
        if self.config.platform_tools_path:
            self.platform_tools_picker.SetPath(self.config.platform_tools_path)
        else:
            self.platform_tools_picker.SetPath('')
    except:
        pass
    identify_sdk_version(self)


# ============================================================================
#                               Function populate_boot_list
# ============================================================================
def populate_boot_list(self):
    self.list.DeleteAllItems()
    con = get_db()
    con.execute("PRAGMA foreign_keys = ON")
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
        JOIN PACKAGE
            ON PACKAGE.id = PACKAGE_BOOT.package_id
    """
    if self.config.show_all_boot:
        sql += ";"
    else:
        rom_path = ''
        firmware_path = ''
        if self.config.custom_rom and self.config.advanced_options:
            rom_path = self.config.custom_rom_path
        if self.config.firmware_path:
            firmware_path = self.config.firmware_path
        sql += f"AND package.file_path IN (\'{firmware_path}\', \'{rom_path}\');"

    with con:
        data = con.execute(sql)
        i = 0
        for row in data:
            index = self.list.InsertItem(i, row[1][:8])                     # boot_hash
            self.list.SetItem(index, 1, row[8][:8])                         # package_boot_hash
            self.list.SetItem(index, 2, row[10])                            # package_sig
            self.list.SetItem(index, 3, row[4])                             # magisk_version
            self.list.SetItem(index, 4, row[5])                             # hardware
            ts = datetime.fromtimestamp(row[6])
            self.list.SetItem(index, 5, ts.strftime('%Y-%m-%d %H:%M:%S'))   # boot_date
            self.list.SetItem(index, 6, row[11])                            # package_path
            if row[3]:
                self.list.SetItemColumnImage(i, 0, 0)
            else:
                self.list.SetItemColumnImage(i, 0, -1)
            i += 1
    # auto size columns to largest text, make the last column expand the available room
    cw = 0
    for i in range (0, self.list.ColumnCount - 1):
        self.list.SetColumnWidth(i, -2)
        cw += self.list.GetColumnWidth(i)
    self.list.SetColumnWidth(self.list.ColumnCount - 1, self.list.BestVirtualSize.Width - cw)

    # disable buttons
    self.config.boot_id = None
    self.config.selected_boot_md5 = None
    print("\nNo boot image is selected!")
    self.patch_boot_button.Enable(False)
    self.delete_boot_button.Enable(False)


# ============================================================================
#                               Function identify_sdk_version
# ============================================================================
def identify_sdk_version(self):
    sdk_version = None
    # Let's grab the adb version
    if get_adb():
        theCmd = "\"%s\" --version" % get_adb()
        response = run_shell(theCmd)
        for line in response.stdout.split('\n'):
            if 'Version' in line:
                sdk_version = line.split()[1]
                set_sdk_version(sdk_version)


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
        message += f"                        [Patched] with Magisk {boot.magisk_version} on {boot.hardware}\n"
    message += f"\nFlash Mode:             {self.config.flash_mode}\n"
    message += "\n"
    return message


# ============================================================================
#                               Function purge
# ============================================================================
# This function delete multiple files matching a pattern
def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir, f))


# ============================================================================
#                               Function delete_all
# ============================================================================
# This function delete multiple files matching a pattern
def delete_all(dir):
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


# ============================================================================
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print("debug: %s" % message)


# ============================================================================
#                               Function run_shell
# ============================================================================
# We use this when we want to capture the returncode and also selectively
# output what we want to console. Nothing is sent to console, both stdout and
# stderr are only available when the call is completed.
def run_shell(cmd):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        wx.Yield()
        return response
    except Exception as e:
        raise e


# ============================================================================
#                               Function run_shell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
# no returncode is available.
def run_shell2(cmd):
    class obj(object):
        pass

    response = obj()
    proc = subprocess.Popen("%s" % cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print
    stdout = ''
    while True:
        line = proc.stdout.readline()
        wx.Yield()
        if line.strip() == "":
            pass
        else:
            print(line.strip())
            stdout += line
        if not line: break
    proc.wait()
    response.stdout = stdout
    return response


# ============================================================================
#                               Function md5
# ============================================================================
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# ============================================================================
#                               Function Which
# ============================================================================
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


# ============================================================================
#                               Function select_firmware
# ============================================================================
def select_firmware(self):
    firmware = ntpath.basename(self.config.firmware_path)
    filename, extension = os.path.splitext(firmware)
    extension = extension.lower()
    if extension == '.zip':
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} The following firmware is selected:\n{firmware}")
        firmware = firmware.split("-")
        if len(firmware) == 1:
            set_firmware_id(filename)
        else:
            try:
                set_firmware_model(firmware[0])
                set_firmware_id(firmware[0] + "-" + firmware[1])
            except Exception as e:
                set_firmware_model(None)
                set_firmware_id(filename)
        if get_firmware_id():
            set_flash_button_state(self)
        else:
            self.flash_button.Disable()
        process_file(self, 'firmware')
    else:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {firmware} is not a zip file.")
        self.config.firmware_path = None
        self.firmware_picker.SetPath('')


# ============================================================================
#                               Function process_file
# ============================================================================
def process_file(self, file_type):
    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Processing {file_type} file ...")
    config_path = get_config_path()
    path_to_7z = get_path_to_7z()
    boot_images = os.path.join(config_path, 'boot_images')
    tmp_dir_full = os.path.join(config_path, 'tmp')
    con = get_db()
    con.execute("PRAGMA foreign_keys = ON")
    cursor = con.cursor()
    start_1 = time.time()
    checksum = ''

    if file_type == 'firmware':
        file_to_process = self.config.firmware_path
        factory_images = os.path.join(config_path, 'factory_images')
        package_sig = get_firmware_id()
        package_dir_full = os.path.join(factory_images, package_sig)
        # Unzip the factory image
        image_file_path = os.path.join(package_dir_full, 'image-' + package_sig + ".zip")
        debug(f"Unzipping Image: {file_to_process} into {package_dir_full} ...")
        theCmd = f"\"{path_to_7z}\" x -bd -y -o{factory_images} \"{file_to_process}\""
        debug(theCmd)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
            print(res.stderr)
            print("Aborting ...")
            return
    else:
        file_to_process = self.config.custom_rom_path
        package_sig = get_custom_rom_id()
        image_file_path = file_to_process

    # see if we have a record for the firmware/rom being processed
    cursor.execute(f"SELECT ID, boot_hash FROM PACKAGE WHERE package_sig = '{package_sig}' AND file_path = '{file_to_process}'")
    data = cursor.fetchall()
    if len(data) > 0:
        pre_package_id = data[0][0]
        pre_checksum = data[0][1]
        debug(f"Found a previous {file_type} PACKAGE record id={pre_package_id} for package_sig: {package_sig} Firmware: {file_to_process}")
    else:
        pre_package_id = 0
        pre_checksum = 'x'

    # delete all files in tmp folder to make sure we're dealing with new files only.
    delete_all(tmp_dir_full)

    if not os.path.exists(image_file_path):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {image_file_path} is not found.")
        print("Aborting ...")
        return

    # extract boot.img
    debug(f"Extracting boot.img from {image_file_path} ...")
    theCmd = "\"%s\" x -bd -y -o\"%s\" \"%s\" boot.img" % (path_to_7z, tmp_dir_full, image_file_path)
    debug("%s" % theCmd)
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract boot.img.")
        print(res.stderr)
        print("Aborting ...")
        return
    # sometimes the return code is 0 but no file to extract, handle that case.
    boot_img_file = os.path.join(tmp_dir_full, "boot.img")
    if not os.path.exists(boot_img_file):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract boot.img, ")
        print(f"Please make sure the file: {image_file_path} has boot.img in it.")
        print("Aborting ...")
        return

    # get the checksum of the boot.img
    checksum = md5(os.path.join(boot_img_file))
    debug(f"md5 of boot.img: {checksum}")

    # if a matching boot.img is not found, store it.
    cached_boot_img_dir_full = os.path.join(boot_images, checksum)
    cached_boot_img_path = os.path.join(cached_boot_img_dir_full, 'boot.img')
    debug("Checking for cached copy of boot.img")
    if not os.path.exists(cached_boot_img_dir_full):
        os.makedirs(cached_boot_img_dir_full, exist_ok=True)
    if not os.path.exists(cached_boot_img_path):
        debug(f"Cached copy of boot.img with md5: {checksum} was not found.")
        debug(f"Copying {image_file_path} to {cached_boot_img_dir_full}")
        shutil.copy(boot_img_file, cached_boot_img_dir_full, follow_symlinks=True)
    else:
        debug(f"Found a cached copy of {file_type} boot.img md5={checksum}")

    # create PACKAGE db record
    sql = 'INSERT INTO PACKAGE (boot_hash, type, package_sig, file_path, epoch ) values(?, ?, ?, ?, ?) ON CONFLICT (file_path) DO NOTHING'
    data = (checksum, file_type, package_sig, file_to_process, time.time())
    try:
        cursor.execute(sql, data)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(e)
    package_id = cursor.lastrowid
    print(f"Package ID: {package_id}")
    # if we didn't insert a new record, let's use the pre_package_id in case we need to insert a record into PACKAGE_BOOT
    if package_id == 0:
        package_id = pre_package_id

    # create BOOT db record
    sql = 'INSERT INTO BOOT (boot_hash, file_path, is_patched, magisk_version, hardware, epoch) values(?, ?, ?, ?, ?, ?) ON CONFLICT (boot_hash) DO NOTHING'
    data = (checksum, cached_boot_img_path, 0, '', '', time.time())
    try:
        cursor.execute(sql, data)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(e)
    boot_id = cursor.lastrowid
    print(f"Boot ID: {boot_id}")
    # if we didn't insert in BOOT, see if we have a record for the boot being processed in case we need to insert a record into PACKAGE_BOOT
    if boot_id == 0:
        cursor.execute(f"SELECT ID FROM BOOT WHERE boot_hash = '{pre_checksum}' OR boot_hash = '{checksum}'")
        data = cursor.fetchall()
        if len(data) > 0:
            boot_id = data[0][0]
            debug(f"Found a previous BOOT record id={boot_id} for boot_hash: {pre_checksum} or {checksum}")
        else:
            boot_id = 0

    # create PACKAGE_BOOT db record
    if package_id > 0 and boot_id > 0:
        debug(f"Creating PACKAGE_BOOT record, package_id: {package_id} boot_id: {boot_id}")
        sql = 'INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch) values(?, ?, ?) ON CONFLICT (package_id, boot_id) DO NOTHING'
        data = (package_id, boot_id, time.time())
        try:
            cursor.execute(sql, data)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
            print(e)
        package_boot_id = cursor.lastrowid
        print(f"Package_Boot ID: {package_boot_id}")

    # save db
    con.commit()
    set_db(con)
    populate_boot_list(self)
    end_1 = time.time()
    print("Process %s time: %s seconds" % (file_type, math.ceil(end_1 - start_1)))


# ============================================================================
#                               Function set_flash_button_state
# ============================================================================
def set_flash_button_state(self):
    try:
        boot = get_boot()
        if self.config.firmware_path != '' and os.path.exists(boot.package_path):
            self.flash_button.Enable()
        else:
            self.flash_button.Disable()
    except:
        self.flash_button.Disable()


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
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unexpect first line: {line} in file: {filepath}")
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
                    print(f"WARNING! Encountered an unexpected fastboot line while parsing {filepath}")
                    print(line)

            #-----------------
            # Unexpected lines
            else:
                print(f"WARNING! Encountered an unexpected line while parsing {filepath}")
                print(line)

            cnt += 1
        return flash_file_lines


# ============================================================================
#                               Function patch_boot_img
# ============================================================================
def patch_boot_img(self):
    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Patching boot.img ")
    print("==============================================================================")

    # get device
    device = get_phone()

    # Make sure boot image is selected
    if not self.config.boot_id:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select a boot image.")
        print("Aborting ...")
        return

    # Make sure platform-tools is set and adb and fastboot are found
    if not self.config.platform_tools_path:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select Android Platform Tools (ADB)")
        print("Aborting ...")
        return

    # Make sure Phone is connected
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select an ADB connection (phone)")
        print("Aborting ...")
        return

    # Make sure the phone is in adb mode.
    if device.mode != 'adb':
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device: {device.id} is not in adb mode.")
        print(f"Perhaps a refresh is necessary?")
        print("Aborting ...")
        return

    start = time.time()

    boot = get_boot()
    config_path = get_config_path()
    boot_images = os.path.join(config_path, 'boot_images')
    tmp_dir_full = os.path.join(config_path, 'tmp')

    # delete all files in tmp folder to make sure we're dealing with new files only.
    delete_all(tmp_dir_full)

    # check if boot.img got extracted (if not probably the zip does not have it)
    if not os.path.exists(boot.boot_path):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You have selected the Patch option, however boot file is not found.")
        print("Aborting ...")
        return

    # Extract phone model from boot.package_sig and warn the user if it is not from the current phone model
    package_sig = boot.package_sig.split("-")
    try:
        firmware_model = package_sig[0]
    except Exception as e:
        firmware_model = None
    if firmware_model != device.hardware:
        title = "Boot Model Mismatch"
        message =  f"WARNING: Your phone model is: {device.hardware}\n\n"
        message += f"The selected boot.img is from: {boot.package_sig}\n\n"
        message += "Please make sure the boot.img file you are trying to patch,\n"
        message += f"is for the selected device: {device.id}\n\n"
        message += "Click OK to accept and continue.\n"
        message += "or Hit CANCEL to abort."
        print(message)
        dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            print("User pressed ok.")
        else:
            print("User pressed cancel.")
            print("Aborting ...")
            return

    # delete existing boot.img from phone
    print("Deleting boot.img from phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell rm -f {self.config.phone_path}/boot.img"
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return

    # check if delete worked.
    print("Making sure boot.img is not on the phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell ls -l {self.config.phone_path}/boot.img"
    res = run_shell(theCmd)
    # expect ret 1
    if res.returncode != 1:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot.img Delete Failed!")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return

    # delete existing magisk_patched.img from phone
    print("Deleting magisk_patched.img from phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell rm -f {self.config.phone_path}/magisk_patched*.img"
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return

    # check if delete worked.
    print("Making sure magisk_patched.img is not on the phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell ls -l {self.config.phone_path}/magisk_patched*.img"
    res = run_shell(theCmd)
    # expect ret 1
    if res.returncode != 1:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: magisk_patched.img delete failed!")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return

    # Transfer boot image to the phone
    print("Transfering boot.img to the phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} push \"{boot.boot_path}\" {self.config.phone_path}/boot.img"
    debug("%s" % theCmd)
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return
    else:
        print(res.stdout)

    # check if transfer worked.
    print("Making sure boot.img is found on the phone in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell ls -l {self.config.phone_path}/boot.img"
    res = run_shell(theCmd)
    # expect 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot.img is not found!")
        print(f"Return Code: {res.returncode}.")
        print(f"Stdout: {res.stdout}.")
        print(f"Stderr: {res.stderr}.")
        print("Aborting ...")
        return

    if not device.rooted:
        print("Magisk Tools not found on the phone")
        # Check to see if Magisk is installed
        print("Looking for Magisk app ...")
        if not device.magisk_version:
            print("Unable to find magisk on the phone, perhaps it is hidden?")
            # Message to Launch Manually and Patch
            title = "Magisk not found"
            message =  "WARNING: Magisk is not found on the phone\n\n"
            message += "This could be either because it is hidden, or it is not installed\n\n"
            message += "Please manually launch Magisk on your phone.\n"
            message += "- Click on `Install` and choose\n"
            message += "- `Select and Patch a File`\n"
            message += "- select boot.img in %s \n" % self.config.phone_path
            message += "- Then hit `LET's GO`\n\n"
            message += "Click OK when done to continue.\n"
            message += "Hit CANCEL to abort."
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
            else:
                print("User pressed cancel.")
                print("Aborting ...")
                return
        else:
            print("Found Magisk app on the phone.")
            print("Launching Magisk ...")
            theCmd = f"\"{get_adb()}\" -s {device.id} shell monkey -p {get_magisk_package()} -c android.intent.category.LAUNCHER 1"
            res = run_shell(theCmd)
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk could not be launched")
                print(res.stderr)
                print("Please launch Magisk manually.")
            else:
                print("Magisk should now be running on the phone.")
            # Message Dialog Here to Patch Manually
            title = "Magisk found"
            message =  "Magisk should now be running on your phone.\n\n"
            message += "If it is not, you  can try starting in manually\n\n"
            message += "Please follow these steps in Magisk.\n"
            message += "- Click on `Install` and choose\n"
            message += "- `Select and patch a file`\n"
            message += "- select boot.img in %s \n" % self.config.phone_path
            message += "- Then hit `LET's GO`\n\n"
            message += "Click OK when done to continue.\n"
            message += "Hit CANCEL to abort."
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User Pressed Ok.")
            else:
                print("User Pressed Cancel.")
                print("Aborting ...")
                return
    else:
        startPatch = time.time()
        print(f"Detected a rooted phone with Magisk Tools: {device.magisk_version}")
        print("Creating patched boot.img ...")
        theCmd = f"\"{get_adb()}\" -s {device.id} shell \"su -c \'export KEEPVERITY=true; export KEEPFORCEENCRYPT=true; ./data/adb/magisk/boot_patch.sh /sdcard/Download/boot.img; mv ./data/adb/magisk/new-boot.img /sdcard/Download/magisk_patched.img\'\""
        res = run_shell2(theCmd)
        endPatch = time.time()

    # check if magisk_patched.img got created.
    print("")
    print("Looking for magisk_patched.img in %s ..." % (self.config.phone_path))
    theCmd = f"\"{get_adb()}\" -s {device.id} shell ls {self.config.phone_path}/magisk_patched*.img"
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode == 1:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: magisk_patched*.img not found")
        print(res.stderr)
        print("Aborting ...")
        return
    else:
        magisk_patched = res.stdout.strip()
        print("Found %s" %magisk_patched)

    # Transfer back boot.img
    print("Pulling %s from the phone ..." % (magisk_patched))
    theCmd = "\"%s\" -s %s pull %s \"%s\""  % (get_adb(), device.id, magisk_patched, os.path.join(tmp_dir_full, "magisk_patched.img"))
    debug("%s" % theCmd)
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode == 1:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull magisk_patched.img from phone.")
        print(res.stderr)
        print("Aborting ...")
        return

    # get the checksum of the magisk_patched.img
    magisk_patched_img_file = os.path.join(tmp_dir_full, "magisk_patched.img")
    checksum = md5(os.path.join(magisk_patched_img_file))
    debug(f"md5 of magisk_patched.img: {checksum}")

    # if a matching magisk_patched.img is not found, store it.
    cached_boot_img_dir_full = os.path.join(boot_images, checksum)
    cached_boot_img_path = os.path.join(cached_boot_img_dir_full, 'magisk_patched.img')
    debug("Checking for cached copy of boot.img")
    if not os.path.exists(cached_boot_img_dir_full):
        os.makedirs(cached_boot_img_dir_full, exist_ok=True)
    if not os.path.exists(cached_boot_img_path):
        debug(f"Cached copy of boot.img with md5: {checksum} was not found.")
        debug(f"Copying {magisk_patched_img_file} to {cached_boot_img_dir_full}")
        shutil.copy(magisk_patched_img_file, cached_boot_img_dir_full, follow_symlinks=True)
    else:
        debug(f"Found a cached copy of magisk_patched.img md5={checksum}")

    # create BOOT db record
    con = get_db()
    con.execute("PRAGMA foreign_keys = ON")
    cursor = con.cursor()
    sql = 'INSERT INTO BOOT (boot_hash, file_path, is_patched, magisk_version, hardware, epoch) values(?, ?, ?, ?, ?, ?) ON CONFLICT (boot_hash) DO NOTHING'
    data = (checksum, cached_boot_img_path, 1, device.magisk_version, device.hardware, time.time())
    cursor.execute(sql, data)
    boot_id = cursor.lastrowid
    print(f"Boot ID: {boot_id}")
    # if we didn't insert in BOOT, see if we have a record for the boot being processed in case we need to insert a record into PACKAGE_BOOT
    if boot_id == 0:
        cursor.execute(f"SELECT ID FROM BOOT WHERE boot_hash = '{checksum}'")
        data = cursor.fetchall()
        if len(data) > 0:
            boot_id = data[0][0]
            debug(f"Found a previous BOOT record id={boot_id} for boot_hash: {checksum}")
        else:
            boot_id = '0'

    # create PACKAGE_BOOT db record
    if boot.package_id > 0 and boot_id > 0:
        debug(f"Creating PACKAGE_BOOT record, package_id: {boot.package_id} boot_id: {boot_id}")
        sql = 'INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch) values(?, ?, ?) ON CONFLICT (package_id, boot_id) DO NOTHING'
        # sql = 'INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch) values(?, ?, ?)'
        data = (boot.package_id, boot_id, time.time())
        cursor.execute(sql, data)
        package_boot_id = cursor.lastrowid
        print(f"Package_Boot ID: {package_boot_id}")

    # save db
    con.commit()
    set_db(con)
    populate_boot_list(self)

    end = time.time()
    print("Patch time: %s seconds"%(math.ceil(end - start)))


# ============================================================================
#                               Function flash_phone
# ============================================================================
def flash_phone(self):
    if not get_adb():
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android Platform Tools must be set.")
        return

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid adb device.")
        return

    package_sig = get_firmware_id()
    if not package_sig:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a firmware file.")
        return

    cwd = os.getcwd()
    config_path = get_config_path()
    factory_images = os.path.join(config_path, 'factory_images')
    package_dir_full = os.path.join(factory_images, package_sig)
    boot = get_boot()

    message = ''

    # if advanced options is set, and we have flash options ...
    fastboot_options = ''
    if self.config.advanced_options:
        if self.config.flash_both_slots:
            fastboot_options += '--slot all '
        if self.config.disable_verity:
            fastboot_options += '--disable-verity '
        if self.config.disable_verification:
            fastboot_options += '--disable-verification '
        if self.config.fastboot_verbose:
            fastboot_options += '--verbose '
        message  = "Custom Flash Options:   %s\n" % str(self.config.advanced_options)
        message += "Disable Verity:         %s\n" % str(self.config.disable_verity)
        message += "Disable Verification:   %s\n" % str(self.config.disable_verification)
        message += "Flash Both Slots:       %s\n" % str(self.config.flash_both_slots)
        message += "Verbose Fastboot:       %s\n" % str(self.config.fastboot_verbose)

    if sys.platform == "win32":
        dest = os.path.join(package_dir_full, "flash-phone.bat")
        first_line = "@ECHO OFF\n"
        version_sig = f":: This is a generated file by PixelFlasher v{VERSION}\n\n"
    else:
        dest = os.path.join(package_dir_full, "flash-phone.sh")
        version_sig = f"# This is a generated file by PixelFlasher v{VERSION}\n\n"
        first_line = "#!/bin/sh\n"
    # delete previous flash-phone.bat file if it exists
    if os.path.exists(dest):
        os.remove(dest)

    #-------------------------------
    # if we are in custom Flash mode
    #-------------------------------
    if self.config.advanced_options and self.config.flash_mode == 'customFlash':
        image_mode = get_image_mode()
        if image_mode and get_image_path():
            title = "Advanced Flash Options"
            # create flash-phone.bat based on the custom options.
            f = open(dest.strip(), "w")
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
                else:
                    action = f"flash {image_mode}"
                    msg  = f"\nFlash {image_mode:<18}"
                data += f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} {action} \"{get_image_path()}\"\n"

            f.write(data)
            f.close()
            message += f"{msg}{get_image_path()}\n\n"

    #---------------------------
    # do the standard flash mode
    #---------------------------
    else:
        # check for boot file
        if not os.path.exists(boot.boot_path):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot file: {boot.boot_path} is not found.")
            print("Aborting ...")
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
            print("Aborting ...")
            return

        # Make sure Phone model matches firmware model
        if get_firmware_model() != device.hardware:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android device model {device.hardware} does not match firmware Model {get_firmware_model()}")
            # return

        # if firmware_model != device.hardware:
            title = "Device / Firmware Mismatch"
            message =  f"ERROR: Your phone model is: {device.hardware}\n\n"
            message += f"The selected firmware is for: {get_firmware_model()}\n\n"
            message += "Unless you know what you are doing, if you continue flashing\n"
            message += "you risk bricking your device, proceed only if you are absolutely\n"
            message += "certian that this is what you want, you have been warned.\n\n"
            message += "Click OK to accept and continue.\n"
            message += "or Hit CANCEL to abort."
            print(message)
            dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                print("User pressed ok.")
            else:
                print("User pressed cancel.")
                print("Aborting ...")
                return

        # Process flash_all files
        flash_all_win32 = process_flash_all_file(os.path.join(package_dir_full, "flash-all.bat"))
        flash_all_linux = process_flash_all_file(os.path.join(package_dir_full, "flash-all.sh"))
        s1 = ''
        s2 = ''
        for f in flash_all_win32:
            if f.sync_line != '':
                s1 += f"{f.sync_line}\n"
        for f in flash_all_linux:
            if f.sync_line != '':
                s2 += f"{f.sync_line}\n"
        # check to see if we have consistent linux / windows files
        if s1 != s2:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Found inconsistency between flash-all.bat and flash-all.sh files.")
            debug(f"bat file:\n{s1}")
            debug(f"\nsh file\n{s2}\n")

        data = ''
        add_echo =''
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
                    data += f":: This is a generated file by PixelFlasher v{VERSION}\n\n"
                else:
                    data += f"# This is a generated file by PixelFlasher v{VERSION}\n\n"
                continue
            if f.type in ['sleep', 'path']:
                data += f"{f.full_line}\n"
                continue
            if f.action == 'reboot-bootloader':
                data += f"{get_fastboot()} -s {device.id} {fastboot_options} {f.action} {f.arg1} {f.arg2}\n"
                continue
            if f.action == 'flash':
                data += f"{add_echo}{get_fastboot()} -s {device.id} {fastboot_options} {f.action} {f.arg1} {f.arg2}\n"
                continue
            if f.action == '-w update':
                action = '--skip-reboot update'
                arg1 = f.arg1
                if self.config.flash_mode == 'wipeData':
                    action = '--skip-reboot -w update'
                if self.config.custom_rom and self.config.advanced_options:
                    arg1 = f"\"{get_custom_rom_file()}\""
                data += f"{add_echo}{get_fastboot()} -s {device.id} {fastboot_options} {action} {arg1}\n"
        # add the boot.img flashing
        data += f"{add_echo}{get_fastboot()} -s {device.id} {fastboot_options} flash pf_boot.img\n"

        if self.config.flash_mode == 'dryRun':
            data += f"{get_fastboot()} -s {device.id} reboot\n"

        fin = open(dest, "wt")
        fin.write(data)
        fin.close()

        title = "Flash Options"
        message = get_flash_settings(self) + message + '\n'

    #----------------------------------------
    # common part for package or custom flash
    #----------------------------------------
    # make he sh script executable
    if sys.platform != "win32":
        theCmd = f"chmod 755 {dest}"
        debug(theCmd)
        res = run_shell(theCmd)

    message += "\nNote: Pressing OK button will invoke a script that will utilize\n"
    message += "fastboot commands, if your PC fastboot drivers are not propely setup,\n"
    message += "fastboot will wait forever, and PixelFlasher will appear hung.\n"
    message += "In such cases, killing the fastboot process will resume to normalcy.\n\n"
    message += "      Do you want to continue to flash with the above options?\n"
    message += "              Press OK to continue or CANCEL to abort.\n"
    print(message)
    debug(f"The script content that will be executed:")
    debug(f"--------------------------------------------\n{data}")
    debug("--------------------------------------------\n")
    set_message_box_title(title)
    set_message_box_message(message)
    dlg = MessageBox(self)
    dlg.CentreOnParent(wx.BOTH)
    result = dlg.ShowModal()

    if result == wx.ID_OK:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Ok.")
    else:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
        print("Aborting ...")
        dlg.Destroy()
        return
    dlg.Destroy()

    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Flashing Phone    ")
    # print(" PixelFlasher %s              Flashing Phone                                  " % VERSION)
    print("==============================================================================")
    startFlash = time.time()

    # If we're doing Sideload flashing
    if self.config.advanced_options and self.config.flash_mode == 'customFlash' and image_mode == 'SIDELOAD':
        device.reboot_sideload()
        print("Waiting 20 seconds ...")
        time.sleep(20)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Flashing device {device.id} ...")
        theCmd = dest
        os.chdir(package_dir_full)
        theCmd = "\"%s\"" % theCmd
        debug(theCmd)
        run_shell2(theCmd)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Done!")
        endFlash = time.time()
        print("Flashing elapsed time: %s seconds"%(math.ceil(endFlash - startFlash)))
        os.chdir(cwd)
        return

    if device.mode == 'adb':
        device.reboot_bootloader()
        print("Waiting 5 seconds ...")
        time.sleep(5)
        # device.refresh_phone_mode()
        self.device_choice.SetItems(get_connected_devices())
        self._select_configured_device()

    device = get_phone()
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to detect the device.")
        return

    # vendor_dlkm needs to be flashed in fastbootd mode
    if self.config.advanced_options and self.config.flash_mode == 'customFlash' and get_image_mode() == 'vendor_dlkm':
        device.reboot_fastboot()
        print("Waiting 5 seconds ...")
        time.sleep(5)

    # if in bootloader mode, Start flashing
    if device.mode == 'f.b' and get_fastboot():
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Flashing device {device.id} ...")
        # confirm for wipe data
        if self.config.flash_mode == 'wipeData':
            print("Flash Mode: Wipe Data")
            dlg = wx.MessageDialog(None, "You have selected to WIPE data\nAre you sure want to continue?",'Wipe Data',wx.YES_NO | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User canceled flashing.")
                return

        theCmd = dest
        os.chdir(package_dir_full)
        theCmd = "\"%s\"" % theCmd
        debug(theCmd)
        run_shell2(theCmd)
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Done!")
        endFlash = time.time()
        print("Flashing elapsed time: %s seconds"%(math.ceil(endFlash - startFlash)))
        os.chdir(cwd)
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device {device.id} not in bootloader mode.")
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Aborting ...")

