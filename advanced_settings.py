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

import wx
import images as images
import webbrowser
import sys
from runtime import *
from constants import *
from i18n import _


# ============================================================================
#                               Class AdvancedSettings
# ============================================================================
class AdvancedSettings(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.SetTitle(_("Advanced Configuration Settings"))

        # Top Part:
        top_panel = wx.Panel(self)
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        # advanced options
        advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.advanced_options_checkbox = wx.CheckBox(parent=top_panel, id=wx.ID_ANY, label=_("Enable Advanced Options (only enable this if you know what you're doing)"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.advanced_options_checkbox.SetToolTip(_("Expert mode"))
        advanced_options_sizer.Add(self.advanced_options_checkbox, proportion=0, flag=wx.ALL, border=5)
        top_sizer.Add(advanced_options_sizer, proportion=0, flag=wx.EXPAND, border=5)

        # static line
        staticline = wx.StaticLine(parent=top_panel, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LI_HORIZONTAL)
        top_sizer.Add(staticline, proportion=0, flag=wx.EXPAND, border=5)

        top_panel.SetSizer(top_sizer)

        # Middle Part: Scrolled panel with widgets
        scrolled_panel = wx.ScrolledWindow(self, style=wx.VSCROLL | wx.HSCROLL)
        middle_sizer = wx.BoxSizer(wx.VERTICAL)

        fgs1 = wx.FlexGridSizer(cols=2, vgap=10, hgap=10)
        # this makes the second column expandable (index starts at 0)
        fgs1.AddGrowableCol(1, 1)
        # this makes the height expandable
        fgs1.AddGrowableRow(0, 1)

        # Magisk Package name
        package_name_label = wx.StaticText(parent=scrolled_panel, label=_("Magisk Package Name"))
        self.package_name = wx.TextCtrl(parent=scrolled_panel, id=-1, size=(-1, -1))
        self.package_name.SetToolTip(_("If you have hidden Magisk,\nset this to the hidden package name."))
        self.reset_magisk_pkg = wx.BitmapButton(parent=scrolled_panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.reset_magisk_pkg.SetBitmap(images.scan_24.GetBitmap())
        self.reset_magisk_pkg.SetToolTip(_("Resets package name to default: %s") % MAGISK_PKG_NAME)
        package_name_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        package_name_sizer.Add(self.package_name, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        package_name_sizer.Add(self.reset_magisk_pkg, proportion=0, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)

        # Spoofed apps package names
        self.spoofed_apps_label = wx.StaticText(parent=scrolled_panel, id=wx.ID_ANY, label=_("Spoofed Apps Package Names"))
        self.spoofed_apps_label.SetToolTip(_("The listed package names are spoofed apps that PixelFlasher will look for."))
        self.spoofed_apps = wx.SearchCtrl(scrolled_panel, style=wx.TE_LEFT)
        self.spoofed_apps.ShowCancelButton(True)
        self.spoofed_apps.SetDescriptiveText(_("Example: xz.jft.fn, otgs.werg.dflkjh"))
        self.spoofed_apps.ShowSearchButton(False)

        # only add if we're on linux
        if sys.platform.startswith("linux"):
            # Linux File Explorer
            file_explorer_label = wx.StaticText(scrolled_panel, label=_("Linux File Explorer:"))
            file_explorer_label.SetSize(self.package_name.GetSize())
            self.file_explorer = wx.TextCtrl(scrolled_panel, -1, size=(300, -1))
            self.file_explorer.SetToolTip(_("Set full path to File Explorer.\nDefault: Nautilus"))
            file_explorer_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
            file_explorer_sizer.Add((20, 0), proportion=0, flag=wx.ALL, border=5)
            file_explorer_sizer.Add(self.file_explorer, proportion=0, flag=wx.LEFT, border=10)

            # Linux Shell
            shell_label = wx.StaticText(parent=scrolled_panel, label=_("Linux Shell:"))
            shell_label.SetSize(self.package_name.GetSize())
            self.shell = wx.TextCtrl(parent=scrolled_panel, id=wx.ID_ANY, size=(300, -1))
            self.shell.SetToolTip(_("Set full path to Linux Shell.\nDefault: gnome-terminal"))
            shell_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
            shell_sizer.Add((20, 0), proportion=0, flag=wx.ALL, border=5)
            shell_sizer.Add(self.shell, proportion=0, flag=wx.LEFT, border=10)

        # Offer Patch methods
        self.patch_methods_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Offer Patch Methods"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.patch_methods_checkbox.SetToolTip(_("When patching the choice of method is presented."))
        self.recovery_patch_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Patching Recovery Partition"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.recovery_patch_checkbox.SetToolTip(_("Enabling this will show an option to patch a recovery partition.\nThis should be kept disabled unless you have an old device.\n(most A-only devices launched with Android 9, legacy SAR)"))
        self.keep_temp_files_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Keep Temp Files"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.keep_temp_files_checkbox.SetToolTip(_("Enabling this will keep temporary files used for patching.\nThis is useful for debugging purposes.\nIt is recommended to keep this disabled."))

        # Use Busybox Shell
        self.use_busybox_shell_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Use Busybox Shell"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.use_busybox_shell_checkbox.SetToolTip(_("When creating a patch, if this is checked, busybox ash will be used as shell."))

        # Enable Low Memory
        self.low_mem_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("System has low memory"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.low_mem_checkbox.SetToolTip(_("Use this option to sacrifice speed in favor of memory."))

        # Extra img extraction
        self.extra_img_extracts_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Extra img extraction"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.extra_img_extracts_checkbox.SetToolTip(_("When checked and available in payload.bin\nAlso extract vendor_boot.img, vendor_kernel_boot.img, dtbo.img, super_empty.img"))

        # Show Notifications
        self.show_notifications_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Show notifications"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.show_notifications_checkbox.SetToolTip(_("When checked PixelFlasher will display system toast notifications."))

        # Always Create boot.tar
        self.create_boot_tar_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Always create boot.tar"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.create_boot_tar_checkbox.SetToolTip(_("When checked, PixelFlasher always creates boot.tar of the patched boot file.\nIf unchecked, only for Samsung firmware boot.tar will be created."))
        self.create_boot_tar_checkbox.Disable()

        # Check for updates options
        self.check_for_update_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Check for updates"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_update_checkbox.SetToolTip(_("Checks for available updates on startup"))

        # Check for Minimum Disk space option
        self.check_for_disk_space_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Check for Minimum Disk (5Gb)"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_disk_space_checkbox.SetToolTip(_("Enforces minimum disk space of 5 Gb to allow flashing.\nThis avoids storage related issues."))

        # Check for Bootloader unlocked option
        self.check_for_bootloader_unlocked_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Check for bootloader unlocked"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_bootloader_unlocked_checkbox.SetToolTip(_("Checks to make sure bootloader is unlocked before flashing."))

        # Check for Firmware hash validity option
        self.check_for_firmware_hash_validity_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Check for firmware hash validity"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_firmware_hash_validity_checkbox.SetToolTip(_("Checks for sha256 portion to be in the image filename to detect Pixel compatible image."))

        # Keep temporary support files option
        self.keep_temporary_support_files_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Keep temporary support files"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.keep_temporary_support_files_checkbox.SetToolTip(_("It keeps the temporary support files.\nUseful for inspecting what data is included in support.zip."))

        # Check if Magisk modules have updates
        self.check_module_updates = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Check Magisk modules for updates"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_module_updates.SetToolTip(_("It checks if the module has updates.\nDisable this if you don't want to check for updates or\n if some module update server has issues and delays the process."))

        # Show custom ROM options
        self.show_custom_rom_options = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Show custom ROM options"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.show_custom_rom_options.SetToolTip(_("Make sure you check if your ROM is supported."))

        # Sanitize support files
        self.sanitize_support_files = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Sanitize (Redact) support files"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.sanitize_support_files.SetToolTip(_("The support files are always encrypted.\nThis option redacts sensitive information from the support files.\nBut impedes support and is not recommended."))

        # KB Indexing
        self.kb_index_cb = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Keybox Index"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.kb_index_cb.SetToolTip(_("This will enable keybox indexing.\nThis is useful if you process multiple keyboxes.\nWhich can be used to analyze keyboxes and compare them to previously processed ones.\nThis can help in identifying duplicate keyboxes"))

        # Force codepage
        self.force_codepage_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Force codepage to"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.force_codepage_checkbox.SetToolTip(_("Uses specified code page instead of system code page"))
        self.code_page = wx.TextCtrl(parent=scrolled_panel, id=wx.ID_ANY, size=(-1, -1))

        # Delete Bundle libs
        self.delete_bundled_libs_label = wx.StaticText(parent=scrolled_panel, id=wx.ID_ANY, label=_("Delete bundled libs"))
        self.delete_bundled_libs_label.SetToolTip(_("The listed libraries would be deleted from the PF bundle to allow system defined ones to be used."))
        self.delete_bundled_libs = wx.SearchCtrl(scrolled_panel, style=wx.TE_LEFT)
        self.delete_bundled_libs.ShowCancelButton(True)
        self.delete_bundled_libs.SetDescriptiveText(_("Example: libreadline.so.8, libgdk*"))
        self.delete_bundled_libs.ShowSearchButton(False)

        # Override KMI
        self.override_kmi_label = wx.StaticText(parent=scrolled_panel, id=wx.ID_ANY, label=_("Override KMI"))
        self.override_kmi_label.SetToolTip(_("This will override the Kernel Module Interface (KMI) to the specified value.\nThis is useful for devices with custom kernels.\nThe value will be passed to KernelSU as the KMI value."))
        self.override_kmi = wx.SearchCtrl(scrolled_panel, style=wx.TE_LEFT)
        self.override_kmi.ShowCancelButton(True)
        self.override_kmi.SetDescriptiveText(_("Example: 5.15.131-android14"))
        self.override_kmi.ShowSearchButton(False)

        # Use Custom Font
        self.use_custom_font_checkbox = wx.CheckBox(parent=scrolled_panel, id=wx.ID_ANY, label=_("Use Custom Fontface"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.use_custom_font_checkbox.SetToolTip(_("Use custom font for monospace fonts\nMight require PixelFlasher restart to properly apply to the Console window."))

        # Font Selection
        fonts = wx.FontEnumerator()
        fonts.EnumerateFacenames(wx.FONTENCODING_SYSTEM, fixedWidthOnly=True)
        font_list = fonts.GetFacenames(wx.FONTENCODING_SYSTEM, fixedWidthOnly=True)
        self.font = wx.ListBox(parent=scrolled_panel, id=wx.ID_ANY, size=(300, 100), choices=font_list)
        self.font_size = wx.SpinCtrl(parent=scrolled_panel, id=wx.ID_ANY, min=6, max=50, initial=self.Parent.config.pf_font_size)
        self.sample = wx.StaticText(parent=scrolled_panel, id=wx.ID_ANY, label=_("Sample "))
        fonts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        fonts_sizer.Add(self.font, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        fonts_sizer.Add(self.font_size, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        fonts_sizer.Add(self.sample, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.font.SetSelection(-1)
        self.font_size.SetToolTip(_('Select font size'))
        self._onFontSelect(None)

        # scrcpy 1st row widgets, select path
        self.scrcpy_path_label = wx.StaticText(parent=scrolled_panel, id=wx.ID_ANY, label=_("scrcpy Path"))
        self.scrcpy_link = wx.BitmapButton(parent=scrolled_panel, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.scrcpy_link.SetBitmap(bitmap=images.open_link_24.GetBitmap())
        self.scrcpy_link.SetToolTip(_("Download scrcpy"))
        self.scrcpy_path_picker = wx.FilePickerCtrl(parent=scrolled_panel, id=wx.ID_ANY, path=wx.EmptyString, message=_("Select scrcpy executable"), wildcard=_("Scrcpy executable (*.exe;*)|*.exe;*"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.FLP_USE_TEXTCTRL)

        self.scrcpy_path_picker.SetToolTip(_("Select scrcpy executable"))
        self.scrcpy_h1sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.scrcpy_h1sizer.Add(window=self.scrcpy_path_label, proportion=0, flag=wx.EXPAND)
        self.scrcpy_h1sizer.AddSpacer(10)
        self.scrcpy_h1sizer.Add(window=self.scrcpy_link, proportion=0, flag=wx.EXPAND)
        self.scrcpy_h1sizer.AddSpacer(10)
        self.scrcpy_h1sizer.Add(window=self.scrcpy_path_picker, proportion=1, flag=wx.EXPAND)

        # scrcpy 2nd row flags
        self.scrcpy_flags = wx.SearchCtrl(scrolled_panel, style=wx.TE_LEFT)
        self.scrcpy_flags.ShowCancelButton(True)
        self.scrcpy_flags.SetDescriptiveText(_("Flags / Arguments (Example: --video-bit-rate 2M --max-fps=30 --max-size 1024)"))
        self.scrcpy_flags.ShowSearchButton(False)

        # build the sizers for scrcpy
        scrcpy_sb = wx.StaticBox(scrolled_panel, -1, _("Scrcpy settings"))
        scrcpy_vsizer = wx.StaticBoxSizer(scrcpy_sb, wx.VERTICAL)
        scrcpy_vsizer.Add(self.scrcpy_h1sizer, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        scrcpy_vsizer.Add(self.scrcpy_flags, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        #
        scrcpy_outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scrcpy_outer_sizer.AddSpacer(20)
        scrcpy_outer_sizer.Add(scrcpy_vsizer, proportion=1, flag=wx.EXPAND, border=10)
        scrcpy_outer_sizer.AddSpacer(20)

        # Set Widget values from config
        self.advanced_options_checkbox.SetValue(self.Parent.config.advanced_options)
        self.package_name.SetValue(self.Parent.config.magisk)
        self.spoofed_apps.SetValue(self.Parent.config.spoofed_apps)
        self.patch_methods_checkbox.SetValue(self.Parent.config.offer_patch_methods)
        self.recovery_patch_checkbox.SetValue(self.Parent.config.show_recovery_patching_option)
        self.keep_temp_files_checkbox.SetValue(self.Parent.config.keep_patch_temporary_files)
        self.use_busybox_shell_checkbox.SetValue(self.Parent.config.use_busybox_shell)
        self.low_mem_checkbox.SetValue(self.Parent.config.low_mem)
        self.extra_img_extracts_checkbox.SetValue(self.Parent.config.extra_img_extracts)
        self.show_notifications_checkbox.SetValue(self.Parent.config.show_notifications)
        self.create_boot_tar_checkbox.SetValue(self.Parent.config.create_boot_tar)
        self.check_for_update_checkbox.SetValue(self.Parent.config.update_check)
        self.check_for_disk_space_checkbox.SetValue(self.Parent.config.check_for_disk_space)
        self.check_for_bootloader_unlocked_checkbox.SetValue(self.Parent.config.check_for_bootloader_unlocked)
        self.check_for_firmware_hash_validity_checkbox.SetValue(self.Parent.config.check_for_firmware_hash_validity)
        self.keep_temporary_support_files_checkbox.SetValue(self.Parent.config.keep_temporary_support_files)
        self.check_module_updates.SetValue(self.Parent.config.check_module_updates)
        self.show_custom_rom_options.SetValue(self.Parent.config.show_custom_rom_options)
        self.sanitize_support_files.SetValue(self.Parent.config.sanitize_support_files)
        self.kb_index_cb.SetValue(self.Parent.config.kb_index)
        self.force_codepage_checkbox.SetValue(self.Parent.config.force_codepage)
        self.delete_bundled_libs.SetValue(self.Parent.config.delete_bundled_libs)
        self.override_kmi.SetValue(self.Parent.config.override_kmi)
        self.code_page.SetValue(str(self.Parent.config.custom_codepage))
        self.use_custom_font_checkbox.SetValue(self.Parent.config.customize_font)
        self.font.SetStringSelection(self.Parent.config.pf_font_face)

        if self.Parent.config.scrcpy and self.Parent.config.scrcpy['path'] != '' and os.path.exists(self.Parent.config.scrcpy['path']):
            self.scrcpy_path_picker.SetPath(self.Parent.config.scrcpy['path'])
        if self.Parent.config.scrcpy and self.Parent.config.scrcpy['flags'] != '':
            self.scrcpy_flags.SetValue(self.Parent.config.scrcpy['flags'])

        if sys.platform.startswith("linux"):
            self.file_explorer.SetValue(self.Parent.config.linux_file_explorer)
            self.shell.SetValue(self.Parent.config.linux_shell)

        # add the widgets to the grid in two columns, first fix size, the second expandable.
        fgs1.Add(package_name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        fgs1.Add(package_name_sizer, 0, wx.EXPAND)

        fgs1.Add(self.spoofed_apps_label, 0, wx.ALIGN_CENTER_VERTICAL)
        fgs1.Add(self.spoofed_apps, 1, wx.EXPAND)

        fgs1.Add(self.patch_methods_checkbox, 0, wx.EXPAND)
        fgs1.Add(self.recovery_patch_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))
        fgs1.Add(self.keep_temp_files_checkbox, 0, wx.EXPAND)

        if sys.platform.startswith("linux"):
            # only add if we're on linux
            fgs1.Add(file_explorer_label, 0, wx.EXPAND)
            fgs1.Add(file_explorer_sizer, 1, wx.EXPAND)
            fgs1.Add(shell_label, 0, wx.EXPAND)
            fgs1.Add(shell_sizer, 1, wx.EXPAND)

        fgs1.Add(self.use_busybox_shell_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.low_mem_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.extra_img_extracts_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.show_notifications_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.create_boot_tar_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.check_for_update_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.check_for_disk_space_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.check_for_bootloader_unlocked_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.check_for_firmware_hash_validity_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.keep_temporary_support_files_checkbox, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.check_module_updates, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.show_custom_rom_options, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.sanitize_support_files, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.kb_index_cb, 0, wx.EXPAND)
        fgs1.Add((0, 0))

        fgs1.Add(self.force_codepage_checkbox, 0, wx.EXPAND)
        fgs1.Add(self.code_page, 1, wx.EXPAND)

        fgs1.Add(self.delete_bundled_libs_label, 0, wx.EXPAND)
        fgs1.Add(self.delete_bundled_libs, 1, wx.EXPAND)

        fgs1.Add(self.override_kmi_label, 0, wx.EXPAND)
        fgs1.Add(self.override_kmi, 1, wx.EXPAND)

        fgs1.Add(self.use_custom_font_checkbox, 0, wx.EXPAND)
        fgs1.Add(fonts_sizer, 1, wx.EXPAND)

        middle_sizer.Add(fgs1, proportion=1, flag=wx.EXPAND)
        middle_sizer.Add(scrcpy_outer_sizer, proportion=0, flag=wx.EXPAND, border=5)
        scrolled_panel.SetSizer(middle_sizer)
        scrolled_panel.SetScrollRate(10, 10)

        # Bottom Part: OK and Cancel buttons
        bottom_panel = wx.Panel(self)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=5)
        self.ok_button = wx.Button(parent=bottom_panel, id=wx.ID_ANY, label=_("OK"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        bottom_sizer.Add(self.ok_button, proportion=0, flag=wx.ALL, border=20)
        self.cancel_button = wx.Button(parent=bottom_panel, id=wx.ID_ANY, label=_("Cancel"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        bottom_sizer.Add(self.cancel_button, proportion=0, flag=wx.ALL, border=20)
        bottom_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=5)
        bottom_panel.SetSizer(bottom_sizer)

        # Main Sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(top_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(scrolled_panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=20)
        main_sizer.Add(bottom_panel, proportion=0, flag=wx.EXPAND, border=5)

        self.SetSizer(main_sizer)
        self.Center()
        # self.Layout()

        # Disable horizontal resizing
        self.SetMinSize(wx.Size(-1, self.GetSize().y))
        self.SetMaxSize(wx.Size(-1, self.GetSize().y))

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)
        self.font.Bind(wx.EVT_LISTBOX, self._onFontSelect)
        self.font_size.Bind(wx.EVT_SPINCTRL, self._onFontSelect)
        self.reset_magisk_pkg.Bind(wx.EVT_BUTTON, self._onResetMagiskPkg)
        self.patch_methods_checkbox.Bind(wx.EVT_CHECKBOX, self._on_offer_patch_methods)
        self.use_custom_font_checkbox.Bind(wx.EVT_CHECKBOX, self._on_use_custom_fontface)
        self.Bind(wx.EVT_INIT_DIALOG, self.on_init_dialog)
        self.scrcpy_link.Bind(wx.EVT_BUTTON, self._open_scrcpy_link)
        self.Bind(wx.EVT_CLOSE, self._onCancel)
        # self.Bind(wx.EVT_SIZE, self.on_resize)

        # Enable / Disable Widgets
        self.enable_disable_widgets()


    def on_init_dialog(self, event):
        # Autosize the dialog without exceeding 90% of the screen
        screen_width, screen_height = wx.GetDisplaySize()
        debug(f"Screen Size: {screen_width} x {screen_height}")
        screen_max_width = int(screen_width * 0.9)
        screen_max_height = int(screen_height * 0.9)
        self.max_width = min(screen_max_width, 914)
        self.max_height = min(screen_max_height, 1250)
        debug(f"Max Dialog Size: {self.max_width} x {self.max_height}")
        self.SetMaxSize(wx.Size(self.max_width, self.max_height))
        self.SetSizeHints(self.GetMinSize(), self.GetMaxSize())
        self.SetSize((self.max_width, self.max_height))
        self.CenterOnParent()
        event.Skip()


    def on_resize(self, event):
        # Get the current size of the frame
        frame_size = self.GetSize()

        if frame_size.width > self.max_width or frame_size.height > self.max_height:
            # Adjust the size to the maximum allowed size
            new_width = min(frame_size.width, self.max_width)
            new_height = min(frame_size.height, self.max_height)
            self.SetSize((new_width, new_height))
        event.Skip()


    def enable_disable_widgets(self):
        if self.patch_methods_checkbox.GetValue():
            self.recovery_patch_checkbox.Enable()
        else:
            self.recovery_patch_checkbox.Disable()
        if self.use_custom_font_checkbox.GetValue():
            self.font.Enable()
            self.font_size.Enable()
            self.sample.Enable()
        else:
            self.font.Disable()
            self.font_size.Disable()
            self.sample.Disable()


    def _on_offer_patch_methods(self, event):
        self.enable_disable_widgets()


    def _on_use_custom_fontface(self, event):
        self.enable_disable_widgets()


    def _onFontSelect(self, evt):
        facename = self.font.GetStringSelection()
        size = self.font_size.GetValue()
        font = wx.Font(size, family=wx.DEFAULT, style=wx.NORMAL, weight=wx.NORMAL, underline=False, faceName=facename)
        self.sample.SetLabel(facename)
        self.sample.SetFont(font)
        self.Refresh()

    def _open_scrcpy_link(self, event):
        try:
            sys.stdout.write(f"Launching browser for scrcpy download URL: {SCRCPYURL}\n")
            webbrowser.open_new(SCRCPYURL)
            puml(f":Open scrcpy Link;\nnote right\n=== scrcpy\n[[{SCRCPYURL}]]\nend note\n", True)
        except Exception as e:
            sys.stdout.write(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while opening skd link\n")
            traceback.print_exc()

    def _onResetMagiskPkg(self, e):
        self.package_name.SetValue(MAGISK_PKG_NAME)


    def _onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)


    def _onOk(self, e):
        try:
            if self.advanced_options_checkbox.GetValue() != self.Parent.config.advanced_options:
                sys.stdout.write(f"Setting Enable Advanced Options to: {self.advanced_options_checkbox.GetValue()}\n")
            self.Parent.config.advanced_options = self.advanced_options_checkbox.GetValue()

            if self.patch_methods_checkbox.GetValue() != self.Parent.config.offer_patch_methods:
                sys.stdout.write(f"Setting Offer Patch Methods to: {self.patch_methods_checkbox.GetValue()}\n")
            self.Parent.config.offer_patch_methods = self.patch_methods_checkbox.GetValue()

            value = self.spoofed_apps.GetValue()
            if value is None:
                value = ''
            if value != self.Parent.config.spoofed_apps:
                sys.stdout.write(f"Setting Spoofed Apps to: {value}\n")
                self.Parent.config.spoofed_apps = value

            if self.recovery_patch_checkbox.GetValue() != self.Parent.config.show_recovery_patching_option:
                sys.stdout.write(f"Setting Patching Recovery Partition to: {self.recovery_patch_checkbox.GetValue()}\n")
            self.Parent.config.show_recovery_patching_option = self.recovery_patch_checkbox.GetValue()

            if self.keep_temp_files_checkbox.GetValue() != self.Parent.config.keep_patch_temporary_files:
                sys.stdout.write(f"Keep Temp Files to: {self.keep_temp_files_checkbox.GetValue()}\n")
            self.Parent.config.keep_patch_temporary_files = self.keep_temp_files_checkbox.GetValue()

            if self.use_busybox_shell_checkbox.GetValue() != self.Parent.config.use_busybox_shell:
                sys.stdout.write(f"Setting Use Busybox Shell to: {self.use_busybox_shell_checkbox.GetValue()}\n")
            self.Parent.config.use_busybox_shell = self.use_busybox_shell_checkbox.GetValue()

            if self.low_mem_checkbox.GetValue() != self.Parent.config.low_mem:
                sys.stdout.write(f"Setting Low Memory to: {self.low_mem_checkbox.GetValue()}\n")
            self.Parent.config.low_mem = self.low_mem_checkbox.GetValue()
            set_low_memory(self.low_mem_checkbox.GetValue())

            if self.extra_img_extracts_checkbox.GetValue() != self.Parent.config.extra_img_extracts:
                sys.stdout.write(f"Setting Extra img extraction to: {self.extra_img_extracts_checkbox.GetValue()}\n")
            self.Parent.config.extra_img_extracts = self.extra_img_extracts_checkbox.GetValue()

            if self.show_notifications_checkbox.GetValue() != self.Parent.config.show_notifications:
                sys.stdout.write(f"Setting Show notifications to: {self.show_notifications_checkbox.GetValue()}\n")
            self.Parent.config.show_notifications = self.show_notifications_checkbox.GetValue()

            if self.create_boot_tar_checkbox.GetValue() != self.Parent.config.create_boot_tar:
                sys.stdout.write(f"Setting Always create boot.tar: {self.create_boot_tar_checkbox.GetValue()}\n")
            self.Parent.config.create_boot_tar = self.create_boot_tar_checkbox.GetValue()

            if self.check_for_update_checkbox.GetValue() != self.Parent.config.update_check:
                sys.stdout.write(f"Setting Check for updates to: {self.check_for_update_checkbox.GetValue()}\n")
            self.Parent.config.update_check = self.check_for_update_checkbox.GetValue()

            if self.check_for_disk_space_checkbox.GetValue() != self.Parent.config.check_for_disk_space:
                sys.stdout.write(f"Setting Check for Minimum Disk Space to: {self.check_for_disk_space_checkbox.GetValue()}\n")
            self.Parent.config.check_for_disk_space = self.check_for_disk_space_checkbox.GetValue()

            if self.check_for_bootloader_unlocked_checkbox.GetValue() != self.Parent.config.check_for_bootloader_unlocked:
                sys.stdout.write(f"Setting Check for Minimum Disk Space to: {self.check_for_bootloader_unlocked_checkbox.GetValue()}\n")
            self.Parent.config.check_for_bootloader_unlocked = self.check_for_bootloader_unlocked_checkbox.GetValue()

            if self.check_for_firmware_hash_validity_checkbox.GetValue() != self.Parent.config.check_for_firmware_hash_validity:
                sys.stdout.write(f"Setting Check for Firmware Hash Validity to: {self.check_for_firmware_hash_validity_checkbox.GetValue()}\n")
            self.Parent.config.check_for_firmware_hash_validity = self.check_for_firmware_hash_validity_checkbox.GetValue()

            if self.keep_temporary_support_files_checkbox.GetValue() != self.Parent.config.keep_temporary_support_files:
                sys.stdout.write(f"Setting Keep temporary support files to: {self.keep_temporary_support_files_checkbox.GetValue()}\n")
            self.Parent.config.keep_temporary_support_files = self.keep_temporary_support_files_checkbox.GetValue()

            if self.check_module_updates.GetValue() != self.Parent.config.check_module_updates:
                sys.stdout.write(f"Setting Check Magisk modules for updates to: {self.check_module_updates.GetValue()}\n")
            self.Parent.config.check_module_updates = self.check_module_updates.GetValue()

            if self.show_custom_rom_options.GetValue() != self.Parent.config.show_custom_rom_options:
                sys.stdout.write(f"Setting Show custom ROM options to: {self.show_custom_rom_options.GetValue()}\n")
            self.Parent.config.show_custom_rom_options = self.show_custom_rom_options.GetValue()

            if self.sanitize_support_files.GetValue() != self.Parent.config.sanitize_support_files:
                sys.stdout.write(f"Setting Sanitize Support Files options to: {self.sanitize_support_files.GetValue()}\n")
            self.Parent.config.sanitize_support_files = self.sanitize_support_files.GetValue()

            if self.kb_index_cb.GetValue() != self.Parent.config.kb_index:
                sys.stdout.write(f"Setting Keybox Indexing options to: {self.kb_index_cb.GetValue()}\n")
            self.Parent.config.kb_index = self.kb_index_cb.GetValue()

            if self.package_name.GetValue():
                with contextlib.suppress(Exception):
                    if self.package_name.GetValue() != self.Parent.config.magisk:
                        sys.stdout.write(f"Setting Magisk Package Name to: {self.package_name.GetValue()}\n")
                        set_magisk_package(self.package_name.GetValue())
                        self.Parent.config.magisk = self.package_name.GetValue()

            if sys.platform.startswith("linux"):
                with contextlib.suppress(Exception):
                    if self.file_explorer.GetValue() != self.Parent.config.linux_file_explorer:
                        sys.stdout.write(f"Setting Linux File Explorer to: {self.file_explorer.GetValue()}\n")
                    self.Parent.config.linux_file_explorer = self.file_explorer.GetValue()

                with contextlib.suppress(Exception):
                    if self.shell.GetValue() != self.Parent.config.linux_shell:
                        sys.stdout.write(f"Setting Linux Shell to: {self.shell.GetValue()}\n")
                    set_linux_shell(self.shell.GetValue())
                    self.Parent.config.linux_shell = self.shell.GetValue()

            self.Parent.config.force_codepage = self.force_codepage_checkbox.GetValue()
            if self.code_page.GetValue() and self.code_page.GetValue().isnumeric():
                self.Parent.config.custom_codepage = int(self.code_page.GetValue())

            value = self.delete_bundled_libs.GetValue()
            if value is None:
                value = ''
            if value != self.Parent.config.delete_bundled_libs:
                sys.stdout.write(f"Setting Delete bundled libs to: {value}\n")
                self.Parent.config.delete_bundled_libs = value

            value = self.override_kmi.GetValue()
            if value is None:
                value = ''
            if value != self.Parent.config.override_kmi:
                sys.stdout.write(f"Setting Kernel KMI to: {value}\n")
                self.Parent.config.override_kmi = value

            font_settings_changed = False
            if self.use_custom_font_checkbox.GetValue() != self.Parent.config.customize_font:
                sys.stdout.write("Enabling Custom Font\n")
                font_settings_changed = True
            if self.font.GetStringSelection() != self.Parent.config.pf_font_face:
                sys.stdout.write(f"Setting Application Font to: {self.font.GetStringSelection()}\n")
                if self.use_custom_font_checkbox.GetValue():
                    font_settings_changed = True
            if self.font_size.GetValue() != self.Parent.config.pf_font_size:
                sys.stdout.write(f"Setting Application Font Size to: {self.font_size.GetValue()}\n")
                if self.use_custom_font_checkbox.GetValue():
                    font_settings_changed = True
            self.Parent.config.customize_font = self.use_custom_font_checkbox.GetValue()
            self.Parent.config.pf_font_face = self.font.GetStringSelection()
            self.Parent.config.pf_font_size = self.font_size.GetValue()

            value = self.scrcpy_path_picker.GetPath()
            if value is None:
                value = ''
            if value != self.Parent.config.scrcpy['path'] and os.path.exists(value):
                sys.stdout.write(f"Setting scrcpy path path to: {value}\n")
                self.Parent.config.scrcpy['path'] = value

            value = self.scrcpy_flags.GetValue()
            if value is None:
                value = ''
            if value != self.Parent.config.scrcpy['flags']:
                sys.stdout.write(f"Setting scrcpy flags to: {value}\n")
                self.Parent.config.scrcpy['flags'] = value

            # update the runtime config
            set_config(self.Parent.config)

            if font_settings_changed:
                self.Parent.set_ui_fonts()
        finally:
            self.EndModal(wx.ID_OK)
