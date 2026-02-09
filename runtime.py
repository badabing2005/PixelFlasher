#!/usr/bin/env python

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2025 Badabing2005
# SPDX-FileCopyrightText: 2025 Badabing2005
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If your software can interact with users remotely through a computer network,
# you should also make sure that it provides a way for users to get its source.
# For example, if your program is a web application, its interface could
# display a "Source" link that leads users to an archive of the code. There are
# many ways you could offer source, and different solutions will be better for
# different programs; see section 13 for the specific requirements.
#
# You should also get your employer (if you work as a programmer) or school, if
# any, to sign a "copyright disclaimer" for the program, if necessary. For more
# information on this, and how to apply and follow the GNU AGPL, see
# <https://www.gnu.org/licenses/>.

import apk
import binascii
import contextlib
import chardet
import fnmatch
import hashlib
import html
import io
import json
import json5
import math
import ntpath
import os
import re
import shutil
import signal
import sqlite3 as sl
import subprocess
import sys
import random
import tarfile
import tempfile
import threading
import time
import traceback
import zipfile
import psutil
import xml.etree.ElementTree as ET
import urllib3
import warnings
from datetime import datetime, timezone, timedelta
from os import path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from i18n import _, set_language
import lz4.frame
import requests
import wx
from packaging.version import parse
from platformdirs import *
from constants import *
from payload_dumper import extract_payload
from ksu_asset_selector import show_ksu_asset_selector
import cProfile, pstats, io
import avbtool

app_language = 'en'  # Default language is English
_verbose = False
_adb = None
_fastboot = None
_adb_sha256 = None
_fastboot_sha256 = None
_phones = []
_device_list = []
_phone_id = None
# _advanced_options = False
# _update_check = True
_firmware_model = None
_firmware_id = None
_custom_rom_id = None
_logfile = None
_pumlfile = None
_sdk_version = None
_image_mode = None
_image_path = None
_custom_rom_file = None
_message_box_title = None
_message_box_message = None
# _version = None
_db = None
_boot = None
_system_code_page = None
# _codepage_setting = False
# _codepage_value = ''
_magisk_package = ''
# _file_explorer = ''
_linux_shell = ''
_patched_with = ''
# _customize_font = False
# _pf_font_face = ''
# _pf_font_size = 12
_app_labels = {}
_xiaomi_list = {}
_favorite_pifs = {}
_a_only = False
# _offer_patch_methods = False
# _use_busybox_shell = False
_firmware_hash_valid = False
_firmware_has_init_boot = False
_rom_has_init_boot = False
_dlg_checkbox_values = None
# _recovery_patch = False
_config_path = None
_android_versions = {}
_android_devices = {}
_env_variables = os.environ.copy()
_is_ota = False
_sdk_is_ok = False
_low_memory = False
_config = {}
_config_file_path = ''
_unlocked_devices = []
_window_shown = False
_puml_enabled = True
_rooting_app_apks = None
_selected_boot_partition = None


# ============================================================================
#                               Class Boot
# ============================================================================
class Boot():
    def __init__(self):
        self.boot_id = None
        self.boot_hash = None
        self.boot_path = None
        self.is_patched = None
        self.patch_method = None
        self.magisk_version = None
        self.hardware = None
        self.boot_epoch = None
        self.package_id = None
        self.package_boot_hash = None
        self.package_type = None
        self.package_sig = None
        self.package_path = None
        self.package_epoch = None
        self.is_odin = None
        self.is_stock_boot = None
        self.is_init_boot = None
        self.patch_source_sha1 = None
        self.spl = None


# ============================================================================
#                               Class BetaData
# ============================================================================
class BetaData:
    def __init__(self, release_date, build, emulator_support, security_patch_level, google_play_services, beta_expiry_date, incremental, security_patch, devices):
        self.release_date = release_date
        self.build = build
        self.emulator_support = emulator_support
        self.security_patch_level = security_patch_level
        self.google_play_services = google_play_services
        self.beta_expiry_date = beta_expiry_date
        self.incremental = incremental
        self.security_patch = security_patch
        self.devices = devices


# ============================================================================
#                               Class Coords
# ============================================================================
class Coords:
    def __init__(self):
        self.file_path = get_coords_file_path()
        self.data = self.load_data()

    def load_data(self):
        with contextlib.suppress(Exception):
            if path.exists(self.file_path):
                with open(self.file_path, "r", encoding='ISO-8859-1', errors="replace") as file:
                    return json.load(file)
        return {}

    def save_data(self):
        with open(self.file_path, 'w', encoding='ISO-8859-1', errors="replace", newline='\n') as file:
            json.dump(self.data, file, indent=4)

    def query_entry(self, device, package):
        if device in self.data and package in self.data[device]:
            return self.data[device][package]
        return None

    def query_nested_entry(self, device, package, nested_key):
        if device in self.data and package in self.data[device] and nested_key in self.data[device][package]:
            return self.data[device][package][nested_key]
        return None

    def update_entry(self, device, package, coordinates):
        if device not in self.data:
            self.data[device] = {}
        self.data[device][package] = coordinates
        self.save_data()

    def update_nested_entry(self, device, package, nested_key, nested_value):
        if device not in self.data:
            self.data[device] = {}
        if package not in self.data[device]:
            self.data[device][package] = {}
        self.data[device][package][nested_key] = nested_value
        self.save_data()


# ============================================================================
#                               Class ModuleUpdate
# ============================================================================
class ModuleUpdate():
    def __init__(self, url):
        self.url = url


# ============================================================================
#                               Class MagiskApk
# ============================================================================
class MagiskApk():
    def __init__(self, type):
        self.type = type


# ============================================================================
#                               Function get_app_language
# ============================================================================
def get_app_language():
    global _app_language
    return _app_language


# ============================================================================
#                               Function set_app_language
# ============================================================================
def set_app_language(value):
    global _app_language
    _app_language = value
    # Update the actual translation system
    set_language(value)

# ============================================================================
#                               Function get_config
# ============================================================================
def get_config():
    global _config
    return _config


# ============================================================================
#                               Function set_config
# ============================================================================
def set_config(value):
    global _config
    _config = value


# ============================================================================
#                               Function get_window_shown
# ============================================================================
def get_window_shown():
    global _window_shown
    return _window_shown


# ============================================================================
#                               Function set_window_shown
# ============================================================================
def set_window_shown(value):
    global _window_shown
    _window_shown = value


# ============================================================================
#                               Function check_for_unlocked
# ============================================================================
def check_for_unlocked(item):
    global _unlocked_devices
    if item in _unlocked_devices:
        return True
    else:
        return False


# ============================================================================
#                               Function add_unlocked_device
# ============================================================================
def add_unlocked_device(item):
    global _unlocked_devices
    if item not in _unlocked_devices:
        _unlocked_devices.append(item)


# ============================================================================
#                               Function remove_unlocked_device
# ============================================================================
def remove_unlocked_device(item):
    global _unlocked_devices
    if item in _unlocked_devices:
        _unlocked_devices.remove(item)


# ============================================================================
#                               Function get_unlocked_device
# ============================================================================
def get_unlocked_device():
    global _unlocked_devices
    return _unlocked_devices


# ============================================================================
#                               Function set_console_widget
# ============================================================================
def set_console_widget(widget):
    global _console_widget
    _console_widget = widget


# ============================================================================
#                               Function flush_output
# ============================================================================
def flush_output():
    global _console_widget
    if get_window_shown():
        wx.YieldIfNeeded()
    if _console_widget:
        sys.stdout.flush()
        wx.CallAfter(_console_widget.Update)
        if get_window_shown():
            wx.YieldIfNeeded()


# ============================================================================
#                               Function get_boot
# ============================================================================
def get_boot():
    global _boot
    return _boot


# ============================================================================
#                               Function set_boot
# ============================================================================
def set_boot(value):
    global _boot
    _boot = value


# ============================================================================
#                               Function get_labels
# ============================================================================
def get_labels():
    global _app_labels
    return _app_labels


# ============================================================================
#                               Function set_labels
# ============================================================================
def set_labels(value):
    global _app_labels
    _app_labels = value


# ============================================================================
#                               Function get_xiaomi
# ============================================================================
def get_xiaomi():
    global _xiaomi_list
    return _xiaomi_list


# ============================================================================
#                               Function set_xiaomi
# ============================================================================
def set_xiaomi(value):
    global _xiaomi_list
    _xiaomi_list = value


# ============================================================================
#                               Function get_favorite_pifs
# ============================================================================
def get_favorite_pifs():
    global _favorite_pifs
    return _favorite_pifs


# ============================================================================
#                               Function set_favorite_pifs
# ============================================================================
def set_favorite_pifs(value):
    global _favorite_pifs
    _favorite_pifs = value


# ============================================================================
#                               Function get_low_memory
# ============================================================================
def get_low_memory():
    global _low_memory
    return _low_memory


# ============================================================================
#                               Function set_low_memory
# ============================================================================
def set_low_memory(value):
    global _low_memory
    _low_memory = value


# ============================================================================
#                               Function get_android_versions
# ============================================================================
def get_android_versions():
    global _android_versions
    return _android_versions


# ============================================================================
#                               Function set_android_versions
# ============================================================================
def set_android_versions(value):
    global _android_versions
    _android_versions = value


# ============================================================================
#                               Function get_android_devices
# ============================================================================
def get_android_devices():
    global _android_devices
    return _android_devices


# ============================================================================
#                               Function set_android_devices
# ============================================================================
def set_android_devices(value):
    global _android_devices
    _android_devices = value


# ============================================================================
#                               Function get_env_variables
# ============================================================================
def get_env_variables():
    global _env_variables
    return _env_variables


# ============================================================================
#                               Function set_env_variables
# ============================================================================
def set_env_variables(value):
    global _env_variables
    _env_variables = value


# ============================================================================
#                               Function get_patched_with
# ============================================================================
def get_patched_with():
    global _patched_with
    return _patched_with


# ============================================================================
#                               Function set_patched_with
# ============================================================================
def set_patched_with(value):
    global _patched_with
    _patched_with = value


# ============================================================================
#                               Function get_db
# ============================================================================
def get_db():
    global _db
    return _db


# ============================================================================
#                               Function set_db
# ============================================================================
def set_db(value):
    global _db
    _db = value


# ============================================================================
#                               Function get_boot_images_dir
# ============================================================================
def get_boot_images_dir():
    # boot_images did not change at version 5, so we can keep on using 4
    if parse(VERSION) < parse('4.0.0'):
        return 'boot_images'
    else:
        return 'boot_images4'


# ============================================================================
#                               Function get_factory_images_dir
# ============================================================================
def get_factory_images_dir():
    # factory_images only changed after version 5
    if parse(VERSION) < parse('9.0.0'):
        return 'factory_images'
    else:
        return 'factory_images9'


# ============================================================================
#                               Function get_pf_db
# ============================================================================
def get_pf_db():
    # we have different db schemas for each of these versions
    if parse(VERSION) < parse('4.0.0'):
        return 'PixelFlasher.db'
    elif parse(VERSION) < parse('99.0.0'):
        return 'PixelFlasher4.db'
    else:
        return 'PixelFlasher99.db'


# ============================================================================
#                               Function get_verbose
# ============================================================================
def get_verbose():
    global _verbose
    return _verbose


# ============================================================================
#                               Function set_verbose
# ============================================================================
def set_verbose(value):
    global _verbose
    _verbose = value


# ============================================================================
#                               Function get_a_only
# ============================================================================
def get_a_only():
    global _a_only
    return _a_only


# ============================================================================
#                               Function set_a_only
# ============================================================================
def set_a_only(value):
    global _a_only
    _a_only = value


# ============================================================================
#                   Function get_selected_boot_partition
# ============================================================================
def get_selected_boot_partition():
    global _selected_boot_partition
    return _selected_boot_partition


# ============================================================================
#                   Function set_selected_boot_partition
# ============================================================================
def set_selected_boot_partition(value):
    global _selected_boot_partition
    _selected_boot_partition = value


# ============================================================================
#                               Function get_adb
# ============================================================================
def get_adb():
    global _adb
    return _adb


# ============================================================================
#                               Function set_adb
# ============================================================================
def set_adb(value):
    global _adb
    _adb = value


# ============================================================================
#                               Function get_puml_state
# ============================================================================
def get_puml_state():
    global _puml_enabled
    return _puml_enabled


# ============================================================================
#                               Function set_puml_state
# ============================================================================
def set_puml_state(value):
    global _puml_enabled
    _puml_enabled = value


# ============================================================================
#                               Function get_fastboot
# ============================================================================
def get_fastboot():
    global _fastboot
    return _fastboot


# ============================================================================
#                               Function set_fastboot
# ============================================================================
def set_fastboot(value):
    global _fastboot
    _fastboot = value


# ============================================================================
#                               Function get_adb_sha256
# ============================================================================
def get_adb_sha256():
    global _adb_sha256
    return _adb_sha256


# ============================================================================
#                               Function set_adb_sha256
# ============================================================================
def set_adb_sha256(value):
    global _adb_sha256
    _adb_sha256 = value


# ============================================================================
#                               Function get_fastboot_sha256
# ============================================================================
def get_fastboot_sha256():
    global _fastboot_sha256
    return _fastboot_sha256


# ============================================================================
#                               Function set_fastboot_sha256
# ============================================================================
def set_fastboot_sha256(value):
    global _fastboot_sha256
    _fastboot_sha256 = value


# ============================================================================
#                               Function get_phones
# ============================================================================
def get_phones():
    global _phones
    return _phones


# ============================================================================
#                               Function set_phones
# ============================================================================
def set_phones(value):
    global _phones
    _phones = value


# ============================================================================
#                               Function get_device_list
# ============================================================================
def get_device_list():
    global _device_list
    return _device_list


# ============================================================================
#                               Function set_device_list
# ============================================================================
def set_device_list(value):
    global _device_list
    _device_list = value


# ============================================================================
#                               Function get_phone_id
# ============================================================================
def get_phone_id():
    global _phone_id
    return _phone_id


# ============================================================================
#                               Function set_phone_id
# ============================================================================
def set_phone_id(value):
    global _phone_id
    _phone_id = value


# ============================================================================
#                               Function get_phone
# ============================================================================
def get_phone(make_sure_connected=False):
    devices = get_phones()
    phone_id = get_phone_id()
    if phone_id and devices:
        for phone in devices:
            if phone.id == phone_id:
                if make_sure_connected and not phone.is_connected(phone_id):
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device: {phone_id} is not connected.")
                    return None
                return phone


# ============================================================================
#                               Function get_system_codepage
# ============================================================================
def get_system_codepage():
    global _system_code_page
    return _system_code_page


# ============================================================================
#                               Function set_system_codepage
# ============================================================================
def set_system_codepage(value):
    global _system_code_page
    _system_code_page = value


# ============================================================================
#                               Function get_magisk_package
# ============================================================================
def get_magisk_package():
    global _magisk_package
    return _magisk_package


# ============================================================================
#                               Function set_magisk_package
# ============================================================================
def set_magisk_package(value):
    global _magisk_package
    _magisk_package = value


# ============================================================================
#                               Function get_linux_shell
# ============================================================================
def get_linux_shell():
    global _linux_shell
    return _linux_shell


# ============================================================================
#                               Function set_linux_shell
# ============================================================================
def set_linux_shell(value):
    global _linux_shell
    _linux_shell = value


# ============================================================================
#                               Function get_is_ota
# ============================================================================
def get_ota():
    global _is_ota
    return _is_ota


# ============================================================================
#                               Function set_ota
# ============================================================================
def set_ota(self, value):
    global _is_ota
    _is_ota = value
    self.config.firmware_is_ota = value
    if value:
        self.enable_disable_radio_button('OTA', True, selected=True, just_select=True)
        self.config.flash_mode = 'OTA'
    elif self.config.flash_mode == 'OTA':
            self.config.flash_mode = 'dryRun'
            self.enable_disable_radio_button('dryRun', True, selected=True, just_select=True)


# ============================================================================
#                               Function get_sdk_state
# ============================================================================
def get_sdk_state():
    global _sdk_is_ok
    return _sdk_is_ok


# ============================================================================
#                               Function set_sdk_state
# ============================================================================
def set_sdk_state(value):
    global _sdk_is_ok
    _sdk_is_ok = value


# ============================================================================
#                               Function get_firmware_hash_validity
# ============================================================================
def get_firmware_hash_validity():
    global _firmware_hash_valid
    return _firmware_hash_valid


# ============================================================================
#                               Function set_firmware_hash_validity
# ============================================================================
def set_firmware_hash_validity(value):
    global _firmware_hash_valid
    _firmware_hash_valid = value


# ============================================================================
#                               Function get_firmware_has_init_boot
# ============================================================================
def get_firmware_has_init_boot():
    global _firmware_has_init_boot
    return _firmware_has_init_boot


# ============================================================================
#                               Function set_firmware_has_init_boot
# ============================================================================
def set_firmware_has_init_boot(value):
    global _firmware_has_init_boot
    _firmware_has_init_boot = value


# ============================================================================
#                               Function get_rom_has_init_boot
# ============================================================================
def get_rom_has_init_boot():
    global _rom_has_init_boot
    return _rom_has_init_boot


# ============================================================================
#                               Function set_rom_has_init_boot
# ============================================================================
def set_rom_has_init_boot(value):
    global _rom_has_init_boot
    _rom_has_init_boot = value


# ============================================================================
#                               Function get_dlg_checkbox_values
# ============================================================================
def get_dlg_checkbox_values():
    global _dlg_checkbox_values
    return _dlg_checkbox_values


# ============================================================================
#                               Function set_dlg_checkbox_values
# ============================================================================
def set_dlg_checkbox_values(value):
    global _dlg_checkbox_values
    _dlg_checkbox_values = value


# ============================================================================
#                               Function get_firmware_model
# ============================================================================
def get_firmware_model():
    global _firmware_model
    return _firmware_model


# ============================================================================
#                               Function set_firmware_model
# ============================================================================
def set_firmware_model(value):
    global _firmware_model
    _firmware_model = value


# ============================================================================
#                               Function get_firmware_id
# ============================================================================
def get_firmware_id():
    global _firmware_id
    return _firmware_id


# ============================================================================
#                               Function set_firmware_id
# ============================================================================
def set_firmware_id(value):
    global _firmware_id
    _firmware_id = value


# ============================================================================
#                               Function get_custom_rom_id
# ============================================================================
def get_custom_rom_id():
    global _custom_rom_id
    return _custom_rom_id


# ============================================================================
#                               Function set_custom_rom_id
# ============================================================================
def set_custom_rom_id(value):
    global _custom_rom_id
    _custom_rom_id = value


# ============================================================================
#                               Function get_logfile
# ============================================================================
def get_logfile():
    global _logfile
    return _logfile


# ============================================================================
#                               Function set_logfile
# ============================================================================
def set_logfile(value):
    global _logfile
    _logfile = value


# ============================================================================
#                               Function get_pumlfile
# ============================================================================
def get_pumlfile():
    global _pumlfile
    return _pumlfile


# ============================================================================
#                               Function set_pumlfile
# ============================================================================
def set_pumlfile(value):
    global _pumlfile
    _pumlfile = value


# ============================================================================
#                               Function get_sdk_version
# ============================================================================
def get_sdk_version():
    global _sdk_version
    return _sdk_version


# ============================================================================
#                               Function set_sdk_version
# ============================================================================
def set_sdk_version(value):
    global _sdk_version
    _sdk_version = value


# ============================================================================
#                               Function get_image_mode
# ============================================================================
def get_image_mode():
    global _image_mode
    return _image_mode


# ============================================================================
#                               Function set_image_mode
# ============================================================================
def set_image_mode(value):
    global _image_mode
    _image_mode = value


# ============================================================================
#                               Function get_image_path
# ============================================================================
def get_image_path():
    global _image_path
    return _image_path


# ============================================================================
#                               Function set_image_path
# ============================================================================
def set_image_path(value):
    global _image_path
    _image_path = value


# ============================================================================
#                               Function get_custom_rom_file
# ============================================================================
def get_custom_rom_file():
    global _custom_rom_file
    return _custom_rom_file


# ============================================================================
#                               Function set_custom_rom_file
# ============================================================================
def set_custom_rom_file(value):
    global _custom_rom_file
    _custom_rom_file = value


# ============================================================================
#                               Function get_message_box_title
# ============================================================================
def get_message_box_title():
    global _message_box_title
    return _message_box_title


# ============================================================================
#                               Function set_message_box_title
# ============================================================================
def set_message_box_title(value):
    global _message_box_title
    _message_box_title = value


# ============================================================================
#                               Function get_message_box_message
# ============================================================================
def get_message_box_message():
    global _message_box_message
    return _message_box_message


# ============================================================================
#                               Function set_message_box_message
# ============================================================================
def set_message_box_message(value):
    global _message_box_message
    _message_box_message = value


# ============================================================================
#                               Function get_downgrade_boot_path
# ============================================================================
def get_downgrade_boot_path():
    boot = get_boot()
    if not boot:
        return None, False

    boot_path = boot.boot_path
    directory_path = os.path.dirname(boot_path)
    downgrade_file_name = "downgrade_boot.img"
    downgrade_file_path = os.path.join(directory_path, downgrade_file_name)
    if os.path.exists(downgrade_file_path):
        return downgrade_file_path, True
    else:
        return downgrade_file_path, False


# ============================================================================
#                               Function has_init_boot
# ============================================================================
def has_init_boot(device_codename):
    try:
        android_devices = get_android_devices()
        if not android_devices or device_codename not in android_devices:
            return False
        return android_devices[device_codename]['has_init_boot']
    except Exception as e:
        return False


# ============================================================================
#                               Function is_pixel_watch
# ============================================================================
def is_pixel_watch(device_codename):
    try:
        android_devices = get_android_devices()
        if not android_devices or device_codename not in android_devices:
            return False
        return android_devices[device_codename]['is_pixel_watch']
    except Exception as e:
        return False


# ============================================================================
#                               Function puml
# ============================================================================
def puml(message='', left_ts = False, mode='a'):
    if get_puml_state():
        with open(get_pumlfile(), mode, encoding="ISO-8859-1", errors="replace") as puml_file:
            puml_file.write(message)
            if left_ts:
                puml_file.write(f"note left:{datetime.now():%Y-%m-%d %H:%M:%S}\n")


# ============================================================================
#                               Function init_config_path
# ============================================================================
def init_config_path(config_file_path=''):
    try:
        config_path = get_sys_config_path()
        set_config_path(config_path)
        with contextlib.suppress(Exception):
            if config_file_path == '':
                config_file_path = os.path.join(config_path, CONFIG_FILE_NAME)
            print(f"config_file_path: {config_file_path}")
            set_config_file_path(config_file_path)
            if os.path.exists(config_file_path):
                encoding = detect_encoding(config_file_path)
                with open(config_file_path, 'r', encoding=encoding, errors="replace") as f:
                    data = json.load(f)
                pf_home = data['pf_home']
                if pf_home and os.path.exists(pf_home):
                    set_config_path(pf_home)
        config_path = get_config_path()
        directories = ['logs', 'factory_images', get_boot_images_dir(), 'tmp', 'puml']
        for directory in directories:
            full_path = os.path.join(config_path, directory)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while init_config_path")
        traceback.print_exc()


# ============================================================================
#                               Function init_db
# ============================================================================
def init_db():
    try:
        global _db
        config_path = get_sys_config_path()
        # connect / create db
        _db = sl.connect(os.path.join(config_path, get_pf_db()))
        _db.execute("PRAGMA foreign_keys = ON")
        # create tables
        with _db:
            # PACKAGE Table
            _db.execute("""
                CREATE TABLE IF NOT EXISTS PACKAGE (
                    id INTEGER NOT NULL PRIMARY KEY,
                    boot_hash TEXT NOT NULL,
                    type TEXT CHECK (type IN ('firmware', 'rom')) NOT NULL,
                    package_sig TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    epoch INTEGER NOT NULL
                );
            """)
            # BOOT Table
            _db.execute("""
                CREATE TABLE IF NOT EXISTS BOOT (
                    id INTEGER NOT NULL PRIMARY KEY,
                    boot_hash TEXT NOT NULL UNIQUE,
                    file_path TEXT NOT NULL,
                    is_patched INTEGER CHECK (is_patched IN (0, 1)),
                    magisk_version TEXT,
                    hardware TEXT,
                    epoch INTEGER NOT NULL,
                    patch_method TEXT
                );
            """)
            # PACKAGE_BOOT Table
            _db.execute("""
                CREATE TABLE IF NOT EXISTS PACKAGE_BOOT (
                    package_id INTEGER,
                    boot_id INTEGER,
                    epoch INTEGER NOT NULL,
                    PRIMARY KEY (package_id, boot_id),
                    FOREIGN KEY (package_id) REFERENCES PACKAGE(id),
                    FOREIGN KEY (boot_id) REFERENCES BOOT(id)
                );
            """)

            # Check if the patch_method and is_odin column already exists in the BOOT table
            # Added in version 5.1
            cursor = _db.execute("PRAGMA table_info(BOOT)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            if 'patch_method' not in column_names:
                # Add the patch_method column to the BOOT table
                _db.execute("ALTER TABLE BOOT ADD COLUMN patch_method TEXT;")
            if 'is_odin' not in column_names:
                # Add the is_odin column to the BOOT table
                _db.execute("ALTER TABLE BOOT ADD COLUMN is_odin INTEGER;")
            # Added in version 5.4
            if 'is_stock_boot' not in column_names:
                # Add the is_stock_boot column to the BOOT table
                _db.execute("ALTER TABLE BOOT ADD COLUMN is_stock_boot INTEGER;")
            if 'is_init_boot' not in column_names:
                # Add the is_init_boot column to the BOOT table
                _db.execute("ALTER TABLE BOOT ADD COLUMN is_init_boot INTEGER;")
            if 'patch_source_sha1' not in column_names:
                # Add the patch_source_sha1 column to the BOOT table
                _db.execute("ALTER TABLE BOOT ADD COLUMN patch_source_sha1 INTEGER;")

            # Check if the full_ota column already exists in the PACKAGE table
            # Added in version 5.8
            cursor = _db.execute("PRAGMA table_info(PACKAGE)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            if 'full_ota' not in column_names:
                # Add the full_ota column to the BOOT table (values: 0:Not Full OTA, 1:Full OTA NULL:UNKNOWN)
                _db.execute("ALTER TABLE PACKAGE ADD COLUMN full_ota INTEGER;")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while init_db")
        traceback.print_exc()


# ============================================================================
#                               Function get_config_file_path
# ============================================================================
def get_config_file_path():
    # return os.path.join(get_sys_config_path(), CONFIG_FILE_NAME).strip()
    global _config_file_path
    return _config_file_path


# ============================================================================
#                           Function set_config
# ============================================================================
def set_config_file_path(value):
    global _config_file_path
    _config_file_path = value


# ============================================================================
#                       Function get_sys_config_path
# ============================================================================
def get_sys_config_path():
    return user_data_dir(APPNAME, appauthor=False, roaming=True)


# ============================================================================
#                         Function get_config_path
# ============================================================================
def get_config_path():
    global _config_path
    return _config_path


# ============================================================================
#                       Function set_config_path
# ============================================================================
def set_config_path(value):
    global _config_path
    _config_path = value


# ============================================================================
#                      Function get_labels_file_path
# ============================================================================
def get_labels_file_path():
    return os.path.join(get_config_path(), "labels.json").strip()


# ============================================================================
#                     Function get_xiaomi_file_path
# ============================================================================
def get_xiaomi_file_path():
    return os.path.join(get_config_path(), "xiaomi.json").strip()


# ============================================================================
#                    Function get_favorite_pifs_file_path
# ============================================================================
def get_favorite_pifs_file_path():
    return os.path.join(get_config_path(), "favorite_pifs.json").strip()


# ============================================================================
#                 Function get_device_images_history_file_path
# ============================================================================
def get_device_images_history_file_path():
    return os.path.join(get_config_path(), "device_images_history.json").strip()


# ============================================================================
#                        Function get_coords_file_path
# ============================================================================
def get_coords_file_path():
    return os.path.join(get_config_path(), "coords.json").strip()


# ============================================================================
#                        Function get_skip_urls_file_path
# ============================================================================
def get_skip_urls_file_path():
    return os.path.join(get_config_path(), "skip_urls.txt").strip()


# ============================================================================
#                        Function get_wifi_history_file_path
# ============================================================================
def get_wifi_history_file_path():
    return os.path.join(get_config_path(), "wireless.json").strip()


# ============================================================================
#                        Function get_mytools_file_path
# ============================================================================
def get_mytools_file_path():
    return os.path.join(get_config_path(), "mytools.json").strip()


# ============================================================================
#                        Function get_devices_file_path
# ============================================================================
def get_devices_file_path():
    return os.path.join(get_config_path(), "devices.json").strip()


# ============================================================================
#                           Function load_devices_json
# ============================================================================
def load_devices_json():
    try:
        file_path = get_devices_file_path()
        if os.path.exists(file_path):
            encoding = detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors="replace") as f:
                data = json.load(f)
                return data.get('devices', {})
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error loading devices.json: {e}")
    return {}


# ============================================================================
#                         Function save_devices_json
# ============================================================================
def save_devices_json(devices_data):
    try:
        file_path = get_devices_file_path()
        data = {'devices': devices_data}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error saving devices.json: {e}")
        return False


# ============================================================================
#                    Function add_or_update_device
# ============================================================================
def add_or_update_device(device_id, device_name='', hardware='', connected=True):
    try:
        devices = load_devices_json()
        now = datetime.now().isoformat()

        if device_id not in devices:
            # New device - add with enabled=True by default
            devices[device_id] = {
                'enabled': True,
                'device_name': device_name,
                'hardware': hardware,
                'custom_label': '',  # Empty by default, user can set via Manage Devices
                'first_detected': now,
                'last_seen': now,
                'connected': connected
            }
            print(f"New device detected and added to devices.json: {device_id} ({device_name})")
        else:
            # Update existing device
            devices[device_id]['last_seen'] = now
            devices[device_id]['connected'] = connected
            if device_name:
                devices[device_id]['device_name'] = device_name
            if hardware:
                devices[device_id]['hardware'] = hardware

        save_devices_json(devices)
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error updating device {device_id}: {e}")
        return False


# ============================================================================
#                     Function is_device_enabled
# ============================================================================
def is_device_enabled(device_id):
    try:
        devices = load_devices_json()
        if device_id in devices:
            return devices[device_id].get('enabled', True)
        # If device not in file, it's considered enabled (will be added as enabled)
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error checking device {device_id}: {e}")
        return True


# ============================================================================
#                     Function toggle_device_enabled
# ============================================================================
def toggle_device_enabled(device_id):
    try:
        devices = load_devices_json()
        if device_id in devices:
            current_state = devices[device_id].get('enabled', True)
            devices[device_id]['enabled'] = not current_state
            save_devices_json(devices)
            return devices[device_id]['enabled']
        return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error toggling device {device_id}: {e}")
        return None


# ============================================================================
#                     Function get_device_display_name
# ============================================================================
def get_device_display_name(device_id, device_info=None):
    # Get display name for a device. Format: device_id : custom_label or device_id : hardware
    # Priority: custom_label > hardware > device_name > device_id
    try:
        devices = load_devices_json()
        if device_id in devices:
            # Priority 1: custom_label (user-defined)
            custom_label = devices[device_id].get('custom_label', '')
            if custom_label:
                return f"{device_id} : {custom_label}"

            # Priority 2: hardware
            hardware = devices[device_id].get('hardware', '')
            if hardware:
                return f"{device_id} : {hardware}"

            # Priority 3: device_name
            device_name = devices[device_id].get('device_name', '')
            if device_name:
                return f"{device_id} : {device_name}"

        # Fallback to device_info if provided
        if device_info and hasattr(device_info, 'hardware'):
            return f"{device_id} : {device_info.hardware}"
        return device_id
    except Exception:
        return device_id


# ============================================================================
#                     Function update_device_custom_label
# ============================================================================
def update_device_custom_label(device_id, custom_label):
    try:
        devices = load_devices_json()
        if device_id in devices:
            devices[device_id]['custom_label'] = custom_label.strip()
            save_devices_json(devices)
            return True
        return False
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error updating custom label for device {device_id}: {e}")
        return False


# ============================================================================
#                         Function delete_device
# ============================================================================
def delete_device(device_id):
    try:
        devices = load_devices_json()
        if device_id in devices:
            del devices[device_id]
            save_devices_json(devices)
            return True
        return False
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error deleting device {device_id}: {e}")
        return False


# ============================================================================
#                Function update_all_devices_connection_status
# ============================================================================
def update_all_devices_connection_status(connected_device_ids):
    try:
        devices = load_devices_json()
        for device_id in devices:
            devices[device_id]['connected'] = device_id in connected_device_ids
        save_devices_json(devices)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Error updating device connection status: {e}")


# ============================================================================
#                        Function get_path_to_7z
# ============================================================================
def get_path_to_7z():
    if sys.platform == "win32":
        path_to_7z =  os.path.join(get_bundle_dir(),'bin', '7z.exe')
    elif sys.platform == "darwin":
        path_to_7z =  os.path.join(get_bundle_dir(),'bin', '7zz')
    else:
        path_to_7z =  os.path.join(get_bundle_dir(),'bin', '7zzs')

    if not os.path.exists(path_to_7z):
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {path_to_7z} is not found")
        return None
    return path_to_7z


# ============================================================================
#                               Function delete_bundled_library
# ============================================================================
# Example usage
# delete_bundled_library("libreadline.so.8, libgtk*")
def delete_bundled_library(library_names):
    try:
        if not getattr(sys, 'frozen', False):
            return
        bundle_dir = sys._MEIPASS
        debug(f"Bundle Directory: {bundle_dir}")
        if bundle_dir:
            names = library_names.split(",")
            for file_name in os.listdir(bundle_dir):
                for name in names:
                    if fnmatch.fnmatch(file_name, name.strip()):
                        file_path = os.path.join(bundle_dir, file_name)
                        print(f"Found library and deleted: {file_path}")
                        os.remove(file_path)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while deleting bundled library")
        traceback.print_exc()


# ============================================================================
#                               Function get_bundle_dir
# ============================================================================
# set by PyInstaller, see http://pyinstaller.readthedocs.io/en/v3.2/runtime-information.html
# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def get_bundle_dir():
    if getattr(sys, 'frozen', False):
        # noinspection PyUnresolvedReferences,PyProtectedMember
        # running in a bundle
        return sys._MEIPASS
    else:
        # running live
        return os.path.dirname(os.path.abspath(__file__))


# ============================================================================
#                               Function check_latest_version
# ============================================================================
def check_latest_version():
    try:
        url = 'https://github.com/badabing2005/PixelFlasher/releases/latest'
        response = request_with_fallback(method='GET', url=url)
        # look in history to find the 302, and get the location header
        location = response.history[0].headers['Location']
        # split by '/' and get the last item
        l_version = location.split('/')[-1]
        # If it starts with v, remove it
        if l_version[:1] == "v":
            version = l_version[1:]
        if version.count('.') == 2:
            version = f"{version}.0"
    except Exception:
        version = '0.0.0.0'
    return version


# ============================================================================
#                               Function enabled_disabled
# ============================================================================
def enabled_disabled(data):
    if data:
        return "Enabled"
    else:
        return "Disabled"


# ============================================================================
#                               Function grow_column
# ============================================================================
def grow_column(list, col, value = 20):
    w = list.GetColumnWidth(col)
    list.SetColumnWidth(col, w + value)


# ============================================================================
#                               Function open_folder
# ============================================================================
def open_folder(self, path, isFile = False):
    try:
        if not path:
            return
        if isFile:
            dir_path = os.path.dirname(path)
        else:
            dir_path = path
        if not os.path.exists(dir_path):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {dir_path} does not exist.")
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", dir_path], env=get_env_variables())
        elif sys.platform == "win32":
            os.startfile(dir_path)
        # linux
        elif self.config.linux_file_explorer:
            try:
                explorer_name = os.path.basename(self.config.linux_file_explorer.lower())

                # Handle specific file managers that need special treatment
                if explorer_name in ["dolphin", "nautilus"]:
                    try:
                        # Try with --new-window flag first
                        subprocess.Popen([self.config.linux_file_explorer, "--new-window", dir_path], env=get_env_variables())
                        return
                    except:
                        # Fallback to basic launch
                        subprocess.Popen([self.config.linux_file_explorer, dir_path], env=get_env_variables())
                        return
                else:
                    try:
                        # All other file managers work with just the path
                        subprocess.Popen([self.config.linux_file_explorer, dir_path], env=get_env_variables())
                        return
                    except:
                        # Fallback to --new-window launch
                        subprocess.Popen([self.config.linux_file_explorer, "--new-window", dir_path], env=get_env_variables())
                        return

            except FileNotFoundError:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Configured file explorer '{self.config.linux_file_explorer}' not found.")
                return
            except Exception as e:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to launch configured file explorer: {e}")
                return
        else:
            # No file explorer configured, try automatic detection
            # Try xdg-open first as it's the standard way
            try:
                subprocess.Popen(["xdg-open", dir_path], env=get_env_variables())
            except FileNotFoundError:
                # Fallback to common file managers with proper handling
                file_managers = [
                    ("dolphin", ["--new-window"]),
                    ("nautilus", ["--new-window"]),
                    ("thunar", []),
                    ("pcmanfm", []),
                    ("nemo", [])
                ]
                for fm, args in file_managers:
                    try:
                        cmd = [fm] + args + [dir_path]
                        subprocess.Popen(cmd, env=get_env_variables())
                        return  # Success, exit the function
                    except FileNotFoundError:
                        continue
                # If all fail
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: No suitable file explorer found. Please install xdg-utils or set linux_file_explorer in settings.")
                return
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a folder.")
        traceback.print_exc()


# ============================================================================
#                               Function open_terminal
# ============================================================================
def open_terminal(self, path, isFile=False):
    try:
        if path:
            if isFile:
                dir_path = os.path.dirname(path)
            else:
                dir_path = path
            if sys.platform.startswith("win"):
                subprocess.Popen(["start", "cmd.exe", "/k", "cd", "/d", dir_path], shell=True, env=get_env_variables())
            elif sys.platform.startswith("linux"):
                if self.config.linux_shell:
                    # Handle different terminal applications with their specific arguments
                    terminal_name = os.path.basename(self.config.linux_shell.lower())
                    if terminal_name in ["konsole"]:
                        subprocess.Popen([self.config.linux_shell, "--workdir", dir_path], env=get_env_variables())
                    elif terminal_name in ["gnome-terminal", "xfce4-terminal", "terminator", "alacritty"]:
                        subprocess.Popen([self.config.linux_shell, "--working-directory", dir_path], env=get_env_variables())
                    elif terminal_name in ["kitty"]:
                        subprocess.Popen([self.config.linux_shell, "--directory", dir_path], env=get_env_variables())
                    else:
                        # Fallback: try common arguments or just launch without directory
                        try:
                            subprocess.Popen([self.config.linux_shell, "--working-directory", dir_path], env=get_env_variables())
                        except:
                            try:
                                subprocess.Popen([self.config.linux_shell, "--workdir", dir_path], env=get_env_variables())
                            except:
                                try:
                                    subprocess.Popen([self.config.linux_shell, "--directory", dir_path], env=get_env_variables())
                                except:
                                    # Last resort: change directory then launch terminal
                                    subprocess.Popen(f"cd '{dir_path}' && {self.config.linux_shell}", shell=True, env=get_env_variables())
                else:
                    try:
                        subprocess.Popen(["gnome-terminal", "--working-directory", dir_path], env=get_env_variables())
                    except FileNotFoundError:
                        try:
                            subprocess.Popen(["konsole", "--workdir", dir_path], env=get_env_variables())
                        except FileNotFoundError:
                            try:
                                subprocess.Popen(["xfce4-terminal", "--working-directory", dir_path], env=get_env_variables())
                            except FileNotFoundError:
                                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: No suitable terminal found. Please set linux_shell in config.")
                                return
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", "-a", "Terminal", dir_path], env=get_env_variables())
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a terminal.")
        traceback.print_exc()


# ============================================================================
#                      Function get_compression_method
# ============================================================================
def get_compression_method(zip_path, file_to_replace):
    try:
        path_to_7z = get_path_to_7z()
        theCmd = f"\"{path_to_7z}\" l -slt \"{zip_path}\""
        result = subprocess.run(theCmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()

        # Parse the output to find the compression method
        in_file_section = False
        for line in output.splitlines():
            if line.startswith("Path = "):
                in_file_section = file_to_replace in line
            if in_file_section and line.startswith("Method = "):
                return line.split(" = ")[1]
        return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function get_compression_method.")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function extract_from_nested_tgz
# ============================================================================
def extract_from_nested_tgz(archive_path, file_paths, output_dir):
    """
    Extract files from nested archives (like tgz -> tar -> folder structure).

    Args:
        archive_path: Path to the outer archive file
        file_paths: List of filenames to extract
        output_dir: Directory to extract files to

    Returns:
        True if all files were successfully extracted, False otherwise
    """

    temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())
    success = True

    try:
        path_to_7z = get_path_to_7z()

        # First extract the outer archive (tgz) to get the inner archive (tar)
        debug(f"Extracting outer archive to {temp_dir}")

        cmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir}\" \"{archive_path}\""
        debug(f"{cmd}")
        result = run_shell(cmd)
        if result.returncode != 0:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to extract outer archive")
            return False

        # Find the inner tar file
        tar_file = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.tar'):
                    tar_file = os.path.join(root, file)
                    break
            if tar_file:
                break

        if not tar_file:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find inner tar archive")
            return False

        # Extract the tar file to the temp directory
        debug(f"Extracting inner archive {tar_file}")

        inner_extract_dir = os.path.join(temp_dir, "inner")
        os.makedirs(inner_extract_dir, exist_ok=True)

        cmd = f"\"{path_to_7z}\" x -bd -y -o\"{inner_extract_dir}\" \"{tar_file}\""
        debug(f"{cmd}")
        result = run_shell(cmd)
        if result.returncode != 0:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to extract inner archive")
            return False
        # delete the tar file
        os.remove(tar_file)

        # Copy each needed file to the output directory
        for file_name in file_paths.split():
            found = False
            file_path = None

            for root, _, files in os.walk(inner_extract_dir):
                for file in files:
                    if file == file_name:
                        file_path = os.path.join(root, file)
                        found = True
                        break
                if found:
                    break

            if file_path and os.path.exists(file_path):
                output_file = os.path.join(output_dir, file_name)
                shutil.copy2(file_path, output_file)
                debug(f"Extracted {file_name} to {output_file}")
            else:
                print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {file_name} in extracted content")
                success = False

    except Exception as e:
        print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to extract from nested archive: {str(e)}")
        traceback.print_exc()
        success = False
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            debug(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: cleaning up temp directory: {str(e)}")
    return success


# ============================================================================
#                   Function replace_file_in_zip_with_7zip
# ============================================================================
def replace_file_in_zip_with_7zip(zip_path, file_to_replace, new_file_path):
    try:
        path_to_7z = get_path_to_7z()

        # Delete the existing file
        theCmd = f"\"{path_to_7z}\" d \"{zip_path}\" \"{file_to_replace}\""
        debug(theCmd)
        res = run_shell2(theCmd)

        # add the replacement file
        theCmd = f"\"{path_to_7z}\" a \"{zip_path}\" \"{new_file_path}\" -m0=Deflate -mx=0"
        debug(theCmd)
        res = run_shell2(theCmd)
        if res.returncode == 0:
            debug(f"Successfully replaced {file_to_replace} in {zip_path}")
            return True
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to replace {file_to_replace} in {zip_path}")
            print(res.stderr.decode())
            return False
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function replace_file_in_zip_with_7zip.")
        traceback.print_exc()
        return False


# ============================================================================
#                               Function check_archive_contains_file
# ============================================================================
def check_archive_contains_file(archive_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        debug(f"Looking for {file_to_check} in file {archive_file_path} with nested: {nested}")
        wx.Yield()

        file_ext = os.path.splitext(archive_file_path)[1].lower()

        if file_ext in ['.zip']:
            return check_zip_contains_file(archive_file_path, file_to_check, get_low_memory(), nested, is_recursive)
        elif file_ext in ['.img']:
            return check_img_contains_file(archive_file_path, file_to_check)
        elif file_ext in ['.tgz', '.gz', '.tar', '.md5']:
            return check_tar_contains_file(archive_file_path, file_to_check, nested, is_recursive)
        else:
            debug("Unsupported file format.")
            return ''
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while check_archive_contains_file.")
        traceback.print_exc()


# ============================================================================
#                               Function check_zip_contains_file
# ============================================================================
def check_zip_contains_file(zip_file_path, file_to_check, low_mem, nested=False, is_recursive=False):
    if low_mem:
        return check_zip_contains_file_lowmem(zip_file_path, file_to_check, nested, is_recursive)
    else:
        return check_zip_contains_file_fast(zip_file_path, file_to_check, nested, is_recursive)


# ============================================================================
#                               Function check_zip_contains_file_fast
# ============================================================================
def check_zip_contains_file_fast(zip_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        if not is_recursive:
            debug(f"Looking for {file_to_check} in zipfile {zip_file_path} with zip-nested: {nested}")
            wx.Yield()
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
                for name in zip_file.namelist():
                    if name.endswith(f'/{file_to_check}') or name == file_to_check:
                        if not is_recursive:
                            debug(f"Found: {name}\n")
                        return name
                    elif nested and name.endswith('.zip'):
                        debug(f"Entering nested zip: {name}")
                        with zip_file.open(name, 'r') as nested_zip_file:
                            nested_zip_data = nested_zip_file.read()
                        with io.BytesIO(nested_zip_data) as nested_zip_stream:
                            with zipfile.ZipFile(nested_zip_stream, 'r') as nested_zip:
                                nested_file_path = check_zip_contains_file_fast(nested_zip_stream, file_to_check, nested=True, is_recursive=True)
                                if nested_file_path:
                                    if not is_recursive:
                                        debug(f"Found: {name}/{nested_file_path}\n")
                                    return f'{name}/{nested_file_path}'
        except zipfile.BadZipFile:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: File {zip_file_path} is not a zip file or is corrupt, skipping this file ...")
            return ''
        debug(f"file: {file_to_check} was NOT found in checked zip on stack\n")
        return ''
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to check_zip_contains_file_fast. Reason: {e}")
        traceback.print_exc()
        return ''


# ============================================================================
#                               Function check_file_pattern_in_zip_file
# ============================================================================
def check_file_pattern_in_zip_file(zip_file_path, pattern, return_all_matches=False):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as myzip:
            if return_all_matches:
                matches = [file for file in myzip.namelist() if fnmatch.fnmatch(file, pattern)]
                return matches
            else:
                for file in myzip.namelist():
                    if fnmatch.fnmatch(file, pattern):
                        return file
        if return_all_matches:
            return []
        else:
            return ''
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to check_file_pattern_in_zip_file. Reason: {e}")
        traceback.print_exc()
        if return_all_matches:
            return []
        else:
            return ''


# ============================================================================
#                               Function check_img_contains_file
# ============================================================================
def check_img_contains_file(img_file_path, file_to_check):
    try:
        result = subprocess.run([get_path_to_7z(), 'l', img_file_path], capture_output=True, text=True)

        if "Unexpected end of archive" in result.stderr:
            print(f"⚠️ Warning: Unexpected end of archive in {img_file_path}")
            return []

        file_list = result.stdout.split('\n')

        matches = []
        for line in file_list:
            columns = line.split()
            if len(columns) < 6:  # Skip lines with less than 6 columns
                continue
            file_path = columns[5].replace('\\\\', '\\')
            if file_path.endswith(file_to_check):
                debug(f"Found: {file_path}\n")
                # matches.append(file_path)
                return file_path

        if not matches:
            debug(f"file: {file_to_check} was NOT found\n")

        return matches
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to check_img_contains_file. Reason: {e}")
        traceback.print_exc()
        return []


# ============================================================================
#                               Function check_zip_contains_file_lowmem
# ============================================================================
def check_zip_contains_file_lowmem(zip_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        if not is_recursive:
            debug(f"Looking for {file_to_check} in zipfile {zip_file_path} with zip-nested: {nested} Low Memory version.")
            wx.Yield()

        stack = [(zip_file_path, '')]
        temp_files = []

        while stack:
            current_zip, current_path = stack.pop()

            try:
                with zipfile.ZipFile(current_zip, 'r') as zip_file:
                    # Check for corrupted files
                    corrupted_file = zip_file.testzip()
                    if corrupted_file is not None:
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Corrupted file found: {corrupted_file} in {current_zip} - skipping this zip file ...")
                        continue

                    for name in zip_file.namelist():
                        full_name = os.path.join(current_path, name)
                        debug(f"Checking: {full_name}")

                        if os.path.basename(full_name) == file_to_check:
                            debug(f"Found: {full_name}")
                            return full_name
                        elif nested and name.endswith('.zip'):
                            debug(f"Entering nested zip: {full_name}")
                            with zip_file.open(name, 'r') as nested_zip_file:
                                nested_zip_data = nested_zip_file.read()

                            with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
                                temp_zip_file.write(nested_zip_data)
                                temp_zip_path = temp_zip_file.name

                            # Close the temporary zip file
                            temp_zip_file.close()

                            stack.append((temp_zip_path, full_name))
                            temp_files.append(temp_zip_path)
                            if is_recursive:
                                stack.append((temp_zip_path, full_name))  # Add the nested zip to be processed recursively
            except zipfile.BadZipFile:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: File {current_zip} is not a zip file or is corrupt, skipping this file ...")
                continue

        debug(f"File {file_to_check} was NOT found")

        # Clean up the temporary zip files
        for temp_file in temp_files:
            os.remove(temp_file)

        return ''
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to check_zip_contains_file_lowmem. Reason: {e}")
        traceback.print_exc()
        return ''


# ============================================================================
#                               Function check_tar_contains_file
# ============================================================================
def check_tar_contains_file(tar_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        if not is_recursive:
            debug(f"Looking for {file_to_check} in tarfile {tar_file_path} with tar-nested: {nested}")
            wx.Yield()
        with tarfile.open(tar_file_path, 'r') as tar_file:
            for member in tar_file.getmembers():
                if member.name.endswith(f'/{file_to_check}') or member.name == file_to_check:
                    if not is_recursive:
                        debug(f"Found: {member.name}\n")
                    return member.name
                elif nested and member.name.endswith('.tar'):
                    nested_tar_file_path = tar_file.extractfile(member).read()
                    nested_file_path = check_tar_contains_file(nested_tar_file_path, file_to_check, nested=True, is_recursive=True)
                    if nested_file_path:
                        if not is_recursive:
                            debug(f"Found: {member.name}/{nested_file_path}\n")
                        return f'{member.name}/{nested_file_path}'
                elif nested and member.name.endswith('.zip'):
                    with tar_file.extractfile(member) as nested_zip_file:
                        nested_zip_data = nested_zip_file.read()

                    # Create a temporary file to write the nested zip data
                    with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
                        temp_zip_file.write(nested_zip_data)
                        temp_zip_path = temp_zip_file.name

                    nested_file_path = check_zip_contains_file(temp_zip_path, file_to_check, get_low_memory(), nested=True, is_recursive=True)
                    if nested_file_path:
                        if not is_recursive:
                            debug(f"Found: {member.name}/{nested_file_path}\n")
                        return f'{member.name}/{nested_file_path}'

                    # Clean up the temporary zip file
                    os.remove(temp_zip_path)
            debug(f"File {file_to_check} was NOT found\n")
            return ''
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while check_tar_contains_file.")
        traceback.print_exc()


# ============================================================================
#                               Function get_zip_file_list
# ============================================================================
def get_zip_file_list(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            file_list = zip_file.namelist()
        return file_list
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting sip file list.")
        traceback.print_exc()


# ============================================================================
#                               Function get_filenames_in_dir
# ============================================================================
def get_filenames_in_dir(directory, isFile = False):
    # sourcery skip: inline-immediately-returned-variable, list-comprehension
    if not directory:
        return
    if isFile:
        dir_path = os.path.dirname(directory)
    else:
        dir_path = directory
    file_names = []
    for file in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, file)):
            file_names.append(file)
    return file_names


# ============================================================================
#                               Function find_file_by_prefix
# ============================================================================
def find_file_by_prefix(directory, prefix):
    for filename in os.listdir(directory):
        if filename.startswith(prefix):
            return os.path.join(directory, filename)
    return None


# ============================================================================
#                               Function get_ui_coordinates
# ============================================================================
def get_ui_cooridnates(xmlfile, search):
    with open(xmlfile, "r", encoding='ISO-8859-1', errors="replace") as fin:
        data = fin.read()
    regex = re.compile(rf'{search}.*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]".+')

    m = re.findall(regex, data)
    if m:
        debug(f"Found Bounds: {m[0][0]} {m[0][1]} {m[0][2]} {m[0][3]}")
        x = int((int(m[0][0]) + int(m[0][2])) / 2)
        y = int((int(m[0][1]) + int(m[0][3])) / 2)
        debug(f"Click Coordinates: {x} {y}")
        return f"{x} {y}"


# ============================================================================
#                               Function get_playstore_user_coords
# ============================================================================
def get_playstore_user_coords(xmlfile):
    with open(xmlfile, "r", encoding='ISO-8859-1', errors="replace") as fin:
        xml_content = fin.read()

    # Find the position of "Voice Search"
    user_search_position = xml_content.find('Voice Search')

    # Check if "Voice Search" is found
    if user_search_position == -1:
        # Fallback to old version.
        user_search_position = xml_content.find('Show notifications and offers')

    if user_search_position != -1:
        node = xml_content.find('/node', user_search_position)

        if node != -1:
            bounds_pos = xml_content.find('bounds=', node)

            if bounds_pos != -1:
                value_start_pos = xml_content.find('"', bounds_pos) + 1
                value_end_pos = xml_content.find('"', value_start_pos)
                bounds = xml_content[value_start_pos:value_end_pos]

                bounds_values = re.findall(r'\d+', bounds)
                x = (int(bounds_values[0]) + int(bounds_values[2])) // 2
                y = (int(bounds_values[1]) + int(bounds_values[3])) // 2

                debug(f"Found Bounds: {bounds}")
                debug(f"Click Coordinates: {x} {y}")
                return f"{x} {y}"


# ============================================================================
#                               Function extract_sha1
# ============================================================================
def extract_sha1(binfile, length=8):
    with open(binfile, 'rb') as f:
        s = f.read()
        # Find SHA1=
        pos = s.find(b'\x53\x48\x41\x31\x3D')
        # Move to that location
        if pos != -1:
            # move to 5 characters from the found position
            f.seek(pos + 5, 0)
            # read length bytes
            byte_string = f.read(length)
            # convert byte string to hex string
            hex_string = binascii.hexlify(byte_string).decode('ascii')
            # convert hex string to ASCII string
            ascii_string = binascii.unhexlify(hex_string).decode('ascii', errors='replace')
            # replace non-decodable characters with ~
            ascii_string = ascii_string.replace('\ufffd', '~')
            # replace non-printable characters with !
            ascii_string = ''.join(['!' if ord(c) < 32 or ord(c) > 126 else c for c in ascii_string])
            return ascii_string
        else:
            return None


# ============================================================================
#                               Function compare_sha1
# ============================================================================
def compare_sha1(SHA1, Extracted_SHA1):
    try:
        if len(SHA1) != len(Extracted_SHA1):
            print("⚠️ Warning!: The SHA1 values have different lengths")
            return 0
        else:
            num_match = 0
            max_shift = 4  # Maximum allowed shift

            for i in range(len(SHA1)):
                if SHA1[i] == Extracted_SHA1[i]:
                    num_match += 1
                else:
                    shift_count = 0
                    j = 1
                    while j <= max_shift:
                        # Check if there is a match within the allowed shift range
                        if i + j < len(SHA1) and SHA1[i] == Extracted_SHA1[i + j]:
                            num_match += 1
                            shift_count = j
                            break
                        elif i - j >= 0 and SHA1[i] == Extracted_SHA1[i - j]:
                            num_match += 1
                            shift_count = -j
                            break
                        j += 1

                    # Adjust the position for the next iteration based on the shift count
                    i += shift_count

            # return confidence level
            return num_match / len(SHA1)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while comparing sha1.")
        traceback.print_exc()


# ============================================================================
#                               Function extract_fingerprint
# ============================================================================
def extract_fingerprint(binfile):
    try:
        with open(binfile, 'rb') as f:
            s = f.read()
            # Find fingerprint=
            pos = s.find(b'\x66\x69\x6E\x67\x65\x72\x70\x72\x69\x6E\x74')
            # Move to that location
            if pos == -1:
                return None
            # move to 12 characters from the found position
            f.seek(pos + 12, 0)
            # read 65 bytes
            byte_string = f.read(65)
            # convert byte string to hex string
            hex_string = binascii.hexlify(byte_string).decode('ascii')
            # convert hex string to ASCII string
            ascii_string = binascii.unhexlify(hex_string).decode('ascii', errors='replace')
            # replace non-decodable characters with ~
            ascii_string = ascii_string.replace('\ufffd', '~')
            # replace non-printable characters with !
            ascii_string = ''.join(['!' if ord(c) < 32 or ord(c) > 126 else c for c in ascii_string])
            return ascii_string
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while extracting fingerprint.")
        traceback.print_exc()


# ============================================================================
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print(f"debug: {message}")


# ============================================================================
#                               Function print_user_interaction_message
# ============================================================================
def print_user_interaction_message(mode):
    message = f'''
\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Programmatic reboot to mode {mode} is failing.
There could be several reasons for this.
- Your device bootloader is locked.
- The device / platform tools does not support this option.
- Your phone is not connected / detected.

Is your device is waiting for interaction? if so perform the actions manually.
- Using volume keys, scroll up and down and select the proper option.
- Press the power button to apply.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n
'''
    print(message)


# ============================================================================
#                               Function md5
# ============================================================================
def md5(fname):
    try:
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error computing md5.")
        traceback.print_exc()


# ============================================================================
#                               Function json_hexdigest
# ============================================================================
def json_hexdigest(json_string):
    # Convert the JSON string to a dictionary to eliminate space being a factor
    dictionary = json5.loads(json_string)

    # Convert the dictionary to a JSON string with sorted keys to keep them consistent
    sorted_json_string = json.dumps(dictionary, sort_keys=True)

    # Create a hash object using md5
    hash_object = hashlib.md5()

    # Update the hash object with the sorted JSON string
    hash_object.update(sorted_json_string.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    return hash_object.hexdigest()


# ============================================================================
#                               Function sha1
# ============================================================================
def sha1(fname):
    try:
        if not fname or not os.path.exists(fname):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: File [{fname}] does not exist, cannot compute sha1")
            return "NA Error"
        hash_sha1 = hashlib.sha1()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
        return hash_sha1.hexdigest()
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while computing sha1")
        traceback.print_exc()


# ============================================================================
#                               Function sha256
# ============================================================================
def sha256(fname):
    try:
        hash_sha256 = hashlib.sha256()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while computing sha256")
        traceback.print_exc()


# ============================================================================
#                               Function unpack_lz4
# ============================================================================
def unpack_lz4(source, dest):
    try:
        with open(source, 'rb') as file:
            compressed_data = file.read()
        decompressed_data = lz4.frame.decompress(compressed_data)
        with open(dest, 'wb') as file:
            file.write(decompressed_data)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while unpacking lz4")
        traceback.print_exc()


# ============================================================================
#                               Function create_boot_tar
# ============================================================================
def create_boot_tar(dir, source='boot.img', dest='boot.tar'):
    original_dir = os.getcwd()
    try:
        os.chdir(dir)
        with tarfile.open(dest, 'w', format=tarfile.GNU_FORMAT) as tar:
            tar.add(source, arcname=source)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while creating boot.tar")
        traceback.print_exc()
    finally:
        os.chdir(original_dir)


# ============================================================================
#                               Function get_code_page
# ============================================================================
def get_code_page():
    try:
        if sys.platform != "win32":
            return
        cp = get_system_codepage()
        if cp:
            print(f"Active code page: {cp}")
        else:
            theCmd = "chcp"
            res = run_shell(theCmd)
            if res and isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                # extract the code page portion
                try:
                    debug(f"CP: {res.stdout}")
                    cp = res.stdout.split(":")
                    cp = cp[1].strip()
                    cp = int(cp.replace('.',''))
                    print(f"Active code page: {cp}")
                    set_system_codepage(cp)
                except Exception:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to get Active code page.\n")
                    traceback.print_exc()
                    print(f"{res.stderr}")
                    print(f"{res.stdout}")
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to get Active code page.\n")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting codepage.")
        traceback.print_exc()


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
#                               Function remove_quotes
# ============================================================================
def remove_quotes(string):
    if string and string.startswith('"') and string.endswith('"'):
        # Remove existing double quotes
        string = string[1:-1]
    return string


# ============================================================================
#                               Function create_support_zip
# ============================================================================
def create_support_zip():
    try:
        print(f"\nℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} Creating support.zip file ...")
        config_path = get_config_path()
        sys_config_path = get_sys_config_path()
        config = get_config()
        tmp_dir_full = os.path.join(config_path, 'tmp')
        support_dir_full = os.path.join(config_path, 'support')
        support_zip = os.path.join(tmp_dir_full, 'support.zip')
        temp_dir = tempfile.gettempdir()

        # if a previous support dir exist delete it along with support.zip
        if os.path.exists(support_dir_full):
            debug("Deleting old support files ...")
            delete_all(support_dir_full)
        if os.path.exists(support_zip):
            debug("Deleting old support.zip ...")
            os.remove(support_zip)

        # create support folder if it does not exist
        if not os.path.exists(support_dir_full):
            os.makedirs(support_dir_full, exist_ok=True)

        # copy the default PixelFlasher.json to tmp\support folder
        to_copy = os.path.join(sys_config_path, 'PixelFlasher.json')
        if os.path.exists(to_copy):
            debug(f"Copying {to_copy} to {support_dir_full}")
            shutil.copy(to_copy, support_dir_full, follow_symlinks=True)

        # copy the loaded config json if it is different
        current_config = get_config_file_path()
        if to_copy != current_config:
            filename = ntpath.basename(current_config)
            folder = os.path.dirname(current_config)
            if filename.lower() == "pixelflasher.json":
                filename = "PixelFlasher_Custom.json"
            custom_config_file = os.path.join(folder, filename)
            debug(f"Copying {custom_config_file} to {support_dir_full}")
            shutil.copy(current_config, os.path.join(support_dir_full, filename), follow_symlinks=True)

        # copy PixelFlasher.db to tmp\support folder
        to_copy = os.path.join(sys_config_path, get_pf_db())
        if os.path.exists(to_copy):
            debug(f"Copying {to_copy} to {support_dir_full}")
            shutil.copy(to_copy, support_dir_full, follow_symlinks=True)

        # copy labels.json to tmp\support folder
        to_copy = os.path.join(config_path, 'labels.json')
        if os.path.exists(to_copy):
            debug(f"Copying {to_copy} to {support_dir_full}")
            shutil.copy(to_copy, support_dir_full, follow_symlinks=True)

        # copy logs to support folder
        to_copy = os.path.join(config_path, 'logs')
        logs_dir = os.path.join(support_dir_full, 'logs')
        if os.path.exists(to_copy):
            debug(f"Copying {to_copy} to {support_dir_full}")
            shutil.copytree(to_copy, logs_dir)

        # copy puml to support folder
        to_copy = os.path.join(config_path, 'puml')
        puml_dir = os.path.join(support_dir_full, 'puml')
        if os.path.exists(to_copy):
            debug(f"Copying {to_copy} to {support_dir_full}")
            shutil.copytree(to_copy, puml_dir)

        # create directory/file listing
        if sys.platform == "win32":
            theCmd = f"dir /s /b \"{config_path}\" > \"{os.path.join(support_dir_full, 'files.txt')}\""
        else:
            theCmd = f"ls -lRgn \"{config_path}\" > \"{os.path.join(support_dir_full, 'files.txt')}\""
        debug(f"{theCmd}")
        res = run_shell(theCmd)

        # sanitize json
        file_path = os.path.join(support_dir_full, 'PixelFlasher.json')
        if os.path.exists(file_path) and config.sanitize_support_files:
            sanitize_file(file_path)
        # sanitize files.txt
        file_path = os.path.join(support_dir_full, 'files.txt')
        if os.path.exists(file_path) and config.sanitize_support_files:
            sanitize_file(file_path)

        # for each file in logs, sanitize
        if config.sanitize_support_files:
            for filename in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, filename)
                if os.path.exists(file_path):
                    sanitize_file(file_path)

            # for each file in logs, sanitize
            for filename in os.listdir(puml_dir):
                file_path = os.path.join(puml_dir, filename)
                if os.path.exists(file_path):
                    sanitize_file(file_path)

        # sanitize db
        file_path = os.path.join(support_dir_full, get_pf_db())
        if os.path.exists(file_path) and config.sanitize_support_files:
            sanitize_db(file_path)

        # create symmetric key
        session_key = Fernet.generate_key()

        # zip support folder
        debug(f"Zipping {support_dir_full} ...")
        zip_file_path = shutil.make_archive(support_dir_full, 'zip', support_dir_full)

        # delete support folder
        if not config.keep_temporary_support_files:
            delete_all(support_dir_full)

        # encrypt support.zip with session key
        symmetric_cipher = Fernet(session_key)
        with open(zip_file_path, 'rb') as f:
            encrypted_data = symmetric_cipher.encrypt(f.read())
        encrypted_zip_file_path = zip_file_path + '.pf'
        with open(encrypted_zip_file_path, 'wb') as f:
            f.write(encrypted_data)

        # delete unencrypted support.zip
        os.remove(zip_file_path)

        # encrypt session key with RSA public key
        encrypted_session_key_path = os.path.join(tmp_dir_full, 'pf.dat')
        encrypt_sk(session_key=session_key, output_file_name=encrypted_session_key_path, public_key=None)

        # zip encrypted support.zip and session key
        final_zip_file_path = zip_file_path
        with zipfile.ZipFile(final_zip_file_path, 'w') as final_zip:
            final_zip.write(encrypted_zip_file_path, arcname='support.pf')
            final_zip.write(encrypted_session_key_path, arcname='pf.dat')

        # delete encrypted support.zip and session key
        os.remove(encrypted_zip_file_path)
        os.remove(encrypted_session_key_path)

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while creating support.zip.")
        traceback.print_exc()


# ============================================================================
#                               Function sanitize_filename
# ============================================================================
def sanitize_filename(filepath, split=False):
    try:
        # Check if the file exists
        if not os.path.exists(filepath):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: File {filepath} does not exist.")
            if split:
                return None, None
            else:
                return None

        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        suspect_chars = '<>:"|?*()&;'

        # Check if filename needs sanitization
        needs_sanitization = any(char in filename for char in suspect_chars)

        if not needs_sanitization:
            if split:
                return directory, filename
            else:
                return filepath

        # Create sanitized filename by replacing suspect chars with underscore
        sanitized_filename = filename
        for char in suspect_chars:
            sanitized_filename = sanitized_filename.replace(char, '_')

        # Create temp file in system temp directory
        temp_dir = tempfile.gettempdir()
        temp_filepath = os.path.join(temp_dir, sanitized_filename)

        # Copy the original file to temp location with sanitized name
        # Use copy2 to preserve timestamps and metadata
        shutil.copy2(filepath, temp_filepath)

        if split:
            return temp_dir, sanitized_filename
        else:
            return temp_filepath

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while sanitizing filepath {filepath}")
        traceback.print_exc()
        return None, None


# ============================================================================
#                               Function sanitize_file
# ============================================================================
def sanitize_file(filename):
    try:
        debug(f"Sanitizing {filename} ...")
        with contextlib.suppress(Exception):
            with open(filename, "rt", encoding='ISO-8859-1', errors="replace") as fin:
                data = fin.read()
            data = re.sub(r'(\\Users\\+)(?:.*?)(\\+)', r'\1REDACTED\2', data, flags=re.IGNORECASE)
            data = re.sub(r'(\/Users\/+)(?:.*?)(\/+)', r'\1REDACTED\2', data, flags=re.IGNORECASE)
            data = re.sub(r'(\"device\":\s+)(\"\w+?\")', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(device\sid:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(device:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(device\s+\')(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(\(usb\)\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(superkey:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(./boot_patch.sh\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(Rebooting device\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(Flashing device\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(waiting for\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(Serial\sNumber\.+\:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(fastboot(.exe)?\"? -s\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(adb(.exe)?\"? -s\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
            data = re.sub(r'(\S\  \((?:adb|f\.b|rec|sid)\)   )(.+?)(\s+.*)', r'\1REDACTED\3', data, flags=re.IGNORECASE)
            data = re.sub(r'(?<=List of devices attached\n)((?:\S+\s+device\n)+)', lambda m: re.sub(r'(\S+)(\s+device)', r'REDACTED\2', m.group(0)), data, flags=re.MULTILINE)
            data = re.sub(r'(?<=debug: fastboot devices:\n)((?:\S+\s+fastboot\n)+)', lambda m: re.sub(r'(\S+)(\s+fastboot)', r'REDACTED\2', m.group(0)), data, flags=re.MULTILINE)
            with open(filename, "wt", encoding='ISO-8859-1', errors="replace") as fin:
                fin.write(data)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while sanitizing {filename}")
        traceback.print_exc()


# ============================================================================
#                               Function sanitize_db
# ============================================================================
def sanitize_db(filename):
    try:
        debug(f"Sanitizing {filename} ...")
        con = sl.connect(filename)
        con.execute("PRAGMA secure_delete = ON;")
        cursor = con.cursor()
        with con:
            data = con.execute("SELECT id, file_path FROM BOOT")
            for row in data:
                id = row[0]
                file_path = row[1]
                if sys.platform == "win32":
                    file_path_sanitized = re.sub(r'(\\Users\\+)(?:.*?)(\\+)', r'\1REDACTED\2', file_path, flags=re.IGNORECASE)
                else:
                    file_path_sanitized = re.sub(r'(\/Users\/+)(?:.*?)(\/+)', r'\1REDACTED\2', file_path, flags=re.IGNORECASE)
                cursor.execute("Update BOOT set file_path = ? where id = ?", (file_path_sanitized, id,))
                con.commit()
        with con:
            data = con.execute("SELECT id, file_path FROM PACKAGE")
            for row in data:
                id = row[0]
                file_path = row[1]
                if sys.platform == "win32":
                    file_path_sanitized = re.sub(r'(\\Users\\+)(?:.*?)(\\+)', r'\1REDACTED\2', file_path, flags=re.IGNORECASE)
                else:
                    file_path_sanitized = re.sub(r'(\/Users\/+)(?:.*?)(\/+)', r'\1REDACTED\2', file_path, flags=re.IGNORECASE)
                cursor.execute("Update PACKAGE set file_path = ? where id = ?", (file_path_sanitized, id,))
                con.commit()
        # Wipe the Write-Ahead log data
        con.execute("VACUUM;")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while sanitizing db {filename}.")
        traceback.print_exc()


# ============================================================================
#                               Function encrypt_file
# ============================================================================
def encrypt_sk(session_key, output_file_name, public_key=None):
    try:
        if public_key is None:
            public_key = serialization.load_pem_public_key(
                b"""-----BEGIN PUBLIC KEY-----
                MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAj/OLsTAnmLVDR0tpTCEF
                TrEi0touCGRCRPmScmZpyY0+b+Iv52gFJMmYaqC+HUbd3F9tdLWFwWmRFSYXFXaV
                STb1F8DbG+dqWMTG6HtilVl8yfX/ihftlfl/Zj6mtMj3BmMNe475GohwZTdfXXkF
                hPRxrx2WIVlzrZAozVdfLCj6o7iCq27Wbsuis7x5LtlM5ojraK7lYPMlCXigR+2N
                VDsaAzCaYZAxn2YXNrtLRcmwsRxEH1YnJgQiH7CqJz8w10ArkOxvZ/vbLq3Yrokd
                JPcPqPWn9Zu0Rb9q3U42ghuO7f5Laqt0ANf4nHaMK+Q3sWZvf/rVpOIlrLVCaa/H
                swIDAQAB
                -----END PUBLIC KEY-----""",
                backend=default_backend()
            )

        encrypted_session_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        with open(output_file_name, 'wb') as f:
            f.write(encrypted_session_key)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an in function encrypt_sk")
        traceback.print_exc()


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
            print(f"Failed to delete {file_path}. Reason: {e}")
            traceback.print_exc()


# ============================================================================
#                               Function get_size_from_url
# ============================================================================
def get_size_from_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if 'Content-Length' in response.headers:
            file_size = int(response.headers['Content-Length'])
            debug(f"Size of {url} is {file_size} bytes")
            return file_size
        else:
            debug("Could not determine file size from headers")
            return None
    except Exception as e:
        print(f"Error getting file size: {e}")
        return None


# ============================================================================
#                               Function check_module_update
# ============================================================================
def check_module_update(url):
    try:
        skiplist = get_skip_urls_file_path()
        if os.path.exists(skiplist):
            with open(skiplist, 'r', encoding='ISO-8859-1', errors="replace") as f:
                skiplist_urls = f.read().splitlines()
                if url in skiplist_urls:
                    print(f"\nℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} Skipping update check for {url}")
                    return None
        payload={}
        headers = {
            'Content-Type': "application/json"
        }
        response = request_with_fallback(method='GET', url=url, headers=headers, data=payload)
        if response != 'ERROR':
            if response.status_code == 404:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Module update not found for URL: {url}")
                return None
            with contextlib.suppress(Exception):
                data = response.json()
                mu = ModuleUpdate(url)
                setattr(mu, 'version', data['version'])
                setattr(mu, 'versionCode', data['versionCode'])
                setattr(mu, 'zipUrl', data['zipUrl'])
                setattr(mu, 'changelog', data['changelog'])
                headers = {}
                response = request_with_fallback(method='GET', url=mu.changelog, headers=headers, data=payload)
                setattr(mu, 'changelog', response.text)
                return mu
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Module update URL has issues, inform the module author: {url}")
            dlg = wx.MessageDialog(None, _("Module update URL has issues, inform the module author: %s\nDo you want to skip checking updates for this module?") % url, _("Error"), wx.YES_NO | wx.ICON_ERROR)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                # add url to a list of failed urls
                with open(skiplist, 'a') as f:
                    f.write(url + '\n')
                print(f"\nℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} Added {url} to update check skip list.")
                return None
            else:
                return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during getUpdateDetails url: {url} processing")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function get_free_space
# ============================================================================
def get_free_space(path=''):
    try:
        path_to_check = path or tempfile.gettempdir()
        path_to_check = os.path.realpath(path_to_check)

        total, used, free = shutil.disk_usage(path_to_check)

        debug(f"Path: {path_to_check} - Total: {round(total / (1024 ** 3), 2)} GB, Used: {round(used / (1024 ** 3), 2)} GB, Free: {round(free / (1024 ** 3), 2)} GB")

        return int(round(free / (1024 ** 3)))
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting free space.")
        traceback.print_exc()


# ============================================================================
#                               Function get_free_memory
# ============================================================================
def get_free_memory():
    memory = psutil.virtual_memory()
    free_memory = memory.available
    total_memory = memory.total
    return free_memory, total_memory


# ============================================================================
#                               Function format_memory_size
# ============================================================================
def format_memory_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024


# ============================================================================
#                               Function parse_device_list_html
# ============================================================================
def parse_device_list_html(ul_content):
    """
    Parse HTML ul content of device names and return both model_list and product_list.

    Args:
        ul_content (str or Tag): HTML ul element with device names, can be a string or BeautifulSoup Tag

    Returns:
        tuple: (model_list, product_list)
    """

    device_data = get_android_devices()
    # Create reverse lookup from display name to codename
    device_to_product = {}
    for product, info in device_data.items():
        device_to_product[info['device'].lower()] = product

    li_items = []

    # Check if ul_content is a BeautifulSoup Tag
    if hasattr(ul_content, 'find_all'):
        # It's a BeautifulSoup Tag, use find_all to extract list items
        li_tags = ul_content.find_all('li')
        li_items = [li.get_text() for li in li_tags]
    else:
        # It's a string, use regex to extract list items
        li_pattern = r'<li>(.*?)</li>'
        li_items = re.findall(li_pattern, ul_content)

    model_list = []
    product_list = []

    for item in li_items:
        # Handle different list item formats
        parts = []

        # Example: "Pixel 9, 9 Pro, 9 Pro XL, and 9 Pro Fold" should be split into 4 devices
        if ',' in item and ('and' in item or '&' in item):
            # Split by commas first
            comma_parts = [p.strip() for p in item.split(',')]
            # Last part might contain "and" or "&"
            last_part = comma_parts.pop()
            if ' and ' in last_part:
                and_parts = last_part.split(' and ')
            elif 'and ' in last_part:
                and_parts = last_part.split('and ')
            elif ' & ' in last_part:
                and_parts = last_part.split(' & ')
            elif '& ' in last_part:
                and_parts = last_part.split('& ')
            else:
                and_parts = [last_part]
            # Remove empty parts from and_parts
            and_parts = [part for part in and_parts if part.strip()]
            # Combine comma parts with and parts
            parts = comma_parts + and_parts

        # Example: "Pixel 6 and 6 Pro" - no commas but has "and"
        elif ' and ' in item or ' & ' in item:
            if ' and ' in item:
                and_parts = item.split(' and ')
            else:
                and_parts = item.split(' & ')

            # Remove empty parts from and_parts
            and_parts = [part for part in and_parts if part.strip()]
            parts = and_parts

        # Simple case example "Pixel 6a" and nothing else.
        else:
            parts = [item]

        # Process all parts to add to model and product lists
        for part in parts:
            part = part.strip()

            # Handle missing 'Pixel' like "9 Pro" -> "Pixel 9 Pro"
            if not part.lower().startswith("pixel"):
                # Find the prefix from the last full device name
                for i in range(len(model_list) - 1, -1, -1):
                    prev_model = model_list[i]
                    if prev_model.lower().startswith("pixel"):
                        prefix = prev_model.split(' ')[0]  # Example: "Pixel"
                        part = f"{prefix} {part}"
                        break

            # Add to model list
            model_list.append(part)

            # Find matching product name
            device_name = part.lower()
            product = None

            # Try exact match
            if device_name in device_to_product:
                product = device_to_product[device_name]
            else:
                # Try partial match for cases like "Pixel 6" -> "Google Pixel 6"
                for display_name, prod_name in device_to_product.items():
                    if device_name in display_name or display_name.endswith(device_name):
                        product = prod_name
                        break

            if product:
                product_list.append(f"{product}_beta")
            else:
                # Fallback for unrecognized devices as UNKNOWN
                print(f"\n⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING! Could not find product name for {part}")
                product_list.append(f"UNKNOWN")

    return model_list, product_list


# ============================================================================
#                 Function get_gsi_data
# ============================================================================
def get_gsi_data(force_version=None):
    try:
        error = False
        # URLs
        gsi_url = "https://developer.android.com/topic/generic-system-image/releases"
        debug(f"Fetching GSI data from {gsi_url} ...")

        # Fetch GSI HTML
        response = request_with_fallback('GET', gsi_url)
        if response == 'ERROR' or response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch GSI HTML")
            return None, None
        gsi_html = response.text

        # Parse GSI HTML
        soup = BeautifulSoup(gsi_html, 'html.parser')

        id_to_find = f"android-gsi-{force_version}"
        # get the position of id_to_find
        pos = gsi_html.find(id_to_find)
        if pos == -1:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: GSI version {force_version} not found in HTML")
            return None, None
        # Move to that position
        gsi_html = gsi_html[pos:]
        # Parse the HTML again with the new gsi_html
        soup = BeautifulSoup(gsi_html, 'html.parser')
        # find the first <ul> tag in the new soup
        ul_content = soup.find('ul')
        # use it to extract model_list and product_list
        model_list, product_list = parse_device_list_html(ul_content)

        # Find the anchor tag with the text 'corresponding Google Pixel builds'
        release = soup.find('a', string=lambda x: x and 'corresponding Google Pixel builds' in x)
        if not release:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Release version not found")
            return None, None

        href = release['href']
        release_version = href.split('/')[3]
        if release_version != str(force_version):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Fetched Release version {release_version} does not match requested version {force_version}")

        # Find the build ID inside <code> blocks
        build_id_text = None
        security_patch_level_text = None
        google_play_services = None
        for code in soup.find_all('code'):
            code_text = code.get_text()
            if 'Build:' in code_text:
                build_id_text = code_text
                if 'Security patch level:' in code_text:
                    security_patch_level_text = code_text
                if 'Google Play Services:' in code_text:
                    google_play_services = code_text.split('Google Play Services: ')[1].split('\n')[0]
                break
        if build_id_text:
            build_id = build_id_text.split('Build: ')[1].split()[0]
            # Extract date portion from the build ID (typically in format like BP1A.250405.005.C1)
            # The date part is in the middle segment (YYMMDD format, example: 250405 for April 5, 2025)
            date_match = re.search(r'\.(\d{6})\.', build_id)
            if date_match:
                build_date_str = date_match.group(1)
                build_year = 2000 + int(build_date_str[:2])
                build_month = int(build_date_str[2:4])
                build_day = int(build_date_str[4:6])
                try:
                    build_date = datetime(build_year, build_month, build_day)
                except ValueError:
                    # Invalid date in build ID
                    print(f"\n⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Invalid date in build ID: {build_date_str}")
                    build_date = None
            else:
                build_date = None
                print(f"\n⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Could not extract date from build ID: {build_id}")
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Build ID not found")
            return None, None

        if security_patch_level_text:
            security_patch_level_date = security_patch_level_text.split('Security patch level: ')[1].split('\n')[0]
            release_date = security_patch_level_text.split('Date: ')[1].split('\n')[0]
            beta_release_date = datetime.strptime(release_date, '%B %d, %Y').strftime('%Y-%m-%d')
            # verify if the beta_release_date falls correctly within the build date with a 30-day margin
            if build_date:
                published_date = datetime.strptime(beta_release_date, '%Y-%m-%d')
                delta_days = abs((published_date - build_date).days)
                if delta_days > 60:
                    print(f"\n⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Large discrepancy between published GSI release date ({release_date}) and build ID date ({build_date.strftime('%Y-%m-%d')}). Difference: {delta_days} days")
                    error = True
            beta_expiry = datetime.strptime(beta_release_date, '%Y-%m-%d') + timedelta(weeks=6)
            beta_expiry_date = beta_expiry.strftime('%Y-%m-%d')
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Security patch level date not found")
            return None, None

        # Find the incremental value
        incremental = None
        match = re.search(rf'{build_id}-(\d+)-', gsi_html)
        if match:
            incremental = match.group(1)
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Incremental not found")
            return None, None

        devices = []
        table = soup.find('table')
        if table:
            # Skip the header row
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                # Ensure we have at least 2 columns
                if len(cols) >= 2:
                    device = cols[0].text.strip()
                    button = cols[1].find('button')
                    if button and 'data-category' in button.attrs:
                        category = button['data-category']
                        zip_filename = button.text.strip()
                        hashcode = cols[1].find('code')
                        if hashcode:
                            hashcode = hashcode.text.strip()
                        else:
                            hashcode = ""
                        devices.append({
                            'device': device,
                            'category': category,
                            'zip_filename': zip_filename,
                            'hash': hashcode,
                            'url': None  # Placeholder for URL
                        })

        # Find all hrefs and match with zip_filename
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            for device in devices:
                if device['zip_filename'] in href:
                    device['url'] = href
                    break

        emulator_support = ""
        security_patch = ""
        ret_obj = BetaData(release_date, build_id, emulator_support, security_patch_level_date, google_play_services, beta_expiry_date, incremental, security_patch, devices)
        # append the model_list and product_list to ret_obj
        ret_obj.model_list = model_list
        ret_obj.product_list = product_list
        # append the release['href] to ret_obj
        ret_obj.release_href = release['href']
        return ret_obj, error

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting GSI data.")
        traceback.print_exc()
        return None, None


# ============================================================================
#                 Function get_beta_links
# ============================================================================
def get_beta_links():
    try:
        url_base = "https://developer.android.com/about/versions"

        # Get the latest Android version
        latest_version, latest_version_url = get_latest_android_version(None)
        ota_data = None
        factory_data = None
        if latest_version == -1:
            return None, None, None, None


        # Fetch OTA HTML
        ota_url = f"{url_base}/{latest_version}/download-ota"
        if latest_version_url:
            ota_url = f"{latest_version_url}/download-ota"
        ota_data, ota_error = get_beta_data(ota_url)

        # Fetch Factory HTML
        factory_url = f"{url_base}/{latest_version}/download"
        if latest_version_url:
            factory_url = f"{latest_version_url}/download"
        factory_data, factory_error = get_beta_data(factory_url)

        return ota_data, factory_data, ota_error, factory_error
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting beta links.")
        traceback.print_exc()
        return None, None, None, None


# ============================================================================
#                 Function get_telegram_factory_images
# ============================================================================
def get_telegram_factory_images(max_pages=3):
    try:
        base_url = "https://t.me/s/pixelfactoryimagestracker"
        config_path = get_config_path()
        telegram_factory_images_file = os.path.join(config_path, 'telegram_factory_images.json')

        # Load existing cached data
        cached_images = []
        cached_message_ids = set()
        if os.path.exists(telegram_factory_images_file):
            try:
                with open(telegram_factory_images_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    cached_images = cached_data
                    debug(f"Loaded {len(cached_images)} cached factory images")
                    for image in cached_images:
                        # Create a unique identifier from device, build_id, and url
                        unique_id = f"{image.get('device', '')}|{image.get('build_id', '')}|{image.get('url', '')}"
                        cached_message_ids.add(unique_id)
            except (json.JSONDecodeError, KeyError) as e:
                debug(f"Could not load cached data: {e}, starting fresh")
                cached_images = []
                cached_message_ids = set()

        factory_images = []
        all_message_ids = set()
        found_cached_content = False
        new_images_count = 0

        # Start with the first page
        current_url = base_url
        page_count = 0

        while page_count < max_pages:
            debug(f"Fetching page {page_count + 1} from Telegram channel...")

            response = requests.get(current_url)
            if response.status_code != 200:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch URL: {current_url}")
                break

            telegram_html = response.text
            soup = BeautifulSoup(telegram_html, 'html.parser')

            # Find all message containers
            message_containers = soup.find_all('div', class_='tgme_widget_message')
            if not message_containers:
                debug(f"No more messages found on page {page_count + 1}")
                break

            page_has_new_messages = False
            for container in message_containers:
                # Get message ID to avoid duplicates
                message_id = container.get('data-post')
                if message_id in all_message_ids:
                    continue

                all_message_ids.add(message_id)

                # Find the message text within this container
                message_text_div = container.find('div', class_='tgme_widget_message_text')
                if not message_text_div:
                    continue

                # Check if we've reached content that's already in our cache
                # Create unique identifier for this message
                current_unique_id = None
                if "New Pixel Factory Image Detected" in message_text_div.get_text():
                    # Extract basic info to create unique identifier
                    device_match = re.search(r'<b>Device:<\/b>\s*([^<]+)<br', str(message_text_div))
                    build_id_match = re.search(r'<b>Build ID:<\/b>\s*<code>([^<]+)<\/code>', str(message_text_div))
                    link = message_text_div.find('a', href=True)

                    if device_match and link:
                        device = device_match.group(1).strip()
                        build_id = build_id_match.group(1).strip() if build_id_match else ''
                        download_url = link['href']
                        current_unique_id = f"{device}|{build_id}|{download_url}"

                        # Check if this content is already cached, but don't break yet
                        # Continue processing the rest of the page since newest entries are at the bottom
                        if current_unique_id in cached_message_ids:
                            found_cached_content = True
                            debug(f"Found cached content for {device}, but continuing to process rest of page")
                            continue

                page_has_new_messages = True

                # Check if this is a factory image announcement
                if "New Pixel Factory Image Detected" in message_text_div.get_text():
                    device = None
                    image_type = None
                    build_id = None
                    download_url = None

                    # Extract device info
                    device_match = re.search(r'<b>Device:<\/b>\s*([^<]+)<br', str(message_text_div))
                    if device_match:
                        device = device_match.group(1).strip()

                    # Extract type info
                    type_match = re.search(r'<b>Type:<\/b>\s*([^<]+)<br', str(message_text_div))
                    if type_match:
                        image_type = type_match.group(1).strip()

                    # Extract build ID
                    build_id_match = re.search(r'<b>Build ID:<\/b>\s*<code>([^<]+)<\/code>', str(message_text_div))
                    if build_id_match:
                        build_id = build_id_match.group(1).strip()

                    # Extract download URL
                    link = message_text_div.find('a', href=True)
                    if link:
                        download_url = link['href']

                    # Add to the array if we have all the required fields
                    if device and download_url:
                        factory_images.append({
                            "device": device,
                            "type": image_type,
                            "build_id": build_id,
                            "url": download_url,
                            "message_id": message_id
                        })
                        new_images_count += 1

            # If we found cached content or no new messages, break
            if not page_has_new_messages:
                debug(f"No new messages found on page {page_count + 1}, stopping pagination")
                break
            elif found_cached_content and new_images_count == 0:
                debug(f"Stopped fetching at page {page_count + 1} due to reaching only cached content")
                break

            # Look for "Load more" link or pagination
            next_page_url = None

            # Method 1: Look for "before" parameter in existing links
            before_links = soup.find_all('a', href=True)
            for link in before_links:
                href = link['href']
                if 'before=' in href and 'pixelfactoryimagestracker' in href:
                    next_page_url = href
                    if not next_page_url.startswith('http'):
                        next_page_url = f"https://t.me{next_page_url}"
                    break

            # Method 2: If no pagination link is found, try to construct one using the oldest message ID
            if not next_page_url and message_containers:
                oldest_message = message_containers[-1]
                oldest_message_id = oldest_message.get('data-post')
                if oldest_message_id:
                    # Extract just the message number part
                    message_num = oldest_message_id.split('/')[-1] if '/' in oldest_message_id else oldest_message_id
                    next_page_url = f"{base_url}?before={message_num}"

            if not next_page_url:
                debug(f"No pagination link found on page {page_count + 1}, stopping")
                break

            current_url = next_page_url
            page_count += 1

            # Add a small delay to be respectful to the server
            time.sleep(1)

        # Merge new images with cached images
        # New images go first (they're newer), then cached images
        combined_images = factory_images + cached_images

        # Remove duplicates based on unique identifier while preserving order
        seen_unique_ids = set()
        deduplicated_images = []
        for image in combined_images:
            # Create unique identifier for deduplication
            unique_id = f"{image.get('device', '')}|{image.get('build_id', '')}|{image.get('url', '')}"
            if unique_id not in seen_unique_ids:
                seen_unique_ids.add(unique_id)
                deduplicated_images.append(image)

        # Sort all images by message_id in descending order (newest first)
        # Handle both regular message IDs and entries without message_id
        def sort_key(image):
            msg_id = image.get('message_id')
            if not msg_id:
                # For entries without message_id (cached entries), use a very low number
                return 0
            try:
                return int(msg_id.split('/')[-1])
            except (ValueError, AttributeError):
                return 0

        deduplicated_images.sort(key=sort_key, reverse=True)

        # Remove message_id from final output as it's just for sorting
        for image in deduplicated_images:
            image.pop('message_id', None)

        # Save merged telegram factory_images to file
        if deduplicated_images:
            with open(telegram_factory_images_file, 'w', encoding='utf-8') as f:
                json.dump(deduplicated_images, f, indent=4, ensure_ascii=False)

            if new_images_count > 0:
                debug(f"Found {new_images_count} new factory images, merged with {len(cached_images)} cached images")
                debug(f"Total {len(deduplicated_images)} factory images saved to cache")
            else:
                debug(f"No new images found, using {len(cached_images)} cached factory images")
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} No factory images found in Telegram channel.")

        return deduplicated_images
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting Telegram factory images.")
        traceback.print_exc()
        return -1


# ============================================================================
#                 Function get_api_level
# ============================================================================
def get_api_level(android_version):
    try:
        version_data = get_android_versions()
        # Create reverse lookup from API version to Android version
        version_to_api = {}
        for api_version, info in version_data.items():
            version_to_api[info['Version'].lower()] = api_version
        api_level = version_to_api[str(android_version)]
        return int(api_level)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get API level for Android version {android_version}")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function get_beta_factory_object
# ============================================================================
def get_beta_factory_object(product, canary = True, active = True, latest = True):
    try:
        debug(f"Retrieving canary data for product: {product}")

        if 'beta' not in product:
            product += '_beta'

        page_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        response = requests.get("https://flash.android.com", headers=page_headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        body_tag = soup.body
        if body_tag is None:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not locate body tag on flash.android.com")
            return None

        raw_client_config = body_tag.get("data-client-config", "")
        if not raw_client_config:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Missing data-client-config attribute on flash.android.com body")
            return None

        client_config = html.unescape(raw_client_config)
        key_match = re.search(r"\"(AIza[0-9A-Za-z\-_]+)\"", client_config)
        if not key_match:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to extract key from flash.android.com")
            return None

        api_key = key_match.group(1)
        api_url = f"https://content-flashstation-pa.googleapis.com/v1/builds?key={api_key}&product={product}"
        debug(f"Querying Flashstation API: {api_url}")

        api_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://flash.android.com",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        api_response = requests.get(api_url, headers=api_headers, timeout=30)
        api_response.raise_for_status()
        data = api_response.json()

        if not latest:
            return data

        builds = data.get("flashstationBuild", [])
        debug(f"Received {len(builds)} builds for {product}")

        filtered_builds = []
        for build in builds:
            preview = build.get("previewMetadata") or {}
            canary_flag = preview.get("canary")
            active_flag = preview.get("active")

            if canary is not None and bool(canary_flag) != bool(canary):
                continue
            if active is not None and bool(active_flag) != bool(active):
                continue

            filtered_builds.append(build)

        if not filtered_builds:
            debug("No builds matched the requested criteria")
            return None

        def build_sort_key(entry):
            build_id = entry.get("buildId", "0")
            try:
                return int(build_id)
            except (TypeError, ValueError):
                return 0

        filtered_builds.sort(key=build_sort_key, reverse=True)

        latest_build = filtered_builds[0].copy()
        latest_build.pop("licenseText", None)
        return latest_build

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to retrieve canary URL for {product}")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function find_canary_url
# ============================================================================
def find_canary_url(api_level=36):
    try:
        for i in range(9, 0, -1):
            url = f"https://dl.google.com/android/repository/sys-img/google_apis/arm64-v8a-{api_level}.0-CANARY_r{i:02d}.zip"
            #debug(f"Checking: {url}")
            response = requests.head(url, allow_redirects=True, timeout=5)
            if response.status_code == 200:
                return url
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in find_canary_url function")
        traceback.print_exc()
    return None


# ============================================================================
#                               Function get_canary_miner
# ============================================================================
def get_canary_miner(device_model='random', default_selection=None, miner_url=None):
    if not miner_url:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: No miner URL provided")
        return -1
    # get file list from miner_url
    try:
        canary_device = None
        canary_url = None
        response = requests.get(miner_url)
        if response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch Canary PIFs page")
            return -1
        page_html = response.text
        file_list = []
        directory = path.basename(urlparse(miner_url).path) or "devices"
        file_pattern = rf'{{"name":"([^"]+)","path":"({re.escape(directory)}/[^"]+)","contentType":"file"}}'
        matches = re.findall(file_pattern, page_html)
        for match in matches:
            file_name = match[0]
            if '.pif.prop' not in file_name:
                continue
            file_name = file_name.replace('.pif.prop', '')
            file_path = match[1]
            file_path = f"https://raw.githubusercontent.com/Vagelis1608/get_the_canary_miner/refs/heads/main/{file_path}"
            file_list.append({"device": file_name, "path": file_path})
            if device_model != 'random' and device_model != '_select_' and device_model in file_name:
                canary_url = file_path
                canary_device = device_model

        debug(f"Found {len(file_list)} Canary PIF files")
        if device_model == 'random':
            selected_file = random.choice(file_list)
            canary_url = selected_file['path']
            canary_device = selected_file['device']
        elif device_model == '_select_':
            if len(file_list) == 1:
                only_file = file_list[0]
                debug(f"Only one Canary PIF found, auto-selecting {only_file['device']}")
                canary_url = only_file['path']
                canary_device = only_file['device']
            else:
                canary_url, canary_device = select_pif_device(file_list, default_selection, device_type="Canary")
            if not canary_url:
                return "Selection cancelled."
        elif not canary_url:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find Canary PIF for device model: {device_model}")
            return -1

        response = requests.get(canary_url)
        if response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch Canary PIF file for {canary_device}")
            return -1
        pif_content = response.text
        return pif_content

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting Canary Miner data.")
        traceback.print_exc()
        return -1


# ============================================================================
#                 Function select_pif_device
# ============================================================================
def select_pif_device(devices_data, default_selection=None, device_type=""):
    try:
        from device_selector import show_device_selector
        selected_device = show_device_selector(
            parent=None,
            devices=devices_data,
            title=f"Select {device_type} Device",
            message=f"Select a {device_type} device:",
            select_device=default_selection
        )
        if selected_device:
            pif_url = selected_device['path']
            pif_device = selected_device['device']
            print(f"  Selected: {pif_device}")
            return pif_url, pif_device
        else:
            print("Selection cancelled.")
            return None, None
    except ImportError:
        selected_url = None


# ============================================================================
#                 Function get_beta_pif
# ============================================================================
def get_beta_pif(device_model='random', force_version=None):
    # Get the latest Android version
    latest_version, latest_version_url = get_latest_android_version(force_version)
    print(f"Selected Version:         {latest_version}")
    if latest_version == -1:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get the latest Android version")
        return -1

    canary_data = False
    beta_type = "Beta"
    if force_version and str(force_version).startswith('CANARY'):
        # moved this logic to pif manager
        # the code should never get here
        pass
    else:
        # set the url to the latest version
        ota_url = f"https://developer.android.com/about/versions/{latest_version}/download-ota"
        factory_url = f"https://developer.android.com/about/versions/{latest_version}/download"
        if not force_version and latest_version_url:
            ota_url = f"{latest_version_url}/download-ota"
            factory_url = f"{latest_version_url}/download"

        # Fetch OTA HTML
        ota_data, ota_error = get_beta_data(ota_url)
        if not ota_data:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or Developer Preview OTA data for Android {latest_version}")
        # print(ota_data.__dict__)

        # Fetch Factory HTML
        factory_data, factory_error = get_beta_data(factory_url)
        if not factory_data:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or Developer Preview Factory data for Android {latest_version}")
        # print(factory_data.__dict__)

        # Fetch GSI HTML
        gsi_data, gsi_error = get_gsi_data(force_version=force_version or latest_version)
        if not gsi_data:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or Developer Preview GSI data for Android {latest_version}")
        # print(gsi_data.__dict__)

        if not ota_data and not factory_data and not gsi_data and not canary_data:
            return -1
        if not ota_data and not factory_data and not canary_data:
            print(f"Getting beta print from GSI data, version {latest_version} ...")

        ota_date_object = None
        factory_date_object = None
        gsi_date_object = None
        if ota_data:
            ota_date = ota_data.__dict__['release_date']
            ota_date_object = datetime.strptime(ota_date, "%B %d, %Y")
            if ota_error:
                print(f"Beta OTA Date:            {ota_date} (❌ Problems with download links or hashes)")
            else:
                print(f"Beta OTA Date:            {ota_date}")
        else:
            print(f"Beta OTA:                 Unavailable")

        if factory_data:
            factory_date = factory_data.__dict__['release_date']
            factory_date_object = datetime.strptime(factory_date, "%B %d, %Y")
            if factory_error:
                print(f"Beta Factory Date:        {factory_date} (❌ Problems with download links or hashes)")
            else:
                print(f"Beta Factory Date:        {factory_date}")
        else:
            print(f"Beta Factory:             Unavailable")

        if gsi_data:
            gsi_date = gsi_data.__dict__['release_date']
            gsi_date_object = datetime.strptime(gsi_date, "%B %d, %Y")
            if gsi_error:
                print(f"Beta GSI Date:            {gsi_date} (❌ Possible problems with GSI date)")
            else:
                print(f"Beta GSI Date:            {gsi_date}")
        else:
            print(f"Beta GSI:                 Unavailable")

        # Determine the latest date(s)
        newest_data = []
        dates = []
        if ota_date_object and not ota_error:
            dates.append((ota_date_object, 'ota'))
        if factory_date_object and not factory_error:
            dates.append((factory_date_object, 'factory'))
        if gsi_date_object and not gsi_error:
            dates.append((gsi_date_object, 'gsi'))
        if ota_date_object and ota_error:
            dates.append((ota_date_object, 'ota_error'))
        if factory_date_object and factory_error:
            dates.append((factory_date_object, 'factory_error'))
        if gsi_date_object and gsi_error:
            dates.append((gsi_date_object, 'gsi_error'))

        # Sort dates in descending order
        dates.sort(key=lambda x: (x[0], {'ota': 0, 'factory': 1, 'gsi': 2, 'ota_error': 3, 'factory_error': 4, 'gsi_error': 5}[x[1]]), reverse=True)

        if not dates:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to determine the latest date")
            return -1

        latest_date = dates[0][0]

        # Group dates by their value
        date_groups = {}
        for date, source in dates:
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(source)

        # Process groups in descending date order
        for date in sorted(date_groups.keys(), reverse=True):
            # Sort sources within each date group to maintain ota, factory, gsi order
            sources = sorted(date_groups[date], key=lambda x: {'ota': 0, 'factory': 1, 'gsi': 2, 'ota_error': 3, 'factory_error': 4, 'gsi_error': 5}[x])
            newest_data.extend(sources)

        def get_model_and_prod_list(data):
            for device in data.__dict__['devices']:
                model_list.append(device['device'])
                zip_filename = device['zip_filename']
                product = zip_filename.split('-')[0]
                product_list.append(product)
            return model_list, product_list

        # Show a dialog to list the dates and their sources
        # recommed to select the first one (newest)
        # let the user have the option to select another source if they want

        # setup the dialog options
        title = f"Select Beta print source"
        message = ""
        size = (580, 360)
        button_texts = [_('Automatic'), _('OTA Image'), _('Factory Image'), _('GSI Image'), _("Cancel")]
        default_button = 1

        message = '''
# Available Beta sources<br/>
- **Automatic:** PixelFlasher automatically chooses the most recent option.
- **OTA:** Sourced from Pixel beta OTA images.
- **Factory:** Sourced from Pixel beta factory images.
- **GSI** Sourced from Pixel GSI images.
'''

        # Additional message details
        message += f"<pre>"
        for item in dates:
            the_date = item[0]
            source = item[1]
            source = source.replace("_error", "")
            # message += f"{source}:  {the_date}\n"
            message += f"{source:<10}: {the_date.strftime('%B %d, %Y')}\n"
        message += f"</pre>"

        clean_message = message.replace("<br/>", "").replace("</pre>", "").replace("<pre>", "")
        print(f"\n*** Dialog ***\n{clean_message}\n______________\n")
        puml(":Dialog;\n", True)
        puml(f"note right\n{clean_message}\nend note\n")
        from message_box_ex import MessageBoxEx
        dlg = MessageBoxEx(
            parent=None,
            title=title,
            message=message,
            button_texts=button_texts,
            default_button=default_button,
            disable_buttons=None,
            is_md=True,
            size=size,
            checkbox_labels=None,
            checkbox_initial_values=None,
            disable_checkboxes=None,
            vertical_checkboxes=False,
            checkbox_labels2=None,
            checkbox_initial_values2=None,
            disable_checkboxes2=None,
            radio_labels=None,
            radio_initial_value=0,
            disable_radios=None,
            vertical_radios=False
        )
        dlg.CentreOnParent(wx.BOTH)
        result = dlg.ShowModal()

        dlg.Destroy()
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {button_texts[result -1]}")

        if result == 1:
            # User selected Automatic
            pass # keep newest_data intact
        elif result == 2:
            # User selected OTA
            newest_data = ['ota']
        elif result == 3:
            # User selected Factory
            newest_data = ['factory']
        elif result == 4:
            # User selected GSI
            newest_data = ['gsi']
        else:
            # result = 5
            # user selected CANCEL
            return -1

        fingerprint = None
        security_patch = None
        for data in newest_data:
            if data in ['ota', 'ota_error'] and ota_data:
                print("  Extracting PIF from Beta OTA ...")
                selected_url = None
                if device_model == '_select_':
                    try:
                        from device_selector import show_device_selector
                        devices = ota_data.__dict__['devices']
                        selected_device = show_device_selector(
                            parent=None,
                            devices=devices,
                            title="Select OTA Device",
                            message="Select an OTA device:"
                        )

                        if selected_device:
                            selected_url = selected_device['url']
                            # Extract codename from zip filename (format: codename-buildid-*.zip)
                            zip_filename = selected_device['zip_filename']
                            device_model = zip_filename.split('-')[0]
                            device_model = device_model.lower().replace('_beta', '').replace('beta_', '')
                            print(f"  Selected: {selected_device['device']} - {selected_device['zip_filename']}")
                        else:
                            print("Selection cancelled.")
                            return "Selection cancelled."
                    except ImportError:
                        selected_url = None
                elif device_model != 'random':
                    # Try to find a device that matches the requested device model
                    for device in ota_data.__dict__['devices']:
                        if device_model.lower() in device['zip_filename'].lower():
                            selected_url = device['url']
                            debug(f"  Found matching OTA device: {device['zip_filename']}")
                            break
                # Fall back to last device if no match found or if random was requested
                if selected_url is None:
                    selected_url = ota_data.__dict__['devices'][-1]['url']
                    debug(f"  Using last OTA device: {ota_data.__dict__['devices'][-1]['zip_filename']}")
                # Grab fp and sp from selected OTA zip
                fingerprint, security_patch = url2fpsp(selected_url, "ota")
                if fingerprint and security_patch:
                    model_list = []
                    product_list = []
                    model_list, product_list = get_model_and_prod_list(ota_data)
                    expiry_date = ota_data.__dict__['beta_expiry_date']
                    if model_list and product_list:
                        break
            elif data in ['factory', 'factory_error'] and factory_data:
                print("  Extracting PIF from Beta Factory ...")
                selected_url = None
                if device_model == '_select_':
                    try:
                        from device_selector import show_device_selector
                        devices = factory_data.__dict__['devices']
                        selected_device = show_device_selector(
                            parent=None,
                            devices=devices,
                            title="Select Factory Device",
                            message="Select a Factory device:"
                        )
                        if selected_device:
                            selected_url = selected_device['url']
                            # Extract codename from zip filename (format: codename-buildid-*.zip)
                            zip_filename = selected_device['zip_filename']
                            device_model = zip_filename.split('-')[0]
                            device_model = device_model.lower().replace('_beta', '').replace('beta_', '')
                            print(f"  Selected: {selected_device['device']} - {selected_device['zip_filename']}")
                        else:
                            print("Selection cancelled.")
                            return "Selection cancelled."
                    except ImportError:
                        selected_url = None
                elif device_model != 'random':
                    # Try to find a device that matches the requested model
                    for device in factory_data.__dict__['devices']:
                        if device_model.lower() in device['zip_filename'].lower():
                            selected_url = device['url']
                            debug(f"  Found matching Factory device: {device['zip_filename']}")
                            break
                # Fall back to last device if no match found or if random was requested
                if selected_url is None:
                    selected_url = factory_data.__dict__['devices'][-1]['url']
                    debug(f"  Using last Factory device: {factory_data.__dict__['devices'][-1]['zip_filename']}")
                # Grab fp and sp from selected Factory zip
                fingerprint, security_patch = url2fpsp(selected_url, "factory")
                if fingerprint and security_patch:
                    model_list = []
                    product_list = []
                    model_list, product_list = get_model_and_prod_list(factory_data)
                    expiry_date = factory_data.__dict__['beta_expiry_date']
                    if model_list and product_list:
                        break
            elif data in ['gsi', 'gsi_error'] and gsi_data:
                print(f"  Extracting beta print from GSI data version {latest_version} ...")
                fingerprint, security_patch = url2fpsp(gsi_data.__dict__['devices'][0]['url'], "gsi")
                incremental = gsi_data.__dict__['incremental']
                expiry_date = gsi_data.__dict__['beta_expiry_date']
                model_list = gsi_data.__dict__['model_list']
                product_list = gsi_data.__dict__['product_list']
                security_patch_level = gsi_data.__dict__['security_patch_level']
                if not model_list or not product_list:
                    model_list = []
                    product_list = []
                    if factory_data:
                        model_list, product_list = get_model_and_prod_list(factory_data)
                if not model_list or not product_list:
                    model_list = []
                    product_list = []
                    if ota_data:
                        model_list, product_list = get_model_and_prod_list(ota_data)
                if model_list and product_list:
                    if not security_patch:
                        # Make sur security_patch_level to YYYY-MM-DD format
                        try:
                            if security_patch_level:
                                # Handle month name format like "September 2020"
                                try:
                                    date_obj = datetime.strptime(security_patch_level, "%B %Y")
                                    security_patch = date_obj.strftime("%Y-%m-05")
                                except ValueError:
                                    # Try other common formats
                                    try:
                                        # handle YYYY-MM format
                                        if re.match(r'^\d{4}-\d{2}$', security_patch_level):
                                            security_patch = f"{security_patch_level}-05"
                                        # handle YYYY-MM-DD format already
                                        elif re.match(r'^\d{4}-\d{2}-\d{2}$', security_patch_level):
                                            security_patch = security_patch_level
                                        else:
                                            # fallback
                                            security_patch = security_patch_level
                                    except:
                                        security_patch = security_patch_level
                            else:
                                security_patch = ""
                        except Exception as e:
                            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to parse security patch level: {security_patch_level}")
                            security_patch = security_patch_level  # Fallback to original value
                    if not fingerprint:
                        build_id = gsi_data.__dict__['build']
                        fingerprint = f"google/gsi_gms_arm64/gsi_arm64:{latest_version}/{build_id}/{incremental}:user/release-keys"
                    if fingerprint and security_patch:
                        break


    build_type = 'user'
    build_tags = 'release-keys'
    if fingerprint and security_patch:
        print(f"Security Patch:           {security_patch}")
        # Extract props from fingerprint
        pattern = r'([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)$'
        match = re.search(pattern, fingerprint)
        if match and match.lastindex == 8:
            # product_brand = match[1]
            # product_name = match[2]
            # product_device = match[3]
            latest_version = match[4]
            build_id = match[5]
            incremental = match[6]
            if not canary_data:
                build_type = match[7]
                build_tags = match[8]

    def set_random_beta():
        list_count = len(model_list)
        list_rand = random.randint(0, list_count - 1)
        model = model_list[list_rand]
        product = product_list[list_rand]
        device = product.replace('_beta', '')
        return model, product, device

    def get_pif_data(model, product, device, latest_version, build_id, incremental, security_patch, build_type='user', build_tags='release-keys'):
        pif_data = {
            "MANUFACTURER": "Google",
            "MODEL": model,
            "FINGERPRINT": f"google/{product}/{device}:{latest_version}/{build_id}/{incremental}:{build_type}/{build_tags}",
            "PRODUCT": product,
            "DEVICE": device,
            "SECURITY_PATCH": security_patch,
            "DEVICE_INITIAL_SDK_INT": "32"
        }
        return pif_data

    if device_model and product_list and f"{device_model}_beta" in product_list:
        product = f"{device_model}_beta"
        model = model_list[product_list.index(product)]
        device = device_model
    elif device_model == 'all':
        json_string = ""
        i = 0
        for item in model_list:
            model = item
            product = product_list[i]
            device = product.replace('_beta', '')
            pif_data = get_pif_data(model, product, device, latest_version, build_id, incremental, security_patch, build_type, build_tags)
            # {
            #     "MANUFACTURER": "Google",
            #     "MODEL": model,
            #     "FINGERPRINT": f"google/{product}/{device}:{latest_version}/{build_id}/{incremental}:{build_type}/{build_tags}",
            #     "PRODUCT": product,
            #     "DEVICE": device,
            #     "SECURITY_PATCH": security_patch,
            #     "DEVICE_INITIAL_SDK_INT": "32"
            # }
            json_string += json.dumps(pif_data, indent=4) + "\n"
            i = i + 1
        print(f"Beta Print Expiry Date:   {expiry_date}")
        print(f"Pixel Beta Profile/Fingerprint:\n{json_string}")
        return json_string
    else:
        if model_list and product_list:
            model, product, device = set_random_beta()
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: No beta data found.")
            return "No beta print found for the selected version."

    # Dump values to pif.json
    pif_data = get_pif_data(model, product, device, latest_version, build_id, incremental, security_patch, build_type, build_tags)
    # pif_data = {
    #     "MANUFACTURER": "Google",
    #     "MODEL": model,
    #     "FINGERPRINT": f"google/{product}/{device}:{latest_version}/{build_id}/{incremental}:{build_type}/{build_tags}",
    #     "PRODUCT": product,
    #     "DEVICE": device,
    #     "SECURITY_PATCH": security_patch,
    #     "DEVICE_INITIAL_SDK_INT": "32"
    # }

    random_print_json = json.dumps(pif_data, indent=4)
    print(f"{beta_type} Print Expiry Date:   {expiry_date}")
    print(f"Random {beta_type} Profile/Fingerprint:\n{random_print_json}\n")
    return random_print_json


# ============================================================================
#                               Function get_beta_data
# ============================================================================
def get_beta_data(url):
    try:
        debug(f"Fetching beta data from URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch URL: {url}")
            return None, None
        ota_html = response.text

        soup = BeautifulSoup(ota_html, 'html.parser')

        # check if the page has beta in it.
        if 'beta' not in soup.get_text().lower():
            # print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: 'Beta' not found For URL: {url}")
            return None, None

        # Extract information from the first table
        table = soup.find('table', class_='responsive fixed')

        # If metadata table is missing, try to fetch it from alternate pages
        if not table:
            # Determine base URL to construct alternates
            # Typical URLs:
            # .../versions/16/qpr3/download-ota
            # .../versions/16/qpr3/download
            # .../versions/16/download-ota

            base_url = url.rsplit('/', 1)[0]
            current_endpoint = url.rsplit('/', 1)[1]

            alternates = []

            # 1. Try the counterpart (download <-> download-ota)
            if 'download-ota' in current_endpoint:
                alternates.append(f"{base_url}/download")
            elif 'download' in current_endpoint:
                alternates.append(f"{base_url}/download-ota")

            # 2. Try release notes
            alternates.append(f"{base_url}/release-notes")

            for alt_url in alternates:
                debug(f"ℹ️ Metadata table not found, checking alternate URL: {alt_url}")
                try:
                    alt_resp = requests.get(alt_url)
                    if alt_resp.status_code == 200:
                        alt_soup = BeautifulSoup(alt_resp.text, 'html.parser')
                        table = alt_soup.find('table', class_='responsive fixed')
                        if table:
                            debug(f"  ✅ Found metadata table at {alt_url}")
                            break
                except Exception as e:
                    print(f"  ❌ Failed to fetch alternate metadata from {alt_url}: {e}")

        release_date = None
        build = None
        emulator_support = None
        security_patch_level = None
        google_play_services = None
        beta_expiry_date = None

        if table:
            rows = table.find_all('tr')
            data = {}
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    key = cols[0].text.strip().lower().replace(' ', '_')
                    value = cols[1].text.strip()
                    data[key] = value

            release_date = data.get('release_date')
            build = data.get('build')
            if not build:
                wx.Yield()
                # try again to get the build, this time looking for builds
                build = data.get('builds')
            if not build:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Build(s) not found in the data.")
                return None, None
            else:
                # we might get an output like this: 'BP31.250610.004\n      BP31.250610.004.A1 (Pixel 6, 6 Pro)'
                # we need to extract the first build from it, but we also need to keep the other builds for later
                # when we're extracting the devices, we need to match the build with the device.
                builds = build.split('\n')
                if len(builds) > 1:
                    print(f"ℹ️ Multiple Builds are found, selecting the first one: {builds[0].strip()}")
                    build = builds[0].strip()  # Take the first build only
                    print(f"ℹ️ Selected Build:           {build}")
                else:
                    print(f"ℹ️ Single Build is found: {builds[0].strip()}")
                    build = builds[0].strip()
            emulator_support = data.get('emulator_support')
            security_patch_level = data.get('security_patch_level')
            google_play_services = data.get('google_play_services')

            if release_date:
                try:
                    beta_release_date = datetime.strptime(release_date, '%B %d, %Y').strftime('%Y-%m-%d')
                    beta_expiry = datetime.strptime(beta_release_date, '%Y-%m-%d') + timedelta(weeks=6)
                    beta_expiry_date = beta_expiry.strftime('%Y-%m-%d')
                except:
                    pass
        elif soup.find('table', id='images'):
            debug(f"⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Metadata table not found, using dummy metadata.")
            release_date = datetime.now().strftime("%B %d, %Y")
            build = "Unknown"
            emulator_support = "Unknown"
            security_patch_level = "Unknown"
            google_play_services = "Unknown"
            beta_expiry_date = (datetime.now() + timedelta(weeks=6)).strftime('%Y-%m-%d')
        else:
            # print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Required table is not found on the page.")
            return None, None

        # Extract information from the second table
        devices = []
        table = soup.find('table', id='images')
        rows = table.find_all('tr')[1:]  # Skip the header row
        error = False
        for row in rows:
            cols = row.find_all('td')
            device = cols[0].text.strip()
            button = cols[1].find('button')
            category = button['data-category']
            zip_filename = button.text.strip()
            hashcode = cols[1].find('code').text.strip()

            # Check if the build is present in the zip_filename, if not print a warning
            if not build:
                # If we have no build info, we can't verify, but we shouldn't fail the whole process
                pass
            if build and build != "Unknown" and build.lower() not in zip_filename.lower():
                print(f"⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Build '{build}' not found in zip filename '{zip_filename}' for device '{device}'")
                error = True

            # check if the first 8 characters of the hashcode is not in the zip_filename, if not print a warning
            if hashcode[:8].lower() not in zip_filename.lower():
                print(f"⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Hashcode '{hashcode[:8]}' not found in zip filename '{zip_filename}' for device '{device}'")
                error = True

            devices.append({
                'device': device,
                'category': category,
                'zip_filename': zip_filename,
                'hash': hashcode,
                'url': None,  # Placeholder for URL
                'error': error
            })

        # Find all hrefs and match with zip_filename
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            for device in devices:
                if device['zip_filename'] in href:
                    device['url'] = href
                    break
        incremental = ""
        security_patch = ""
        beta_data = BetaData(release_date, build, emulator_support, security_patch_level, google_play_services, beta_expiry_date, incremental, security_patch, devices)
        return beta_data, error
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_beta_data function")
        traceback.print_exc()
        return None, None


# ============================================================================
#                               Function get_latest_android_version
# ============================================================================
def get_latest_android_version(force_version=None):
    versions_url = "https://developer.android.com/about/versions"
    response = request_with_fallback('GET', versions_url)
    if response == 'ERROR' or response.status_code != 200:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch VERSIONS HTML")
        return -1, ''
    versions_html = response.text

    soup = BeautifulSoup(versions_html, 'html.parser')
    version = 0
    beta_link_url = ''
    beta_links = {}

    for link in soup.find_all('a'):
        # Look for Android Beta link
        span = link.find('span', class_='devsite-nav-text')
        if span and span.get_text(strip=True) == 'Android Beta':
            beta_href = link.get('href')
            if beta_href:
                # Convert relative URL to absolute if needed
                if beta_href.startswith('/'):
                    full_url = f"https://developer.android.com{beta_href}"
                else:
                    full_url = beta_href

                # Extract version from URL
                match = re.search(r'about/versions/(\d+)', full_url)
                if match:
                    ver = int(match.group(1))
                    # Only store if not already present (assuming descending order on page, first is newest)
                    if ver not in beta_links:
                        beta_links[ver] = full_url

        # Look for version links
        href = link.get('href')
        if href and re.match(r'https:\/\/developer\.android\.com\/about\/versions\/\d+', href):
            # capture the d+ part
            link_version = int(re.search(r'\d+', href).group())
            if force_version and not str(force_version).startswith('CANARY'):
                if link_version == force_version:
                    version = link_version
            else:
                if link_version > version:
                    version = link_version

    # Determine best beta link
    if force_version and not str(force_version).startswith('CANARY'):
        # Try to find beta link for forced version
        try:
            force_ver_int = int(force_version)
            if force_ver_int in beta_links:
                beta_link_url = beta_links[force_ver_int]
        except ValueError:
            pass
    else:
        # Find highest version in beta_links
        if beta_links:
            max_ver = max(beta_links.keys())
            beta_link_url = beta_links[max_ver]

    # Check for QPR updates on the specific version page
    if version > 0:
        version_page_url = f"https://developer.android.com/about/versions/{version}"
        print(f"Checking for QPR updates on {version_page_url}...")
        try:
            v_response = request_with_fallback('GET', version_page_url)
            if v_response != 'ERROR' and v_response.status_code == 200:
                v_soup = BeautifulSoup(v_response.text, 'html.parser')
                max_qpr = 0
                qpr_url = ""

                for link in v_soup.find_all('a'):
                    href = link.get('href')
                    if href:
                        # Check for qpr pattern: .../versions/{version}/qpr(\d+)
                        match = re.search(rf'about/versions/{version}/qpr(\d+)', href)
                        if match:
                            qpr_num = int(match.group(1))
                            if qpr_num > max_qpr:
                                max_qpr = qpr_num
                                # Construct base QPR url
                                qpr_url = f"https://developer.android.com/about/versions/{version}/qpr{qpr_num}"

                if max_qpr > 0:
                    print(f"Found newer QPR version:  QPR{max_qpr}")
                    beta_link_url = qpr_url
        except Exception as e:
            print(f"Failed to check for QPR updates: {e}")

    # Resolve any redirects in the beta_link_url
    if beta_link_url and 'qpr' not in beta_link_url.lower():
        beta_link_url = resolve_url_redirects(beta_link_url)

    return version, beta_link_url


# ============================================================================
#                               Function resolve_url_redirects
# ============================================================================
def resolve_url_redirects(url, max_redirects=5):
    try:
        if not url:
            return url

        current_url = url
        redirect_count = 0

        while redirect_count < max_redirects:
            response = request_with_fallback('HEAD', current_url)
            if response == 'ERROR':
                debug(f"Failed to check redirects for URL: {current_url}")
                return current_url

            if response.history:
                # There was a redirect, use the final URL
                new_url = response.url
                debug(f"URL redirected from {current_url} to: {new_url}")

                # Check if we've reached a stable URL (no more redirects)
                if new_url == current_url:
                    break

                current_url = new_url
                redirect_count += 1
            else:
                # No redirect, we've found the final URL
                break

        if redirect_count >= max_redirects:
            debug(f"Maximum redirect limit ({max_redirects}) reached for URL: {url}")

        return current_url

    except Exception as e:
        debug(f"Failed to resolve redirects for URL {url}: {e}")
        return url


# ============================================================================
#                Function get_fp_sp_from_incremental_remote_file
# ============================================================================
def get_fp_sp_from_incremental_remote_file(url, image_type, chunk_size=8*1024*1024, overlap=200, fallback_size=60*1024*1024):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)

            # Get the file size
            total_size = get_size_from_url(url)
            if total_size is None:
                print(f"⚠️ Could not determine file size for {url}.")
                return None, None

            fingerprint = None
            security_patch = None

            # Set up regex patterns based on image type, note: we won't be using the partial patterns here for now.
            if image_type == 'ota':
                fp_pattern_complete = r"post-build=(.+?)(\s|$)"
                fp_pattern_partial = r"post-build=([^\s]*?)$"
                sp_pattern_complete = r"security-patch-level=(.+?)(\s|$)"
                sp_pattern_partial = r"security-patch-level=([^\s]*?)$"
            elif image_type == 'factory':
                fp_pattern_complete = r"com\.android\.build\.boot\.fingerprint(.+?)\x00"
                fp_pattern_partial = r"com\.android\.build\.boot\.fingerprint([^\x00]*?)$"
                sp_pattern_complete = r"com\.android\.build\.boot\.security_patch(.+?)\x00"
                sp_pattern_partial = r"com\.android\.build\.boot\.security_patch([^\x00]*?)$"
            else:
                print(f"Unsupported image type for incremental reading: {image_type}")
                return None, None

            # First, try partial content requests (assume the server supports it)
            supports_partial_content = True
            debug(f"Starting chunked download with chunk_size=0x{chunk_size:x}, overlap=0x{overlap:x}")
            i = 0
            while fingerprint is None or security_patch is None:
                # Calculate start and end ranges with overlap
                start_range = i * chunk_size
                end_range = ((i + 1) * chunk_size) + overlap

                # Check if we've reached the end of the file
                if start_range >= total_size:
                    debug(f"Reached end of file at position {start_range}")
                    break

                # Adjust end_range if it exceeds file size
                if end_range > total_size:
                    end_range = total_size

                # Request range of bytes
                headers = {
                    "Range": f"bytes={start_range}-{end_range - 1}",
                    "Accept-Encoding": "identity"  # Disable compression to avoid gzip issues
                }
                # debug(f"Fetching bytes {start_range} to {end_range - 1} from {url}")
                debug(f"Fetching bytes 0x{start_range:x} to 0x{(end_range - 1):x}")
                wx.Yield()

                try:
                    response = requests.get(url, headers=headers, stream=True, verify=False, timeout=30)

                    if response.status_code == 206:  # Partial content success
                        ## Optional save each binary chunk to file for debugging
                        #
                        # config_path = get_config_path()
                        # debug_dir = os.path.join(config_path, 'debug_chunks')
                        # os.makedirs(debug_dir, exist_ok=True)
                        # chunk_filename = os.path.join(debug_dir, f"chunk_{start_range}_{end_range - 1}.bin")
                        # with open(chunk_filename, 'wb') as chunk_file:
                        #     chunk_file.write(response.content)
                        # print(f"Saved chunk to {chunk_filename}")

                        content = response.content.decode('utf-8', errors='ignore')

                        # Search for fingerprint
                        if fingerprint is None:
                            fp_match = re.search(fp_pattern_complete, content)
                            if fp_match:
                                fingerprint = fp_match.group(1).strip('\x00')
                                debug(f"Found fingerprint: {fingerprint}")
                                wx.Yield()

                        # Search for security patch
                        if security_patch is None:
                            sp_match = re.search(sp_pattern_complete, content)
                            if sp_match:
                                security_patch = sp_match.group(1).strip('\x00')
                                debug(f"Found security patch: {security_patch}")
                                wx.Yield()

                        i += 1
                    else:
                        print(f"⚠️ Server doesn't support partial content, status: {response.status_code}")
                        supports_partial_content = False
                        break
                except Exception as e:
                    print(f"⚠️ Error fetching chunk: {str(e)}")
                    # Try to continue with the next chunk
                    i += 1
                    # If we've gone too far, break out
                    if i * chunk_size >= total_size:
                        print("⚠️ Reached end of file or encountered too many errors, stopping chunked download")
                        break

            # If we couldn't find the patterns with partial content,
            # or server doesn't support it, try a single larger request as fallback
            if not supports_partial_content or (fingerprint is None or security_patch is None):
                print(f"⚠️ Using fallback method: requesting file directly. This might take a while for large files...")
                try:
                    # For OTA files, limit to first few MB since metadata is usually at the beginning
                    if image_type == 'ota':
                        fallback_size = min(5*1024*1024, total_size)  # 5MB for OTA
                        debug(f"Downloading first {fallback_size // (1024*1024)}MB of OTA file...")
                        headers = {"Accept-Encoding": "identity"}  # Disable compression
                        response = requests.get(url, headers=headers, stream=True, verify=False, timeout=60)
                        content = response.raw.read(fallback_size).decode('utf-8', errors='ignore')
                    else:
                        # For factory images, we might need to download a larger portion
                        fallback_size = min(fallback_size, total_size)  # 60MB for factory images
                        debug(f"Downloading first {fallback_size // (1024*1024)}MB of file...")
                        headers = {"Accept-Encoding": "identity"}  # Disable compression
                        response = requests.get(url, headers=headers, stream=True, verify=False, timeout=90)
                        content = response.raw.read(fallback_size).decode('utf-8', errors='ignore')

                    # Search for patterns in the fallback content
                    if fingerprint is None:
                        fp_match = re.search(fp_pattern_complete, content)
                        if fp_match:
                            fingerprint = fp_match.group(1).strip('\x00')
                            debug(f"Found fingerprint: {fingerprint}")
                            wx.Yield()

                    if security_patch is None:
                        sp_match = re.search(sp_pattern_complete, content)
                        if sp_match:
                            security_patch = sp_match.group(1).strip('\x00')
                            debug(f"Found security patch: {security_patch}")
                            wx.Yield()

                except Exception as e:
                    print(f"⚠️ Fallback request failed: {str(e)}")

                # If fallback approach failed and we still don't have the data,
                if fingerprint is None or security_patch is None:
                    print(f"⚠️ Could not extract required information from partial download.")

            return fingerprint, security_patch

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_fp_sp_from_incremental_remote_file")
        traceback.print_exc()
        return None, None


# ============================================================================
#                               Function url2fpsp
# ============================================================================
def url2fpsp(url, image_type, override_size_limit=None):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)

            fingerprint = None
            security_patch = None

            # For OTA and factory images, use incremental chunk fetching
            if image_type == 'ota':
                chunk_size = override_size_limit if override_size_limit is not None else 2*1024
                fingerprint, security_patch = get_fp_sp_from_incremental_remote_file(url, image_type, chunk_size)

            elif image_type == 'factory':
                chunk_size = override_size_limit if override_size_limit is not None else 8*1024*1024
                fingerprint, security_patch = get_fp_sp_from_incremental_remote_file(url, image_type, chunk_size)

            elif image_type == 'gsi':
                response = requests.head(url)
                file_size = int(response.headers["Content-Length"])
                start_byte = max(0, file_size - 8192)
                headers = {
                    "Range": f"bytes={start_byte}-{file_size - 1}",
                    "Accept-Encoding": "identity"  # Disable compression
                }
                response = requests.get(url, headers=headers, stream=True, verify=False)
                end_content = response.content
                content = partial_extract(end_content, "build.prop")
                if content is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to extract build.prop from GSI content")
                    return None, None
                content_str = content.decode('utf-8', errors='ignore')
                fingerprint_match = re.search(r"ro\.system\.build\.fingerprint=(.+)", content_str)
                security_patch_match = re.search(r"ro\.build\.version\.security_patch=(.+)", content_str)

                fingerprint = fingerprint_match.group(1).strip('\x00') if fingerprint_match else None
                security_patch = security_patch_match.group(1).strip('\x00') if security_patch_match else None

            elif image_type == 'canary':
                response = requests.get(url, stream=True, verify=False)
                content = response.content.decode('utf-8', errors='ignore')
                fingerprint_match = re.search(r"^FINGERPRINT=(.+)", content, re.MULTILINE)
                security_patch_match = re.search(r"^SECURITY_PATCH=(.+)", content, re.MULTILINE)
                expiry_date_match = re.search(r"^#\sEstimated\sExpiry:\s(.+)", content, re.MULTILINE)
                if fingerprint_match:
                    fingerprint = fingerprint_match.group(1).strip()
                if security_patch_match:
                    security_patch = security_patch_match.group(1).strip()
                if expiry_date_match:
                    expiry_date = expiry_date_match.group(1).strip()
                return fingerprint, security_patch, expiry_date

            else:
                print(f"Invalid image type: {image_type}")
                return None, None

            # debug("FINGERPRINT:", fingerprint)
            # debug("SECURITY_PATCH:", security_patch)
            return fingerprint, security_patch
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in url2fpsp function")
        traceback.print_exc()
        return None, None


# ============================================================================
#                               Function partial_extract
# ============================================================================
def partial_extract(content, extract_file):
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            debug(f"Files in the partial ZIP content:")
            debug(zip_file.namelist())
            # Extracting a specific file by name
            with zip_file.open(extract_file) as file:
                content = file.read()
                return content
    except zipfile.BadZipFile as e:
        print("Unable to read ZIP file:", e)
    except KeyError:
        print("Target file not found in ZIP content.")
    except Exception as e:
        print("An error occurred:", e)


# ============================================================================
#                               Function format_memory_size
# ============================================================================
def get_printable_memory():
    try:
        free_memory, total_memory = get_free_memory()
        formatted_free_memory = format_memory_size(free_memory)
        formatted_total_memory = format_memory_size(total_memory)
        return f"Available Free Memory: {formatted_free_memory} / {formatted_total_memory}"
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_printable_memory function")
        traceback.print_exc()


# ============================================================================
#                               Function device_has_update
# ============================================================================
def device_has_update(data, device_id, target_date):
    try:
        if not data:
            return False
        if device_id in data:
            device_data = data[device_id]

            for download_type in ['ota', 'factory']:
                for download_entry in device_data[download_type]:
                    download_date = download_entry['date']
                    # Compare the download date with the target date
                    if download_date > target_date:
                        return True
        return False
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in device_has_update function")
        traceback.print_exc()


# ============================================================================
#                     Function fetch_canary_miner_catalog
# ============================================================================
def fetch_canary_miner_catalog(catalog_path=None):
    if catalog_path is None:
        catalog_path = os.path.join(get_config_path(), 'canary_miner_catalog.json').strip()

    try:
        from constants import CANARY_MINER_CATALOG_URL
        catalog_url = CANARY_MINER_CATALOG_URL
        if 'github.com' in catalog_url and '/blob/' in catalog_url:
            catalog_url = catalog_url.replace('https://github.com/', 'https://raw.githubusercontent.com/').replace('/blob/', '/')

        res = request_with_fallback(method='GET', url=catalog_url)
        if res == 'ERROR':
            return None, catalog_path

        content = res.content if hasattr(res, 'content') else res.text
        text = content if isinstance(content, str) else content.decode('utf-8', errors='replace')

        try:
            catalog_json = json.loads(text)
            with open(catalog_path, 'w', encoding='utf-8') as f:
                json.dump(catalog_json, f, indent=2)
            return catalog_json, catalog_path
        except Exception:
            with open(catalog_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return None, catalog_path
    except Exception:
        return (None, catalog_path) if catalog_path else (None, None)


# ============================================================================
#                               Function get_google_images
# ============================================================================
def get_google_images(save_to=None):
    try:
        COOKIE = {'Cookie': 'devsite_wall_acks=nexus-ota-tos,nexus-image-tos,watch-image-tos,watch-ota-tos'}
        data = {}

        if save_to is None:
            save_to = os.path.join(get_config_path(), "google_images.json").strip()

        # Fetch the Beta OTA and Beta Factory image data
        ota_beta_data, factory_beta_data, ota_error, factory_error = get_beta_links()
        if ota_beta_data.build:
            ota_build_id = ota_beta_data.build
        else:
            ota_build_id = ''
        if factory_beta_data.build:
            factory_build_id = factory_beta_data.build
        else:
            factory_build_id = ''

        for image_type in ['ota', 'factory', 'ota-watch', 'factory-watch']:
            if image_type == 'ota':
                url = "https://developers.google.com/android/ota"
                download_type = "ota"
                device_type = "phone"
            elif image_type == 'factory':
                url = "https://developers.google.com/android/images"
                download_type = "factory"
                device_type = "phone"
            elif image_type == 'ota-watch':
                url = "https://developers.google.com/android/ota-watch"
                download_type = "ota"
                device_type = "watch"
            elif image_type == 'factory-watch':
                url = "https://developers.google.com/android/images-watch"
                download_type = "factory"
                device_type = "watch"

            response = request_with_fallback(method='GET', url=url, headers=COOKIE)
            if response != 'ERROR':
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                marlin_flag = False

                # Find all the <h2> elements containing device names
                device_elements = soup.find_all('h2')
            else:
                device_elements = []

            # Iterate through the device elements
            for device_element in device_elements:
                # Check if the text of the <h2> element should be skipped
                if device_element.text.strip() in [
                        "Terms and conditions",
                        "Updating instructions",
                        "Updating Pixel 6, Pixel 6 Pro, and Pixel 6a devices to Android 13 for the first time",
                        "Use Android Flash Tool",
                        "Flashing instructions",
                        "Special instructions for updating Pixel 6, Pixel 6 Pro, and Pixel 6a devices to Android 13 for the first time",
                        "Manual flashing instructions",
                        "Special instructions for updating Pixel devices to the May 2025 monthly release"
                    ]:
                    continue

                # Extract the device name from the 'id' attribute
                device_id = device_element.get('id')

                # Skip if device_id is None or empty or one of the known invalid ids
                if not device_id or device_id in [
                        "key-takeaways-panel-title"
                    ]:
                    continue

                                # Extract the device name from the 'id' attribute
                device_class = device_element.get('class')
                if device_class and ("no-link" in device_class or "hide-from-toc" in device_class):
                    # debug(f"Skipping element with class: {device_class} and id: {device_id}")
                    continue

                # Extract the device label from the text and strip "id", if it fails, skip it
                try:
                    device_label = device_element.get('data-text').strip('"').split('" for ')[1]
                except Exception as e:
                    print(f"⚠️ {datetime.now():%Y-%m-%d %H:%M:%S} WARNING: Skipping element [{device_id}] with unexpected device format: {device_element.get('data-text')}")
                    continue

                # Initialize a dictionary to store the device's downloads for both OTA and Factory
                downloads_dict = {'ota': [], 'factory': []}

                # Find the <table> element following the <h2> for each device
                table = device_element.find_next('table')

                # Find all <tr> elements in the table
                rows = table.find_all('tr')

                # For factory images, the table format changes from Marlin onwards
                if device_id == 'marlin':
                    marlin_flag = True

                for row in rows:
                    # Extract the fields from each <tr> element
                    columns = row.find_all('td')
                    version = ''
                    with contextlib.suppress(Exception):
                        version = columns[0].text.strip()

                    # Different extraction is necessary per type
                    download_url = ''
                    sha256_checksum = ''
                    if image_type in ['ota', 'ota-watch'] or (marlin_flag and image_type == "factory"):
                        with contextlib.suppress(Exception):
                            sha256_checksum = columns[2].text.strip()
                        with contextlib.suppress(Exception):
                            download_url = columns[1].find('a')['href']
                    elif image_type in ['factory', 'factory-watch']:
                        with contextlib.suppress(Exception):
                            download_url = columns[2].find('a')['href']
                        with contextlib.suppress(Exception):
                            sha256_checksum = columns[3].text.strip()

                    date = ''
                    with contextlib.suppress(Exception):
                        date_match = re.search(r'\b(\d{6})\b', version)
                        date = None
                        if date_match:
                            date = date_match[1]
                        else:
                            date = extract_date_from_google_version(version)

                    # Create a dictionary for each download
                    download_info = {
                        'version': version,
                        'url': download_url,
                        'sha256': sha256_checksum,
                        'date': date
                    }

                    # Check if the download entry already exists, and only add it if it's a new entry
                    if download_info not in downloads_dict[download_type]:
                        downloads_dict[download_type].append(download_info)

                # Add the device name (using 'device_id') and device label (using 'device_label') to the data dictionary
                if device_id not in data:
                    data[device_id] = {
                        'label': device_label,
                        'type': device_type,
                        'ota': [],
                        'factory': []
                    }

                # Append the downloads to the corresponding list based on download_type
                data[device_id]['ota'].extend(downloads_dict['ota'])
                data[device_id]['factory'].extend(downloads_dict['factory'])

                beta_entries = []

                # Check if we have valid beta data for OTA
                if ota_beta_data and isinstance(ota_beta_data, BetaData) and hasattr(ota_beta_data, 'devices'):
                    for beta_item in ota_beta_data.devices:
                        if device_label == beta_item['device']:
                            if beta_item['error']:
                                the_version = f"⚠️ OTA - {beta_item['category']} ({ota_build_id}) - Problem with wrong build or hash"
                            else:
                                the_version = f"OTA - {beta_item['category']} ({ota_build_id})"
                            beta_info = {
                                'version': the_version,
                                'url': beta_item['url'],
                                'sha256': beta_item['hash'],
                                'date': datetime.now().strftime('%y%m%d')
                            }
                            beta_entries.append(beta_info)

                # Check if we have valid beta data for Factory
                if factory_beta_data and isinstance(factory_beta_data, BetaData) and hasattr(factory_beta_data, 'devices'):
                    for beta_item in factory_beta_data.devices:
                        if device_label == beta_item['device']:
                            if beta_item['error']:
                                the_version = f"⚠️ Factory - {beta_item['category']} ({factory_build_id}) - Problem with wrong build or hash"
                            else:
                                the_version = f"Factory - {beta_item['category']} ({factory_build_id})"
                            beta_info = {
                                'version': f"Factory - {beta_item['category']} ({factory_build_id})",
                                'url': beta_item['url'],
                                'sha256': beta_item['hash'],
                                'date': datetime.now().strftime('%y%m%d')
                            }
                            beta_entries.append(beta_info)

                # Only add beta list if there are actual beta entries
                if beta_entries:
                    data[device_id]['beta'] = beta_entries

        # Attempt to fetch and incorporate canary miner catalog if available
        try:
            catalog, catalog_path = fetch_canary_miner_catalog()
            if not catalog_path:
                catalog_path = os.path.join(get_config_path(), 'canary_miner_catalog.json').strip()

            if not catalog and catalog_path and os.path.exists(catalog_path):
                try:
                    with open(catalog_path, 'r', encoding='utf-8') as f:
                        catalog = json.load(f)
                except Exception:
                    catalog = None

            if catalog:
                def extract_sha256_from_url(u):
                    if not u:
                        return ''
                    m = re.search(r"([a-fA-F0-9]{64})", u)
                    if m:
                        return m.group(1)
                    # fallback: last path segment without extension
                    try:
                        name = os.path.basename(urlparse(u).path)
                        # strip extension
                        name = os.path.splitext(name)[0]
                        return name
                    except Exception:
                        return ''

                # Build by_device from catalog structure. Catalog typically has top-level 'canaries' and 'betas'.
                by_device = {}
                if isinstance(catalog, dict):
                    for section_name in ('canaries', 'betas'):
                        section = catalog.get(section_name, {})
                        if not isinstance(section, dict):
                            continue
                        for device_key, device_obj in section.items():
                            releases = []
                            try:
                                releases = device_obj.get('releases', [])
                            except Exception:
                                continue
                            for rel in releases:
                                try:
                                    releaseId = rel.get('releaseId', '') if isinstance(rel, dict) else ''
                                    buildName = rel.get('buildName', '') if isinstance(rel, dict) else ''
                                    url_field = rel.get('url', '') if isinstance(rel, dict) else ''
                                    typ = 'canaries' if section_name == 'canaries' else 'betas'
                                    version = ''
                                    if releaseId and buildName:
                                        version = f"{releaseId} - {buildName}"
                                    elif releaseId:
                                        version = str(releaseId)
                                    elif buildName:
                                        version = str(buildName)
                                    sha = extract_sha256_from_url(url_field)
                                    date = None
                                    if buildName:
                                        m = re.search(r"(\d{6})", str(buildName))
                                        if m:
                                            date = m.group(1)
                                    entry = {'version': version, 'url': url_field, 'sha256': sha, 'date': date}
                                    if device_key not in by_device:
                                        by_device[device_key] = {'canaries': [], 'betas': []}
                                    by_device[device_key][typ].append(entry)
                                except Exception:
                                    continue
                elif isinstance(catalog, list):
                    # fallback: try to process list items
                    for item in catalog:
                        try:
                            if not isinstance(item, dict):
                                continue
                            device_key = get_first_match(item, ['device', 'codename', 'product', 'device_codename'])
                            releaseId = get_first_match(item, ['releaseId', 'release', 'channel'])
                            buildName = get_first_match(item, ['buildName', 'build', 'name'])
                            url_field = get_first_match(item, ['url', 'downloadUrl', 'link'])
                            typ = 'betas'
                            lower = (str(releaseId) + ' ' + str(buildName)).lower()
                            if 'canary' in lower or 'canary' in str(releaseId).lower():
                                typ = 'canaries'
                            version = ''
                            if releaseId and buildName:
                                version = f"{releaseId} - {buildName}"
                            elif releaseId:
                                version = str(releaseId)
                            elif buildName:
                                version = str(buildName)
                            sha = extract_sha256_from_url(url_field)
                            date = None
                            if buildName:
                                m = re.search(r"(\d{6})", str(buildName))
                                if m:
                                    date = m.group(1)
                            entry = {'version': version, 'url': url_field, 'sha256': sha, 'date': date}
                            if device_key not in by_device:
                                by_device[device_key] = {'canaries': [], 'betas': []}
                            by_device[device_key][typ].append(entry)
                        except Exception:
                            continue

                # merge into existing data
                for dev_key, lists in by_device.items():
                    # try to find matching device id in data; device ids in data are keys like 'redfin'.
                    # If device_key matches any of device label or id, attach; otherwise skip.
                    target_key = None
                    if dev_key in data:
                        target_key = dev_key
                    else:
                        # try match by label
                        for did, dval in data.items():
                            label = dval.get('label', '')
                            if label and dev_key and dev_key.lower() in label.lower():
                                target_key = did
                                break
                    if not target_key:
                        # if blank device_key, skip
                        continue

                    # sort newest first by date (None treated as 0)
                    def sort_key(e):
                        try:
                            return int(e['date']) if e.get('date') else 0
                        except Exception:
                            return 0

                    if lists.get('canaries'):
                        sorted_can = sorted(lists['canaries'], key=sort_key, reverse=True)
                        data[target_key]['canaries'] = sorted_can
                    if lists.get('betas'):
                        sorted_bet = sorted(lists['betas'], key=sort_key, reverse=True)
                        # Preserve existing 'beta' key used elsewhere; also add 'betas' for All Betas submenu
                        data[target_key]['betas'] = sorted_bet
        except Exception:
            pass

        # Convert to JSON
        json_data = json.dumps(data, indent=2)

        # Save
        with open(save_to, 'w', encoding='utf-8') as json_file:
            json_file.write(json_data)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_google_images function")
        traceback.print_exc()


# ============================================================================
#                         extract_date_from_google_version
# ============================================================================
def extract_date_from_google_version(version_string):
    try:
        # pattern to find a 3-letter month followed by a year
        pattern = re.compile(r'(\b[A-Za-z]{3}\s\d{4}\b)')
        match = pattern.search(version_string)

        if match:
            date_str = match.group()
            date_obj = datetime.strptime(date_str, '%b %Y')
            # convert to yymm01
            return date_obj.strftime('%y%m01')
        return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in extract_date_from_google_version function")
        traceback.print_exc()


# ============================================================================
#                               Function download_file
# ============================================================================
def download_file(url, filename=None, callback=None, stream=True):
    if not url:
        return
    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Downloading: {url} ...")
    start = time.time()

    try:
        response = request_with_fallback(method='GET', url=url, stream=stream)
        config_path = get_config_path()
        if not filename:
            filename = os.path.basename(urlparse(url).path)
        downloaded_file_path = os.path.join(config_path, 'tmp', filename)
        with open(downloaded_file_path, "wb") as fd:
            for chunk in response.iter_content(chunk_size=131072):
                fd.write(chunk)
        # check if filename got downloaded
        if not os.path.exists(downloaded_file_path):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
            print("Aborting ...\n")
            return 'ERROR'
        end = time.time()
        print(f"\nℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} Download: {filename} completed! in {math.ceil(end - start)} seconds")
        # Call the callback function if provided
        if callback:
            callback()
        return downloaded_file_path
    except Exception:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
        traceback.print_exc()
        return 'ERROR'


# ============================================================================
#                               Function get_first_match
# ============================================================================
def get_first_match(dictionary, keys):
    try:
        for key in keys:
            if key in dictionary:
                value = dictionary[key]
                break
        else:
            value = ''
        return value
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_first_match function")
        traceback.print_exc()


# ============================================================================
#                               Function delete_keys_from_dict
# ============================================================================
def delete_keys_from_dict(dictionary, keys):
    try:
        for key in keys:
            if key in dictionary:
                del dictionary[key]
        return dictionary
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in delete_keys_from_dict function")
        traceback.print_exc()


# ============================================================================
#                               Function is_valid_json
# ============================================================================
def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except Exception:
        try:
            json5.loads(json_str)
            return True
        except Exception:
            return False


# ============================================================================
#                               Function process_dict
# ============================================================================
def process_dict(the_dict, add_missing_keys=False, pif_flavor='', set_first_api=None, sort_data=False, keep_all=False):
    try:
        module_versionCode = 0
        module_flavor = None
        config = get_config()
        with contextlib.suppress(Exception):
            module_flavor = pif_flavor.split('_')[0]
            module_versionCode = int(pif_flavor.split('_')[1])
        if module_flavor is None or module_flavor == '':
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to determine module flavor.")
            return ''
        if module_versionCode == 0:
            module_versionCode = 9999999
        android_devices = get_android_devices()
        autofill = False
        if add_missing_keys:
            device = get_phone()
            if device:
                device_dict = device.props.property
                autofill = True
            else:
                print("ERROR: Device is unavailable to add missing fields from device.")

        # FINGERPRINT
        fp_ro_product_brand = ''
        fp_ro_product_name = ''
        fp_ro_product_device = ''
        fp_ro_build_version_release = ''
        fp_ro_build_id = ''
        fp_ro_build_version_incremental = ''
        fp_ro_build_type = ''
        fp_ro_build_tags = ''
        keys = ['ro.build.fingerprint', 'ro.system.build.fingerprint', 'ro.product.build.fingerprint', 'ro.vendor.build.fingerprint']
        ro_build_fingerprint = get_first_match(the_dict, keys)
        if ro_build_fingerprint != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if autofill and ro_build_fingerprint == '':
            ro_build_fingerprint = get_first_match(device_dict, keys)
        if ro_build_fingerprint:
            # Let's extract props from fingerprint in case we need them
            pattern = r'([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)$'
            match = re.search(pattern, ro_build_fingerprint)
            if match and match.lastindex == 8:
                fp_ro_product_brand = match[1]
                fp_ro_product_name = match[2]
                fp_ro_product_device = match[3]
                fp_ro_build_version_release = match[4]
                fp_ro_build_id = match[5]
                fp_ro_build_version_incremental = match[6]
                fp_ro_build_type = match[7]
                fp_ro_build_tags = match[8]

        # PRODUCT
        keys = ['ro.product.name', 'ro.product.system.name', 'ro.product.product.name', 'ro.product.vendor.name', 'ro.vendor.product.name']
        ro_product_name = get_first_match(the_dict, keys)
        if ro_product_name != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (not ro_product_name or any(keyword in ro_product_name.lower() for keyword in ['mainline', 'generic'])) and fp_ro_product_name:
            debug(f"Properties for PRODUCT are extracted from FINGERPRINT: {fp_ro_product_name}")
            ro_product_name = fp_ro_product_name
        if autofill and ro_product_name == '':
            ro_product_name = get_first_match(device_dict, keys)

        # DEVICE (ro.build.product os fallback, keep it last)
        keys = ['ro.product.device', 'ro.product.system.device', 'ro.product.product.device', 'ro.product.vendor.device', 'ro.vendor.product.device', 'ro.build.product']
        ro_product_device = get_first_match(the_dict, keys)
        if ro_product_device != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (not ro_product_device or any(keyword in ro_product_device.lower() for keyword in ['mainline', 'generic'])) and fp_ro_product_device:
            debug(f"Properties for DEVICE are extracted from FINGERPRINT: {fp_ro_product_device}")
            ro_product_device = fp_ro_product_device
        if autofill and ro_product_device == '':
            ro_product_device = get_first_match(device_dict, keys)

        # MANUFACTURER
        keys = ['ro.product.manufacturer', 'ro.product.system.manufacturer', 'ro.product.product.manufacturer', 'ro.product.vendor.manufacturer', 'ro.vendor.product.manufacturer']
        ro_product_manufacturer = get_first_match(the_dict, keys)
        if ro_product_manufacturer != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if autofill and ro_product_manufacturer == '':
            ro_product_manufacturer = get_first_match(device_dict, keys)

        # BRAND
        keys = ['ro.product.brand', 'ro.product.system.brand', 'ro.product.product.brand', 'ro.product.vendor.brand', 'ro.vendor.product.brand']
        ro_product_brand = get_first_match(the_dict, keys)
        if ro_product_brand != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_product_brand is None or ro_product_brand == '') and fp_ro_product_brand != '':
            debug(f"Properties for BRAND are not found, using value from FINGERPRINT: {fp_ro_product_brand}")
            ro_product_brand = fp_ro_product_brand
        if autofill and ro_product_brand == '':
            ro_product_brand = get_first_match(device_dict, keys)

        # MODEL
        keys = ['ro.product.model', 'ro.product.system.model', 'ro.product.product.model', 'ro.product.vendor.model', 'ro.vendor.product.model']
        ro_product_model = get_first_match(the_dict, keys)
        if (not ro_product_model or any(keyword in ro_product_model.lower() for keyword in ['mainline', 'generic'])):
            ro_product_model_bak = ro_product_model
            # get it from vendor/build.prop (ro.product.vendor.model)
            ro_product_vendor_model = get_first_match(the_dict, ['ro.product.vendor.model'])
            if ro_product_vendor_model and ro_product_vendor_model != '':
                ro_product_model = ro_product_vendor_model
            else:
                # If it is a Google device
                if ro_product_manufacturer == 'Google':
                # get model from android_devices if it is a Google device
                    try:
                        ro_product_model = android_devices[ro_product_device]['device']
                    except KeyError:
                        ro_product_model = ro_product_model_bak
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Key '{ro_product_device}' not found in android_devices.\nMODEL field could be wrong")
        if ro_product_model != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if autofill and ro_product_model == '':
            ro_product_model = get_first_match(device_dict, keys)

        # SECURITY_PATCH
        keys = ['ro.build.version.security_patch', 'ro.vendor.build.security_patch']
        ro_build_version_security_patch = get_first_match(the_dict, keys)
        if ro_build_version_security_patch != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if autofill and ro_build_version_security_patch == '':
            ro_build_version_security_patch = get_first_match(device_dict, keys)

        # FIRST_API_LEVEL
        keys = ['ro.product.first_api_level', 'ro.board.first_api_level', 'ro.board.api_level', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.vendor.build.version.sdk', 'ro.product.build.version.sdk']
        if set_first_api:
            ro_product_first_api_level = set_first_api
        else:
            ro_product_first_api_level = get_first_match(the_dict, keys)
            if ro_product_first_api_level and int(ro_product_first_api_level) > 32:
                ro_product_first_api_level = '32'
            if autofill and ro_product_first_api_level == '':
                ro_product_first_api_level = get_first_match(device_dict, keys)
        if ro_product_first_api_level != '':
            the_dict = delete_keys_from_dict(the_dict, keys)

        # BUILD_ID
        keys = ['ro.build.id']
        ro_build_id = get_first_match(the_dict, keys)
        if ro_build_id != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_build_id is None or ro_build_id == '') and fp_ro_build_id != '':
            debug(f"Properties for ID are not found, using value from FINGERPRINT: {fp_ro_build_id}")
            ro_build_id = fp_ro_build_id
        if autofill and ro_build_id == '':
            ro_build_id = get_first_match(device_dict, keys)

        # RELEASE
        keys = ['ro.build.version.release']
        ro_build_version_release = get_first_match(the_dict, keys)
        if ro_build_version_release != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_build_version_release is None or ro_build_version_release == '') and fp_ro_build_version_release != '':
            debug(f"Properties for RELEASE are not found, using value from FINGERPRINT: {fp_ro_build_version_release}")
            ro_build_version_release = fp_ro_build_version_release
        if autofill and ro_build_version_release == '':
            ro_build_version_release = get_first_match(device_dict, keys)

        # INCREMENTAL
        keys = ['ro.build.version.incremental']
        ro_build_version_incremental = get_first_match(the_dict, keys)
        if ro_build_version_incremental != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_build_version_incremental is None or ro_build_version_incremental == '') and fp_ro_build_version_incremental != '':
            debug(f"Properties for INCREMENTAL are not found, using value from FINGERPRINT: {fp_ro_build_version_incremental}")
            ro_build_version_incremental = fp_ro_build_version_incremental
        if autofill and ro_build_version_incremental == '':
            ro_build_version_incremental = get_first_match(device_dict, keys)

        # TYPE
        keys = ['ro.build.type']
        ro_build_type = get_first_match(the_dict, keys)
        if ro_build_type != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_build_type is None or ro_build_type == '') and fp_ro_build_type != '':
            debug(f"Properties for TYPE are not found, using value from FINGERPRINT: {fp_ro_build_type}")
            ro_build_type = fp_ro_build_type
        if autofill and ro_build_type == '':
            ro_build_type = get_first_match(device_dict, keys)

        # TAGS
        keys = ['ro.build.tags']
        ro_build_tags = get_first_match(the_dict, keys)
        if ro_build_tags != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if (ro_build_tags is None or ro_build_tags == '') and fp_ro_build_tags != '':
            debug(f"Properties for TAGS are not found, using value from FINGERPRINT: {fp_ro_build_tags}")
            ro_build_tags = fp_ro_build_tags
        if autofill and ro_build_tags == '':
            ro_build_tags = get_first_match(device_dict, keys)

        # VNDK_VERSION
        keys = ['ro.vndk.version', 'ro.product.vndk.version']
        ro_vndk_version = get_first_match(the_dict, keys)
        if ro_vndk_version != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if autofill and ro_vndk_version == '':
            ro_vndk_version = get_first_match(device_dict, keys)

        # Get any missing FINGERPRINT fields
        ffp_ro_product_brand = fp_ro_product_brand if fp_ro_product_brand != '' else ro_product_brand
        ffp_ro_product_name = fp_ro_product_name if fp_ro_product_name != '' else ro_product_name
        ffp_ro_product_device = fp_ro_product_device if fp_ro_product_device != '' else ro_product_device
        ffp_ro_build_version_release = fp_ro_build_version_release if fp_ro_build_version_release != '' else ro_build_version_release
        ffp_ro_build_id = fp_ro_build_id if fp_ro_build_id != '' else ro_build_id
        ffp_ro_build_version_incremental = fp_ro_build_version_incremental if fp_ro_build_version_incremental != '' else ro_build_version_incremental
        ffp_ro_build_type = fp_ro_build_type if fp_ro_build_type != '' else ro_build_type
        ffp_ro_build_tags = fp_ro_build_tags if fp_ro_build_tags != '' else ro_build_tags
        # Rebuild the FINGERPRINT
        if ffp_ro_product_brand and ffp_ro_product_name and ffp_ro_product_device and ffp_ro_build_version_release and ffp_ro_build_id and ffp_ro_build_version_incremental and ffp_ro_build_type and ffp_ro_build_tags:
            ro_build_fingerprint = f"{ffp_ro_product_brand}/{ffp_ro_product_name}/{ffp_ro_product_device}:{ffp_ro_build_version_release}/{ffp_ro_build_id}/{ffp_ro_build_version_incremental}:{ffp_ro_build_type}/{ffp_ro_build_tags}"

        # Global Common
        donor_data = {
            "MANUFACTURER": ro_product_manufacturer,
            "MODEL": ro_product_model,
            "FINGERPRINT": ro_build_fingerprint,
            "BRAND": ro_product_brand,
            "PRODUCT": ro_product_name,
            "DEVICE": ro_product_device,
            "RELEASE": ro_build_version_release,
            "ID": ro_build_id,
            "INCREMENTAL": ro_build_version_incremental,
            "TYPE": ro_build_type,
            "TAGS": ro_build_tags,
            "SECURITY_PATCH": ro_build_version_security_patch,
            # "BOARD": ro_product_board,
            # "HARDWARE": ro_product_hardware,
            "DEVICE_INITIAL_SDK_INT": ro_product_first_api_level
        }

        # Play Integrity Fork
        if module_flavor == 'playintegrityfork':
            # Common in Play Integrity Fork (v4 and newer)
            # donor_data["INCREMENTAL"] = ro_build_version_incremental
            # donor_data["TYPE"] = ro_build_type
            # donor_data["TAGS"] = ro_build_tags
            # donor_data["RELEASE"] = ro_build_version_release
            # donor_data["DEVICE_INITIAL_SDK_INT"] = ro_product_first_api_level
            # donor_data["ID"] = ro_build_id

            # v5 or newer
            if module_versionCode >= 5000 and module_flavor != 'trickystore':
                donor_data["*api_level"] = ro_product_first_api_level
                donor_data["*.security_patch"] = ro_build_version_security_patch
                donor_data["*.build.id"] = ro_build_id
                if module_versionCode <= 7000:
                    donor_data["VERBOSE_LOGS"] = "0"
            if module_versionCode > 9000 and module_flavor != 'trickystore':
                spoofBuild_value = config.pif.get('spoofBuild', True)
                donor_data["spoofBuild"] = "1" if spoofBuild_value else "0"
                spoofProps_value = config.pif.get('spoofProps', False)
                donor_data["spoofProps"] = "1" if spoofProps_value else "0"
                spoofProvider_value = config.pif.get('spoofProvider', False)
                donor_data["spoofProvider"] = "1" if spoofProvider_value else "0"
                spoofSignature_value = config.pif.get('spoofSignature', False)
                donor_data["spoofSignature"] = "1" if spoofSignature_value else "0"
                spoofVendingSdk_value = config.pif.get('spoofVendingSdk', False)
                donor_data["spoofVendingSdk"] = "1" if spoofVendingSdk_value else "0"
                spoofVendingFinger_value = config.pif.get('spoofVendingFinger', False)
                donor_data["spoofVendingFinger"] = "1" if spoofVendingFinger_value else "0"
            if module_versionCode > 7000 and module_flavor != 'trickystore':
                donor_data["verboseLogs"] = "0"
            # donor_data["*.vndk_version"] = ro_vndk_version

            # Discard keys with empty values if the flag is set
            modified_donor_data = {key: value for key, value in donor_data.items() if value != ""}

        # Chit's module and other forks
        elif module_flavor == 'playintegrityfix':
            donor_data["FIRST_API_LEVEL"] = ro_product_first_api_level
            donor_data["BUILD_ID"] = ro_build_id
            donor_data["VNDK_VERSION"] = ro_vndk_version
            donor_data["FORCE_BASIC_ATTESTATION"] = "true"
            # donor_data["KERNEL"] = "Goolag-perf"

            # No discard keys with empty values on chit's module
            modified_donor_data = donor_data
        else:
            modified_donor_data = donor_data

        # Keep unknown props if the flag is set
        if keep_all:
            for key, value in the_dict.items():
                if key not in modified_donor_data:
                    modified_donor_data[key] = value

        if not keep_all:
            filtered_data = {}
            for key, value in modified_donor_data.items():
                if value:
                    filtered_data[key] = value
            modified_donor_data = filtered_data

        if not sort_data:
            return json.dumps(modified_donor_data, indent=4)
        sorted_donor_data = dict(sorted(modified_donor_data.items()))
        return json.dumps(sorted_donor_data, indent=4)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in function process_dict.")
        traceback.print_exc()
        return ''


# ============================================================================
#                               Function detect_encoding
# ============================================================================
def detect_encoding(filename):
    try:
        with open(filename, 'rb') as file:
            result = chardet.detect(file.read())
        return result['encoding']
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in detect_encoding function")
        traceback.print_exc()


# ============================================================================
#                               Function process_pi_xml_piac
# ============================================================================
def process_pi_xml_piac(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_string = file.read()

        # Parse the XML string
        root = ET.fromstring(xml_string)

        # Specify the resource-ids to identify the nodes of interest
        resource_ids_list = [
            'gr.nikolasspyr.integritycheck:id/basic_integrity_icon',
            'gr.nikolasspyr.integritycheck:id/device_integrity_icon',
            'gr.nikolasspyr.integritycheck:id/strong_integrity_icon'
        ]

        # Check if the XML contains the specific string
        if 'The calling app is making too many requests to the API' in xml_string:
            return "Quota Reached.\nPlay Integrity API Checker\nis making too many requests to the Google API."

        # Print the 'content-desc' values along with a modified version of the resource-id
        result = ''
        for resource_id in resource_ids_list:
            nodes = root.findall(f'.//node[@resource-id="{resource_id}"]')
            for node in nodes:
                value = node.get('content-desc', '')
                modified_resource_id = resource_id.replace('gr.nikolasspyr.integritycheck:id/', '').replace('_icon', '')
                result += f"{modified_resource_id}:\t{value}\n"
        if result == '':
            return -1
        debug(result)
        return result
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_piac function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function process_pi_xml_spic
# ============================================================================
def process_pi_xml_spic(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_content = file.read()

        # Check if the XML contains the specific string
        if 'Integrity API error (-8)' in xml_content:
            return "Quota Reached.\nSimple Play Integrity Checker\nis making too many requests to the Google API."

        # Find the position of "Play Integrity Result:"
        play_integrity_result_pos = xml_content.find("Play Integrity Result:")

        # If "Play Integrity Result:" is found, continue searching for index="3"
        if play_integrity_result_pos != -1:
            index_3_pos = xml_content.find('index="3"', play_integrity_result_pos)

            # If index="3" is found, extract the value after it
            if index_3_pos != -1:
                # Adjust the position to point at the end of 'index="3"' and then get the next value between double quotes.
                index_3_pos += len('index="3"')
                value_start_pos = xml_content.find('"', index_3_pos) + 1
                value_end_pos = xml_content.find('"', value_start_pos)
                value_after_index_3 = xml_content[value_start_pos:value_end_pos]
                debug(value_after_index_3)
                if value_after_index_3 == "NO_INTEGRITY":
                    result = "[✗] [✗] [✗]"
                elif value_after_index_3 == "MEETS_BASIC_INTEGRITY":
                    result = "[✓] [✗] [✗]"
                elif value_after_index_3 == "MEETS_DEVICE_INTEGRITY":
                    result = "[✓] [✓] [✗]"
                elif value_after_index_3 == "MEETS_STRONG_INTEGRITY":
                    result = "[✓] [✓] [✓]"
                elif value_after_index_3 == "MEETS_VIRTUAL_INTEGRITY":
                    result = "[o] [o] [o]"
                return f"{result} {value_after_index_3}"
            else:
                print("Error")
                return -1
        else:
            print("'Play Integrity Result:' not found")
            return -1
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_spic function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function process_pi_xml_aic
# ============================================================================
def process_pi_xml_aic(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_content = file.read()

        # Check if the XML contains the specific string
        if 'Integrity API error' in xml_content:
            return "Quota Reached.\nAndroid Integrity Checker\nis making too many requests to the Google API."

        # Find the position of "Play Integrity Result:"
        device_recognition_verdict_pos = xml_content.find("Device recognition verdict")

        # If "Device recognition verdict" is found, continue searching for index="3"
        if device_recognition_verdict_pos != -1:
            index_6_pos = xml_content.find('index="6"', device_recognition_verdict_pos)

            # If index="6" is found, extract the value after it
            if index_6_pos != -1:
                # Adjust the position to point at the end of 'index="3"' and then get the next value between double quotes.
                index_6_pos += len('index="6"')
                value_start_pos = xml_content.find('"', index_6_pos) + 1
                value_end_pos = xml_content.find('"', value_start_pos)
                value_after_index_6 = xml_content[value_start_pos:value_end_pos]
                debug(value_after_index_6)
                result = ''
                if 'MEETS_BASIC_INTEGRITY' in value_after_index_6:
                    result += '[✓]'
                else:
                    result += '[✗]'

                if 'MEETS_DEVICE_INTEGRITY' in value_after_index_6:
                    result += ' [✓]'
                else:
                    result += ' [✗]'

                if 'MEETS_STRONG_INTEGRITY' in value_after_index_6:
                    result += ' [✓]'
                else:
                    result += ' [✗]'

                return f"{result}\n{value_after_index_6}"
            else:
                print("Error")
                return -1
        else:
            print("'Play Integrity Result:' not found")
            return -1
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_spic function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function process_pi_xml_tb
# ============================================================================
def process_pi_xml_tb(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_content = file.read()

        # Find the position of "Play Integrity Result:"
        play_integrity_result_pos = xml_content.find("Result Play integrity")

        # If "Result Play integrity" is found, continue searching for index="3"
        if play_integrity_result_pos != -1:
            basic_integrity_pos = xml_content.find('"Basic integrity"', play_integrity_result_pos)

            # If "Basic integrity" is found, continue looking for text=
            if basic_integrity_pos != -1:
                # find next text= position
                basic_integrity_result_pos = xml_content.find('text=', basic_integrity_pos)

                # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                basic_integrity_result_pos += len('text=')

                value_start_pos = xml_content.find('"', basic_integrity_result_pos) + 1
                value_end_pos = xml_content.find('"', value_start_pos)
                basic_integrity = xml_content[value_start_pos:value_end_pos]

                device_integrity_pos = xml_content.find('"Device integrity"', value_end_pos)
                # If "Device integrity" is found, continue looking for text=
                if device_integrity_pos != -1:
                    # find next text= position
                    device_integrity_result_pos = xml_content.find('text=', device_integrity_pos)

                    # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                    device_integrity_result_pos += len('text=')

                    value_start_pos = xml_content.find('"', device_integrity_result_pos) + 1
                    value_end_pos = xml_content.find('"', value_start_pos)
                    device_integrity = xml_content[value_start_pos:value_end_pos]


                    strong_integrity_pos = xml_content.find('"Strong integrity"', value_end_pos)
                    # If "Device integrity" is found, continue looking for text=
                    if strong_integrity_pos != -1:
                        # find next text= position
                        strong_integrity_result_pos = xml_content.find('text=', strong_integrity_pos)

                        # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                        strong_integrity_result_pos += len('text=')

                        value_start_pos = xml_content.find('"', strong_integrity_result_pos) + 1
                        value_end_pos = xml_content.find('"', value_start_pos)
                        strong_integrity = xml_content[value_start_pos:value_end_pos]

                    result = f"Basic integrity:  {basic_integrity}\n"
                    result += f"Device integrity: {device_integrity}\n"
                    result += f"Strong integrity: {strong_integrity}\n"

                    debug(result)
                    return result
            else:
                print("Error")
                return -1
        else:
            print("'Result Play integrity' not found")
            return -1
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_tb function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function process_pi_xml_ps
# ============================================================================
def process_pi_xml_ps(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_content = file.read()

        # Find the position of text="Labels:
        labels_pos = xml_content.find('text="Labels:')

        # If found
        if labels_pos != -1:

            # Adjust the position to point at the end of 'text=' and then get the next value between [ ].
            labels_pos += len('text="Labels:')

            value_start_pos = xml_content.find('[', labels_pos) + 1
            value_end_pos = xml_content.find(']', value_start_pos)
            result = xml_content[value_start_pos:value_end_pos]
            debug(result)
            return result
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_ps function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function process_pi_xml_yasnac
# ============================================================================
def process_pi_xml_yasnac(filename):
    try:
        encoding = detect_encoding(filename)
        with open(filename, 'r', encoding=encoding, errors="replace") as file:
            xml_content = file.read()

        # Find the position of text="Result"
        yasnac_result_pos = xml_content.find('text="Result"')

        # If found, continue searching for text="Basic integrity"
        if yasnac_result_pos != -1:
            basic_integrity_pos = xml_content.find('"Basic integrity"', yasnac_result_pos)

            # If "Basic integrity" is found, continue looking for text=
            if basic_integrity_pos != -1:
                # find next text= position
                basic_integrity_result_pos = xml_content.find('text=', basic_integrity_pos)

                # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                basic_integrity_result_pos += len('text=')

                value_start_pos = xml_content.find('"', basic_integrity_result_pos) + 1
                value_end_pos = xml_content.find('"', value_start_pos)
                basic_integrity = xml_content[value_start_pos:value_end_pos]

                cts_profile_match_pos = xml_content.find('"CTS profile match"', value_end_pos)
                # If "CTS profile match" is found, continue looking for text=
                if cts_profile_match_pos != -1:
                    # find next text= position
                    cts_profile_match_result_pos = xml_content.find('text=', cts_profile_match_pos)

                    # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                    cts_profile_match_result_pos += len('text=')

                    value_start_pos = xml_content.find('"', cts_profile_match_result_pos) + 1
                    value_end_pos = xml_content.find('"', value_start_pos)
                    cts_profile_match = xml_content[value_start_pos:value_end_pos]


                    evaluation_type_pos = xml_content.find('"Evaluation type"', value_end_pos)
                    # If "Evaluation type" is found, continue looking for text=
                    if evaluation_type_pos != -1:
                        # find next text= position
                        evaluation_type_result_pos = xml_content.find('text=', evaluation_type_pos)

                        # Adjust the position to point at the end of 'text=' and then get the next value between double quotes.
                        evaluation_type_result_pos += len('text=')

                        value_start_pos = xml_content.find('"', evaluation_type_result_pos) + 1
                        value_end_pos = xml_content.find('"', value_start_pos)
                        evaluation_type = xml_content[value_start_pos:value_end_pos]

                    result = f"Basic integrity:   {basic_integrity}\n"
                    result += f"CTS profile match: {cts_profile_match}\n"
                    result += f"Evaluation type:   {evaluation_type}\n"

                    debug(result)
                    return result
            else:
                print("Error")
                return -1
        else:
            print("'Result' not found")
            return -1
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in process_pi_xml_yasnac function")
        traceback.print_exc()
        return -1


# ============================================================================
#                               Function get_xiaomi_apk
# ============================================================================
def get_xiaomi_apk(filename):
    try:
        xiaomi_pifs = get_xiaomi()
        # Fetch RSS feed and extract the latest link
        print("Checking for latest xiaomi apk link ...")
        response = request_with_fallback(method='GET', url=XIAOMI_URL)

        latest_link = response.text.split('<link>')[2].split('</link>')[0]
        print(f"Xiaomi apk link: {latest_link}")
        match = re.search(r'([^/]+\.apk)', latest_link)
        value = None
        if match:
            apk_name = match[1]
            key = os.path.splitext(apk_name)[0]
            value = xiaomi_pifs.get(key)

        if not value:
            print("Downloading xiaomi apk ...")
            download_file(url=latest_link, filename=filename)
        else:
            print("No new Xiaomi update!")
        return key
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_xiaomi_apk function")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function extract_from_zip
# ============================================================================
def extract_from_zip(zip_path, to_extract, extracted_file_path, quiet=False):
    try:
        print(f"Extracting {to_extract} from {zip_path}...")
        if quiet:
            with contextlib.suppress(Exception):
                with zipfile.ZipFile(zip_path, "r") as archive:
                    archive.extract(to_extract, extracted_file_path)
        else:
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extract(to_extract, extracted_file_path)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in extract_from_zip function")
        traceback.print_exc()


# ============================================================================
#                               Function axml2xml
# ============================================================================
def axml2xml(inputfile, outputfile=None):
    try:
        print(f"Decoding extracted xml file: {inputfile} ...")
        buff = ""
        if path.exists(inputfile):
            ap = apk.AXMLPrinter(open(inputfile, "rb").read())
            if ap is None:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to parse the AXML file {inputfile}.")
                return
            # Check if the buffer is empty (happens for Android packages binary format)
            if not ap.get_buff():
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to decode {inputfile} - unsupported format.")
                return
            buff = ap.get_xml_obj().toprettyxml()
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: XML input file {inputfile} is not found.")
            return

        if outputfile:
            with open(outputfile, "w") as fd:
                fd.write( buff )
        return(buff)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in axml2xml function")
        traceback.print_exc()


# ============================================================================
#                               Function xiaomi_xml_to_json
# ============================================================================
def xiaomi_xml_to_json(decoded_xml, json_path=None):
    # sourcery skip: use-dictionary-union
    try:
        print(f"Extracting pif data from {decoded_xml} ...")
        # Parse the XML string
        root = ET.fromstring(decoded_xml)

        # Extract key-value pairs under android.os.Build
        build_data = {}
        build_class = root.find(".//class[@name='android.os.Build']")
        if build_class:
            for field in build_class.iter("field"):
                field_name = field.get("name")
                field_value = field.get("value")
                build_data[field_name] = field_value

        # Extract key-value pairs under android.os.Build$VERSION
        version_data = {}
        version_class = root.find(".//class[@name='android.os.Build$VERSION']")
        if version_class:
            for field in version_class.iter("field"):
                field_name = field.get("name")
                field_value = field.get("value")
                version_data[field_name] = field_value

        # Flatten the key-value pairs
        flattened_data = {**build_data, **version_data}
        # flattened_data = build_data | version_data

        # Save the data as JSON
        if json_path:
            with open(json_path, "w") as json_file:
                json.dump(flattened_data, json_file, indent=4)

        return json.dumps(flattened_data, indent=4)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in xiaomi_xml_to_json function")
        traceback.print_exc()


# ============================================================================
#                               Function get_xiaomi_pif
# ============================================================================
def get_xiaomi_pif():  # sourcery skip: move-assign
    try:
        xiaomi_pifs = get_xiaomi()
        config_path = get_config_path()
        tmp_dir_full = os.path.join(config_path, 'tmp')
        xiaomi_dir_full = os.path.join(config_path, 'xiaomi')
        xiaomi_apk = os.path.join(tmp_dir_full, 'xiaomi.apk')
        to_extract = "res/xml/inject_fields.xml"

        # download apk if we need to download
        key = get_xiaomi_apk(xiaomi_apk)
        xiaomi_axml = os.path.join(xiaomi_dir_full, f"{key}")
        xiaomi_xml = os.path.join(xiaomi_dir_full, f"{key}.xml")
        xiaomi_json = os.path.join(xiaomi_dir_full, f"{key}.json")
        if key in xiaomi_pifs:
            pif_object = xiaomi_pifs.get(key)
            if pif_object is not None:
                pif_value = pif_object.get("pif")
                if pif_value is not None:
                    print("Xiaomi Pif:")
                    print(json.dumps(pif_value, indent=4))
                    return json.dumps(pif_value, indent=4)
            del xiaomi_pifs[key]

        # Extract res/xml/inject_fields.xml
        if path.exists(xiaomi_apk):
            extract_from_zip(xiaomi_apk, to_extract, xiaomi_axml)
            xiaomi_pifs.setdefault(key, {})["axml_path"] = xiaomi_axml
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Xiaomi download failed.")

        # Decode xml
        if path.exists(xiaomi_axml):
            xiaomi_xml_content = axml2xml(os.path.join(xiaomi_axml, to_extract), xiaomi_xml)
            xiaomi_pifs.setdefault(key, {})["xml_path"] = xiaomi_xml
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Xiaomi axml not found")

        # Extract the build fields and convert to json
        xiaomi_json = xiaomi_xml_to_json(xiaomi_xml_content, xiaomi_json)
        if xiaomi_json:
            xiaomi_pifs.setdefault(key, {})["pif"] = json.loads(xiaomi_json)
            set_xiaomi(xiaomi_pifs)

            print("Caching data ...")
            with open(get_xiaomi_file_path(), "w", encoding='ISO-8859-1', errors="replace") as f:
                # Write the dictionary to the file in JSON format
                json.dump(xiaomi_pifs, f, indent=4)
        return xiaomi_json

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_xiaomi_pif function")
        traceback.print_exc()


# ============================================================================
#                               Function get_freeman_pif
# ============================================================================
def get_freeman_pif(abi_list=None):
    print("\n===== PIFS Random Profile/Fingerprint Picker =====\nCopyright (C) MIT License 2023 Nicholas Bissell (TheFreeman193)")

    try:
        config_path = get_config_path()
        tmp_dir_full = os.path.join(config_path, 'tmp')
        freeman_dir_full = os.path.join(config_path, 'TheFreeman193_JSON')
        zip_file = os.path.join(tmp_dir_full, 'PIFS.zip')

        if not os.path.exists(freeman_dir_full):
            if not os.path.exists(zip_file):
                print("Downloading profile/fingerprint repo from GitHub...")
                download_file(FREEMANURL, zip_file)
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            # Move the extracted 'JSON' directory contents directly to the target directory
            json_contents_path = os.path.join(temp_dir, "PIFS-main", "JSON")
            shutil.move(json_contents_path, freeman_dir_full)
            # Remove the temporary directory
            shutil.rmtree(temp_dir)

        if abi_list:
            if abi_list == "arm64-v8a":
                abi_list = "arm64-v8a,armeabi-v7a,armeabi"
            print(f"Will use profile/fingerprint with ABI list '{abi_list}'")
            file_list = [os.path.join(root, file) for root, dirs, files in os.walk(f"{freeman_dir_full}/{abi_list}") for file in files]
        else:
            print("Couldn't detect ABI list. Will use profile/fingerprint from anywhere.")
            file_list = [os.path.join(root, file) for root, dirs, files in os.walk(f"{freeman_dir_full}") for file in files]

            if not file_list:
                print("Couldn't find any profiles/fingerprints. Is the JSON directory empty?")
                return

        f_count = len(file_list)
        debug(f"Matching json count: {f_count}")
        if f_count == 0:
            print("Couldn't parse JSON file list!")
            return

        print("Picking a random profile/fingerprint...")
        random_fp_num = random.randint(1, f_count)
        rand_fp = file_list[random_fp_num - 1]

        print(f"\nRandom profile/fingerprint file: '{os.path.basename(rand_fp)}'\n")
        with open(rand_fp, "r") as file:
            json_content = json.load(file)
            return json.dumps(json_content, indent=4)

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_freeman_pif function")
        traceback.print_exc()


# ============================================================================
#                               Function get_pif_from_image
# ============================================================================
def get_pif_from_image(image_file):
    config_path = get_config_path()
    config = get_config()
    path_to_7z = get_path_to_7z()
    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = temp_dir.name
    # create props folder
    props_folder = os.path.join(config_path, "props")
    package_sig = os.path.splitext(os.path.basename(image_file))[0]
    props_path = os.path.join(props_folder, package_sig)
    if os.path.exists(props_path):
        shutil.rmtree(props_path)
    os.makedirs(props_path, exist_ok=True)

    file_to_process = image_file
    basename = ntpath.basename(image_file)
    filename, extension = os.path.splitext(basename)
    extension = extension.lower()

    # ==================================================
    # Sub Function  process_system_vendor_product_images
    # ==================================================
    def process_system_vendor_product_images():
        # process system.img
        try:
            img_archive = os.path.join(temp_dir_path, "system.img")
            if os.path.exists(img_archive):
                found_system_build_prop = check_archive_contains_file(archive_file_path=img_archive, file_to_check="build.prop", nested=False, is_recursive=False)
                if found_system_build_prop:
                    print(f"Extracting build.prop from {img_archive} ...")
                    theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{props_path}\" \"{img_archive}\" {found_system_build_prop}"
                    debug(theCmd)
                    res = run_shell2(theCmd)
                    if os.path.exists(os.path.join(props_path, found_system_build_prop)):
                        os.rename(os.path.join(props_path, found_system_build_prop), os.path.join(props_path, "system-build.prop"))
                else:
                    print(f"build.prop not found in {img_archive}")
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing system.img:")
            traceback.print_exc()

        # process vendor.img
        try:
            img_archive = os.path.join(temp_dir_path, "vendor.img")
            if os.path.exists(img_archive):
                found_vendor_img_prop = check_archive_contains_file(archive_file_path=img_archive, file_to_check="build.prop", nested=False, is_recursive=False)
                if found_vendor_img_prop:
                    print(f"Extracting build.prop from {img_archive} ...")
                    theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{props_path}\" \"{img_archive}\" {found_vendor_img_prop}"
                    debug(theCmd)
                    res = run_shell2(theCmd)
                    if os.path.exists(os.path.join(props_path, found_vendor_img_prop)):
                        os.rename(os.path.join(props_path, found_vendor_img_prop), os.path.join(props_path, "vendor-build.prop"))
                else:
                    print(f"build.prop not found in {img_archive}")
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing vendor.img:")
            traceback.print_exc()

        # process product.img
        try:
            img_archive = os.path.join(temp_dir_path, "product.img")
            if os.path.exists(img_archive):
                found_product_img_prop = check_archive_contains_file(archive_file_path=img_archive, file_to_check="build.prop", nested=False, is_recursive=False)
                if found_product_img_prop:
                    print(f"Extracting build.prop from {img_archive} ...")
                    theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{props_path}\" \"{img_archive}\" {found_product_img_prop}"
                    debug(theCmd)
                    res = run_shell2(theCmd)
                    if os.path.exists(os.path.join(props_path, found_product_img_prop)):
                        os.rename(os.path.join(props_path, found_product_img_prop), os.path.join(props_path, "product-build.prop"))
                else:
                    print(f"build.prop not found in {img_archive}")
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing product.img:")
            traceback.print_exc()

    # ==================================================
    # Sub Function  check_for_system_vendor_product_imgs
    # ==================================================
    def check_for_system_vendor_product_imgs(filename):
        # check if image file is included and contains what we need
        if os.path.exists(filename):
            # extract system.img
            found_system_img = check_archive_contains_file(archive_file_path=filename, file_to_check="system.img", nested=False, is_recursive=False)
            if found_system_img:
                print(f"Extracting system.img from {filename} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{filename}\" system.img"
                debug(theCmd)
                res = run_shell2(theCmd)

            # extract vendor.img
            found_vendor_img = check_archive_contains_file(archive_file_path=filename, file_to_check="vendor.img", nested=False, is_recursive=False)
            if found_vendor_img:
                print(f"Extracting system.img from {filename} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{filename}\" vendor.img"
                debug(theCmd)
                res = run_shell2(theCmd)

            # extract product.img
            found_product_img = check_archive_contains_file(archive_file_path=filename, file_to_check="product.img", nested=False, is_recursive=False)
            if found_product_img:
                print(f"Extracting system.img from {filename} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{filename}\" product.img"
                debug(theCmd)
                res = run_shell2(theCmd)

    try:
        # .img file
        if extension == ".img":
            if filename in ["system", "vendor", "product"]:
                # copy the image file to the temp directory
                shutil.copy2(file_to_process, temp_dir_path)
            else:
                shutil.copy2(file_to_process, os.path.join(temp_dir_path, "system.img"))
            process_system_vendor_product_images()
            return props_path

        found_flash_all_bat = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="flash-all.bat", nested=False)
        if found_flash_all_bat:
            found_flash_all_sh = check_archive_contains_file(archive_file_path=file_to_process, file_to_check="flash-all.sh", nested=False)

        if found_flash_all_bat and found_flash_all_sh:
            # -----------------------------
            # Pixel factory file
            # -----------------------------
            package_sig = found_flash_all_bat.split('/')[0]
            if not package_sig:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract package signature from {found_flash_all_bat}")
                return
            package_dir_full = os.path.join(temp_dir_path, package_sig)
            image_file_path = os.path.join(package_dir_full, f"image-{package_sig}.zip")
            # Unzip the factory image
            debug(f"Unzipping Image: {file_to_process} into {package_dir_full} ...")
            theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{file_to_process}\""
            debug(theCmd)
            res = run_shell2(theCmd)
            if res and isinstance(res, subprocess.CompletedProcess):
                debug(f"Return Code: {res.returncode}")
                debug(f"Stdout: {res.stdout}")
                debug(f"Stderr: {res.stderr}")
                if res.returncode != 0:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {file_to_process}")
                    print("Aborting ...\n")
                    return
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {file_to_process}")
                print("Aborting ...\n")
                return

            # check if image file is included and contains what we need
            if os.path.exists(image_file_path):
                check_for_system_vendor_product_imgs(image_file_path)
                process_system_vendor_product_images()
                return props_path

        elif check_zip_contains_file(file_to_process, "payload.bin", config.low_mem):
            # -----------------------------
            # Firmware with payload.bin
            # -----------------------------
            print("Detected a firmware, with payload.bin")
            # extract the payload.bin into a temporary directory
            print(f"Extracting payload.bin from {file_to_process} ...")
            theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{file_to_process}\" payload.bin"
            debug(f"{theCmd}")
            res = run_shell(theCmd)
            if res and isinstance(res, subprocess.CompletedProcess) and res.returncode != 0:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract payload.bin.")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
                print("Aborting ...\n")
                return

            payload_file_path = os.path.join(temp_dir_path, "payload.bin")
            if os.path.exists(payload_file_path):
                extract_payload(payload_file_path, out=temp_dir_path, diff=False, old='old', images='system,vendor,product')
                process_system_vendor_product_images()
                return props_path
            return

        elif check_zip_contains_file(file_to_process, "servicefile.xml", config.low_mem):
            # -----------------------------
            # Motorola Firmware
            # -----------------------------
            sparse_chunk_pattern = "system.img_sparsechunk.*"
            sparse_chunks = check_file_pattern_in_zip_file(file_to_process, sparse_chunk_pattern, return_all_matches=True)
            if sparse_chunks:
                print("Detected a Motorola firmware")
                # # Extract sparse chunks
                # for chunk in sparse_chunks:
                #     print(f"Extracting {chunk} from {file_to_process} ...")
                #     theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{file_to_process}\" \"{chunk}\""
                #     debug(theCmd)
                #     res = run_shell2(theCmd)
                #     if res.returncode != 0:
                #         print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {chunk}.")
                #         print(f"Return Code: {res.returncode}")
                #         print(f"Stdout: {res.stdout}")
                #         print(f"Stderr: {res.stderr}")
                #         print("Aborting ...\n")
                #         return
                # # Combine sparse chunks
                # combined_sparse_path = os.path.join(temp_dir_path, "combined_system.img")
                # with open(combined_sparse_path, 'wb') as combined_file:
                #     for chunk in sparse_chunks:
                #         chunk_path = os.path.join(temp_dir_path, chunk)
                #         with open(chunk_path, 'rb') as chunk_file:
                #             combined_file.write(chunk_file.read())
                # # converting to raw image
                # raw_image_path = os.path.join(temp_dir_path, "system.img")
                # subprocess.run(["simg2img", combined_sparse_path, raw_image_path], check=True)

        elif check_zip_contains_file(file_to_process, "system.img", config.low_mem):
            check_for_system_vendor_product_imgs(file_to_process)
            process_system_vendor_product_images()
            return props_path

        elif check_zip_contains_file(file_to_process, "vendor.img", config.low_mem):
            check_for_system_vendor_product_imgs(file_to_process)
            process_system_vendor_product_images()
            return props_path

        elif check_zip_contains_file(file_to_process, "product.img", config.low_mem):
            check_for_system_vendor_product_imgs(file_to_process)
            process_system_vendor_product_images()
            return props_path

        else:
            found_ap = check_file_pattern_in_zip_file(file_to_process, "AP_*.tar.md5")
            if found_ap is not None and found_ap != "":
                # -----------------------------
                # Samsung firmware
                # -----------------------------
                print("Detected a Samsung firmware")

                # extract AP file
                print(f"Extracting {found_ap} from {image_file} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{image_file}\" {found_ap}"
                debug(theCmd)
                res = run_shell2(theCmd)
                if res and isinstance(res, subprocess.CompletedProcess):
                    debug(f"Return Code: {res.returncode}")
                    debug(f"Stdout: {res.stdout}")
                    debug(f"Stderr: {res.stderr}")
                    if res.returncode != 0:
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {found_ap}.")
                        print("Aborting ...\n")
                        return
                else:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {found_ap}.")
                    print("Aborting ...\n")
                    return
                image_file_path = os.path.join(temp_dir_path, found_ap)
                if not os.path.exists(image_file_path):
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {image_file_path}.")
                    return
                # extract image file
                print(f"Extracting {image_file_path} ...")
                theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{image_file_path}\" \"meta-data\""
                debug(theCmd)
                res = run_shell2(theCmd)
                if res and isinstance(res, subprocess.CompletedProcess):
                    debug(f"Return Code: {res.returncode}")
                    debug(f"Stdout: {res.stdout}")
                    debug(f"Stderr: {res.stderr}")
                    if res.returncode != 0:
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract meta-data.")
                        print("Aborting ...\n")
                        return
                else:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract meta-data.")
                    print("Aborting ...\n")
                    return

                # get a file listing
                file_list = get_file_list_from_directory(temp_dir_path)
                found_fota_zip = False
                for file_path in file_list:
                    if "fota.zip" in file_path:
                        found_fota_zip = True
                        break

                if found_fota_zip:
                    # extract fota.zip
                    print(f"Extracting fota.zip from {image_file_path} ...")
                    theCmd = f"\"{path_to_7z}\" x -bd -y -o\"{temp_dir_path}\" \"{file_path}\" \"SYSTEM\" \"VENDOR\""
                    debug(theCmd)
                    res = run_shell2(theCmd)

                    source_path = os.path.join(temp_dir_path, "VENDOR", "build.prop")
                    destination_path = os.path.join(props_path, "system-build.prop")
                    if os.path.exists(source_path):
                        shutil.copy(source_path, destination_path)

                    source_path = os.path.join(temp_dir_path, "SYSTEM", "build.prop")
                    destination_path = os.path.join(props_path, "vendor-build.prop")
                    if os.path.exists(source_path):
                        shutil.copy(source_path, destination_path)

                    return props_path

                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unexpected image layout for {file_to_process}")
                return

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while processing ota/firmware file:")
        traceback.print_exc()
    finally:
        temp_dir.cleanup()


# ============================================================================
#                               Function extract_motorola_image
# ============================================================================
def extract_motorola_image(moto_img_path, output_img_path):
    """
    Extracts a Motorola image file, skipping its custom header.

    :param moto_img_path: Path to the Motorola image file.
    :param output_img_path: Path where the extracted raw image will be saved.
    """
    # Motorola header signature for identification
    moto_header_signature = b"MOTO\x13W\x9b\x00MOT_PIV_FULL256"
    header_length = len(moto_header_signature)  # Adjust based on actual header length

    try:
        with open(moto_img_path, 'rb') as moto_file:
            # check for the Motorola header
            header = moto_file.read(header_length)
            if header.startswith(moto_header_signature):
                print("Motorola image detected, proceeding with extraction...")
                # Skip the header to get to the actual image data
                # moto_file.seek(header_length, os.SEEK_SET)  # Uncomment if additional bytes need to be skipped
                # Read the rest of the file
                image_data = moto_file.read()
                # Save the extracted data to a new file
                with open(output_img_path, 'wb') as output_file:
                    output_file.write(image_data)
                print(f"Motorola Extraction complete. Raw image saved to {output_img_path}")
            else:
                print("File does not have the expected Motorola header.")
    except IOError as e:
        print(f"Error opening or reading file: {e}")


# ============================================================================
#                               Function get_file_list_from_directory
# ============================================================================
def get_file_list_from_directory(directory):
    try:
        file_list = []
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_list.append(os.path.join(dirpath, filename))
        return file_list
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_file_list_from_directory function")
        traceback.print_exc()


# ============================================================================
#                               Function patch_binary_file
# ============================================================================
def patch_binary_file(file_path, hex_offset, text, output_file_path=None):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        # convert to decimal
        offset = int(hex_offset, 16)
        # Patch the data
        data = data[:offset] + text.encode() + data[offset + len(text):]

        if output_file_path is None:
            output_file_path = file_path

        with open(output_file_path, 'wb') as f:
            f.write(data)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in patch_binary_file function")
        traceback.print_exc()


# ============================================================================
#                 Function bootloader_issue_message
# ============================================================================
def bootloader_issue_message():
    print("ℹ️ This issue is most likely related to communication between your device and your computer.")
    print("Please ensure that you have installed the latest Google USB Drivers in both adb and bootloader (fastboot) modes.")
    print("If the problem persists, try using a different USB cable or port.")
    print("USB 2.0 ports are reportedly more stable than USB 3.0 ports.\n")


# ============================================================================
#                 Function download_ksu_latest_release_asset
# ============================================================================
def download_ksu_latest_release_asset(user, repo, asset_name=None, anykernel=True, custom_kernel=None, include_prerelease = False, latest_any=False, version_choice=False, get_all=False):
    try:
        # For ShirkNeko and other custom kernels that might use pre-releases, check pre-releases first
        include_prerelease = custom_kernel in ['ShirkNeko', 'MiRinFork', 'WildKernels']

        if asset_name:
            look_for = asset_name
        else:
            look_for = "[all entries]"

        debug(f"Fetching latest release from {user}/{repo} matching {look_for} (include_prerelease: {include_prerelease})...")
        wx.Yield()
        response_data = get_gh_release_object(user=user, repo=repo, include_prerelease=include_prerelease, latest_any=latest_any)
        if response_data is None:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch release data from {user}/{repo}")
            return None

        assets = response_data.get('assets', [])
        if not asset_name:
            return assets

        # Split the asset_name into parts
        parts = asset_name.split('-')
        base_name = parts[0]
        base_name = f"{base_name}"
        version_parts = parts[1].split('.')
        fixed_version = '.'.join(version_parts[:-1])
        variable_version = int(version_parts[-1])

        # Prepare the regular expression pattern
        if anykernel:
            if get_all:
                version_choice = True
                pattern = re.compile(rf"^.*\.zip$")
                debug(f"Using pattern for all assets of {custom_kernel}: {pattern.pattern}")
            elif custom_kernel:
                if custom_kernel in ["MiRinFork", 'ShirkNeko']:
                    # MiRinFork format: android14-6.1.145-2025-08-AnyKernel3.zip
                    # ShirkNeko format:  android14-6.1.124-2025-02-AnyKernel3.zip
                    pattern = re.compile(rf"^{base_name}-{fixed_version}\.([0-9]+)-.*-AnyKernel3\.zip$")
                    debug(f"Using pattern for {custom_kernel}: {pattern.pattern}")
                elif custom_kernel == "WildKernels":
                    # Latest format: 6.1.57-android14-2023-12-Normal-AnyKernel3.zip
                    #                6.1.57-android14-2024-01-Bypass-AnyKernel3.zip
                    # version_choice = True
                    pattern = re.compile(rf"^{fixed_version}\.([0-9]+)-{base_name}-[0-9]{{4}}-[0-9]{{2}}-(?:Normal|Bypass)-AnyKernel3\.zip$")
                    debug(f"Using pattern for {custom_kernel}: {pattern.pattern}")
                else:
                    # Fallback pattern for other custom kernels
                    pattern = re.compile(rf"^{base_name}-{fixed_version}\.([0-9]+)-.*-AnyKernel3\.zip$")
                    debug(f"Using fallback pattern for {custom_kernel}: {pattern.pattern}")
            else:
                pattern = re.compile(rf"^AnyKernel3-{base_name}-{fixed_version}\.([0-9]+)(_.*|)\.zip$")
                debug(f"Using AnyKernel pattern: {pattern.pattern}")
        else:
            pattern = re.compile(rf"^{base_name}-{fixed_version}\.([0-9]+)(_.*|)-boot\.img\.gz$")
            debug(f"Using boot.img pattern: {pattern.pattern}")

        # Find the best match based on configuration
        config = get_config()
        selection_mode = getattr(config, 'ksu_asset_selection_mode', 0)
        if version_choice:
            selection_mode = 2  # Force user selectable mode

        best_match = None
        best_version = -1
        matching_assets = []
        fallback_match = None
        fallback_version = float('inf')
        all_matching_assets = []

        # For WildKernels, track Normal and Bypass builds separately for prioritization
        normal_assets = []
        bypass_assets = []

        for asset in assets:
            match = pattern.match(asset['name'])
            if match:
                # Handle case when get_all is True and pattern has no capture groups
                if get_all and custom_kernel:
                    # Default version for get_all mode
                    asset_version = 0
                elif len(match.groups()) > 0:
                    asset_version = int(match[1])
                else:
                    asset_version = 0
                matching_assets.append((asset['name'], asset_version))
                asset_info = {
                    'asset': asset,
                    'version': asset_version
                }
                all_matching_assets.append(asset_info)

                # For WildKernels, categorize by build type for prioritization
                if custom_kernel == "WildKernels":
                    if '-Normal-' in asset['name']:
                        normal_assets.append(asset_info)
                    elif '-Bypass-' in asset['name']:
                        bypass_assets.append(asset_info)

        # Create prioritized asset list: Normal first, then Bypass, then all others
        prioritized_assets = normal_assets + bypass_assets + all_matching_assets

        # Process assets in priority order
        for asset_info in prioritized_assets:
            asset = asset_info['asset']
            asset_version = asset_info['version']

            # First priority: find highest version <= requested version
            if asset_version <= variable_version and asset_version > best_version:
                best_match = asset
                best_version = asset_version
                if asset_version == variable_version and selection_mode == 0:
                    break

            # Fallback: track lowest version > requested version
            elif asset_version > variable_version and asset_version < fallback_version:
                fallback_match = asset
                fallback_version = asset_version

        # Apply selection logic based on mode
        if selection_mode == 1:  # Highest Available
            if all_matching_assets:
                highest_asset = max(all_matching_assets, key=lambda x: x['version'])
                best_match = highest_asset['asset']
                best_version = highest_asset['version']
                print(f"ℹ️ Using highest available version: {best_version}")
        elif selection_mode == 2:  # User selectable
            if all_matching_assets:
                try:
                    # Sort assets by version (highest first) for better display
                    sorted_assets = sorted(all_matching_assets, key=lambda x: x['version'], reverse=True)
                    asset_list = [item['asset'] for item in sorted_assets]

                    # Determine suggested asset (current logic)
                    suggested_asset = best_match if best_match else fallback_match

                    selected_asset = show_ksu_asset_selector(
                        parent=None,
                        assets=asset_list,
                        title="Select KernelSU Asset",
                        message=f"Multiple KernelSU assets found for {base_name}-{fixed_version}.x\nRequested version: {variable_version}",
                        suggested_asset=suggested_asset,
                        initial_filter=f"{fixed_version}."
                    )

                    if selected_asset:
                        best_match = selected_asset
                        # Extract version from selected asset
                        match = pattern.match(selected_asset['name'])
                        if match:
                            if len(match.groups()) > 0:
                                best_version = int(match[1])
                            else:
                                best_version = 0
                        print(f"ℹ️ User selected version: {best_version}")
                    else:
                        print("ℹ️ User cancelled selection, using suggested asset, aborting ...")
                        return None
                except ImportError:
                    print("⚠️ Asset selector not available, falling back to default selection")

        wx.Yield()
        # Default mode (0) or fallback logic
        if selection_mode == 0 or (selection_mode == 2 and not best_match):
            # If no version <= requested found, use the closest higher version
            if not best_match and fallback_match:
                best_match = fallback_match
                best_version = fallback_version
                print(f"⚠️ No version <= {variable_version} found, using closest higher version: {fallback_version}")

        if matching_assets:
            print(f"Assets matched {len(matching_assets)} assets:")
            for name, version in matching_assets:
                print(f"  - {name} (version: {version})")
                wx.Yield()

        if best_match:
            print(f"Selected best match KernelSU: {best_match['name']}")
            download_file(best_match['browser_download_url'])
            print(f"Downloaded {best_match['name']}")
            return best_match['name']
        else:
            print(f"⚠️ Automatic good match for asset {asset_name} not found in the latest release of {user}/{repo}")
            print("ℹ️ To see all available assets, enable the checkbox [Show all assets including non-matching ones] when selecting kernel flavor.\n")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_ksu_latest_release_asset function")
        traceback.print_exc()


# ============================================================================
#                 Function download_gh_pre_release_asset_regex
# ============================================================================
def download_gh_pre_release_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=True, latest_any=False)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=True)
        if asset:
            print(f"Downloaded asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest pre-release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_gh_pre_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function download_gh_latest_release_asset_regex
# ============================================================================
def download_gh_latest_release_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=False, latest_any=False)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return None
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=True)
        if asset:
            print(f"Downloaded asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_gh_latest_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function download_gh_latest_any_asset_regex
# ============================================================================
def download_gh_latest_any_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=True, latest_any=True)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=True)
        if asset:
            print(f"Downloaded asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest pre-release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_gh_pre_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function get_gh_pre_release_asset_regex
# ============================================================================
def get_gh_pre_release_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=True, latest_any=False)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=False)
        if asset:
            print(f"Found asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest pre-release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_pre_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function get_gh_latest_release_asset_regex
# ============================================================================
def get_gh_latest_release_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=False, latest_any=False)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=False)
        if asset:
            print(f"Found asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_latest_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function get_gh_latest_any_asset_regex
# ============================================================================
def get_gh_latest_release_asset_regex(user, repo, asset_name_pattern):
    try:
        release_object = get_gh_release_object(user=user, repo=repo, include_prerelease=False, latest_any=True)
        if release_object is None:
            print(f"No releases found for {user}/{repo}")
            return
        asset = gh_asset_utility(release_object=release_object, asset_name_pattern=asset_name_pattern, download=False)
        if asset:
            print(f"Found asset: {asset}")
            return asset
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest release of {user}/{repo}")
            return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_latest_release_asset_regex function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function gh_asset_utility
# ============================================================================
def gh_asset_utility(release_object, asset_name_pattern, download):
    try:
        if not release_object:
            print(f"No release object provided.")
            return

        assets = release_object.get('assets', [])

        # Prepare the regular expression pattern
        pattern = re.compile(asset_name_pattern)

        # Find the best match
        best_match = None
        for asset in assets:
            match = pattern.match(asset['name'])
            if match:
                best_match = asset
                break

        if best_match:
            print(f"Found match: {best_match['name']}")
            if not download:
                return best_match['browser_download_url']
            download_file(best_match['browser_download_url'])
            print(f"Downloaded {best_match['name']}")
            return best_match['name']
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest release of the provided release object")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in gh_asset_utility function")
        traceback.print_exc()


# ============================================================================
#                   Function get_gh_latest_release_notes
# ============================================================================
def get_gh_latest_release_notes(owner, repo):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        response = requests.get(url)
        data = response.json()

        if 'body' in data:
            return data['body']
        else:
            return "# No release notes found for the latest release."
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_latest_release_notes function")
        traceback.print_exc()


# ============================================================================
#                   Function get_gh_latest_release_version
# ============================================================================
def get_gh_latest_release_version(user, repo, include_prerelease=False):
    try:
        # Get all releases
        url = f"https://api.github.com/repos/{user}/{repo}/releases"
        response = request_with_fallback(method='GET', url=url)
        releases = response.json()

        # Filter releases based on the include_prerelease flag
        if not include_prerelease:
            releases = [release for release in releases if not release['prerelease']]
        else:
            releases = [release for release in releases if release['prerelease']]

        # Get the latest release
        latest_release = releases[0] if releases else None

        if not latest_release:
            print(f"No releases found for {user}/{repo}")
            return ''

        return latest_release.get('tag_name', '')
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_latest_release_version function")
        traceback.print_exc()
        return ''


# ============================================================================
#                   Function get_gh_release_object
# ============================================================================
def get_gh_release_object(user, repo, include_prerelease=False, latest_any=False):
    try:
        # Get all releases
        url = f"https://api.github.com/repos/{user}/{repo}/releases"
        response = request_with_fallback(method='GET', url=url)
        if response.status_code != 200:
            print(f"Failed to fetch releases from {user}/{repo}. HTTP Status Code: {response.status_code}")
            return None
        releases = response.json()

        # Filter releases based on the flags
        if latest_any:
            # Don't filter - use all releases to pick the absolute latest
            filtered_releases = releases
        elif not include_prerelease:
            filtered_releases = [release for release in releases if not release['prerelease']]
        else:
            filtered_releases = [release for release in releases if release['prerelease']]

        # Get the latest release
        latest_release = filtered_releases[0] if filtered_releases else None

        if not latest_release:
            release_type = "any releases" if latest_any else ("pre-releases" if include_prerelease else "releases")
            print(f"No {release_type} found for {user}/{repo}")
            return None

        return latest_release
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_gh_release_object function")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function extract_magiskboot
# ============================================================================
def extract_magiskboot(apk_path, architecture, output_path):
    try:
        path_to_7z = get_path_to_7z()
        file_path_in_apk = f"lib/{architecture}/libmagiskboot.so"
        output_file_path = os.path.join(output_path, "magiskboot")

        cmd = f"\"{path_to_7z}\" e \"{apk_path}\" -o\"{output_path}\" -r {file_path_in_apk} -y"
        debug(cmd)
        res = run_shell2(cmd)
        if res and isinstance(res, subprocess.CompletedProcess):
            debug(f"Return Code: {res.returncode}")
            debug(f"Stdout: {res.stdout}")
            debug(f"Stderr: {res.stderr}")
            if res.returncode != 0:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract from {apk_path}")
                puml("#red:ERROR: Could not extract image;\n")
                print("Aborting ...\n")
                return
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract from {apk_path}")
            puml("#red:ERROR: Could not extract image;\n")
            print("Aborting ...\n")
            return

        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        os.rename(os.path.join(output_path, "libmagiskboot.so"), output_file_path)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in extract_magiskboot function")
        traceback.print_exc()


# ============================================================================
#                               Function request_with_fallback
# ============================================================================
def request_with_fallback(method, url, headers=None, data=None, stream=False, nocache=False):
    response = 'ERROR'
    # Initialize headers if None
    headers = headers or {}

    # Add nocache headers only when requested
    if nocache:
        headers.update({
            'Cache-Control': 'no-cache, max-age=0',
            'Pragma': 'no-cache'
        })

    try:
        if check_internet():
            with requests.Session() as session:
                response = session.request(method, url, headers=headers, data=data, stream=stream)
                response.raise_for_status()
    except requests.exceptions.SSLError:
        print(f"⚠️ WARNING! Encountered SSL certification error while connecting to: {url}")
        print("Retrying with SSL certificate verification disabled. ...")
        print("For security, you should double check and make sure your system or communication is not compromised.")
        if check_internet():
            with requests.Session() as session:
                response = session.request(method, url, headers=headers, data=data, verify=False, stream=stream)
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.Timeout:
        print("The request timed out")
    except requests.exceptions.TooManyRedirects:
        print("Too many redirects")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return response


# ============================================================================
#                               Function check_internet
# ============================================================================
def check_internet():
    url = "http://www.google.com"
    timeout = 5
    try:
        unused = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError as e:
        print("No internet connection available.")
        print(e)
    return False


# ============================================================================
#                               Function load_kb_index
# ============================================================================
def load_kb_index():
    try:
        kb_index_path = os.path.join(get_config_path(), 'kb_index.json')
        if os.path.exists(kb_index_path):
            with open(kb_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to load kb_index.json: {e}")
        return {}


# ============================================================================
#                               Function save_kb_index
# ============================================================================
def save_kb_index(kb_index):
    try:
        kb_index_path = os.path.join(get_config_path(), 'kb_index.json')
        with open(kb_index_path, 'w', encoding='utf-8') as f:
            json.dump(kb_index, f, indent=2)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to save kb_index.json: {e}")


# ============================================================================
#                               Function check_kb
# Credit to hldr4  for the original suggestion
# https://gist.github.com/hldr4/b933f584b2e2c3088bcd56eb056587f8
# ============================================================================
def check_kb(filename, force_fresh=False):
    url = "https://android.googleapis.com/attestation/status"
    headers = {
        'Cache-Control': 'no-cache, max-age=0',
        'Pragma': 'no-cache'
    }

    try:
        # Load kb_index
        config = get_config()
        if config.kb_index:
            kb_index = load_kb_index()

        # Check for cached CRL data first to avoid multiple network requests
        config_path = get_config_path()
        crl_cache_path = os.path.join(config_path, 'tmp', 'crl_cache.json')
        crl_data = None
        last_modified = 'Unknown'
        content_date = 'Unknown'
        use_cache = False

        # Check if cached file exists and is fresh (less than 15 minute old), unless force_fresh is True
        if not force_fresh and os.path.exists(crl_cache_path):
            cache_age = time.time() - os.path.getmtime(crl_cache_path)
            if cache_age < 900:  # 15 minutes
                try:
                    with open(crl_cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        crl_data = cached_data['crl_data']
                        last_modified = cached_data.get('last_modified', 'Unknown')
                        content_date = cached_data.get('content_date', 'Unknown')
                        use_cache = True
                        debug(f"Using cached CRL data (age: {cache_age:.1f} seconds)")
                except (json.JSONDecodeError, KeyError, IOError) as e:
                    debug(f"Failed to load cached CRL data: {e}")

        # If no valid cache, fetch from server
        if not use_cache:
            # Add timestamp to URL to ensure fresh data
            timestamp = int(time.time())
            cache_bust_url = f"{url}?_t={timestamp}"

            # Enhanced cache-busting headers
            fresh_headers = headers.copy()
            fresh_headers.update({
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0',
                'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
                'Accept-Encoding': 'identity'
            })

            crl = request_with_fallback(method='GET', url=cache_bust_url, headers=fresh_headers, nocache=True)
            if crl is not None and crl != 'ERROR':
                last_modified = crl.headers.get('last-modified', 'Unknown')
                content_date = crl.headers.get('date', 'Unknown')
                crl_data = crl.json()

                # Cache the data
                try:
                    cache_data = {
                        'crl_data': crl_data,
                        'last_modified': last_modified,
                        'content_date': content_date,
                        'cached_at': datetime.now().isoformat()
                    }
                    with open(crl_cache_path, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2)
                    debug("CRL data cached successfully")
                except IOError as e:
                    debug(f"Failed to cache CRL data: {e}")
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not fetch CRL from {url}")
                return ['invalid']

        # Display CRL info
        print("------------------------------------------------------------------------")
        print(f"CRL Last Modified:     {last_modified}")
        print(f"Server Response Date:  {content_date}")
        crl = crl_data

        print(f"\nChecking keybox: {filename} ...")

        # Calculate file hash for kb_index
        if config.kb_index:
            file_hash = sha1(filename)

        shadow_banned_list = SHADOW_BANNED_ISSUERS
        is_sw_signed = False
        is_google_signed = False
        is_expired = False
        expiring_soon = False
        is_revoked = False
        is_shadow_banned = False
        long_chain = False
        results = []
        ecdsa_root_ca_sn = None
        rsa_root_ca_sn = None

        # Parse keybox XML
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
        except Exception as e:
            print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not parse keybox XML {filename}")
            print(e)
            results.append('invalid')
            return results

        # 1. Validate root element is AndroidAttestation
        if root.tag != 'AndroidAttestation':
            print(f"❌ ERROR: Root element is not AndroidAttestation, found: {root.tag}")
            results.append('invalid_structure')
            return results

        # 2. Check NumberOfKeyboxes
        num_keyboxes = root.find('NumberOfKeyboxes')
        if num_keyboxes is None:
            print("❌ ERROR: Missing NumberOfKeyboxes element")
            results.append('invalid_structure')
            return results
        expected_keyboxes = int(num_keyboxes.text)
        print(f"Expected number of keyboxes: {expected_keyboxes}")

        # 3. Process each Keybox
        keyboxes = root.findall('Keybox')
        if not keyboxes:
            print("❌ ERROR: No Keybox elements found")
            results.append('invalid_structure')
            return results

        if len(keyboxes) != expected_keyboxes:
            print(f"⚠️ WARNING: NumberOfKeyboxes ({expected_keyboxes}) does not match actual keyboxes found ({len(keyboxes)})")

        k = 1
        for keybox in keyboxes:
            wx.Yield()
            device_id = keybox.get('DeviceID')
            if not device_id:
                print("❌ ERROR: Keybox missing DeviceID attribute")
                results.append('invalid_structure')
            print(f"\nProcessing Keybox {k}/{expected_keyboxes} for Device ID: {device_id}")

            if config.kb_index:
                # Initialize keybox data collection for this specific keybox
                keybox_data_collection = {}

            # 4. Verify both RSA and ECDSA algorithms are present
            required_algorithms = {'rsa', 'ecdsa'}
            found_algorithms = set()

            ecdsa_chain = 'valid'
            rsa_chain = 'valid'
            for key_element in keybox.findall('Key'):
                wx.Yield()
                algorithm = key_element.get('algorithm')
                if not algorithm:
                    print("  ❌ ERROR: Key element missing algorithm attribute")
                    continue

                # Process the Chain
                algorithm = algorithm.lower()
                print(f"\n→ Processing {algorithm} chain:")
                found_algorithms.add(algorithm)

                # 5. Check PrivateKey
                private_key = key_element.find('PrivateKey')
                if private_key is None:
                    print(f"  ❌ ERROR: No PrivateKey found for {algorithm} key")
                    results.append('missing_private_key')
                    continue

                # 6. Check CertificateChain
                cert_chain = key_element.find('CertificateChain')
                if cert_chain is None:
                    print(f"  ❌ ERROR: No CertificateChain found for {algorithm} key")
                    results.append('missing_chain')
                    continue

                # 7. Verify number of certificates matches
                num_certs_elem = cert_chain.find('NumberOfCertificates')
                if num_certs_elem is None:
                    print(f"  ❌ ERROR: Missing NumberOfCertificates for {algorithm} chain")
                    results.append('invalid_chain')
                    continue

                expected_certs = int(num_certs_elem.text)
                actual_certs = len(cert_chain.findall('Certificate'))
                if actual_certs != expected_certs:
                    print(f"  ⚠️ WARNING: NumberOfCertificates ({expected_certs}) does not match actual certificates found ({actual_certs})")

                # 8. Process certificates
                certs = cert_chain.findall('Certificate')
                if len(certs) < 2:
                    print(f"  ❌ ERROR: {algorithm} chain must have at least 2 certificates (leaf and root)")
                    results.append('invalid_chain')
                    continue

                # Store chain length for kb_index
                chain_length = len(certs)

                # Validate certificate chain
                try:
                    cert_chain = []
                    # Parse private key from the keybox
                    private_key_text = private_key.text.strip()
                    private_key_text = re.sub(re.compile(r'^\s+', re.MULTILINE), '', private_key_text)
                    private_key_text = clean_pem_key(private_key_text)
                    private_key_obj = None

                    try:
                        private_key_obj = serialization.load_pem_private_key(
                            private_key_text.encode(),
                            password=None
                        )
                    except Exception as e:
                        if "EC curves with explicit parameters" in str(e) or "unsupported" in str(e).lower():
                            # Set private_key_obj to a special sentinel value to indicate skipped validation.
                            private_key_obj = "UNSUPPORTED_CURVE"
                        else:
                            print(f"  ❌ ERROR: Failed to parse private key for {algorithm} key: {e}")
                            results.append('invalid_private_key')

                    # Parse certificates in the chain
                    if len(certs) > 4:
                        long_chain = True
                    tab_text = ""
                    for cert in certs:
                        wx.Yield()
                        cert_text = cert.text.strip()
                        parsed_cert = x509.load_pem_x509_certificate(cert_text.encode())
                        cert_chain.append(parsed_cert)
                        ecdsa_leaf = "valid"
                        rsa_leaf = "valid"
                        cert_status = "valid"

                        cert_sn, cert_issuer, cert_subject, sig_algo, expiry, key_usages, parsed, crl_distribution_points = parse_cert(cert.text)

                        # Format the issuer field
                        formatted_issuer, issuer_sn = format_dn(cert_issuer)

                        if issuer_sn in shadow_banned_list:
                            is_shadow_banned = True

                        # Format the issued to field
                        formatted_issued_to, issued_to_sn = format_dn(cert_subject)

                        # indent the chain
                        tab_text += "  "

                        # redact if verbose is not set
                        if get_verbose():
                            cert_sn_text = cert_sn
                            formatted_issued_to_text = formatted_issued_to
                            formatted_issuer_text = formatted_issuer
                        else:
                            cert_sn_text = "REDACTED"
                            formatted_issued_to_text = "REDACTED"
                            formatted_issuer_text = "REDACTED"

                        print(f'{tab_text}Certificate SN:          {cert_sn_text}')
                        print(f'{tab_text}Issued to:               {formatted_issued_to_text}')
                        print(f'{tab_text}Issuer:                  {formatted_issuer_text}')
                        print(f'{tab_text}Signature Algorithm:     {sig_algo}')
                        print(f'{tab_text}Key Usage:               {key_usages}')
                        if crl_distribution_points:
                            print(f'{tab_text}CRL Distribution Points: {crl_distribution_points}')
                        expired_text = ""
                        if expiry < datetime.now(timezone.utc):
                            expired_text = " (EXPIRED)"
                        print(f"{tab_text}Validity:                {parsed.not_valid_before_utc.date()} to {expiry.date()} {expired_text}\n")

                        if "Software Attestation" in cert_issuer:
                            is_sw_signed = True
                            cert_status = "sw_signed"

                        if issuer_sn in ['f92009e853b6b045']:
                            is_google_signed = True

                        if expiry < datetime.now(timezone.utc):
                            is_expired = True
                            print(f"{tab_text}❌❌❌ Certificate is EXPIRED")
                            cert_status = "expired"
                        elif expiry < datetime.now(timezone.utc) + timedelta(days=30):
                            expiring_soon = True
                            print(f"{tab_text}⚠️ Certificate is EXPIRING SOON")

                        if cert_sn.strip().lower() in (sn.strip().lower() for sn in crl["entries"].keys()):
                            print(f"{tab_text}❌❌❌ Certificate is REVOKED")
                            print(f"{tab_text}❌❌❌ Reason: {crl['entries'][cert_sn]['reason']} ***")
                            is_revoked = True
                            cert_status = "revoked"

                        # Collect status
                        if algorithm == "ecdsa":
                            if tab_text == "  ":
                                ecdsa_leaf = cert_status
                            else:
                                if ecdsa_chain == 'valid':
                                    ecdsa_chain = cert_status
                            if is_google_signed:
                                ecdsa_root_ca_sn = cert_sn
                        elif algorithm == "rsa":
                            if tab_text == "  ":
                                rsa_leaf = cert_status
                            else:
                                if rsa_chain == 'valid':
                                    rsa_chain = cert_status
                            if is_google_signed:
                                rsa_root_ca_sn = cert_sn

                        if config.kb_index:
                            # Add the leaf cert details to keybox_data_collection
                            if algorithm == "ecdsa" and tab_text == "  ":
                                keybox_data_collection["ecdsa_sn"] = cert_sn
                                keybox_data_collection["ecdsa_issuer"] = formatted_issuer
                                keybox_data_collection["ecdsa_leaf"] = ecdsa_leaf
                                keybox_data_collection["ecdsa_length"] = chain_length
                                keybox_data_collection["ecdsa_not_before"] = parsed.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
                                keybox_data_collection["ecdsa_not_after"] = expiry.strftime("%Y-%m-%d %H:%M:%S UTC")
                            elif algorithm == "rsa" and tab_text == "  ":
                                keybox_data_collection["rsa_sn"] = cert_sn
                                keybox_data_collection["rsa_issuer"] = formatted_issuer
                                keybox_data_collection["rsa_leaf"] = rsa_leaf
                                keybox_data_collection["rsa_length"] = chain_length
                                keybox_data_collection["rsa_not_before"] = parsed.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
                                keybox_data_collection["rsa_not_after"] = expiry.strftime("%Y-%m-%d %H:%M:%S UTC")

                    if config.kb_index:
                        keybox_data_collection["ecdsa_chain"] = ecdsa_chain
                        keybox_data_collection["rsa_chain"] = rsa_chain

                    # First is leaf, last is root
                    leaf_cert = cert_chain[0]
                    root_cert = cert_chain[-1]
                    intermediate_certs = cert_chain[1:-1]

                    # Verify the private key matches the leaf certificate's public key
                    if private_key_obj is not None and private_key_obj != "UNSUPPORTED_CURVE" and leaf_cert is not None:
                        try:
                            leaf_public_key = leaf_cert.public_key()

                            # For RSA keys
                            if isinstance(private_key_obj, rsa.RSAPrivateKey) and isinstance(leaf_public_key, rsa.RSAPublicKey):
                                priv_public_numbers = private_key_obj.public_key().public_numbers()
                                leaf_public_numbers = leaf_public_key.public_numbers()

                                if (priv_public_numbers.n == leaf_public_numbers.n and
                                    priv_public_numbers.e == leaf_public_numbers.e):
                                    print(f"  ✅ Private key matches leaf certificate for {algorithm} chain")
                                else:
                                    print(f"  ❌ ERROR: Private key does not match leaf certificate for {algorithm} chain")
                                    results.append('key_mismatch')

                            # For ECDSA keys
                            elif isinstance(private_key_obj, ec.EllipticCurvePrivateKey) and isinstance(leaf_public_key, ec.EllipticCurvePublicKey):
                                priv_public_key = private_key_obj.public_key()

                                priv_public_bytes = priv_public_key.public_bytes(
                                    encoding=serialization.Encoding.PEM,
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                                )

                                leaf_public_bytes = leaf_public_key.public_bytes(
                                    encoding=serialization.Encoding.PEM,
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                                )

                                if priv_public_bytes == leaf_public_bytes:
                                    print(f"  ✅ Private key matches leaf certificate for {algorithm} chain")
                                else:
                                    print(f"  ❌ ERROR: Private key does not match leaf certificate for {algorithm} chain")
                                    results.append('key_mismatch')
                            else:
                                print(f"  ❌ ERROR: Mismatched key types between private key and certificate for {algorithm} chain")
                                results.append('key_mismatch')
                        except Exception as e:
                            print(f"  ❌ ERROR: Failed to verify key pair match: {e}")
                            results.append('key_mismatch')
                    elif private_key_obj == "UNSUPPORTED_CURVE":
                        print(f"  ⚠️ WARNING: Skipped private key validation due to unsupported curve format")

                    # Validate the certificate chain
                    try:
                        # Verify leaf is signed by first intermediate (or root if no intermediates)
                        current_cert = leaf_cert
                        next_cert = intermediate_certs[0] if intermediate_certs else root_cert

                        # Verify leaf cert is signed by next cert in chain
                        public_key = next_cert.public_key()
                        if isinstance(public_key, rsa.RSAPublicKey):
                            try:
                                public_key.verify(
                                    current_cert.signature,
                                    current_cert.tbs_certificate_bytes,
                                    padding.PKCS1v15(),
                                    current_cert.signature_hash_algorithm
                                )
                            except Exception as e:
                                print(f"  ❌ ERROR: RSA Certificate chain validation failed for {algorithm}: {e}")
                                results.append('invalid_chain')
                        elif isinstance(public_key, ec.EllipticCurvePublicKey):
                            try:
                                public_key.verify(
                                    current_cert.signature,
                                    current_cert.tbs_certificate_bytes,
                                    ec.ECDSA(current_cert.signature_hash_algorithm)
                                )
                            except Exception as e:
                                print(f"  ❌ ERROR: ECDSA Certificate chain validation failed for {algorithm}: {e}")
                                results.append('invalid_chain')

                        # Verify the rest of the chain
                        for i in range(len(intermediate_certs)):
                            wx.Yield()
                            current_cert = intermediate_certs[i]
                            next_cert = intermediate_certs[i + 1] if i + 1 < len(intermediate_certs) else root_cert

                            # Verify current_cert was signed by next_cert
                            public_key = next_cert.public_key()
                            if isinstance(public_key, rsa.RSAPublicKey):
                                try:
                                    public_key.verify(
                                        current_cert.signature,
                                        current_cert.tbs_certificate_bytes,
                                        padding.PKCS1v15(),
                                        current_cert.signature_hash_algorithm
                                    )
                                except Exception as e:
                                    print(f"  ❌ RSA Certificate chain validation failed for {algorithm}: {e}")
                                    results.append('invalid_chain')
                            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                                try:
                                    public_key.verify(
                                        current_cert.signature,
                                        current_cert.tbs_certificate_bytes,
                                        ec.ECDSA(current_cert.signature_hash_algorithm)
                                    )
                                except Exception as e:
                                    print(f"  ❌ ECDSA Certificate chain validation failed for {algorithm}: {e}")
                                    results.append('invalid_chain')
                            else:
                                print(f"  ❌ ERROR: Unsupported public key type for {algorithm}")
                                results.append('invalid_chain')
                                # raise ValueError("Unsupported public key type")

                        # Finally verify root signed the last intermediate (if any intermediates exist)
                        if intermediate_certs:
                            public_key = root_cert.public_key()
                            if isinstance(public_key, rsa.RSAPublicKey):
                                public_key.verify(
                                    intermediate_certs[-1].signature,
                                    intermediate_certs[-1].tbs_certificate_bytes,
                                    padding.PKCS1v15(),
                                    intermediate_certs[-1].signature_hash_algorithm
                                )
                            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                                public_key.verify(
                                    intermediate_certs[-1].signature,
                                    intermediate_certs[-1].tbs_certificate_bytes,
                                    ec.ECDSA(intermediate_certs[-1].signature_hash_algorithm)
                                )

                        print(f"  ✅ Certificate chain validation successful for {algorithm}")

                    except Exception as e:
                        print(f"  ❌ Certificate chain validation failed for {algorithm}: {e}")
                        results.append('invalid_chain')

                except Exception as e:
                    print(f"❌ ERROR validating certificate chain: {e}")
                    results.append('invalid_chain')

            # Check if all required algorithms were found
            missing_algorithms = required_algorithms - found_algorithms
            if missing_algorithms:
                print(f"\n❌ Missing required algorithm chains: {', '.join(missing_algorithms)}")
                results.append('missing_algorithms')

            if config.kb_index:
                # Update kb_index, use ECDSA serial number as the key.
                file_key = filename
                if len(keyboxes) > 1:
                    file_key = f"{filename}__{k}"

                ecdsa_sn = keybox_data_collection.get("ecdsa_sn")
                if ecdsa_sn:
                    # Check if this is a new keybox or existing one
                    is_new_keybox = ecdsa_sn not in kb_index
                    is_new_file = True

                    if is_new_keybox:
                        # Initialize new keybox entry
                        kb_index[ecdsa_sn] = {
                            "ecdsa_sn": ecdsa_sn,
                            "files": []
                        }
                        print(f"  🆕 New keybox detected with ECDSA SN: {ecdsa_sn}")
                    else:
                        # Check if current file is already in the files list
                        for file_entry in kb_index[ecdsa_sn]["files"]:
                            if file_entry["path"] == file_key:
                                is_new_file = False
                                break

                        if is_new_file:
                            print(f"  🔄 Duplicate keybox detected - same ECDSA SN ({ecdsa_sn}) but new file: {file_key}")

                    # Track changes in root level values for existing keyboxes
                    changes_detected = []
                    if not is_new_keybox:
                        # Compare current values with existing ones
                        fields_to_check = [
                            ("ecdsa_issuer", "ECDSA Issuer"),
                            ("ecdsa_leaf", "ECDSA Leaf Status"),
                            ("ecdsa_chain", "ECDSA Chain Status"),
                            ("ecdsa_length", "ECDSA Chain Length"),
                            ("ecdsa_not_before", "ECDSA Not Before"),
                            ("ecdsa_not_after", "ECDSA Not After"),
                            ("rsa_sn", "RSA Serial Number"),
                            ("rsa_issuer", "RSA Issuer"),
                            ("rsa_leaf", "RSA Leaf Status"),
                            ("rsa_chain", "RSA Chain Status"),
                            ("rsa_length", "RSA Chain Length"),
                            ("rsa_not_before", "RSA Not Before"),
                            ("rsa_not_after", "RSA Not After")
                        ]

                        for field_key, field_name in fields_to_check:
                            old_value = kb_index[ecdsa_sn].get(field_key)
                            new_value = keybox_data_collection.get(field_key)

                            if old_value != new_value:
                                changes_detected.append(f"       - {field_name}: '{old_value}' → '{new_value}'")

                    # Report changes if any were detected
                    if changes_detected:
                        print(f"  🔑 Changes detected for ECDSA SN {ecdsa_sn}:")
                        for change in changes_detected:
                            print(change)

                    # Update certificate details
                    kb_index[ecdsa_sn].update({
                        "ecdsa_issuer": keybox_data_collection.get("ecdsa_issuer"),
                        "ecdsa_leaf": keybox_data_collection.get("ecdsa_leaf"),
                        "ecdsa_chain": keybox_data_collection.get("ecdsa_chain"),
                        "ecdsa_length": keybox_data_collection.get("ecdsa_length"),
                        "ecdsa_not_before": keybox_data_collection.get("ecdsa_not_before"),
                        "ecdsa_not_after": keybox_data_collection.get("ecdsa_not_after"),
                        "rsa_sn": keybox_data_collection.get("rsa_sn"),
                        "rsa_issuer": keybox_data_collection.get("rsa_issuer"),
                        "rsa_leaf": keybox_data_collection.get("rsa_leaf"),
                        "rsa_chain": keybox_data_collection.get("rsa_chain"),
                        "rsa_length": keybox_data_collection.get("rsa_length"),
                        "rsa_not_before": keybox_data_collection.get("rsa_not_before"),
                        "rsa_not_after": keybox_data_collection.get("rsa_not_after"),
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                    # Add new file entry if it doesn't exist
                    if is_new_file:
                        kb_index[ecdsa_sn]["files"].append({
                            "path": file_key,
                            "hash": file_hash,
                            "ecdsa_root_ca_sn": ecdsa_root_ca_sn,
                            "rsa_root_ca_sn": rsa_root_ca_sn
                        })
                    else:
                        # Update existing file entry hash
                        for i, file_entry in enumerate(kb_index[ecdsa_sn]["files"]):
                            if file_entry["path"] == file_key:
                                kb_index[ecdsa_sn]["files"][i]["hash"] = file_hash
                                kb_index[ecdsa_sn]["files"][i]["ecdsa_root_ca_sn"] = ecdsa_root_ca_sn
                                kb_index[ecdsa_sn]["files"][i]["rsa_root_ca_sn"] = rsa_root_ca_sn
                                break

            k += 1

        if is_revoked:
            print(f"\n❌❌❌ Keybox {filename} contains revoked certificates!")
            results.append('revoked')
        else:
            print(f"\n✅ certificates in Keybox {filename} are not on the revocation list")
            results.append('valid')
        if is_expired:
            print(f"\n❌❌❌ Keybox {filename} contains expired certificates!")
            results.append('expired')
        if is_sw_signed or not is_google_signed:
            print(f"⚠️ Keybox {filename} is possibly software signed! This is not a hardware-backed keybox!")
            results.append('aosp')
        if expiring_soon:
            print(f"⚠️ Keybox {filename} contains certificates that are expiring soon!")
            results.append('expiring_soon')
        if long_chain:
            print(f"⚠️ Keybox {filename} contains certificates longer chain than normal, this may no work.")
            results.append('long_chain')
        if is_shadow_banned:
            print(f"\n❌❌❌ Keybox {filename} has certificate(s) issued by an authority in shadow banned list!")
            results.append('shadow_banned')
        print('')

        # Save kb_index if it was used
        if config.kb_index:
            save_kb_index(kb_index)

        return results
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in check_kb function")
        print(e)
        traceback.print_exc()


# ============================================================================
#                               Function to clean_pem_key
# ============================================================================
def clean_pem_key(key_text):
    # Key with spaces instead of newlines (common in XML)
    if '-----BEGIN' in key_text and '\n' not in key_text:
        # Split at the BEGIN marker
        parts = re.split(r'(-----BEGIN [^-]+-----)', key_text)
        if len(parts) >= 3:
            header = parts[1]
            # Split at the END marker
            content_parts = re.split(r'(-----END [^-]+-----)', parts[2])
            if len(content_parts) >= 2:
                # Extract the base64 content and format with newlines
                content = content_parts[0].strip()
                content_chunks = content.split()
                formatted_content = '\n'.join(content_chunks)
                footer = content_parts[1]
                # Reassemble the key
                key_text = f"{header}\n{formatted_content}\n{footer}"
    return key_text


# ============================================================================
#                               Function to parse the certificate
# ============================================================================
def parse_cert(cert):
    import logging
    from cryptography.x509.oid import ExtensionOID

    cert = "\n".join(line.strip() for line in cert.strip().split("\n"))
    parsed = x509.load_pem_x509_certificate(cert.encode(), default_backend())
    issuer = None
    subject = None
    serial_number = None
    sig_algo = None
    expiry = None
    key_usages = 'None'
    crl_distribution_points = None

    try:
        issuer = parsed.issuer.rfc4514_string()
    except Exception as e:
        logging.error(f"Issuer extraction failed: {e}")
    try:
        subject = parsed.subject.rfc4514_string()
    except Exception as e:
        logging.error(f"Subject extraction failed: {e}")
    try:
        serial_number = f'{parsed.serial_number:x}'
    except Exception as e:
        logging.error(f"Serial number extraction failed: {e}")
    try:
        sig_algo = parsed.signature_algorithm_oid._name
    except Exception as e:
        logging.error(f"Signature algorithm extraction failed: {e}")
    try:
        expiry = parsed.not_valid_after_utc
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    except Exception as e:
        logging.error(f"Expiry extraction failed: {e}")
    try:
        key_usage_ext = parsed.extensions.get_extension_for_oid(ExtensionOID.KEY_USAGE)
        key_usage = key_usage_ext.value
        allowed_usages = []
        if key_usage.digital_signature:
            allowed_usages.append("Digital Signature")
        if key_usage.content_commitment:
            allowed_usages.append("Content Commitment")
        if key_usage.key_encipherment:
            allowed_usages.append("Key Encipherment")
        if key_usage.data_encipherment:
            allowed_usages.append("Data Encipherment")
        if key_usage.key_agreement:
            allowed_usages.append("Key Agreement")
            # Only check encipher_only and decipher_only if key_agreement is True
            if key_usage.encipher_only:
                allowed_usages.append("Encipher Only")
            if key_usage.decipher_only:
                allowed_usages.append("Decipher Only")
        if key_usage.key_cert_sign:
            allowed_usages.append("Certificate Signing")
        if key_usage.crl_sign:
            allowed_usages.append("CRL Signing")
        if allowed_usages:
            key_usages = ", ".join(allowed_usages)
    except Exception as e:
        logging.error(f"Key usage extraction failed: {e}")

    # Extract CRL Distribution Points
    try:
        crl_ext = parsed.extensions.get_extension_for_oid(ExtensionOID.CRL_DISTRIBUTION_POINTS)
        if crl_ext:
            crl_points = []
            for point in crl_ext.value:
                if point.full_name:
                    for name in point.full_name:
                        if name.value:
                            crl_points.append(name.value)
            if crl_points:
                crl_distribution_points = crl_points
    except Exception as e:
        if not "ObjectIdentifier(oid=2.5.29.31" in str(e):
            logging.error(f"CRL distribution points extraction failed: {e}")

    return serial_number, issuer, subject, sig_algo, expiry, key_usages, parsed, crl_distribution_points


# ============================================================================
#                               Function to format the DN string
# ============================================================================
def format_dn(dn):
    try:
        formatted = []
        sn = ""
        # Split the DN string by commas not preceded by a backslash (escape character)
        parts = re.split(r'(?<!\\),', dn)
        for part in parts:
            # Replace escaped commas with actual commas
            part = part.replace("\\,", ",")
            if part.startswith("2.5.4.5="):
                sn = part.split("=")[1]
                formatted.insert(0, sn)
            else:
                formatted.append(part.split("=")[1])
        if formatted:
            return ", ".join(formatted), sn
        else:
            return "UNKNOWN", sn
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in format_dn function")
        print(e)
        traceback.print_exc()
        return "UNKNOWN", sn


# ============================================================================
#                               Function analyze_kb_file
# ============================================================================
def analyze_kb_file(filepath=None, ecdsa_sn=None, ecdsa_issuer=None, rsa_sn=None, rsa_issuer=None, verbose=False):
    try:
        kb_index = load_kb_index()
        if not kb_index:
            print("No kb_index.json data found or file is empty.")
            return

        target_ecdsa_sn = None
        target_data = None

        # Direct lookup by ECDSA SN
        if ecdsa_sn and ecdsa_sn in kb_index:
            target_ecdsa_sn = ecdsa_sn
            target_data = kb_index[ecdsa_sn]

        # Search by filepath if ECDSA SN not provided
        elif filepath:
            for ecdsa_serial, data in kb_index.items():
                files = data.get('files', [])
                for file_entry in files:
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                    if file_path == filepath:
                        target_ecdsa_sn = ecdsa_serial
                        target_data = data
                        break
                if target_data:
                    break

        # Fallback search by other criteria
        elif ecdsa_issuer or rsa_sn or rsa_issuer:
            for ecdsa_serial, data in kb_index.items():
                if ((ecdsa_issuer and data.get('ecdsa_issuer') == ecdsa_issuer) or
                    (rsa_sn and data.get('rsa_sn') == rsa_sn) or
                    (rsa_issuer and data.get('rsa_issuer') == rsa_issuer)):
                    target_ecdsa_sn = ecdsa_serial
                    target_data = data
                    break

        if not target_data:
            print("❌ ERROR: No keybox found matching the specified criteria.")
            return

        target_files = target_data.get('files', [])

        if verbose:
            print("=" * 80)
            print("KEYBOX FILE ANALYSIS REPORT")
            print("=" * 80)
            if filepath:
                print(f"Target File: {filepath}")
            print(f"Target ECDSA SN: {target_ecdsa_sn}")
            print("-" * 80)

            # Display keybox information
            print(f"ECDSA SN:     {target_ecdsa_sn}")
            print(f"RSA SN:       {target_data.get('rsa_sn', 'N/A')}")
            print(f"ECDSA Issuer: {target_data.get('ecdsa_issuer', 'N/A')}")
            print(f"RSA Issuer:   {target_data.get('rsa_issuer', 'N/A')}")
            print(f"ECDSA Leaf:   {target_data.get('ecdsa_leaf', 'N/A')}")
            print(f"ECDSA Chain:  {target_data.get('ecdsa_chain', 'N/A')}")
            print(f"RSA Leaf:     {target_data.get('rsa_leaf', 'N/A')}")
            print(f"RSA Chain:    {target_data.get('rsa_chain', 'N/A')}")
            print(f"Files Count:  {len(target_files)}")
            print("Files:")
            for file_entry in target_files:
                file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                file_hash = file_entry.get('hash', 'N/A') if isinstance(file_entry, dict) else 'N/A'
                if file_hash != 'N/A':
                    print(f"  - {file_path} (hash: {file_hash})")
                else:
                    print(f"  - {file_path}")

        # Find matches with other keyboxes
        hash_matches = []
        rsa_sn_matches = []
        ecdsa_issuer_matches = []
        rsa_issuer_matches = []

        # Get target hashes for comparison
        target_hashes = set()
        for file_entry in target_files:
            file_hash = file_entry.get('hash', '') if isinstance(file_entry, dict) else ''
            if file_hash:
                target_hashes.add(file_hash)

        # Compare with other keyboxes
        for ecdsa_serial, data in kb_index.items():
            if ecdsa_serial == target_ecdsa_sn:
                # If we're analyzing the same ECDSA serial number, we need to check for hash matches within the same group
                # but exclude the target file if analyzing a specific file
                files = data.get('files', [])
                for file_entry in files:
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                    file_hash = file_entry.get('hash', '') if isinstance(file_entry, dict) else ''

                    # Only include if it's not the target file we're analyzing AND has matching hash
                    if file_hash in target_hashes and (not filepath or file_path != filepath):
                        hash_matches.append(file_path)

                # Also check for RSA SN matches within the same group
                if target_data.get('rsa_sn', 'N/A') != 'N/A' and data.get('rsa_sn') == target_data.get('rsa_sn'):
                    for file_entry in files:
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                        # Only include if it's not the target file we're analyzing
                        if not filepath or file_path != filepath:
                            rsa_sn_matches.append(file_path)

                continue

            files = data.get('files', [])

            # Check for matching hashes
            for file_entry in files:
                file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                file_hash = file_entry.get('hash', '') if isinstance(file_entry, dict) else ''
                if file_hash in target_hashes:
                    hash_matches.append(file_path)

            # Check for matching RSA SN
            if target_data.get('rsa_sn', 'N/A') != 'N/A' and data.get('rsa_sn') == target_data.get('rsa_sn'):
                rsa_sn_matches.extend([f.get('path', '') if isinstance(f, dict) else f for f in files])

            # Check for matching ECDSA Issuer
            if target_data.get('ecdsa_issuer', 'N/A') != 'N/A' and data.get('ecdsa_issuer') == target_data.get('ecdsa_issuer'):
                ecdsa_issuer_matches.extend([f.get('path', '') if isinstance(f, dict) else f for f in files])

            # Check for matching RSA Issuer
            if target_data.get('rsa_issuer', 'N/A') != 'N/A' and data.get('rsa_issuer') == target_data.get('rsa_issuer'):
                rsa_issuer_matches.extend([f.get('path', '') if isinstance(f, dict) else f for f in files])

        to_print = f"  FILES WITH IDENTICAL HASH (hash: {list(target_hashes)[0] if target_hashes else 'N/A'}):"
        print("  " + "." * (len(to_print) -2))
        print(to_print)
        if hash_matches:
            for file_path in hash_matches:
                print(f"    - {file_path}")
        else:
            print("    No other files with identical hash found.")

        to_print = f"  FILES WITH IDENTICAL ECDSA SERIAL NUMBER ({target_data.get('ecdsa_sn', 'N/A')}):"
        print("  " + "." * (len(to_print) -2))
        print(to_print)

        # Get all files with the same ECDSA serial number (excluding the target file if analyzing a specific file)
        ecdsa_sn_matches = []
        target_files = target_data.get('files', [])

        if filepath:
            # If analyzing a specific file, exclude it from the list
            for file_entry in target_files:
                file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                if file_path != filepath:
                    ecdsa_sn_matches.append(file_path)
        else:
            # If searching by ECDSA SN directly, show all files
            for file_entry in target_files:
                file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else file_entry
                ecdsa_sn_matches.append(file_path)

        if ecdsa_sn_matches:
            for file_path in ecdsa_sn_matches:
                print(f"    - {file_path}")
        else:
            print("    No other files with identical ECDSA serial number found.")

        to_print = f"  FILES WITH IDENTICAL RSA SERIAL NUMBER ({target_data.get('rsa_sn', 'N/A')}):"
        print("  " + "." * (len(to_print) -2))
        print(to_print)
        if rsa_sn_matches:
            for file_path in rsa_sn_matches:
                print(f"    - {file_path}")
        else:
            print("    No other files with identical RSA serial number found.")

        to_print = f"  FILES WITH SAME ECDSA ISSUER ({target_data.get('ecdsa_issuer', 'N/A')}):"
        print("  " + "." * (len(to_print) -2))
        print(to_print)
        if ecdsa_issuer_matches:
            for file_path in ecdsa_issuer_matches:
                print(f"    - {file_path}")
        else:
            print("    No other files with same ECDSA issuer found.")

        to_print = f"  FILES WITH SAME RSA ISSUER ({target_data.get('rsa_issuer', 'N/A')}):"
        print("  " + "." * (len(to_print) -2))
        print(to_print)
        if rsa_issuer_matches:
            for file_path in rsa_issuer_matches:
                print(f"    - {file_path}")
        else:
            print("    No other files with same RSA issuer found.")

        print("  -------")
        print("  SUMMARY")
        print("  -------")
        print(f"  Hash matches:                      {len(hash_matches)}")
        print(f"  ECDSA SN matches:                  {len(ecdsa_sn_matches)}")
        print(f"  RSA SN matches:                    {len(rsa_sn_matches)}")
        print(f"  ECDSA Issuer matches:              {len(ecdsa_issuer_matches)}")
        print(f"  RSA Issuer matches:                {len(rsa_issuer_matches)}")

        all_matches = set(hash_matches + ecdsa_sn_matches + rsa_sn_matches + ecdsa_issuer_matches + rsa_issuer_matches)
        print(f"  Total unique files with any match: {len(all_matches)}")

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in analyze_kb_file function")
        traceback.print_exc()


# ============================================================================
#                               Function kb_add_missing_files
# ============================================================================
def kb_add_missing_files(target_path, check_validity=True, dry_run=False, verbose=False):
    try:
        if not target_path or not os.path.exists(target_path):
            print(f"❌ ERROR: Target path '{target_path}' does not exist or is not provided")
            return None

        kb_index = load_kb_index()

        # Get all existing file paths from kb_index
        existing_files = set()
        for ecdsa_sn, entry in kb_index.items():
            files = entry.get('files', [])
            for file_entry in files:
                file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                existing_files.add(os.path.normpath(file_path))

        # Scan for keybox files in target path
        keybox_files = []
        total_scanned = 0

        print(f"Scanning directory: {target_path}")
        print("Looking for keybox files (*.xml)...")

        for root, dirs, files in os.walk(target_path):
            for file in files:
                total_scanned += 1
                if file.lower().endswith('.xml'):
                    file_path = os.path.join(root, file)
                    normalized_path = os.path.normpath(file_path)

                    # Check if this file is already in kb_index
                    if normalized_path not in existing_files:
                        keybox_files.append(file_path)
                        if verbose:
                            print(f"  Found potential keybox: {file_path}")

        print(f"Found {len(keybox_files)} potentially missing keybox files")

        # Initialize results
        results = {
            'total_scanned': total_scanned,
            'missing_files_found': len(keybox_files),
            'valid_files': [],
            'invalid_files': [],
            'added_count': 0
        }

        if not keybox_files:
            print("No missing keybox files found")
            return results

        # Check validity if requested
        if check_validity:
            print("Validating keybox files...")
            for file_path in keybox_files:
                wx.Yield()
                try:
                    # Basic XML validation
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    # Check if it's a valid keybox file
                    if root.tag == 'AndroidAttestation':
                        keyboxes = root.findall('Keybox')
                        if keyboxes:
                            print(f"  ✅ Valid keybox: {os.path.basename(file_path)}")
                            results['valid_files'].append(file_path)
                        else:
                            print(f"  ❌ Invalid keybox (no Keybox elements): {os.path.basename(file_path)}")
                            results['invalid_files'].append(file_path)
                    else:
                        print(f"  ❌ Invalid keybox (not AndroidAttestation): {os.path.basename(file_path)}")
                        results['invalid_files'].append(file_path)

                except Exception as e:
                    print(f"  ❌ Invalid keybox (parse error): {os.path.basename(file_path)} - {str(e)}")
                    results['invalid_files'].append(file_path)
        else:
            # If not checking validity, assume all are valid
            results['valid_files'] = keybox_files[:]

        # Add valid files to kb_index if not in dry_run mode
        if not dry_run and results['valid_files']:
            print(f"Adding {len(results['valid_files'])} valid keybox files to kb_index...")

            for file_path in results['valid_files']:
                wx.Yield()
                try:
                    print(f"  Processing: {os.path.basename(file_path)}")

                    # Check the keybox to get certificate details
                    kb_results = check_kb(file_path, force_fresh=False)

                    if kb_results and 'invalid' not in kb_results:
                        results['added_count'] += 1
                        if verbose:
                            print(f"    ✅ Added to kb_index")
                    else:
                        print(f"    ⚠️ Keybox validation failed, not added to index")
                        results['invalid_files'].append(file_path)
                        if file_path in results['valid_files']:
                            results['valid_files'].remove(file_path)

                except Exception as e:
                    print(f"    ❌ Error processing keybox: {str(e)}")
                    results['invalid_files'].append(file_path)
                    if file_path in results['valid_files']:
                        results['valid_files'].remove(file_path)

        elif dry_run:
            print("DRY RUN: kb_index is not updated")
            results['added_count'] = len(results['valid_files'])

        return results

    except Exception as e:
        print(f"❌ ERROR: Encountered an error in kb_add_missing_files function")
        traceback.print_exc()
        return None


# ============================================================================
#                 Function: kb_stats
# ============================================================================
def kb_stats(verbose=False, list_unique_files=False, list_valid_entries=False, list_non_common_entries=False, target_path=None, check_file_existence=False, list_non_existent=False, remove_non_existent=False, add_missing_files=False):
    try:
        kb_index = load_kb_index()
        if not kb_index:
            print("❌ ERROR: No kb_index.json data found or file is empty.")
            print("Please ensure keybox files have been processed first and KB indexing is enabled.")
            return None

        print(f"\n" + "=" * 80)
        print("KEYBOX STATISTICS ANALYSIS")
        print("=" * 80)

        # Initialize counters
        stats = {
            'total_entries': len(kb_index),
            'total_files': 0,
            'unique_file_entries': 0,
            'unique_valid_ecdsa_only': 0,
            'unique_valid_all_chains': 0,
            'entries_valid_ecdsa': 0,
            'entries_valid_all_chains': 0,
            'entries_valid_ecdsa_revoked_chain': 0,
            'revoked_ecdsa_leaf': 0,
            'expired_ecdsa_leaf': 0,
            'valid_ecdsa_chain': 0,
            'revoked_ecdsa_chain': 0,
            'unique_ecdsa_issuers': set(),
            'unique_rsa_issuers': set(),
            'unique_ecdsa_root_ca_sns': {},
            'unique_rsa_root_ca_sns': {},
            'non_common_keyboxes_path': {
                'valid_ecdsa': [],
                'invalid': [],
                'valid_count': 0,
                'invalid_count': 0
            },
            'non_existent_files': [],
            'non_existent_count': 0,
            'valid_ecdsa_revoked_chain_entries': [],
            'unique_file_list': [],
            'valid_ecdsa_entries': [],
            'valid_all_chains_entries': [],
            'parsing_errors': 0
        }

        # Track entries to remove if requested
        entries_to_update = []

        # Analyze each entry
        for ecdsa_sn, entry in kb_index.items():
            try:
                # Count total files
                files = entry.get('files', [])
                stats['total_files'] += len(files)

                # Check file existence if requested
                if check_file_existence:
                    existing_files = []
                    for file_entry in files:
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        if os.path.exists(file_path):
                            existing_files.append(file_entry)
                        else:
                            stats['non_existent_files'].append({
                                'ecdsa_sn': ecdsa_sn,
                                'file_path': file_path,
                                'file_entry': file_entry
                            })
                            stats['non_existent_count'] += 1

                    # Update the files list if we're removing non-existent files
                    if remove_non_existent and len(existing_files) != len(files):
                        entries_to_update.append({
                            'ecdsa_sn': ecdsa_sn,
                            'existing_files': existing_files
                        })

                # Get validation statuses
                ecdsa_leaf = entry.get('ecdsa_leaf', '')
                ecdsa_chain = entry.get('ecdsa_chain', '')
                rsa_leaf = entry.get('rsa_leaf', '')
                rsa_chain = entry.get('rsa_chain', '')

                # Get root CA SNs from the first file entry
                ecdsa_root_ca_sn = None
                rsa_root_ca_sn = None
                if files and isinstance(files[0], dict):
                    ecdsa_root_ca_sn = files[0].get('ecdsa_root_ca_sn')
                    rsa_root_ca_sn = files[0].get('rsa_root_ca_sn')

                ecdsa_leaf_valid = ecdsa_leaf == 'valid' and ecdsa_root_ca_sn
                ecdsa_chain_valid = ecdsa_chain == 'valid'
                rsa_leaf_valid = rsa_leaf == 'valid' and rsa_root_ca_sn
                rsa_chain_valid = rsa_chain == 'valid'

                # Check for single file entries
                if len(files) == 1:
                    stats['unique_file_entries'] += 1
                    stats['unique_file_list'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'file': files[0],
                        'ecdsa_leaf': ecdsa_leaf,
                        'ecdsa_chain': ecdsa_chain,
                        'rsa_leaf': rsa_leaf,
                        'rsa_chain': rsa_chain
                    })

                    # Count unique file entries with valid certificates
                    if ecdsa_leaf_valid and ecdsa_chain_valid:
                        stats['unique_valid_ecdsa_only'] += 1
                    if ecdsa_leaf_valid and ecdsa_chain_valid and rsa_leaf_valid and rsa_chain_valid:
                        stats['unique_valid_all_chains'] += 1

                # Count certificate statuses
                if ecdsa_leaf == 'revoked':
                    stats['revoked_ecdsa_leaf'] += 1
                if ecdsa_leaf == 'expired':
                    stats['expired_ecdsa_leaf'] += 1
                if ecdsa_chain_valid:
                    stats['valid_ecdsa_chain'] += 1
                if ecdsa_chain == 'revoked':
                    stats['revoked_ecdsa_chain'] += 1

                # Count entries with valid certificates
                if ecdsa_leaf_valid and ecdsa_chain_valid:
                    stats['entries_valid_ecdsa'] += 1
                    stats['valid_ecdsa_entries'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'files': files,
                        'file_count': len(files),
                        'ecdsa_issuer': entry.get('ecdsa_issuer', ''),
                        'rsa_issuer': entry.get('rsa_issuer', ''),
                        'rsa_leaf': rsa_leaf,
                        'rsa_chain': rsa_chain
                    })

                # Count entries with valid ECDSA leaf but revoked ECDSA chain
                if ecdsa_leaf_valid and ecdsa_chain == 'revoked':
                    ecdsa_length = entry.get('ecdsa_length', 0)
                    if ecdsa_length <= 3:
                        stats['entries_valid_ecdsa_revoked_chain'] += 1
                        stats['valid_ecdsa_revoked_chain_entries'].append({
                            'ecdsa_sn': ecdsa_sn,
                            'files': files,
                            'file_count': len(files),
                            'ecdsa_leaf': ecdsa_leaf,
                            'ecdsa_chain': ecdsa_chain,
                            'rsa_leaf': rsa_leaf,
                            'rsa_chain': rsa_chain,
                            'ecdsa_issuer': entry.get('ecdsa_issuer', ''),
                            'rsa_issuer': entry.get('rsa_issuer', '')
                        })

                if ecdsa_leaf_valid and ecdsa_chain_valid and rsa_leaf_valid and rsa_chain_valid:
                    stats['entries_valid_all_chains'] += 1
                    stats['valid_all_chains_entries'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'files': files,
                        'file_count': len(files),
                        'ecdsa_issuer': entry.get('ecdsa_issuer', ''),
                        'rsa_issuer': entry.get('rsa_issuer', '')
                    })

                # Collect unique issuers
                ecdsa_issuer = entry.get('ecdsa_issuer', '')
                rsa_issuer = entry.get('rsa_issuer', '')
                if ecdsa_issuer:
                    stats['unique_ecdsa_issuers'].add(ecdsa_issuer)
                if rsa_issuer:
                    stats['unique_rsa_issuers'].add(rsa_issuer)

                # Collect unique root CA serial numbers from files
                for file_entry in files:
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)

                    # Process ECDSA root CA serial numbers
                    ecdsa_root_ca_sn = file_entry.get('ecdsa_root_ca_sn', '') if isinstance(file_entry, dict) else ''
                    if ecdsa_root_ca_sn:
                        if ecdsa_root_ca_sn not in stats['unique_ecdsa_root_ca_sns']:
                            stats['unique_ecdsa_root_ca_sns'][ecdsa_root_ca_sn] = []
                        stats['unique_ecdsa_root_ca_sns'][ecdsa_root_ca_sn].append(file_path)

                    # Process RSA root CA serial numbers
                    rsa_root_ca_sn = file_entry.get('rsa_root_ca_sn', '') if isinstance(file_entry, dict) else ''
                    if rsa_root_ca_sn:
                        if rsa_root_ca_sn not in stats['unique_rsa_root_ca_sns']:
                            stats['unique_rsa_root_ca_sns'][rsa_root_ca_sn] = []
                        stats['unique_rsa_root_ca_sns'][rsa_root_ca_sn].append(file_path)

                # Check for entries not in target path - only if target_path is specified
                if target_path:
                    has_common_path = False
                    for file_entry in files:
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        # Normalize path separators for cross-platform comparison
                        if os.path.normpath(target_path).lower() in os.path.normpath(file_path).lower():
                            has_common_path = True
                            break

                    if not has_common_path:
                        entry_info = {
                            'ecdsa_sn': ecdsa_sn,
                            'files': files,
                            'file_count': len(files),
                            'ecdsa_leaf': ecdsa_leaf,
                            'ecdsa_chain': ecdsa_chain,
                            'rsa_leaf': rsa_leaf,
                            'rsa_chain': rsa_chain,
                            'ecdsa_issuer': ecdsa_issuer,
                            'rsa_issuer': rsa_issuer
                        }

                        if ecdsa_leaf_valid and ecdsa_chain_valid:
                            stats['non_common_keyboxes_path']['valid_ecdsa'].append(entry_info)
                            stats['non_common_keyboxes_path']['valid_count'] += 1
                        else:
                            stats['non_common_keyboxes_path']['invalid'].append(entry_info)
                            stats['non_common_keyboxes_path']['invalid_count'] += 1

            except Exception as e:
                print(f"⚠️ Warning: Error processing entry {ecdsa_sn}: {e}")
                stats['parsing_errors'] += 1
                continue

        # Update kb_index if removing non-existent files
        if remove_non_existent and entries_to_update:
            for entry_update in entries_to_update:
                ecdsa_sn = entry_update['ecdsa_sn']
                existing_files = entry_update['existing_files']

                if len(existing_files) == 0:
                    # Remove entire entry if no files exist
                    del kb_index[ecdsa_sn]
                    print(f"  Removed entire entry for ECDSA SN: {ecdsa_sn} (no existing files)")
                else:
                    # Update files list with only existing files
                    kb_index[ecdsa_sn]['files'] = existing_files
                    print(f"  Updated files list for ECDSA SN: {ecdsa_sn} ({len(existing_files)} files remain)")

            # Save updated kb_index
            save_kb_index(kb_index)
            print(f"Updated kb_index.json with {len(entries_to_update)} entries modified")

        # Print results
        print(f"Total entries (keys):                                    {stats['total_entries']:>8,}")
        print(f"Total files:                                             {stats['total_files']:>8,}")
        print()
        print(f"Unique file entries (single file per key) total:         {stats['unique_file_entries']:>8,}")
        print(f"  - Entries with valid ECDSA leaf & chain:               {stats['unique_valid_ecdsa_only']:>8,}")
        print(f"  - Entries with all valid chains (ECDSA + RSA):         {stats['unique_valid_all_chains']:>8,}")
        print()
        print(f"Entries with valid ECDSA leaf & chain:                   {stats['entries_valid_ecdsa']:>8,}")
        print(f"Entries with all valid chains (ECDSA + RSA):             {stats['entries_valid_all_chains']:>8,}")
        print(f"Entries with valid ECDSA leaf but revoked ECDSA chain:   {stats['entries_valid_ecdsa_revoked_chain']:>8,}")
        print()
        print(f"Revoked ECDSA leaf certificates:                         {stats['revoked_ecdsa_leaf']:>8,}")
        print(f"Expired ECDSA leaf certificates:                         {stats['expired_ecdsa_leaf']:>8,}")
        print(f"Valid ECDSA certificate chains:                          {stats['valid_ecdsa_chain']:>8,}")
        print(f"Revoked ECDSA certificate chains:                        {stats['revoked_ecdsa_chain']:>8,}")
        print()
        print(f"Unique ECDSA issuers:                                    {len(stats['unique_ecdsa_issuers']):>8,}")
        print(f"Unique RSA issuers:                                      {len(stats['unique_rsa_issuers']):>8,}")
        print(f"Unique ECDSA root CA serial numbers:                     {len(stats['unique_ecdsa_root_ca_sns']):>8,}")
        print(f"Unique RSA root CA serial numbers:                       {len(stats['unique_rsa_root_ca_sns']):>8,}")

        if target_path:
            print()
            print(f"Entries NOT in '{target_path}':")
            print(f"  Valid ECDSA (leaf & chain):                            {stats['non_common_keyboxes_path']['valid_count']:>8,}")
            print(f"  Invalid/Other:                                         {stats['non_common_keyboxes_path']['invalid_count']:>8,}")

        if check_file_existence:
            print()
            print(f"Non-existent files:                                      {stats['non_existent_count']:>8,}")

        if stats['parsing_errors'] > 0:
            print(f"\nParsing errors encountered:                            {stats['parsing_errors']:>8,}")

        # List unique files if requested
        if list_unique_files and stats['unique_file_list']:
            print(f"\n" + "=" * 80)
            print(f"UNIQUE FILE ENTRIES LIST ({len(stats['unique_file_list'])} entries)")
            print("=" * 80)
            for i, entry in enumerate(stats['unique_file_list'], 1):
                file_path = entry['file'].get('path', '') if isinstance(entry['file'], dict) else str(entry['file'])
                print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                print(f"     Status: ECDSA({entry['ecdsa_leaf']}/{entry['ecdsa_chain']}) RSA({entry['rsa_leaf']}/{entry['rsa_chain']})")
                print(f"     File: {file_path}")
                print()

        # List valid entries if requested
        if list_valid_entries:
            if stats['valid_ecdsa_entries']:
                print(f"\n" + "=" * 80)
                print(f"ENTRIES WITH VALID ECDSA LEAF & CHAIN ({len(stats['valid_ecdsa_entries'])} entries)")
                print("=" * 80)
                for i, entry in enumerate(stats['valid_ecdsa_entries'], 1):
                    print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                    print(f"     RSA Status: {entry['rsa_leaf']}/{entry['rsa_chain']}")
                    print(f"     ECDSA Issuer: {entry['ecdsa_issuer']}")
                    if entry['rsa_issuer']:
                        print(f"     RSA Issuer: {entry['rsa_issuer']}")
                    print(f"     Files: {entry['file_count']}")
                    # List the actual files
                    kb_entry = kb_index.get(entry['ecdsa_sn'], {})
                    files = kb_entry.get('files', [])
                    for j, file_entry in enumerate(files, 1):
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        # print(f"       {j}. {file_path}")
                        print(f"       - {file_path}")
                    print()

            if stats['valid_all_chains_entries']:
                print(f"\n" + "=" * 80)
                print(f"ENTRIES WITH ALL VALID CHAINS ({len(stats['valid_all_chains_entries'])} entries)")
                print("=" * 80)
                for i, entry in enumerate(stats['valid_all_chains_entries'], 1):
                    print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                    print(f"     ECDSA Issuer: {entry['ecdsa_issuer']}")
                    print(f"     RSA Issuer: {entry['rsa_issuer']}")
                    print(f"     Files: {entry['file_count']}")
                    # List the actual files
                    kb_entry = kb_index.get(entry['ecdsa_sn'], {})
                    files = kb_entry.get('files', [])
                    for j, file_entry in enumerate(files, 1):
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        # print(f"       {j}. {file_path}")
                        print(f"       - {file_path}")
                    print()

        # List valid entries with revoked chains if verbose
        if verbose and stats['valid_ecdsa_revoked_chain_entries']:
            print(f"\n" + "=" * 80)
            print(f"ENTRIES WITH VALID ECDSA LEAF BUT REVOKED CHAIN ({len(stats['valid_ecdsa_revoked_chain_entries'])} entries)")
            print("=" * 80)
            for i, entry in enumerate(stats['valid_ecdsa_revoked_chain_entries'], 1):
                print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                print(f"     Status: ECDSA({entry['ecdsa_leaf']}/{entry['ecdsa_chain']}) RSA({entry['rsa_leaf']}/{entry['rsa_chain']})")
                print(f"     ECDSA Issuer: {entry['ecdsa_issuer']}")
                if entry['rsa_issuer']:
                    print(f"     RSA Issuer: {entry['rsa_issuer']}")
                print(f"     Files: {entry['file_count']}")
                # List the actual files
                kb_entry = kb_index.get(entry['ecdsa_sn'], {})
                files = kb_entry.get('files', [])
                for j, file_entry in enumerate(files, 1):
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                    print(f"       {j}. {file_path}")
                print()

        # List non-existent files if requested
        if list_non_existent and stats['non_existent_files']:
            print(f"\n" + "=" * 80)
            print(f"NON-EXISTENT FILES ({len(stats['non_existent_files'])} files)")
            print("=" * 80)

            # Group non-existent files by ECDSA SN to show existing files for context
            grouped_missing = {}
            for file_info in stats['non_existent_files']:
                ecdsa_sn = file_info['ecdsa_sn']
                if ecdsa_sn not in grouped_missing:
                    grouped_missing[ecdsa_sn] = []
                grouped_missing[ecdsa_sn].append(file_info['file_path'])

            counter = 1
            for ecdsa_sn, missing_files in grouped_missing.items():
                print(f"{counter:3d}. ECDSA SN: {ecdsa_sn}")

                # Get all files for this ECDSA SN from kb_index
                entry = kb_index.get(ecdsa_sn, {})
                all_files = entry.get('files', [])

                # Separate existing and missing files
                existing_files = []
                for file_entry in all_files:
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                    if file_path not in missing_files and os.path.exists(file_path):
                        existing_files.append(file_path)

                # Print missing files
                for missing_file in missing_files:
                    print(f"     Missing: {missing_file}")

                # Print existing files
                if existing_files:
                    for existing_file in existing_files:
                        print(f"     Present: {existing_file}")
                else:
                    print(f"     Present: None")

                print()
                counter += 1

        # List non-common path entries if requested
        if list_non_common_entries:
            if stats['non_common_keyboxes_path']['valid_ecdsa']:
                print(f"\n" + "=" * 80)
                print(f"ENTRIES WITH VALID ECDSA NOT IN COMMON PATH ({len(stats['non_common_keyboxes_path']['valid_ecdsa'])} entries)")
                print("=" * 80)
                for i, entry in enumerate(stats['non_common_keyboxes_path']['valid_ecdsa'], 1):
                    print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                    print(f"     Status: ECDSA({entry['ecdsa_leaf']}/{entry['ecdsa_chain']}) RSA({entry['rsa_leaf']}/{entry['rsa_chain']})")
                    print(f"     Files: {entry['file_count']}")
                    n = 5  # Number of files to show
                    for j, file_entry in enumerate(entry['files'][:n], 1):  # Show first n files
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        print(f"     {j}. {file_path}")
                    if len(entry['files']) > n:
                        print(f"     ... and {len(entry['files']) - n} more files")
                    print()

            if stats['non_common_keyboxes_path']['invalid']:
                print(f"\n" + "=" * 80)
                print(f"ENTRIES WITH INVALID/OTHER STATUS NOT IN COMMON PATH ({len(stats['non_common_keyboxes_path']['invalid'])} entries)")
                print("=" * 80)
                for i, entry in enumerate(stats['non_common_keyboxes_path']['invalid'], 1):
                    print(f"{i:3d}. ECDSA SN: {entry['ecdsa_sn']}")
                    print(f"     Status: ECDSA({entry['ecdsa_leaf']}/{entry['ecdsa_chain']}) RSA({entry['rsa_leaf']}/{entry['rsa_chain']})")
                    print(f"     Files: {entry['file_count']}")
                    n = 5 # Number of files to show
                    for j, file_entry in enumerate(entry['files'][:n], 1):  # Show first n files
                        file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                        print(f"     {j}. {file_path}")
                    if len(entry['files']) > n:
                        print(f"     ... and {len(entry['files']) - n} more files")
                    print()

        # Verbose output
        if verbose:
            print(f"\n" + "=" * 80)
            print("DETAILED BREAKDOWN")
            print("=" * 80)

            if stats['unique_ecdsa_issuers']:
                print(f"\nUnique ECDSA Issuers ({len(stats['unique_ecdsa_issuers'])}):")
                for issuer in sorted(stats['unique_ecdsa_issuers']):
                    print(f"  - {issuer}")

            if stats['unique_rsa_issuers']:
                print(f"\nUnique RSA Issuers ({len(stats['unique_rsa_issuers'])}):")
                for issuer in sorted(stats['unique_rsa_issuers']):
                    print(f"  - {issuer}")

            if stats['unique_ecdsa_root_ca_sns']:
                print(f"\nUnique ECDSA Root CA Serial Numbers ({len(stats['unique_ecdsa_root_ca_sns'])}):")
                for ecdsa_root_ca_sn in sorted(stats['unique_ecdsa_root_ca_sns'].keys()):
                    print(f"  - {ecdsa_root_ca_sn} ({len(stats['unique_ecdsa_root_ca_sns'][ecdsa_root_ca_sn])} files):")
                    for file_path in sorted(stats['unique_ecdsa_root_ca_sns'][ecdsa_root_ca_sn]):
                        print(f"    - {file_path}")

            if stats['unique_rsa_root_ca_sns']:
                print(f"\nUnique RSA Root CA Serial Numbers ({len(stats['unique_rsa_root_ca_sns'])}):")
                for rsa_root_ca_sn in sorted(stats['unique_rsa_root_ca_sns'].keys()):
                    print(f"  - {rsa_root_ca_sn} ({len(stats['unique_rsa_root_ca_sns'][rsa_root_ca_sn])} files):")
                    for file_path in sorted(stats['unique_rsa_root_ca_sns'][rsa_root_ca_sn]):
                        print(f"    - {file_path}")

        # Add missing files
        if add_missing_files and target_path:
            print(f"\n" + "=" * 80)
            print("SCANNING FOR MISSING KEYBOX FILES")
            print("=" * 80)

            missing_files_results = kb_add_missing_files(

                target_path=target_path,
                check_validity=True,
                dry_run=False,
                verbose=verbose
            )

            if missing_files_results:
                stats['missing_files_scan'] = missing_files_results
                print(f"Missing files scan completed:")
                print(f"  Files scanned: {missing_files_results['total_scanned']:>8,}")
                print(f"  Missing files found: {missing_files_results['missing_files_found']:>8,}")
                if 'valid_files' in missing_files_results:
                    print(f"  Valid files found: {len(missing_files_results['valid_files']):>8,}")
                    print(f"  Invalid files found: {len(missing_files_results['invalid_files']):>8,}")
                print(f"  Files added to kb_index: {missing_files_results['added_count']:>8,}")
        elif add_missing_files and not target_path:
            print(f"\n⚠️ Warning: add_missing_files requested but no target_path specified")

        print("=" * 80)
        return stats

    except Exception as e:
        print(f"❌ ERROR: Unexpected error during analysis: {e}")
        traceback.print_exc()
        return None


# ============================================================================
#                               Function update_kb_index_with_crl
# ============================================================================
def update_kb_index_with_crl():
    try:
        url = "https://android.googleapis.com/attestation/status"
        headers = {
            'Cache-Control': 'no-cache, max-age=0',
            'Pragma': 'no-cache'
        }

        print("Fetching Certificate Revocation List...")

        # Add timestamp to URL to ensure fresh data
        timestamp = int(time.time())
        cache_bust_url = f"{url}?_t={timestamp}"

        # Enhanced cache-busting headers
        fresh_headers = headers.copy()
        fresh_headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'Accept-Encoding': 'identity'
        })

        # Fetch CRL from server
        crl = request_with_fallback(method='GET', url=cache_bust_url, headers=fresh_headers, nocache=True)

        if crl is None or crl == 'ERROR':
            print(f"❌ ERROR: Could not fetch CRL from {url}")
            return {'error': 'Failed to fetch CRL'}

        crl_data = crl.json()

        # Load kb_index
        kb_index = load_kb_index()
        if not kb_index:
            print("❌ ERROR: No kb_index.json data found or file is empty.")
            return {'error': 'No kb_index data found'}

        # Extract revoked entries from CRL
        revoked_entries = set()
        if 'entries' in crl_data:
            for entry_key in crl_data['entries'].keys():
                revoked_entries.add(entry_key.strip().lower())

        print(f"Processing {len(kb_index)} keybox entries against {len(revoked_entries)} revoked certificates...")

        # Track changes
        changes_summary = {
            'total_entries_checked': len(kb_index),
            'entries_modified': 0,
            'ecdsa_leaf_revoked': [],
            'ecdsa_chain_revoked': [],
            'rsa_leaf_revoked': [],
            'rsa_chain_revoked': [],
            'total_changes': 0
        }

        # Process each entry in kb_index
        for ecdsa_sn, entry in kb_index.items():
            entry_modified = False
            changes_for_entry = []

            # Check ECDSA serial number (leaf certificate)
            if entry.get('ecdsa_sn'):
                ecdsa_sn_check = entry['ecdsa_sn'].strip().lower()
                if ecdsa_sn_check in revoked_entries and entry.get('ecdsa_leaf') != 'revoked':
                    old_value = entry.get('ecdsa_leaf', 'unknown')
                    entry['ecdsa_leaf'] = 'revoked'
                    changes_for_entry.append(f"ecdsa_leaf: '{old_value}' → 'revoked'")
                    changes_summary['ecdsa_leaf_revoked'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'old_value': old_value
                    })
                    entry_modified = True

            # Check ECDSA issuer (certificate chain)
            if entry.get('ecdsa_issuer'):
                ecdsa_issuer_check = entry['ecdsa_issuer'].strip().lower()
                if ecdsa_issuer_check in revoked_entries and entry.get('ecdsa_chain') != 'revoked':
                    old_value = entry.get('ecdsa_chain', 'unknown')
                    entry['ecdsa_chain'] = 'revoked'
                    changes_for_entry.append(f"ecdsa_chain: '{old_value}' → 'revoked'")
                    changes_summary['ecdsa_chain_revoked'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'ecdsa_issuer': ecdsa_issuer_check,
                        'old_value': old_value
                    })
                    entry_modified = True

            # Check RSA serial number (leaf certificate)
            if entry.get('rsa_sn'):
                rsa_sn_check = entry['rsa_sn'].strip().lower()
                if rsa_sn_check in revoked_entries and entry.get('rsa_leaf') != 'revoked':
                    old_value = entry.get('rsa_leaf', 'unknown')
                    entry['rsa_leaf'] = 'revoked'
                    changes_for_entry.append(f"rsa_leaf: '{old_value}' → 'revoked'")
                    changes_summary['rsa_leaf_revoked'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'rsa_sn': rsa_sn_check,
                        'old_value': old_value
                    })
                    entry_modified = True

            # Check RSA issuer (certificate chain)
            if entry.get('rsa_issuer'):
                rsa_issuer_check = entry['rsa_issuer'].strip().lower()
                if rsa_issuer_check in revoked_entries and entry.get('rsa_chain') != 'revoked':
                    old_value = entry.get('rsa_chain', 'unknown')
                    entry['rsa_chain'] = 'revoked'
                    changes_for_entry.append(f"rsa_chain: '{old_value}' → 'revoked'")
                    changes_summary['rsa_chain_revoked'].append({
                        'ecdsa_sn': ecdsa_sn,
                        'rsa_issuer': rsa_issuer_check,
                        'old_value': old_value
                    })
                    entry_modified = True

            # Update last_updated timestamp if entry was modified
            if entry_modified:
                entry['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                changes_summary['entries_modified'] += 1
                changes_summary['total_changes'] += len(changes_for_entry)
                print(f"🏷️ Updated ECDSA SN {ecdsa_sn}:")
                for change in changes_for_entry:
                    print(f"    - {change}")

                # Show files associated with this keybox
                files = entry.get('files', [])
                print(f"    Files ({len(files)}):")
                for file_entry in files:
                    file_path = file_entry.get('path', '') if isinstance(file_entry, dict) else str(file_entry)
                    print(f"      - {file_path}")
                print()

        # Save updated kb_index if there were changes
        if changes_summary['entries_modified'] > 0:
            save_kb_index(kb_index)
            print(f"\n✅ Updated kb_index.json with {changes_summary['entries_modified']} modified entries")
        else:
            print("\n✅ No entries needed to be updated based on current CRL")

        # Print summary report
        print("\n" + "=" * 80)
        print("KEYBOX INDEX CRL UPDATE SUMMARY")
        print("=" * 80)
        print(f"Total entries checked:            {changes_summary['total_entries_checked']:>8,}")
        print(f"Entries modified:                 {changes_summary['entries_modified']:>8,}")
        print(f"Total individual changes:         {changes_summary['total_changes']:>8,}")
        print()
        print(f"ECDSA leaf certificates revoked:  {len(changes_summary['ecdsa_leaf_revoked']):>8,}")
        print(f"ECDSA chain certificates revoked: {len(changes_summary['ecdsa_chain_revoked']):>8,}")
        print(f"RSA leaf certificates revoked:    {len(changes_summary['rsa_leaf_revoked']):>8,}")
        print(f"RSA chain certificates revoked:   {len(changes_summary['rsa_chain_revoked']):>8,}")
        print("=" * 80)

        return changes_summary

    except Exception as e:
        print(f"❌ ERROR: Encountered an error in update_kb_index_with_crl function")
        traceback.print_exc()
        return {'error': str(e)}


# ============================================================================
#                               Function get_boot_image_info
# ============================================================================
def get_boot_image_info(boot_image_path):
    try:
        tool = avbtool.AvbTool()
        if not os.path.exists(boot_image_path):
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Boot image file not found: {boot_image_path}")
            return
        info = tool.run(['avbtool.py','info_image', '--image', boot_image_path])
        print('')
        return info

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_boot_image_info function")
        print(e)
        traceback.print_exc()


# ============================================================================
#                               Function add_hash_footer
# ============================================================================
def add_hash_footer(boot_image_path,
                    partition_size,
                    partition_name,
                    salt,
                    rollback_index,
                    algorithm,
                    hash_algorithm,
                    prop_com_android_build_boot_os_version,
                    prop_com_android_build_boot_fingerprint,
                    prop_com_android_build_boot_security_patch_level
                ):

    try:
        tool = avbtool.AvbTool()
        tool.run(['avbtool.py','add_hash_footer',
                    '--image', boot_image_path,
                    '--partition_size', partition_size,
                    '--partition_name', partition_name,
                    '--salt', salt,
                    '--rollback_index', rollback_index,
                    '--key', os.path.join(get_bundle_dir(), 'testkey_rsa4096.pem'),
                    '--algorithm', algorithm,
                    '--hash_algorithm', hash_algorithm,
                    '--prop', f'com.android.build.boot.os_version:{prop_com_android_build_boot_os_version}',
                    '--prop', f'com.android.build.boot.fingerprint:{prop_com_android_build_boot_fingerprint}',
                    '--prop', f'com.android.build.boot.security_patch:{prop_com_android_build_boot_security_patch_level}'
                ])

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in add_hash_footer function")
        print(e)
        traceback.print_exc()


# ============================================================================
#                               Function run_tool
# ============================================================================
def run_tool(tool_details):
    try:
        config = get_config()
        command = tool_details['command']
        arguments = tool_details['arguments']
        directory = tool_details['directory']
        method = tool_details.get('method', 'Method 3')
        if method == 'Method 1':
            shell_method = 'run_shell'
        elif method == 'Method 2':
            shell_method = 'run_shell2'
        elif method == 'Method 3':
            shell_method = 'run_shell3'
        elif method == 'Method 4':
            # this one is not a function
            shell_method = 'run_shell4'
        detached = tool_details.get('detached', True)

        theCmd = f"\"{command}\" {arguments}"
        if sys.platform.startswith("win"):
            debug(theCmd)
            if shell_method == 'run_shell4':
                subprocess.Popen(theCmd, creationflags=subprocess.CREATE_NEW_CONSOLE, start_new_session=detached, env=get_env_variables())
            else:
                # Dynamic function invocation
                res = globals()[shell_method](theCmd, directory=directory, detached=detached, creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform.startswith("linux") and config.linux_shell:
            theCmd = f"{get_linux_shell()} -- /bin/bash -c {theCmd}"
            debug(theCmd)
            if shell_method == 'run_shell4':
                subprocess.Popen(theCmd, start_new_session=detached)
            else:
                # Dynamic function invocation
                res = globals()[shell_method](theCmd, detached=detached)
        elif sys.platform.startswith("darwin"):
            script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sh')
            script_file_content = f'#!/bin/bash\n{theCmd}\nrm "{script_file.name}"'
            debug(script_file_content)
            script_file.write(script_file_content.encode('utf-8'))
            script_file.close()
            os.chmod(script_file.name, 0o755)
            theCmd = f"osascript -e 'tell application \"Terminal\" to do script \"{script_file.name}\"'"
            debug(theCmd)
            if shell_method == 'run_shell4':
                subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{script_file.name}"'], start_new_session=detached, env=get_env_variables())
            else:
                # Dynamic function invocation with additional environment variables
                res = globals()[shell_method](theCmd, detached=detached, env=get_env_variables())

        return 0
    except Exception as e:
        print(f"Failed to run tool: {e}")


# ============================================================================
#                           Function get_db_con
# ============================================================================
def get_db_con():
    try:
        con = get_db()
        if con is None:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get database connection.")
            return None
        con.execute("PRAGMA foreign_keys = ON")
        con.commit()
        return con
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_db_con function")
        traceback.print_exc()
        return None


# ============================================================================
#               Function find_package_ids_with_same_package_boot_hash
# ============================================================================
def find_package_ids_with_same_package_boot_hash(boot_hash):
    con = get_db_con()
    if con is None:
        return []

    sql = """
        SELECT p.id
        FROM PACKAGE p
        WHERE p.boot_hash = ?;
    """
    try:
        with con:
            data = con.execute(sql, (boot_hash,))
            package_ids = [row[0] for row in data.fetchall()]
        return package_ids
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while fetching package IDs.")
        puml("#red:Encountered an error while fetching package IDs;\n", True)
        traceback.print_exc()
        return []


# ============================================================================
#               Function get_package_sig
# ============================================================================
def get_package_sig(package_id):
    con = get_db_con()
    if con is None:
        return None

    sql = """
        SELECT p.package_sig
        FROM PACKAGE p
        WHERE p.id = ?;
    """
    try:
        with con:
            data = con.execute(sql, (package_id,))
            row = data.fetchone()
            if row:
                return row[0]
            else:
                return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while fetching package_sig.")
        puml("#red:Encountered an error while fetching package_sig;\n", True)
        traceback.print_exc()
        return None


# ============================================================================
#               Function get_boot_id_by_file_path
# ============================================================================
def get_boot_id_by_file_path(file_path):
    con = get_db_con()
    if con is None:
        return None

    sql = """
        SELECT b.id
        FROM boot b
        WHERE b.file_path = ?;
    """
    try:
        with con:
            data = con.execute(sql, (file_path,))
            row = data.fetchone()
            if row:
                return row[0]
            else:
                return None
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function get_boot_id_by_file_path.")
        puml("#red:Encountered an error in function get_boot_id_by_file_path;\n", True)
        traceback.print_exc()
        return None


# ============================================================================
#               Function delete_package_boot_record
# ============================================================================
def delete_package_boot_record(boot_id, package_id):
    con = get_db_con()
    if con is None or boot_id is None or package_id is None or boot_id == 0 or package_id == 0 or boot_id == '' or package_id == '':
        return False

    sql = """
        DELETE FROM PACKAGE_BOOT
        WHERE boot_id = ? AND package_id = ?;
    """
    try:
        with con:
            con.execute(sql, (boot_id, package_id))
        con.commit()
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function delete_package_boot_record.")
        puml("#red:Encountered an error in function delete_package_boot_record;\n", True)
        traceback.print_exc()
        return False


# ============================================================================
#               Function delete_boot_record
# ============================================================================
def delete_boot_record(boot_id, delete_file=''):
    con = get_db_con()
    if con is None or boot_id is None or boot_id == 0 or boot_id == '':
        return None

    sql = """
        DELETE FROM BOOT
        WHERE id = ?;
    """
    try:
        with con:
            data = con.execute(sql, (boot_id,))
        con.commit()
        print(f"Cleared db entry for BOOT: {boot_id}")
        # delete the boot file
        if delete_file != '':
            print(f"Deleting Boot file: {delete_file} ...")
            if os.path.exists(delete_file):
                os.remove(delete_file)
                boot_dir = os.path.dirname(delete_file)
                # if deleting init_boot.img and boot.img exists, delete that as well
                boot_img_path = os.path.join(boot_dir, 'boot.img')
                if os.path.exists(boot_img_path) and delete_file.endswith('init_boot.img'):
                    print(f"Deleting {boot_img_path} ...")
                    os.remove(boot_img_path)
            else:
                print(f"⚠️ Warning: Boot file: {delete_file} does not exist")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function delete_boot_record.")
        puml("#red:Encountered an error in function delete_boot_record;\n", True)
        traceback.print_exc()
        return None


# ============================================================================
#               Function delete_last_boot_record
# ============================================================================
def delete_last_boot_record(boot_id, boot_path=''):
    con = get_db_con()
    if con is None or boot_id is None or boot_id == 0 or boot_id == '':
        return False

    # Check to see if this is the last entry for the boot_id, if it is delete it,
    try:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM PACKAGE_BOOT WHERE boot_id = ?", (boot_id,))
        data = cursor.fetchall()
        if len(data) == 0:
            # delete the boot from db
            delete_boot_record(boot_id, boot_path)
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function delete_last_boot_record.")
        puml("#red:Encountered an error in function delete_last_boot_record;\n", True)
        traceback.print_exc()
        print("Aborting ...")
        return False

# ============================================================================
#               Function delete_last_package_record
# ============================================================================
# Check to see if this is the last entry for the package_id, if it is,
# delete the package from db and output a message that a firmware should be selected.
# Also delete unpacked files from factory_images cache
def delete_last_package_record(package_ids, boot_dir):
    con = get_db_con()
    if con is None:
        return False

    try:
        cursor = con.cursor()
        package_ids_tuple = tuple(package_ids)
        placeholders = []
        for unused in package_ids_tuple:
            placeholders.append('?')
        placeholders = ','.join(placeholders)
        query = f"SELECT * FROM PACKAGE_BOOT WHERE package_id IN ({placeholders})"
        cursor.execute(query, package_ids_tuple)
        data = cursor.fetchall()
        if len(data) == 0:
            delete_package = True
            # see if there are any other files in the directory
            files = get_filenames_in_dir(boot_dir)
            if files:
                delete_package = False

            if delete_package:
                config_path = get_config_path()
                for package_id in package_ids:
                    package_sig = get_package_sig(package_id)
                    sql = """
                        DELETE FROM PACKAGE
                        WHERE id = ?;
                    """
                    with con:
                        con.execute(sql, (package_id,))
                    con.commit()
                    if package_sig:
                        print(f"Cleared db entry for PACKAGE: {package_sig}")
                        package_path = os.path.join(config_path, 'factory_images', package_sig)
                        with contextlib.suppress(Exception):
                            print(f"Deleting Firmware cache for: {package_path} ...")
                            delete_all(package_path)
                    else:
                        print(f"⚠️ Warning: Package Signature for package_id: {package_id} does not exist")
        return True
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function delete_last_package_record.")
        puml("#red:Encountered an error in function delete_last_package_record;\n", True)
        traceback.print_exc()
        print("Aborting ...")
        return False


# ============================================================================
#               Function insert_boot_record
# ============================================================================
def insert_boot_record(boot_hash, file_path, is_patched, magisk_version, hardware, patch_method, is_odin, is_stock_boot, is_init_boot, patch_source_sha1):
    con = get_db_con()
    if con is None:
        return None

    try:
        cursor = con.cursor()
        sql = """
            INSERT INTO BOOT (boot_hash, file_path, is_patched, magisk_version, hardware, epoch, patch_method, is_odin, is_stock_boot, is_init_boot, patch_source_sha1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (boot_hash) DO NOTHING
        """
        data = (boot_hash, file_path, is_patched, magisk_version, hardware, time.time(), patch_method, is_odin, is_stock_boot, is_init_boot, patch_source_sha1)
        debug(f"Creating BOOT record, boot_hash: {boot_hash}")
        try:
            cursor.execute(sql, data)
            con.commit()
            boot_id = cursor.lastrowid
            debug(f"DB BOOT record ID: {boot_id}")
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while inserting BOOT record.")
            puml("#red:Encountered an error while inserting BOOT record;\n", True)
            traceback.print_exc()
            boot_id = 0
        return boot_id
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function insert_boot_record.")
        puml("#red:Encountered an error in function insert_boot_record;\n", True)
        traceback.print_exc()
        return 0


# ============================================================================
#               Function insert_package_boot_record
# ============================================================================
def insert_package_boot_record(package_id, boot_id):
    con = get_db_con()
    if con is None:
        return None

    try:
        cursor = con.cursor()

        sql = """
            INSERT INTO PACKAGE_BOOT (package_id, boot_id, epoch)
            VALUES (?, ?, ?)
            ON CONFLICT (package_id, boot_id) DO NOTHING
        """
        data = (package_id, boot_id, time.time())
        try:
            cursor.execute(sql, data)
            con.commit()
            package_boot_id = cursor.lastrowid
            debug(f"DB Package_Boot record ID: {package_boot_id}\n")
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while inserting PACKAGE_BOOT record.")
            puml("#red:Encountered an error while inserting PACKAGE_BOOT record;\n", True)
            traceback.print_exc()
            package_boot_id = 0
        return package_boot_id
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function insert_package_boot_record.")
        puml("#red:Encountered an error in function insert_package_boot_record;\n", True)
        traceback.print_exc()
        return 0


# ============================================================================
#                               Function magisk_apks
# ============================================================================
def get_rooting_app_apks():
    global _rooting_app_apks
    if _rooting_app_apks is None:
        try:
            apks = []
            mlist = [
                'Magisk Stable',
                'Magisk Beta',
                'Magisk Debug',
                'Magisk Release',
                'Magisk Pre-Release',
                'KitsuneMagisk Fork',
                "KernelSU",
                'KernelSU-Next',
                'APatch',
                "SukiSU",
                "Wild_KSU",
                "Magisk zygote64_32 canary",
                "Magisk special 30600",
                "Magisk special 27001",
                "Magisk special 26401",
                'Magisk special 25203'
            ]
            for i in mlist:
                wx.Yield()
                apk = get_rooting_app_details(i)
                if apk:
                    apks.append(apk)
            _rooting_app_apks = apks
        except Exception as e:
            _rooting_app_apks is None
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Rooting App downloads link: {i} processing")
            traceback.print_exc()
    return _rooting_app_apks


# ============================================================================
#                               Function get_rooting_app_details
# ============================================================================
def get_rooting_app_details(channel):
    ma = MagiskApk(channel)
    if channel == 'Magisk Stable':
        url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json"

    elif channel == 'Magisk Beta':
        url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json"

    elif channel == 'Magisk Canary':
        url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json"

    elif channel == 'Magisk Debug':
        url = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/debug.json"

    elif channel == 'Magisk Alpha':
        try:
            # Now published at appcenter: https://install.appcenter.ms/users/vvb2060/apps/magisk/distribution_groups/public
            info_endpoint = "https://install.appcenter.ms/api/v0.1/apps/vvb2060/magisk/distribution_groups/public/public_releases?scope=tester"
            release_endpoint = "https://install.appcenter.ms/api/v0.1/apps/vvb2060/magisk/distribution_groups/public/releases/{}"
            res = request_with_fallback(method='GET', url=info_endpoint)
            latest_id = res.json()[0]['id']
            res = request_with_fallback(method='GET', url=release_endpoint.format(latest_id))
            latest_release = res.json()
            setattr(ma, 'version', latest_release['short_version'])
            setattr(ma, 'versionCode', latest_release['version'])
            setattr(ma, 'link', latest_release['download_url'])
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', latest_release['bundle_identifier'])
            setattr(ma, 'release_notes', latest_release['release_notes'])
            return ma
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Alpha processing")
            traceback.print_exc()
            return
    elif channel == 'KitsuneMagisk Fork':
        url = "https://1q23lyc45.github.io/canary.json"

    elif channel == 'Magisk Delta Canary':
        url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/canary.json"

    elif channel == 'Magisk Delta Debug':
        url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/debug.json"

    elif channel == 'Magisk Release':
        try:
            # https://github.com/topjohnwu/Magisk/releases
            release = get_gh_release_object(user='topjohnwu', repo='Magisk', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^Magisk.*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find Magisk Release APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = f"{release_version.replace('v', '').replace('.', '')}00"
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', MAGISK_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk Release processing")
            traceback.print_exc()
            return

    elif channel == 'Magisk Pre-Release':
        try:
            # https://github.com/topjohnwu/Magisk/releases
            release = get_gh_release_object(user='topjohnwu', repo='Magisk', include_prerelease=True, latest_any=True)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^Magisk.*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find Magisk Release APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_versionCode = f"{release_version.replace('v', '').replace('.', '')}00"
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', MAGISK_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk Release processing")
            traceback.print_exc()
            return

    elif channel == 'KernelSU':
        try:
            # https://github.com/tiann/KernelSU/releases
            release = get_gh_release_object(user='tiann', repo='KernelSU', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^KernelSU.*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find KernelSU APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_version
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', KERNEL_SU_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during KernelSU processing")
            traceback.print_exc()
            return

    elif channel == 'KernelSU-Next':
        try:
            # https://github.com/rifsxd/KernelSU-Next/releases
            release = get_gh_release_object(user='rifsxd', repo='KernelSU-Next', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^KernelSU_Next(?!.*spoofed).*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find KernelSU-Next APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_version
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', KSU_NEXT_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during KernelSU-Next processing")
            traceback.print_exc()
            return

    elif channel == 'SukiSU':
        try:
            # https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases
            release = get_gh_release_object(user='SukiSU-Ultra', repo='SukiSU-Ultra', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^SukiSU.*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find SukiSU APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_version
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', SUKISU_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during SukiSU processing")
            traceback.print_exc()
            return

    elif channel == 'Wild_KSU':
        try:
            # https://github.com/WildKernels/Wild_KSU/releases
            release = get_gh_release_object(user='WildKernels', repo='Wild_KSU', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^Wild_KSU(?!.*spoofed).*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find Wild_KSU APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_version
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', WILD_KSU_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Wild_KSU processing")
            traceback.print_exc()
            return

    elif channel == 'APatch':
        try:
            # https://github.com/bmax121/APatch/releases
            release = get_gh_release_object(user='bmax121', repo='APatch', include_prerelease=False, latest_any=False)
            if release:
                release_version = release['tag_name']
                release_notes = release['body']
                release_url = gh_asset_utility(release_object=release, asset_name_pattern=r'^APatch_.*\.apk$', download=False)
                if release_notes is None:
                    release_version = "No release notes available"
                if release_url is None:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find APatch APK")
                    return
                match = re.search(r'_([0-9]+)-', release_url)
                if match:
                    release_versionCode =  match.group(1)
                else:
                    if release_version:
                        release_versionCode = release_version
                    else:
                        release_versionCode = 0
                setattr(ma, 'version', release_version)
                setattr(ma, 'versionCode', release_versionCode)
                setattr(ma, 'link', release_url)
                setattr(ma, 'note_link', "note_link")
                setattr(ma, 'package', APATCH_PKG_NAME)
                setattr(ma, 'release_notes', release_notes)
                return ma
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find {channel} on GitHub")
                return
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during APatch processing")
            traceback.print_exc()
            return

    elif channel == 'Magisk zygote64_32 stable':
        url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/stable.json"

    elif channel == 'Magisk zygote64_32 beta':
        url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/beta.json"

    elif channel == 'Magisk zygote64_32 canary':
        # url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/canary.json"
        url = "https://raw.githubusercontent.com/ActiveIce/Magisk_zygote64_32/master/canary.json"

    elif channel == 'Magisk zygote64_32 debug':
        url = "https://raw.githubusercontent.com/Namelesswonder/magisk-files/main/debug.json"

    elif channel == 'Magisk special 25203':
        url = ""
        setattr(ma, 'version', "f9e82c9e")
        setattr(ma, 'versionCode', "25203")
        setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_25203/app-release.apk")
        setattr(ma, 'note_link', "note_link")
        setattr(ma, 'package', MAGISK_PKG_NAME)
        release_notes = """
## 2022.10.03 Special Magisk v25.2 Build\n\n
This is a special Magisk build by XDA Member [gecowa6967](https://xdaforums.com/m/gecowa6967.11238881/)\n\n
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
### Full Details: [here](https://xdaforums.com/t/magisk-general-support-discussion.3432382/page-2667#post-87520397)\n
        """
        setattr(ma, 'release_notes', release_notes)
        return ma

    elif channel == 'Magisk special 26401':
        url = ""
        setattr(ma, 'version', "76aef836")
        setattr(ma, 'versionCode', "26401")
        setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_26401/app-release.apk")
        setattr(ma, 'note_link', "note_link")
        setattr(ma, 'package', MAGISK_PKG_NAME)
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
    elif channel == 'Magisk special 27001':
        url = ""
        setattr(ma, 'version', "79fd3e40")
        setattr(ma, 'versionCode', "27001")
        setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_27001/app-release.apk")
        setattr(ma, 'note_link', "note_link")
        setattr(ma, 'package', MAGISK_PKG_NAME)
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
    elif channel == 'Magisk special 30600':
        url = ""
        setattr(ma, 'version', "0d63870f")
        setattr(ma, 'versionCode', "30600")
        setattr(ma, 'link', "https://github.com/badabing2005/Magisk/releases/download/versionCode_30600/app-release.apk")
        setattr(ma, 'note_link', "note_link")
        setattr(ma, 'package', MAGISK_PKG_NAME)
        release_notes = """
## 2025.12.05 Special Magisk v30.6 Build\n\n
This is a special Magisk build\n\n
- Based on build versionCode: 30600 versionName: 0d63870f\n
- Modified to disable loading modules while keep root.\n
- Made to recover from bootloops due to bad / incompatible Modules.\n\n
### Steps to follow [here](https://github.com/badabing2005/Magisk)\n
        """
        setattr(ma, 'release_notes', release_notes)
        return ma

    else:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unknown Magisk channel {channel}\n")
        return

    try:
        payload={}
        headers = {
            'Content-Type': "application/json"
        }
        response = request_with_fallback(method='GET', url=url, headers=headers, data=payload)
        if response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get Magisk downloads links: {url}")
            return
        data = response.json()
        setattr(ma, 'version', data['magisk']['version'])
        setattr(ma, 'versionCode', data['magisk']['versionCode'])
        setattr(ma, 'link', data['magisk']['link'])
        note_link = data['magisk']['note']
        setattr(ma, 'note_link', note_link)
        setattr(ma, 'package', MAGISK_PKG_NAME)
        if channel in ['Magisk Delta Canary', 'Magisk Delta Debug', 'KitsuneMagisk Fork']:
            setattr(ma, 'package', MAGISK_DELTA_PKG_NAME)
        # Get the note contents
        headers = {}
        with contextlib.suppress(Exception):
            setattr(ma, 'release_notes', '')
            response = request_with_fallback(method='GET', url=ma.note_link, headers=headers, data=payload)
            if response.status_code != 200:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not get Magisk download release_notes: {url}")
                return
            setattr(ma, 'release_notes', response.text)
        return ma
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads links: {url} processing")
        traceback.print_exc()
        return


# ============================================================================
#                    Function parse_bootloader_version
# ============================================================================
def parse_bootloader_version(version):
    # Parse version string in format "Major.minor-patch"
    if not version:
        return None
    try:
        major_minor, patch = version.split('-', 1)
        major, minor = major_minor.split('.', 1)
        return (int(major), int(minor), int(patch))
    except (ValueError, AttributeError):
        print(f"⚠️ Warning: Unable to parse bootloader version: {version}")
        return None


# ============================================================================
#                    Function is_bootloader_version_older
# ============================================================================
def is_bootloader_version_older(version, min_version):
    v1 = parse_bootloader_version(version)
    v2 = parse_bootloader_version(min_version)
    if not v1 or not v2:
        # Can't determine, assume it's not older
        return False

    # Compare major.minor-patch components
    return (v1[0] < v2[0] or
            (v1[0] == v2[0] and v1[1] < v2[1]) or
            (v1[0] == v2[0] and v1[1] == v2[1] and v1[2] < v2[2]))


# ============================================================================
#                    Function get_bootloader_versions
# ============================================================================
def get_bootloader_versions():
    try:
        device = get_phone()
        if not device:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: You must first select a valid device.")
            return

        if not device.rooted:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device is not rooted.")
            puml("#red:Device is not rooted;\n}\n")
            return

        res = device.get_partitions()
        if res == -1:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get partitions from the device, aborting ...")
            puml("#red:Failed to get partitions from the device;\n}\n")
            return


        if 'abl_a' not in res or 'abl_b' not in res:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Device does not have abl_a and/or abl_b partitions, aborting ...")
            puml("#red:Device does not have abl_a and abl_b partitions;\n}\n")
            return

        # first delete existing abl_a and abl_b dumps if it exists on the phone
        path = "/data/local/tmp/abl_a.img"
        res = device.delete(path, True)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to delete old abl_a image from the phone;\n}\n")
            return
        path = "/data/local/tmp/abl_b.img"
        res = device.delete(path, True)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to delete old abl_b image from the phone;\n}\n")
            return

        # dump abl_a and abl_b to the phone
        res, file_path = device.dump_partition(partition='abl', slot='a')
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to dump abl_a partition to the phone;\n}\n")
            return
        res, file_path = device.dump_partition(partition='abl', slot='b')
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to dump abl_a partition to the phone;\n}\n")
            return

        # pull abl_a and abl_b from the phone
        temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())
        path = "/data/local/tmp/abl_a.img"
        res = device.pull_file(path, os.path.join(temp_dir, "abl_a.img"), False)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to pull abl_a image from the phone;\n}\n")
            res = device.delete(path, True)
            return
        res = device.delete(path, True)
        path = "/data/local/tmp/abl_b.img"
        res = device.pull_file(path, os.path.join(temp_dir, "abl_b.img"), False)
        if res != 0:
            print("Aborting ...\n")
            puml("#red:Failed to pull abl_b image from the phone;\n}\n")
            res = device.delete(path, True)
            return
        res = device.delete(path, True)

        # Open the bootloader versions from the dumped images
        with open(os.path.join(temp_dir, "abl_a.img"), 'rb') as f:
            abl_a_data = f.read()
        with open(os.path.join(temp_dir, "abl_b.img"), 'rb') as f:
            abl_b_data = f.read()

        # Get the device codename(s)
        android_device = get_android_devices()
        device_codenames = None
        if android_device:
            device_codenames = f"{android_device[device.hardware]['bootloader_codename']}-"

        # Convert single string codename to a list with one element if it's not already a list
        if device_codenames is not None and not isinstance(device_codenames, list):
            device_codenames = [device_codenames]

        if device_codenames is None:
            device_codenames = [
                b"cloudripper-", b"slider-", b"bluejay-", b"ripcurrent-",
                b"akita-", b"ripcurrentpro-"
            ]
        else:
            # Convert string codenames to bytes for compatibility with binary data search
            device_codenames = [codename.encode('utf-8') if isinstance(codename, str) else codename for codename in device_codenames]

        # Process abl_a
        abl_a_version = None
        for codename in device_codenames:
            pos = abl_a_data.find(codename)
            if pos != -1:
                prefix_len = len(codename)
                pos += prefix_len
                end_pos = abl_a_data.find(b'\x00', pos)
                if end_pos != -1:
                    abl_a_version = abl_a_data[pos:end_pos].decode('utf-8').strip('\x00')
                    debug(f"Found bootloader version in abl_a.img with prefix {codename.decode()}")
                    break
        if abl_a_version is None:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find bootloader version in abl_a.img")
            puml("#red:Could not find bootloader version in abl_a.img;\n}\n")
            return

        # Process abl_b
        abl_b_version = None
        for codename in device_codenames:
            pos = abl_b_data.find(codename)
            if pos != -1:
                prefix_len = len(codename)
                pos += prefix_len
                end_pos = abl_b_data.find(b'\x00', pos)
                if end_pos != -1:
                    abl_b_version = abl_b_data[pos:end_pos].decode('utf-8').strip('\x00')
                    debug(f"Found bootloader version in abl_b.img with prefix {codename.decode()}")
                    break
        if abl_b_version is None:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find bootloader version in abl_b.img")
            puml("#red:Could not find bootloader version in abl_b.img;\n}\n")
            return

        # Define the minimum safe versions for different ARB effected devices
        min_versions = {
            "bluejay": "15.3-13239612",
            "oriole": "15.3-13239612",
            "raven": "15.3-13239612",
            "akita": "15.3-13266201",
            "shiba": "15.3-13272266",
            "husky": "15.3-13272266"
        }

        print("\n=================================================")
        print(f"Slot A Bootloader Version: {abl_a_version}")
        print(f"Slot B Bootloader Version: {abl_b_version}")

        # see if any of the devices are at risk of bricking due to Anti-Rollback Protection `ARB`
        if device.hardware in min_versions:
            min_safe_version = min_versions[device.hardware]

            # Check slot A
            if is_bootloader_version_older(abl_a_version, min_safe_version):
                print(f"\n☠️ WARNING: Slot A bootloader version {abl_a_version} is older than the minimum safe version {min_safe_version}")
                print(f"☠️ Your device may be at risk of bricking due to Anti-Rollback Protection (ARB)")
                puml(f"note right #yellow\nWARNING: Slot A bootloader version {abl_a_version} is older than\nthe minimum safe version {min_safe_version}\nYour device may be at risk of bricking due to ARB\nend note\n")
            else:
                print(f"✅ Slot A bootloader version {abl_a_version} is safe because it is newer than the minimum safe version {min_safe_version}")

            # Check slot B
            if is_bootloader_version_older(abl_b_version, min_safe_version):
                print(f"\n☠️ WARNING: Slot B bootloader version {abl_b_version} is older than the minimum safe version {min_safe_version}")
                print(f"☠️ Your device may be at risk of bricking due to Anti-Rollback Protection (ARB)")
                puml(f"note right #yellow\nWARNING: Slot B bootloader version {abl_b_version} is older than\nthe minimum safe version {min_safe_version}\nYour device may be at risk of bricking due to ARB\nend note\n")
            else:
                print(f"✅ Slot B bootloader version {abl_b_version} is safe because it is newer than the minimum safe version {min_safe_version}")
        else:
            print(f"\nℹ️ Info: Device hardware {device.hardware} is not currently in PixelFlasher's Anti-Rollback Protection (ARB) checks")
            print("Please report this to the author if you think it should be included.")

        print("=================================================\n")
        puml(f"note right\nABL_A Version: {abl_a_version}\nABL_B Version: {abl_b_version}\nend note\n")

    except IOError:
        traceback.print_exc()
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            debug(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: cleaning up temp directory: {str(e)}")


# ============================================================================
#                               Function extract_strings
# ============================================================================
def extract_strings(filename):
    with open(filename, "rb") as f:
        data = f.read()
    return re.findall(rb'[\x20-\x7E]{4,}', data)


# ============================================================================
#                               Function extract_kernel_info
# ============================================================================
def extract_kernel_info(boot_img_path):
    strings = [s.decode(errors="ignore") for s in extract_strings(boot_img_path)]
    version_regex = re.compile(r'^\d+\.\d+\.\d+[-\w]+')
    date_regex = re.compile(r'(?:#\d+ )?SMP PREEMPT .+\d{4}')

    # Step 1: Get the prefix portion, don't look into multiline strings
    prefix = None
    for i, line in enumerate(strings):
        if version_regex.match(line):
            prefix = line
            break

    # Step 2: Get the longest candidate by searching all lines
    version_regex2 = re.compile(r'\d+\.\d+\.\d+[-\w]+')
    version_candidates = []
    date_candidates = []

    for line in strings:
        vmatch = version_regex2.search(line)
        if vmatch:
            version_candidates.append(vmatch.group(0))
        dmatch = date_regex.search(line)
        if dmatch:
            date_candidates.append(dmatch.group(0))

    build_number = max(version_candidates, key=len) if version_candidates else None
    build_date = max(date_candidates, key=len) if date_candidates else None

    # Step 3: Filter out anything before the prefix in the longest candidate
    if prefix and build_number and prefix in build_number:
        idx = build_number.index(prefix)
        build_number = build_number[idx:]

    return build_number, build_date


# ============================================================================
#                               Function run_shell
# ============================================================================
# We use this when we want to capture the returncode and also selectively
# output what we want to console. Nothing is sent to console, both stdout and
# stderr are only available when the call is completed.
def run_shell(cmd, timeout=None, encoding='ISO-8859-1'):
    try:
        flush_output()
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding=encoding, errors="replace", env=get_env_variables())
        # Wait for the process to complete or timeout
        stdout, stderr = process.communicate(timeout=timeout)
        # Return the response
        return subprocess.CompletedProcess(args=cmd, returncode=process.returncode, stdout=stdout, stderr=stderr)

    except subprocess.TimeoutExpired as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command {cmd} timed out after {timeout} seconds")
        puml("#red:Command {cmd} timed out;\n", True)
        puml(f"note right\n{e}\nend note\n")
        # Send CTRL + C signal to the process
        process.send_signal(signal.SIGTERM)
        process.terminate()
        return subprocess.CompletedProcess(args=cmd, returncode=-1, stdout='', stderr='')

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell {cmd}")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e
        # return subprocess.CompletedProcess(args=cmd, returncode=-2, stdout='', stderr='')


# ============================================================================
#                               Function run_shell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
def run_shell2(cmd, timeout=None, detached=False, directory=None, encoding='utf-8', chcp=None):
    try:
        flush_output()

        env = get_env_variables()
        env["PYTHONIOENCODING"] = encoding
        if chcp is not None:
            env["CHCP"] = chcp

        if directory is None:
            proc = subprocess.Popen(
                f"{cmd}",
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding=encoding,
                errors="replace",
                start_new_session=detached,
                env=env
            )
        else:
            proc = subprocess.Popen(
                f"{cmd}",
                cwd=directory,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding=encoding,
                errors="replace",
                start_new_session=detached,
                env=env
            )

        print
        while True:
            line = proc.stdout.readline()
            wx.YieldIfNeeded()
            if line.strip() != "":
                print(line.strip())
            if not line:
                break
            if timeout is not None and time.time() > timeout:
                proc.terminate()
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command {cmd} timed out after {timeout} seconds")
                puml("#red:Command timed out;\n", True)
                puml(f"note right\nCommand {cmd} timed out after {timeout} seconds\nend note\n")
                return subprocess.CompletedProcess(args=cmd, returncode=-1, stdout='', stderr='')
        proc.wait()
        # Wait for the process to complete and capture the output
        stdout, stderr = proc.communicate()
        return subprocess.CompletedProcess(args=cmd, returncode=proc.returncode, stdout=stdout, stderr=stderr)
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell2 {cmd}")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e
        # return subprocess.CompletedProcess(args=cmd, returncode=-2, stdout='', stderr='')


# ============================================================================
#                               Function run_shell3
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
def run_shell3(cmd, timeout=None, detached=False, directory=None, encoding='ISO-8859-1', creationflags=0, env=None):
    try:
        flush_output()
        proc_args = {
            "args": f"{cmd}",
            "shell": True,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "encoding": encoding,
            "errors": "replace",
            "start_new_session": detached,
        }
        if env is not None:
            proc_args["env"] = env
        if creationflags is not None:
            proc_args["creationflags"] = creationflags
        if directory is not None:
            proc_args["cwd"] = directory

        proc = subprocess.Popen(**proc_args)

        def read_output():
            print
            start_time = time.time()
            output = []
            while True:
                line = proc.stdout.readline()
                wx.YieldIfNeeded()
                if line.strip() != "":
                    print(line.strip())
                    output.append(line.strip())
                if not line:
                    break
                if timeout is not None and time.time() - start_time > timeout:
                    proc.terminate()
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command {cmd} timed out after {timeout} seconds")
                    puml("#red:Command timed out;\n", True)
                    puml(f"note right\nCommand {cmd} timed out after {timeout} seconds\nend note\n")
                    return subprocess.CompletedProcess(args=cmd, returncode=-1, stdout='\n'.join(output), stderr='')

        threading.Thread(target=read_output, daemon=True).start()
        if not detached:
            proc.wait()
        return proc

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell3 {cmd}")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e
        # return subprocess.CompletedProcess(args=cmd, returncode=-2, stdout='', stderr='')


# def run_shell(*args, **kwargs):
#     pr = cProfile.Profile()
#     pr.enable()
#     result = run_shell1(*args, **kwargs)  # Call your function here
#     pr.disable()
#     s = io.StringIO()
#     ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
#     ps.print_stats()

#     # Get the calling function and line number
#     stack = traceback.extract_stack()
#     filename, lineno, function_name, unused = stack[-3]  # -3 because -1 is current function, -2 is the function that called this function
#     print(f"Called from {function_name} at {filename}:{lineno}")

#     print(s.getvalue())
#     return result

