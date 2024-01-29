#!/usr/bin/env python

import contextlib
import json
import os
import sys

from datetime import datetime
from constants import *

# ============================================================================
#                               Class Config
# ============================================================================
class Config():
    def __init__(self):
        self.flash_mode = 'dryRun'
        self.firmware_path = None
        self.firmware_is_ota = False
        self.platform_tools_path = None
        self.device = None
        self.phone_path = '/storage/emulated/0/Download'
        self.magisk = 'com.topjohnwu.magisk'
        self.width = MAIN_WIDTH
        self.height = MAIN_HEIGHT
        self.magisk_width = MAGISK_WIDTH
        self.magisk_height = MAGISK_HEIGHT
        self.pif_width = PIF_WIDTH
        self.pif_height = PIF_HEIGHT
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
        self.first_run_date = None
        self.last_run_date = None
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
        self.pf_home = None
        self.firmware_sha256 = None
        self.rom_sha256 = None
        self.boot_sort_column = 0
        self.boot_sorting_direction = 'ASC'
        self.low_mem = False
        self.extra_img_extracts = False
        self.show_notifications = False
        self.create_boot_tar = False
        self.delete_bundled_libs = ''
        self.check_for_disk_space = True
        self.check_for_bootloader_unlocked = True
        self.check_for_firmware_hash_validity = True
        self.google_images_update_frequency = 1
        self.google_images_last_checked = None
        self.enable_dg_clean = False
        self.enable_bulk_prop = False
        self.enable_pixel_img_process = False

        self.toolbar = {
            'tb_position': 'top',
            'tb_show_text': True,
            'tb_show_icons': True,
            'visible': {
                'install_apk': True,
                'package_manager': True,
                'adb_shell': True,
                'scrcpy': True,
                'device_info': True,
                'partition_manager': True,
                'switch_slot': True,
                'reboot_system': True,
                'reboot_bootloader': True,
                'reboot_fastbootd': True,
                'reboot_recovery': True,
                'reboot_safe_mode': True,
                'reboot_download': True,
                'reboot_sideload': True,
                'magisk_modules': True,
                'install_magisk': True,
                'magisk_backup_manager': True,
                'pif_manager': True,
                'sos': True,
                'lock_bootloader': True,
                'unlock_bootloader': True,
                'configuration': True
            }
        }

        self.pif = {
            'auto_update_pif_json': False,
            'auto_check_play_integrity': False,
            'test_app_index': 0,
            'disable_uiautomator': False,
            'auto_fill': False,
            'force_first_api': False,
            'first_api_value_when_forced': "25",
            'sort_keys': True,
            'keep_unknown': True
        }

        self.scrcpy = {
            'path': '',
            'flags': ''
        }

    @classmethod
    def load(cls, file_path):
        conf = cls()
        print("Loading configuration File ...")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding="ISO-8859-1", errors="replace") as f:
                    data = json.load(f)
                    conf.data = data
                with contextlib.suppress(KeyError):
                    conf.first_run_date = data['first_run_date']
                with contextlib.suppress(KeyError):
                    conf.device = data['device']
                with contextlib.suppress(KeyError):
                    conf.firmware_path = data['firmware_path']
                with contextlib.suppress(KeyError):
                    conf.firmware_is_ota = data['firmware_is_ota']
                with contextlib.suppress(KeyError):
                    conf.platform_tools_path = data['platform_tools_path']
                with contextlib.suppress(KeyError):
                    conf.flash_mode = data['mode']
                with contextlib.suppress(KeyError):
                    conf.phone_path = data['phone_path']
                with contextlib.suppress(KeyError):
                    conf.magisk = data['magisk']
                with contextlib.suppress(KeyError):
                    conf.width = data['width']
                with contextlib.suppress(KeyError):
                    conf.height = data['height']
                with contextlib.suppress(KeyError):
                    conf.magisk_width = data['magisk_width']
                with contextlib.suppress(KeyError):
                    conf.magisk_height = data['magisk_height']
                with contextlib.suppress(KeyError):
                    conf.pif_width = data['pif_width']
                with contextlib.suppress(KeyError):
                    conf.pif_height = data['pif_height']
                with contextlib.suppress(KeyError):
                    conf.custom_rom = data['custom_rom']
                with contextlib.suppress(KeyError):
                    conf.custom_rom_path = data['custom_rom_path']
                with contextlib.suppress(KeyError):
                    conf.disable_verification = data['disable_verification']
                with contextlib.suppress(KeyError):
                    conf.disable_verity = data['disable_verity']
                with contextlib.suppress(KeyError):
                    conf.fastboot_force = data['fastboot_force']
                with contextlib.suppress(KeyError):
                    conf.fastboot_verbose = data['fastboot_verbose']
                with contextlib.suppress(KeyError):
                    conf.temporary_root = data['temporary_root']
                with contextlib.suppress(KeyError):
                    conf.no_reboot = data['no_reboot']
                with contextlib.suppress(KeyError):
                    conf.advanced_options = data['advanced_options']
                with contextlib.suppress(KeyError):
                    conf.update_check = data['update_check']
                with contextlib.suppress(KeyError):
                    conf.version = data['version']
                with contextlib.suppress(KeyError):
                    conf.flash_both_slots = data['flash_both_slots']
                with contextlib.suppress(KeyError):
                    conf.flash_to_inactive_slot = data['flash_to_inactive_slot']
                with contextlib.suppress(KeyError):
                    conf.verbose = data['verbose']
                with contextlib.suppress(KeyError):
                    conf.pos_x = data['pos_x']
                with contextlib.suppress(KeyError):
                    conf.pos_y = data['pos_y']
                with contextlib.suppress(KeyError):
                    conf.boot_id = data['boot_id']
                with contextlib.suppress(KeyError):
                    conf.selected_boot_md5 = data['selected_boot_md5']
                with contextlib.suppress(KeyError):
                    conf.force_codepage = data['force_codepage']
                with contextlib.suppress(KeyError):
                    conf.custom_codepage = data['custom_codepage']
                with contextlib.suppress(KeyError):
                    conf.customize_font = data['customize_font']
                with contextlib.suppress(KeyError):
                    conf.pf_font_face = data['pf_font_face']
                with contextlib.suppress(KeyError):
                    conf.pf_font_size = data['pf_font_size']
                if conf.flash_to_inactive_slot:
                    conf.flash_both_slots = False
                if conf.flash_both_slots:
                    conf.flash_to_inactive_slot = False
                with contextlib.suppress(KeyError):
                    conf.dev_mode = data['dev_mode']
                with contextlib.suppress(KeyError):
                    conf.offer_patch_methods = data['offer_patch_methods']
                with contextlib.suppress(KeyError):
                    conf.use_busybox_shell = data['use_busybox_shell']
                with contextlib.suppress(KeyError):
                    conf.linux_file_explorer = data['linux_file_explorer']
                with contextlib.suppress(KeyError):
                    conf.linux_shell = data['linux_shell']
                with contextlib.suppress(KeyError):
                    conf.firmware_has_init_boot = data['firmware_has_init_boot']
                with contextlib.suppress(KeyError):
                    conf.rom_has_init_boot = data['rom_has_init_boot']
                with contextlib.suppress(KeyError):
                    conf.show_recovery_patching_option = data['show_recovery_patching_option']
                with contextlib.suppress(KeyError):
                    conf.pf_home = data['pf_home']
                with contextlib.suppress(KeyError):
                    conf.firmware_sha256 = data['firmware_sha256']
                with contextlib.suppress(KeyError):
                    conf.rom_sha256 = data['rom_sha256']
                with contextlib.suppress(KeyError):
                    conf.low_mem = data['low_mem']
                with contextlib.suppress(KeyError):
                    conf.extra_img_extracts = data['extra_img_extracts']
                with contextlib.suppress(KeyError):
                    conf.show_notifications = data['show_notifications']
                with contextlib.suppress(KeyError):
                    conf.create_boot_tar = data['create_boot_tar']
                with contextlib.suppress(KeyError):
                    conf.delete_bundled_libs = data['delete_bundled_libs']
                with contextlib.suppress(KeyError):
                    conf.check_for_disk_space = data['check_for_disk_space']
                with contextlib.suppress(KeyError):
                    conf.check_for_bootloader_unlocked = data['check_for_bootloader_unlocked']
                with contextlib.suppress(KeyError):
                    conf.check_for_firmware_hash_validity = data['check_for_firmware_hash_validity']
                with contextlib.suppress(KeyError):
                    conf.google_images_update_frequency = data['google_images_update_frequency']
                with contextlib.suppress(KeyError):
                    conf.google_images_last_checked = data['google_images_last_checked']
                with contextlib.suppress(KeyError):
                    conf.enable_dg_clean = data['enable_dg_clean']
                with contextlib.suppress(KeyError):
                    conf.enable_bulk_prop = data['enable_bulk_prop']
                with contextlib.suppress(KeyError):
                    conf.enable_pixel_img_process = data['enable_pixel_img_process']

                # read the toolbar section
                with contextlib.suppress(KeyError):
                    toolbar_data = data['toolbar']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['tb_position'] = toolbar_data['tb_position']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['tb_show_text'] = toolbar_data['tb_show_text']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['tb_show_icons'] = toolbar_data['tb_show_icons']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['install_apk'] = toolbar_data['visible']['install_apk']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['package_manager'] = toolbar_data['visible']['package_manager']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['adb_shell'] = toolbar_data['visible']['adb_shell']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['scrcpy'] = toolbar_data['visible']['scrcpy']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['device_info'] = toolbar_data['visible']['device_info']
                    # with contextlib.suppress(KeyError):
                    #     conf.toolbar['visible']['check_verity'] = toolbar_data['visible']['check_verity']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['partition_manager'] = toolbar_data['visible']['partition_manager']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['switch_slot'] = toolbar_data['visible']['switch_slot']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_system'] = toolbar_data['visible']['reboot_system']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_bootloader'] = toolbar_data['visible']['reboot_bootloader']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_fastbootd'] = toolbar_data['visible']['reboot_fastbootd']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_recovery'] = toolbar_data['visible']['reboot_recovery']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_safe_mode'] = toolbar_data['visible']['reboot_safe_mode']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_download'] = toolbar_data['visible']['reboot_download']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['reboot_sideload'] = toolbar_data['visible']['reboot_sideload']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['magisk_modules'] = toolbar_data['visible']['magisk_modules']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['install_magisk'] = toolbar_data['visible']['install_magisk']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['magisk_backup_manager'] = toolbar_data['visible']['magisk_backup_manager']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['pif_manager'] = toolbar_data['visible']['pif_manager']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['sos'] = toolbar_data['visible']['sos']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['lock_bootloader'] = toolbar_data['visible']['lock_bootloader']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['unlock_bootloader'] = toolbar_data['visible']['unlock_bootloader']
                    with contextlib.suppress(KeyError):
                        conf.toolbar['visible']['configuration'] = toolbar_data['visible']['configuration']

                    # read the pif section
                    pif_data = data['pif']
                    with contextlib.suppress(KeyError):
                        conf.pif['auto_update_pif_json'] = pif_data['auto_update_pif_json']
                    with contextlib.suppress(KeyError):
                        conf.pif['auto_check_play_integrity'] = pif_data['auto_check_play_integrity']
                    with contextlib.suppress(KeyError):
                        conf.pif['test_app_index'] = pif_data['test_app_index']
                    with contextlib.suppress(KeyError):
                        conf.pif['disable_uiautomator'] = pif_data['disable_uiautomator']
                    with contextlib.suppress(KeyError):
                        conf.pif['auto_fill'] = pif_data['auto_fill']
                    with contextlib.suppress(KeyError):
                        conf.pif['force_first_api'] = pif_data['force_first_api']
                    with contextlib.suppress(KeyError):
                        conf.pif['first_api_value_when_forced'] = pif_data['first_api_value_when_forced']
                    with contextlib.suppress(KeyError):
                        conf.pif['sort_keys'] = pif_data['sort_keys']
                    with contextlib.suppress(KeyError):
                        conf.pif['keep_unknown'] = pif_data['keep_unknown']

                # read the scrcpy section
                scrcpy_folder = ''
                with contextlib.suppress(KeyError):
                    scrcpy_data = data['scrcpy']
                    with contextlib.suppress(KeyError):
                        scrcpy_folder = scrcpy_data['folder']
                    with contextlib.suppress(KeyError):
                        conf.scrcpy['path'] = scrcpy_data['path']
                    with contextlib.suppress(KeyError):
                        # handle legacy folder instead of path situation.
                        if scrcpy_folder and not conf.scrcpy['path']:
                            if sys.platform == "win32":
                                conf.scrcpy['path'] = os.path.join(scrcpy_folder, 'scrcpy.exe')
                            else:
                                conf.scrcpy['path'] = os.path.join(scrcpy_folder, 'scrcpy')
                            scrcpy_folder = ''
                    with contextlib.suppress(KeyError):
                        conf.scrcpy['flags'] = scrcpy_data['flags']
            else:
                conf.first_run = True
                conf.first_run_date = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: encountered an exception during configuartion file loading.")
            print(f"Exception: {e}")
            print("Deleting the configuration file to recover ...")
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
            'firmware_is_ota': self.firmware_is_ota,
            'platform_tools_path': self.platform_tools_path,
            'mode': self.flash_mode,
            'phone_path': self.phone_path,
            'magisk': self.magisk,
            'first_run_date': self.first_run_date,
            'last_run_date': f"{datetime.now():%Y-%m-%d %H:%M:%S}",
            'width': self.width,
            'height': self.height,
            'magisk_width': self.magisk_width,
            'magisk_height': self.magisk_height,
            'pif_width': self.pif_width,
            'pif_height': self.pif_height,
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
            'show_recovery_patching_option': self.show_recovery_patching_option,
            'pf_home': self.pf_home,
            'firmware_sha256': self.firmware_sha256,
            'rom_sha256': self.rom_sha256,
            'low_mem': self.low_mem,
            'extra_img_extracts': self.extra_img_extracts,
            'show_notifications': self.show_notifications,
            'create_boot_tar': self.create_boot_tar,
            'delete_bundled_libs': self.delete_bundled_libs,
            'check_for_disk_space': self.check_for_disk_space,
            'check_for_bootloader_unlocked': self.check_for_bootloader_unlocked,
            'check_for_firmware_hash_validity': self.check_for_firmware_hash_validity,
            'google_images_update_frequency': self.google_images_update_frequency,
            'google_images_last_checked': self.google_images_last_checked,
            'enable_dg_clean': self.enable_dg_clean,
            'enable_bulk_prop': self.enable_bulk_prop,
            'enable_pixel_img_process': self.enable_pixel_img_process,
            'toolbar': self.toolbar,  # Save the toolbar settings as well
            'pif': self.pif,  # Save the pif settings as well
            'scrcpy': self.scrcpy  # Save the scrcpy settings as well
        }
        with open(file_path, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
            json.dump(data, f, indent=4)
            f.close()
