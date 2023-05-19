#!/usr/bin/env python

import contextlib
import json
import os

from constants import *

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
        self.no_reboot = False
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
        self.offer_patch_methods = False
        self.use_busybox_shell = False
        self.linux_file_explorer = ''
        self.linux_shell = ''
        self.firmware_has_init_boot = False
        self.rom_has_init_boot = False
        self.show_recovery_patching_option = False

    @classmethod
    def load(cls, file_path):
        conf = cls()
        print("Loading configuration File ...")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding="ISO-8859-1", errors="replace") as f:
                    data = json.load(f)
                    f.close()
                with contextlib.suppress(Exception):
                    conf.device = data['device']
                with contextlib.suppress(Exception):
                    conf.firmware_path = data['firmware_path']
                with contextlib.suppress(Exception):
                    conf.platform_tools_path = data['platform_tools_path']
                with contextlib.suppress(Exception):
                    conf.flash_mode = data['mode']
                with contextlib.suppress(Exception):
                    conf.phone_path = data['phone_path']
                with contextlib.suppress(Exception):
                    conf.magisk = data['magisk']
                with contextlib.suppress(Exception):
                    conf.width = data['width']
                with contextlib.suppress(Exception):
                    conf.height = data['height']
                with contextlib.suppress(Exception):
                    conf.custom_rom = data['custom_rom']
                with contextlib.suppress(Exception):
                    conf.custom_rom_path = data['custom_rom_path']
                with contextlib.suppress(Exception):
                    conf.disable_verification = data['disable_verification']
                with contextlib.suppress(Exception):
                    conf.disable_verity = data['disable_verity']
                with contextlib.suppress(Exception):
                    conf.fastboot_force = data['fastboot_force']
                with contextlib.suppress(Exception):
                    conf.fastboot_verbose = data['fastboot_verbose']
                with contextlib.suppress(Exception):
                    conf.temporary_root = data['temporary_root']
                with contextlib.suppress(Exception):
                    conf.no_reboot = data['no_reboot']
                with contextlib.suppress(Exception):
                    conf.advanced_options = data['advanced_options']
                with contextlib.suppress(Exception):
                    conf.update_check = data['update_check']
                with contextlib.suppress(Exception):
                    conf.version = data['version']
                with contextlib.suppress(Exception):
                    conf.flash_both_slots = data['flash_both_slots']
                with contextlib.suppress(Exception):
                    conf.flash_to_inactive_slot = data['flash_to_inactive_slot']
                with contextlib.suppress(Exception):
                    conf.verbose = data['verbose']
                with contextlib.suppress(Exception):
                    conf.pos_x = data['pos_x']
                with contextlib.suppress(Exception):
                    conf.pos_y = data['pos_y']
                with contextlib.suppress(Exception):
                    conf.data = data
                with contextlib.suppress(Exception):
                    conf.boot_id = data['boot_id']
                with contextlib.suppress(Exception):
                    conf.selected_boot_md5 = data['selected_boot_md5']
                with contextlib.suppress(Exception):
                    conf.force_codepage = data['force_codepage']
                with contextlib.suppress(Exception):
                    conf.custom_codepage = data['custom_codepage']
                with contextlib.suppress(Exception):
                    conf.customize_font = data['customize_font']
                with contextlib.suppress(Exception):
                    conf.pf_font_face = data['pf_font_face']
                with contextlib.suppress(Exception):
                    conf.pf_font_size = data['pf_font_size']
                if conf.flash_to_inactive_slot:
                    conf.flash_both_slots = False
                if conf.flash_both_slots:
                    conf.flash_to_inactive_slot = False
                with contextlib.suppress(Exception):
                    conf.dev_mode = data['dev_mode']
                with contextlib.suppress(Exception):
                    conf.offer_patch_methods = data['offer_patch_methods']
                with contextlib.suppress(Exception):
                    conf.use_busybox_shell = data['use_busybox_shell']
                with contextlib.suppress(Exception):
                    conf.linux_file_explorer = data['linux_file_explorer']
                with contextlib.suppress(Exception):
                    conf.linux_shell = data['linux_shell']
                with contextlib.suppress(Exception):
                    conf.firmware_has_init_boot = data['firmware_has_init_boot']
                with contextlib.suppress(Exception):
                    conf.rom_has_init_boot = data['rom_has_init_boot']
                with contextlib.suppress(Exception):
                    conf.show_recovery_patching_option = data['show_recovery_patching_option']
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
            'no_reboot': self.no_reboot,
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
            'dev_mode': self.dev_mode,
            'offer_patch_methods': self.offer_patch_methods,
            'use_busybox_shell': self.use_busybox_shell,
            'linux_file_explorer': self.linux_file_explorer,
            'linux_shell': self.linux_shell,
            'firmware_has_init_boot': self.firmware_has_init_boot,
            'rom_has_init_boot': self.rom_has_init_boot,
            'show_recovery_patching_option': self.show_recovery_patching_option
        }
        with open(file_path, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
            json.dump(data, f, indent=4)
            f.close()
