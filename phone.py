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
#                               Class Package
# ============================================================================
class Package():
    def __init__(self, value):
        self.value = value
        self.type = ''
        self.installed = False
        self.enabled = False
        self.user0 = False
        self.details = ''
        self.path = ''
        self.path2 = ''
        self.label = ''
        self.icon = ''


# ============================================================================
#                               Class Backup
# ============================================================================
class Backup():
    def __init__(self, value):
        self.value = value # sha1
        self.date = ''
        self.firmware = ''


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
        self._sys_oem_unlock_allowed = None
        self._ro_boot_flash_locked = None
        self._ro_boot_vbmeta_device_state = None
        self._vendor_boot_verifiedbootstate = None
        self._ro_product_first_api_level = None
        self._ro_boot_verifiedbootstate = None
        self._vendor_boot_vbmeta_device_state = None
        self._ro_boot_warranty_bit = None
        self._ro_warranty_bit = None
        self._ro_secure = None
        self._ro_zygote = None
        self._ro_vendor_product_cpu_abilist = None
        self._ro_vendor_product_cpu_abilist32 = None
        self._rooted = None
        self._unlocked = None
        self._magisk_version = None
        self._magisk_app_version = None
        self._magisk_version_code = None
        self._magisk_app_version_code = None
        self._magisk_detailed_modules = None
        self._magisk_modules_summary = None
        self._magisk_apks = None
        self._magisk_config_path = None
        self.packages = {}
        self.backups = {}

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
    #                               method get_package_details
    # ----------------------------------------------------------------------------
    def get_package_details(self, package):
        if self.mode != 'adb':
            return
        try:
            theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package {package}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                path = self.get_path_from_details(res.stdout)
                return res.stdout, path
            else:
                return '', ''
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list.")
            puml("#red:ERROR: Could not get package list;\n", True)
            return '', ''

    # -----------------------------------------------
    #    Function get_path_from_package_details
    # -----------------------------------------------
    def get_path_from_details(self, details):
        pattern = re.compile(r'Dexopt state:(?s).*?path:(.*?)\n(?!.*path:)', re.DOTALL)
        match = re.search(pattern, details)
        if match:
            return match[1].strip()
        else:
            return ''

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
                puml("#red:ERROR: adb command is not found!;\n", True)
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
                puml("#red:ERROR: fastboot command is not found!;\n", True)

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
                # USNF related props
                s_sys_oem_unlock_allowed = 'sys.oem_unlock_allowed'
                s_ro_boot_flash_locked = 'ro.boot.flash.locked'
                s_ro_boot_vbmeta_device_state = 'ro.boot.vbmeta.device_state'
                s_vendor_boot_verifiedbootstate = 'vendor.boot.verifiedbootstate'
                s_ro_product_first_api_level = 'ro.product.first_api_level'
                s_ro_boot_verifiedbootstate = 'ro.boot.verifiedbootstate'
                s_vendor_boot_vbmeta_device_state = 'vendor.boot.vbmeta.device_state'
                s_ro_boot_warranty_bit = 'ro.boot.warranty_bit'
                s_ro_warranty_bit = 'ro.warranty_bit'
                s_ro_secure = 'ro.secure'
                # Magisk zygote64_32 related props. https://forum.xda-developers.com/t/magisk-magisk-zygote64_32-enabling-32-bit-support-for-apps.4521029/
                s_ro_zygote = 'ro.zygote'
                s_ro_vendor_product_cpu_abilist = 'ro.vendor.product.cpu.abilist'
                s_ro_vendor_product_cpu_abilist32 = 'ro.vendor.product.cpu.abilist32'
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
                    elif s_sys_oem_unlock_allowed in line and not self._sys_oem_unlock_allowed:
                        self._sys_oem_unlock_allowed = self.extract_prop(s_sys_oem_unlock_allowed, line.strip())
                    elif s_ro_boot_flash_locked in line and not self._ro_boot_flash_locked:
                        self._ro_boot_flash_locked = self.extract_prop(s_ro_boot_flash_locked, line.strip())
                    elif s_ro_boot_vbmeta_device_state in line and not self._ro_boot_vbmeta_device_state:
                        self._ro_boot_vbmeta_device_state = self.extract_prop(s_ro_boot_vbmeta_device_state, line.strip())
                    elif s_vendor_boot_verifiedbootstate in line and not self._vendor_boot_verifiedbootstate:
                        self._vendor_boot_verifiedbootstate = self.extract_prop(s_vendor_boot_verifiedbootstate, line.strip())
                    elif s_ro_product_first_api_level in line and not self._ro_product_first_api_level:
                        self._ro_product_first_api_level = self.extract_prop(s_ro_product_first_api_level, line.strip())
                    elif s_ro_boot_verifiedbootstate in line and not self._ro_boot_verifiedbootstate:
                        self._ro_boot_verifiedbootstate = self.extract_prop(s_ro_boot_verifiedbootstate, line.strip())
                    elif s_vendor_boot_vbmeta_device_state in line and not self._vendor_boot_vbmeta_device_state:
                        self._vendor_boot_vbmeta_device_state = self.extract_prop(s_vendor_boot_vbmeta_device_state, line.strip())
                    elif s_ro_boot_warranty_bit in line and not self._ro_boot_warranty_bit:
                        self._ro_boot_warranty_bit = self.extract_prop(s_ro_boot_warranty_bit, line.strip())
                    elif s_ro_warranty_bit in line and not self._ro_warranty_bit:
                        self._ro_warranty_bit = self.extract_prop(s_ro_warranty_bit, line.strip())
                    elif s_ro_secure in line and not self._ro_secure:
                        self._ro_secure = self.extract_prop(s_ro_secure, line.strip())
                    elif s_ro_zygote in line and not self._ro_zygote:
                        self._ro_zygote = self.extract_prop(s_ro_zygote, line.strip())
                    elif s_ro_vendor_product_cpu_abilist in line and not self._ro_vendor_product_cpu_abilist:
                        self._ro_vendor_product_cpu_abilist = self.extract_prop(s_ro_vendor_product_cpu_abilist, line.strip())
                    elif s_ro_vendor_product_cpu_abilist32 in line and not self._ro_vendor_product_cpu_abilist32:
                        self._ro_vendor_product_cpu_abilist32 = self.extract_prop(s_ro_vendor_product_cpu_abilist32, line.strip())
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
    #                               property inactive_slot
    # ----------------------------------------------------------------------------
    @property
    def inactive_slot(self):
        if self.active_slot is None:
            return ''
        current_slot = self.active_slot
        if current_slot == 'a':
            return '_b'
        else:
            return '_a'

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
    #                               property sys_oem_unlock_allowed
    # ----------------------------------------------------------------------------
    @property
    def sys_oem_unlock_allowed(self):
        if self._sys_oem_unlock_allowed is None:
            return ''
        else:
            return self._sys_oem_unlock_allowed

    # ----------------------------------------------------------------------------
    #                               property ro_boot_flash_locked
    # ----------------------------------------------------------------------------
    @property
    def ro_boot_flash_locked(self):
        if self._ro_boot_flash_locked is None:
            return ''
        else:
            return self._ro_boot_flash_locked

    # ----------------------------------------------------------------------------
    #                               property ro_boot_vbmeta_device_state
    # ----------------------------------------------------------------------------
    @property
    def ro_boot_vbmeta_device_state(self):
        if self._ro_boot_vbmeta_device_state is None:
            return ''
        else:
            return self._ro_boot_vbmeta_device_state

    # ----------------------------------------------------------------------------
    #                               property vendor_boot_verifiedbootstate
    # ----------------------------------------------------------------------------
    @property
    def vendor_boot_verifiedbootstate(self):
        if self._vendor_boot_verifiedbootstate is None:
            return ''
        else:
            return self._vendor_boot_verifiedbootstate

    # ----------------------------------------------------------------------------
    #                               property ro_product_first_api_level
    # ----------------------------------------------------------------------------
    @property
    def ro_product_first_api_level(self):
        if self._ro_product_first_api_level is None:
            return ''
        else:
            return self._ro_product_first_api_level

    # ----------------------------------------------------------------------------
    #                               property ro_boot_verifiedbootstate
    # ----------------------------------------------------------------------------
    @property
    def ro_boot_verifiedbootstate(self):
        if self._ro_boot_verifiedbootstate is None:
            return ''
        else:
            return self._ro_boot_verifiedbootstate

    # ----------------------------------------------------------------------------
    #                               property vendor_boot_vbmeta_device_state
    # ----------------------------------------------------------------------------
    @property
    def vendor_boot_vbmeta_device_state(self):
        if self._vendor_boot_vbmeta_device_state is None:
            return ''
        else:
            return self._vendor_boot_vbmeta_device_state

    # ----------------------------------------------------------------------------
    #                               property ro_boot_warranty_bit
    # ----------------------------------------------------------------------------
    @property
    def ro_boot_warranty_bit(self):
        if self._ro_boot_warranty_bit is None:
            return ''
        else:
            return self._ro_boot_warranty_bit

    # ----------------------------------------------------------------------------
    #                               property ro_warranty_bit
    # ----------------------------------------------------------------------------
    @property
    def ro_warranty_bit(self):
        if self._ro_warranty_bit is None:
            return ''
        else:
            return self._ro_warranty_bit

    # ----------------------------------------------------------------------------
    #                               property ro_secure
    # ----------------------------------------------------------------------------
    @property
    def ro_secure(self):
        if self._ro_secure is None:
            return ''
        else:
            return self._ro_secure

    # ----------------------------------------------------------------------------
    #                               property ro_zygote
    # ----------------------------------------------------------------------------
    @property
    def ro_zygote(self):
        if self._ro_zygote is None:
            return ''
        else:
            return self._ro_zygote

    # ----------------------------------------------------------------------------
    #                               property ro_vendor_product_cpu_abilist
    # ----------------------------------------------------------------------------
    @property
    def ro_vendor_product_cpu_abilist(self):
        if self._ro_vendor_product_cpu_abilist is None:
            return ''
        else:
            return self._ro_vendor_product_cpu_abilist

    # ----------------------------------------------------------------------------
    #                               property ro_vendor_product_cpu_abilist32
    # ----------------------------------------------------------------------------
    @property
    def ro_vendor_product_cpu_abilist32(self):
        if self._ro_vendor_product_cpu_abilist32 is None:
            return ''
        else:
            return self._ro_vendor_product_cpu_abilist32

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
        if self.mode == 'adb':
            res = self.get_package_path(get_magisk_package(), True)
            if res != -1:
                return res
            self._rooted = None
            return None

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
                        self._magisk_version_code = f"{m[0][1]}"
                    else:
                        self._magisk_version = res.stdout
                        self._magisk_version_code = res.stdout
                        self._magisk_version_code = self._magisk_version.strip(':')
                    self._magisk_version = self._magisk_version.strip('\n')
            except Exception:
                try:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/adb/magisk/magisk32 -c\'\""
                    res = run_shell(theCmd)
                    if res.returncode == 0:
                        self._magisk_version = res.stdout.strip('\n')
                        self._magisk_version_code = self._magisk_version.strip(':')
                except Exception:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk version, assuming that it is not rooted.")
                    self._rooted = None
        return self._magisk_version

    # ----------------------------------------------------------------------------
    #                               property magisk_version_code
    # ----------------------------------------------------------------------------
    @property
    def magisk_version_code(self):
        if self._magisk_version_code is None:
            return ''
        else:
            return self._magisk_version_code

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
                puml("#red:ERROR: Could not get magisk sha1;\n", True)
                self._magisk_config_path = None
        return self._magisk_config_path

    # ----------------------------------------------------------------------------
    #                               method get_partitions
    # ----------------------------------------------------------------------------
    def get_partitions(self):
        if self.mode != 'adb':
            return -1
        if self.rooted:
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cd /dev/block/bootdevice/by-name/; ls -1 .\'\""
        else:
            theCmd = f"\"{get_adb()}\" -s {self.id} shell cd /dev/block/bootdevice/by-name/; ls -1 ."
        try:
            res = run_shell(theCmd)
            if res.returncode == 0:
                list = res.stdout.split('\n')
            else:
                return -1
            if not list:
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get partitions list.")
            puml("#red:ERROR: Could not get partitions list.;\n", True)
            return -1
        return list

    # ----------------------------------------------------------------------------
    #                               method get_magisk_backups
    # ----------------------------------------------------------------------------
    def get_magisk_backups(self):
        if self.mode != 'adb' or not self.rooted:
            return -1
        try:
            self.backups.clear()
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -l -d -1 /data/magisk_backup_*\'\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                list = res.stdout.split('\n')
            else:
                return -1
            if not list:
                return -1
            for item in list:
                if item != '':
                    regex = re.compile("d.+root\sroot\s\w+\s(.*)\s\/data\/magisk_backup_(.*)")
                    m = re.findall(regex, item)
                    if m:
                        backup_date = f"{m[0][0]}"
                        backup_sha1 = f"{m[0][1]}"
                    backup = Backup(backup_sha1)
                    backup.date = backup_date
                    with contextlib.suppress(Exception):
                        backup.firmware = self.get_firmware_from_boot(backup_sha1)
                    self.backups[backup_sha1] = backup
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get backup list.")
            puml("#red:ERROR: Could not get backup list.;\n", True)
            return -1
        return 0

    # ----------------------------------------------------------------------------
    #                      function get_firmware_from_boot
    # ----------------------------------------------------------------------------
    def get_firmware_from_boot(self, sha1):
        con = get_db()
        con.execute("PRAGMA foreign_keys = ON")
        con.commit()
        cursor = con.cursor()
        cursor.execute(f"SELECT package_sig FROM PACKAGE WHERE boot_hash = '{sha1}'")
        data = cursor.fetchall()
        if len(data) > 0:
            return data[0][0]
        else:
            return ''

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
                puml("#red:ERROR: Could not get magisk backups;\n", True)
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
                puml("#red:ERROR: Could not get magisk sha1;\n", True)
                _magisk_sha1 = ''
        return _magisk_sha1

    # ----------------------------------------------------------------------------
    #                               Method run_magisk_migration
    # ----------------------------------------------------------------------------
    def run_magisk_migration(self, sha1 = None):
        if self.mode == 'adb' and self.rooted:
            try:
                print("Making sure stock_boot.img is found on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls -l /data/adb/magisk/stock_boot.img\'\""
                res = run_shell(theCmd)
                # expect 0
                if res.returncode != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: /data/adb/magisk/stock_boot.img is not found!")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    print("Aborting run_migration ...\n")
                    return -2

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
                # Transfer boot image to the device
                print(f"Transfering {boot_img} to the device in /data/local/tmp/stock_boot.img ...")

                res = self.push_file(f"{boot_img}", "/data/local/tmp/stock_boot.img")
                if res != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {boot_img}")
                    return -1

                # copy stock_boot from /data/local/tmp folder
                print("Copying /data/local/tmp/stock_boot.img to /data/adb/magisk/stock_boot.img ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cp /data/adb/magisk/stock_boot.img /data/adb/magisk/stock_boot.img\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                # expect ret 0
                if res.returncode != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error.")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    print("Aborting Backup...\n")
                else:
                    print(res.stdout)

                # trigger run migration
                print("Triggering Magisk run_migration to create a Backup ...")
                res = self.run_magisk_migration(sha1)
                if res < 0:
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
    #                               Method delete
    # ----------------------------------------------------------------------------
    def delete(self, file_path: str, with_su = False, dir = False) -> int:
        """Method deletes a file on the device.

        Args:
            file_path:  Full file path
            with_su:    Perform the action as root (Default: False)
            dir:        Delete a directory instead of file (Default: False [file])

        Returns:
            0           if file is deleted or not found.
            -1          if an exception is raised.
        """
        flag = ''
        if dir:
            flag = 'r'
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    print(f"Deleting {file_path} from the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -{flag}f {file_path}\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}. Device is not rooted.")
            else:
                print(f"Deleting {file_path} from the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell rm -{flag}f {file_path}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method dump_partition
    # ----------------------------------------------------------------------------
    def dump_partition(self, file_path: str = '', slot: str = '', partition = '') -> int:
        """Method dumps active boot / init_boot partition on device.

        Args:
            file_path:      Full file path (Default in: /data/local/tmp/ <boot | init_boot>)
            partition:      If specified, then the specified partition will be dumped, otherwise it will be boot on init_boot
            slot:           If slot is specified, then it will dump the specificed slot instead of the active one. (Default: '')
                            The active slot selection only applies if partition is not specified.
                            If partition is specified, then the dump will be without the _slot, unless slot is also specified.

        Returns:
            0, dumped_path  if boot partition is dumped.
            -1, ''          if an exception is raised.
        """
        if self.mode != 'adb' and self.rooted:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not dump partition. Device must be in ADB mode and be rooted.")
            return -1, ''
        try:
            if partition == '':
                if slot not in ['a', 'b']:
                    slot = self.active_slot
                # decide on boot.img or init_boot.img
                if 'panther' in get_firmware_model() or 'cheetah' in get_firmware_model():
                    partition = 'init_boot'
                else:
                    partition = 'boot'
            if slot != '':
                partition = f"{partition}_{slot}"
            if not file_path:
                file_path = f"/data/local/tmp/{partition}.img"

            print(f"Dumping partition to file: {file_path} ...")
            puml(f":Dump Partition;\nnote right:Partition: {partition};\n", True)
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'dd if=/dev/block/bootdevice/by-name/{partition} of={file_path}\'\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0, file_path
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not dump the partition.")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                return -1, ''
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not dump the partition")
            return -1, ''

    # ----------------------------------------------------------------------------
    #                               Method su_cp_on_device
    # ----------------------------------------------------------------------------
    def su_cp_on_device(self, source: str, dest) -> int:
        """Method copies file as su from device to device.

        Args:
            source:     Source file path
            dest:       Destination file path

        Returns:
            0           if copy is succesful.
            -1          if an exception is raised.
        """
        if self.mode != 'adb' or not self.rooted:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not copy. Device is not in ADB mode or is not rooted.")
            return -1
        try:
            print(f"Copying {source} to {dest} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cp {source} {dest}\'\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print("Copy failed.")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Copy failed")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method check_file
    # ----------------------------------------------------------------------------
    def check_file(self, file_path: str, with_su = False) -> int:
        """Method checks if a file exists on the device.

        Args:
            file_path:  Full file path
            with_su:    Perform the action as root (Default: False)

        Returns:
            1,  matches       if file is found.
            0,  None          if file is not found.
            -1, None          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not check {file_path}. Device is not in ADB mode.")
            return -1, None
        try:
            if with_su:
                if self.rooted:
                    print(f"Checking for {file_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls {file_path}\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not check {file_path}. Device is not rooted.")
            else:
                print(f"Checking for {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell ls {file_path}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print(f"File: {file_path} is found on the device.")
                return 1, res.stdout.strip()
            else:
                print(f"File: {file_path} is not found on the device.")
                return 0, None
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not check {file_path}")
            return -1, None

    # ----------------------------------------------------------------------------
    #                               Method create_dir
    # ----------------------------------------------------------------------------
    def create_dir(self, dir_path: str, with_su = False) -> int:
        """Method creates a directory on the device.

        Args:
            dir_path:   Full directory path
            with_su:    Perform the action as root (Default: False)

        Returns:
            0           if directory is created.
            -1          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not check {dir_path}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    print(f"Creating directory {dir_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'mkdir -p {dir_path}\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create directory {dir_path}. Device is not rooted.")
            else:
                print(f"Creating directory {dir_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell mkdir -p {dir_path}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create directory: {dir_path}")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create directory: {dir_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method file_content
    # ----------------------------------------------------------------------------
    def file_content(self, file_path: str, with_su = False) -> int:
        """Method cats the file content.

        Args:
            file_path:  Full file path
            with_su:    Perform the action as root (Default: False)

        Returns:
            filecontent if it exists
            -1          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content of {file_path}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    print(f"Getting file content of {file_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cat {file_path}\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content of {file_path}. Device is not rooted.")
            else:
                print(f"Getting file content of {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell cat {file_path}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return res.stdout
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content: {file_path}")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content: {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method push_file
    # ----------------------------------------------------------------------------
    def push_file(self, local_file: str, file_path: str, with_su = False) -> int:
        """Method pushes a file to the device.

        Args:
            local_file: Local file path.
            file_path:  Full file path on the device
            with_su:        Perform the action as root (Default: False)

        Returns:
            0           if file is pushed.
            -1          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    filename = os.path.basename(urlparse(local_file).path)
                    remote_file = f"/data/local/tmp/{filename}"
                    res = self.push_file(local_file, remote_file, False)
                    if res != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {local_file}")
                        return -1
                    res = self.su_cp_on_device(remote_file, file_path)
                    if res != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not copy {remote_file}")
                        return -1
                    return 0
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not copy to {file_path}. Device is not rooted.")
                    return -1
            else:
                print(f"Pushing local file: {local_file} to the device: {file_path} ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} push \"{local_file}\" {file_path}"
                res = run_shell(theCmd)
                if res.returncode == 0:
                    print("Return Code: 0")
                    return 0
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method pull_file
    # ----------------------------------------------------------------------------
    def pull_file(self, remote_file: str, local_file: str, with_su = False) -> int:
        """Method pulls a file from the device.

        Args:
            remote_file:    Full file path on the device
            local_file:     Local file path.
            with_su:        Perform the action as root (Default: False)

        Returns:
            0               if file is pulled.
            -1              if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    filename = os.path.basename(urlparse(remote_file).path)
                    temp_remote_file = f"/data/local/tmp/{filename}"
                    res = self.su_cp_on_device(remote_file, temp_remote_file)
                    if res != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not copy {remote_file} to {temp_remote_file}. Device is not rooted.")
                        return -1
                    else:
                        remote_file = temp_remote_file
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}. Device is not rooted.")
                    return -1

            print(f"Pulling remote file: {remote_file} from the device to: {local_file} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} pull \"{remote_file}\" {local_file}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method set_file_permissions
    # ----------------------------------------------------------------------------
    def set_file_permissions(self, file_path: str, permissions: str = "755", with_su = False) -> int:
        """Method sets file permissions on the device.

        Args:
            permissions:    Permissions. (Default 755)
            file_path:      Full file path on the device
            with_su:        Perform the action as root (Default: False)

        Returns:
            0               On Success.
            -1              if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permissions on {file_path}. Device is not in ADB mode.")
            return -1
        try:
            if with_su:
                if self.rooted:
                    print(f"Setting permissions {permissions} on {file_path} as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'chmod {permissions} {file_path}\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permissions on {file_path}. Device is not rooted.")
            else:
                print(f"Setting permissions {permissions} on {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell chmod {permissions} {file_path}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"Return Code: {res.returncode}.")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permission on {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method push_aapt2
    # ----------------------------------------------------------------------------
    def push_aapt2(self, file_path = "/data/local/tmp/aapt2") -> int:
        """Method pushes aapt2 binary to the device.

        Args:
            file_path:      Full file path on the device (Default: /data/local/tmp/aapt2)

        Returns:
            0               On Success.
            -1              if an exception is raised.
        """
        # Transfer extraction script to the phone
        path_to_aapt2 = os.path.join(get_bundle_dir(),'bin', f"aapt2_{self.architecture}")
        res = self.push_file(f"{path_to_aapt2}", f"{file_path}")
        if res != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
            return -1
        # set the permissions.
        res = self.set_file_permissions(f"{file_path}", "755")
        if res != 0:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permission on {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method get_package_path
    # ----------------------------------------------------------------------------
    def get_package_path(self, pkg: str, check_details = True) -> str:
        """Method gets a package's apk path on device.

        Args:
            pkg:        Package

        Returns:
            pkg_path    on success returns package apk path.
            -1          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} path. Device is not in ADB mode.")
            return -1
        try:
            print(f"Getting package {pkg} path on the device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell pm path {pkg}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                pkg_path = res.stdout.split('\n')[0]
                pkg_path = pkg_path.split(':')[1]
                print(f"Package Path is: {pkg_path}")
                return pkg_path
            else:
                if check_details:
                    details, pkg_path = self.get_package_details(pkg)
                    if pkg_path != '':
                        print(f"Package Path is: {pkg_path}")
                        return pkg_path
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} path.")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                return -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} path.")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method get_package_label
    # ----------------------------------------------------------------------------
    def get_package_label(self, pkg: str, pkg_path = '') -> str:
        """Method package label (App name) given a package name.

        Args:
            pkg:        Package
            pkg_path:   Package APK path, if provided, the Method skips figuring it out (faster). Default ''

        Returns:
            label, icon on success returns label (App name) and Icon path.
            -1          if an exception is raised.
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} label. Device is not in ADB mode.")
            return -1, -1
        print()
        try:
            if pkg_path == '':
                pkg_path = self.get_package_path(f"{pkg}", True)
                if pkg_path == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} label.")
                    return -1, -1
                print(f"    Package Path: {pkg_path}")
            print(f"Getting package {pkg} label from the device ...")
            # theCmd = f"\"{get_adb()}\" -s {self.id} shell /data/local/tmp/aapt2 d badging {pkg_path} | grep \"application: label=\" |awk \"{{print $2}}\""
            theCmd = f"\"{get_adb()}\" -s {self.id} shell /data/local/tmp/aapt2 d badging {pkg_path} | grep \"application: label=\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                # print(res.stdout)
                regex = re.compile("application: label='(.*)' icon='(.*)'")
                m = re.findall(regex, res.stdout)
                if m:
                    pkg_label = f"{m[0][0]}"
                    pkg_icon = f"{m[0][1]}"
                print(f"{pkg} label is: {pkg_label}")
                return pkg_label, pkg_icon
            elif res.stderr.startswith("ERROR getting 'android:icon'"):
                # try another way
                theCmd = f"\"{get_adb()}\" -s {self.id} shell /data/local/tmp/aapt2 d badging {pkg_path} | grep \"application-label:\""
                res = run_shell(theCmd)
                # print(res.stdout)
                regex = re.compile("application-label:'(.*)'")
                m = re.findall(regex, res.stdout)
                if m:
                    pkg_label = f"{m[0]}"
                print(f"{pkg} label is: {pkg_label}")
                return pkg_label, ''
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} label.")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}")
                print(f"Stderr: {res.stderr}")
                return -1, -1
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} label.")
            return -1, -1

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
                        self._magisk_app_version_code = versionCode
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
    #                               property magisk_app_version_code
    # ----------------------------------------------------------------------------
    @property
    def magisk_app_version_code(self):
        if self._magisk_app_version_code is None:
            return ''
        else:
            return self._magisk_app_version_code

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
                    if sys.platform == "win32":
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'for FILE in /data/adb/modules/*; do echo $FILE; if test -f \"$FILE/disable\"; then echo \"state=disabled\"; else echo \"state=enabled\"; fi; cat \"$FILE/module.prop\"; echo; echo -----pf;done\'\""
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
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error when processing Magisk Modules.")
                            print(f"Return Code: {res.returncode}.")
                            print(f"Stdout: {res.stdout}.")
                            print(f"Stderr: {res.stderr}.")
                    else:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            modules = []
                            self._magisk_detailed_modules = res.stdout.split('\n')
                            for module in self._magisk_detailed_modules:
                                if module != '':
                                    m = Magisk(module)
                                    if self.mode == 'adb' and get_adb():
                                        # get the state by checking if there is a disable file in the module directory
                                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules/{module}/disable\'\""
                                        res = run_shell(theCmd)
                                        if res.returncode == 0:
                                            m.state = 'disabled'
                                        else:
                                            m.state = 'enabled'
                                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cat /data/adb/modules/{module}/module.prop\'\""
                                        res = run_shell(theCmd)
                                        if res.returncode == 0:
                                            module_prop = res.stdout.split('\n')
                                            setattr(m, 'id', '')
                                            setattr(m, 'version', '')
                                            setattr(m, 'versionCode', '')
                                            setattr(m, 'author', '')
                                            setattr(m, 'description', '')
                                            for line in module_prop:
                                                # ignore comment lines
                                                if line[:1] == "#":
                                                    continue
                                                if line.strip() != '' and '=' in line:
                                                    key, value = line.split('=', 1)
                                                    setattr(m, key, value)
                                            modules.append(m)
                            self._magisk_detailed_modules = modules
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error when processing Magisk Modules.")
                            print(f"Return Code: {res.returncode}.")
                            print(f"Stdout: {res.stdout}.")
                            print(f"Stderr: {res.stderr}.")
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
                mlist = ['stable', 'beta', 'canary', 'debug', 'alpha', 'delta', 'zygote64_32 stable', 'zygote64_32 beta', 'zygote64_32 canary', 'zygote64_32 debug', 'special']
                for i in mlist:
                    apk = self.get_magisk_apk_details(i)
                    if apk:
                        apks.append(apk)
                self._magisk_apks = apks
            except Exception as e:
                self._magisk_apks is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads link: {i} processing\nException: {e}")
        return self._magisk_apks

    # ----------------------------------------------------------------------------
    #                               Function get_magisk_apk_details
    # ----------------------------------------------------------------------------
    def get_magisk_apk_details(self, channel):
        ma = MagiskApk(channel)
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
        elif channel == 'zygote64_32 stable':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/stable.json"
        elif channel == 'zygote64_32 beta':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/beta.json"
        elif channel == 'zygote64_32 canary':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/canary.json"
        elif channel == 'zygote64_32 debug':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/debug.json"
        elif channel == 'special':
            url = ""
            setattr(ma, 'version', "f9e82c9e")
            setattr(ma, 'versionCode', "25203")
            setattr(ma, 'link', "https://forum.xda-developers.com/attachments/app-debug-apk.5725759/")
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', 'com.topjohnwu.magisk')
            release_notes = """
## 2022.10.03 Special Magisk v25.2 Build\n\n
This is a special Magisk build by XDA Member [gecowa6967](https://forum.xda-developers.com/m/gecowa6967.11238881/)\n\n
- Based on build versionCode: 25203 versionName: f9e82c9e\n
- Modified to disable loading modules.\n
- Made to recover from bootloops due to bad / incompatible Modules.\n\n
### Steps to follow
If your are bootlooping due to bad modules, and if you load stock boot image, it works fine but you're not rooted to removed modules, then follow these steps.\n\n
- Uninstall the currently installed Magisk Manager.\n
- Install this special version.\n
- Create a patched boot / init_boot using this Magisk Manager version.\n
- Flash the patched image.\n
- You should now be able to get root access, and your modules will not load.\n
- Delete / Disable suspect modules.\n
- Uninstall this Magisk Manager.\n
- Install your Magisk Manager of choice.\n
- Create patched boot / init_boot image.\n
- Flash the patched image.\n
- You should be good to go.\n\n
### Full Details: [here](https://forum.xda-developers.com/t/magisk-general-support-discussion.3432382/page-2667#post-87520397)\n
            """
            setattr(ma, 'release_notes', release_notes)
            return ma
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
            setattr(ma, 'version', data['magisk']['version'])
            setattr(ma, 'versionCode', data['magisk']['versionCode'])
            setattr(ma, 'link', data['magisk']['link'])
            note_link = data['magisk']['note']
            setattr(ma, 'note_link', note_link)
            setattr(ma, 'package', 'com.topjohnwu.magisk')
            if channel == 'alpha':
                # Magisk alpha app link is not a full url, build it from url
                setattr(ma, 'link', f"https://github.com/vvb2060/magisk_files/raw/alpha/{ma.link}")
                setattr(ma, 'note_link', "https://raw.githubusercontent.com/vvb2060/magisk_files/alpha/README.md")
                setattr(ma, 'package', 'io.github.vvb2060.magisk')
            elif channel == 'delta':
                setattr(ma, 'package', 'io.github.huskydg.magisk')
            # Get the note contents
            headers = {}
            response = requests.request("GET", ma.note_link, headers=headers, data=payload)
            setattr(ma, 'release_notes', response.text)
            return ma
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links: {url} processing\nException: {e}")
            return

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
                puml("#red:ERROR: adb command is not found;\n", True)
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
        puml(f":Rebooting device {self.id} to system;\n", True)
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
        puml(f":Rebooting device {self.id} to recovery;\n", True)
        if self.mode == 'adb' and get_adb():
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot recovery "
            debug(theCmd)
            return run_shell(theCmd)
        elif self.mode == 'f.b' and get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot recovery"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_download
    # ----------------------------------------------------------------------------
    def reboot_download(self):
        if self.mode == 'adb' and get_adb():
            print(f"Rebooting device {self.id} to download ...")
            puml(f":Rebooting device {self.id} to download;\n", True)
            theCmd = f"\"{get_adb()}\" -s {self.id} reboot download "
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method reboot_safemode
    # ----------------------------------------------------------------------------
    def reboot_safemode(self):
        if self.mode == 'adb' and get_adb() and self.rooted:
            print(f"Rebooting device {self.id} to safe mode ...")
            puml(f":Rebooting device {self.id} to safe mode;\n", True)
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'setprop persist.sys.safemode 1\'\""
            debug(theCmd)
            run_shell(theCmd)
            self.reboot_system()

    # ----------------------------------------------------------------------------
    #                               Method reboot_bootloader
    # ----------------------------------------------------------------------------
    def reboot_bootloader(self, fastboot_included = False):
        print(f"Rebooting device {self.id} to bootloader ...")
        puml(f":Rebooting device {self.id} to bootloader;\n", True)
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
        puml(f":Rebooting device {self.id} to fastbootd;\n", True)
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
        puml(f":Rebooting device {self.id} to sideload;\n", True)
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
    def install_apk(self, app, fastboot_included = False, owner_playstore = False):
        if self.mode == 'adb' and get_adb():
            print(f"Installing {app} on device ...")
            puml(f":Installing {app};\n", True)
            if owner_playstore:
                puml("note right:Set owner to be Play Store;\n")
                theCmd = f"\"{get_adb()}\" -s {self.id} install -i \"com.android.vending\" -r \"{app}\""
            else:
                theCmd = f"\"{get_adb()}\" -s {self.id} install -r \"{app}\""
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
            puml(f":Setting Active slot to [{slot}];\n", True)
            theCmd = f"\"{get_fastboot()}\" -s {self.id} --set-active={slot}"
            debug(theCmd)
            return run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               Method erase_partition
    # ----------------------------------------------------------------------------
    def erase_partition(self, partition):
        if self.mode == 'adb' and get_adb():
            self.reboot_bootloader()
            print("Waiting 10 seconds ...")
            time.sleep(10)
            self.refresh_phone_mode()
        if self.mode == 'f.b' and get_fastboot():
            print(f"Erasing Partition [{partition}] for device {self.id} ...")
            puml(f":Erasing Partition [{partition}];\n", True)
            theCmd = f"\"{get_fastboot()}\" -s {self.id} erase {partition}"
            debug(theCmd)
            # return run_shell(theCmd)
            return

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
            # TODO add a popup warning before continuing.
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
            puml(":Enable magisk module;\n", True)
            puml(f"note right:{dirname};\n")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            puml(f"#red:ERROR: Device {self.id} is not in adb mode;\n", True)
            return 1

    # ----------------------------------------------------------------------------
    #                               Method open_shell
    # ----------------------------------------------------------------------------
    def open_shell(self):
        if self.mode == 'adb' and get_adb():
            print(f"Opening an adb shell command for device: {self.id} ...")
            puml(":Opening an adb shell command;\n", True)
            theCmd = f"\"{get_adb()}\" -s {self.id} shell"
            debug(theCmd)
            subprocess.Popen(theCmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            puml("#red:ERROR: The Device {self.id} is not in adb mode;\n", True)
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_module
    # ----------------------------------------------------------------------------
    def disable_magisk_module(self, dirname):
        if self.mode == 'adb' and get_adb():
            print(f"Disabling magisk module {dirname} ...")
            puml(":Disable magisk module;\n", True)
            puml(f"note right:{dirname};\n")
            theCmd = f"\"{get_adb()}\" -s {self.id} wait-for-device shell magisk --remove-modules"
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'touch /data/adb/modules/{dirname}/disable\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            return 0
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device {self.id} is not in adb mode.")
            puml("#red:ERROR: The Device {self.id} is not in adb mode;\n", True)
            return 1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_modules
    # ----------------------------------------------------------------------------
    def disable_magisk_modules(self):
        print("Disabling magisk modules ...")
        puml(":SOS Disable magisk modules;\n", True)
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


    # ----------------------------------------------------------------------------
    #                               method perform_package_action
    # ----------------------------------------------------------------------------
    def perform_package_action(self, pkg, action, isSystem):
        # possible actions 'uninstall', 'disable', 'enable'
        if self.mode != 'adb':
            return
        try:
            if action == 'uninstall':
                if isSystem:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm uninstall -k --user 0 {pkg}"
                else:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm uninstall {pkg}"
            elif action == 'disable':
                if isSystem:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm uninstall -k --user 0 {pkg}"
                else:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm disable-user {pkg}"
            elif action == 'enable':
                if isSystem:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm install-existing {pkg}"
                else:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell pm enable {pkg}"
            elif action == 'launch':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1"

            res = run_shell2(theCmd)
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not {action} {pkg}.")


    # ----------------------------------------------------------------------------
    #                               method get_package_list
    # ----------------------------------------------------------------------------
    def get_package_list(self, state = ''):
        # possible options 'all', 'all+uninstalled', 'disabled', 'enabled', 'system', '3rdparty', 'user0'
        if self.mode != 'adb':
            return
        try:
            if state == 'all':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages"
            elif state == 'all+uninstalled':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -u"
            elif state == 'disabled':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -d"
            elif state == 'enabled':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -e"
            elif state == 'system':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -s"
            elif state == '3rdparty':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -3"
            elif state == 'user0':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -s --user 0"

            res = run_shell(theCmd)
            if res.returncode == 0:
                return res.stdout.replace('package:','')
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list.")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            return None
        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list.")
            return None


    # ============================================================================
    #                               method get_detailed_packages
    # ============================================================================
    def get_detailed_packages(self):
        if self.mode != 'adb':
            return -1
        try:
            self.packages.clear()
            # get labels
            labels = get_labels()
            # Get all packages including uninstalled ones
            list = self.get_package_list('all+uninstalled')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '':
                    package = Package(item)
                    package.type = "System"
                    package.installed = False
                    with contextlib.suppress(Exception):
                        package.label = labels[item]
                    self.packages[item] = package

            # Get all packages
            list = self.get_package_list('all')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '' and item in self.packages:
                    self.packages[item].installed = True

            # Get 3rd party packages
            list = self.get_package_list('3rdparty')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '' and item in self.packages:
                    self.packages[item].type = '3rd Party'

            # Get disabled packages
            list = self.get_package_list('disabled')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '' and item in self.packages:
                    self.packages[item].enabled = False

            # Get enabled packages
            list = self.get_package_list('enabled')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '' and item in self.packages:
                    self.packages[item].enabled = True

            # Get user 0 packages
            list = self.get_package_list('user0')
            if not list:
                return -1
            for item in list.split("\n"):
                if item != '' and item in self.packages:
                    self.packages[item].user0 = True

        except Exception as e:
            print(e)
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list.")
            puml("#red:ERROR: Could not get package list;\n", True)
            return -1
        return 0


# ============================================================================
#                               Function run_shell
# ============================================================================
# We use this when we want to capture the returncode and also selectively
# output what we want to console. Nothing is sent to console, both stdout and
# stderr are only available when the call is completed.
def run_shell(cmd, timeout=None):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='ISO-8859-1', errors="replace", timeout=timeout)
        wx.Yield()
        return response
    except subprocess.TimeoutExpired as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command timed out after {timeout} seconds")
        puml("#red:Command timed out;\n", True)
        puml(f"note right\n{e}\nend note\n")
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell")
        print(e)
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e


# ============================================================================
#                               Function run_shell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
# no returncode is available.
def run_shell2(cmd, timeout=None):
    try:
        class obj(object):
            pass

        response = obj()
        proc = subprocess.Popen(f"{cmd}", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='ISO-8859-1', errors="replace")

        print
        stdout = ''
        start_time = time.time()
        while True:
            line = proc.stdout.readline()
            wx.Yield()
            if line.strip() != "":
                print(line.strip())
                stdout += line
            if not line:
                break
            if timeout is not None and time.time() > start_time + timeout:
                proc.terminate()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command timed out after {timeout} seconds")
                puml("#red:Command timed out;\n", True)
                puml(f"note right\nCommand timed out after {timeout} seconds\nend note\n")
                return None
        proc.wait()
        response.stdout = stdout
        return response
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell2")
        print(e)
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
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

    try:
        if get_adb():
            theCmd = f"\"{get_adb()}\" devices"
            response = run_shell(theCmd)
            if response.stdout:
                for device in response.stdout.split('\n'):
                    if 'device' in device or 'recovery' in device or 'sideload' in device:
                        with contextlib.suppress(Exception):
                            d_id = device.split("\t")
                            mode = d_id[1].strip()
                            d_id = d_id[0].strip()
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
                if 'fastboot' in device:
                    d_id = device.split("\t")
                    d_id = d_id[0].strip()
                    device = Device(d_id, 'f.b')
                    device.init('f.b')
                    device_details = device.get_device_details()
                    devices.append(device_details)
                    phones.append(device)
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")

        set_phones(phones)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while scanning for devices.")
        print(e)
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")

    return devices
