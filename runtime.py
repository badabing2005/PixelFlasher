#!/usr/bin/env python

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2024 Badabing2005
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
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import lz4.frame
import requests
import wx
from packaging.version import parse
from platformdirs import *
from constants import *
from payload_dumper import extract_payload
import cProfile, pstats, io
import avbtool

verbose = False
adb = None
fastboot = None
adb_sha256 = None
fastboot_sha256 = None
phones = []
device_list = []
phone_id = None
advanced_options = False
update_check = True
firmware_model = None
firmware_id = None
custom_rom_id = None
logfile = None
pumlfile = None
sdk_version = None
image_mode = None
image_path = None
custom_rom_file = None
message_box_title = None
message_box_message = None
version = None
db = None
boot = None
system_code_page = None
codepage_setting = False
codepage_value = ''
magisk_package = ''
file_explorer = ''
linux_shell = ''
patched_with = ''
customize_font = False
pf_font_face = ''
pf_font_size = 12
app_labels = {}
xiaomi_list = {}
favorite_pifs = {}
a_only = False
offer_patch_methods = False
use_busybox_shell = False
firmware_hash_valid = False
firmware_has_init_boot = False
rom_has_init_boot = False
dlg_checkbox_values = None
recovery_patch = False
config_path = None
android_versions = {}
android_devices = {}
env_variables = os.environ.copy()
is_ota = False
sdk_is_ok = False
low_memory = False
config = {}
config_file_path = ''
unlocked_devices = []
window_shown = False
puml_enabled = True
magisk_apks = None


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
        self.fingerprint = None


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
#                               Function get_config
# ============================================================================
def get_config():
    global config
    return config


# ============================================================================
#                               Function set_config
# ============================================================================
def set_config(value):
    global config
    config = value

# ============================================================================
#                               Function get_window_shown
# ============================================================================
def get_window_shown():
    global window_shown
    return window_shown

# ============================================================================
#                               Function set_window_shown
# ============================================================================
def set_window_shown(value):
    global window_shown
    window_shown = value

# ============================================================================
#                               Function check_for_unlocked
# ============================================================================
def check_for_unlocked(item):
    return item in unlocked_devices


# ============================================================================
#                               Function add_unlocked_device
# ============================================================================
def add_unlocked_device(item):
    if item not in unlocked_devices:
        unlocked_devices.append(item)


# ============================================================================
#                               Function remove_unlocked_device
# ============================================================================
def remove_unlocked_device(item):
    if item in unlocked_devices:
        unlocked_devices.remove(item)


# ============================================================================
#                               Function set_console_widget
# ============================================================================
def set_console_widget(widget):
    global console_widget
    console_widget = widget


# ============================================================================
#                               Function flush_output
# ============================================================================
def flush_output():
    global console_widget
    if get_window_shown():
        wx.YieldIfNeeded()
    if console_widget:
        sys.stdout.flush()
        wx.CallAfter(console_widget.Update)
        if get_window_shown():
            wx.YieldIfNeeded()


# ============================================================================
#                               Function get_boot
# ============================================================================
def get_boot():
    global boot
    return boot


# ============================================================================
#                               Function set_boot
# ============================================================================
def set_boot(value):
    global boot
    boot = value


# ============================================================================
#                               Function get_labels
# ============================================================================
def get_labels():
    global app_labels
    return app_labels


# ============================================================================
#                               Function set_labels
# ============================================================================
def set_labels(value):
    global app_labels
    app_labels = value


# ============================================================================
#                               Function get_xiaomi
# ============================================================================
def get_xiaomi():
    global xiaomi_list
    return xiaomi_list


# ============================================================================
#                               Function set_xiaomi
# ============================================================================
def set_xiaomi(value):
    global xiaomi_list
    xiaomi_list = value


# ============================================================================
#                               Function get_favorite_pifs
# ============================================================================
def get_favorite_pifs():
    global favorite_pifs
    return favorite_pifs


# ============================================================================
#                               Function set_favorite_pifs
# ============================================================================
def set_favorite_pifs(value):
    global favorite_pifs
    favorite_pifs = value


# ============================================================================
#                               Function get_low_memory
# ============================================================================
def get_low_memory():
    global low_memory
    return low_memory


# ============================================================================
#                               Function set_low_memory
# ============================================================================
def set_low_memory(value):
    global low_memory
    low_memory = value


# ============================================================================
#                               Function get_android_versions
# ============================================================================
def get_android_versions():
    global android_versions
    return android_versions


# ============================================================================
#                               Function set_android_versions
# ============================================================================
def set_android_versions(value):
    global android_versions
    android_versions = value


# ============================================================================
#                               Function get_android_devices
# ============================================================================
def get_android_devices():
    global android_devices
    return android_devices


# ============================================================================
#                               Function set_android_devices
# ============================================================================
def set_android_devices(value):
    global android_devices
    android_devices = value


# ============================================================================
#                               Function get_env_variables
# ============================================================================
def get_env_variables():
    global env_variables
    return env_variables


# ============================================================================
#                               Function set_env_variables
# ============================================================================
def set_env_variables(value):
    global env_variables
    env_variables = value


# ============================================================================
#                               Function get_patched_with
# ============================================================================
def get_patched_with():
    global patched_with
    return patched_with


# ============================================================================
#                               Function set_patched_with
# ============================================================================
def set_patched_with(value):
    global patched_with
    patched_with = value


# ============================================================================
#                               Function get_db
# ============================================================================
def get_db():
    global db
    return db


# ============================================================================
#                               Function set_db
# ============================================================================
def set_db(value):
    global db
    db = value


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
    elif parse(VERSION) < parse('9.0.0'):
        return 'PixelFlasher4.db'
    else:
        return 'PixelFlasher9.db'


# ============================================================================
#                               Function get_verbose
# ============================================================================
def get_verbose():
    global verbose
    return verbose


# ============================================================================
#                               Function set_verbose
# ============================================================================
def set_verbose(value):
    global verbose
    verbose = value


# ============================================================================
#                               Function get_a_only
# ============================================================================
def get_a_only():
    global a_only
    return a_only


# ============================================================================
#                               Function set_a_only
# ============================================================================
def set_a_only(value):
    global a_only
    a_only = value


# ============================================================================
#                               Function get_adb
# ============================================================================
def get_adb():
    global adb
    return adb


# ============================================================================
#                               Function set_adb
# ============================================================================
def set_adb(value):
    global adb
    adb = value


# ============================================================================
#                               Function get_puml_state
# ============================================================================
def get_puml_state():
    global puml_enabled
    return puml_enabled


# ============================================================================
#                               Function set_puml_state
# ============================================================================
def set_puml_state(value):
    global puml_enabled
    puml_enabled = value


# ============================================================================
#                               Function get_fastboot
# ============================================================================
def get_fastboot():
    global fastboot
    return fastboot


# ============================================================================
#                               Function set_fastboot
# ============================================================================
def set_fastboot(value):
    global fastboot
    fastboot = value


# ============================================================================
#                               Function get_adb_sha256
# ============================================================================
def get_adb_sha256():
    global adb_sha256
    return adb_sha256


# ============================================================================
#                               Function set_adb_sha256
# ============================================================================
def set_adb_sha256(value):
    global adb_sha256
    adb_sha256 = value


# ============================================================================
#                               Function get_fastboot_sha256
# ============================================================================
def get_fastboot_sha256():
    global fastboot_sha256
    return fastboot_sha256


# ============================================================================
#                               Function set_fastboot_sha256
# ============================================================================
def set_fastboot_sha256(value):
    global fastboot_sha256
    fastboot_sha256 = value


# ============================================================================
#                               Function get_phones
# ============================================================================
def get_phones():
    global phones
    return phones


# ============================================================================
#                               Function set_phones
# ============================================================================
def set_phones(value):
    global phones
    phones = value


# ============================================================================
#                               Function get_device_list
# ============================================================================
def get_device_list():
    global device_list
    return device_list


# ============================================================================
#                               Function set_device_list
# ============================================================================
def set_device_list(value):
    global device_list
    device_list = value


# ============================================================================
#                               Function get_phone_id
# ============================================================================
def get_phone_id():
    global phone_id
    return phone_id


# ============================================================================
#                               Function set_phone_id
# ============================================================================
def set_phone_id(value):
    global phone_id
    phone_id = value


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
    global system_code_page
    return system_code_page


# ============================================================================
#                               Function set_system_codepage
# ============================================================================
def set_system_codepage(value):
    global system_code_page
    system_code_page = value


# ============================================================================
#                               Function get_magisk_package
# ============================================================================
def get_magisk_package():
    global magisk_package
    return magisk_package


# ============================================================================
#                               Function set_magisk_package
# ============================================================================
def set_magisk_package(value):
    global magisk_package
    magisk_package = value


# ============================================================================
#                               Function get_linux_shell
# ============================================================================
def get_linux_shell():
    global linux_shell
    return linux_shell


# ============================================================================
#                               Function set_linux_shell
# ============================================================================
def set_linux_shell(value):
    global linux_shell
    linux_shell = value


# ============================================================================
#                               Function get_is_ota
# ============================================================================
def get_ota():
    global is_ota
    return is_ota


# ============================================================================
#                               Function set_ota
# ============================================================================
def set_ota(self, value):
    global is_ota
    is_ota = value
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
    global sdk_is_ok
    return sdk_is_ok


# ============================================================================
#                               Function set_sdk_state
# ============================================================================
def set_sdk_state(value):
    global sdk_is_ok
    sdk_is_ok = value


# ============================================================================
#                               Function get_firmware_hash_validity
# ============================================================================
def get_firmware_hash_validity():
    global firmware_hash_valid
    return firmware_hash_valid


# ============================================================================
#                               Function set_firmware_hash_validity
# ============================================================================
def set_firmware_hash_validity(value):
    global firmware_hash_valid
    firmware_hash_valid = value


# ============================================================================
#                               Function get_firmware_has_init_boot
# ============================================================================
def get_firmware_has_init_boot():
    global firmware_has_init_boot
    return firmware_has_init_boot


# ============================================================================
#                               Function set_firmware_has_init_boot
# ============================================================================
def set_firmware_has_init_boot(value):
    global firmware_has_init_boot
    firmware_has_init_boot = value


# ============================================================================
#                               Function get_rom_has_init_boot
# ============================================================================
def get_rom_has_init_boot():
    global rom_has_init_boot
    return rom_has_init_boot


# ============================================================================
#                               Function set_rom_has_init_boot
# ============================================================================
def set_rom_has_init_boot(value):
    global rom_has_init_boot
    rom_has_init_boot = value


# ============================================================================
#                               Function get_dlg_checkbox_values
# ============================================================================
def get_dlg_checkbox_values():
    global dlg_checkbox_values
    return dlg_checkbox_values


# ============================================================================
#                               Function set_dlg_checkbox_values
# ============================================================================
def set_dlg_checkbox_values(value):
    global dlg_checkbox_values
    dlg_checkbox_values = value


# ============================================================================
#                               Function get_firmware_model
# ============================================================================
def get_firmware_model():
    global firmware_model
    return firmware_model


# ============================================================================
#                               Function set_firmware_model
# ============================================================================
def set_firmware_model(value):
    global firmware_model
    firmware_model = value


# ============================================================================
#                               Function get_firmware_id
# ============================================================================
def get_firmware_id():
    global firmware_id
    return firmware_id


# ============================================================================
#                               Function set_firmware_id
# ============================================================================
def set_firmware_id(value):
    global firmware_id
    firmware_id = value


# ============================================================================
#                               Function get_custom_rom_id
# ============================================================================
def get_custom_rom_id():
    global custom_rom_id
    return custom_rom_id


# ============================================================================
#                               Function set_custom_rom_id
# ============================================================================
def set_custom_rom_id(value):
    global custom_rom_id
    custom_rom_id = value


# ============================================================================
#                               Function get_logfile
# ============================================================================
def get_logfile():
    global logfile
    return logfile


# ============================================================================
#                               Function set_logfile
# ============================================================================
def set_logfile(value):
    global logfile
    logfile = value


# ============================================================================
#                               Function get_pumlfile
# ============================================================================
def get_pumlfile():
    global pumlfile
    return pumlfile


# ============================================================================
#                               Function set_pumlfile
# ============================================================================
def set_pumlfile(value):
    global pumlfile
    pumlfile = value


# ============================================================================
#                               Function get_sdk_version
# ============================================================================
def get_sdk_version():
    global sdk_version
    return sdk_version


# ============================================================================
#                               Function set_sdk_version
# ============================================================================
def set_sdk_version(value):
    global sdk_version
    sdk_version = value


# ============================================================================
#                               Function get_image_mode
# ============================================================================
def get_image_mode():
    global image_mode
    return image_mode


# ============================================================================
#                               Function set_image_mode
# ============================================================================
def set_image_mode(value):
    global image_mode
    image_mode = value


# ============================================================================
#                               Function get_image_path
# ============================================================================
def get_image_path():
    global image_path
    return image_path


# ============================================================================
#                               Function set_image_path
# ============================================================================
def set_image_path(value):
    global image_path
    image_path = value


# ============================================================================
#                               Function get_custom_rom_file
# ============================================================================
def get_custom_rom_file():
    global custom_rom_file
    return custom_rom_file


# ============================================================================
#                               Function set_custom_rom_file
# ============================================================================
def set_custom_rom_file(value):
    global custom_rom_file
    custom_rom_file = value


# ============================================================================
#                               Function get_message_box_title
# ============================================================================
def get_message_box_title():
    global message_box_title
    return message_box_title


# ============================================================================
#                               Function set_message_box_title
# ============================================================================
def set_message_box_title(value):
    global message_box_title
    message_box_title = value


# ============================================================================
#                               Function get_message_box_message
# ============================================================================
def get_message_box_message():
    global message_box_message
    return message_box_message


# ============================================================================
#                               Function set_message_box_message
# ============================================================================
def set_message_box_message(value):
    global message_box_message
    message_box_message = value


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
        global db
        config_path = get_sys_config_path()
        # connect / create db
        db = sl.connect(os.path.join(config_path, get_pf_db()))
        db.execute("PRAGMA foreign_keys = ON")
        # create tables
        with db:
            # PACKAGE Table
            db.execute("""
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
            db.execute("""
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
            db.execute("""
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
            cursor = db.execute("PRAGMA table_info(BOOT)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            if 'patch_method' not in column_names:
                # Add the patch_method column to the BOOT table
                db.execute("ALTER TABLE BOOT ADD COLUMN patch_method TEXT;")
            if 'is_odin' not in column_names:
                # Add the is_odin column to the BOOT table
                db.execute("ALTER TABLE BOOT ADD COLUMN is_odin INTEGER;")
            # Added in version 5.4
            if 'is_stock_boot' not in column_names:
                # Add the is_stock_boot column to the BOOT table
                db.execute("ALTER TABLE BOOT ADD COLUMN is_stock_boot INTEGER;")
            if 'is_init_boot' not in column_names:
                # Add the is_init_boot column to the BOOT table
                db.execute("ALTER TABLE BOOT ADD COLUMN is_init_boot INTEGER;")
            if 'patch_source_sha1' not in column_names:
                # Add the patch_source_sha1 column to the BOOT table
                db.execute("ALTER TABLE BOOT ADD COLUMN patch_source_sha1 INTEGER;")

            # Check if the full_ota column already exists in the PACKAGE table
            # Added in version 5.8
            cursor = db.execute("PRAGMA table_info(PACKAGE)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            if 'full_ota' not in column_names:
                # Add the full_ota column to the BOOT table (values: 0:Not Full OTA, 1:Full OTA NULL:UNKNOWN)
                db.execute("ALTER TABLE PACKAGE ADD COLUMN full_ota INTEGER;")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while init_db")
        traceback.print_exc()


# ============================================================================
#                               Function get_config_file_path
# ============================================================================
def get_config_file_path():
    # return os.path.join(get_sys_config_path(), CONFIG_FILE_NAME).strip()
    global config_file_path
    return config_file_path


# ============================================================================
#                               Function set_config
# ============================================================================
def set_config_file_path(value):
    global config_file_path
    config_file_path = value


# ============================================================================
#                               Function get_sys_config_path
# ============================================================================
def get_sys_config_path():
    return user_data_dir(APPNAME, appauthor=False, roaming=True)


# ============================================================================
#                               Function get_config_path
# ============================================================================
def get_config_path():
    global config_path
    return config_path


# ============================================================================
#                               Function set_config_path
# ============================================================================
def set_config_path(value):
    global config_path
    config_path = value


# ============================================================================
#                               Function get_labels_file_path
# ============================================================================
def get_labels_file_path():
    return os.path.join(get_config_path(), "labels.json").strip()


# ============================================================================
#                               Function get_xiaomi_file_path
# ============================================================================
def get_xiaomi_file_path():
    return os.path.join(get_config_path(), "xiaomi.json").strip()


# ============================================================================
#                               Function get_favorite_pifs_file_path
# ============================================================================
def get_favorite_pifs_file_path():
    return os.path.join(get_config_path(), "favorite_pifs.json").strip()


# ============================================================================
#                      Function get_device_images_history_file_path
# ============================================================================
def get_device_images_history_file_path():
    return os.path.join(get_config_path(), "device_images_history.json").strip()


# ============================================================================
#                               Function get_coords_file_path
# ============================================================================
def get_coords_file_path():
    return os.path.join(get_config_path(), "coords.json").strip()


# ============================================================================
#                               Function get_skip_urls_file_path
# ============================================================================
def get_skip_urls_file_path():
    return os.path.join(get_config_path(), "skip_urls.txt").strip()


# ============================================================================
#                               Function get_wifi_history_file_path
# ============================================================================
def get_wifi_history_file_path():
    return os.path.join(get_config_path(), "wireless.json").strip()


# ============================================================================
#                               Function get_mytools_file_path
# ============================================================================
def get_mytools_file_path():
    return os.path.join(get_config_path(), "mytools.json").strip()


# ============================================================================
#                               Function get_path_to_7z
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
            subprocess.Popen([self.config.linux_file_explorer, dir_path], env=get_env_variables())
        elif subprocess.call(["which", "xdg-open"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            subprocess.Popen(["xdg-open", dir_path], env=get_env_variables())  # prefer xdg-open if available
        else:
            subprocess.Popen(["nautilus", dir_path], env=get_env_variables())
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
                    subprocess.Popen([self.config.linux_shell, "--working-directory", dir_path], env=get_env_variables())
                else:
                    subprocess.Popen(["gnome-terminal", "--working-directory", dir_path], env=get_env_variables())
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
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
                for name in zip_file.namelist():
                    if name.endswith(f'/{file_to_check}') or name == file_to_check:
                        if not is_recursive:
                            debug(f"Found: {name}\n")
                        return name
                    elif nested and name.endswith('.zip'):
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
        debug(f"file: {file_to_check} was NOT found\n")
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
    if string.startswith('"') and string.endswith('"'):
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
#                               Function check_module_update
# ============================================================================
def check_module_update(url):
    try:
        skiplist = get_skip_urls_file_path()
        if os.path.exists(skiplist):
            with open(skiplist, 'r') as f:
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
            dlg = wx.MessageDialog(None, f"Module update URL has issues, inform the module author: {url}\nDo you want to skip checking updates for this module?", "Error", wx.YES_NO | wx.ICON_ERROR)
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
#                 Function get_partial_gsi_data
# ============================================================================
def get_partial_gsi_data():
    try:
        # URLs
        gsi_url = "https://developer.android.com/topic/generic-system-image/releases"

        # Fetch GSI HTML
        response = request_with_fallback('GET', gsi_url)
        if response == 'ERROR' or response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch GSI HTML")
            return -1
        gsi_html = response.text

        # Parse GSI HTML
        soup = BeautifulSoup(gsi_html, 'html.parser')

        # Find the list item containing 'Beta'
        beta_li = None
        for li in soup.find_all('li'):
            if 'Beta' in li.get_text():
                beta_li = li
                break
        if beta_li:
            beta_text = beta_li.get_text()
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Beta list item not found")
            return -1

        # Find the anchor tag with the text 'corresponding Google Pixel builds'
        release = soup.find('a', string=lambda x: x and 'corresponding Google Pixel builds' in x)
        if release:
            href = release['href']
            release_version = href.split('/')[3]
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Release version not found")
            return -1

        # Find the build ID inside <code> blocks
        build_id_text = None
        security_patch_level_text = None
        for code in soup.find_all('code'):
            code_text = code.get_text()
            if 'Build:' in code_text:
                build_id_text = code.get_text()
                if 'Security patch level:' in code_text:
                    security_patch_level_text = code_text
                if 'Google Play Services:' in code_text:
                    google_play_services = code_text.split('Google Play Services: ')[1].split('\n')[0]
                break
        if build_id_text:
            build_id = build_id_text.split('Build: ')[1].split()[0]
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Build ID not found")
            return -1

        if security_patch_level_text:
            security_patch_level_date = security_patch_level_text.split('Security patch level: ')[1].split('\n')[0]
            release_date = security_patch_level_text.split('Date: ')[1].split('\n')[0]
            beta_release_date = datetime.strptime(release_date, '%B %d, %Y').strftime('%Y-%m-%d')
            beta_expiry = datetime.strptime(beta_release_date, '%Y-%m-%d') + timedelta(weeks=6)
            beta_expiry_date = beta_expiry.strftime('%Y-%m-%d')
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Security patch level date not found")
            return -1

        # Find the incremental value
        incremental = None
        match = re.search(rf'{build_id}-(\d+)-', gsi_html)
        if match:
            incremental = match.group(1)
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Incremental not found")
            return -1


        devices = []
        table = soup.find('table')
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cols = row.find_all('td')
            device = cols[0].text.strip()
            button = cols[1].find('button')
            category = button['data-category']
            zip_filename = button.text.strip()
            hashcode = cols[1].find('code').text.strip()
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
        gsi_data = BetaData(release_date, build_id, emulator_support, security_patch_level_date, google_play_services, beta_expiry_date, incremental, security_patch, devices)
        return gsi_data, release['href']

    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting partial GSI data.")
        traceback.print_exc()


# ============================================================================
#                 Function get_partial_gsi_data2
# ============================================================================
def get_partial_gsi_data2(release_href, security_patch_level_date):
    try:
        secbull_url = "https://source.android.com/docs/security/bulletin/pixel"
        # Fetch Pixel GET HTML
        pixel_get_url = "https://developer.android.com" + release_href
        response = request_with_fallback('GET', pixel_get_url)
        if response == 'ERROR' or response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch Pixel GET HTML")
            return None, None
        pixel_get_html = response.text

        # Fetch Pixel Beta HTML
        soup = BeautifulSoup(pixel_get_html, 'html.parser')
        beta_link = soup.find('a', string=lambda x: x and 'Factory images for Google Pixel' in x)
        if beta_link:
            pixel_beta_url = "https://developer.android.com" + beta_link['href']
            response = request_with_fallback('GET', pixel_beta_url)
            if response == 'ERROR' or response.status_code != 200:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch Pixel Beta HTML")
                return None, None
            pixel_beta_html = response.text
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Beta link not found")
            return None, None

        # Parse Pixel Beta HTML
        soup = BeautifulSoup(pixel_beta_html, 'html.parser')
        pixel_data = []

        # Iterate over each <tr> element
        for tr in soup.find('table', id='images').find_all('tr'):
            # Skip the header row
            if tr.find('th'):
                continue

            model_td = tr.find('td')
            button = tr.find('button')
            code = tr.find('code')

            if model_td and button and code:
                model = model_td.get_text().strip()
                release = button['data-category']
                filename = button.get_text().strip()
                ltr = code.get_text().strip()
                product = filename.split('-')[0]

                # Create the object and add it to the list
                pixel_data.append({
                    'model': model,
                    'release': release,
                    'filename': filename,
                    'ltr': ltr,
                    'product': product
                })

        model_list = [item['model'] for item in pixel_data]
        product_list = [item['product'] for item in pixel_data]

        # Fetch Security Bulletin HTML
        response = request_with_fallback('GET', secbull_url)
        if response == 'ERROR' or response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch Security Bulletin HTML")
            return None, None
        secbull_html = response.text

        # Find the corresponding table row in the html
        soup = BeautifulSoup(secbull_html, 'html.parser')
        security_patch_row = soup.find(string=lambda x: x and security_patch_level_date in x)
        if security_patch_row:
            # Find the <tr> element containing the security patch level (the parent)
            tr_element = security_patch_row.find_parent('tr')
            if tr_element:
                # Find all <td> elements within the <tr>
                td_elements = tr_element.find_all('td')
                if td_elements:
                    # Get the last <td> element
                    security_patch_level = td_elements[-1].get_text().strip()
                    debug(f"Security Patch Level: {security_patch_level}")
                else:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Security patch level not found in Pixel Security Bulletin HTML")
                    return None, None
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Security patch level not found in Pixel Security Bulletin HTML")
                return None, None
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Security patch level not found in Pixel Security Bulletin HTML")
            return None, None

        return model_list, product_list, security_patch_level
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting partial GSI data.")
        traceback.print_exc()


# ============================================================================
#                 Function get_beta_pif
# ============================================================================
def get_beta_pif(device_model='random', force_version=None):
    # Get the latest Android version
    latest_version, latest_version_url = get_latest_android_version(force_version)
    debug(f"Selected Version:  {latest_version}")
    if latest_version == -1:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get the latest Android version")
        return -1

    # set the url to the latest version
    ota_url = f"https://developer.android.com/about/versions/{latest_version}/download-ota"
    factory_url = f"https://developer.android.com/about/versions/{latest_version}/download"

    # Fetch OTA HTML
    ota_data = get_beta_data(ota_url)
    if not ota_data:
        print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or DP OTA data for Android {latest_version}")
    # print(ota_data.__dict__)

    # Fetch Factory HTML
    factory_data = get_beta_data(factory_url)
    if not factory_data:
        print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or DP Factory data for Android {latest_version}")
    # print(factory_data.__dict__)

    # Fetch GSI HTML
    partial_gsi_data, release_href = get_partial_gsi_data()
    if not partial_gsi_data:
        print(f"❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to get beta or DP GSI data for Android {latest_version}")
    # print(partial_gsi_data.__dict__)

    if not ota_data and not factory_data and not partial_gsi_data:
        return -1
    if not ota_data and not factory_data:
        print(f"Getting beta print from latest GSI data, which will not necessarily match the requested Android version {latest_version} ...")

    ota_date_object = None
    factory_date_object = None
    gsi_date_object = None
    if ota_data:
        ota_date = ota_data.__dict__['release_date']
        ota_date_object = datetime.strptime(ota_date, "%B %d, %Y")
        debug(f"Beta OTA Date:     {ota_date}")
    else:
        debug(f"Beta OTA:          Unavailable")

    if partial_gsi_data:
        gsi_date = partial_gsi_data.__dict__['release_date']
        gsi_date_object = datetime.strptime(gsi_date, "%B %d, %Y")
        debug(f"Beta GSI Date:     {gsi_date}")
    else:
        debug(f"Beta GSI:          Unavailable")

    if factory_data:
        factory_date = factory_data.__dict__['release_date']
        factory_date_object = datetime.strptime(factory_date, "%B %d, %Y")
        debug(f"Beta Factory Date: {factory_date}")
    else:
        debug(f"Beta Factory:      Unavailable")

    # Determine the latest date(s)
    newest_data = []
    latest_date = max(filter(None, (ota_date_object, factory_date_object, gsi_date_object)), default=None)

    if latest_date is None:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to determine the latest date")
        return -1

    if ota_date_object == latest_date:
        newest_data.append('ota')
    if factory_date_object == latest_date:
        newest_data.append('factory')
    if gsi_date_object == latest_date:
        newest_data.append('gsi')

    def get_model_and_prod_list(data):
        for device in data.__dict__['devices']:
            model_list.append(device['device'])
            zip_filename = device['zip_filename']
            product = zip_filename.split('-')[0]
            product_list.append(product)
        return model_list, product_list

    for data in newest_data:
        if data == 'ota' and ota_data:
            debug("Extracting PIF from Beta OTA ...")
            # Grab fp and sp from OTA zip
            fingerprint, security_patch = url2fpsp(ota_data.__dict__['devices'][0]['url'], "ota")
            if fingerprint and security_patch:
                model_list = []
                product_list = []
                model_list, product_list = get_model_and_prod_list(ota_data)
                expiry_date = ota_data.__dict__['beta_expiry_date']
                break
        elif data == 'factory' and factory_data:
            debug("Extracting PIF from Beta Factory ...")
            # Grab fp and sp from Factory zip
            fingerprint, security_patch = url2fpsp(factory_data.__dict__['devices'][0]['url'], "factory")
            if fingerprint and security_patch:
                model_list = []
                product_list = []
                model_list, product_list = get_model_and_prod_list(factory_data)
                expiry_date = factory_data.__dict__['beta_expiry_date']
                break
        elif data == 'gsi' and partial_gsi_data:
            debug("Extracting PIF from Beta GSI ...")
            # Grab fp and sp from GSI zip
            fingerprint, security_patch = url2fpsp(partial_gsi_data.__dict__['devices'][0]['url'], "gsi")
            incremental = partial_gsi_data.__dict__['incremental']
            expiry_date = partial_gsi_data.__dict__['beta_expiry_date']
            # Get the latest GSI part2 data
            model_list, product_list, security_patch_level = get_partial_gsi_data2(release_href, partial_gsi_data.__dict__['security_patch_level'])
            if model_list and product_list:
                if not security_patch:
                    security_patch = security_patch_level
                if not fingerprint:
                    build_id = partial_gsi_data.__dict__['build']
                    fingerprint = f"google/gsi_gms_arm64/gsi_arm64:{latest_version}/{build_id}/{incremental}:user/release-keys"
                break

    build_type = 'user'
    build_tags = 'release-keys'
    if fingerprint and security_patch:
        debug(f"Security Patch:    {security_patch}")
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

    if device_model != '' and f"{device_model}_beta" in product_list:
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
        model, product, device = set_random_beta()

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
    print(f"Beta Print Expiry Date:   {expiry_date}")
    print(f"Random Beta Profile/Fingerprint:\n{random_print_json}\n")
    return random_print_json


# ============================================================================
#                               Function get_beta_data
# ============================================================================
def get_beta_data(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch URL: {url}")
            return None
        ota_html = response.text

        soup = BeautifulSoup(ota_html, 'html.parser')

        # check if the page has beta in it.
        if 'beta' not in soup.get_text().lower():
            # print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: 'Beta' not found For URL: {url}")
            return None

        # Extract information from the first table
        table = soup.find('table', class_='responsive fixed')
        if not table:
            # print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Required table is not found on the page.")
            return None

        rows = table.find_all('tr')
        data = {}
        for row in rows:
            cols = row.find_all('td')
            key = cols[0].text.strip().lower().replace(' ', '_')
            value = cols[1].text.strip()
            data[key] = value

        release_date = data.get('release_date')
        build = data.get('build')
        emulator_support = data.get('emulator_support')
        security_patch_level = data.get('security_patch_level')
        google_play_services = data.get('google_play_services')
        beta_release_date = datetime.strptime(release_date, '%B %d, %Y').strftime('%Y-%m-%d')
        beta_expiry = datetime.strptime(beta_release_date, '%Y-%m-%d') + timedelta(weeks=6)
        beta_expiry_date = beta_expiry.strftime('%Y-%m-%d')

        # Extract information from the second table
        devices = []
        table = soup.find('table', id='images')
        rows = table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cols = row.find_all('td')
            device = cols[0].text.strip()
            button = cols[1].find('button')
            category = button['data-category']
            zip_filename = button.text.strip()
            hashcode = cols[1].find('code').text.strip()
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
        incremental = ""
        security_patch = ""
        beta_data = BetaData(release_date, build, emulator_support, security_patch_level, google_play_services, beta_expiry_date, incremental, security_patch, devices)
        return beta_data
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in get_beta_data function")
        traceback.print_exc()


# ============================================================================
#                               Function get_latest_android_version
# ============================================================================
def get_latest_android_version(force_version=None):
    versions_url = "https://developer.android.com/about/versions"
    response = request_with_fallback('GET', versions_url)
    if response == 'ERROR' or response.status_code != 200:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to fetch VERSIONS HTML")
        return -1
    versions_html = response.text

    soup = BeautifulSoup(versions_html, 'html.parser')
    version = 0
    link_url = ''
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(r'https:\/\/developer\.android\.com\/about\/versions\/\d+', href):
            # capture the d+ part
            link_version = int(re.search(r'\d+', href).group())
            if force_version:
                if link_version == force_version:
                    version = link_version
                    link_url = href
                    break
            if link_version > version:
                version = link_version
                link_url = href
    return version, link_url


# ============================================================================
#                               Function url2fpsp
# ============================================================================
def url2fpsp(url, image_type):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)

            fingerprint = None
            security_patch = None
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()

            if image_type == 'ota':
                size_limit = 2 * 1024
                content = response.raw.read(size_limit).decode('utf-8', errors='ignore')
                fingerprint_match = re.search(r"post-build=(.+)", content)
                security_patch_match = re.search(r"security-patch-level=(.+)", content)
            elif image_type == 'factory':
                size_limit = 30000000
                content = response.raw.read(size_limit).decode('utf-8', errors='ignore')
                fingerprint_match = re.search(r"com.android.build.boot.fingerprint(.+?)\x00", content)
                security_patch_match = re.search(r"com.android.build.boot.security_patch(.+?)\x00", content)
            elif image_type == 'gsi':
                response = requests.head(url)
                file_size = int(response.headers["Content-Length"])
                start_byte = max(0, file_size - 8192)
                headers = {"Range": f"bytes={start_byte}-{file_size - 1}"}
                response = requests.get(url, headers=headers, stream=True, verify=False)
                end_content = response.content
                content = partial_extract(end_content, "build.prop")
                content_str = content.decode('utf-8', errors='ignore')
                fingerprint_match = re.search(r"ro\.system\.build\.fingerprint=(.+)", content_str)
                security_patch_match = re.search(r"ro\.build\.version\.security_patch=(.+)", content_str)
            else:
                print(f"Invalid image type: {image_type}")
                return -1

            fingerprint = fingerprint_match.group(1).strip('\x00') if fingerprint_match else None
            security_patch = security_patch_match.group(1).strip('\x00') if security_patch_match else None

            # debug("FINGERPRINT:", fingerprint)
            # debug("SECURITY_PATCH:", security_patch)
            return fingerprint, security_patch
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in url2fpsp function")
        traceback.print_exc()
        return -1


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
#                               Function get_google_images
# ============================================================================
def get_google_images(save_to=None):
    try:
        COOKIE = {'Cookie': 'devsite_wall_acks=nexus-ota-tos,nexus-image-tos,watch-image-tos,watch-ota-tos'}
        data = {}

        if save_to is None:
            save_to = os.path.join(get_config_path(), "google_images.json").strip()

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
                if device_element.text.strip() in ["Terms and conditions", "Updating instructions", "Updating Pixel 6, Pixel 6 Pro, and Pixel 6a devices to Android 13 for the first time", "Use Android Flash Tool", "Flashing instructions"]:
                    continue

                # Extract the device name from the 'id' attribute
                device_id = device_element.get('id')

                # Extract the device label from the text and strip "id"
                device_label = device_element.get('data-text').strip('"').split('" for ')[1]

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
                    version = columns[0].text.strip()

                    # Different extraction is necessary per type
                    if image_type in ['ota', 'ota-watch'] or (marlin_flag and image_type == "factory"):
                        sha256_checksum = columns[2].text.strip()
                        download_url = columns[1].find('a')['href']
                    elif image_type in ['factory', 'factory-watch']:
                        download_url = columns[2].find('a')['href']
                        sha256_checksum = columns[3].text.strip()

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
        if ro_product_name in [None, '', 'mainline', 'generic'] and fp_ro_product_name != '':
            debug(f"Properties for PRODUCT are extracted from FINGERPRINT: {fp_ro_product_name}")
            ro_product_name = fp_ro_product_name
        if autofill and ro_product_name == '':
            ro_product_name = get_first_match(device_dict, keys)

        # DEVICE (ro.build.product os fallback, keep it last)
        keys = ['ro.product.device', 'ro.product.system.device', 'ro.product.product.device', 'ro.product.vendor.device', 'ro.vendor.product.device', 'ro.build.product']
        ro_product_device = get_first_match(the_dict, keys)
        if ro_product_device != '':
            the_dict = delete_keys_from_dict(the_dict, keys)
        if ro_product_device in [None, '', 'mainline', 'generic'] and fp_ro_product_device != '':
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
        if ro_product_model in ['mainline', 'generic']:
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
            'gr.nikolasspyr.integritycheck:id/device_integrity_icon',
            'gr.nikolasspyr.integritycheck:id/basic_integrity_icon',
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
def extract_from_zip(zip_path, to_extract, extracted_file_path):
    try:
        print(f"Extracting {to_extract} from {zip_path}...")
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
    # config = get_config()
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
def download_ksu_latest_release_asset(user, repo, asset_name=None, anykernel=True):
    try:
        url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        response = request_with_fallback(method='GET', url=url)
        assets = response.json().get('assets', [])

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
            pattern = re.compile(rf"^AnyKernel3-{base_name}-{fixed_version}\.([0-9]+)(_.*|)\.zip$")
        else:
            pattern = re.compile(rf"^{base_name}-{fixed_version}\.([0-9]+)(_.*|)-boot\.img\.gz$")

        # Find the best match
        best_match = None
        best_version = -1
        for asset in assets:
            match = pattern.match(asset['name'])
            if match:
                asset_version = int(match[1])
                if asset_version <= variable_version and asset_version > best_version:
                    best_match = asset
                    best_version = asset_version
                    if asset_version == variable_version:
                        break
        if best_match:
            print(f"Found best match KernelSU: {best_match['name']}")
            download_file(best_match['browser_download_url'])
            print(f"Downloaded {best_match['name']}")
            return best_match['name']
        else:
            print(f"Asset {asset_name} not found in the latest release of {user}/{repo}")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_ksu_latest_release_asset function")
        traceback.print_exc()


# ============================================================================
#                 Function download_gh_latest_release_asset_regex
# ============================================================================
def download_gh_latest_release_asset_regex(user, repo, asset_name_pattern, just_url_info=False, include_prerelease=False):
    try:
        url = f"https://api.github.com/repos/{user}/{repo}/releases"
        response = request_with_fallback(method='GET', url=url)
        releases = response.json()

        # Filter releases based on the include_prerelease flag
        if not include_prerelease:
            releases = [release for release in releases if not release['prerelease']]

        # Get the latest release
        latest_release = releases[0] if releases else None

        if not latest_release:
            print(f"No releases found for {user}/{repo}")
            return

        assets = latest_release.get('assets', [])

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
            if just_url_info:
                return best_match['browser_download_url']
            download_file(best_match['browser_download_url'])
            print(f"Downloaded {best_match['name']}")
            return best_match['name']
        else:
            print(f"No asset matches the pattern {asset_name_pattern} in the latest release of {user}/{repo}")
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in download_gh_latest_release_asset_regex function")
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
#                               Function extract_magiskboot
# ============================================================================
def extract_magiskboot(apk_path, architecture, output_path):
    try:
        path_to_7z = get_path_to_7z()
        file_path_in_apk = f"lib/{architecture}/libmagiskboot.so"
        output_file_path = os.path.join(output_path, "magiskboot")

        cmd = f"{path_to_7z} e {apk_path} -o{output_path} -r {file_path_in_apk} -y"
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
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


# ============================================================================
#                               Function check_kb
# Credit to hldr4  for the original idea
# https://gist.github.com/hldr4/b933f584b2e2c3088bcd56eb056587f8
# ============================================================================
def check_kb(filename):
    url = "https://android.googleapis.com/attestation/status"
    headers = {
        'Cache-Control': 'no-cache, max-age=0',
        'Pragma': 'no-cache'
    }
    try:
        crl = request_with_fallback(method='GET', url=url, headers=headers, nocache=True)
        if crl is not None and crl != 'ERROR':
            last_modified = crl.headers.get('last-modified', 'Unknown')
            content_date = crl.headers.get('date', 'Unknown')
            print("------------------------------------------------------------------------")
            print(f"CRL Last Modified:     {last_modified}")
            print(f"Server Response Date:  {content_date}")
            crl = crl.json()
        else:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not fetch CRL from {url}")
            return ['invalid']

        # Extract certificates from keybox
        certs = []
        try:
            for elem in ET.parse(filename).getroot().iter():
                if elem.tag == 'Certificate':
                    certs.append(elem.text.strip())
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract certificates from {filename}")
            print(e)
            return ['invalid']

        shadow_banned_list = SHADOW_BANNED_ISSUERS
        is_sw_signed = False
        is_expired = False
        expiring_soon = False
        is_revoked = False
        is_shadow_banned = False
        i = 1
        print(f"\nChecking keybox: {filename} ...")

        last_issuer = ""
        cert_counter = 0
        tab_text = ""
        chain_counter = 0

        for cert in certs:
            cert_sn, cert_issuer, cert_subject, sig_algo, expiry, key_usages, parsed = parse_cert(cert)

            # Format the issuer field
            formatted_issuer, issuer_sn = format_dn(cert_issuer)

            if issuer_sn in shadow_banned_list:
                is_shadow_banned = True

            # Format the issued to field
            formatted_issued_to, issued_to_sn = format_dn(cert_subject)

            # indent the chain
            if last_issuer == issued_to_sn or last_issuer == cert_subject:
                tab_text += "    "
                cert_counter_text = " "
                chain_counter += 1
            else:
                tab_text = ""
                cert_counter += 1
                cert_counter_text = f"{cert_counter}"

            # handle no sn case
            if issuer_sn == "":
                last_issuer = cert_issuer
                if cert_counter == 0:
                    cert_counter = 1
                cert_counter_text = f"{cert_counter}"
            else:
                last_issuer = issuer_sn

            # redact if verbose is not set
            if get_verbose():
                cert_sn_text = cert_sn
                formatted_issued_to_text = formatted_issued_to
                formatted_issuer_text = formatted_issuer
            else:
                cert_sn_text = "REDACTED"
                formatted_issued_to_text = "REDACTED"
                formatted_issuer_text = "REDACTED"

            print(f'\n{tab_text}Certificate {cert_counter_text} SN:       {cert_sn_text}')
            print(f'{tab_text}Issued to:              {formatted_issued_to_text}')
            print(f'{tab_text}Issuer:                 {formatted_issuer_text}')
            print(f'{tab_text}Signature Algorithm:    {sig_algo}')
            print(f'{tab_text}Key Usage:              {key_usages}')
            expired_text = ""
            if expiry < datetime.now(timezone.utc):
                expired_text = " (EXPIRED)"
            print(f"{tab_text}Validity:               {parsed.not_valid_before_utc.date()} to {expiry.date()} {expired_text}")

            if "Software Attestation" in cert_issuer:
                is_sw_signed = True

            if expiry < datetime.now(timezone.utc):
                is_expired = True
                print(f"{tab_text}❌❌❌ Certificate is EXPIRED")
            elif expiry < datetime.now(timezone.utc) + timedelta(days=30):
                expiring_soon = True
                print(f"{tab_text}⚠️ Certificate is EXPIRING SOON")

            if cert_sn.strip().lower() in (sn.strip().lower() for sn in crl["entries"].keys()):
                print(f"{tab_text}❌❌❌ Certificate {i} is REVOKED")
                print(f"{tab_text}❌❌❌ Reason: {crl['entries'][cert_sn]['reason']} ***")
                is_revoked = True

            i += 1

        results = []
        if is_revoked:
            print(f"\n❌❌❌ Keybox {filename} contains revoked certificates!")
            results.append('revoked')
        else:
            print(f"\n✅ certificates in Keybox {filename} are not on the revocation list")
            results.append('valid')
        if is_expired:
            print(f"\n❌❌❌ Keybox {filename} contains expired certificates!")
            results.append('expired')
        if is_sw_signed:
            print(f"⚠️ Keybox {filename} is software signed! This is not a hardware-backed keybox!")
            results.append('aosp')
        if expiring_soon:
            print(f"⚠️ Keybox {filename} contains certificates that are expiring soon!")
            results.append('expiring_soon')
        if chain_counter > 4:
            print(f"⚠️ Keybox {filename} contains certificates longer chain than normal, this may no work.")
            results.append('long_chain')
        if is_shadow_banned:
            print(f"\n❌❌❌ Keybox {filename} has certificate(s) issued by an authority in shadow banned list!")
            results.append('shadow_banned')
        print('')
        return results
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in check_kb function")
        print(e)
        traceback.print_exc()


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

    return serial_number, issuer, subject, sig_algo, expiry, key_usages, parsed


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
            part = part.replace("\\,", ",")  # Replace escaped commas with actual commas
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
        for _ in package_ids_tuple:
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
def get_magisk_apks():
    global magisk_apks
    if magisk_apks is None:
        try:
            apks = []
            mlist = ['Magisk Stable', 'Magisk Beta', 'Magisk Canary', 'Magisk Debug', 'Magisk Alpha', 'Magisk Delta Canary', 'Magisk Delta Debug', "KernelSU", 'KernelSU-Next', 'APatch', "Magisk zygote64_32 canary", "Magisk special 27001", "Magisk special 26401", 'Magisk special 25203']
            for i in mlist:
                apk = get_magisk_apk_details(i)
                if apk:
                    apks.append(apk)
            magisk_apks = apks
        except Exception as e:
            magisk_apks is None
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Magisk downloads link: {i} processing")
            traceback.print_exc()
    return magisk_apks


# ============================================================================
#                               Function get_magisk_apk_details
# ============================================================================
def get_magisk_apk_details(channel):
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
    elif channel == 'Magisk Delta Canary':
        url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/canary.json"

    elif channel == 'Magisk Delta Debug':
        url = "https://raw.githubusercontent.com/HuskyDG/magisk-files/main/debug.json"

    elif channel == 'KernelSU':
        try:
            # https://github.com/tiann/KernelSU/releases
            kernelsu_version = get_gh_latest_release_version('tiann', 'KernelSU')
            kernelsu_release_notes = get_gh_latest_release_notes('tiann', 'KernelSU')
            kernelsu_url = download_gh_latest_release_asset_regex('tiann', 'KernelSU', r'^KernelSU.*\.apk$', True)
            if kernelsu_url is None:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find KernelSU APK")
                return
            match = re.search(r'_([0-9]+)-', kernelsu_url)
            if match:
                kernelsu_versionCode =  match.group(1)
            else:
                if kernelsu_version:
                    kernelsu_versionCode = kernelsu_version
                else:
                    parts = version.split('.')
                    a = int(parts[0])
                    b = int(parts[1])
                    c = int(parts[2])
                    kernelsu_versionCode = (a * 256 * 256) + (b * 256) + c
            setattr(ma, 'version', kernelsu_version)
            setattr(ma, 'versionCode', kernelsu_versionCode)
            setattr(ma, 'link', kernelsu_url)
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', KERNEL_SU_PKG_NAME)
            setattr(ma, 'release_notes', kernelsu_release_notes)
            return ma
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during KernelSU processing")
            traceback.print_exc()
            return

    elif channel == 'KernelSU-Next':
        try:
            # https://github.com/rifsxd/KernelSU-Next/releases
            kernelsu_next_version = get_gh_latest_release_version('rifsxd', 'KernelSU-Next')
            kernelsu_next_release_notes = get_gh_latest_release_notes('rifsxd', 'KernelSU-Next')
            kernelsu_next_url = download_gh_latest_release_asset_regex('rifsxd', 'KernelSU-Next', r'^KernelSU_Next.*\.apk$', True)
            if kernelsu_next_url is None:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find KernelSU-Next APK")
                return
            match = re.search(r'_([0-9]+)-', kernelsu_next_url)
            if match:
                kernelsu_next_versionCode =  match.group(1)
            else:
                if kernelsu_next_version:
                    kernelsu_next_versionCode = kernelsu_next_version
                else:
                    parts = version.split('.')
                    a = int(parts[0])
                    b = int(parts[1])
                    c = int(parts[2])
                    kernelsu_next_versionCode = (a * 256 * 256) + (b * 256) + c
            setattr(ma, 'version', kernelsu_next_version)
            setattr(ma, 'versionCode', kernelsu_next_versionCode)
            setattr(ma, 'link', kernelsu_next_url)
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', KSU_NEXT_PKG_NAME)
            setattr(ma, 'release_notes', kernelsu_next_release_notes)
            return ma
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during KernelSU Next processing")
            traceback.print_exc()
            return

    elif channel == 'APatch':
        try:
            # https://github.com/bmax121/APatch/releases
            apatch_version = get_gh_latest_release_version('bmax121', 'APatch')
            apatch_release_notes = get_gh_latest_release_notes('bmax121', 'APatch')
            apatch_url = download_gh_latest_release_asset_regex('bmax121', 'APatch', r'^APatch_.*\.apk$', True)
            if apatch_url is None:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not find APatch APK")
                return
            match = re.search(r'_([0-9]+)-', apatch_url)
            if match:
                apatch_versionCode =  match.group(1)
            else:
                if apatch_version:
                    apatch_versionCode = apatch_version
                else:
                    parts = version.split('.')
                    a = int(parts[0])
                    b = int(parts[1])
                    c = int(parts[2])
                    apatch_versionCode = (a * 256 * 256) + (b * 256) + c
            setattr(ma, 'version', apatch_version)
            setattr(ma, 'versionCode', apatch_versionCode)
            setattr(ma, 'link', apatch_url)
            setattr(ma, 'note_link', "note_link")
            setattr(ma, 'package', APATCH_PKG_NAME)
            setattr(ma, 'release_notes', apatch_release_notes)
            return ma
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
        if channel in ['Magisk Delta Canary', 'Magisk Delta Debug']:
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
#     filename, lineno, function_name, _ = stack[-3]  # -3 because -1 is current function, -2 is the function that called this function
#     print(f"Called from {function_name} at {filename}:{lineno}")

#     print(s.getvalue())
#     return result

