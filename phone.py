#!/usr/bin/env python

import contextlib
import re
import subprocess
import time
import traceback
from datetime import datetime
from urllib.parse import urlparse

from constants import *
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
        self.magisk_denylist = False
        self.details = ''
        self.path = ''
        self.path2 = ''
        self.label = ''
        self.icon = ''
        self.uid = ''


# ============================================================================
#                               Class Backup
# ============================================================================
class Backup():
    def __init__(self, value):
        self.value = value # sha1
        self.date = ''
        self.firmware = ''


# ============================================================================
#                               Class Vbmeta
# ============================================================================
class Vbmeta():
    def __init__(self):
        self.clear()

    def clear(self):
        self.type = '' # one of ["a_only", "ab", "none"]
        self.verity_a = None
        self.verity_b = None
        self.verification_a = None
        self.verification_b = None

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
#                               Class DeviceProps
# ============================================================================
class DeviceProps:
    def __init__(self):
        self.property = {}

    def get(self, key):
        return self.property.get(key, "Property not found")

    def upsert(self, key, value):
        self.property[key] = value


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
        self._rooted = None
        self._magisk_version = None
        self._magisk_app_version = None
        self._magisk_version_code = None
        self._magisk_app_version_code = None
        self._get_magisk_detailed_modules = None
        self._magisk_modules_summary = None
        self._magisk_apks = None
        self._magisk_config_path = None
        self._apatch_version = None
        self._apatch_app_version = None
        self._apatch_version_code = None
        self._apatch_app_version_code = None
        self._has_init_boot = None
        self._kernel = None
        self.packages = {}
        self.backups = {}
        self.vbmeta = {}
        self.props = {}
        # Get vbmeta details
        self.vbmeta = self.get_vbmeta_details()

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
    #                               property unlock_ability
    # ----------------------------------------------------------------------------
    @property
    def unlock_ability(self):
        if self.mode == 'adb':
            return
        try:
            theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing get_unlock_ability"
            res = run_shell(theCmd)
            if res.returncode != 0:
                return 'UNKNOWN'
            lines = (f"{res.stderr}{res.stdout}").splitlines()
            for line in lines:
                if "get_unlock_ability:" in line:
                    value = line.split("get_unlock_ability:")[1].strip()
                    if value == '1':
                        return "Yes"
                    elif value == '0':
                        return "No"
                    else:
                        return "UNKNOWN"
            return 'UNKNOWN'  # Value not found
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get unlock ability.")
            puml("#red:ERROR: Could not get unlock ability;\n", True)
            return 'UNKNOWN'

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
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get_package_details.")
            puml("#red:ERROR: Could not get_package_details;\n", True)
            return '', ''

    # ----------------------------------------------------------------------------
    #                               method get_battery_details
    # ----------------------------------------------------------------------------
    def get_battery_details(self):
        if self.mode != 'adb':
            return
        try:
            theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys battery"
            res = run_shell(theCmd)
            if res.returncode == 0:
                # path = self.get_path_from_details(res.stdout)
                return res.stdout #, path
            else:
                return '', ''
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get battery details.")
            puml("#red:ERROR: Could not get battery details;\n", True)
            return '', ''

    # -----------------------------------------------
    #    Function get_path_from_package_details
    # -----------------------------------------------
    def get_path_from_details(self, details):
        try:
            pattern = re.compile(r'(?s)Dexopt state:.*?path:(.*?)\n(?!.*path:)', re.DOTALL)
            match = re.search(pattern, details)
            if match:
                return match[1].strip()
            else:
                return ''
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get_path_from_package_details.")
            puml("#red:ERROR: Could not get_path_from_package_details;\n", True)

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
        """
            Retrieves device information based on the mode of operation.

            If the mode is 'adb', it uses the `getprop` command to fetch the device information using ADB.
            If the mode is 'f.b', it uses the `getvar all` command to fetch the device information using Fastboot.

            Returns:
                str: The device information.

            Raises:
                RuntimeError: If the ADB or Fastboot command is not found.

            Example:
                ```python
                phone = Phone()
                info = phone.device_info()
                print(info)
                ```
        """
        if self.mode == 'adb':
            if get_adb():
                if self.rooted:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/bin/getprop\'\""
                else:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell /bin/getprop"
                device_info = run_shell(theCmd)
                if device_info.returncode == 127 or "/system/bin/sh: /bin/getprop: not found" in device_info.stdout:
                    if self.rooted:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'getprop\'\""
                    else:
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
        try:
            device_props = DeviceProps()
            if mode == 'f.b':
                device_info = self.fastboot_device_info
            else:
                device_info = self.adb_device_info

            if device_info:
                for line in device_info.split('\n'):
                    if not line or ':' not in line:
                        continue

                    line = line.strip()
                    if mode == 'f.b':
                        key, value = line.split(':', 1)
                        key = key.replace('(bootloader) ', 'bootloader_')
                    else:
                        key, value = line.split(': ', 1)
                        key = key.strip('[]')
                        value = value.strip('[]')

                    device_props.upsert(key, value)
                self.props = device_props

            # set has_init_boot
            self._has_init_boot = False
            if self.hardware in KNOWN_INIT_BOOT_DEVICES:
                self._has_init_boot = True
            partitions = self.get_partitions()
            if partitions != -1 and ('init_boot' in partitions or 'init_boot_a' in partitions or 'init_boot_b' in partitions):
                self._has_init_boot = True

        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not init device class")
            puml("#red:ERROR: Could not get_package_details;\n", True)

    # ----------------------------------------------------------------------------
    #                               method get_prop
    # ----------------------------------------------------------------------------
    def get_prop(self, prop, prop2=None):
        if self.props is None:
            return ''
        if self.mode == "f.b":
            res = self.props.get(f"bootloader_{prop}")
            # debug(f"prop: {prop} value: [{res}]")
            if res == 'Property not found' or res is None:
                if not prop2:
                    # debug(f"Property {prop} not found.")
                    return ''
                res = self.props.get(f"bootloader_{prop2}")
                # debug(f"prop2: {prop2} value: [{res}]")
                if res == 'Property not found' or res is None:
                    # debug(f"Bootloader property {prop} and {prop2} are not found.")
                    return ''
                return res
        else:
            res = self.props.get(prop)
            # debug(f"prop: {prop} value: [{res}]")
            if res == 'Property not found' or res is None:
                if prop2:
                    res = self.props.get(prop2)
                    # debug(f"prop2: {prop2} value: [{res}]")
                    if res == 'Property not found' or res is None:
                        # debug(f"Bootloader property {prop} and {prop2} are not found.")
                        return ''
                    return res
                else:
                    # debug(f"Property {prop} not found.")
                    return ''
        return res

    # ----------------------------------------------------------------------------
    #                               method dump_prop
    # ----------------------------------------------------------------------------
    def dump_props(self):  # sourcery skip: use-join
        print("\nDumping properties ...")
        data = ''
        for key, value in self.props.property.items():
            data += f"[{key}]: [{value}]\n"
        print(data)

    # ----------------------------------------------------------------------------
    #                               property has_init_boot
    # ----------------------------------------------------------------------------
    @property
    def has_init_boot(self):
        if self._has_init_boot is None:
            return False
        else:
            return self._has_init_boot

    # ----------------------------------------------------------------------------
    #                               property active_slot
    # ----------------------------------------------------------------------------
    @property
    def active_slot(self):
        res = self.get_prop('current-slot', 'ro.boot.slot_suffix')
        if not res:
            return ''
        if res != '':
            res = res.replace("_", "")
        return res

    # ----------------------------------------------------------------------------
    #                               property inactive_slot
    # ----------------------------------------------------------------------------
    @property
    def inactive_slot(self):
        if self.active_slot is None:
            return ''
        if self.active_slot == 'a':
            return 'b'
        else:
            return 'a'

    # ----------------------------------------------------------------------------
    #                               property build
    # ----------------------------------------------------------------------------
    @property
    def build(self):
        try:
            build =  self.get_prop('ro.build.id')
            if build is not None and build != '':
                return build
            build =  self.ro_build_fingerprint
            if self.ro_build_fingerprint != '':
                return build.split('/')[3]
            else:
                return ''
        except Exception:
            return ''

    # ----------------------------------------------------------------------------
    #                               property api_level
    # ----------------------------------------------------------------------------
    @property
    def firmware_date(self):
        if self.build:
            build_date_match = re.search(r'\b(\d{6})\b', self.build.lower())
            if build_date_match:
                build_date = build_date_match[1]
                return int(build_date)

    # ----------------------------------------------------------------------------
    #                               property api_level
    # ----------------------------------------------------------------------------
    @property
    def api_level(self):
        return self.get_prop('ro.build.version.sdk')

    # ----------------------------------------------------------------------------
    #                               property hardware
    # ----------------------------------------------------------------------------
    @property
    def hardware(self):
        res = self.get_prop('product', 'ro.hardware')
        if res:
            return res
        else:
            return ''

    # ----------------------------------------------------------------------------
    #                               property architecture
    # ----------------------------------------------------------------------------
    @property
    def architecture(self):
        return self.get_prop('ro.product.cpu.abi')

    # ----------------------------------------------------------------------------
    #                               property ro_build_fingerprint
    # ----------------------------------------------------------------------------
    @property
    def ro_build_fingerprint(self):
        res = self.get_prop('ro.build.fingerprint')
        if res == '':
            return f"{self.get_prop('ro.product.brand')}/{self.get_prop('ro.product.name')}/{self.get_prop('ro.product.device')}:{self.get_prop('ro.build.version.release')}/{self.get_prop('ro.build.id')}/{self.get_prop('ro.build.version.incremental')}:{self.get_prop('ro.build.type')}/{self.get_prop('ro.build.tags')}"

    # ----------------------------------------------------------------------------
    #                               property ro_boot_flash_locked
    # ----------------------------------------------------------------------------
    @property
    def ro_boot_flash_locked(self):
        res = self.get_prop('ro.boot.flash.locked')
        if res == '0':
            add_unlocked_device(self.id)
        return res

    # ----------------------------------------------------------------------------
    #                               property unlocked
    # ----------------------------------------------------------------------------
    @property
    def unlocked(self):
        res = self.get_prop('unlocked')
        if res != 'yes':
            return False
        add_unlocked_device(self.id)
        return True

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
    #                               property kernel
    # ----------------------------------------------------------------------------
    @property
    def kernel(self):
        if self._kernel is None and self.mode == 'adb':
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell uname -a"
                res = run_shell(theCmd)
                if res.returncode == 0:
                    self._kernel = res.stdout.strip('\n')
                    match = re.search(r"\b(\d+\.\d+\.\d+-android\d+)\b", self._kernel)
                    if match:
                        self._kmi = match[1]
                    else:
                        self._kmi = None
            except Exception:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get kernel information.")
                traceback.print_exc()
                self._rooted = None
        return self._kernel

    # ----------------------------------------------------------------------------
    #                               property kmi
    # ----------------------------------------------------------------------------
    @property
    def kmi(self):
        try:
            match = re.search(r"\b(\d+\.\d+\.\d+-android\d+)\b", self.kernel)
            if match:
                return match[1]
            else:
                return ''
        except Exception:
            return ''

    # ----------------------------------------------------------------------------
    #                               property magisk_path
    # ----------------------------------------------------------------------------
    @property
    def magisk_path(self):
        try:
            magisk_path = get_magisk_package()
            if self.mode == 'adb' and magisk_path is not None and magisk_path != '':
                res = self.get_package_path(magisk_path, True)
                if res != -1:
                    return res
                self._rooted = None
                return None
        except Exception:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk path")
            traceback.print_exc()
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
                    traceback.print_exc()
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
                traceback.print_exc()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk sha1.")
                puml("#red:ERROR: Could not get magisk sha1;\n", True)
                self._magisk_config_path = None
        return self._magisk_config_path

    # ----------------------------------------------------------------------------
    #                               property current_device_print
    # ----------------------------------------------------------------------------
    @property
    def current_device_print(self):
        return process_dict(the_dict=self.props.property, add_missing_keys=True, pif_flavor=True)

    # ----------------------------------------------------------------------------
    #                               property current_device_props_in_json
    # ----------------------------------------------------------------------------
    @property
    def current_device_props_as_json(self):  # sourcery skip: use-join
        return json.dumps(self.props.property, indent=4)

    # ----------------------------------------------------------------------------
    #                               method get_partitions
    # ----------------------------------------------------------------------------
    def get_partitions(self):
        try:
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
                traceback.print_exc()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get partitions list.")
                puml("#red:ERROR: Could not get partitions list.;\n", True)
                return -1
            return list
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_partitions.")
            puml("#red:Encountered an error in get_partitions.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               method get_verity_verification
    # ----------------------------------------------------------------------------
    def get_verity_verification(self, item):
        if self.mode != 'adb':
            return -1
        if not self.rooted:
            return -1

        try:
            res = self.push_avbctl()
            if res != 0:
                return -1

            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/local/tmp/avbctl get-{item}\'\""
            print(f"Checking {item} status: ...")
            res = run_shell(theCmd)
            if res.returncode == 0:
                return res.stdout
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}")
            print(f"Stderr: {res.stderr}")
            return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get {item} status.")
            puml(f"#red:ERROR: Could not get {item} status.;\n", True)
            return -1

    # ----------------------------------------------------------------------------
    #                               method reset_ota_update
    # ----------------------------------------------------------------------------
    def reset_ota_update(self):
        if self.mode != 'adb':
            return -1
        if not self.rooted:
            return -1

        try:
            res = self.push_update_engine_client()
            if res != 0:
                return -1

            print("Cancelling onging OTA update (if one is in progress, ignore errors) ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/local/tmp/update_engine_client --cancel\'\""
            res = run_shell2(theCmd)
            print("Resetting an already applied update (if one exists) ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/local/tmp/update_engine_client --reset_status\'\""
            res = run_shell2(theCmd)
            if res.returncode == 0:
                return res.stdout
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}")
            print(f"Stderr: {res.stderr}")
            return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an exception if reset_ota_update function.")
            puml(f"#red:ERROR: Encountered an exception if reset_ota_update function.;\n", True)
            return -1

    # ----------------------------------------------------------------------------
    #                               method get_vbmeta_details
    # ----------------------------------------------------------------------------
    def get_vbmeta_details(self):
        if self.mode != 'adb' or not self.rooted:
            return None
        try:
            self.vbmeta.clear()
            vbmeta_a = ''
            vbmeta_b = ''
            vbmeta_a_only = ''
            vbmeta = Vbmeta()
            vbmeta.type = 'none'
            partitions = self.get_partitions()

            if "vbmeta_a" in partitions:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'dd if=/dev/block/bootdevice/by-name/vbmeta_a bs=1 skip=123 count=1 status=none | xxd -p\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    vbmeta.type = 'ab'
                    vbmeta_a = int(res.stdout.strip('\n'))
            if "vbmeta_b" in partitions:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'dd if=/dev/block/bootdevice/by-name/vbmeta_b bs=1 skip=123 count=1 status=none | xxd -p\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    vbmeta.type = 'ab'
                    vbmeta_b = int(res.stdout.strip('\n'))
            if "vbmeta_a" not in partitions and "vbmeta_b" not in partitions and "vbmeta" in partitions:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'dd if=/dev/block/bootdevice/by-name/vbmeta bs=1 skip=123 count=1 status=none | xxd -p\'\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    vbmeta.type = 'a_only'
                    vbmeta_a_only = int(res.stdout.strip('\n'))

            if vbmeta_a == 0:
                vbmeta.verity_a = True
                vbmeta.verification_a = True
            elif vbmeta_a == 1:
                vbmeta.verity_a = False
                vbmeta.verification_a = True
            elif vbmeta_a == 2:
                vbmeta.verity_a = True
                vbmeta.verification_a = False
            elif vbmeta_a == 3:
                vbmeta.verity_a = False
                vbmeta.verification_a = False

            if vbmeta_b == 0:
                vbmeta.verity_b = True
                vbmeta.verification_b = True
            elif vbmeta_b == 1:
                vbmeta.verity_b = False
                vbmeta.verification_b = True
            elif vbmeta_b == 2:
                vbmeta.verity_b = True
                vbmeta.verification_b = False
            elif vbmeta_b == 3:
                vbmeta.verity_b = False
                vbmeta.verification_b = False

            if vbmeta.type == "a_only":
                if vbmeta_a_only == 0:
                    vbmeta.verity_a = True
                    vbmeta.verification_a = True
                elif vbmeta_a_only == 1:
                    vbmeta.verity_a = False
                    vbmeta.verification_a = True
                elif vbmeta_a_only == 2:
                    vbmeta.verity_a = True
                    vbmeta.verification_a = False
                elif vbmeta_a_only == 3:
                    vbmeta.verity_a = False
                    vbmeta.verification_a = False

            self.vbmeta = vbmeta
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get vbmeta details.")
            puml("#red:ERROR: Could not get vbmeta details.;\n", True)
            return vbmeta
        return vbmeta

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
                if item:
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
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get backup list.")
            puml("#red:ERROR: Could not get backup list.;\n", True)
            return -1
        return 0

    # ----------------------------------------------------------------------------
    #                      function get_firmware_from_boot
    # ----------------------------------------------------------------------------
    def get_firmware_from_boot(self, sha1):
        try:
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
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting firmware from boot.")
            puml("#red:Encountered an error while while getting firmware from boot.;\n")
            traceback.print_exc()

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
                traceback.print_exc()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk backups.")
                puml("#red:ERROR: Could not get magisk backups;\n", True)
                _magisk_backups = None
        if _magisk_backups:
            return _magisk_backups
        else:
            return ''

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
                traceback.print_exc()
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk sha1.")
                puml("#red:ERROR: Could not get magisk sha1;\n", True)
                _magisk_sha1 = ''
        if _magisk_sha1:
            return _magisk_sha1
        else:
            return ''

    # ----------------------------------------------------------------------------
    #                               method exec_magisk_settings
    # ----------------------------------------------------------------------------
    def exec_magisk_settings(self, data):
        if self.mode != 'adb' or not self.rooted:
            return
        try:
            if not data:
                return -1

            config = get_config()
            config_path = get_config_path()
            if config.use_busybox_shell:
                busybox_shell_cmd = "/data/adb/magisk/busybox ash"
            else:
                busybox_shell_cmd = ""
            script_path = "/data/local/tmp/pfmagisk_settings.sh"
            exec_cmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'{busybox_shell_cmd} {script_path}\'\""
            the_script = os.path.join(config_path, 'tmp', 'pfmagisk_settings.sh')

            # create the script
            with open(the_script.strip(), "w", encoding="ISO-8859-1", errors="replace", newline='\n') as f:
                # data += "\n"
                f.write(data)
                puml(f"note right\nMagisk update script\n====\n{data}\nend note\n")
            print("PixelFlasher Magisk update script contents:")
            print(f"___________________________________________________\n{data}")
            print("___________________________________________________\n")

            # Transfer Magisk update script to the phone
            res = self.push_file(f"{the_script}", script_path, with_su=False)
            if res != 0:
                print("Aborting ...\n")
                puml("#red:Failed to transfer Magisk update script to the phone;\n")
                return -1

            # set the permissions.
            res = self.set_file_permissions(script_path, "755", False)
            if res != 0:
                print("Aborting ...\n")
                puml("#red:Failed to set the executable bit on Magisk update script;\n")
                return -1

            #------------------------------------
            # Execute the pfmagisk_settings.sh script
            #------------------------------------
            print("Executing the pfmagisk_settings.sh script ...")
            puml(":Executing the pfmagisk_settings script;\n")
            debug(f"exec_cmd: {exec_cmd}")
            res = run_shell2(exec_cmd)
            if res.returncode == 0:
                # delete existing pfmagisk_settings.sh from phone
                res = self.delete("/data/local/tmp/pfmagisk_settings.sh")
                if res != 0:
                    print("Failed to delete temporary pfmagisk_settings.sh file\n")
                    puml("#red:Failed to delete temporary pfmagisk_settings.sh file;\n")
                    return -1
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during pfmagisk_settings script execution")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml("note right:ERROR: during pfmagisk_settings script execution;\n")
                return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during exec_magisk_settings opeation.")
            traceback.print_exc()
            puml("#red:Exception during exec_magisk_settings opeation.;\n", True)
            return -1


    # ----------------------------------------------------------------------------
    #                               method magisk_add_systemless_hosts
    # ----------------------------------------------------------------------------
    def magisk_add_systemless_hosts(self):
        if self.mode == 'adb' and self.rooted:
            try:
                print("Magisk adding built-in systemless hosts module ...")
                puml(":Magisk adding built-in systemless hosts module;\n", True)

                data = """
add_hosts_module() {
  # Do not touch existing hosts module
  [ -d $NVBASE/modules/hosts ] && return
  cd $NVBASE/modules
  mkdir -p hosts/system/etc
  cat << EOF > hosts/module.prop
id=hosts
name=Systemless Hosts
version=1.0
versionCode=1
author=Magisk
description=Magisk app built-in systemless hosts module
EOF
  magisk --clone /system/etc/hosts hosts/system/etc/hosts
  touch hosts/update
  cd /
}

NVBASE=/data/adb
add_hosts_module
                """
                res = self.exec_magisk_settings(data)
                if res == 0:
                    print("Magisk adding built-in systemless hosts module succeeded")
                    puml("note right:Magisk adding built-in systemless hosts module;\n")
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to add built-in systemless hosts module.")
                    puml("note right:ERROR: Failed to add built-in systemless hosts module;\n")
                    return -1
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during magisk_add_systemless_hosts opeation.")
                traceback.print_exc()
                puml("#red:Exception during magisk_add_systemless_hosts opeation.;\n", True)


    # ----------------------------------------------------------------------------
    #                               method magisk_enable_zygisk
    # ----------------------------------------------------------------------------
    def magisk_enable_zygisk(self, enable):
        if self.mode == 'adb' and self.rooted:
            try:
                value = "1" if enable else "0"
                print(f"Updating Zygisk flag value to: {value}")
                puml(f":Updating Zygisk flag value to: {value};\n", True)

                data = f"magisk --sqlite \"UPDATE settings SET value = {value} WHERE key = 'zygisk';\""
                res = self.exec_magisk_settings(data)
                if res == 0:
                    print("Updating Zygisk flag succeeded")
                    puml("note right:Updating Zygisk flag succeeded;\n")
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to update Zygisk flag")
                    puml("note right:ERROR: Updating Zygisk flag;\n")
                    return -1
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during magisk_enable_zygisk opeation.")
                traceback.print_exc()
                puml("#red:Exception during magisk_enable_zygisk opeation.;\n", True)


    # ----------------------------------------------------------------------------
    #                               method magisk_enable_denylist
    # ----------------------------------------------------------------------------
    def magisk_enable_denylist(self, enable):
        if self.mode != 'adb' or not self.rooted:
            return
        try:
            if get_magisk_package() == 'io.github.huskydg.magisk':
                print("Magisk denylist is currently not supported in PixelFlasher for Magisk Delta.")
                return
            value = "1" if enable else "0"
            print(f"Updating Enforce denylist flag value to: {value}")
            puml(f":Updating Enforce denylist flag value to: {value};\n", True)

            data = f"magisk --sqlite \"UPDATE settings SET value = {value} WHERE key = 'denylist';\""
            res = self.exec_magisk_settings(data)
            if res == 0:
                print("Updating Enforce denylist flag succeeded")
                puml("note right:Updating Enforce denylist flag succeeded;\n")
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to update Enforce denylist flag")
                puml("note right:ERROR: Updating Enforce denylist flag;\n")
                return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during magisk_enable_denylist opeation.")
            traceback.print_exc()
            puml("#red:Exception during magisk_enable_denylist opeation.;\n", True)


    # ----------------------------------------------------------------------------
    #                               method magisk_update_su
    # ----------------------------------------------------------------------------
    def magisk_update_su(self, uid, policy, logging, notification, until=0, label=''):
        if self.mode == 'adb' and self.rooted:
            try:
                if policy == "allow":
                    value = 2
                elif policy == "deny":
                    value = 1
                else:
                    return
                print(f"\nSetting SU permissions for: {label}")
                print(f"    uid:          {uid}")
                print(f"    rights:       {policy}")
                print(f"    Notification: {notification}")
                print(f"    Logging:      {logging}")
                puml(f":Setting SU permissions for: {label} {uid};\n", True)

                data = f"magisk --sqlite \"INSERT OR REPLACE INTO policies (uid, policy, logging, notification, until) VALUES ('{uid}', {value}, {logging}, {notification}, {until});\""
                res = self.exec_magisk_settings(data)
                if res == 0:
                    print("Setting SU permissions succeeded")
                    puml("note right:Setting SU permissions succeeded;\n")
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to Setting SU permissions")
                    puml("note right:ERROR: Setting SU permissions flag;\n")
                    return -1
            except Exception as e:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during magisk_update_su opeation.")
                traceback.print_exc()
                puml("#red:Exception during magisk_update_su opeation.;\n", True)


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
                    print(f"Stdout: {res.stdout}")
                    print(f"Stderr: {res.stderr}")
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
                traceback.print_exc()
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
                    print(f"Stdout: {res.stdout}")
                    print(f"Stderr: {res.stderr}")
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
                traceback.print_exc()
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
            traceback.print_exc()
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
            file_path = remove_quotes(file_path)
            if with_su:
                if self.rooted:
                    print(f"Deleting {file_path} from the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -{flag}f \"{file_path}\"\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}. Device is not rooted.")
            else:
                print(f"Deleting {file_path} from the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell rm -{flag}f \"{file_path}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not delete {file_path}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}")
                print(f"Stderr: {res.stderr}")
                return -1
        except Exception as e:
            traceback.print_exc()
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
                if self.hardware in KNOWN_INIT_BOOT_DEVICES:
                    partition = 'init_boot'
                else:
                    partition = 'boot'
            if slot:
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
                print(f"Stdout: {res.stdout}")
                print(f"Stderr: {res.stderr}")
                return -1, ''
        except Exception as e:
            traceback.print_exc()
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
            source = remove_quotes(source)
            dest = remove_quotes(dest)
            print(f"Copying {source} to {dest} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cp \"{source}\" \"{dest}\";chmod 666 \"{dest}\"\'\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not su cp.")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}")
                print(f"Stderr: {res.stderr}")
                return -1
        except Exception as e:
            traceback.print_exc()
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
            file_path = remove_quotes(file_path)
            if with_su:
                if self.rooted:
                    print(f"Checking for {file_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls \"{file_path}\"\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not check {file_path}. Device is not rooted.")
            else:
                print(f"Checking for {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell ls \"{file_path}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print(f"File: {file_path} is found on the device.")
                return 1, res.stdout.strip()
            else:
                print(f"File: {file_path} is not found on the device.")
                return 0, None
        except Exception as e:
            traceback.print_exc()
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
            dir_path = remove_quotes(dir_path)
            if with_su:
                if self.rooted:
                    print(f"Creating directory {dir_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'mkdir -p \"{dir_path}\"\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create directory {dir_path}. Device is not rooted.")
            else:
                print(f"Creating directory {dir_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell mkdir -p \"{dir_path}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not create directory: {dir_path}")
                return -1
        except Exception as e:
            traceback.print_exc()
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
            file_path = remove_quotes(file_path)
            if with_su:
                if self.rooted:
                    print(f"Getting file content of {file_path} on the device as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'cat \"{file_path}\"\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content of {file_path}. Device is not rooted.")
            else:
                print(f"Getting file content of {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell cat \"{file_path}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return res.stdout
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content: {file_path}")
                return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get file content: {file_path}")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method push_file
    # ----------------------------------------------------------------------------
    def push_file(self, local_file: str, file_path: str, with_su = False) -> int:
        """
            Pushes a file to the device.

            Args:
                local_file (str): Local file path.
                file_path (str): Full file path on the device.
                with_su (bool, optional): Perform the action as root. Defaults to False.

            Returns:
                int: 0 if the file is pushed, -1 if an exception is raised.

            Raises:
                None

            Example:
                ```python
                phone = Phone()
                result = phone.push_file("local_file.txt", "/data/files/file.txt", with_su=True)
                print(result)
                ```
        """
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}. Device is not in ADB mode.")
            return -1
        try:
            local_file = remove_quotes(local_file)
            file_path = remove_quotes(file_path)
            if with_su:
                if self.rooted:
                    print(f"Pushing local file as root: {local_file} to the device: {file_path} ...")
                    filename = os.path.basename(urlparse(local_file).path)
                    remote_file = f"\"/data/local/tmp/{filename}\""
                    res = self.push_file(local_file, remote_file, with_su=False)
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
                theCmd = f"\"{get_adb()}\" -s {self.id} push \"{local_file}\" \"{file_path}\""
                res = run_shell(theCmd)
                if res.returncode == 0:
                    print("Return Code: 0")
                    return 0
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}")
                    print(f"Stderr: {res.stderr}")
                    return -1
        except Exception as e:
            traceback.print_exc()
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
            remote_file = remove_quotes(remote_file)
            local_file = remove_quotes(local_file)
            if with_su:
                if self.rooted:
                    filename = os.path.basename(urlparse(remote_file).path)
                    temp_remote_file = f"/data/local/tmp/{filename}"
                    res = self.su_cp_on_device(remote_file, temp_remote_file)
                    if res != 0:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not copy {remote_file} to {temp_remote_file}. Perhaps the file does not exist.")
                        return -1
                    else:
                        remote_file = temp_remote_file
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}. Device is not rooted.")
                    return -1

            print(f"Pulling remote file: {remote_file} from the device to: {local_file} ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} pull \"{remote_file}\" \"{local_file}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not pull {remote_file}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}")
                print(f"Stderr: {res.stderr}")
                return -1
        except Exception as e:
            traceback.print_exc()
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
            file_path = remove_quotes(file_path)
            if with_su:
                if self.rooted:
                    print(f"Setting permissions {permissions} on {file_path} as root ...")
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'chmod {permissions} \"{file_path}\"\'\""
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permissions on {file_path}. Device is not rooted.")
            else:
                print(f"Setting permissions {permissions} on {file_path} on the device ...")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell chmod {permissions} \"{file_path}\""
            res = run_shell(theCmd)
            if res.returncode == 0:
                print("Return Code: 0")
                return 0
            else:
                print(f"Return Code: {res.returncode}.")
                return -1
        except Exception as e:
            traceback.print_exc()
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
        try:
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
            return 0
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pushing aapt.")
            puml("#red:Encountered an error while pushing appt.;\n")
            traceback.print_exc()

    # ----------------------------------------------------------------------------
    #                               Method push_avbctl
    # ----------------------------------------------------------------------------
    def push_avbctl(self, file_path = "/data/local/tmp/avbctl") -> int:
        """Method pushes avbctl binary to the device.

        Args:
            file_path:      Full file path on the device (Default: /data/local/tmp/avbctl)

        Returns:
            0               On Success.
            -1              if an exception is raised.
        """
        try:
            # Transfer extraction script to the phone
            if self.architecture in ['armeabi-v7a', 'arm64-v8a']:
                path_to_avbctl = os.path.join(get_bundle_dir(),'bin', 'avbctl')
                res = self.push_file(f"{path_to_avbctl}", f"{file_path}")
                if res != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
                    return -1
                # set the permissions.
                res = self.set_file_permissions(f"{file_path}", "755")
                if res != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permission on {file_path}")
                    return -1
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: avbctl is not available for device architecture: {self.architecture}")
                return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pushing avbctl")
            puml("#red:Encountered an error while pushing avbctl;\n")
            traceback.print_exc()

    # ----------------------------------------------------------------------------
    #                               Method push_update_engine_client
    # ----------------------------------------------------------------------------
    def push_update_engine_client(self, file_path = "/data/local/tmp/update_engine_client") -> int:
        try:
            # Transfer extraction script to the phone
            if self.architecture in ['armeabi-v7a', 'arm64-v8a']:
                path_to_update_engine_client = os.path.join(get_bundle_dir(),'bin', 'update_engine_client')
                res = self.push_file(f"{path_to_update_engine_client}", f"{file_path}")
                if res != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not push {file_path}")
                    return -1
                # set the permissions.
                res = self.set_file_permissions(f"{file_path}", "755")
                if res != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not set permission on {file_path}")
                    return -1
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: update_engine_client is not available for device architecture: {self.architecture}")
                return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pushing update_engine_client")
            puml("#red:Encountered an error while pushing update_engine_client;\n")
            traceback.print_exc()

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
                pkg_path = ''
                with contextlib.suppress(Exception):
                    pkg_path = res.stdout.split('\n')[0]
                    pkg_path = pkg_path.split(':')[1]
                    print(f"Package Path is: {pkg_path}")
                return pkg_path
            else:
                if check_details:
                    details, pkg_path = self.get_package_details(pkg)
                    if pkg_path:
                        print(f"Package Path is: {pkg_path}")
                        return pkg_path
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} path.")
                print(f"{details}")
                return -1
        except Exception as e:
            traceback.print_exc()
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
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"/data/local/tmp/aapt2 d badging {pkg_path} | grep 'application: label='\""
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
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"/data/local/tmp/aapt2 d badging {pkg_path} | grep 'application-label:'\""
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
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package {pkg} label.")
            return -1, -1

    # ----------------------------------------------------------------------------
    #                               Method uiautomator_dump
    # ----------------------------------------------------------------------------
    def uiautomator_dump(self, path: str):
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not uiautomator dump. Device is not in ADB mode.")
            return -1
        try:
            print(f"uiautomator dump {path} path on the device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell uiautomator dump {path}"
            res = run_shell(theCmd)
            if res.returncode == 0 and res.stderr == '':
                return path
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: uiautomator dump failed.")
            print(res.stderr)
            return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: not uiautomator dump.")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method click
    # ----------------------------------------------------------------------------
    def click(self, coords):
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not tap. Device is not in ADB mode.")
            return -1
        if coords is None or coords == '' or coords == -1:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not tap. Coordinates are [{coords}]")
            return -1
        try:
            print(f"tap {coords} on the device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell input tap {coords}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                return 0
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: tap failed.")
            print(res.stderr)
            return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: tap failed.")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method swipe
    # ----------------------------------------------------------------------------
    def swipe(self, coords):
        if self.mode != 'adb':
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not swipe. Device is not in ADB mode.")
            return -1
        if coords is None or coords == '' or coords == -1:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not swipe. Coordinates are [{coords}]")
            return -1
        try:
            print(f"swipe {coords} on the device ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell input swipe {coords}"
            res = run_shell(theCmd)
            if res.returncode == 0:
                return 0
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: swipe failed.")
            print(res.stderr)
            return -1
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: swipe failed.")
            return -1

    # ----------------------------------------------------------------------------
    #                               property magisk_app_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_app_version(self):
        if self._magisk_app_version is None and self.mode == 'adb' and get_magisk_package():
            self._magisk_app_version, self._magisk_app_version_code = self.get_app_version(get_magisk_package())
        return self._magisk_app_version

    # ----------------------------------------------------------------------------
    #                               property apatch_app_version
    # ----------------------------------------------------------------------------
    @property
    def apatch_app_version(self):
        if self._apatch_app_version is None and self.mode == 'adb':
            self._apatch_app_version, self._apatch_app_version_code = self.get_app_version('me.bmax.apatch')
        return self._apatch_app_version

    # ----------------------------------------------------------------------------
    #                               method app_version
    # ----------------------------------------------------------------------------
    def get_app_version(self, pkg):
        version = ''
        versionCode = ''
        if pkg and self.mode == 'adb':
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package {pkg}"
                res = run_shell(theCmd)
                data = res.stdout.split('\n')
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
                return '', ''
        # return version, versionCode
        return f"{str(version)}:{str(versionCode)}", versionCode

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
    #                               property apatch_app_version_code
    # ----------------------------------------------------------------------------
    @property
    def apatch_app_version_code(self):
        if self._apatch_app_version_code is None:
            return ''
        else:
            return self._apatch_app_version_code

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_magisk_app_version
    # ----------------------------------------------------------------------------
    def get_uncached_magisk_app_version(self):
        self._magisk_app_version = None
        return self.magisk_app_version

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_apatch_app_version
    # ----------------------------------------------------------------------------
    def get_uncached_apatch_app_version(self):
        self._apatch_app_version = None
        return self.apatch_app_version

    # ----------------------------------------------------------------------------
    #                               Method is_display_unlocked
    # ----------------------------------------------------------------------------
    def is_display_unlocked(self):
        print("Checking to see if display is unlocked ...")
        try:
            if self.mode == 'adb':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"dumpsys power | grep \'mHolding\'\""
                res = run_shell(theCmd)
                mHoldingWakeLockSuspendBlocker = False
                mHoldingDisplaySuspendBlocker = False
                if res.returncode == 0:
                    results = res.stdout.strip().split('\n')
                    for m in results:
                        s = False
                        k, v = m.strip().split('=')
                        if v == 'true':
                            s = True
                        if k == 'mHoldingDisplaySuspendBlocker':
                            mHoldingDisplaySuspendBlocker = s
                        elif k == 'mHoldingWakeLockSuspendBlocker':
                            mHoldingWakeLockSuspendBlocker = s
                # https://stackoverflow.com/questions/35275828/is-there-a-way-to-check-if-android-device-screen-is-locked-via-adb
                # I'm not going to check for both flags as it is not reliable
                # But this won't work if display is on but locked :(
                # if mHoldingWakeLockSuspendBlocker and mHoldingDisplaySuspendBlocker:
                if mHoldingDisplaySuspendBlocker:
                    print("Display is unlocked")
                    return True
                else:
                    print("Display is locked")
                    return False
        except Exception:
            print("Display is locked")
            return False

    # ----------------------------------------------------------------------------
    #                               Method stop_magisk
    # ----------------------------------------------------------------------------
    def stop_magisk(self):
        try:
            print("Stopping Magisk ...")
            with contextlib.suppress(Exception):
                self.perform_package_action(get_magisk_package(), 'kill')
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during stop_magisk")
            traceback.print_exc()

    # ----------------------------------------------------------------------------
    #                               method get_magisk_detailed_modules
    # ----------------------------------------------------------------------------
    def  get_magisk_detailed_modules(self, refresh=False):
        if self._get_magisk_detailed_modules is None or refresh == True:
            try:
                if self.mode == 'adb' and self.rooted:
                    if sys.platform == "win32":
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'for FILE in /data/adb/modules/*; do echo $FILE; if test -f \"$FILE/remove\"; then echo \"state=remove\"; elif test -f \"$FILE/disabled\"; then echo \"state=disabled\"; else echo \"state=enabled\"; fi; cat \"$FILE/module.prop\"; echo; echo -----pf;done\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            modules = []
                            themodules = res.stdout.split('-----pf\n')
                            for item in themodules:
                                if item:
                                    module_prop = item.split('\n')
                                    filepath = module_prop[0]
                                    module = os.path.basename(urlparse(filepath).path)
                                    m = Magisk(module)
                                    setattr(m, 'id', '')
                                    setattr(m, 'version', '')
                                    setattr(m, 'versionCode', '')
                                    setattr(m, 'author', '')
                                    setattr(m, 'description', '')
                                    setattr(m, 'name', '')
                                    setattr(m, 'updateJson', '')
                                    setattr(m, 'updateDetails', {})
                                    setattr(m, 'updateAvailable', False)
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
                                        if line.strip() and '=' in line:
                                            key, value = line.split('=', 1)
                                            setattr(m, key, value)
                                    if m.updateJson:
                                        setattr(m, 'updateDetails', check_module_update(m.updateJson))
                                    with contextlib.suppress(Exception):
                                        if m.versionCode and m.updateDetails and m.updateDetails.versionCode and int(m.updateDetails.versionCode) > int(m.versionCode):
                                            m.updateAvailable = True
                                    modules.append(m)
                            self._get_magisk_detailed_modules = modules
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error when processing Magisk Modules.")
                            print(f"Return Code: {res.returncode}.")
                            print(f"Stdout: {res.stdout}.")
                            print(f"Stderr: {res.stderr}.")
                    else:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            debug(res.stdout)
                            modules = []
                            self._get_magisk_detailed_modules = res.stdout.split('\n')
                            for module in self._get_magisk_detailed_modules:
                                if module:
                                    m = Magisk(module)
                                    if self.mode == 'adb' and get_adb():
                                        # get the uninstall state by checking if there is a remove file in the module directory
                                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules/{module}/remove\'\""
                                        res = run_shell(theCmd)
                                        if res.returncode == 0:
                                            m.state = 'remove'
                                        else:
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
                                            setattr(m, 'name', '')
                                            setattr(m, 'updateJson', '')
                                            setattr(m, 'updateDetails', {})
                                            setattr(m, 'updateAvailable', False)
                                            for line in module_prop:
                                                # ignore comment lines
                                                if line[:1] == "#":
                                                    continue
                                                if line.strip() and '=' in line:
                                                    key, value = line.split('=', 1)
                                                    setattr(m, key, value)
                                            if m.updateJson:
                                                setattr(m, 'updateDetails', check_module_update(m.updateJson))
                                            with contextlib.suppress(Exception):
                                                if m.versionCode and m.updateDetails and m.updateDetails.versionCode and int(m.updateDetails.versionCode) > int(m.versionCode):
                                                    m.updateAvailable = True
                                            modules.append(m)
                            self._get_magisk_detailed_modules = modules
                        else:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error when processing Magisk Modules.")
                            print(f"Return Code: {res.returncode}.")
                            print(f"Stdout: {res.stdout}.")
                            print(f"Stderr: {res.stderr}.")
            except Exception as e:
                self._get_magisk_detailed_modules is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk modules processing")
                traceback.print_exc()
                print(f"    Module: {module}\n    Line: {line}")
                print(f"    module.prop:\n-----\n{res.stdout}-----\n")
        return self._get_magisk_detailed_modules

    # ----------------------------------------------------------------------------
    #                               property magisk_apks
    # ----------------------------------------------------------------------------
    @property
    def magisk_apks(self):
        if self._magisk_apks is None:
            try:
                apks = []
                mlist = ['stable', 'beta', 'canary', 'debug', 'delta canary', 'delta debug', 'special 25203', "special 26401", "special 27001"]
                for i in mlist:
                    apk = self.get_magisk_apk_details(i)
                    if apk:
                        apks.append(apk)
                self._magisk_apks = apks
            except Exception as e:
                self._magisk_apks is None
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads link: {i} processing")
                traceback.print_exc()
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

        elif channel == 'delta canary':
            url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/canary.json"

        elif channel == 'delta debug':
            url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/debug.json"

        elif channel == 'zygote64_32 stable':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/stable.json"

        elif channel == 'zygote64_32 beta':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/beta.json"

        elif channel == 'zygote64_32 canary':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/canary.json"

        elif channel == 'zygote64_32 debug':
            url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/debug.json"

        elif channel == 'special 25203':
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

        elif channel == 'special 26401':
            url = ""
            setattr(ma, 'version', "76aef836")
            setattr(ma, 'versionCode', "26401")
            setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_26401/app-release.apk")
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', 'com.topjohnwu.magisk')
            release_notes = """
## 2023.11.12 Special Magisk v26.4 Build\n\n
This is a special Magisk build\n\n
- Based on build versionCode: 26401 versionName: 76aef836\n
- Modified to disable loading modules while keep root.\n
- Made to recover from bootloops due to bad / incompatible Modules.\n\n
### Steps to follow [here](https://github.com/badabing2005/Magisk)\n
            """
            setattr(ma, 'release_notes', release_notes)
            return ma
        elif channel == 'special 27001':
            url = ""
            setattr(ma, 'version', "79fd3e40")
            setattr(ma, 'versionCode', "27001")
            setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_27001/app-release.apk")
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', 'com.topjohnwu.magisk')
            release_notes = """
## 2024.02.12 Special Magisk v27.0 Build\n\n
This is a special Magisk build\n\n
- Based on build versionCode: 27001 versionName: 79fd3e40\n
- Modified to disable loading modules while keep root.\n
- Made to recover from bootloops due to bad / incompatible Modules.\n\n
### Steps to follow [here](https://github.com/badabing2005/Magisk)\n
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
            response = request_with_fallback(method='GET', url=url, headers=headers, data=payload)
            data = response.json()
            setattr(ma, 'version', data['magisk']['version'])
            setattr(ma, 'versionCode', data['magisk']['versionCode'])
            setattr(ma, 'link', data['magisk']['link'])
            note_link = data['magisk']['note']
            setattr(ma, 'note_link', note_link)
            setattr(ma, 'package', 'com.topjohnwu.magisk')
            # if channel == 'alpha':
            #     # Magisk alpha app link is not a full url, build it from url
            #     setattr(ma, 'link', f"https://github.com/vvb2060/magisk_files/raw/alpha/{ma.link}")
            #     setattr(ma, 'note_link', "https://raw.githubusercontent.com/vvb2060/magisk_files/alpha/README.md")
            #     setattr(ma, 'package', 'io.github.vvb2060.magisk')
            if channel in ['delta canary', 'delta debug']:
                setattr(ma, 'package', 'io.github.huskydg.magisk')
            # Get the note contents
            headers = {}
            with contextlib.suppress(Exception):
                setattr(ma, 'release_notes', '')
                response = request_with_fallback(method='GET', url=ma.note_link, headers=headers, data=payload)
                setattr(ma, 'release_notes', response.text)
            return ma
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links: {url} processing")
            traceback.print_exc()
            return

    # ----------------------------------------------------------------------------
    #                               property magisk_modules_summary
    # ----------------------------------------------------------------------------
    @property
    def magisk_modules_summary(self):
        if self._magisk_modules_summary is None:
            if self.get_magisk_detailed_modules():
                summary = ''
                for module in self.get_magisk_detailed_modules():
                    with contextlib.suppress(Exception):
                        updateText = ''
                        if module.updateAvailable:
                            updateText = "\t [Update Available]"
                        summary += f"        {module.name:<36}{module.state:<10}{module.version}{updateText}\n"
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
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c 'ls -l /data/adb/'\""
                res = run_shell(theCmd, timeout=8)
                if res.returncode == 0 and '/system/bin/sh: su: not found' not in res.stdout:
                    self._rooted = True
                else:
                    # theCmd = f"\"{get_adb()}\" -s {self.id} shell busybox ls"
                    # res = run_shell(theCmd, 8)
                    # if res.returncode == 0:
                    #     print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device: appears to be rooted, however adb root access is not granted.\Please grant root access to adb and scan again.")
                    self._rooted = False
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
                puml("#red:ERROR: adb command is not found;\n", True)
        return self._rooted

    # ----------------------------------------------------------------------------
    #                               Method get_details
    # ----------------------------------------------------------------------------
    def get_device_details(self):
        try:
            if self.true_mode != self.mode:
                mode = self.true_mode[:3]
            else:
                mode = self.mode
            return f"{self.root_symbol:<3}({mode:<3})   {self.id:<25}{self.hardware:<12}{self.build:<25}"
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting device details.")
            puml("#red:Encountered an error while getting device details.;\n")
            traceback.print_exc()

    # ----------------------------------------------------------------------------
    #                               Method reboot_system
    # ----------------------------------------------------------------------------
    def reboot_system(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to system ...")
            puml(f":Rebooting device: {self.id} to system;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    if timeout:
                        res = self.adb_wait_for(timeout=timeout, wait_for='device')
                        if res == 1:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during adb_wait_for in reboot_system")
                            # puml(f"note right:ERROR: during adb_wait_for in reboot_system;\n")
                            return -1
                        update_phones(self.id)
                    puml("note right:State ADB;\n")
                    return res
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_system")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during reboot_system;\n")
            elif mode == 'fastboot' and get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    if timeout:
                        res = self.adb_wait_for(timeout=timeout, wait_for='device')
                        # puml(f"note right:Res [{res}];\n")
                    update_phones(self.id)
                    return 0
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_system")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during adb_wait_for in reboot_system;\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_system")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_system;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_recovery
    # ----------------------------------------------------------------------------
    def reboot_recovery(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to recovery ...")
            puml(f":Rebooting device: {self.id} to recovery;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot recovery"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    if timeout:
                        res = self.adb_wait_for(timeout=timeout, wait_for='recovery')
                        if res == 1:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_recovery")
                            # puml(f"note right:ERROR: during adb_wait_for in reboot_recovery;\n")
                            return -1
                        update_phones(self.id)
                    puml("note right:State recovery;\n")
                    return res
            elif mode == 'fastboot' and get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot recovery"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    res = self.adb_wait_for(timeout=timeout, wait_for='recovery')
                    # puml(f"note right:Res [{res}];\n")
                    update_phones(self.id)
                    return res
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_recovery")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during adb_wait_for in reboot_recovery;\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_recovery")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_recovery;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_download
    # ----------------------------------------------------------------------------
    def reboot_download(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to download ...")
            puml(f":Rebooting device: {self.id} to download;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot download"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    time.sleep(5)
                    mode = self.get_device_state()
                    if mode and mode != 'ERROR':
                        print(f"Device is now in {mode} mode.")
                        # puml(f"note right:ERROR: during get_device_state in reboot_download;\n")
                        id = self.id
                    else:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Download state cannot be confirmed, please check your device.")
                        puml(f"note right:Download state cannot be confirmed, please check your device.;\n")
                        id = None
                return res
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_download")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_download;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_safemode
    # ----------------------------------------------------------------------------
    def reboot_safemode(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to safe mode ...")
            puml(f":Rebooting device: {self.id} to safe mode;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'setprop persist.sys.safemode 1\'\""
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    res = self.reboot_system(timeout=timeout)
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while setting safemode prop")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    puml(f"note right:ERROR: during reboot_safemode;\n")
                    res = res.returncode
                return res
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_safemode")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_bootloader
    # ----------------------------------------------------------------------------
    def reboot_bootloader(self, fastboot_included = False, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to bootloader ...")
            puml(f":Rebooting device: {self.id} to bootloader;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot bootloader "
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    if timeout:
                        res = self.fastboot_wait_for_bootloader(timeout=timeout)
                        if res == 1:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_bootloader")
                            # puml(f"note right:ERROR: during fastboot_wait_for_bootloader in reboot_bootloader;\n")
                            return -1
                        update_phones(self.id)
                        puml("note right:State Bootloader;\n")
                        return res
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_bootloader")
                    print(f"stdout: {res.stdout}   stderr: {res.stderr}")
                    puml(f"note right:ERROR: during reboot_bootloader;\n")
                    return -1
            elif mode == 'fastboot' and fastboot_included and get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot bootloader"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    res = self.fastboot_wait_for_bootloader(timeout=timeout)
                    update_phones(self.id)
                    return res
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_bootloader")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during reboot_bootloader;\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_bootloader")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_bootloader;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_fastbootd
    # ----------------------------------------------------------------------------
    def reboot_fastboot(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to fastbootd ...")
            print("This process will wait for fastbootd indefinitly.")
            print("WARNING! if your device does not boot to fastbootd PixelFlasher will hang and you'd have to kill it.")
            puml(f":Rebooting device: {self.id} to fastbootd;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot fastboot "
                debug(theCmd)
                return run_shell(theCmd, timeout=timeout)
            elif mode == 'fastboot' and get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} reboot fastboot"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    res = self.fastboot_wait_for_bootloader(timeout=timeout)
                    update_phones(self.id)
                    return res
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_fastboot")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during adb_wait_for in reboot_fastboot;\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_fastbootd")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_fastboot;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method reboot_sideload
    # ----------------------------------------------------------------------------
    def reboot_sideload(self, timeout=60):
        try:
            mode = self.get_device_state()
            print(f"Rebooting device: {self.id} to sideload ...")
            puml(f":Rebooting device: {self.id} to sideload;\n", True)
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} reboot sideload"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res.returncode == 0:
                    if timeout:
                        res = self.adb_wait_for(timeout=timeout, wait_for='sideload')
                        if res == 1:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_sideload")
                            # puml(f"note right:ERROR: during adb_wait_for in reboot_sideload;\n")
                            return -1
                        update_phones(self.id)
                        puml("note right:State sideload;\n")
                        return res
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_sideload")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
                    puml(f"note right:ERROR: during reboot_sideload;\n")
            elif mode == 'fastboot' and get_fastboot():
                print("Device is in bootloader mode, first rebooting to system (this could take some time) ...")
                res = self.reboot_system(timeout=timeout)
                if res == 0:
                    res = self.adb_wait_for(timeout=timeout, wait_for='device')
                    # puml(f"note right:Res [{res}];\n")
                    update_phones(self.id)
                    debug("Calling reboot_sideload ...")
                    res = self.reboot_sideload(timeout=timeout)
                    return res
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during reboot_sideload")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                puml(f"note right:ERROR: during adb_wait_for in reboot_system;\n")
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during reboot_sideload")
            traceback.print_exc()
            puml(f"note right:Exception: during reboot_sideload;\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method get_device_state
    # ----------------------------------------------------------------------------
    def get_device_state(self, device_id='', timeout=60, retry=0):
        """
        Gets the state of a device.

        The method retrieves the state of a device identified by the given device ID. It supports retrying the operation multiple times with a specified timeout between each attempt.

        Args:
            device_id (str): The ID of the device. If not provided, the ID of the instance is used.
            timeout (int): The timeout value for each shell command attempt in seconds. Defaults to 60.
            retry (int): The number of retry attempts. Defaults to 0.

        Returns:
            str: The state of the device. Possible values are 'fastboot', 'ERROR', or the device state retrieved from ADB.

        Raises:
            Exception: If an error occurs during the operation.

        """
        try:
            if not device_id:
                device_id = self.id
            retry_text = f"retry [{retry + 1}] times" if retry > 0 else ''
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Getting device: {device_id} state {retry_text} ...")
            puml(f":Getting device: {device_id} state {retry_text};\n", True)
            for i in range(retry + 1):
                if get_adb():
                    puml(f":Getting device: {device_id} state [{i + 1}/{retry + 1}] using get-state;\n", True)
                    debug(f":Getting device: {device_id} state [{i + 1}/{retry + 1}] using get-state")
                    theCmd = f"\"{get_adb()}\" -s {device_id} get-state"
                    debug(theCmd)
                    res = run_shell(theCmd, timeout=timeout)
                    if res.returncode == 0:
                        device_mode = res.stdout.strip('\n')
                        if device_mode == "device":
                            puml("note right:State ADB;\n")
                            return "adb"
                        else:
                            state = res.stdout.strip('\n')
                            puml(f"note right:State {state};\n")
                            return state
                if get_fastboot():
                    puml(f":Getting device: {device_id} state [{i + 1}/{retry + 1}] using fastboot devices;\n", True)
                    debug(f":Getting device: {device_id} state [{i + 1}/{retry + 1}] using fastboot devices")
                    theCmd = f"\"{get_fastboot()}\" devices"
                    res = run_shell(theCmd, timeout=timeout)
                    if res.returncode == 0 and device_id in res.stdout:
                        puml("note right:State fastboot;\n")
                        return 'fastboot'
                time.sleep(1)
            update_phones(device_id)
            return 'ERROR'
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during get_device_state for device: {device_id}")
            traceback.print_exc()
            puml(f"note right:ERROR: Exception during get_device_state for device;\n")
            return 'ERROR'

    # ----------------------------------------------------------------------------
    #                               Method adb_wait_for
    # ----------------------------------------------------------------------------
    def adb_wait_for(self, device_id='', timeout=60, wait_for=''):
        try:
            if not device_id:
                device_id = self.id
            print(f"ADB waiting for device: {device_id} for {wait_for} ...")
            puml(f":ADB waiting for device: {device_id} for {wait_for};\n", True)
            if wait_for not in ['device', 'bootloader', 'sideload', 'recovery', 'rescue', 'disconnect']:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Wrong wait-for [{wait_for}] request!")
                puml(f"#red:ERROR: Wrong wait-for [{wait_for}] request;\n", True)
                return -1

            if get_adb():
                theCmd = f"\"{get_adb()}\" -s {device_id} wait-for-{wait_for}"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res == 0:
                    print(f"device: {device_id} is now in {wait_for} mode.")
                    puml(f":device: {device_id} is now in {wait_for} mode;\n", True)
                    return 0
                else:
                    mode = self.get_device_state()
                    if mode:
                        print(f"Device is now in {mode} mode.")
                        puml(f":device is now in {mode} mode;\n", True)
                with contextlib.suppress(Exception):
                    return res.returncode
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during adb_wait_for: {wait_for}")
            traceback.print_exc()
            puml(f"note right:ERROR: Exception during adb_wait_for: {wait_for};\n")
            return -1

    # ----------------------------------------------------------------------------
    #                               Method fastboot_wait_for_bootloader
    # ----------------------------------------------------------------------------
    def fastboot_wait_for_bootloader(self, device_id='', timeout=60):
        try:
            if not get_fastboot():
                return -1

            if not device_id:
                device_id = self.id
            print(f"Fastboot waiting for device: {device_id} for bootloader ...")
            puml(f":Fastboot waiting for device: {device_id} for bootloader;\n", True)
            start_time = time.time()
            while time.time() - start_time < timeout:
                with contextlib.suppress(Exception):
                    theCmd = f"\"{get_fastboot()}\" devices"
                    output = run_shell(theCmd)
                    if f"{device_id}\t" in output.stdout:
                        print(f"device: {device_id} is now in bootloader mode.")
                        puml(f":device: {device_id} is now in bootloader mode;\n", True)
                        return 0
                time.sleep(1)
            print(f"Timeout: [{timeout}] Fastboot could not detect device: {device_id} in bootloader mode ")
            puml(f":Timeout: [{timeout}] Fastboot could not detect device: {device_id} in bootloader mode;\n", True)
            return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in fastboot_wait_for_bootloader")
            puml("#red:Encountered an error in fastboot_wait_for_bootloader;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method get_magisk_denylist
    # ----------------------------------------------------------------------------
    def get_magisk_denylist(self):
        try:
            if self.mode != 'adb' or not get_adb() or not self.rooted:
                return []
            print("Getting Magisk denylist ...")
            puml(f":Magisk denylist;\n", True)
            if get_magisk_package() == 'io.github.huskydg.magisk':
                print("Magisk denylist is currently not supported in PixelFlasher for Magisk Delta.")
                return []
            theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk --denylist ls\'\""
            debug(theCmd)
            res = run_shell(theCmd)
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting Magisk denylist")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")

            lines = res.stdout.split('\n')
            unique_packages = set()
            for line in lines:
                if line.strip():  # Skip empty lines if any
                    package = line.split('|')[0]
                    unique_packages.add(package)
            return list(unique_packages)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_magisk_denylist")
            puml("#red:Encountered an error in get_magisk_denylist;\n")
            traceback.print_exc()
            return []

    # ----------------------------------------------------------------------------
    #                               Method install_apk
    # ----------------------------------------------------------------------------
    def install_apk(self, app, fastboot_included = False, owner_playstore = False, bypass_low_target = False):
        try:
            if owner_playstore:
                playstore_flag = " -i \"com.android.vending\""
            else:
                playstore_flag = ""

            if bypass_low_target:
                sdk_flag = " --bypass-low-target-sdk-block"
            else:
                sdk_flag = ""

            if self.mode == 'adb' and get_adb():
                print(f"Installing {app} on device ...")
                puml(f":Installing {app};\n", True)
                theCmd = f"\"{get_adb()}\" -s {self.id} install {playstore_flag} {sdk_flag} -r \"{app}\""
                debug(theCmd)
                res = run_shell(theCmd)
                if res.returncode != 0:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while installing \"{app}\"")
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
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in install_apk")
            puml("#red:Encountered an error in install_apk;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method get_current_slot
    # ----------------------------------------------------------------------------
    def get_current_slot(self):
        try:
            if self.mode == 'adb' and get_adb():
                return -1
            if self.mode == 'f.b' and get_fastboot():
                print(f"Getting current slot for device: {self.id} ...")
                puml(f":Getting current slot;\n", True)
                theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar current-slot"
                debug(theCmd)
                res = run_shell(theCmd)
                if res.returncode != 0:
                    return 'UNKNOWN'
                lines = (f"{res.stderr}{res.stdout}").splitlines()
                for line in lines:
                    if "current-slot:" in line:
                        value = line.split("current-slot:")[1].strip()
                        if value in ['a', 'b']:
                            return value
                return 'UNKNOWN'
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_current_slot")
            puml("#red:Encountered an error in get_current_slot;\n")
            traceback.print_exc()
            return 'UNKNOWN'

    # ----------------------------------------------------------------------------
    #                               Method get_wm_size
    # ----------------------------------------------------------------------------
    def get_wm_size(self):
        try:
            if self.mode != 'adb' and get_adb():
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device is not in adb mode.")
                return -1
            print("Getting device resolution ...")
            theCmd = f"\"{get_adb()}\" -s {self.id} shell wm size"
            debug(theCmd)
            res = run_shell(theCmd)
            if res.returncode != 0:
                return -1
            lines = (f"{res.stdout}").splitlines()
            for line in lines:
                if "Physical size:" in line:
                    return line.split("Physical size:")[1].strip()
            return -1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_wm_size")
            puml("#red:Encountered an error in get_wm_size;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method swipe_up
    # ----------------------------------------------------------------------------
    def swipe_up(self, percentage=10):
        try:
            if self.mode != 'adb' and get_adb():
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device is not in adb mode.")
                return -1
            print("Swipe up ...")
            wm_size = self.get_wm_size()
            x,y = wm_size.split('x')
            coords = f"{int(x) / 2} {int(int(y) * (1 - (percentage / 100)))} {int(x) / 2} {int(int(y) * percentage / 100)}"
            debug(f"coord: {coords}")
            res = self.swipe(coords)
            if res != 0:
                return -1
            return coords
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_wm_size")
            puml("#red:Encountered an error in get_wm_size;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method set_active
    # ----------------------------------------------------------------------------
    def set_active_slot(self, slot):
        try:
            if self.mode == 'adb' and get_adb():
                res = self.reboot_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
                self.refresh_phone_mode()
            if self.mode == 'f.b' and get_fastboot():
                print(f"Setting active slot to slot [{slot}] for device: {self.id} ...")
                puml(f":Setting Active slot to [{slot}];\n", True)
                theCmd = f"\"{get_fastboot()}\" -s {self.id} --set-active={slot}"
                debug(theCmd)
                return run_shell(theCmd)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in set_active_slot")
            puml("#red:Encountered an error in set_active_slot;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method switch_slot
    # ----------------------------------------------------------------------------
    def switch_slot(self, timeout=60):
        try:
            mode = self.get_device_state()
            if mode in ['adb', 'recovery', 'sideload', 'rescue'] and get_adb():
                res = self.reboot_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
                # self.refresh_phone_mode()
                update_phones(self.id)
            if mode == 'fastboot' and get_fastboot():
                print(f"Switching to other slot. Current slot [{self.active_slot}] for device: {self.id} ...")
                puml(f":Switching slot. Currernt Slot [{self.active_slot}];\n", True)
                if self.active_slot == 'a':
                    switch_to_slot = 'b'
                elif self.active_slot == 'b':
                    switch_to_slot = 'a'
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown Slot.")
                    puml("#red:ERROR: Unknown Slot;\n", True)
                    return 1
                theCmd = f"\"{get_fastboot()}\" -s {self.id} --set-active={switch_to_slot}"
                debug(theCmd)
                res = run_shell(theCmd, timeout=timeout)
                if res == 1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: during slot switch")
                    return -1
                update_phones(self.id)
                return res
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during switch_slot")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method erase_partition
    # ----------------------------------------------------------------------------
    def erase_partition(self, partition):
        try:
            if self.mode == 'adb' and get_adb():
                res = self.reboot_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
                self.refresh_phone_mode()
            if self.mode == 'f.b' and get_fastboot():
                print(f"Erasing Partition [{partition}] for device: {self.id} ...")
                puml(f":Erasing Partition [{partition}];\n", True)
                theCmd = f"\"{get_fastboot()}\" -s {self.id} erase {partition}"
                debug(theCmd)
                # return run_shell(theCmd)
                return
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in erase_partition.")
            puml("#red:Encountered an error in erase_partition.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method lock_bootloader
    # ----------------------------------------------------------------------------
    def lock_bootloader(self):
        try:
            if self.mode == 'adb' and get_adb():
                res = self.reboot_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
                self.refresh_phone_mode()
            if self.mode == 'f.b' and get_fastboot():
                # add a popup warning before continuing.
                print(f"Unlocking bootloader for device: {self.id} ...")
                theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing lock"
                debug(theCmd)
                return run_shell(theCmd)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in lock_bootloader.")
            puml("#red:Encountered an error in lock_bootloader.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method unlock_bootloader
    # ----------------------------------------------------------------------------
    def unlock_bootloader(self):
        try:
            if self.mode == 'adb' and get_adb():
                res = self.reboot_bootloader()
                if res == -1:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while rebooting to bootloader")
                self.refresh_phone_mode()
            if self.mode == 'f.b' and get_fastboot():
                print(f"Unlocking bootloader for device: {self.id} ...")
                theCmd = f"\"{get_fastboot()}\" -s {self.id} flashing unlock"
                debug(theCmd)
                return run_shell(theCmd)
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in unlock_bootloader.")
            puml("#red:Encountered an error in unlock_bootloader.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method install_magisk_module
    # ----------------------------------------------------------------------------
    def install_magisk_module(self, module):
        try:
            if self.mode == 'adb' and get_adb():
                print(f"Installing magisk module {module} ...")
                puml(":Install magisk module;\n", True)
                puml(f"note right:{module};\n")
                module_name = os.path.basename(module)
                res = self.push_file(f"\"{module}\"", f"/sdcard/Download/{module_name}", with_su=False)
                if res != 0:
                    puml("#red:Failed to transfer the module file to the phone;\n")
                    print("Aborting ...\n}\n")
                    return
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk --install-module /sdcard/Download/{module_name}\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                if res.returncode != 0:
                    puml("#red:Failed to transfer the install module;\n")
                    print("Aborting ...\n}\n")
                    return -1
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml(f"#red:ERROR: Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in install_magisk_module.")
            puml("#red:Encountered an error in install_magisk_module.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method enable_magisk_module
    # ----------------------------------------------------------------------------
    def enable_magisk_module(self, dirname):
        try:
            if self.mode == 'adb' and get_adb():
                print(f"Enabling magisk module {dirname} ...")
                puml(":Enable magisk module;\n", True)
                puml(f"note right:{dirname};\n")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/modules/{dirname}/disable\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml(f"#red:ERROR: Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in enable_magisk_module.")
            puml("#red:Encountered an error in enable_magisk_module.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method restore_magisk_module
    # ----------------------------------------------------------------------------
    def restore_magisk_module(self, dirname):
        try:
            if self.mode == 'adb' and get_adb():
                print(f"Restoring magisk module {dirname} ...")
                puml(":Restore magisk module;\n", True)
                puml(f"note right:{dirname};\n")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'rm -f /data/adb/modules/{dirname}/remove\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml(f"#red:ERROR: Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in restore_magisk_module.")
            puml("#red:Encountered an error in restore_magisk_module.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method open_shell
    # ----------------------------------------------------------------------------
    def open_shell(self):
        try:
            config = get_config()
            if self.mode == 'adb' and get_adb():
                print(f"Opening an adb shell command for device: {self.id} ...")
                puml(":Opening an adb shell command;\n", True)
                theCmd = f"\"{get_adb()}\" -s {self.id} shell"
                debug(theCmd)
                if sys.platform.startswith("win"):
                    subprocess.Popen(theCmd, creationflags=subprocess.CREATE_NEW_CONSOLE, start_new_session=True, env=get_env_variables())
                elif sys.platform.startswith("linux") and config.linux_shell:
                    subprocess.Popen([get_linux_shell(), "--", "/bin/bash", "-c", theCmd], start_new_session=True)
                elif sys.platform.startswith("darwin"):
                    script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
                    script_file.write(f'#!/bin/bash\n{theCmd}'.encode('utf-8'))
                    script_file.close()
                    os.chmod(script_file.name, 0o755)
                    subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{script_file.name}"'], start_new_session=True, env=get_env_variables())
                    os.remove(script_file.name)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml("#red:ERROR: The Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in open_shell.")
            puml("#red:Encountered an error in open_shell.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method scrcpy
    # ----------------------------------------------------------------------------
    def scrcpy(self):
        try:
            config = get_config()
            scrcpy_path = config.scrcpy['path']
            flags = config.scrcpy['flags']
            if not os.path.exists(scrcpy_path):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: invalid scrcpy path {scrcpy_path} ")
                return 1
            scrcpy_folder = os.path.dirname(scrcpy_path)
            if self.mode == 'adb' and get_adb():
                print(f"Launching scrcpy for device: {self.id} ...")
                puml(":Launching scrcpy;\n", True)
                theCmd = f"\"{scrcpy_path}\" -s {self.id} {flags}"
                debug(theCmd)
                if sys.platform.startswith("win"):
                    subprocess.Popen(theCmd, cwd=scrcpy_folder, start_new_session=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif sys.platform.startswith("linux") and config.linux_shell:
                    subprocess.Popen([get_linux_shell(), "--", "/bin/bash", "-c", theCmd], start_new_session=True)
                elif sys.platform.startswith("darwin"):
                    script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
                    script_file.write(f'#!/bin/bash\n{theCmd}'.encode('utf-8'))
                    script_file.close()
                    os.chmod(script_file.name, 0o755)
                    subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{script_file.name}"'], start_new_session=True, env=get_env_variables())
                    os.remove(script_file.name)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml("#red:ERROR: The Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in scrcpy.")
            puml("#red:Encountered an error in scrcpy.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method uninstall_magisk_module
    # ----------------------------------------------------------------------------
    def uninstall_magisk_module(self, dirname):
        try:
            if self.mode == 'adb' and get_adb():
                print(f"Uninstalling magisk module {dirname} ...")
                puml(":Uninstall magisk module;\n", True)
                puml(f"note right:{dirname};\n")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'touch /data/adb/modules/{dirname}/remove\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml("#red:ERROR: The Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in uninstall_magisk_module.")
            puml("#red:Encountered an error in uninstall_magisk_module.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_module
    # ----------------------------------------------------------------------------
    def disable_magisk_module(self, dirname):
        try:
            if self.mode == 'adb' and get_adb():
                print(f"Disabling magisk module {dirname} ...")
                puml(":Disable magisk module;\n", True)
                puml(f"note right:{dirname};\n")
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'touch /data/adb/modules/{dirname}/disable\'\""
                debug(theCmd)
                res = run_shell(theCmd)
                return 0
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: The Device: {self.id} is not in adb mode.")
                puml("#red:ERROR: The Device: {self.id} is not in adb mode;\n", True)
                return 1
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in disable_magisk_module.")
            puml("#red:Encountered an error in disable_magisk_module.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method disable_magisk_modules
    # ----------------------------------------------------------------------------
    def disable_magisk_modules(self):
        try:
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
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in disable_magisk_modules.")
            puml("#red:Encountered an error in disable_magisk_modules.;\n")
            traceback.print_exc()
            return -1

    # ----------------------------------------------------------------------------
    #                               Method refresh_phone_mode
    # ----------------------------------------------------------------------------
    def refresh_phone_mode(self):
        try:
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
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in refresh_phone_mode.")
            puml("#red:Encountered an error in refresh_phone_mode.;\n")
            traceback.print_exc()
            return -1

    # ============================================================================
    #                               Function ui_action
    # ============================================================================
    def ui_action(self, dump_file, local_file, look_for=None, click=True):
        try:
            # Get uiautomator dump, save as dump_file
            # the_view = "view1.xml"
            res = self.uiautomator_dump(dump_file)
            if res == -1:
                puml("#red:Failed to uiautomator dump;\n}\n")
                return -1

            # Pull dump_file
            print(f"Pulling {dump_file} from the phone to: {local_file} ...")
            res = self.pull_file(dump_file, local_file)
            if res != 0:
                puml("#red:Failed to pull uiautomator dump from the phone;\n}\n")
                return -1

            coords = -1
            if look_for is not None:
                if look_for == "PixelFlasher_Playstore":
                    coords = get_playstore_user_coords(local_file)
                else:
                    # get bounds
                    coords = get_ui_cooridnates(local_file, look_for)

                if click:
                    if coords is None or coords == '' or coords == -1:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not tap. Coordinates are [{coords}]")
                        return -1

                    # Check for Display being locked again
                    if not self.is_display_unlocked():
                        print("ERROR: The device display is Locked!\n")
                        return -1

                    # Click on coordinates
                    res = self.click(coords)
                    if res == -1:
                        puml("#red:Failed to click;\n}\n")
                        return -1

                    # Sleep 2 seconds
                    print("Sleeping 2 seconds to make sure the view is loaded ...")
                    time.sleep(2)

                    # Check for Display being locked again
                    if not self.is_display_unlocked():
                        print("ERROR: The device display is Locked!\n")
                        return -1
                return coords
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while performing ui action")
            puml("#red:Encountered an error while performing ui action;\n")
            traceback.print_exc()

    # ----------------------------------------------------------------------------
    #                               method perform_package_action
    # ----------------------------------------------------------------------------
    def perform_package_action(self, pkg, action, isSystem=False):
        # possible actions 'uninstall', 'disable', 'enable', 'launch', 'launch-am', 'launch-am-main', 'kill', killall', 'clear-data', 'clear-cache', 'add-to-denylist', 'rm-from-denylist', 'optimize', 'reset-optimize'
        if self.mode != 'adb':
            return
        if action in ['add-to-denylist', 'rm-from-denylist'] and get_magisk_package() == 'io.github.huskydg.magisk':
                print("Magisk denylist is currently not supported in PixelFlasher for Magisk Delta.")
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
            elif action == 'launch-am':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell am start -n {pkg}/{pkg}.MainActivity"
            elif action == 'launch-am-main':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell am start -n {pkg}/{pkg}.main.MainActivity"
            elif action == 'kill':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell am force-stop {pkg}"
            elif action == 'killall':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'killall -v {pkg}\'\""
            elif action == 'clear-data':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm clear {pkg}"
            elif action == 'clear-cache':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm clear --cache-only {pkg}"
            elif action == 'add-to-denylist':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk --denylist add {pkg}\'\""
            elif action == 'rm-from-denylist':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'magisk --denylist rm {pkg}\'\""
            elif action == 'optimize':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell cmd {pkg} compile -m speed-profile -a"
            elif action == 'reset-optimize':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell cmd {pkg} compile --reset -a"

            return run_shell2(theCmd)
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not {action} {pkg}.")

    # ----------------------------------------------------------------------------
    #                               method get_package_list
    # ----------------------------------------------------------------------------
    def get_package_list(self, state = ''):
        # possible options 'all', 'all+uninstalled', 'disabled', 'enabled', 'system', '3rdparty', 'user0', 'uid'
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
            elif state == 'uid':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell pm list packages -U"

            res = run_shell(theCmd)
            if res.returncode == 0:
                return res.stdout.replace('package:','')
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list of {state}.")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
            return None
        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get package list of {state}.")
            return None


    # ----------------------------------------------------------------------------
    #                               method get_detailed_packages
    # ----------------------------------------------------------------------------
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
                if item:
                    package = Package(item)
                    package.type = "System"
                    package.installed = False
                    with contextlib.suppress(Exception):
                        package.label = labels[item]
                    self.packages[item] = package

            # Get all packages
            list = self.get_package_list('all')
            if list:
                for item in list.split("\n"):
                    if item and item in self.packages:
                        self.packages[item].installed = True

            # Get 3rd party packages
            list = self.get_package_list('3rdparty')
            if list:
                for item in list.split("\n"):
                    if item and item in self.packages:
                        self.packages[item].type = '3rd Party'

            # Get disabled packages
            list = self.get_package_list('disabled')
            if list:
                for item in list.split("\n"):
                    if item and item in self.packages:
                        self.packages[item].enabled = False

            # Get enabled packages
            list = self.get_package_list('enabled')
            if list:
                for item in list.split("\n"):
                    if item and item in self.packages:
                        self.packages[item].enabled = True

            # Get user 0 packages
            list = self.get_package_list('user0')
            if list:
                for item in list.split("\n"):
                    if item and item in self.packages:
                        self.packages[item].user0 = True

            # Get magisk denylist packages
            list = self.get_magisk_denylist()
            if list:
                for item in list:
                    if item and item in self.packages:
                        self.packages[item].magisk_denylist = True

            # Get package UIDs
            list = self.get_package_list('uid')
            if list:
                for item in list.split("\n"):
                    if item:
                        package, uid = item.split(" ", 1)
                        uid = uid.replace("uid:", "")
                        if package in self.packages:
                            self.packages[package].uid = uid

        except Exception as e:
            traceback.print_exc()
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get detailed packages.")
            puml("#red:ERROR: Could not get detailed packages;\n", True)
            return -1
        return 0


# ============================================================================
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print(f"debug: {message}")


# ============================================================================
#                               Function update_phones
# ============================================================================
def update_phones(device_id):
    try:
        phones = get_phones()
        devices = get_device_list()
        # Find the index of the entry you want to replace
        index_to_replace = None
        for i, device in enumerate(phones):
            if device.id == device_id:
                index_to_replace = i
                device = None
                break
        if get_adb():
            theCmd = f"\"{get_adb()}\" -s {device_id} get-state"
            response = run_shell(theCmd, timeout=60)
            if response.returncode == 0:
                device_mode = response.stdout.strip('\n')
                if device_mode == "device":
                    device = Device(device_id, 'adb')
                else:
                    device = Device(device_id, 'adb', device_mode)
                device.init('adb')
                device_details = device.get_device_details()
        if get_fastboot():
            theCmd = f"\"{get_fastboot()}\" -s {device_id} devices"
            response = run_shell(theCmd)
            if response.returncode == 0 and 'fastboot' in response.stdout:
                device = Device(device_id, 'f.b')
                device.init('f.b')
                device_details = device.get_device_details()
        # Replace the entry at the found index with the new device_details or remove if it does not exist
        if index_to_replace is not None:
            if device:
                phones[index_to_replace] = device
                devices[index_to_replace] = device_details
                set_phone_id(device.id)
            else:
                with contextlib.suppress(Exception):
                    del phones[index_to_replace]
                    del devices[index_to_replace]
                    set_phone_id(None)
        set_phones(phones)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while updating phones.")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")

    set_device_list(devices)
    return devices


# ============================================================================
#                               Function get_connected_devices
# ============================================================================
def get_connected_devices():
    devices = []
    phones = []

    try:
        if get_adb():
            theCmd = f"\"{get_adb()}\" devices"
            response = run_shell(theCmd, timeout=60)
            if response.stdout:
                debug(f"adb devices:\n{response.stdout}")
                for device in response.stdout.split('\n'):
                    if 'device' in device or 'recovery' in device or 'sideload' in device or 'rescue' in device:
                        if device == "List of devices attached":
                            continue
                        # with contextlib.suppress(Exception):
                        try:
                            d_id = device.split("\t")
                            if len(d_id) != 2:
                                continue
                            mode = d_id[1].strip()
                            d_id = d_id[0].strip()
                            true_mode = None
                            if mode in ('recovery', 'sideload', 'rescue'):
                                true_mode = mode
                            device = Device(d_id, 'adb', true_mode)
                            device.init('adb')
                            device_details = device.get_device_details()
                            devices.append(device_details)
                            phones.append(device)
                        except Exception as e:
                            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting connected devices.")
                            traceback.print_exc()

            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to determine Android Platform Tools version.\n")
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")

        if get_fastboot():
            theCmd = f"\"{get_fastboot()}\" devices"
            response = run_shell(theCmd)
            for device in response.stdout.split('\n'):
                debug(f"fastboot devices:\n{response.stdout}")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting connected devices.")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")

    set_device_list(devices)
    return devices
