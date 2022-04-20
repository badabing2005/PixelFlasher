#!/usr/bin/env python

import os
import json

VERSION = "2.4.1.0"
WIDTH = 1200
HEIGHT = 800


# ============================================================================
#                               Class Config
# ============================================================================
class Config():
    def __init__(self):
        self.flash_mode = 'dryRun'
        self.firmware_path = None
        self.platform_tools_path = None
        self.device = None
        self.phone_path = '/storage/emulated/0/Download'
        self.magisk = 'com.topjohnwu.magisk'
        self.width = WIDTH
        self.height = HEIGHT
        self.patch_boot = True
        self.custom_rom = False
        self.custom_rom_path = None
        self.disable_verification = False
        self.disable_verity = False
        self.fastboot_verbose = False
        self.advanced_options = False
        self.update_check = True
        self.version = VERSION
        self.flash_both_slots = False
        self.verbose = False
        self.pos_x = None
        self.pos_y = None
        self.data = None

    @classmethod
    def load(cls, file_path):
        conf = cls()
        print(f"Loading configuration File ...")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    f.close()
                conf.data = data
                conf.device = data['device']
                conf.firmware_path = data['firmware_path']
                conf.platform_tools_path = data['platform_tools_path']
                conf.flash_mode = data['mode']
                conf.phone_path = data['phone_path']
                conf.magisk = data['magisk']
                conf.width = data['width']
                conf.height = data['height']
                conf.patch_boot = data['patch_boot']
                conf.custom_rom = data['custom_rom']
                conf.custom_rom_path = data['custom_rom_path']
                conf.disable_verification = data['disable_verification']
                conf.disable_verity = data['disable_verity']
                conf.fastboot_verbose = data['fastboot_verbose']
                conf.advanced_options = data['advanced_options']
                conf.update_check = data['update_check']
                conf.version = data['version']
                conf.flash_both_slots = data['flash_both_slots']
                conf.verbose = data['verbose']
                conf.pos_x = data['pos_x']
                conf.pos_y = data['pos_y']
        except Exception as e:
            os.remove(file_path)
        return conf

    def save(self, file_path):
        data = {
            'device': self.device,
            'firmware_path': self.firmware_path,
            'platform_tools_path': self.platform_tools_path,
            'mode': self.flash_mode,
            'phone_path': self.phone_path,
            'magisk': self.magisk,
            'width': self.width,
            'height': self.height,
            'patch_boot': self.patch_boot,
            'custom_rom': self.custom_rom,
            'custom_rom_path': self.custom_rom_path,
            'disable_verification': self.disable_verification,
            'disable_verity': self.disable_verity,
            'fastboot_verbose': self.fastboot_verbose,
            'advanced_options': self.advanced_options,
            'update_check': self.update_check,
            'version': VERSION,
            'flash_both_slots': self.flash_both_slots,
            'verbose': self.verbose,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            f.close()
