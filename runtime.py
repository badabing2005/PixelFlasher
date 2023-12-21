#!/usr/bin/env python

import binascii
import contextlib
import fnmatch
import hashlib
import io
import json
import ntpath
import os
import re
import shutil
import signal
import sqlite3 as sl
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import zipfile
import psutil
import xml.etree.ElementTree as ET
from datetime import datetime
from os import path
from urllib.parse import urlparse

import lz4.frame
import requests
import wx
from packaging.version import parse
from platformdirs import *
from constants import *

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
    wx.YieldIfNeeded()
    if console_widget:
        sys.stdout.flush()
        wx.CallAfter(console_widget.Update)
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
    if parse(VERSION) < parse('7.0.0'):
        return 'factory_images'
    else:
        return 'factory_images7'


# ============================================================================
#                               Function get_pf_db
# ============================================================================
def get_pf_db():
    # we have different db schemas for each of these versions
    if parse(VERSION) < parse('4.0.0'):
        return 'PixelFlasher.db'
    elif parse(VERSION) < parse('7.0.0'):
        return 'PixelFlasher4.db'
    else:
        return 'PixelFlasher7.db'


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
def get_phone():
    devices = get_phones()
    phone_id = get_phone_id()
    if phone_id and devices:
        for phone in devices:
            if phone.id == phone_id:
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
                with open(config_file_path, 'r', encoding="ISO-8859-1", errors="replace") as f:
                    data = json.load(f)
                    f.close()
                pf_home = data['pf_home']
                if pf_home and os.path.exists(pf_home):
                    set_config_path(pf_home)
        config_path = get_config_path()
        if not os.path.exists(os.path.join(config_path, 'logs')):
            os.makedirs(os.path.join(config_path, 'logs'), exist_ok=True)
        if not os.path.exists(os.path.join(config_path, 'factory_images')):
            os.makedirs(os.path.join(config_path, 'factory_images'), exist_ok=True)
        if not os.path.exists(os.path.join(config_path, get_boot_images_dir())):
            os.makedirs(os.path.join(config_path, get_boot_images_dir()), exist_ok=True)
        if not os.path.exists(os.path.join(config_path, 'tmp')):
            os.makedirs(os.path.join(config_path, 'tmp'), exist_ok=True)
        if not os.path.exists(os.path.join(config_path, 'puml')):
            os.makedirs(os.path.join(config_path, 'puml'), exist_ok=True)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while init_config_path")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while init_db")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: {path_to_7z} is not found")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while deleting bundled library")
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
        response = requests.get('https://github.com/badabing2005/PixelFlasher/releases/latest')
        # look in history to find the 302, and get the loaction header
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
        else:
            subprocess.Popen(["nautilus", dir_path], env=get_env_variables())
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a folder.")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening a terminal.")
        traceback.print_exc()


# ============================================================================
#                               Function check_archive_contains_file
# ============================================================================
def check_archive_contains_file(archive_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        debug(f"Looking for {file_to_check} in file {archive_file_path} with nested: {nested}")

        file_ext = os.path.splitext(archive_file_path)[1].lower()

        if file_ext == '.zip':
            return check_zip_contains_file(archive_file_path, file_to_check, get_low_memory(), nested, is_recursive)
        elif file_ext in ['.tgz', '.gz', '.tar', '.md5']:
            return check_tar_contains_file(archive_file_path, file_to_check, nested, is_recursive)
        else:
            debug("Unsupported file format.")
            return ''
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while check_archive_contains_file.")
        traceback.print_exc()


# ============================================================================
#                               Function check_zip_conatins_file
# ============================================================================
def check_zip_contains_file(zip_file_path, file_to_check, low_mem, nested=False, is_recursive=False):
    if low_mem:
        return check_zip_contains_file_lowmem(zip_file_path, file_to_check, nested, is_recursive)
    else:
        return check_zip_contains_file_fast(zip_file_path, file_to_check, nested, is_recursive)



# ============================================================================
#                               Function check_zip_conatins_file_fast
# ============================================================================
def check_zip_contains_file_fast(zip_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        if not is_recursive:
            debug(f"Looking for {file_to_check} in zipfile {zip_file_path} with zip-nested: {nested}")
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
            debug(f"file: {file_to_check} was NOT found\n")
            return ''
    except Exception as e:
        print(f"Failed to check_zip_contains_file_fast. Reason: {e}")
        traceback.print_exc()
        return ''


# ============================================================================
#                               Function check_zip_contains_file_lowmem
# ============================================================================
def check_zip_contains_file_lowmem(zip_file_path, file_to_check, nested=False, is_recursive=False):
    try:
        if not is_recursive:
            debug(f"Looking for {file_to_check} in zipfile {zip_file_path} with zip-nested: {nested} Low Memory version.")

        stack = [(zip_file_path, '')]

        while stack:
            current_zip, current_path = stack.pop()

            with zipfile.ZipFile(current_zip, 'r') as zip_file:
                for name in zip_file.namelist():
                    full_name = os.path.join(current_path, name)
                    debug(f"Checking: {full_name}")

                    # if full_name.endswith(f'/{file_to_check}') or full_name == file_to_check:
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
                        if is_recursive:
                            stack.append((temp_zip_path, full_name))  # Add the nested zip to be processed recursively

                        # Clean up the temporary zip file
                        os.remove(temp_zip_path)
        debug(f"File {file_to_check} was NOT found")
        return ''
    except Exception as e:
        print(f"Failed to check_zip_contains_file_lowmem. Reason: {e}")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while check_tar_contains_file.")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting sip file list.")
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
#                               Function get_ui_cooridnates
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
            print("Warning!: The SHA1 values have different lengths")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while comparing sha1.")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while extracting fingerprint.")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error computing md5.")
        traceback.print_exc()


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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while computing sha1")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while computing sha256")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while unpacking lz4")
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
            if res.returncode == 0:
                # extract the code page portion
                try:
                    debug(f"CP: {res.stdout}")
                    cp = res.stdout.split(":")
                    cp = cp[1].strip()
                    cp = int(cp.replace('.',''))
                    print(f"Active code page: {cp}")
                    set_system_codepage(cp)
                except Exception:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to get Active code page.\n")
                    traceback.print_exc()
                    print(f"{res.stderr}")
                    print(f"{res.stdout}")
            else:
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Unable to get Active code page.\n")
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting codepage.")
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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} Creating support.zip file ...")
        config_path = get_config_path()
        tmp_dir_full = os.path.join(config_path, 'tmp')
        support_dir_full = os.path.join(config_path, 'support')
        support_zip = os.path.join(tmp_dir_full, 'support.zip')

        # if a previous support dir exist delete it allong with support.zip
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
        to_copy = os.path.join(config_path, 'PixelFlasher.json')
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
            shutil.copy(custom_config_file, support_dir_full, follow_symlinks=True)

        # copy PixelFlasher.db to tmp\support folder
        to_copy = os.path.join(config_path, get_pf_db())
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

        # zip support folder
        debug(f"Zipping {support_dir_full} ...")
        shutil.make_archive(support_dir_full, 'zip', support_dir_full)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while creating support.zip.")
        traceback.print_exc()


# ============================================================================
#                               Function sanitize_file
# ============================================================================
def sanitize_file(filename):
    debug(f"Santizing {filename} ...")
    with contextlib.suppress(Exception):
        with open(filename, "rt", encoding='ISO-8859-1', errors="replace") as fin:
            data = fin.read()
        data = re.sub(r'(\\Users\\+)(?:.*?)(\\+)', r'\1REDACTED\2', data, flags=re.IGNORECASE)
        data = re.sub(r'(\/Users\/+)(?:.*?)(\/+)', r'\1REDACTED\2', data, flags=re.IGNORECASE)
        data = re.sub(r'(\"device\":\s+)(\"\w+?\")', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(device\sid:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(device:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(device\s+\')(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(Rebooting device\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(Flashing device\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(waiting for\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(Serial\sNumber\.+\:\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(fastboot(.exe)?\"? -s\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(adb(.exe)?\"? -s\s+)(\w+)', r'\1REDACTED', data, flags=re.IGNORECASE)
        data = re.sub(r'(\S\  \((?:adb|f\.b|rec|sid)\)   )(.+?)(\s+.*)', r'\1REDACTED\3', data, flags=re.IGNORECASE)
        with open(filename, "wt", encoding='ISO-8859-1', errors="replace") as fin:
            fin.write(data)


# ============================================================================
#                               Function sanitize_db
# ============================================================================
def sanitize_db(filename):
    debug(f"Santizing {filename} ...")
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
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 404:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Module update not found for URL: {url}")
            return -1
        response.raise_for_status()
        data = response.json()
        mu = ModuleUpdate(url)
        setattr(mu, 'version', data['version'])
        setattr(mu, 'versionCode', data['versionCode'])
        setattr(mu, 'zipUrl', data['zipUrl'])
        setattr(mu, 'changelog', data['changelog'])
        headers = {}
        response = requests.request("GET", mu.changelog, headers=headers, data=payload)
        setattr(mu, 'changelog', response.text)
        return mu
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during getUpdateDetails url: {url} processing")
        traceback.print_exc()
        return -1

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
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while getting free space.")
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
#                               Function download_file
# ============================================================================
def download_file(url, filename = None):
    if url:
        print (f"Downloading File: {url}")
        try:
            response = requests.get(url)
            config_path = get_config_path()
            if not filename:
                filename = os.path.basename(urlparse(url).path)
            downloaded_file_path = os.path.join(config_path, 'tmp', filename)
            open(downloaded_file_path, "wb").write(response.content)
            # check if filename got downloaded
            if not os.path.exists(downloaded_file_path):
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
                print("Aborting ...\n")
                return 'ERROR'
        except Exception:
            print (f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to download file from  {url}\n")
            traceback.print_exc()
            return 'ERROR'
    return downloaded_file_path


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
#                               Function process_pi_xml
# ============================================================================
def process_pi_xml_piac(filename):
    with open(filename, 'r') as file:
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
#                               Function process_pi_xml2
# ============================================================================
def process_pi_xml_spic(filename):
    with open(filename, 'r') as file:
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
#                               Function process_pi_xml3
# ============================================================================
def process_pi_xml_tb(filename):
    with open(filename, 'r') as file:
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
#                               Function process_pi_xml4
# ============================================================================
def process_pi_xml_ps(filename):
    with open(filename, 'r') as file:
        xml_content = file.read()

    # Find the position of "Play Integrity Result:"
    labels_pos = xml_content.find('text="Labels:')

    # If "Result Play integrity" is found, continue searching for index="3"
    if labels_pos != -1:

        # Adjust the position to point at the end of 'text=' and then get the next value between [ ].
        labels_pos += len('text="Labels:')

        value_start_pos = xml_content.find('[', labels_pos) + 1
        value_end_pos = xml_content.find(']', value_start_pos)
        result = xml_content[value_start_pos:value_end_pos]
        debug(result)
        return result

# ============================================================================
#                               Function run_shell
# ============================================================================
# We use this when we want to capture the returncode and also selectively
# output what we want to console. Nothing is sent to console, both stdout and
# stderr are only available when the call is completed.
def run_shell(cmd, timeout=None):
    try:
        flush_output()
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='ISO-8859-1', errors="replace", env=get_env_variables())
        # Wait for the process to complete or timeout
        stdout, stderr = process.communicate(timeout=timeout)
        # Return the response
        return subprocess.CompletedProcess(args=cmd, returncode=process.returncode, stdout=stdout, stderr=stderr)
    except subprocess.TimeoutExpired as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command timed out after {timeout} seconds")
        puml("#red:Command timed out;\n", True)
        puml(f"note right\n{e}\nend note\n")
        # Send CTRL + C signal to the process
        process.send_signal(signal.SIGTERM)
        process.terminate()
        return subprocess.CompletedProcess(args=cmd, returncode=-1, stdout='', stderr='')

    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e
        # return subprocess.CompletedProcess(args=cmd, returncode=-2, stdout='', stderr='')


# ============================================================================
#                               Function run_shell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
def run_shell2(cmd, timeout=None, detached=False, directory=None):
    try:
        flush_output()
        if directory is None:
            proc = subprocess.Popen(f"{cmd}", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='ISO-8859-1', errors="replace", start_new_session=detached, env=get_env_variables())
        else:
            proc = subprocess.Popen(f"{cmd}", cwd=directory, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='ISO-8859-1', errors="replace", start_new_session=detached, env=get_env_variables())

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
                print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Command timed out after {timeout} seconds")
                puml("#red:Command timed out;\n", True)
                puml(f"note right\nCommand timed out after {timeout} seconds\nend note\n")
                return subprocess.CompletedProcess(args=cmd, returncode=-1, stdout='', stderr='')
        proc.wait()
        # Wait for the process to complete and capture the output
        stdout, stderr = proc.communicate()
        return subprocess.CompletedProcess(args=cmd, returncode=proc.returncode, stdout=stdout, stderr=stderr)
    except Exception as e:
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while executing run_shell2")
        traceback.print_exc()
        puml("#red:Encountered an error;\n", True)
        puml(f"note right\n{e}\nend note\n")
        raise e
        # return subprocess.CompletedProcess(args=cmd, returncode=-2, stdout='', stderr='')

