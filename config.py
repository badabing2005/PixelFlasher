#!/usr/bin/env python

import json
import os

VERSION = '4.8.2.0'
SDKVERSION = '33.0.3'
WIDTH = 1400
HEIGHT = 1040
POS_X = 40
POS_Y = 40


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
        self.boot_id = None
        self.selected_boot_md5 = None
        self.custom_rom = False
        self.custom_rom_path = None
        self.disable_verification = False
        self.disable_verity = False
        self.fastboot_verbose = False
        self.temporary_root = False
        self.fastboot_force = False
        self.advanced_options = False
        self.update_check = True
        self.version = VERSION
        self.flash_both_slots = False
        self.flash_to_inactive_slot = False
        self.verbose = False
        self.pos_x = POS_X
        self.pos_y = POS_Y
        self.data = None
        self.show_all_boot=False
        self.first_run=False
        self.force_codepage = False
        self.custom_codepage = None
        self.customize_font = False
        self.pf_font_face = 'Courier'
        self.pf_font_size = 12
        self.dev_mode = False

    @classmethod
    def load(cls, file_path):
        conf = cls()
        print("Loading configuration File ...")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding="ISO-8859-1", errors="replace") as f:
                    data = json.load(f)
                    f.close()
                conf.device = data['device']
                conf.firmware_path = data['firmware_path']
                conf.platform_tools_path = data['platform_tools_path']
                conf.flash_mode = data['mode']
                conf.phone_path = data['phone_path']
                conf.magisk = data['magisk']
                conf.width = data['width']
                conf.height = data['height']
                conf.custom_rom = data['custom_rom']
                conf.custom_rom_path = data['custom_rom_path']
                conf.disable_verification = data['disable_verification']
                conf.disable_verity = data['disable_verity']
                conf.fastboot_force = data['fastboot_force']
                conf.fastboot_verbose = data['fastboot_verbose']
                conf.temporary_root = data['temporary_root']
                conf.advanced_options = data['advanced_options']
                conf.update_check = data['update_check']
                conf.version = data['version']
                conf.flash_both_slots = data['flash_both_slots']
                conf.flash_to_inactive_slot = data['flash_to_inactive_slot']
                conf.verbose = data['verbose']
                conf.pos_x = data['pos_x']
                conf.pos_y = data['pos_y']
                conf.data = data
                conf.boot_id = data['boot_id']
                conf.selected_boot_md5 = data['selected_boot_md5']
                conf.force_codepage = data['force_codepage']
                conf.custom_codepage = data['custom_codepage']
                conf.customize_font = data['customize_font']
                conf.pf_font_face = data['pf_font_face']
                conf.pf_font_size = data['pf_font_size']
                if conf.flash_to_inactive_slot:
                    conf.flash_both_slots = False
                if conf.flash_both_slots:
                    conf.flash_to_inactive_slot = False
                conf.dev_mode = data['dev_mode']
            else:
                conf.first_run = True
        except Exception as e:
            os.remove(file_path)
        return conf

    def save(self, file_path):
        if self.flash_to_inactive_slot:
            self.flash_both_slots = False
        if self.flash_both_slots:
            self.flash_to_inactive_slot = False
        data = {
            'device': self.device,
            'firmware_path': self.firmware_path,
            'platform_tools_path': self.platform_tools_path,
            'mode': self.flash_mode,
            'phone_path': self.phone_path,
            'magisk': self.magisk,
            'width': self.width,
            'height': self.height,
            'custom_rom': self.custom_rom,
            'custom_rom_path': self.custom_rom_path,
            'disable_verification': self.disable_verification,
            'disable_verity': self.disable_verity,
            'fastboot_force': self.fastboot_force,
            'fastboot_verbose': self.fastboot_verbose,
            'temporary_root': self.temporary_root,
            'advanced_options': self.advanced_options,
            'update_check': self.update_check,
            'version': VERSION,
            'flash_both_slots': self.flash_both_slots,
            'flash_to_inactive_slot': self.flash_to_inactive_slot,
            'verbose': self.verbose,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'boot_id': self.boot_id,
            'selected_boot_md5': self.selected_boot_md5,
            'force_codepage': self.force_codepage,
            'custom_codepage': self.custom_codepage,
            'customize_font': self.customize_font,
            'pf_font_face': self.pf_font_face,
            'pf_font_size': self.pf_font_size,
            'dev_mode': self.dev_mode
        }
        with open(file_path, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
            json.dump(data, f, indent=4)
            f.close()
