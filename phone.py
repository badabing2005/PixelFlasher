#!/usr/bin/env python

import contextlib
import re
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse

import wx

from runtime import *


# ============================================================================
#                               Class Magisk
# ============================================================================
class Magisk():
    def __init__(self, dirname):
        self.dirname = dirname


# ============================================================================
#                               Class MagiskApk
# ============================================================================
class MagiskApk():
    def __init__(self, type):
        self.type = type


# ============================================================================
#                               Class Device
# ============================================================================
class Device():
    # Class variable
    vendor = "google"

    def __init__(self, id, mode, true_mode = None):
        # Instance variables
        self.id = id
        self.mode = mode
        if true_mode:
            self.true_mode = true_mode
        else:
            self.true_mode = mode
        # The below are for caching.
        self._adb_device_info = None
        self._fastboot_device_info = None
        self._hardware = None
        self._build = None
        self._api_level = None
        self._architecture = None
        self._active_slot = None
        self._bootloader_version = None
        self._rooted = None
        self._unlocked = None
        self._magisk_version = None
        self._magisk_app_version = None
        self._magisk_detailed_modules = None
        self._magisk_modules_summary = None
        self._magisk_apks = None
        self._magisk_path = None
        self._magisk_config_path = None

    # ----------------------------------------------------------------------------
    #                               property adb_device_info
    # ----------------------------------------------------------------------------
    @property
    def adb_device_info(self):
        if self.mode == 'adb':
            if self._adb_device_info is None:
                self._adb_device_info = self.device_info
            else:
                 self._adb_device_info = ''
            return self._adb_device_info

    # ----------------------------------------------------------------------------
    #                               property fastboot_device_info
    # ----------------------------------------------------------------------------
    @property
    def fastboot_device_info(self):
        if self.mode == 'f.b':
            if self._fastboot_device_info is None:
                self._fastboot_device_info = self.device_info
            else:
                 self._fastboot_device_info = ''
            return self._fastboot_device_info

    # ----------------------------------------------------------------------------
    #                               property device_info
    # ----------------------------------------------------------------------------
    @property
    def device_info(self):
        if self.mode == 'adb':
            if get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} shell /bin/getprop"
                device_info = run_shell(theCmd)
                if device_info.returncode == 127:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop"
                    device_info = run_shell(theCmd)
                return ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
        elif self.mode == 'f.b':
            if get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar all"
                device_info = run_shell(theCmd)
                if (device_info.stdout == ''):
                    return ''.join(device_info.stderr)
                else:
                    return ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")

    # ----------------------------------------------------------------------------
    #                               Method init
    # ----------------------------------------------------------------------------
    def init(self, mode):
        if mode == 'adb':
            device_info = self.adb_device_info
            if device_info:
                s_active_slot = "ro.boot.slot_suffix"
                s_bootloader_version = "ro.bootloader"
                s_build = "ro.build.fingerprint"
                s_api_level = "ro.build.version.sdk"
                s_hardware = "ro.hardware"
                s_architecture = "ro.product.cpu.abi"
                for line in device_info.split("\n"):
                    if s_active_slot in line and not self._active_slot:
                        self._active_slot = self.extract_prop(s_active_slot, line.strip())
                        self._active_slot = self._active_slot.replace("_", "")
                    elif s_bootloader_version in line and not self._bootloader_version:
                        self._bootloader_version = self.extract_prop(s_bootloader_version, line.strip())
                    elif s_build in line and not self._build:
                        self._build = self.extract_prop(s_build, line.strip())
                        self._build = self._build.split('/')[3]
                    elif s_api_level in line and not self._api_level:
                        self._api_level = self.extract_prop(s_api_level, line.strip())
                    elif s_hardware in line and not self._hardware:
                        self._hardware = self.extract_prop(s_hardware, line.strip())
                    elif s_architecture in line and not self._architecture:
                        self._architecture = self.extract_prop(s_architecture, line.strip())
        elif mode == 'f.b':
            device_info = self.fastboot_device_info
            if device_info:
                s_active_slot = "(bootloader) current-slot"
                s_hardware = "(bootloader) product"
                s_unlocked = "(bootloader) unlocked"
                for line in device_info.split("\n"):
                    if s_active_slot in line and not self._active_slot:
                        self._active_slot = self.extract_prop(s_active_slot, line.strip())
                    elif s_hardware in line and not self._hardware:
                        self._hardware = self.extract_prop(s_hardware, line.strip())
                    elif s_unlocked in line and not self._unlocked:
                        self._unlocked = self.extract_prop(s_unlocked, line.strip())
                        if self._unlocked == 'yes':
                            self._unlocked = True
                        else:
                            self._unlocked = False

    # ----------------------------------------------------------------------------
    #                               property extract_prop
    # ----------------------------------------------------------------------------
    def extract_prop(self, search, match):
        if self.mode == 'adb':
            l,r = match.split(": ")
            if l.strip() == f"[{search}]":
                return r.strip().strip("[").strip("]")
        elif self.mode == 'f.b':
            l,r = match.split(":")
            if l.strip() == f"{search}":
                return r.strip()

    # ----------------------------------------------------------------------------
    #                               property active_slot
    # ----------------------------------------------------------------------------
    @property
    def active_slot(self):
        if self._active_slot is None:
            return ''
        else:
            return self._active_slot

    # ----------------------------------------------------------------------------
    #                               property bootloader_version
    # ----------------------------------------------------------------------------
    @property
    def bootloader_version(self):
        if self._bootloader_version is None:
            return ''
        else:
            return self._bootloader_version

    # ----------------------------------------------------------------------------
    #                               property build
    # ----------------------------------------------------------------------------
    @property
    def build(self):
        if self._build is None:
            return ''
        else:
            return self._build

    # ----------------------------------------------------------------------------
    #                               property api_level
    # ----------------------------------------------------------------------------
    @property
    def api_level(self):
        if self._api_level is None:
            return ''
        else:
            return self._api_level

    # ----------------------------------------------------------------------------
    #                               property hardware
    # ----------------------------------------------------------------------------
    @property
    def hardware(self):
        if self._hardware is None:
            return ''
        else:
            return self._hardware

    # ----------------------------------------------------------------------------
    #                               property architecture
    # ----------------------------------------------------------------------------
    @property
    def architecture(self):
        if self._architecture is None:
            return ''
        else:
            return self._architecture

    # ----------------------------------------------------------------------------
    #                               property unlocked
    # ----------------------------------------------------------------------------
    @property
    def unlocked(self):
        if self._unlocked is None:
            return ''
        else:
            return self._unlocked

    # ----------------------------------------------------------------------------
    #                               property root_symbol
    # ----------------------------------------------------------------------------
    @property
    def root_symbol(self):
        if self.mode == 'f.b':
            return '?'
        elif self.rooted:
            return '✓'
        else:
            return '✗'

    # ----------------------------------------------------------------------------
    #                               property magisk_path
    # ----------------------------------------------------------------------------
    @property
    def magisk_path(self):
        if self._magisk_path is None and self.mode == 'adb':
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm path {get_magisk_package()}"
                res = run_shell(theCmd)
                if res.returncode == 0:
                    self._magisk_path = res.stdout.split(':')[1]
                    self._magisk_path = self._magisk_path.strip('\n')
            except Exception:
                self._rooted = None
        return self._magisk_path

    # ----------------------------------------------------------------------------
    #                               property magisk_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_version(self):
        if self._magisk_version is None and self.mode == 'adb' and self.rooted:
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk -c\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    regex = re.compile("(.*?):.*\((.*?)\)")
                    m = re.findall(regex, res.stdout)
                    if m:
                        self._magisk_version = f"{m[0][0]}:{m[0][1]}"
                    else:
                        self._magisk_version = res.stdout
                    self._magisk_version = self._magisk_version.strip('\n')
            except Exception:
                try:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/adb/magisk/magisk32 -c\'\""
                    res = run_shell(theCmd)
                    if res.returncode == 0:
                        self._magisk_version = res.stdout.strip('\n')
                except Exception:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk version, assuming that it is not rooted.")
                    self._rooted = None
        return self._magisk_version

    # ----------------------------------------------------------------------------
    #                               property magisk_config_path
    # ----------------------------------------------------------------------------
    @property
    def magisk_config_path(self):
        if self._magisk_config_path is None and self.mode == 'adb' and self.rooted:
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -1 $(magisk --path)/.magisk/config\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    self._magisk_config_path = res.stdout.strip('\n')
                else:
                    self._magisk_config_path = None
            except Exception as e:
                print(e)
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk sha1.")
                self._magisk_config_path = None
        return self._magisk_config_path

    # ----------------------------------------------------------------------------
    #                               property magisk_backups
    # ----------------------------------------------------------------------------
    @property
    def magisk_backups(self):
        if self.mode == 'adb' and self.rooted:
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -d -1 /data/magisk_backup_*\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    _magisk_backups = res.stdout.replace('/data/magisk_backup_', '').split('\n')
                else:
                    _magisk_backups = None
            except Exception as e:
                print(e)
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk backups.")
                _magisk_backups = None
        return _magisk_backups

    # ----------------------------------------------------------------------------
    #                               property magisk_sha1
    # ----------------------------------------------------------------------------
    @property
    def magisk_sha1(self):
        if self.mode == 'adb' and self.rooted:
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cat $(magisk --path)/.magisk/config | grep SHA1 | cut -d \'=\' -f 2\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    _magisk_sha1 = res.stdout.strip('\n')
                else:
                    _magisk_sha1 = ''
            except Exception as e:
                print(e)
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk sha1.")
                _magisk_sha1 = ''
        return _magisk_sha1

    # ----------------------------------------------------------------------------
    #                               Method run_magisk_migration
    # ----------------------------------------------------------------------------
    def run_magisk_migration(self, sha1 = None):
        if self.mode == 'adb' and self.rooted:
            try:
                print("Making sure stock-boot.img is found on the phone ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell ls -l /data/adb/magisk/stock-boot.img"
                res = run_shell(theCmd)
                # expect 0
                if res.returncode != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: /data/adb/magisk/stock-boot.img is not found!")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    print("Aborting run_migration ...\n")
                    return -1

                print("Triggering Magisk run_migration to create a Backup of source boot.img")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cd /data/adb/magisk; ./magiskboot cleanup; . ./util_functions.sh; run_migrations\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    print("run_migration completed.")
                    if sha1:
                        magisk_backups = self.magisk_backups
                        if self.magisk_backups and sha1 in magisk_backups:
                            print(f"Magisk backup for {sha1} was successful")
                            return 0
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk backup failed.")
                            return -1
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk backup failed.")
                    return -1
            except Exception as e:
                print(e)
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk backup failed.")
                return -1
        return -1

    # ----------------------------------------------------------------------------
    #                               Method create_magisk_backup
    # ----------------------------------------------------------------------------
    def create_magisk_backup(self, sha1 = None):
        if self.mode == 'adb' and self.rooted and sha1:
            try:
                print("Getting the current SHA1 from Magisk config ...")
                magisk_sha1 = self.magisk_sha1
                print(f"The Current SHA1 in Magisk config is: {magisk_sha1}")

                boot_img = os.path.join(get_boot_images_dir(), sha1, 'boot.img')
                if not os.path.exists(boot_img):
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: boot.img with SHA1 of {sha1} is not found.")
                    print("Aborting backup ...\n")
                    return -1
                # Transfer boot image to the phone
                print(f"Transfering {boot_img} to the phone in /data/adb/magisk/stock-boot.img ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} push \"{boot_img}\" /data/adb/magisk/stock-boot.img"
                debug(theCmd)
                res = run_shell(theCmd)
                # expect ret 0
                if res.returncode != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    print("Aborting backup ...\n")
                    return -1
                else:
                    print(res.stdout)

                # trigger run migration
                print("Triggering Magisk run_migration to create a Backup ...")
                res = self.run_magisk_migration(sha1)
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk backup failed.")
                    return -1

                # read config
                print("Getting the SHA1 from Magisk config again ...")
                magisk_sha1 = self.magisk_sha1
                print(f"SHA1 from Magisk config is: {magisk_sha1}")
                if sha1 != magisk_sha1:
                    print(f"Updating Magisk Config SHA1 to {sha1} to match the SHA1 of the source boot.img ...")
                    res = self.update_magisk_config(sha1)
                    if res == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not update Magisk config")
                        return -1
                    else:
                        print(f"Magisk config successfully updated with SHA1: {sha1}")

                return 0
            except Exception as e:
                print(e)
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Magisk backup failed.")
                return -1
        return -1

    # ----------------------------------------------------------------------------
    #                               Method update_magisk_config
    # ----------------------------------------------------------------------------
    def update_magisk_config(self, sha1 = None):
        if self.mode != 'adb' or not self.rooted or not sha1:
            return -1
        try:
            magisk_config_path = self.magisk_config_path
            if magisk_config_path:
                print("Getting the current SHA1 from Magisk config ...")
                magisk_sha1 = self.magisk_sha1
                print(f"The Current SHA1 in Magisk config is: {magisk_sha1}")
                print(f"Changing Magisk config SHA1 to: {sha1} ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cd {magisk_config_path}; sed -i \"s/{magisk_sha1}/{sha1}/g\" config\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    # Read back to make sure it us updated
                    print("Getting back the SHA1 from Magisk config ...")
                    magisk_sha1 = self.magisk_sha1
                    print(f"SHA1 from Magisk config is: {magisk_sha1}")
                    if magisk_sha1 != sha1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not update Magisk config")
                        return -1
                    else:
                        print(f"Magisk config successfully updated with SHA1: {sha1}")
                        return 0
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not update Magisk config")
                    return -1
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get Magisk config")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk sha1.")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method delete_magisk_ramdisk_cpio
    # ----------------------------------------------------------------------------
    def delete_magisk_ramdisk_cpio(self):
        if self.mode != 'adb' or not self.rooted:
            return -1
        try:
            print("Deleting old ramdisk.cpio to prevent Magisk issue ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/magisk/ramdisk.cpio\'\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Successfully deleted Magisk ramdisk.cpio")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete Magisk ramdisk.cpio")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete Magisk ramdisk.cpio")
            return -1

    # ----------------------------------------------------------------------------
    #                               property magisk_app_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_app_version(self):
        if self._magisk_app_version is None and self.mode == 'adb':
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package {get_magisk_package()}"
                res = run_shell(theCmd)
                data = res.stdout.split('\n')
                version = None
                versionCode = None
                for line in data:
                    if re.search('versionCode', line):
                        versionCode = line.split('=')
                        versionCode = versionCode[1]
                        versionCode = versionCode.split(' ')
                        versionCode = versionCode[0]
                    if re.search('versionName', line):
                        version = line.split('=')
                        version = version[1]
            except Exception:
                return ''
            if version and versionCode:
                self._magisk_app_version = f"{str(version)}:{str(versionCode)}"
            else:
                self._magisk_app_version = ''
        return self._magisk_app_version

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_magisk_app_version
    # ----------------------------------------------------------------------------
    def get_uncached_magisk_app_version(self):
        self._magisk_app_version = None
        return self.magisk_app_version

    # # ----------------------------------------------------------------------------
    # #                               Method is_display_unlocked
    # # ----------------------------------------------------------------------------
    # def is_display_unlocked(self):
    #     print("Checking to see if display is unlocked ...")
    #     try:
    #         if self.mode == 'adb':
    #             theCmd = f"\"{get_adb()}\" -s {self.id} shell \"dumpsys power | grep \'mHolding\'\""
    #             res = run_shell(theCmd)
    #             mHoldingWakeLockSuspendBlocker = False
    #             mHoldingDisplaySuspendBlocker = False
    #             if res.returncode == 0:
    #                 results = res.stdout.strip().split('\n')
    #                 for m in results:
    #                     s = False
    #                     k, v = m.strip().split('=')
    #                     if v == 'true':
    #                         s = True
    #                     if k == 'mHoldingDisplaySuspendBlocker':
    #                         mHoldingDisplaySuspendBlocker = s
    #                     elif k == 'mHoldingWakeLockSuspendBlocker':
    #                         mHoldingWakeLockSuspendBlocker = s
    #             # https://stackoverflow.com/questions/35275828/is-there-a-way-to-check-if-android-device-screen-is-locked-via-adb
    #             # I'm not going to check for both flags as it is not reliable
    #             # But this won't work if display is on but locked :(
    #             # if mHoldingWakeLockSuspendBlocker and mHoldingDisplaySuspendBlocker:
    #             if mHoldingDisplaySuspendBlocker:
    #                 print("Display is unlocked")
    #                 return True
    #             else:
    #                 print("Display is locked")
    #                 return False
    #     except Exception:
    #         print("Display is locked")
    #         return False


    # ----------------------------------------------------------------------------
    #                               Method stop_magisk
    # ----------------------------------------------------------------------------
    def stop_magisk(self):
        print("Stopping Magisk ...")
        with contextlib.suppress(Exception):
            if self.mode == 'adb':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell am force-stop {get_magisk_package()}"
                res = run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               property magisk_detailed_modules
    # ----------------------------------------------------------------------------
    @property
    def  magisk_detailed_modules(self):
        if self._magisk_detailed_modules is None:
            try:
                if self.mode == 'adb' and self.rooted:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'for FILE in /data/adb/modules/*; do echo $FILE; if test -f \"$FILE/disable\"; then echo \"state=disabled\"; else echo \"state=enabled\"; fi; cat \"$FILE/module.prop\"; echo; echo -----pf;done\'"
                    res = run_shell(theCmd)
                    if res.returncode == 0:
                        modules = []
                        themodules = res.stdout.split('-----pf\n')
                        for item in themodules:
                            if item != '':
                                module_prop = item.split('\n')
                                filepath = module_prop[0]
                                module = os.path.basename(urlparse(filepath).path)
                                m = Magisk(module)
                                setattr(m, 'id', '')
                                setattr(m, 'version', '')
                                setattr(m, 'versionCode', '')
                                setattr(m, 'author', '')
                                setattr(m, 'description', '')
                                for line in module_prop:
                                    # ignore empty lines
                                    if line == '':
                                        continue
                                    # ignore the first line which is the full path
                                    if line == filepath:
                                        continue
                                    # ignore comment lines
                                    if line[:1] == "#":
                                        continue
                                    if line.strip() != '' and '=' in line:
                                        key, value = line.split('=', 1)
                                        setattr(m, key, value)
                                modules.append(m)
                        self._magisk_detailed_modules = modules
            except Exception as e:
                self._magisk_detailed_modules is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules processing\nException: {e}")
                print(f"    Module: {module}\n    Line: {line}")
                print(f"    module.prop:\n-----\n{res.stdout}-----\n")
        return self._magisk_detailed_modules

    # ----------------------------------------------------------------------------
    #                               property magisk_apks
    # ----------------------------------------------------------------------------
    @property
    def magisk_apks(self):
        if self._magisk_apks is None:
            try:
                apks = []
                mlist = ['stable', 'beta', 'canary', 'debug', 'alpha', 'delta']
                for i in mlist:
                    apk = self.get_magisk_apk_details(i)
                    apks.append(apk)
                self._magisk_apks = apks
            except Exception as e:
                self._magisk_apks is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links processing\nException: {e}")
        return self._magisk_apks

    # ----------------------------------------------------------------------------
    #                               Function get_magisk_apk_details
    # ----------------------------------------------------------------------------
    def get_magisk_apk_details(self, channel):
        if channel == 'stable':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json"
        elif channel == 'beta':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json"
        elif channel == 'canary':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json"
        elif channel == 'debug':
            url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/debug.json"
        elif channel == 'alpha':
            url = "https://raw.githubusercontent.com/vvb2060/magisk_files/alpha/alpha.json"
        elif channel == 'delta':
            url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/canary.json"
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown Magisk channel {channel}\n")
            return
        try:
            payload={}
            headers = {
                'Content-Type': "application/json"
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            ma = MagiskApk(channel)
            setattr(ma, 'version', data['magisk']['version'])
            setattr(ma, 'versionCode', data['magisk']['versionCode'])
            setattr(ma, 'link', data['magisk']['link'])
            note_link = data['magisk']['note']
            setattr(ma, 'note_link', note_link)
            # Get the note contents
            headers = {}
            response = requests.request("GET", note_link, headers=headers, data=payload)
            setattr(ma, 'release_notes', response.text)
            return ma
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links processing\nException: {e}")

    # ----------------------------------------------------------------------------
    #                               property magisk_modules_summary
    # ----------------------------------------------------------------------------
    @property
    def magisk_modules_summary(self):
        if self._magisk_modules_summary is None:
            if self.magisk_detailed_modules:
                summary = ''
                for module in self.magisk_detailed_modules:
                    with contextlib.suppress(Exception):
                        summary += f"        {module.name:<36}{module.state:<10}{module.version}\n"
                self._magisk_modules_summary = summary
            else:
                self._magisk_modules_summary = ''
        return self._magisk_modules_summary

    # ----------------------------------------------------------------------------
    #                               property rooted
    # ----------------------------------------------------------------------------
    @property
    def rooted(self):
        if self._rooted is None and self.mode == 'adb':
            if get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -l /data/adb/magisk/\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    self._rooted = True
                else:
                    self._rooted = False
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
        return self._rooted

    # ----------------------------------------------------------------------------
    #                               Method get_details
    # ----------------------------------------------------------------------------
    def get_device_details(self):
        if self.true_mode != self.mode:
            mode = self.true_mode[:3]
        else:
            mode = self.mode
        return f"{self.root_symbol:<3}({mode:<3})   {self.id:<25}{self.hardware:<12}{self.build:<25}"

    # ----------------------------------------------------------------------------
    #                               Method reboot_system
    # ----------------------------------------------------------------------------
    def reboot_system(self):
        print(f"Rebooting device {self.id} to system ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot"
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_recovery
    # ----------------------------------------------------------------------------
    def reboot_recovery(self):
        print(f"Rebooting device {self.id} to recovery ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot recovery "
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot recovery"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_bootloader
    # ----------------------------------------------------------------------------
    def reboot_bootloader(self, fastboot_included = False):
        print(f"Rebooting device {self.id} to bootloader ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot bootloader "
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and fastboot_included and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot bootloader"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_fastbootd
    # ----------------------------------------------------------------------------
    def reboot_fastboot(self):
        print(f"Rebooting device {self.id} to fastbootd ...")
        print("This process will wait for fastbootd indefinitly.")
        print("WARNING! if your device does not boot to fastbootd PixelFlasher will hang and you'd have to kill it.")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot fastboot "
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot fastboot"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_sideload
    # ----------------------------------------------------------------------------
    def reboot_sideload(self):
        print(f"Rebooting device {self.id} for sideload ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot sideload "
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.reboot_sideload()
            return res

    # ----------------------------------------------------------------------------
    #                               Method install_apk
    # ----------------------------------------------------------------------------
    def install_apk(self, app, fastboot_included = False):
        if self.mode == 'adb' and get_adb():
            print(f"Installing {app} on device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} install \"{app}\""
            debug(theCmd)
            res = run_shell(theCmd)
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an errorwhile installing \"{app}\"")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
            else:
                print(f"{res.stdout}")
            return res
        if self.mode == 'f.b' and fastboot_included and get_fastboot():
            print("Device is in fastboot mode, will reboot to system and wait 60 seconds for system to load before installing ...")
            self.reboot_system()
            time.sleep(60)
            res = self.refresh_phone_mode()
            if self.mode == 'adb' and get_adb():
                res = self.install_apk(app)
            else:
                print("Please perform the install again when the device is in adb mode.")
            return res

    # ----------------------------------------------------------------------------
    #                               Method set_active
    # ----------------------------------------------------------------------------
    def set_active_slot(self, slot):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            print(f"Setting active slot to slot [{slot}] for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} --set-active={slot}"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method lock_bootloader
    # ----------------------------------------------------------------------------
    def lock_bootloader(self):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            # add a popup warning before continuing.
            print(f"Unlocking bootloader for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing lock"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method unlock_bootloader
    # ----------------------------------------------------------------------------
    def unlock_bootloader(self):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 5 seconds ...")
            time.sleep(5)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            # add a popup warning before continuing.
            print(f"Unlocking bootloader for device {self.id} ...")
            theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing unlock"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method enable_magisk_module
    # ----------------------------------------------------------------------------
    def enable_magisk_module(self, dirname):
        if self.mode == 'adb' and get_adb():
            print(f"Enabling magisk module {dirname} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_module
    # ----------------------------------------------------------------------------
    def disable_magisk_module(self, dirname):
        if self.mode == 'adb' and get_adb():
            print(f"Disabling magisk module {dirname} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'touch /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_modules
    # ----------------------------------------------------------------------------
    def disable_magisk_modules(self):
        print("Disabling magisk modules ...")
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
            debug(theCmd)
            res = run_shell(theCmd)
            print("Waiting 15 seconds ...")
            time.sleep(15)
            return self.disable_magisk_modules()

    # ----------------------------------------------------------------------------
    #                               Method refresh_phone_mode
    # ----------------------------------------------------------------------------
    def refresh_phone_mode(self):
        if self.mode == 'adb' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" devices"
            response = run_shell(theCmd)
            if self.id in response.stdout:
                self.mode = 'f.b'
        elif self.mode == 'f.b' and get_adb():
            theCmd = f"\"{get_adb()}\" devices"
            response = run_shell(theCmd)
            if self.id in response.stdout:
                self.mode = 'adb'


# ============================================================================
#                               Function run_shell
# ============================================================================
def run_shell(cmd):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='ISO-8859-1')
        wx.Yield()
        return response
    except Exception as e:
        raise e


# ============================================================================
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print(f"debug: {message}")


# ============================================================================
#                               Function get_connected_devices
# ============================================================================
def get_connected_devices():
    devices = []
    phones = []

    if get_adb():
        theCmd = f"\"{get_adb()}\" devices"
        response = run_shell(theCmd)
        if response.stdout:
            for device in response.stdout.split('\n'):
                if '\tdevice' in device or '\trecovery' in device or '\tsideload' in device:
                    with contextlib.suppress(Exception):
                        d_id = device.split("\t")
                        mode = d_id[1]
                        d_id = d_id[0]
                        true_mode = None
                        if mode in ('recovery', 'sideload'):
                            true_mode = mode
                        device = Device(d_id, 'adb', true_mode)
                        device.init('adb')
                        device_details = device.get_device_details()
                        devices.append(device_details)
                        phones.append(device)
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to determine Android Platform Tools version.\n")

    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")

    if get_fastboot():
        theCmd = f"\"{get_fastboot()}\" devices"
        response = run_shell(theCmd)
        for device in response.stdout.split('\n'):
            if '\tfastboot' in device:
                d_id = device.split("\t")
                d_id = d_id[0]
                device = Device(d_id, 'f.b')
                device.init('f.b')
                device_details = device.get_device_details()
                devices.append(device_details)
                phones.append(device)
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")

    set_phones(phones)
    return devices
