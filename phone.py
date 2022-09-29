#!/usr/bin/env python

import contextlib
import re
import subprocess
import time
from datetime import datetime

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
        self._rooted = None
        self._root_symbol = None
        self._magisk_version = None
        self._magisk_app_version = None
        self._build = None
        self._hardware = None
        self._active_slot = None
        self._unlocked = None
        self._bootloader_version = None
        self._device_info = None
        self._magisk_modules = None
        self._magisk_detailed_modules = None
        self._magisk_modules_summary = None
        self._magisk_apks = None
        self._api_level = None

    # ----------------------------------------------------------------------------
    #                               property root_symbol
    # ----------------------------------------------------------------------------
    @property
    def root_symbol(self):
        if self._root_symbol is None:
            if self.mode == 'f.b':
                self._root_symbol = '?'
            elif self.rooted:
                self._root_symbol = '✓'
            else:
                self._root_symbol = '✗'
        return self._root_symbol

    # ----------------------------------------------------------------------------
    #                               property magisk_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_version(self):
        if self._magisk_version is None and self.mode == 'adb':
            if self.rooted:
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
                except Exception:
                    try:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'/data/adb/magisk/magisk32 -c\'\""
                        res = run_shell(theCmd)
                        if res.returncode == 0:
                            self._magisk_version = res.stdout
                    except Exception:
                        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk version, assuming that it is not rooted.")
                        self._rooted = None
            self._magisk_version = self._magisk_version.strip('\n')
        return self._magisk_version

    # ----------------------------------------------------------------------------
    #                               property magisk_app_version
    # ----------------------------------------------------------------------------
    @property
    def magisk_app_version(self):
        if self._magisk_app_version is None and self.mode == 'adb':
            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package {get_magisk_package()} | grep versionName"
                res = run_shell(theCmd)
                version = res.stdout.split('\n')
                version = version[0].split('=')
                version = version[1]
            except Exception:
                return ''

            try:
                theCmd = f"\"{get_adb()}\" -s {self.id} shell dumpsys package {get_magisk_package()} | grep versionCode"
                res = run_shell(theCmd)
                versionCode = res.stdout.split('\n')
                versionCode = versionCode[0].split('=')
                versionCode = versionCode[1]
                versionCode = versionCode.split(' ')
                versionCode = versionCode[0]
            except Exception:
                return version

            self._magisk_app_version = f"{version}:{versionCode}"
        return self._magisk_app_version

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_magisk_version
    # ----------------------------------------------------------------------------
    def get_uncached_magisk_version(self):
        self._magisk_version is None
        return self.magisk_version

    # ----------------------------------------------------------------------------
    #                               Method get_uncached_magisk_app_version
    # ----------------------------------------------------------------------------
    def get_uncached_magisk_app_version(self):
        self._magisk_app_version is None
        return self.magisk_app_version

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
        print("Stopping Magisk ...")
        with contextlib.suppress(Exception):
            if self.mode == 'adb':
                theCmd = f"\"{get_adb()}\" -s {self.id} shell am force-stop {get_magisk_package()}"
                res = run_shell(theCmd)

    # ----------------------------------------------------------------------------
    #                               property magisk_modules
    # ----------------------------------------------------------------------------
    @property
    def magisk_modules(self):
        if self._magisk_modules is None and self.mode == 'adb':
            if self.rooted:
                try:
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell \"su -c \'ls /data/adb/modules\'\""
                    res = run_shell(theCmd)
                    if res.returncode == 0:
                        self._magisk_modules = res.stdout.split('\n')
                except Exception:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get magisk modules, assuming that it is not rooted.")
                    self._rooted = None
                    self._magisk_modules = ''
            else:
                self._magisk_modules = ''
        return self._magisk_modules

    # ----------------------------------------------------------------------------
    #                               property magisk_detailed_modules
    # ----------------------------------------------------------------------------
    @property
    def magisk_detailed_modules(self):
        if self._magisk_detailed_modules is None:
            try:
                if self.mode == 'adb' and self.rooted:
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
                mlist = ['stable', 'beta', 'canary', 'debug']
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
    #                               property hardware
    # ----------------------------------------------------------------------------
    @property
    def hardware(self):
        if self._hardware is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.hardware"
                    hardware = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    self._hardware = ''.join(hardware.stdout.split())
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar product"
                    hardware = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    hardware = hardware.stderr.split('\n')
                    hardware = hardware[0].split(' ')
                    self._hardware = hardware[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._hardware

    # ----------------------------------------------------------------------------
    #                               property api_level
    # ----------------------------------------------------------------------------
    @property
    def api_level(self):
        if self._api_level is None:
            if self.mode == 'adb':
                if get_adb():
                    try:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.build.version.sdk"
                        version_sdk = run_shell(theCmd)
                        # remove any whitespace including tab and newline
                        self._api_level = ''.join(version_sdk.stdout.split())
                    except Exception:
                        self._api_level = ''
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            else:
               self._api_level = ''
        return self._api_level

    # ----------------------------------------------------------------------------
    #                               property build
    # ----------------------------------------------------------------------------
    @property
    def build(self):
        if self._build is None:
            if self.mode == 'adb':
                if get_adb():
                    try:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.build.fingerprint"
                        fingerprint = run_shell(theCmd)
                        # remove any whitespace including tab and newline
                        fingerprint = ''.join(fingerprint.stdout.split())
                        self._build = fingerprint.split('/')[3]
                    except Exception:
                        self._build = ''
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            else:
               self._build = ''
        return self._build

    # ----------------------------------------------------------------------------
    #                               property active_slot
    # ----------------------------------------------------------------------------
    @property
    def active_slot(self):
        if self._active_slot is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell /bin/getprop ro.boot.slot_suffix"
                    active_slot = run_shell(theCmd)
                    if active_slot.returncode == 127:
                        theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.boot.slot_suffix"
                        active_slot = run_shell(theCmd)
                    active_slot = active_slot.stdout.replace("\n", "")
                    self._active_slot = active_slot.replace("_", "")
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar current-slot"
                    active_slot = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    active_slot = active_slot.stderr.split('\n')
                    active_slot = active_slot[0].split(' ')
                    self._active_slot = active_slot[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._active_slot

    # ----------------------------------------------------------------------------
    #                               property unlocked
    # ----------------------------------------------------------------------------
    @property
    def unlocked(self):
        if self._unlocked is None and self.mode == 'f.b':
            if get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar unlocked"
                unlocked = run_shell(theCmd)
                # remove any whitespace including tab and newline
                unlocked = unlocked.stderr.split('\n')
                unlocked = unlocked[0].split(' ')
                unlocked = unlocked[1]
                if unlocked == 'yes':
                    self._unlocked = True
                else:
                    self._unlocked = False
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._unlocked

    # ----------------------------------------------------------------------------
    #                               property bootloader_version
    # ----------------------------------------------------------------------------
    @property
    def bootloader_version(self):
        if self._bootloader_version is None:
            if self.mode == 'adb':
                if get_adb():
                    theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop ro.bootloader"
                    bootloader_version = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    self._bootloader_version = ''.join(bootloader_version.stdout.split())
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
            elif self.mode == 'f.b':
                if get_fastboot():
                    theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar version-bootloader"
                    bootloader_version = run_shell(theCmd)
                    # remove any whitespace including tab and newline
                    bootloader_version = bootloader_version.stderr.split('\n')
                    bootloader_version = bootloader_version[0].split(' ')
                    self._bootloader_version = bootloader_version[1]
                else:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._bootloader_version

    # ----------------------------------------------------------------------------
    #                               property device_info
    # ----------------------------------------------------------------------------
    @property
    def device_info(self):
        if self.mode == 'adb':
            if get_adb():
                theCmd = f"\"{get_adb()}\" -s {self.id} shell getprop"
                device_info = run_shell(theCmd)
                self._device_info = ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adb command is not found!")
        elif self.mode == 'f.b':
            if get_fastboot():
                theCmd = f"\"{get_fastboot()}\" -s {self.id} getvar all"
                device_info = run_shell(theCmd)
                if (device_info.stdout == ''):
                    self._device_info = ''.join(device_info.stderr)
                else:
                    self._device_info = ''.join(device_info.stdout)
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")
        return self._device_info

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
            theCmd = f"\"{get_adb()}\" -s {self.id} install {app}"
            debug(theCmd)
            res = run_shell(theCmd)
            if res.returncode != 0:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an errorwhile installing {app}")
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
                device_details = device.get_device_details()
                devices.append(device_details)
                phones.append(device)
    else:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: fastboot command is not found!")

    set_phones(phones)
    return devices
