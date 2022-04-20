#!/usr/bin/env python

import os
import subprocess
import re
import wx
import json
import time
import shutil
import zipfile
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
#                               Function get_package_ready
# ============================================================================
def get_package_ready(self, src, includeFlashMode = False, includeTitle = False):
    message = ''
    if os.path.exists(src):
        with open(src, 'r') as f:
            data = json.load(f)
        p_device = data['device']
        p_patch_boot = data['patch_boot']
        p_custom_rom = data['custom_rom']
        p_custom_rom_path = data['custom_rom_path']
        message = ''
        if includeTitle:
            message +=  "The package is of the following state.\n\n"
        message += "Patch Boot:             %s\n" % str(p_patch_boot)
        message += "Custom Rom:             %s\n" % str(p_custom_rom)
        if p_custom_rom:
            message += "Custom Rom File:        %s\n" % p_custom_rom_path
            rom_file = ntpath.basename(p_custom_rom_path)
            set_custom_rom_file(rom_file)
        if includeFlashMode:
            message += "Flash Mode:             %s\n" % self.config.flash_mode
        message += "\n"
    return message


# ============================================================================
#                               Function set_package_ready
# ============================================================================
def set_package_ready(self, file_path):
    data = {
        'device': self.config.device,
        'patch_boot': self.config.patch_boot,
        'custom_rom': self.config.custom_rom,
        'custom_rom_path': self.config.custom_rom_path,
    }
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


# ============================================================================
#                               Function purge
# ============================================================================
# This function delete multiple files matching a pattern
def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir, f))


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
        try:
            set_firmware_model(firmware[0])
            set_firmware_id(firmware[0] + "-" + firmware[1])
        except Exception as e:
            set_firmware_model(None)
            set_firmware_id(None)
        if get_firmware_id():
            set_flash_button_state(self)
        else:
            self.flash_button.Disable()
        # process_firmware(self)
    else:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The selected file {firmware} is not a zip file.")
        self.config.firmware_path = None
        self.firmware_picker.SetPath('')


# ============================================================================
#                               Function process_firmware
# ============================================================================
def process_firmware(self):
    print(f"processing firmware {self.config.firmware_path} ...")
    path_to_7z = get_path_to_7z()
    config_path = get_config_path()
    factory_images = os.path.join(config_path, 'factory_images')
    boot_images = os.path.join(config_path, 'boot_images')
    package_dir_full = os.path.join(factory_images, get_firmware_id())
    image_file_path = os.path.join(package_dir_full, 'image-' + get_firmware_id() + ".zip")

    # let's do some db stuff
    # connect / create db
    con = sl.connect(os.path.join(config_path,'PixelFlasher.db'))
    # create table
    try:
        with con:
            con.execute("""
                CREATE TABLE BOOT (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    epoch integer,
                    factory_id TEXT,
                    factory_file TEXT,
                    boot_hash TEXT,
                    boot_file TEXT,
                    patched_boot_hash,
                    patched_boot_file,
                    magisk_version,
                    magisk_options
                );
            """)
    except:
        pass

    # Unzip the factory image
    start_1 = time.time()
    debug(f"Unzipping Image: {self.config.firmware_path} into {package_dir_full} ...")
    theCmd = f"\"{path_to_7z}\" x -bd -y -o{factory_images} \"{self.config.firmware_path}\""
    debug(theCmd)
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(res.stderr)
        print("Aborting ...")
        return

    # extract boot.img
    debug(f"Extracting boot.img from {image_file_path} ...")
    theCmd = "\"%s\" x -bd -y -o\"%s\" \"%s\" boot.img" % (path_to_7z, package_dir_full, image_file_path)
    debug("%s" % theCmd)
    res = run_shell(theCmd)
    # expect ret 0
    if res.returncode != 0:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
        print(res.stderr)
        print("Aborting ...")
        return

    # get the checksum of the boot.img
    boot_img_file = os.path.join(package_dir_full, "boot.img")
    checksum = md5(os.path.join(boot_img_file))
    debug(f"md5 of boot.img: {checksum}")

    # if a matching boot.img is not found, store it.
    cached_boot_img_dir_full = os.path.join(config_path, 'boot_images', checksum)
    cached_boot_img_path = os.path.join(cached_boot_img_dir_full, 'boot.img')
    debug("Checking for cached copy of boot.img")
    if not os.path.exists(cached_boot_img_dir_full):
        os.makedirs(cached_boot_img_dir_full, exist_ok=True)
    if not os.path.exists(cached_boot_img_path):
        debug(f"Cached copy of boot.img with md5: {checksum} was not found.")
        debug(f"Copying {image_file_path} to {cached_boot_img_dir_full}")
        shutil.copy(boot_img_file, cached_boot_img_dir_full, follow_symlinks=True)
        # create db record
        sql = 'INSERT INTO BOOT (epoch, factory_id, factory_file, boot_hash, boot_file) values(?, ?, ?, ?, ?)'
        data = [
            (time.time(), get_firmware_id(), self.config.firmware_path, checksum, cached_boot_img_path)
        ]
        with con:
            con.executemany(sql, data)
    else:
        debug(f"Found a cached copy of boot.img md5={checksum}")
        with con:
            data = con.execute(f"SELECT * FROM BOOT WHERE boot_hash = '{checksum}'")
            for row in data:
                print(row)

    end_1 = time.time()
    print("Process firmware time: %s seconds"%(math.ceil(end_1 - start_1)))

        # id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        # epoch integer,
        # factory_id TEXT,
        # factory_file TEXT,
        # boot_hash TEXT,
        # boot_file TEXT,
        # patched_boot_hash,
        # patched_boot_file,
        # magisk_version,
        # magisk_options

    # # Get the checksum for boot.img
    # # see if we already have a match
    # # if we do, enumerate all patched copies of it, along with the magisk version and the options.
    # # probably it is best to store this in db
    # # Fields to store:
    #     # Date / Time
    #     # Factory Filename
    #     # Factory ID
    #     # Factory model
    #     # path to unpatched boot.img
    #     # unpatched boot.img md5
    #     # magisk version
    #     # magisk options
    #     # path to patched boot.img
    #     # patched boot.img md5

    # TODO: UI to manage boot.img.
    # TODO: UI to manage previous packages (multiple)


# ============================================================================
#                               Function set_flash_button_state
# ============================================================================
def set_flash_button_state(self):
    try:
        src = os.path.join(get_firmware_id(), "Package_Ready.json")
        if os.path.exists(src):
            self.flash_button.Enable()
            print(f"Previous flashable package is found for the firmware:\n{self.config.firmware_path}")
            message = get_package_ready(self, src, includeTitle=True)
            print(message)
        else:
            self.flash_button.Disable()
            if self.config.firmware_path:
                print(f"No previous flashable package is found for the firmware:\n{self.config.firmware_path}")
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
#                               Function prepare_package
# ============================================================================
def prepare_package(self):
    print("")
    print("==============================================================================")
    print(f" {datetime.now():%Y-%m-%d %H:%M:%S} PixelFlasher {VERSION}              Preparing Package ")
    print("==============================================================================")

    # get device
    device = get_phone()

    # Make sure factory image is selected
    if not get_firmware_model():
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select a valid factory image.")
        return

    # Make sure platform-tools is set and adb and fastboot are found
    if not self.config.platform_tools_path:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select Android Platform Tools (ADB)")
        return

    # Make sure Phone is connected
    if not device:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Select an ADB connection (phone)")
        return

    # Make sure Phone model matches firmware model
    if get_firmware_model() != device.hardware:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android device model {device.hardware} does not match firmware model {get_firmware_model()}")
        return

    start = time.time()
    cwd = os.getcwd()
    package_dir = get_firmware_id()
    package_dir_full = os.path.join(cwd, package_dir)

    # disable Flash Button
    self.flash_button.Disable()

    # Delete the previous folder if it exists
    if os.path.exists(package_dir_full):
        try:
            print(f"Found a previous package {package_dir} deleting ...")
            shutil.rmtree(package_dir_full)
        except OSError as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete the previous package.")
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {e.filename} - {e.strerror}.")
            print("Aborting ...")
            return

    # See if the bundled 7zip is found.
    path_to_7z = get_path_to_7z()
    debug(f"7Zip Path: {path_to_7z}")
    if os.path.exists(path_to_7z):
        print("Found Bundled 7zip.\nzip/unzip operations will be faster")
    else:
        print("Could not find bundled 7zip.\nzip/unzip operations will be slower")
        path_to_7z = None

    # Unzip the factory image
    startUnzip1 = time.time()
    print("Unzipping Image: %s into %s ..." % (self.config.firmware_path, cwd))
    if path_to_7z:
        theCmd = f"\"{path_to_7z}\" x -bd -y \"{self.config.firmware_path}\""
        debug(theCmd)
        res = run_shell(theCmd)
    else:
        try:
            with zipfile.ZipFile(self.config.firmware_path, 'r') as zip_ref:
                zip_ref.extractall(cwd)
                zip_ref.close()
        except Exception as e:
            raise e
    endUnzip1 = time.time()
    print("Unzip time1: %s seconds"%(math.ceil(endUnzip1 - startUnzip1)))

    # double check if unpacked directory exists, this should match firmware_id from factory image name
    if os.path.exists(package_dir):
        print("Unzipped into %s folder." % package_dir)
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unzipped folder {package_dir} not found.")
        # if bundled 7zip fails, let's try with Python libraries and see if that works.
        if path_to_7z:
            debug("returncode is: %s" %res.returncode)
            debug("stdout is: %s" %res.stdout)
            debug("stderr is: %s" %res.stderr)
            print("Disabling bundled 7zip ...")
            path_to_7z = None
            print("Trying unzip again with python libraries ...")
            startUnzip1 = time.time()
            try:
                with zipfile.ZipFile(self.config.firmware_path, 'r') as zip_ref:
                    zip_ref.extractall(cwd)
            except Exception as e:
                raise e
            endUnzip1 = time.time()
            print("Unzip time1.1: %s seconds"%(math.ceil(endUnzip1 - startUnzip1)))
            # double check if unpacked directory exists, this should match firmware_id from factory image name
            if os.path.exists(package_dir):
                print("Unzipped into %s folder." % package_dir)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unzipped folder {package_dir} not found again.")
                print("Aborting ...")
                return
        else:
            print("Aborting ...")
            return

    # if custom rom is selected, copy it to the flash folder
    if self.config.advanced_options and self.config.custom_rom:
        if self.config.custom_rom_path:
            rom_file = ntpath.basename(self.config.custom_rom_path)
            set_custom_rom_file(rom_file)
            rom_file_full = os.path.join(package_dir_full, rom_file)
            image_file = rom_file
            image_file_full = rom_file_full
            image_id = get_custom_rom_id()
            if os.path.exists(self.config.custom_rom_path):
                shutil.copy(self.config.custom_rom_path, rom_file_full, follow_symlinks=True)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Custom ROM file: {self.config.custom_rom_path} is not found")
                print("Aborting ...")
                return
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Custom ROM file is not set")
            print("Aborting ...")
            return
    else:
        image_id = 'image-' + package_dir
        image_file = image_id + ".zip"
        image_file_full = os.path.join(package_dir_full, image_file)

    # Do this only if patch is checked.
    if self.config.patch_boot:
        # unzip image (we only need to unzip the full image if we cannot find 7zip)
        # with 7zip we extract a single file, and then put it back later, without full unzip
        startUnzip2 = time.time()
        boot_img_folder = os.path.join(package_dir_full, image_id)
        boot_img = os.path.join(package_dir_full, "boot.img")
        if path_to_7z:
            print("Extracting boot.img from %s ..." % (image_file))
            theCmd = "\"%s\" x -bd -y -o\"%s\" \"%s\" boot.img" % (path_to_7z, package_dir_full, image_file_full)
            debug("%s" % theCmd)
            res = run_shell(theCmd)
        else:
            try:
                print("Extracting %s ..." % (image_file))
                with zipfile.ZipFile(image_file_full, 'r') as zip_ref:
                    zip_ref.extractall(boot_img_folder)
            except Exception as e:
                raise e
            # check if unpacked directory exists, move boot.img
            if os.path.exists(boot_img_folder):
                print("Unzipped into %s folder." %(boot_img_folder))
                src = os.path.join(boot_img_folder, "boot.img")
                os.rename(src, boot_img)
                os.rename(image_file_full, image_file_full + ".orig")
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unzipped folder {boot_img_folder} not found.")
                print("Aborting ...")
                return
        endUnzip2 = time.time()
        print("Unzip time2: %s seconds"%(math.ceil(endUnzip2 - startUnzip2)))

        # check if boot.img got extracted (if not probably the zip does not have it)
        if not os.path.exists(boot_img):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You have selected the Patch option, however boot.img file is not found.")
            print(f"Please make sure that the zip file: \n{image_file_full} contains boot.img at root level.")
            print("Aborting ...")
            return

        # delete existing boot.img
        print("Deleting boot.img from phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell rm -f %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
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
        theCmd = "\"%s\" -s %s shell ls -l %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 1
        if res.returncode != 1:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot.img Delete Failed!")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            print("Aborting ...")
            return

        # delete existing magisk_patched.img
        print("Deleting magisk_patched.img from phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell rm -f %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
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
        theCmd = "\"%s\" -s %s shell ls -l %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 1
        if res.returncode != 1:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: magisk_patched.img delete failed!")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            print("Aborting ...")
            return

        # Transfer boot.img to the phone
        print("Transfering boot.img to the phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s push \"%s\" %s/boot.img" % (get_adb(), device.id, boot_img, self.config.phone_path)
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
        theCmd = "\"%s\" -s %s shell ls -l %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
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
                theCmd = "\"%s\" -s %s shell monkey -p %s -c android.intent.category.LAUNCHER 1" % (get_adb(), device.id, get_magisk_package())
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
            theCmd = "\"%s\" -s %s shell \"su -c \'export KEEPVERITY=true; export KEEPFORCEENCRYPT=true; ./data/adb/magisk/boot_patch.sh /sdcard/Download/boot.img; mv ./data/adb/magisk/new-boot.img /sdcard/Download/magisk_patched.img\'\"" % (get_adb(), device.id)
            res = run_shell2(theCmd)
            endPatch = time.time()
            print("Patch time: %s seconds"%(math.ceil(endPatch - startPatch)))

        # check if magisk_patched.img got created.
        print("")
        print("Looking for magisk_patched.img in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell ls %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
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
        theCmd = "\"%s\" -s %s pull %s \"%s\""  % (get_adb(), device.id, magisk_patched, os.path.join(package_dir_full, "magisk_patched.img"))
        debug("%s" % theCmd)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode == 1:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to pull magisk_patched.img from phone.")
            print(res.stderr)
            print("Aborting ...")
            return

        # Replace Boot.img and create a zip file
        print("Replacing boot.img with patched version ...")
        startZip = time.time()
        if path_to_7z:
            # ren boot.img to boot.img.orig
            dest = os.path.join(package_dir_full, "boot.img.orig")
            shutil.copy(boot_img, dest, follow_symlinks=True)
            # copy magisk_patched to boot.img
            src = os.path.join(package_dir_full, "magisk_patched.img")
            dest = boot_img
            shutil.copy(src, dest, follow_symlinks=True)
            theCmd = "\"%s\" a \"%s\" boot.img" % (path_to_7z, image_file_full)
            debug("%s" % theCmd)
            os.chdir(package_dir_full)
            res = run_shell(theCmd)
            os.chdir(cwd)
        else:
            src = os.path.join(package_dir_full, "magisk_patched.img")
            dest = os.path.join(package_dir_full, image_id, "boot.img")
            shutil.copy(src, dest, follow_symlinks=True)
            dir_name = os.path.join(package_dir, image_id)
            dest = os.path.join(package_dir_full, image_file)
            print("")
            print("Zipping  %s ..." % dir_name)
            print("Please be patient as this is a slow process and could take some time.")
            shutil.make_archive(dir_name, 'zip', dir_name)
        if os.path.exists(dest):
            print("Package is successfully created!")
            # create a marker file to confirm successful package creation, this will be checked by Flash command
            src = os.path.join(package_dir_full, "Package_Ready.json")
            set_package_ready(self, src)
            self.flash_button.Enable()
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while preparing the package.")
            print(f"Package file: {dest} is not found.")
            print("Aborting ...")
        endZip = time.time()
        print("Zip time: %s seconds"%(math.ceil(endZip - startZip)))
    else:
        print("Package is successfully created!")
        src = os.path.join(package_dir_full, "Package_Ready.json")
        set_package_ready(self, src)
        self.flash_button.Enable()

    end = time.time()
    print("Total elapsed time: %s seconds"%(math.ceil(end - start)))


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

    package_dir = get_firmware_id()
    if not package_dir:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a firmware file.")
        return

    cwd = os.getcwd()
    package_dir_full = os.path.join(cwd, package_dir)
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

    # delete previous flash-phone.bat file if it exists
    if sys.platform == "win32":
        dest = os.path.join(package_dir_full, "flash-phone.bat")
        first_line = "@ECHO OFF\n"
        version_sig = f":: This is a generated file by PixelFlasher v{VERSION}\n\n"
    else:
        dest = os.path.join(package_dir_full, "flash-phone.sh")
        version_sig = f"# This is a generated file by PixelFlasher v{VERSION}\n\n"
        first_line = "#!/bin/sh\n"
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
                msg  = "ADB Sideload:         "
                data += f"\"{get_adb()}\" -s {device.id} sideload \"{get_image_path()}\"\n"
            else:
                data += version_sig
                if image_mode == 'image':
                    action = "update"
                    msg  = "Flash:                "
                elif image_mode == 'boot' and self.live_boot_radio_button.Value:
                    action = "boot"
                    msg  = "Live Boot to:         "
                else:
                    action = f"flash {image_mode}"
                    msg  = "Flash:                "
                data += f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} {action} \"{get_image_path()}\"\n"

            f.write(data)
            f.close()
            message += f"{msg}{get_image_path()} to {image_mode}\n\n"

    #--------------------------
    # do the package flash mode
    #--------------------------
    else:
        pr = os.path.join(get_firmware_id(), "Package_Ready.json")
        if not os.path.exists(pr):
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first prepare a package.")
            print("       Press the `Prepare Package` Button!")
            print("")
            return

        # Make sure Phone model matches firmware model
        if get_firmware_model() != device.hardware:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Android device model {device.hardware} does not match firmware Model {get_firmware_model()}")
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
                action = 'update'
                arg1 = f.arg1
                if self.config.flash_mode == 'wipeData':
                    action = '-w update'
                if self.config.custom_rom:
                    arg1 = f"\"{get_custom_rom_file()}\""
                data += f"{add_echo}{get_fastboot()} -s {device.id} {fastboot_options} {action} {arg1}\n"
        if self.config.flash_mode == 'dryRun':
            data += f"{get_fastboot()} -s {device.id} reboot\n"

        fin = open(dest, "wt")
        fin.write(data)
        fin.close()

        title = "Package Flash Options"
        message += get_package_ready(self, pr, includeFlashMode=True)

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
        os.chdir(package_dir)
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
        self.device_choice.SetItems(self.get_connected_devices())
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
        os.chdir(package_dir)
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

