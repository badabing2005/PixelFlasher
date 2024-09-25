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
import platform
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
from datetime import datetime, timezone
from os import path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
# from cryptography.x509 import ExtensionNotFound
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
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
#                               Function set_is_ota
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
                subprocess.Popen(f"{get_linux_shell() or "gnome-terminal --"} '{os.environ.get("SHELL").replace("'", "'\\''")}'", shell=True, cwd=dir_path, env=get_env_variables())
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", "-a", "Terminal", dir_path], env=get_env_variables())
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a terminal.")
        traceback.print_exc()


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
    regex = re.compile(f"{search}.*?bounds\=\"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\".+")
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

    # Find the position of "Show notifications and offers"
    show_notifications_position = xml_content.find('Show notifications and offers')

    # Check if "Show notifications and offers" is found
    if show_notifications_position != -1:
        node = xml_content.find('/node', show_notifications_position)

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
        if os.path.exists(file_path):
            sanitize_file(file_path)
        # sanitize files.txt
        file_path = os.path.join(support_dir_full, 'files.txt')
        if os.path.exists(file_path):
            sanitize_file(file_path)

        # for each file in logs, sanitize
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
        if os.path.exists(file_path):
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
#                               Function format_memory_size
# ============================================================================
def get_printable_memory():
    free_memory, total_memory = get_free_memory()
    formatted_free_memory = format_memory_size(free_memory)
    formatted_total_memory = format_memory_size(total_memory)
    return f"Available Free Memory: {formatted_free_memory} / {formatted_total_memory}"


# ============================================================================
#                               Function device_has_update
# ============================================================================
def device_has_update(data, device_id, target_date):
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


# ============================================================================
#                               Function get_google_images
# ============================================================================
def get_google_images(save_to=None):
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


# ============================================================================
#                         extract_date_from_google_version
# ============================================================================
def extract_date_from_google_version(version_string):
    # pattern to find a 3-letter month followed by a year
    pattern = re.compile(r'(\b[A-Za-z]{3}\s\d{4}\b)')
    match = pattern.search(version_string)

    if match:
        date_str = match.group()
        date_obj = datetime.strptime(date_str, '%b %Y')
        # convert to yymm01
        return date_obj.strftime('%y%m01')
    return None


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
    for key in keys:
        if key in dictionary:
            value = dictionary[key]
            break
    else:
        value = ''
    return value


# ============================================================================
#                               Function delete_keys_from_dict
# ============================================================================
def delete_keys_from_dict(dictionary, keys):
    for key in keys:
        if key in dictionary:
            del dictionary[key]
    return dictionary


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
    with open(filename, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']


# ============================================================================
#                               Function process_pi_xml_piac
# ============================================================================
def process_pi_xml_piac(filename):
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


# ============================================================================
#                               Function process_pi_xml_spic
# ============================================================================
def process_pi_xml_spic(filename):
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


# ============================================================================
#                               Function process_pi_xml_tb
# ============================================================================
def process_pi_xml_tb(filename):
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


# ============================================================================
#                               Function process_pi_xml_ps
# ============================================================================
def process_pi_xml_ps(filename):
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


# ============================================================================
#                               Function process_pi_xml_yasnac
# ============================================================================
def process_pi_xml_yasnac(filename):
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
            if res and isinstance(res, subprocess.CompletedProcess) and res.returncode != 0:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {file_to_process}")
                print(f"Return Code: {res.returncode}.")
                print(f"Stdout: {res.stdout}.")
                print(f"Stderr: {res.stderr}.")
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
                #         print(f"Return Code: {res.returncode}.")
                #         print(f"Stdout: {res.stdout}.")
                #         print(f"Stderr: {res.stderr}.")
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
                if res and isinstance(res, subprocess.CompletedProcess) and res.returncode != 0:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract {found_ap}.")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
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
                if res and isinstance(res, subprocess.CompletedProcess) and res.returncode != 0:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract meta-data.")
                    print(f"Return Code: {res.returncode}.")
                    print(f"Stdout: {res.stdout}.")
                    print(f"Stderr: {res.stderr}.")
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
            pattern = re.compile(f"^AnyKernel3-{base_name}-{fixed_version}\.([0-9]+)(_.*|)\\.zip$")
        else:
            pattern = re.compile(f"^{base_name}-{fixed_version}\.([0-9]+)(_.*|)-boot\\.img\\.gz$")

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
        if res and isinstance(res, subprocess.CompletedProcess) and res.returncode != 0:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Could not extract from {apk_path}")
            print(f"Return Code: {res.returncode}.")
            print(f"Stdout: {res.stdout}.")
            print(f"Stderr: {res.stderr}.")
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
def request_with_fallback(method, url, headers=None, data=None, stream=False):
    response = 'ERROR'
    try:
        if check_internet():
            response = requests.request(method, url, headers=headers, data=data, stream=stream)
            response.raise_for_status()
    except requests.exceptions.SSLError:
        # Retry with SSL certificate verification disabled
        print(f"⚠️ WARNING! Encountered SSL certification error while connecting to: {url}")
        print("Retrying with SSL certificate verification disabled. ...")
        print("For security, you should double check and make sure your system or communication is not compromised.")
        if check_internet():
            response = requests.request(method, url, headers=headers, data=data, verify=False, stream=stream)
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
# Credit to hldr4 https://gist.github.com/hldr4/b933f584b2e2c3088bcd56eb056587f8
# ============================================================================
def check_kb(filename):
    url = "https://android.googleapis.com/attestation/status"
    headers = {'Cache-Control': 'max-age=0'}
    try:
        crl = request_with_fallback(method='GET', url=url, headers=headers)
        if crl is not None and crl != 'ERROR':
            crl = crl.json()
        else:
            print(f"ERROR: Could not fetch CRL from {url}")
            return False

        certs = [elem.text for elem in ET.parse(filename).getroot().iter() if elem.tag == 'Certificate']

        from cryptography.x509.oid import ExtensionOID
        import logging

        def parse_cert(cert):
            cert = "\n".join(line.strip() for line in cert.strip().split("\n"))
            parsed = x509.load_pem_x509_certificate(cert.encode(), default_backend())
            issuer = None
            serial_number = None
            sig_algo = None
            expiry = None
            key_usages = 'None'

            try:
                issuer = parsed.issuer.rfc4514_string()
            except Exception as e:
                logging.error(f"Issuer extraction failed: {e}")
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

            return serial_number, issuer, sig_algo, expiry, key_usages

        is_sw_signed = False
        i = 1
        is_revoked = False
        print(f"\nChecking keybox: {filename} ...")
        cert_sn_text = "REDACTED"
        cert_issuer_test = "REDACTED"

        for cert in certs:
            cert_sn, cert_issuer, sig_algo, expiry, key_usages = parse_cert(cert)
            if get_verbose():
                cert_sn_text = cert_sn
                cert_issuer_test = cert_issuer
            print(f'\nCertificate {i} SN:       {cert_sn_text}')
            print(f'Certificate {i} Issuer:   {cert_issuer_test}')
            print(f'Signature Algorithm:    {sig_algo}')
            print(f'Key Usage:              {key_usages}')
            expired_text = ""
            if expiry < datetime.now(timezone.utc):
                expired_text = " (EXPIRED)"
            print(f"Certificate expires on: {expiry} {expired_text}")
            if "Software Attestation" in cert_issuer:
                is_sw_signed = True
            if cert_sn in crl["entries"].keys():
                print(f"*** Certificate {i} is REVOKED ***")
                is_revoked = True
            i += 1

        if is_revoked:
            print('\nKeybox contains revoked certificates!')
            result = False
        else:
            print('\nKeybox is clean from revoked certificates')
            result = True
        if is_sw_signed:
            print('Keybox is software signed! This is not a hardware-backed keybox!')
            result =  False
        print('')
        return result
    except Exception as e:
        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in check_kb function")
        print(e)
        traceback.print_exc()


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
            theCmd = f"{get_linux_shell()} /usr/bin/env bash -c {theCmd}"
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
def run_shell2(cmd, timeout=None, detached=False, directory=None, encoding='ISO-8859-1'):
    try:
        flush_output()
        if directory is None:
            proc = subprocess.Popen(f"{cmd}", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding, errors="replace", start_new_session=detached, env=get_env_variables())
        else:
            proc = subprocess.Popen(f"{cmd}", cwd=directory, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding, errors="replace", start_new_session=detached, env=get_env_variables())

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
