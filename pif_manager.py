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
import wx.stc as stc
import traceback
import images as images
import json
import json5
import re
from datetime import datetime
from runtime import *
from file_editor import FileEditor
from i18n import _
from package_manager import PackageManager
from factory_image_selector import show_factory_image_dialog
from message_box_ex import MessageBoxEx

# ============================================================================
#                               Class PifModule
# ============================================================================
class PifModule:
    def __init__(self, id, name, version, version_code, format, path, flavor):
        self.id = id
        self.name = name
        self.version = version
        self.version_code = version_code
        self.format = format
        self.path = path
        self.flavor = flavor

# ============================================================================
#                               Class PifManager
# ============================================================================
class PifManager(wx.Dialog):
    def __init__(self, *args, parent=None, config=None, **kwargs):
        self.config = config
        wx.Dialog.__init__(self, parent, *args, **kwargs, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        # Position the dialog 200 px offset horizontally
        default_pos = self.GetPosition()
        offset_x = default_pos.x + 200
        self.SetPosition((offset_x, default_pos.y))

        self.config = config
        self.SetTitle(_("Pif Manager"))
        self.pif_path = None
        self.device_pif = ''
        self.pi_app = 'gr.nikolasspyr.integritycheck'
        # self.launch_method = 'launch-am'
        self.launch_method = 'launch'
        self.coords = Coords()
        self.enable_buttons = False
        self.pif_exists = False
        self.pif_flavor = 'playintegrityfork_9999999'
        self.favorite_pifs = get_favorite_pifs()
        self.insync = False
        self.pif_format = None
        self.keep_unknown = False
        self.current_pif_module = {}
        self._last_call_was_on_spin = False
        self.beta_pif_version = 'latest'
        self._tf_targets_loaded = False
        self._validation_timer = None  # Timer for debounced validation

        # Active pif label
        self.active_pif_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_("Active Pif"))
        self.active_pif_label.SetToolTip(_("Loaded Pif (from Device)"))
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.active_pif_label.SetFont(font)
        # Modified status
        self.pif_modified_image = wx.StaticBitmap(parent=self)
        self.pif_modified_image.SetBitmap(images.alert_gray_24.GetBitmap())
        self.pif_modified_image.SetToolTip(_("Active pif is not modified."))
        # Save pif
        self.save_pif_button = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.save_pif_button.SetBitmap(images.save_24.GetBitmap())
        self.save_pif_button.SetToolTip(_("Save Active pif content to a json file on disk."))
        # Module version label
        self.pif_selection_combo = wx.ComboBox(self, choices=[], style=wx.CB_READONLY)
        self.pif_selection_combo.SetToolTip(_("Pif Module"))
        # TF Targets
        self.tf_targets_combo = wx.ComboBox(self, choices=[_("TF Targets")], style=wx.CB_READONLY)
        self.tf_targets_combo.SetToolTip(_("TargetedFix Targets"))
        self.tf_targets_combo.SetSelection(0)
        self.tf_targets_combo.SetForegroundColour(wx.Colour(128, 128, 128))  # Gray placeholder text
        self.tf_targets_combo.SetMinSize((130, -1))
        self.tf_targets_combo.Enable(False)
        # Favorite button
        self.favorite_pif_button = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.favorite_pif_button.SetBitmap(images.heart_gray_24.GetBitmap())
        self.favorite_pif_button.SetToolTip(_("Active pif is not saved in favorites."))
        # Combo Box of favorites
        pif_labels = [pif["label"] for pif in self.favorite_pifs.values()]
        self.pif_combo_box = wx.ComboBox(self, choices=pif_labels, style=wx.CB_READONLY)
        # Import button
        self.import_pif_button = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.import_pif_button.SetBitmap(images.import_24.GetBitmap())
        self.import_pif_button.SetToolTip(_("Select a folder to import pif json files."))

        # Active Pif
        self.active_pif_stc = stc.StyledTextCtrl(self)
        self.setup_syntax_highlighting(self.active_pif_stc)
        self.active_pif_stc.SetCaretForeground(wx.BLACK)
        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.active_pif_stc.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.active_pif_stc.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.active_pif_stc.SetUseHorizontalScrollBar(True)
        self.active_pif_stc.SetTabWidth(4)
        self.active_pif_stc.SetIndent(4)
        self.active_pif_stc.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.active_pif_stc.SetMarginWidth(1, 30)

        # TargetedFix button row (initially hidden)
        self.tf_add_target_button = wx.Button(self, wx.ID_ANY, _("Add TF Target"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.tf_add_target_button.SetToolTip(_("Add a new TargetedFix target by selecting from package list on device"))

        self.tf_delete_target_button = wx.Button(self, wx.ID_ANY, _("Delete TF Target"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.tf_delete_target_button.SetToolTip(_("Delete the selected TargetedFix target"))
        self.tf_delete_target_button.Enable(False)

        self.tf_edit_targets_button = wx.Button(self, wx.ID_ANY, _("Edit TF Targets"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.tf_edit_targets_button.SetToolTip(_("Edit TargetedFix targets file"))
        # self.tf_edit_targets_button.Enable(False)

        self.tf_push_json_button = wx.Button(self, wx.ID_ANY, _("Push TF Json"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.tf_push_json_button.SetToolTip(_("Push Active pif content as JSON to the selected TargetedFix target"))
        self.tf_push_json_button.Enable(False)

        # TargetedFix button row sizer (initially hidden)
        self.tf_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tf_buttons_sizer.Add(self.tf_add_target_button, 0, wx.ALL, 5)
        self.tf_buttons_sizer.Add(self.tf_delete_target_button, 0, wx.ALL, 5)
        self.tf_buttons_sizer.Add(self.tf_edit_targets_button, 0, wx.ALL, 5)
        self.tf_buttons_sizer.Add(self.tf_push_json_button, 0, wx.ALL, 5)
        self.tf_buttons_sizer.AddStretchSpacer()

        # Hide the TargetedFix buttons initially
        self.tf_add_target_button.Show(False)
        self.tf_delete_target_button.Show(False)
        self.tf_edit_targets_button.Show(False)
        self.tf_push_json_button.Show(False)

        # Console label
        self.console_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_("Output"))
        self.console_label.SetToolTip(_("Console Output:\nIt could be the json output of processed prop\nor it could be the Play Integrity Check result.\n\nThis is not what currently is on the device."))
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.console_label.SetFont(font)
        # Smart Paste Up
        self.smart_paste_up = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.smart_paste_up.SetBitmap(images.smart_paste_up_24.GetBitmap())
        self.smart_paste_up.SetToolTip(_("Smart Paste:\nSets First API to the set value if it is missing or forced.\nReprocesses the output window content to adapt to current module requirements.\nPastes to Active pif."))
        self.smart_paste_up.Enable(False)
        # Paste Up
        self.paste_up = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.paste_up.SetBitmap(images.paste_up_24.GetBitmap())
        self.paste_up.SetToolTip(_("Paste the console window content to Active pif."))
        self.paste_up.Enable(False)
        # Paste Down
        self.paste_down = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.paste_down.SetBitmap(images.paste_down_24.GetBitmap())
        self.paste_down.SetToolTip(_("Paste the Active pif to console window."))
        self.paste_down.Enable(False)
        # Reprocess
        self.reprocess = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.reprocess.SetBitmap(images.scan_24.GetBitmap())
        self.reprocess.SetToolTip(_("Reprocess current Active Pif window json.\nUseful if you changed module version which might require additional / different fields."))
        self.reprocess.Enable(False)
        # Reprocess Json File(s)
        self.reprocess_json_file = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.reprocess_json_file.SetBitmap(images.json_24.GetBitmap())
        self.reprocess_json_file.SetToolTip(_("Reprocess one or many json file(s)\nUseful if you changed module version which might require additional / different fields.\nIf a single file is selected, the new json will output to console output\nHowever if multiple files are selected, the selected file will be updated in place."))
        # Env to Json
        self.e2j = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.e2j.SetBitmap(images.e2j_24.GetBitmap())
        self.e2j.SetToolTip(_("Convert console content from env (key=value) prop format to json"))
        # Json to Env
        self.j2e = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.j2e.SetBitmap(images.j2e_24.GetBitmap())
        self.j2e.SetToolTip(_("Convert console content from json to env (key=value) prop format"))
        # Get FP Code
        self.get_fp_code = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.get_fp_code.SetBitmap(images.java_24.GetBitmap())
        self.get_fp_code.SetToolTip(_("Process one or many json file(s) to generate the FrameworkPatcher formatted code excerpts.\n"))
        # Add missing keys checkbox
        self.add_missing_keys_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Add missing Keys from device"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.add_missing_keys_checkbox.SetToolTip(_("When Processing or Reprocessing, add missing fields from device."))
        # Force First API
        self.force_first_api_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Force First API to:"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.force_first_api_checkbox.SetToolTip(_("Forces First API value(s) to"))
        # Input box for the API value
        self.api_value_input = wx.TextCtrl(parent=self, id=wx.ID_ANY, value="25", size=(40, -1))
        # sort_keys
        self.sort_keys_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Sort Keys"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.sort_keys_checkbox.SetToolTip(_("Sorts json keys"))
        # keep_unknown
        self.keep_unknown_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Keep All keys"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.keep_unknown_checkbox.SetToolTip(_("Does not remove non standard / unrecognized keys"))
        # add advanced options checkboxes
        self.spoofBuild_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Build"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spoofBuild_checkbox.SetValue(True)
        self.spoofProps_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Props"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spoofProvider_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Provider"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spoofSignature_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Signature"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spoofVendingSdk_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Vending SDK"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.spoofVendingFinger_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Spoof Vending Fingerprint"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)

        # Console
        self.console_stc = stc.StyledTextCtrl(self)
        self.setup_syntax_highlighting(self.console_stc)
        self.console_stc.SetCaretForeground(wx.BLACK)
        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.console_stc.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.console_stc.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.console_stc.SetUseHorizontalScrollBar(True)
        self.console_stc.SetTabWidth(4)
        self.console_stc.SetIndent(4)
        self.console_stc.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.console_stc.SetMarginWidth(1, 30)

        # Close button
        self.close_button = wx.Button(self, wx.ID_ANY, _("Close"), wx.DefaultPosition, wx.DefaultSize, 0)

        # Create print button
        self.create_pif_button = wx.Button(self, wx.ID_ANY, _("Create print"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.create_pif_button.SetToolTip(_("Create pif.json / spoof_build_vars"))
        self.create_pif_button.Enable(False)

        # Push print no validation button
        self.push_pif_button = wx.Button(self, wx.ID_ANY, _("Push print, no validation"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.push_pif_button.SetToolTip(_("Pushes the print as is without performing any validation.\nThis is useful to retain comments."))
        self.push_pif_button.Enable(False)

        # Reload print button
        self.reload_pif_button = wx.Button(self, wx.ID_ANY, _("Reload print"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.reload_pif_button.SetToolTip(_("Reload pif.json / spoof_build_vars from device."))
        self.reload_pif_button.Enable(False)

        # Clean DG button
        self.cleanup_dg_button = wx.Button(self, wx.ID_ANY, _("Cleanup DG"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.cleanup_dg_button.SetToolTip(_("Cleanup Droidguard Cache"))
        self.cleanup_dg_button.Enable(False)

        # Push keybox button
        self.push_kb_button = wx.Button(self, wx.ID_ANY, _("Push keybox.xml"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.push_kb_button.SetToolTip(_("Push a valid keybox.xml to device."))
        self.push_kb_button.Enable(False)
        self.push_kb_button.Show(False)

        # Edit Tricky Store target.txt button
        self.edit_ts_target_button = wx.Button(self, wx.ID_ANY, _("Edit TS Target"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.edit_ts_target_button.SetToolTip(_("Edit Tricky Store target.txt file."))
        self.edit_ts_target_button.Enable(False)
        self.edit_ts_target_button.Show(False)

        # Edit Tricky Store security_patch.txt button
        self.edit_security_patch_button = wx.Button(self, wx.ID_ANY, _("Edit TS SP"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.edit_security_patch_button.SetToolTip(_("Edit Tricky Store security_patch.txt file."))
        self.edit_security_patch_button.Enable(False)
        self.edit_security_patch_button.Show(False)

        # Process build.prop button
        self.process_build_prop_button = wx.Button(self, wx.ID_ANY, _("Process build.prop(s)"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.process_build_prop_button.SetToolTip(_("Process build.prop to extract a compatible print."))

        # Process bulk prop
        self.process_bulk_prop_button = wx.Button(self, wx.ID_ANY, _("Process bulk props"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.process_bulk_prop_button.SetToolTip(_("Process a folder containing .prop files and convert then to .json files."))
        self.process_bulk_prop_button.Hide()

        # Process Image
        self.process_img_button = wx.Button(self, wx.ID_ANY, _("Process Image"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.process_img_button.SetToolTip(_("Process an image and get a print from it."))
        self.process_img_button.Hide()
        # if self.config.enable_pixel_img_process:
        self.process_img_button.Show()

        # Check for Auto Push print
        self.auto_update_pif_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Auto Update print"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.auto_update_pif_checkbox.SetToolTip(_("After Processing build.props, the print is automatically pushed to the device and the GMS process is killed."))
        self.auto_update_pif_checkbox.Enable(False)

        # Check for Auto Check Play Integrity
        self.auto_check_pi_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Auto Check Play Integrity"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.auto_check_pi_checkbox.SetToolTip(_("After saving (pushing) print, automatically run Play Integrity Check."))
        self.auto_check_pi_checkbox.Enable(False)

        # Auto Run migrate script
        self.auto_run_migrate_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Auto run migrate.sh"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.auto_run_migrate_checkbox.SetToolTip(_("After saving (pushing) print, automatically run migrate.sh"))
        self.auto_run_migrate_checkbox.Enable(False)

        # option button PI Selection
        self.pi_choices = ["Play Integrity API Checker", "Simple Play Integrity Checker", "Android Integrity Checker", "Play Store"]
        self.pi_option = wx.RadioBox(self, choices=self.pi_choices, style=wx.RA_VERTICAL)

        # Disable UIAutomator
        self.disable_uiautomator_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_("Disable UIAutomator"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.disable_uiautomator_checkbox.SetToolTip(_("Disables UIAutomator\nThis is useful for devices with buggy UIAutomator.\nNOTE: Create the coords.json file manually to make use of automated testing."))

        # Play Integrity API Checker button
        self.pi_checker_button = wx.Button(self, wx.ID_ANY, _("Play Integrity Check"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.pi_checker_button.SetToolTip(_("Play Integrity API Checker\nNote: Need to install app from Play store."))

        # Beta Pif version selection
        self.rb_latest = wx.RadioButton(self, wx.ID_ANY, _("Latest"), style=wx.RB_GROUP)
        self.rb_custom = wx.RadioButton(self, wx.ID_ANY, _("Custom"))
        self.rb_custom.SetToolTip(_("Select 'Latest' to get the latest Pixel beta pif (Includes Developer Preview).\nSelect 'Custom' to set a custom Android version code."))
        self.rb_latest.SetValue(True)

        # Custom version input
        self.custom_version = wx.TextCtrl(self, wx.ID_ANY, "15", size=(75, -1))
        self.custom_version.SetToolTip(_("Set a valid Android version code."))
        # self.custom_version.SetToolTip(_("Set a valid two digit Android version code,\nor 'C' for Canary,\nor 'CANARY_rxx' for Canary release.\nExample: 15, 16, 17, C, CANARY_r01\nNote: The custom version is only used when 'Custom' is selected."))
        self.custom_version.Enable(False)

        # Get Beta Pif button
        self.beta_pif_button = wx.Button(self, wx.ID_ANY, _("Get Pixel Beta Pif"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.beta_pif_button.SetToolTip(_("Get the latest Pixel beta pif."))

        # Get the Canary miner button
        self.canary_pif_button = wx.Button(self, wx.ID_ANY, _("Get the Canary miner"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.canary_pif_button.SetToolTip(_("Get the latest Vagelis1608 Canary pif."))

        # Get TheFreeman193 Pif button
        self.freeman_pif_button = wx.Button(self, wx.ID_ANY, _("Get TheFreeman193 Random Pif"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.freeman_pif_button.SetToolTip(_("Get a random pif from TheFreeman193 repository.\nNote: The pif might or might not work."))

        # Make the buttons the same size
        button_width = self.pi_option.GetSize()[0] + 10
        self.create_pif_button.SetMinSize((button_width, -1))
        self.push_pif_button.SetMinSize((button_width, -1))
        self.reload_pif_button.SetMinSize((button_width, -1))
        self.cleanup_dg_button.SetMinSize((button_width, -1))
        self.push_kb_button.SetMinSize((button_width, -1))
        self.edit_ts_target_button.SetMinSize((button_width, -1))
        self.edit_security_patch_button.SetMinSize((button_width, -1))
        self.process_build_prop_button.SetMinSize((button_width, -1))
        self.process_bulk_prop_button.SetMinSize((button_width, -1))
        self.process_img_button.SetMinSize((button_width, -1))
        self.auto_update_pif_checkbox.SetMinSize((button_width, -1))
        self.auto_check_pi_checkbox.SetMinSize((button_width, -1))
        self.auto_run_migrate_checkbox.SetMinSize((button_width, -1))
        self.disable_uiautomator_checkbox.SetMinSize((button_width, -1))
        self.pi_checker_button.SetMinSize((button_width, -1))
        self.canary_pif_button.SetMinSize((button_width, -1))
        self.freeman_pif_button.SetMinSize((button_width, -1))
        self.beta_pif_button.SetMinSize((button_width, -1))

        h_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        h_buttons_sizer.Add(self.close_button, 0, wx.ALL, 5)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 5)

        # h_api_sizer
        h_api_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_api_sizer.Add(self.force_first_api_checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
        h_api_sizer.Add(self.api_value_input, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.beta_pif_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.beta_pif_hsizer.Add(self.rb_latest, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.beta_pif_hsizer.Add(self.rb_custom, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.beta_pif_hsizer.Add(self.custom_version, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        v_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        v_buttons_sizer.Add(self.create_pif_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.push_pif_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.reload_pif_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)
        v_buttons_sizer.Add(self.cleanup_dg_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)
        v_buttons_sizer.Add(self.push_kb_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)
        v_buttons_sizer.Add(self.edit_ts_target_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)
        v_buttons_sizer.Add(self.edit_security_patch_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 5)
        v_buttons_sizer.AddStretchSpacer()
        v_buttons_sizer.Add(self.process_build_prop_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.process_bulk_prop_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.process_img_button, 0, wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.auto_update_pif_checkbox, 0, wx.ALL, 5)
        v_buttons_sizer.Add(self.auto_check_pi_checkbox, 0, wx.ALL, 5)
        v_buttons_sizer.Add(self.auto_run_migrate_checkbox, 0, wx.ALL, 5)
        v_buttons_sizer.Add(self.pi_option, 0, wx.TOP, 5)
        v_buttons_sizer.Add(self.disable_uiautomator_checkbox, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.pi_checker_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.beta_pif_hsizer, 0, wx.EXPAND | wx.TOP | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.beta_pif_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.canary_pif_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)
        v_buttons_sizer.Add(self.freeman_pif_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 5)

        self.vertical_btn_sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.vertical_btn_sizer1.Add(self.paste_up, 0, wx.ALL, 0)
        self.vertical_btn_sizer1.AddStretchSpacer()
        self.vertical_btn_sizer1.Add(self.paste_down, 0, wx.ALL, 0)

        self.vertical_btn_sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.vertical_btn_sizer2.Add(self.reprocess_json_file, 1, wx.ALL, 0)
        self.vertical_btn_sizer2.Add(self.e2j, 1, wx.ALL, 0)
        self.vertical_btn_sizer2.Add(self.j2e, 1, wx.ALL, 0)
        self.vertical_btn_sizer2.Add(self.get_fp_code, 1, wx.ALL, 0)

        self.vertical_cb_sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.vertical_cb_sizer1.Add(self.add_missing_keys_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer1.Add(h_api_sizer, 1, wx.ALL, 0)
        self.vertical_cb_sizer1.Add(self.sort_keys_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer1.Add(self.keep_unknown_checkbox, 1, wx.ALL, 0)

        self.vertical_cb_sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.vertical_cb_sizer2.Add(self.spoofBuild_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer2.Add(self.spoofProps_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer2.Add(self.spoofProvider_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer2.Add(self.spoofSignature_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer2.Add(self.spoofVendingSdk_checkbox, 1, wx.ALL, 0)
        self.vertical_cb_sizer2.Add(self.spoofVendingFinger_checkbox, 1, wx.ALL, 0)

        console_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.console_label, 0, wx.ALIGN_BOTTOM)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.smart_paste_up, 0, wx.ALIGN_TOP)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.reprocess, 0, wx.ALIGN_TOP)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.vertical_btn_sizer1, 1, wx.EXPAND)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.vertical_btn_sizer2, 0, wx.EXPAND)
        console_label_sizer.AddSpacer(15)
        console_label_sizer.Add(self.vertical_cb_sizer1, 0, wx.EXPAND)
        console_label_sizer.AddSpacer(15)
        console_label_sizer.Add(self.vertical_cb_sizer2, 0, wx.EXPAND)

        stc_sizer = wx.BoxSizer(wx.VERTICAL)
        stc_sizer.Add(self.active_pif_stc, 1, wx.EXPAND | wx.ALL, 10)
        stc_sizer.Add(self.tf_buttons_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        stc_sizer.Add(console_label_sizer, 0, wx.TOP, 10)
        stc_sizer.Add(self.console_stc, 1, wx.EXPAND | wx.ALL, 10)

        outside_stc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outside_stc_sizer.Add(stc_sizer, 1, wx.EXPAND | wx.ALL, 0)
        outside_stc_sizer.Add(v_buttons_sizer, 0, wx.EXPAND | wx.ALL, 0)

        active_pif_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.active_pif_label, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.pif_modified_image, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.save_pif_button, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(50)
        active_pif_label_sizer.Add(self.pif_selection_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.tf_targets_combo, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        active_pif_label_sizer.AddSpacer(50)
        active_pif_label_sizer.Add(self.favorite_pif_button, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.pif_combo_box, 1, wx.EXPAND)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.import_pif_button, 0, wx.ALIGN_CENTER_VERTICAL)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(active_pif_label_sizer, 0, wx.TOP, 10)
        vSizer.Add(outside_stc_sizer, 1, wx.EXPAND, 0)
        vSizer.Add(h_buttons_sizer, 0, wx.EXPAND, 10)

        self.SetSizer(vSizer)
        min_width = 800
        min_height = 500
        self.SetMinSize((min_width, min_height))
        self.Layout()

        # Connect Events
        self.save_pif_button.Bind(wx.EVT_BUTTON, self.onSavePif)
        self.pif_selection_combo.Bind(wx.EVT_COMBOBOX, self.onPifSelectionComboBox)
        self.tf_targets_combo.Bind(wx.EVT_COMBOBOX, self.onTFTargetSelectionComboBox)
        self.favorite_pif_button.Bind(wx.EVT_BUTTON, self.onSaveToFavorites)
        self.pif_combo_box.Bind(wx.EVT_COMBOBOX, self.onFavoritesComboBox)
        self.import_pif_button.Bind(wx.EVT_BUTTON, self.onImportFavorites)
        #
        self.active_pif_stc.Bind(wx.stc.EVT_STC_CHANGE, self.ActivePifStcChange)
        self.console_stc.Bind(wx.stc.EVT_STC_CHANGE, self.ConsoleStcChange)
        #
        self.create_pif_button.Bind(wx.EVT_BUTTON, self.onUpdatePrint)
        self.push_pif_button.Bind(wx.EVT_BUTTON, self.onPushPrint)
        self.reload_pif_button.Bind(wx.EVT_BUTTON, self.onReloadPrint)
        self.cleanup_dg_button.Bind(wx.EVT_BUTTON, self.onCleanupDG)
        self.push_kb_button.Bind(wx.EVT_BUTTON, self.onPushKeybox)
        self.edit_ts_target_button.Bind(wx.EVT_BUTTON, self.onEditTSTarget)
        self.edit_security_patch_button.Bind(wx.EVT_BUTTON, self.onEditTSSP)
        #
        self.process_build_prop_button.Bind(wx.EVT_BUTTON, self.onProcessBuildProps)
        self.process_bulk_prop_button.Bind(wx.EVT_BUTTON, self.onProcessBulkProps)
        self.process_img_button.Bind(wx.EVT_BUTTON, self.onProcessImage)
        self.auto_update_pif_checkbox.Bind(wx.EVT_CHECKBOX, self.onAutoUpdatePrint)
        self.auto_check_pi_checkbox.Bind(wx.EVT_CHECKBOX, self.onAutoCheckPlayIntegrity)
        self.auto_run_migrate_checkbox.Bind(wx.EVT_CHECKBOX, self.onAutoRunMigrate)
        #
        self.pi_option.Bind(wx.EVT_RADIOBOX, self.onTestPIAppOptionSelect)
        #
        self.disable_uiautomator_checkbox.Bind(wx.EVT_CHECKBOX, self.onDisableUIAutomator)
        self.pi_checker_button.Bind(wx.EVT_BUTTON, self.onPlayIntegrityCheck)
        #
        self.rb_latest.Bind(wx.EVT_RADIOBUTTON, self.onBetaRadioSelect)
        self.rb_custom.Bind(wx.EVT_RADIOBUTTON, self.onBetaRadioSelect)
        self.custom_version.Bind(wx.EVT_TEXT, self.onBetaVersionChange)
        self.beta_pif_button.Bind(wx.EVT_BUTTON, self.onGetPixelBetaPif)
        self.canary_pif_button.Bind(wx.EVT_BUTTON, self.onGetCanaryPif)
        self.freeman_pif_button.Bind(wx.EVT_BUTTON, self.onGetFreemanPif)
        #
        self.smart_paste_up.Bind(wx.EVT_BUTTON, self.onSmartPasteUp)
        self.reprocess.Bind(wx.EVT_BUTTON, self.onReProcess)
        self.paste_up.Bind(wx.EVT_BUTTON, self.onPasteUp)
        self.paste_down.Bind(wx.EVT_BUTTON, self.onPasteDown)
        self.reprocess_json_file.Bind(wx.EVT_BUTTON, self.onReProcessJsonFiles)
        self.j2e.Bind(wx.EVT_BUTTON, self.onJ2E)
        self.e2j.Bind(wx.EVT_BUTTON, self.onE2J)
        self.get_fp_code.Bind(wx.EVT_BUTTON, self.onGetFrameworkPatcherCode)
        #
        self.add_missing_keys_checkbox.Bind(wx.EVT_CHECKBOX, self.onAddMissingKeysFromDevice)
        self.force_first_api_checkbox.Bind(wx.EVT_CHECKBOX, self.onForceFirstAPI)
        self.api_value_input.Bind(wx.EVT_TEXT, self.onApiValueChange)
        self.sort_keys_checkbox.Bind(wx.EVT_CHECKBOX, self.onSortKeys)
        self.keep_unknown_checkbox.Bind(wx.EVT_CHECKBOX, self.onKeepAllKeys)
        #
        self.spoofBuild_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofBuild)
        self.spoofProps_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofProps)
        self.spoofProvider_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofProvider)
        self.spoofSignature_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofSignature)
        self.spoofVendingSdk_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofVendingSdk)
        self.spoofVendingFinger_checkbox.Bind(wx.EVT_CHECKBOX, self.onSpoofVendingFinger)
        #
        self.tf_add_target_button.Bind(wx.EVT_BUTTON, self.onAddTFTarget)
        self.tf_delete_target_button.Bind(wx.EVT_BUTTON, self.onDeleteTFTarget)
        self.tf_edit_targets_button.Bind(wx.EVT_BUTTON, self.onEditTFTargets)
        self.tf_push_json_button.Bind(wx.EVT_BUTTON, self.onPushTFProp)
        #
        self.close_button.Bind(wx.EVT_BUTTON, self.onClose)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_SHOW, self.onShow)

        # init button states
        self.init()

        # Autosize the dialog
        self.active_pif_stc.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)

        print("\nOpening Pif Manager ...")

    # -----------------------------------------------
    #              setup_syntax_highlighting
    # -----------------------------------------------
    def setup_syntax_highlighting(self, stc_ctrl, format_type=None):
        if format_type is None:
            format_type = getattr(self, 'pif_format', 'json')

        # Set font for all styles
        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        bold_font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        italic_font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)

        if format_type == 'prop':
            # Properties format (key=value with comments)
            stc_ctrl.SetLexer(stc.STC_LEX_PROPERTIES)

            # Set up properties syntax highlighting with proper fonts
            stc_ctrl.StyleSetSpec(stc.STC_PROPS_DEFAULT, "fore:#7F007F")  # Default/values (purple)
            stc_ctrl.StyleSetFont(stc.STC_PROPS_DEFAULT, font)

            # stc_ctrl.StyleSetSpec(stc.STC_PROPS_COMMENT, "fore:#008000")  # Comments (green)
            stc_ctrl.StyleSetSpec(stc.STC_PROPS_COMMENT, "fore:#808080")  # Comments (gray)
            stc_ctrl.StyleSetFont(stc.STC_PROPS_COMMENT, italic_font)

            stc_ctrl.StyleSetSpec(stc.STC_PROPS_SECTION, "fore:#0000FF")  # Section headers
            stc_ctrl.StyleSetFont(stc.STC_PROPS_SECTION, bold_font)

            stc_ctrl.StyleSetSpec(stc.STC_PROPS_ASSIGNMENT, "fore:#FF0000")  # = sign (red, bold)
            stc_ctrl.StyleSetFont(stc.STC_PROPS_ASSIGNMENT, bold_font)

            stc_ctrl.StyleSetSpec(stc.STC_PROPS_DEFVAL, "fore:#7F007F")  # Values (purple)
            stc_ctrl.StyleSetFont(stc.STC_PROPS_DEFVAL, font)

            # stc_ctrl.StyleSetSpec(stc.STC_PROPS_KEY, "fore:#000080")  # Keys (dark blue, bold)
            # stc_ctrl.StyleSetFont(stc.STC_PROPS_KEY, bold_font)
            stc_ctrl.StyleSetSpec(stc.STC_PROPS_KEY, "fore:#007F00")  # Keys (green)
            stc_ctrl.StyleSetFont(stc.STC_PROPS_KEY, font)

        else:
            # JSON format
            stc_ctrl.SetLexer(stc.STC_LEX_JSON)
            stc_ctrl.StyleSetSpec(stc.STC_JSON_DEFAULT, "fore:#000000")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_NUMBER, "fore:#007F7F")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_STRING, "fore:#7F007F")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_PROPERTYNAME, "fore:#007F00")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_ESCAPESEQUENCE, "fore:#7F7F00")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_KEYWORD, "fore:#00007F,bold")
            stc_ctrl.StyleSetSpec(stc.STC_JSON_OPERATOR, "fore:#7F0000")

    # -----------------------------------------------
    #              update_syntax_highlighting
    # -----------------------------------------------
    def update_syntax_highlighting(self):
        if hasattr(self, 'active_pif_stc') and hasattr(self, 'pif_format'):
            self.setup_syntax_highlighting(self.active_pif_stc, self.pif_format)
            # Force refresh of highlighting
            self.active_pif_stc.Refresh()

        # Also update console syntax highlighting to match
        if hasattr(self, 'console_stc') and hasattr(self, 'pif_format'):
            self.setup_syntax_highlighting(self.console_stc, self.pif_format)
            self.console_stc.Refresh()

    # -----------------------------------------------
    #              Function onShow
    # -----------------------------------------------
    def onShow(self, event):
        if self.IsShown():
            if self.config:
                size = (self.config.pif_width, self.config.pif_height)
            else:
                size=(PIF_WIDTH, PIF_HEIGHT)
            self.SetSize(size)
        event.Skip()

    # -----------------------------------------------
    #              Function init
    # -----------------------------------------------
    def init(self, refresh=False):
        if self.config.pif:
            with contextlib.suppress(KeyError):
                self.add_missing_keys_checkbox.SetValue(self.config.pif['auto_fill'])
            with contextlib.suppress(KeyError):
                self.force_first_api_checkbox.SetValue(self.config.pif['force_first_api'])
            with contextlib.suppress(KeyError):
                self.first_api_value = self.config.pif['first_api_value_when_forced']
                self.force_first_api_checkbox.SetToolTip(f"Forces First API value(s) to {self.first_api_value}")
                self.api_value_input.SetValue(str(self.first_api_value))
            with contextlib.suppress(KeyError):
                self.sort_keys_checkbox.SetValue(self.config.pif['sort_keys'])
            with contextlib.suppress(KeyError):
                self.keep_unknown_checkbox.SetValue(self.config.pif['keep_unknown'])
            with contextlib.suppress(KeyError):
                self.spoofBuild_checkbox.SetValue(self.config.pif['spoofBuild'])
            with contextlib.suppress(KeyError):
                self.spoofProps_checkbox.SetValue(self.config.pif['spoofProps'])
            with contextlib.suppress(KeyError):
                self.spoofProvider_checkbox.SetValue(self.config.pif['spoofProvider'])
            with contextlib.suppress(KeyError):
                self.spoofSignature_checkbox.SetValue(self.config.pif['spoofSignature'])
            with contextlib.suppress(KeyError):
                self.spoofVendingSdk_checkbox.SetValue(self.config.pif['spoofVendingSdk'])
            with contextlib.suppress(KeyError):
                self.spoofVendingFinger_checkbox.SetValue(self.config.pif['spoofVendingFinger'])
            with contextlib.suppress(KeyError):
                self.auto_update_pif_checkbox.SetValue(self.config.pif['auto_update_pif_json'])
            with contextlib.suppress(KeyError):
                self.auto_check_pi_checkbox.SetValue(self.config.pif['auto_check_play_integrity'])
            with contextlib.suppress(KeyError):
                self.auto_run_migrate_checkbox.SetValue(self.config.pif['auto_run_migrate'])
            with contextlib.suppress(KeyError):
                selected_index = self.config.pif['test_app_index']
                if selected_index >= len(self.pi_choices):
                    selected_index = 0
                self.pi_option.SetSelection(selected_index)
                self.pi_selection(self.pi_choices[selected_index])
            with contextlib.suppress(KeyError):
                self.disable_uiautomator_checkbox.SetValue(self.config.pif['disable_uiautomator'])
        if self.config.enable_bulk_prop:
            self.process_bulk_prop_button.Show()

        self.keep_unknown = self.keep_unknown_checkbox.IsChecked()
        self.sort_keys = self.sort_keys_checkbox.IsChecked()

        if self.force_first_api_checkbox.IsChecked():
            self.first_api = self.first_api_value
        else:
            self.first_api = None

        device = get_phone(True)
        if not device:
            self.console_stc.SetText(_("No Device is selected.\nPif Manager features are set to limited mode."))
            return
        if not device.rooted:
            self.console_stc.SetText(_("Device is not rooted or SU permissions to adb shell is not granted.\nPif Manager features are set to limited mode."))
            return
        modules = device.get_magisk_detailed_modules(refresh)

        self.create_pif_button.Enable(False)
        self.push_pif_button.Enable(False)
        self.reload_pif_button.Enable(False)
        self.push_kb_button.Enable(False)
        self.cleanup_dg_button.Enable(False)
        self.push_kb_button.Show(False)
        self.edit_ts_target_button.Enable(False)
        self.edit_ts_target_button.Show(False)
        self.edit_security_patch_button.Enable(False)
        self.edit_security_patch_button.Show(False)
        self.auto_update_pif_checkbox.Enable(False)
        self.auto_check_pi_checkbox.Enable(False)
        self.auto_run_migrate_checkbox.Enable(False)
        self.pi_checker_button.Enable(False)
        self.tf_targets_combo.Enable(False)
        self.tf_targets_combo.Clear()
        self.tf_targets_combo.Append(_("TF Targets"))
        self.tf_targets_combo.SetSelection(0)
        self.tf_targets_combo.SetForegroundColour(wx.Colour(128, 128, 128))
        # self.tf_targets_combo.Show(False)
        self.enable_buttons = False
        self.pif_selection_combo.Clear()
        self.pif_modules = []

        if modules:
            found_pif_module = False
            for module in modules:
                if module.state == 'enabled' and ((module.id == "playintegrityfix" and "Play Integrity" in module.name) or module.id == "tricky_store" or module.id == "targetedfix"):
                    self.pif_format = None
                    self.pif_path = None
                    # playintegrityfix
                    if module.id == "playintegrityfix":
                        self.pif_format = 'json'
                        if "Play Integrity Fork" in module.name:
                            self.pif_path = '/data/adb/modules/playintegrityfix/custom.pif.json'
                            if int(module.versionCode) > 4000:
                                print("Advanced props support enabled.")
                                res, unused = device.check_file('/data/adb/modules/playintegrityfix/example.pif.prop', True)
                                if res == 1:
                                    res, unused = device.check_file('/data/adb/modules/playintegrityfix/custom.pif.prop', True)
                                    if res == 1:
                                        self.pif_format = 'prop'
                                        self.pif_path = '/data/adb/modules/playintegrityfix/custom.pif.prop'
                                        print("ℹ️ custom.pif.prop detected, switching to prop format.")
                                    elif res == 0:
                                        res, unused = device.check_file('/data/adb/modules/playintegrityfix/custom.pif.json', True)
                                        if res == 1:
                                            self.pif_format = 'json'
                                            self.pif_path = '/data/adb/modules/playintegrityfix/custom.pif.json'
                                            print("ℹ️ custom.pif.json detected, switching to json format.")
                                        else:
                                            self.pif_format = 'prop'
                                            self.pif_path = '/data/adb/modules/playintegrityfix/custom.pif.prop'
                                            print("⚠️ custom.pif.prop and custom.pif.json not found, defaulting to prop format.")
                        else:
                            if module.version in ["PROPS-v2.1", "PROPS-v2.0"]:
                                self.pif_path = '/data/adb/modules/playintegrityfix/pif.json'
                            else:
                                self.pif_path = '/data/adb/pif.json'
                        self.auto_check_pi_checkbox.Enable(True)
                        self.auto_run_migrate_checkbox.Enable(True)

                    # tricky_store
                    elif module.id == "tricky_store":
                        self.pif_format = 'prop'
                        self.pif_path = '/data/adb/tricky_store/spoof_build_vars'
                        self.push_kb_button.Enable(True)
                        self.push_kb_button.Show(True)
                        self.edit_ts_target_button.Enable(True)
                        self.edit_ts_target_button.Show(True)
                        self.edit_security_patch_button.Enable(True)
                        self.edit_security_patch_button.Show(True)
                        self.auto_run_migrate_checkbox.Enable(False)

                    # targetedfix
                    elif module.id == "targetedfix":
                        self.pif_format = 'json'
                        self.tf_target_path = f"{TARGETEDFIX_CONFIG_PATH}/target.txt"
                        self.tf_targets_combo.Enable(True)
                        self.auto_run_migrate_checkbox.Enable(False)
                        self.create_pif_button.Enable(False)
                        self.push_pif_button.Enable(False)
                        self.reload_pif_button.Enable(False)
                        self.auto_update_pif_checkbox.Enable(False)
                        self.enable_buttons = False
                        if int(module.versionCode) >= 300:
                            print("ℹ️ Detected newer TargetedFix, switching to prop format.")
                            self.pif_format = 'prop'
                            self.tf_push_json_button.SetLabelText(_("Push TF Prop"))

                    flavor = module.name.replace(" ", "").lower()
                    self.pif_flavor = f"{flavor}_{module.versionCode}"
                    self.pif_modules.append(PifModule(id=module.id, name=module.name, version=module.version, version_code=module.versionCode, format=self.pif_format, path=self.pif_path, flavor=self.pif_flavor))
                    found_pif_module = True
                    self.create_pif_button.Enable(True)
                    self.push_pif_button.Enable(True)
                    self.reload_pif_button.Enable(True)
                    self.cleanup_dg_button.Enable(True)
                    self.auto_update_pif_checkbox.Enable(True)
                    self.pi_checker_button.Enable(True)
                    self.enable_buttons = True
                    module_label = f"{module.name} {module.version} {module.versionCode}"
                    if module.id != "tricky_store":
                        self.pif_selection_combo.Append(module_label)

        if found_pif_module:
            # Update combo box size based on content
            self.update_combo_size(self.pif_selection_combo)

            # Make the selection in priority order: Play Integrity, Trickystore, TargetedFix
            for i in range(self.pif_selection_combo.GetCount()):
                if "Play Integrity" in self.pif_selection_combo.GetString(i):
                    self.pif_selection_combo.SetSelection(i)
                    break
                elif "Tricky" in self.pif_selection_combo.GetString(i):
                    self.pif_selection_combo.SetSelection(i)
                elif "TargetedFix" in self.pif_selection_combo.GetString(i):
                    self.pif_selection_combo.SetSelection(i)
            # If nothing is selected and there are items, select the first item
            if self.pif_selection_combo.GetSelection() == wx.NOT_FOUND and self.pif_selection_combo.GetCount() > 0:
                self.pif_selection_combo.SetSelection(0)

            # Manually trigger the combo box change event
            self.onPifSelectionComboBox(None)

    # -----------------------------------------------
    #                  check_pif_json
    # -----------------------------------------------
    def check_pif_json(self):
        device = get_phone(True)
        if not device.rooted:
            return
        # check for presence of pif.json
        if self.pif_path is None:
            self.pif_exists = False
            self.create_pif_button.Enable(False)
            self.push_pif_button.Enable(False)
            self.reload_pif_button.Enable(False)
            self.cleanup_dg_button.Enable(False)
            self.create_pif_button.SetLabel(_("Create print"))
            self.create_pif_button.SetToolTip(_("Create pif.json / spoof_build_vars."))
            return
        res, unused = device.check_file(self.pif_path, True)
        if res == 1:
            self.pif_exists = True
            self.reload_pif_button.Enable(True)
            self.cleanup_dg_button.Enable(True)
            self.create_pif_button.SetLabel(_("Update print"))
            self.create_pif_button.SetToolTip(_("Update pif.json / spoof_build_vars."))
        else:
            self.pif_exists = False
            self.create_pif_button.SetLabel(_("Create print"))
            self.create_pif_button.SetToolTip(_("Create pif.json / spoof_build_vars."))

    # -----------------------------------------------
    #                  onFavoritesComboBox
    # -----------------------------------------------
    def onFavoritesComboBox(self, event):
        selected_index = event.GetSelection()
        pif_list = list(self.favorite_pifs.values())

        if 0 <= selected_index < len(pif_list):
            selected_pif = pif_list[selected_index]
            pif_object = selected_pif["pif"]
            if self.pif_format == 'prop':
                json_string = json.dumps(pif_object, indent=4, sort_keys=self.sort_keys)
                self.active_pif_stc.SetText(self.J2P(json_string))
            else:
                self.active_pif_stc.SetText(json.dumps(pif_object, indent=4))
        else:
            print("Selected Pif not found, Index out of range")

    # -----------------------------------------------
    #                  onPifSelectionComboBox
    # -----------------------------------------------
    def onPifSelectionComboBox(self, event):
        selection_index = self.pif_selection_combo.GetSelection()
        if selection_index != wx.NOT_FOUND and self.pif_modules and selection_index < len(self.pif_modules):
            selected_module = self.pif_modules[selection_index]
            self.current_pif_module = selected_module
            self.pif_format = selected_module.format
            self.pif_path = selected_module.path
            self.pif_flavor = selected_module.flavor

        if selected_module.id == "tricky_store":
            self.spoofBuild_checkbox.Enable(False)
            self.spoofProps_checkbox.Enable(False)
            self.spoofProvider_checkbox.Enable(False)
            self.spoofSignature_checkbox.Enable(False)
            self.spoofVendingSdk_checkbox.Enable(False)
            self.spoofVendingFinger_checkbox.Enable(False)
            self.auto_run_migrate_checkbox.Enable(False)
        else:
            self.spoofBuild_checkbox.Enable(True)
            self.spoofProps_checkbox.Enable(True)
            self.spoofProvider_checkbox.Enable(True)
            self.spoofSignature_checkbox.Enable(True)
            self.spoofVendingSdk_checkbox.Enable(True)
            self.spoofVendingFinger_checkbox.Enable(True)
            if selected_module.id == "targetedfix":
                # Show TargetedFix buttons
                self.tf_add_target_button.Show(True)
                self.tf_delete_target_button.Show(True)
                self.tf_edit_targets_button.Show(True)
                self.tf_push_json_button.Show(True)
                self.auto_run_migrate_checkbox.Enable(False)
                self.tf_targets_combo.Enable(True)
            else:
                # Play Integrity Fix selected
                self.auto_run_migrate_checkbox.Enable(True)
                # Hide TargetedFix buttons
                self.tf_add_target_button.Show(False)
                self.tf_delete_target_button.Show(False)
                self.tf_edit_targets_button.Show(False)
                self.tf_push_json_button.Show(False)
                self.tf_targets_combo.Enable(False)
                self.tf_targets_combo.Clear()
                self.tf_targets_combo.Append(_("TF Targets"))
                self.tf_targets_combo.SetSelection(0)
                self.tf_targets_combo.SetForegroundColour(wx.Colour(128, 128, 128))

        self.Layout()

        self.update_syntax_highlighting()

        selected_label = f"{selected_module.name} {selected_module.version}"
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} Loading selected Module: {selected_label}")
        print("==============================================================================")
        if selected_module.id == "targetedfix":
            # For TargetedFix, check if we have targets loaded, if not load them
            if self.tf_targets_combo.GetCount() <= 1 and self.tf_targets_combo.GetString(0) == _("TF Targets"):
                # No targets loaded yet, load them now and only once
                targets = self.load_tf_targets()

            # Select the first target
            if self.tf_targets_combo.GetCount() > 0:
                first_item = self.tf_targets_combo.GetString(0)
                if first_item != _("TF Targets"):
                    self.tf_targets_combo.SetSelection(0)  # Select first actual target
                    self.onTFTargetSelectionComboBox(None)
                else:
                    if self.pif_format == 'json':
                        self.active_pif_stc.SetValue("{}")
                    else:
                        self.active_pif_stc.SetValue("")
                    self.console_stc.SetText("No Target selected")
            else:
                if self.pif_format == 'json':
                    self.active_pif_stc.SetValue("{}")
                else:
                    self.active_pif_stc.SetValue("")
                self.console_stc.SetText("No Target selected")
        else:
            self.LoadPif(self.pif_path)


    # -----------------------------------------------
    #                  load_tf_targets
    # -----------------------------------------------
    def load_tf_targets(self):
        try:
            device = get_phone(True)
            if not device.rooted:
                self.populate_tf_targets([])
                return []

            config_path = get_config_path()
            local_target_file = os.path.join(config_path, 'tmp', 'tf_target.txt')

            if not self._tf_targets_loaded:
                res, unused = device.check_file(self.tf_target_path, True)
                if res == 1:
                    self.tf_target_exists = True

                    # Pull the target.txt file to local as tf_target.txt
                    res = device.pull_file(self.tf_target_path, local_target_file, True, quiet=True)
                    if res != 0:
                        # File doesn't exist, create empty local file
                        with open(local_target_file, 'w', encoding='utf-8') as f:
                            f.write('')
                        targets = []
                    else:
                        self._tf_targets_loaded = True
                else:
                    self.tf_target_exists = False
                    # Create empty local file
                    with open(local_target_file, 'w', encoding='utf-8') as f:
                        f.write('')
                    self.populate_tf_targets([])
                    return []

            # check for presence of tf targets file
            if self.tf_target_path is None:
                self.tf_target_exists = False
                self.populate_tf_targets([])
                return []

            else:
                # Read targets from local file
                with open(local_target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                targets = [target.strip() for target in content.strip().splitlines() if target.strip()]

                # Only pull files that don't exist locally
                for target in targets:
                    local_tf_target_file = os.path.join(config_path, 'tmp', f'{target}.{self.pif_format}')
                    if not os.path.exists(local_tf_target_file) or not self._tf_targets_loaded:
                        remote_tf_target_file = f"{TARGETEDFIX_CONFIG_PATH}/{target}.{self.pif_format}"
                        res = device.pull_file(remote_tf_target_file, local_tf_target_file, True, quiet=True)
                        # If pull fails, create empty JSON file
                        if res != 0:
                            with open(local_tf_target_file, 'w', encoding='utf-8') as f:
                                if self.pif_format == 'json':
                                    f.write('{}')
                                else:
                                    f.write('')

                self.populate_tf_targets(targets)
                return targets

        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: loading TargetedFix targets")
            traceback.print_exc()
            self.populate_tf_targets([])
            return []

    # -----------------------------------------------
    #                  populate_tf_targets
    # -----------------------------------------------
    def populate_tf_targets(self, targets):
        try:
            self.tf_targets_combo.Clear()

            if targets and len(targets) > 0:
                # Add all targets to the combo box
                for target in targets:
                    self.tf_targets_combo.Append(target)

                # Select the first target
                self.tf_targets_combo.SetSelection(0)

                # Set normal text color (black)
                self.tf_targets_combo.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

                # Update combo box size based on content
                self.update_combo_size(self.tf_targets_combo)

                # Update button states based on selection
                self.update_tf_button_states()

                print(f"Populated TF targets combo with {len(targets)} targets")
            else:
                # No targets found, add placeholder
                self.tf_targets_combo.Append(_("TF Targets"))
                self.tf_targets_combo.SetSelection(0)
                self.tf_targets_combo.Enabled = False

                # Set gray placeholder text color
                self.tf_targets_combo.SetForegroundColour(wx.Colour(128, 128, 128))

                # Update button states
                self.update_tf_button_states()

                print("No TF targets found, showing placeholder")

            # Force layout refresh
            self.Layout()

        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: populating TF targets")
            traceback.print_exc()
            # On error, show placeholder
            self.tf_targets_combo.Clear()
            self.tf_targets_combo.Append(_("TF Targets"))
            self.tf_targets_combo.SetSelection(0)
            self.tf_targets_combo.SetForegroundColour(wx.Colour(128, 128, 128))

    # -----------------------------------------------
    #                  onTFTargetSelectionComboBox
    # -----------------------------------------------
    def onTFTargetSelectionComboBox(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User made a TargetedFix target selection.")
        print("==============================================================================")
        selection_index = self.tf_targets_combo.GetSelection()
        selected_text = self.tf_targets_combo.GetStringSelection()

        # Handle placeholder text selection
        if selected_text == _("TF Targets"):
            # Keep the gray color for placeholder
            self.update_tf_button_states()
            return

        # Handle actual target selection
        self.tf_targets_combo.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        print(f"Selected target: {selected_text}")
        self.update_tf_button_states()

        if selected_text:
            # Load from local file instead of device
            config_path = get_config_path()
            local_tf_target_file = os.path.join(config_path, 'tmp', f'{selected_text}.{self.pif_format}')

            if os.path.exists(local_tf_target_file):
                try:
                    with open(local_tf_target_file, 'r', encoding='utf-8') as f:
                        contents = f.read()
                    self.device_pif = contents
                    self.active_pif_stc.SetValue(contents)
                except Exception as e:
                    print(f"Error reading local {self.pif_format} file: {e}")
                    if self.pif_format == 'prop':
                        self.active_pif_stc.SetValue("")
                    else:
                        self.active_pif_stc.SetValue("{}")
            else:
                # Create empty {self.pif_format} if file doesn't exist
                with open(local_tf_target_file, 'w', encoding='utf-8') as f:
                    if self.pif_format == 'json':
                        f.write('{}')
                    else:
                        f.write('')
                if self.pif_format == 'prop':
                    self.active_pif_stc.SetValue("")
                else:
                    self.active_pif_stc.SetValue("{}")

    # -----------------------------------------------
    #                  onTestPIAppOptionSelect
    # -----------------------------------------------
    def onTestPIAppOptionSelect(self, event):
        option = event.GetString()
        self.pi_selection(option)

    # -----------------------------------------------
    #                  pi_selection
    # -----------------------------------------------
    def pi_selection(self, selected_option):
        if selected_option == "Play Integrity API Checker":
            print("Play Integrity API Checker option selected")
            self.pi_app = 'gr.nikolasspyr.integritycheck'
            # self.launch_method = 'launch-am'
            self.launch_method = 'launch'

        elif selected_option == "Simple Play Integrity Checker":
            print("Simple Play Integrity Checker option selected")
            self.pi_app = 'com.henrikherzig.playintegritychecker'
            # self.launch_method = 'launch-am'
            self.launch_method = 'launch'

        elif selected_option == "TB Checker":
            print("TB Checker option selected")
            self.pi_app = 'krypton.tbsafetychecker'
            # self.launch_method = 'launch-am-main'
            self.launch_method = 'launch'

        elif selected_option == "Android Integrity Checker":
            print("Android Integrity Checker option selected")
            self.pi_app = 'com.thend.integritychecker'
            # self.launch_method = 'launch-am-main'
            self.launch_method = 'launch'

        elif selected_option == "Play Store":
            print("Play Store option selected")
            self.pi_app = 'com.android.vending'
            self.launch_method = 'launch'

        elif selected_option == "YASNAC":
            print("YASNAC option selected")
            self.pi_app = 'rikka.safetynetchecker'
            # self.launch_method = 'launch-am-main'
            self.launch_method = 'launch'

        print(f"Auto Update print is set to: {selected_option}")
        self.config.pif['test_app_index'] = self.pi_option.Selection

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  onClose
    # -----------------------------------------------
    def onClose(self, e):
        try:
            # Clean up the validation timer
            if self._validation_timer is not None:
                self._validation_timer.Stop()

            dialog_size = self.GetSize()
            dialog_x, dialog_y = dialog_size.GetWidth(), dialog_size.GetHeight()
            config = get_config()
            config.pif_width = dialog_x
            config.pif_height = dialog_y
            config.pif = self.config.pif
            set_config(config)
        except Exception:
            traceback.print_exc()
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to properly close the window.")
        finally:
            self.Destroy()

    # -----------------------------------------------
    #                  onReloadPrint
    # -----------------------------------------------
    def onReloadPrint(self, e):
        if self.pif_path:
            self.LoadPif(self.pif_path)

    # -----------------------------------------------
    #                  LoadPif
    # -----------------------------------------------
    def LoadPif(self, file_path):
        try:
            device = get_phone(True)
            if not device.rooted:
                return
            self._on_spin('start')
            config_path = get_config_path()
            self.check_pif_json()
            pif_prop = os.path.join(config_path, 'tmp', 'pif.json')
            if self.reload_pif_button.Enabled or "targetedfix" in file_path:
                # pull the file
                res = device.pull_file(remote_file=file_path, local_file=pif_prop, with_su=True, quiet=True)
                if res != 0:
                    print(f"File: {file_path} not found.")
                    self.active_pif_stc.SetValue("")
                    # puml("#red:Failed to pull pif.prop from the phone;\n}\n")
                    self._on_spin('stop')
                    return
            else:
                # we need to create one.
                with open(pif_prop, 'w', encoding='utf-8') as file:
                    pass
            # get the contents of modified pif.json
            encoding = detect_encoding(pif_prop)
            with open(pif_prop, 'r', encoding=encoding, errors="replace") as f:
                contents = f.read()
                self.device_pif = contents
            self.active_pif_stc.SetValue(contents)

        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Load {file_path} process.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onUpdatePrint
    # -----------------------------------------------
    def onUpdatePrint(self, e):
        self.create_update_pif(just_push=False)

    # -----------------------------------------------
    #                  onPushPrint
    # -----------------------------------------------
    def onPushPrint(self, e):
        self.create_update_pif(just_push=True)

    # -----------------------------------------------
    #                  onAddTFTarget
    # -----------------------------------------------
    def onAddTFTarget(self, e):
        try:
            print("\n==============================================================================")
            print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Add Target process")
            print("==============================================================================")
            device = get_phone(True)
            if not device or not device.rooted:
                print("Error: Device not available or not rooted")
                return

            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Add TF Target")

            # Create a simplified package manager dialog
            self._on_spin('start')
            # load labels if not already loaded
            if not get_labels() and os.path.exists(get_labels_file_path()):
                with open(get_labels_file_path(), "r", encoding='ISO-8859-1', errors="replace") as f:
                    set_labels(json.load(f))
            dlg = PackageManager(self, title="Select Package for TargetedFix Target", simplified_mode=True)
            self._on_spin('stop')
            result = dlg.ShowModal()

            if result == wx.ID_OK:
                selected_package = dlg.GetSelectedPackage()
                if selected_package:
                    print(f"Selected package: {selected_package}")

                    # Validate target name (package names are already valid)
                    target_name = selected_package

                    # Check if target already exists in local file
                    config_path = get_config_path()
                    local_target_file = os.path.join(config_path, 'tmp', 'tf_target.txt')
                    existing_targets = []
                    if os.path.exists(local_target_file):
                        with open(local_target_file, 'r', encoding='utf-8') as f:
                            existing_targets = [line.strip() for line in f.readlines() if line.strip()]

                    if target_name in existing_targets:
                        wx.MessageBox(f"Target '{target_name}' already exists in the list.", "Target Exists", wx.OK | wx.ICON_WARNING)
                        dlg.Destroy()
                        return

                    # Add to target list file locally and push to device
                    if self.add_target_to_device(target_name):
                        # Just update the combo box locally instead of reloading everything
                        self.tf_targets_combo.Append(target_name)
                        target_index = self.tf_targets_combo.FindString(target_name)
                        if target_index != wx.NOT_FOUND:
                            self.tf_targets_combo.SetSelection(target_index)
                            self.tf_targets_combo.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
                            self.onTFTargetSelectionComboBox(None)

                        # Update combo box size and button states
                        self.update_combo_size(self.tf_targets_combo)
                        self.update_tf_button_states()

                        print(f"Successfully added target: {target_name}")
                        self.console_stc.SetText(f"Added target: {target_name}")
                    else:
                        wx.MessageBox(f"Failed to add target '{target_name}' to device.", "Error", wx.OK | wx.ICON_ERROR)

            dlg.Destroy()

        except Exception as ex:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during TF add target process.")
            traceback.print_exc()

    # -----------------------------------------------
    #                  add_target_to_device
    # -----------------------------------------------
    def add_target_to_device(self, target_name):
        try:
            config_path = get_config_path()
            local_target_file = os.path.join(config_path, 'tmp', 'tf_target.txt')

            # Read existing targets from local file
            if os.path.exists(local_target_file):
                with open(local_target_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                targets = [target.strip() for target in content.strip().splitlines() if target.strip()]
            else:
                targets = []

            # Add new target if not already present
            if target_name not in targets:
                targets.append(target_name)

                # Write back to local file
                with open(local_target_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(targets) + '\n')

                # Create empty local {self.pif_format} file for the target
                local_tf_target_file = os.path.join(config_path, 'tmp', f'{target_name}.{self.pif_format}')
                with open(local_tf_target_file, 'w', encoding='utf-8') as f:
                    if self.pif_format == 'prop':
                        f.write('')
                    else:
                        f.write('{}')

                device = get_phone(True)
                if device and device.rooted:
                    # Push target.txt (using original name on device)
                    res = device.push_file(local_target_file, self.tf_target_path, True)
                    if res != 0:
                        print(f"Failed to push target.txt to device")
                        return False
                    return True
            return True

        except Exception as ex:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: adding target locally: {ex}")
            traceback.print_exc()
            return False

    # -----------------------------------------------
    #                  onDeleteTFTarget
    # -----------------------------------------------
    def onDeleteTFTarget(self, e):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Delete Target process")
        print("==============================================================================")
        # if no target selected, do nothing
        selected_index = self.tf_targets_combo.GetSelection()
        selected_text = self.tf_targets_combo.GetStringSelection()
        if selected_text == _("TF Targets") or selected_index == wx.NOT_FOUND:
            return
        # confirm deletion
        dlg = wx.MessageDialog(self, f"Are you sure you want to delete the target '{selected_text}'?\nThis will remove the target and its associated {self.pif_format} file from the device.", "Confirm Deletion", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            try:
                config_path = get_config_path()
                local_target_file = os.path.join(config_path, 'tmp', 'tf_target.txt')
                local_tf_target_file = os.path.join(config_path, 'tmp', f'{selected_text}.{self.pif_format}')

                print(f"Deleting target: {selected_text}")

                # Remove from local target.txt file
                if os.path.exists(local_target_file):
                    with open(local_target_file, 'r', encoding='utf-8') as f:
                        targets = [line.strip() for line in f.readlines() if line.strip()]

                    # Remove the selected target
                    targets = [target for target in targets if target != selected_text]

                    # Write back to local file
                    with open(local_target_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(targets) + '\n' if targets else '')

                # Remove local {self.pif_format} file
                if os.path.exists(local_tf_target_file):
                    os.remove(local_tf_target_file)

                # Push updated files to device
                device = get_phone(True)
                if device and device.rooted:
                    # Push updated target.txt (using original name on device)
                    res = device.push_file(local_target_file, self.tf_target_path, True)
                    if res != 0:
                        print(f"Failed to update target list file: {self.tf_target_path}")
                        return

                    # Delete the {self.pif_format} file from device
                    remote_tf_target_file = f"{TARGETEDFIX_CONFIG_PATH}/{selected_text}.{self.pif_format}"
                    res = device.delete(remote_tf_target_file, with_su=True, dir=False)
                    if res != 0:
                        print(f"Failed to delete {self.pif_format} file: {remote_tf_target_file}")
                        return

                    print(f"Target '{selected_text}' and its {self.pif_format} file have been deleted.")
                    self.console_stc.SetText(f"Deleted target: {selected_text}")

                    # Refresh the targets combo box
                    targets = self.load_tf_targets()
                    if targets and len(targets) > 0:
                        self.tf_targets_combo.SetSelection(0)
                        self.onTFTargetSelectionComboBox(None)
                    else:
                        self.console_stc.AppendText("\nNo Target selected")
            except Exception as ex:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during TF target deletion process.")
                traceback.print_exc()

    # -----------------------------------------------
    #                  onPushTFProp
    # -----------------------------------------------
    def onPushTFProp(self, e):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated Push Target {self.pif_format} process")
        print("==============================================================================")
        # Get the selected target and update the local PROP / JSON file first
        selected_text = self.tf_targets_combo.GetStringSelection()
        if selected_text and selected_text != _("TF Targets"):
            config_path = get_config_path()
            local_tf_target_file = os.path.join(config_path, 'tmp', f'{selected_text}.{self.pif_format}')

            # Save current content to local file
            content = self.active_pif_stc.GetValue()
            with open(local_tf_target_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Now push the local file to device
            remote_filepath = f"{TARGETEDFIX_CONFIG_PATH}/{selected_text}.{self.pif_format}"
            print(f"Pushing {self.pif_format} for target '{selected_text}' to device...")
            self.create_update_pif(just_push=True, filepath=remote_filepath)

    # -----------------------------------------------
    #                  onCleanupDG
    # -----------------------------------------------
    def onCleanupDG(self, e):
        device = get_phone()
        if not device or not device.rooted:
            return
        print("Cleaning up DG Cache ...")
        device.delete("/data/data/com.google.android.gms/app_dg_cache", with_su = True, dir = True)
        device.delete("/data/data/com.google.android.gms/databases/dg.db*", with_su = True, dir = False)

    # -----------------------------------------------
    #                  UpdatePifJson
    # -----------------------------------------------
    def UpdatePifJson(self, e):
        self.create_update_pif()

    # -----------------------------------------------
    #                  create_update_pif
    # -----------------------------------------------
    def create_update_pif(self, just_push=False, filepath=None):
        try:
            device = get_phone(True)
            if not device.rooted:
                return

            self._on_spin('start')
            config_path = get_config_path()
            pif_prop = os.path.join(config_path, 'tmp', 'pif.json')
            json_data = None

            content = self.active_pif_stc.GetValue()
            if not just_push:
                if self.pif_format == 'prop':
                    json_data = self.P2J(content)
                else:
                    json_data = content
                if json_data:
                    try:
                        data = json.loads(json_data)
                    except Exception:
                        try:
                            data = json5.loads(json_data)
                        except Exception:
                            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Not a valid json.")
                            self._on_spin('stop')
                            return
                else:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Not a valid json.")
                    self._on_spin('stop')
                    return

            # Save the data as normal JSON
            with open(pif_prop, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
                if just_push:
                    with open(pif_prop, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
                        f.write(content)
                else:
                    if self.pif_format == 'prop':
                        f.write(self.J2P(json.dumps(data, indent=4, sort_keys=self.sort_keys)))
                    else:
                        json.dump(data, f, indent=4, sort_keys=self.sort_keys)

            # push the file
            if not filepath:
                filepath = self.pif_path
            res = device.push_file(pif_prop, filepath, True)
            if res != 0:
                print("Aborting ...\n")
                # puml("#red:Failed to push pif.json from the phone;\n}\n")
                self._on_spin('stop')
                return -1

            if just_push:
                self.device_pif = content
            else:
                self.device_pif = json.dumps(data, indent=4, sort_keys=self.sort_keys)

            print("Killing Google GMS  ...")
            res = device.perform_package_action(pkg='com.google.android.gms.unstable', action='killall')
            if res.returncode != 0:
                print("Error killing GMS.")
            else:
                print("Killing Google GMS succeeded.")

            print("Killing Android Vending  ...")
            res = device.perform_package_action(pkg='com.android.vending', action='killall')
            if res.returncode != 0:
                print("Error killing Android Vending.")
            else:
                print("Killing Android Vending succeeded.")

            if not just_push:
                self.check_pif_json()
            self.LoadPif(filepath)

            # Auto run migrate if enabled
            if self.auto_run_migrate_checkbox.IsEnabled() and self.auto_run_migrate_checkbox.IsChecked():
                print("Auto Running Migrate ...")
                self.runMigrate()

            # Auto test Play Integrity
            if self.auto_check_pi_checkbox.IsEnabled() and self.auto_check_pi_checkbox.IsChecked():
                print("Auto Testing Play Integrity ...")
                self.onPlayIntegrityCheck(None)
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during pip Create process.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  get_pi_app_coords
    # -----------------------------------------------
    def get_pi_app_coords(self, child=None):
        try:
            device = get_phone()
            if not device.rooted:
                return
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Getting coordinates for {self.pi_app}")

            # pull view
            config_path = get_config_path()
            pi_app_xml = os.path.join(config_path, 'tmp', 'pi_app.xml')

            if self.pi_app == 'gr.nikolasspyr.integritycheck':
                return  device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "CHECK", False)

            elif self.pi_app == 'com.henrikherzig.playintegritychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Make Play Integrity Request", False)

            elif self.pi_app == 'krypton.tbsafetychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Run Play Integrity Check", False)

            elif self.pi_app == 'com.thend.integritychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "android.widget.Button", False)

            elif self.pi_app == 'rikka.safetynetchecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Run SafetyNet Attestation", False)

            elif self.pi_app == 'com.android.vending':
                if child == 'user':
                    # This needs custom handling, as there is no identifiable string to look for
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "PixelFlasher_Playstore", True)
                if child == 'settings':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Settings", True)
                if child == 'general':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "General", True)
                if child == 'scroll':
                    return device.swipe_up()
                if child == 'developer_options':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Developer options", True)
                if child == 'test':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Check integrity", False)
                if child == 'dismiss':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Dismiss", False)

        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in get_pi_app_coords function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onGetCanaryPif
    # -----------------------------------------------
    def onGetCanaryPif(self, e):
        try:
            self._on_spin('start')
            device = get_phone()
            if device:
                device_model = device.hardware
            buttons_text = [_("Canary Device"), "Canary Emulator", "Beta Device", _("Cancel")]
            dlg = MessageBoxEx(
                parent=self,
                title=_('Canary Miner Selection'),
                message=_("Please make a selection"),
                button_texts=buttons_text,
                default_button=1,
                disable_buttons=None,
                is_md=False,
                size=(800, 600),
                checkbox_labels=None,
                checkbox_initial_values=None,
                disable_checkboxes=None,
                vertical_checkboxes=False,
                checkbox_labels2=None,
                checkbox_initial_values2=None,
                disable_checkboxes2=None,
                radio_labels=None,
                radio_initial_value=None,
                disable_radios=None,
                vertical_radios=False
            )
            dlg.CentreOnParent(wx.BOTH)
            result = dlg.ShowModal()
            dlg.Destroy()
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed {buttons_text[result -1]}")
            miner_url = None
            if result == 1:
                miner_url = "https://github.com/Vagelis1608/get_the_canary_miner/tree/main/devices"
            elif result == 2:
                miner_url = "https://github.com/Vagelis1608/get_the_canary_miner/tree/main/emulator"
            elif result == 3:
                miner_url = "https://github.com/Vagelis1608/get_the_canary_miner/tree/main/betas"
            else:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Cancel.")
                print("Aborting ...\n")
                return -1

            canary_pif = get_canary_miner(device_model='_select_', default_selection=device_model if device else None, miner_url=miner_url)
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(canary_pif, quiet=True))
            else:
                self.console_stc.SetValue(self.P2J(canary_pif))
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onGetCanaryPif function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onGetFreemanPif
    # -----------------------------------------------
    def onGetFreemanPif(self, e):
        try:
            device = get_phone()
            if not device:
                abilist = ''
            else:
                if not device.rooted:
                    return
                self._on_spin('start')
                keys = ['ro.product.cpu.abilist', 'ro.product.cpu.abi', 'ro.system.product.cpu.abilist', 'ro.vendor.product.cpu.abilist']
                abilist = get_first_match(device.props.property, keys)

            freeman_pif = get_freeman_pif(abilist)
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(freeman_pif))
            else:
                self.console_stc.SetValue(freeman_pif)
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onGetFreemanPif function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onBetaRadioSelect
    # -----------------------------------------------
    def onBetaRadioSelect(self, event):
        is_custom = self.rb_custom.GetValue()
        self.custom_version.Enable(is_custom)

        if self.rb_latest.GetValue():
            self.beta_pif_version = 'latest'
        else:
            # When switching to custom, validate existing text
            try:
                value = self.custom_version.GetValue()
                if value.isdigit() or value.lower() == 'c' or value.startswith('CANARY') or value.lower() == 't':
                    self.beta_pif_version = str(value)
                else:
                    self.beta_pif_version = 'latest'
            except ValueError:
                self.beta_pif_version = 'latest'

            # Set focus to the custom version input and select all text
            if is_custom:
                self.custom_version.SetFocus()
                self.custom_version.SetSelection(-1, -1)

    # -----------------------------------------------
    #                  onBetaVersionChange
    # -----------------------------------------------
    def onBetaVersionChange(self, event):
        text = self.custom_version.GetValue().strip()

        try:
            if text:
                self.beta_pif_version = str(text)
            else:
                self.beta_pif_version = 'latest'
        except ValueError:
            print(f"ERROR: Invalid Android version number: {text}")
            self.custom_version.SetValue('')  # Clear invalid input
            event.Skip(False)  # Prevent invalid input
            return

        # Allow valid changes
        event.Skip()

    # -----------------------------------------------
    #                  onGetPixelBetaPif
    # -----------------------------------------------
    def onGetPixelBetaPif(self, e):
        try:
            self._on_spin('start')
            wx.CallAfter(self.console_stc.SetValue, _("Getting Pixel beta print ...\nPlease be patient this could take some time ..."))
            wx.Yield()
            force_version = None
            device = get_phone()
            if wx.GetKeyState(wx.WXK_CONTROL) and wx.GetKeyState(wx.WXK_SHIFT):
                device_model = "all"
            elif wx.GetKeyState(wx.WXK_CONTROL):
                device_model = "_select_"
            elif device:
                device_model = device.hardware
            else:
                # device_model = "Random"
                device_model = "_select_"
            # Check if self.beta_pif_version is a two digit number then set force_version to that (int)
            if self.beta_pif_version.isdigit() and len(self.beta_pif_version) == 2:
                force_version = int(self.beta_pif_version)
            elif self.beta_pif_version.lower() == 'c':
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
                    selected_entry = self.select_catalog_image(catalog)
                    if selected_entry:
                        release = selected_entry.get('release', {}) if isinstance(selected_entry, dict) else {}
                        selected_url = release.get('url') if isinstance(release, dict) else None
                        if selected_url and self.process_factory_image_selection(selected_url, "Canary"):
                            return
                        if not selected_url:
                            print("⚠️ WARNING! Selected Canary catalog entry is missing a download URL.")
                        device_model = release.get('target') or selected_entry.get('device_key', device_model)
                    else:
                        print("ℹ️ INFO: Canary catalog selection cancelled by user; skipping automatic retrieval.")
                        wx.CallAfter(self.console_stc.SetValue, _("Canary selection cancelled."))
                        return
            elif self.beta_pif_version.lower() == 't':
                force_version = 't'
                t_factory_images = get_telegram_factory_images()
                if t_factory_images and isinstance(t_factory_images, list):
                    selected_image = self.select_t_image(t_factory_images)
                    if selected_image is None:
                        force_version = None
                        self.console_stc.SetValue(f"{self.console_stc.GetValue()}\n⚠️ WARNING! No valid Telegram factory image selected.")
                        return
                    if self.process_factory_image_selection(selected_image, "Telegram"):
                        return
                    return
                else:
                    force_version = None
                    print(f"⚠️ WARNING! The requested Android beta / canary version is not valid: {self.beta_pif_version}. Using latest version instead.")
            else:
                force_version = None
                if self.rb_custom.GetValue():
                    print(f"⚠️ WARNING! The requested Android beta / canary version is not valid: {self.beta_pif_version}. Using latest version instead.")

            beta_pif = get_beta_pif(device_model, force_version)
            if beta_pif == -1:
                wx.CallAfter(self.console_stc.SetValue, _("Failed to get beta print."))
                return
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(beta_pif))
            else:
                self.console_stc.SetValue(beta_pif)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onGetPixelBetaPif function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  select_t_image
    # -----------------------------------------------
    # Create a custom dialog with tree control for selection
    def select_t_image(self, t_factory_images):
        try:
            if not (t_factory_images and isinstance(t_factory_images, list)):
                return None

            build_groups = {}
            for image in t_factory_images:
                if not isinstance(image, dict):
                    continue
                build_id = image.get('build_id', 'Unknown Build')
                build_groups.setdefault(build_id, []).append(image)

            if not build_groups:
                print("⚠️ WARNING! Telegram factory images did not contain any selectable entries.")
                return None

            tree_nodes = []
            for build_id, images in build_groups.items():
                children = []
                for image in images:
                    device_label = image.get('device', 'Unknown Device')
                    image_type = image.get('type', 'Factory Image')
                    children.append({
                        'label': f"{device_label} - {image_type}",
                        'data': image,
                    })
                tree_nodes.append({
                    'label': build_id,
                    'children': children,
                })

            selected_image = show_factory_image_dialog(
                self,
                _("Telegram Factory Images"),
                _("Select a factory image to use:"),
                _("Factory Images"),
                tree_nodes,
                size=(800, 600),
                download_button=True,
            )

            if selected_image and isinstance(selected_image, dict):
                print(f"Selected factory image: {selected_image.get('device', 'Unknown Device')} - {selected_image.get('type', 'Factory Image')}")
                print(f"URL: {selected_image.get('url')}")
                return selected_image.get('url')
            return None
        except Exception as e:
            print(f"Error selecting Telegram factory image: {e}")
            traceback.print_exc()
            return None

    # -----------------------------------------------
    #                  select_catalog_image
    # -----------------------------------------------
    def select_catalog_image(self, catalog):
        try:
            if not isinstance(catalog, dict):
                return None

            tree_data = {}
            sections = (
                ('canaries', _("Canaries")),
                ('betas', _("All Betas")),
            )

            for section_key, section_label in sections:
                section = catalog.get(section_key, {})
                if not isinstance(section, dict):
                    continue
                build_map = {}
                for device_key, device_obj in section.items():
                    if not isinstance(device_obj, dict):
                        continue
                    device_name = device_obj.get('name') or device_key
                    releases = device_obj.get('releases', [])
                    if not isinstance(releases, list):
                        continue
                    for release in releases:
                        if not isinstance(release, dict):
                            continue
                        build_name = release.get('buildName') or release.get('releaseId') or release.get('buildId') or _("Unknown Build")
                        entry = {
                            'category': section_label,
                            'device_key': device_key,
                            'device_name': device_name,
                            'release': release,
                        }
                        build_map.setdefault(build_name, []).append(entry)
                if build_map:
                    tree_data[section_label] = build_map

            if not tree_data:
                print("⚠️ WARNING! Canary Miner catalog did not contain any selectable entries.")
                return None

            def build_sort_value(build_name, entries):
                values = []
                for entry in entries:
                    release = entry.get('release') if isinstance(entry, dict) else None
                    if not isinstance(release, dict):
                        continue
                    for key in ('buildName', 'releaseId', 'buildId'):
                        candidate = release.get(key)
                        if not isinstance(candidate, str):
                            continue
                        match = re.search(r'(\d{6})', candidate)
                        if match:
                            values.append(int(match.group(1)))
                            break
                        match = re.search(r'(\d+)', candidate)
                        if match:
                            values.append(int(match.group(1)))
                            break
                if values:
                    return max(values)
                match = re.search(r'(\d{6})', build_name)
                if match:
                    return int(match.group(1))
                match = re.search(r'(\d+)', build_name)
                if match:
                    return int(match.group(1))
                return 0

            tree_nodes = []
            for section_label, build_map in sorted(tree_data.items()):
                build_children = []
                sorted_builds = sorted(
                    build_map.items(),
                    key=lambda kv: (build_sort_value(kv[0], kv[1]), kv[0]),
                    reverse=True
                )
                for build_name, entries in sorted_builds:
                    release_children = []
                    for entry in entries:
                        release = entry['release']
                        release_id = release.get('releaseId', '') if isinstance(release, dict) else ''
                        device_text = entry['device_name'] or entry['device_key']
                        if entry['device_key'] and entry['device_key'] not in device_text:
                            device_text = f"{device_text} [{entry['device_key']}]"
                        if release_id:
                            device_text = f"{device_text} ({release_id})"
                        release_children.append({
                            'label': device_text,
                            'data': entry,
                        })
                    if release_children:
                        build_children.append({
                            'label': build_name,
                            'children': release_children,
                        })
                if build_children:
                    tree_nodes.append({
                        'label': section_label,
                        'children': build_children,
                    })

            if not tree_nodes:
                print("⚠️ WARNING! Canary Miner catalog did not contain any selectable entries.")
                return None

            return show_factory_image_dialog(
                self,
                _("Canary Miner Catalog"),
                _("Select a Canary or Beta factory image:"),
                _("Catalog"),
                tree_nodes,
            )
        except Exception as e:
            print(f"Error selecting Canary catalog entry: {e}")
            traceback.print_exc()
            return None

    # -----------------------------------------------
    #          process_factory_image_selection
    # -----------------------------------------------
    def process_factory_image_selection(self, image_url, source_label):
        try:
            if not image_url:
                print(f"⚠️ WARNING! No download URL available for {source_label} factory image selection.")
                return False

            fingerprint, security_patch = url2fpsp(image_url, "factory")
            if fingerprint is None or security_patch is None:
                debug(f"Failed to get fingerprint and security patch from partial {image_url}\nTrying the full image ...")
                override_size_limit = get_size_from_url(image_url)
                if override_size_limit is not None:
                    self.console_stc.SetValue(f"{self.console_stc.GetValue()}\n⚠️ Downloading full {source_label} factory image {override_size_limit} bytes ...\nThis may take quite a while ...")
                    wx.Yield()
                    fingerprint, security_patch = url2fpsp(image_url, "factory", override_size_limit)

            if fingerprint and security_patch:
                print(f"Security Patch:           {security_patch}")
                pattern = r'([^\/]*)\/([^\/]*)\/([^:]*)[:]([^\/]*)\/([^\/]*)\/([^:]*)[:]([^\/]*)\/([^\/]*)$'
                match = re.search(pattern, fingerprint)
                if match and match.lastindex == 8:
                    product = match[2]
                    device = match[3]
                    latest_version = match[4]
                    build_id = match[5]
                    incremental = match[6]
                    build_type = match[7]
                    build_tags = match[8]
                    device_data = get_android_devices()
                    model = None
                    with contextlib.suppress(Exception):
                        model = device_data[device]['device']
                        # if model starts with "Google ", remove that part
                        if model.startswith("Google "):
                            model = model[7:]
                    pif_data = {
                        "MANUFACTURER": "Google",
                        "MODEL": model,
                        "FINGERPRINT": f"google/{product}/{device}:{latest_version}/{build_id}/{incremental}:{build_type}/{build_tags}",
                        "PRODUCT": product,
                        "DEVICE": device,
                        "SECURITY_PATCH": security_patch,
                        "DEVICE_INITIAL_SDK_INT": "32"
                    }
                    json_string = json.dumps(pif_data, indent=4) + "\n"
                    if self.pif_format == 'prop':
                        self.console_stc.SetValue(self.J2P(json_string))
                    else:
                        self.console_stc.SetValue(json_string)
                    print(f"{source_label} Pixel Beta Profile/Fingerprint:\n{json_string}")
                    return True

            print(f"⚠️ WARNING! Failed to create fingerprint from {source_label.lower()} factory image.")
            wx.CallAfter(self.console_stc.SetValue, _("Failed to get beta print."))
            return False
        except Exception as e:
            print(f"⚠️ WARNING! Exception while processing {source_label.lower()} factory image: {e}")
            traceback.print_exc()
            wx.CallAfter(self.console_stc.SetValue, _("Failed to get beta print."))
            return False

    # -----------------------------------------------
    #                  onPlayIntegrityCheck
    # -----------------------------------------------
    def onPlayIntegrityCheck(self, e):
        try:
            device = get_phone(True)
            if not device:
                return
            if not device.rooted:
                return
            if wx.GetKeyState(wx.WXK_CONTROL):
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Play Integrity API Checker with clear option.")
                clear_first = True
            else:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Play Integrity API Checker.")
                clear_first = False
            self._on_spin('start')

            if not self.insync:
                self.toast(_("Active pif not in sync"), _("⚠️ WARNING! Device pif is not in sync with Active Pif contents.\nThe result will not be reflective of the Active pif you're viewing."))

            # We need to kill TB Checker , Play Store and YASNAC to make sure we read fresh values
            if self.pi_option.StringSelection in ['Android Integrity Checker', 'TB Checker', 'Play Store', 'YASNAC']:
                res = device.perform_package_action(self.pi_app, 'kill', False)

            # launch the app
            res = device.perform_package_action(self.pi_app, self.launch_method, False)
            if res == -1:
                print(f"Error: during launching app {self.pi_app}.")
                return -1

            # See if we have coordinates saved
            coords = self.coords.query_entry(device.id, self.pi_app)
            coord_dismiss = None
            if coords is None or clear_first:
                if self.disable_uiautomator_checkbox.IsChecked():
                    print(f"⚠️ WARNING! You have disabled using UIAutomator.\nPlease uncheck Disable UIAutomator checkbox if you want to enable UIAutomator usage.")
                    return
                # For Play Store, we need to save multiple coordinates
                if self.pi_option.StringSelection == 'Play Store':
                    # Get coordinates for the first time
                    # user
                    coord_user = self.get_pi_app_coords(child='user')
                    if coord_user == -1:
                        print(f"Error: during tapping {self.pi_app} [user] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "user", coord_user)

                    # settings
                    coord_settings = self.get_pi_app_coords(child='settings')
                    if coord_settings == -1:
                        print(f"Error: during tapping {self.pi_app} [settings] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "settings", coord_settings)

                    # general
                    coord_general = self.get_pi_app_coords(child='general')
                    if coord_general == -1:
                        print(f"Error: during tapping {self.pi_app} [general] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "general", coord_general)
                    # page scroll
                    coord_scroll = self.get_pi_app_coords(child='scroll')
                    if coord_scroll == -1:
                        print(f"Error: during swiping {self.pi_app} [scroll] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "scroll", coord_scroll)
                    # Developer Options
                    coord_developer_options = self.get_pi_app_coords(child='developer_options')
                    if coord_developer_options == -1:
                        print(f"Error: during tapping {self.pi_app} [developer_options] screen.\nPossibly swipe failed.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "developer_options", coord_developer_options)
                    # Check Integrity
                    coord_test = self.get_pi_app_coords(child='test')
                    if coord_test == -1:
                        print(f"Error: during tapping {self.pi_app} [Check Integrity] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "test", coord_test)
                    coords = coord_test
                else:
                    # Get coordinates for the first time
                    coords = self.get_pi_app_coords()
                    if coords is not None and coords != -1:
                        # update coords.json
                        self.coords.update_entry(device.id, self.pi_app, coords)
                    else:
                        print("Error: Could not get coordinates.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        return -1
            elif self.pi_option.StringSelection == 'Play Store':
                coord_user = self.coords.query_nested_entry(device.id, self.pi_app, "user")
                coord_settings = self.coords.query_nested_entry(device.id, self.pi_app, "settings")
                coord_general = self.coords.query_nested_entry(device.id, self.pi_app, "general")
                coord_scroll = self.coords.query_nested_entry(device.id, self.pi_app, "scroll")
                coord_developer_options = self.coords.query_nested_entry(device.id, self.pi_app, "developer_options")
                coord_test = self.coords.query_nested_entry(device.id, self.pi_app, "test")
                coord_dismiss = self.coords.query_nested_entry(device.id, self.pi_app, "dismiss")
                if coord_user is None or coord_user == '' or coord_settings is None or coord_settings == '' or coord_general is None or coord_general == '' or coord_developer_options is None or coord_developer_options == '' or coord_test is None or coord_test == '':
                    print(f"\nError: coordinates for {self.pi_app} is missing from settings\nPlease run the test again so that PixelFlasher can try to get fresh new coordinates.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1

                # user
                res = device.click(coord_user)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [user] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1
                time.sleep(1)
                # settings
                res = device.click(coord_settings)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [settings] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1
                time.sleep(1)
                # general
                res = device.click(coord_general)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [general] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1
                time.sleep(1)
                res = device.swipe(coord_scroll)
                if res == -1:
                    print(f"Error: during swiping {self.pi_app} [scroll] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1
                time.sleep(1)
                # developer_options
                res = device.click(coord_developer_options)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [developer_options] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    return -1
                time.sleep(1)
                # test
                coords = coord_test

            # Click on coordinates
            res = device.click(coords)
            if res == -1:
                print(f"\nError: coordinates for {self.pi_app} is missing from settings\nPlease run the test again so that PixelFlasher can try to get fresh new coordinates.")
                if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                    del self.coords.data[device.id][self.pi_app]
                    self.coords.save_data()
                return -1

            # Skip Getting results if UIAutomator is disabled.
            if not self.disable_uiautomator_checkbox.IsChecked():
                # pull view
                config_path = get_config_path()
                pi_xml = os.path.join(config_path, 'tmp', 'pi.xml')
                print("Sleeping 10 seconds to get the results ...")
                time.sleep(5)

                if self.pi_option.StringSelection == 'Android Integrity Checker':
                    device.swipe_up(percentage=20)

                res = device.ui_action('/data/local/tmp/pi.xml', pi_xml)
                if res == -1:
                    print(f"Error: during uiautomator {self.pi_app}.")
                    return -1

                # extract result
                if self.pi_option.StringSelection == 'Play Integrity API Checker':
                    res = process_pi_xml_piac(pi_xml)
                if self.pi_option.StringSelection == 'Simple Play Integrity Checker':
                    res = process_pi_xml_spic(pi_xml)
                if self.pi_option.StringSelection == 'TB Checker':
                    res = process_pi_xml_tb(pi_xml)
                if self.pi_option.StringSelection == 'Android Integrity Checker':
                    res = process_pi_xml_aic(pi_xml)
                if self.pi_option.StringSelection == 'Play Store':
                    res = process_pi_xml_ps(pi_xml)
                    # dismiss
                    if coord_dismiss is None or coord_dismiss == '' or coord_dismiss == -1:
                        coord_dismiss = self.get_pi_app_coords(child='dismiss')
                        if coord_dismiss == -1:
                            print(f"Error: getting coordinates for {self.pi_app} [dismiss] screen.")
                            if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                                del self.coords.data[device.id][self.pi_app]['dismiss']
                                self.coords.save_data()
                        self.coords.update_nested_entry(device.id, self.pi_app, "dismiss", coord_dismiss)
                if self.pi_option.StringSelection == 'YASNAC':
                    res = process_pi_xml_yasnac(pi_xml)

                if res == -1:
                    print(f"Error: during processing the response from {self.pi_app}.")
                    return -1

                self.console_stc.SetValue('')
                if res is None or res == '':
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]['dismiss']
                else:
                    self.console_stc.SetValue(res)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during Play Integrity API Check process.")
            traceback.print_exc()
        finally:
            if device:
                res = device.delete("/data/local/tmp/pi.xml", device.rooted)
            self._on_spin('stop')

    # -----------------------------------------------
    #                  sort_prop
    # -----------------------------------------------
    def sort_prop(self, file_path):
        filename = os.path.basename(file_path)
        if filename == "build.prop":
            return 1
        elif filename == "system-build.prop":
            return 2
        elif filename == "system.prop":
            return 3
        elif filename == "product-build.prop":
            return 4
        elif filename == "product.prop":
            return 5
        elif filename == "vendor-build.prop":
            return 6
        elif filename == "vendor.prop":
            return 7
        else:
            return 999

    # -----------------------------------------------
    #                  onProcessBuildProps
    # -----------------------------------------------
    def onProcessBuildProps(self, e):
        # sourcery skip: dict-assign-update-to-union
        try:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User pressed Process build.prop")
            wildcard = "Property files (*.prop)|*.prop|All files (*.*)|*.*"
            dialog = wx.FileDialog(self, _("Choose property files to open"), wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)

            if dialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled file selection.")
                return

            paths = dialog.GetPaths()
            dialog.Destroy()
            sorted_paths = sorted(paths, key=self.sort_prop)

            print(f"Selected files: {sorted_paths}")

            self._on_spin('start')
            self.process_props(sorted_paths)
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onProcessBuildProps function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  process_props
    # -----------------------------------------------
    def process_props(self, prop_files):
        # sourcery skip: dict-assign-update-to-union
        try:
            processed_dict = {}
            for pathname in reversed(prop_files):
                with open(pathname, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    content = f.readlines()

                contentList = [x.strip().split('#')[0].split('=', 1) for x in content if '=' in x.split('#')[0]]
                contentDict = dict(contentList)

                # Update processed_dict with entries from the current file
                # In place Union operator below fails on Windows 2019 build, so use the update method instead.
                # processed_dict |= contentDict
                processed_dict.update(contentDict)

                # Apply the substitution to the values in processed_dict
                for k, v in contentDict.items():
                    for x in v.split('$')[1:]:
                        key = re.findall(r'\w+', x)[0]
                        v = v.replace(f'${key}', processed_dict[key])
                    processed_dict[k] = v.strip()

            # if running in debugger
            if not getattr( sys, 'frozen', False ):
                # save processed_dict to a file
                config_path = get_config_path()
                processed_dict_file = os.path.join(config_path, 'tmp', 'processed_dict.json')
                with open(processed_dict_file, 'w') as f:
                    json.dump(processed_dict, f, indent=4)

            donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=self.first_api, keep_all=self.keep_unknown)
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(donor_json_string))
            else:
                self.console_stc.SetValue(donor_json_string)
            # print(donor_json_string)

            # Auto Update print
            if self.auto_update_pif_checkbox.IsEnabled() and self.auto_update_pif_checkbox.IsChecked():
                self.active_pif_stc.SetValue(self.console_stc.GetValue())
                self.UpdatePifJson(None)

            # Auto run migrate if enabled
            if self.auto_run_migrate_checkbox.IsEnabled() and self.auto_run_migrate_checkbox.IsChecked():
                print("Auto Migrating ...")
                self.runMigrate()

            # Auto test Play Integrity
            if self.auto_update_pif_checkbox.IsEnabled() and self.auto_update_pif_checkbox.IsChecked():
                if self.auto_check_pi_checkbox.IsEnabled() and self.auto_check_pi_checkbox.IsChecked():
                    print("Auto Testing Play Integrity ...")
                    self.onPlayIntegrityCheck(None)

        except Exception:
            print(f"Cannot process file: '{pathname}'.")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onProcessImage
    # -----------------------------------------------
    def onProcessImage(self, e):
        try:
            file_dialog = wx.FileDialog(self, _("Select a Device Image"), wildcard="Device image files (*.img;*.zip)|*.img;*.zip")
            if file_dialog.ShowModal() == wx.ID_OK:
                file_path = file_dialog.GetPath()
                self._on_spin('start')
                wx.CallAfter(self.console_stc.SetValue, _("Processing %s ...\nPlease be patient this could take some time ...") % file_path)
                props_dir = get_pif_from_image(file_path)
                # prop_files = get files from the props_dir (single level) and store them in a list
                if props_dir:
                    prop_files = [os.path.join(props_dir, f) for f in os.listdir(props_dir) if os.path.isfile(os.path.join(props_dir, f))]
                    self.process_props(prop_files)
                else:
                    wx.CallAfter(self.console_stc.SetValue, _("Image format not supported"))
                    self.console_stc.Refresh()
                    self.console_stc.Update()
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onProcessImage function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onProcessBulkProps
    # -----------------------------------------------
    def onProcessBulkProps(self, e):
        # sourcery skip: dict-assign-update-to-union
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User pressed Process build.props Folder")

        with wx.DirDialog(self, _("Select folder to bulk process props files"), style=wx.DD_DEFAULT_STYLE) as folderDialog:
            if folderDialog.ShowModal() == wx.ID_CANCEL:
                print("User cancelled folder selection.")
                return
            selected_folder = folderDialog.GetPath()

        try:
            self._on_spin('start')
            prop_files = [file for file in os.listdir(selected_folder) if file.endswith(".prop")]
            for prop in prop_files:
                prop_path = os.path.join(selected_folder, prop)
                processed_dict = {}
                with open(prop_path, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    content = f.readlines()

                contentList = [x.strip().split('#')[0].split('=', 1) for x in content if '=' in x.split('#')[0]]
                contentDict = dict(contentList)

                # Update processed_dict with entries from the current file
                # In place Union operator below fails on Windows 2019 build, so use the update method instead.
                # processed_dict |= contentDict
                processed_dict.update(contentDict)

                # Apply the substitution to the values in processed_dict
                for k, v in contentDict.items():
                    for x in v.split('$')[1:]:
                        key = re.findall(r'\w+', x)[0]
                        v = v.replace(f'${key}', processed_dict[key])
                    processed_dict[k] = v.strip()

                json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=self.first_api, keep_all=self.keep_unknown)

                # not needed if we don't want to auto-fill first api
                json_dict = json5.loads(json_string)
                keys = ['FIRST_API_LEVEL', 'DEVICE_INITIAL_SDK_INT', '*api_level', 'ro.product.first_api_level']
                first_api = get_first_match(json_dict, keys)
                json_string = json.dumps(json_dict, indent=4, sort_keys=self.sort_keys)
                processed_dict = self.load_json_with_rules(json_string, self.keep_unknown)
                if first_api == '':
                    donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=self.first_api_value, sort_data=self.sort_keys)
                else:
                    donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=None, sort_data=self.sort_keys)

                # save json file
                json_path = os.path.splitext(prop_path)[0] + ".json"
                with open(json_path, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
                    f.write(donor_json_string)

        except Exception:
            print(f"Cannot process file: '{selected_folder}'.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  ConsoleStcChange
    # -----------------------------------------------
    def ConsoleStcChange(self, event):
        try:
            console_data = self.console_stc.GetValue()
            json_data = None
            if console_data:
                if self.pif_format == 'prop':
                    json_data = self.P2J(console_data)
                else:
                    json_data = console_data

            if json_data:
                try:
                    json.loads(json_data)
                    self.smart_paste_up.Enable(True)
                    self.paste_up.Enable(True)
                except Exception:
                    try:
                        json5.loads(json_data)
                        self.smart_paste_up.Enable(True)
                        self.paste_up.Enable(True)
                    except Exception:
                        self.smart_paste_up.Enable(False)
                        self.paste_up.Enable(False)
            else:
                self.smart_paste_up.Enable(False)
                self.paste_up.Enable(False)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in ConsoleStcChange function")
            traceback.print_exc()
        if event:
            event.Skip()

    # -----------------------------------------------
    #                  ActivePifStcChange
    # -----------------------------------------------
    def ActivePifStcChange(self, event):
        # Allow the default event handler to run first
        if event:
            event.Skip()

        # Use debounced validation to avoid performance issues during typing
        if self._validation_timer is not None:
            self._validation_timer.Stop()

        # Delay validation by 500ms to allow for smooth typing
        self._validation_timer = wx.CallLater(500, self.process_active_pif_updated_value)

    # -----------------------------------------------
    #          process_active_pif_updated_value
    # -----------------------------------------------
    def process_active_pif_updated_value(self):
        try:
            active_data = self.active_pif_stc.GetValue()
            json_data = ''
            if active_data:
                if self.pif_format == 'prop':
                    json_data = self.P2J(active_data)
                else:
                    json_data = active_data

            if not self.enable_buttons:
                self.create_pif_button.Enable(False)
                self.push_pif_button.Enable(False)
                return

            if json_data:
                try:
                    json.loads(json_data)
                    self.paste_down.Enable(True)
                    self.reprocess.Enable(True)
                    if "Targeted Fix" not in self.pif_selection_combo.StringSelection:
                        self.create_pif_button.Enable(True)
                        self.push_pif_button.Enable(True)
                    self.favorite_pif_button.Enable(True)
                    self.save_pif_button.Enable(True)
                except Exception:
                    try:
                        json5.loads(json_data)
                        self.paste_down.Enable(True)
                        self.reprocess.Enable(True)
                        self.create_pif_button.Enable(True)
                        self.push_pif_button.Enable(True)
                        self.favorite_pif_button.Enable(True)
                        self.save_pif_button.Enable(True)
                    except Exception:
                        self.create_pif_button.Enable(False)
                        self.push_pif_button.Enable(False)
                        self.reprocess.Enable(False)
                        self.paste_down.Enable(False)
                        self.favorite_pif_button.Enable(False)
                        self.save_pif_button.Enable(False)
            else:
                self.paste_down.Enable(False)
                self.create_pif_button.Enable(False)
                self.push_pif_button.Enable(False)
                self.reprocess.Enable(False)
                self.favorite_pif_button.Enable(False)
                self.save_pif_button.Enable(False)

            if self.pif_format == 'prop':
                compare_data = self.P2J(self.device_pif)
            else:
                compare_data = self.device_pif
            if json_data != compare_data:
                self.pif_modified_image.SetBitmap(images.alert_red_24.GetBitmap())
                self.pif_modified_image.SetToolTip(_("The contents is different than what is currently on the device.\nUpdate the print before testing."))
                self.insync = False
            else:
                self.pif_modified_image.SetBitmap(images.alert_gray_24.GetBitmap())
                self.pif_modified_image.SetToolTip(_("Active pif is not modified."))
                self.insync = True

            # Check if we should update favorite status (either create button enabled or TargetedFix module)
            is_pif_create_update_enabled = self.create_pif_button.Enabled
            is_targetedfix_module = (
                                        hasattr(self, 'current_pif_module') and
                                        self.current_pif_module and
                                        getattr(self.current_pif_module, 'id', None) == "targetedfix"
                                    )
            is_favorite_enabled = self.favorite_pif_button.Enabled

            if (is_pif_create_update_enabled or is_targetedfix_module) and is_favorite_enabled:
                sorted_json_data = json.dumps(json5.loads(json_data), indent=4, sort_keys=True)
                pif_hash = json_hexdigest(sorted_json_data)
                if pif_hash in self.favorite_pifs:
                    self.favorite_pif_button.SetBitmap(images.heart_red_24.GetBitmap())
                    self.favorite_pif_button.SetToolTip(_("Active pif is saved in favorites."))
                    self.update_combo_box(pif_hash)
                else:
                    self.favorite_pif_button.SetBitmap(images.heart_gray_24.GetBitmap())
                    self.favorite_pif_button.SetToolTip(_("Active pif is not saved in favorites."))

            # Update TargetedFix button states if applicable
            if is_targetedfix_module:
                self.update_tf_button_states()

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in ActivePifStcChange function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  update_combo_box
    # -----------------------------------------------
    def update_combo_box(self, pif_hash=None):
        try:
            pif_labels = [pif["label"] for pif in self.favorite_pifs.values()]
            self.pif_combo_box.SetItems(pif_labels)

            # temporarily unbind so that we don't trigger another ActivePifStcChange with the combo box selection
            self.active_pif_stc.Unbind(wx.stc.EVT_STC_CHANGE, handler=self.ActivePifStcChange)
            # Make the combo box selection
            if pif_hash is None:
                self.pif_combo_box.SetSelection(-1)
            else:
                label = self.favorite_pifs[pif_hash]["label"]
                index = self.pif_combo_box.FindString(label)
                if index != wx.NOT_FOUND:
                    self.pif_combo_box.SetSelection(index)
                else:
                    self.pif_combo_box.SetSelection(-1)
            # rebind the event
            self.active_pif_stc.Bind(wx.stc.EVT_STC_CHANGE, self.ActivePifStcChange)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in update_combo_box function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onSmartPasteUp
    # -----------------------------------------------
    def onSmartPasteUp(self, event):
        try:
            print("Smart pasting up the console content ...")
            self._on_spin('start')
            console_data = self.console_stc.GetValue()
            json_string = None
            if console_data:
                if self.pif_format == 'prop':
                    json_string = self.P2J(console_data)
                else:
                    json_string = console_data

            json_dict = json5.loads(json_string)
            keys = ['FIRST_API_LEVEL', 'DEVICE_INITIAL_SDK_INT', '*api_level', 'ro.product.first_api_level']
            first_api = get_first_match(json_dict, keys)
            json_string = json.dumps(json_dict, indent=4, sort_keys=self.sort_keys)
            processed_dict = self.load_json_with_rules(json_string, self.pif_flavor)
            if self.force_first_api_checkbox.IsChecked():
                donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=str(self.first_api_value), sort_data=self.sort_keys, keep_all=self.keep_unknown)
            else:
                donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=first_api, sort_data=self.sort_keys, keep_all=self.keep_unknown)
            if self.pif_format == 'prop':
                self.active_pif_stc.SetValue(self.J2P(donor_json_string))
            else:
                self.active_pif_stc.SetValue(donor_json_string)

            # Auto Update print
            if self.auto_update_pif_checkbox.IsEnabled() and self.auto_update_pif_checkbox.IsChecked():
                self.UpdatePifJson(None)

                # Auto run migrate if enabled
                if self.auto_run_migrate_checkbox.IsEnabled() and self.auto_run_migrate_checkbox.IsChecked():
                    print("Auto Migrating ...")
                    self.runMigrate()

            # Auto test Play Integrity
            if self.auto_update_pif_checkbox.IsEnabled() and self.auto_update_pif_checkbox.IsChecked():
                if self.auto_check_pi_checkbox.IsEnabled() and self.auto_check_pi_checkbox.IsChecked():
                    print("Auto Testing Play Integrity ...")
                    self.onPlayIntegrityCheck(None)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onSmartPasteUp function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')
            if event:
                event.Skip()

    # -----------------------------------------------
    #                  onPasteUp
    # -----------------------------------------------
    def onPasteUp(self, event):
        self.active_pif_stc.SetValue(self.console_stc.GetValue())
        event.Skip()

    # -----------------------------------------------
    #                  onPasteDown
    # -----------------------------------------------
    def onPasteDown(self, event):
        self.console_stc.SetValue(self.active_pif_stc.GetValue())
        event.Skip()

    # -----------------------------------------------
    #                  onAddMissingKeysFromDevice
    # -----------------------------------------------
    def onAddMissingKeysFromDevice(self, event):
        self.add_missing_keys_checkbox = event.GetEventObject()
        status = self.add_missing_keys_checkbox.GetValue()
        print(f"Add Missing Keys is set to: {status}")
        self.config.pif['auto_fill'] = status

    # -----------------------------------------------
    #                  onSortKeys
    # -----------------------------------------------
    def onSortKeys(self, event):
        self.sort_keys_checkbox = event.GetEventObject()
        status = self.sort_keys_checkbox.GetValue()
        self.sort_keys = status
        self.config.pif['sort_keys'] = status

    # -----------------------------------------------
    #                  onKeepAllKeys
    # -----------------------------------------------
    def onKeepAllKeys(self, event):
        self.keep_unknown_checkbox = event.GetEventObject()
        status = self.keep_unknown_checkbox.GetValue()
        self.keep_unknown = status
        self.config.pif['keep_unknown'] = status

    # -----------------------------------------------
    #                  onSpoofBuild
    # -----------------------------------------------
    def onSpoofBuild(self, event):
        self.spoofBuild_checkbox = event.GetEventObject()
        status = self.spoofBuild_checkbox.GetValue()
        self.spoofBuild = status
        self.config.pif['spoofBuild'] = status

    # -----------------------------------------------
    #                  onSpoofProps
    # -----------------------------------------------
    def onSpoofProps(self, event):
        self.spoofProps_checkbox = event.GetEventObject()
        status = self.spoofProps_checkbox.GetValue()
        self.spoofProps = status
        self.config.pif['spoofProps'] = status

    # -----------------------------------------------
    #                  onApiValueChange
    # -----------------------------------------------
    def onApiValueChange(self, event):
        try:
            self.first_api_value = int(self.api_value_input.GetValue())
            self.config.pif['first_api_value_when_forced'] = self.first_api_value
            self.force_first_api_checkbox.SetToolTip(f"Forces First API value(s) to {self.first_api_value}")
        except ValueError:
            # Handle the case where the input is not a valid integer
            pass

    # -----------------------------------------------
    #                  onSpoofProvider
    # -----------------------------------------------
    def onSpoofProvider(self, event):
        self.spoofProvider_checkbox = event.GetEventObject()
        status = self.spoofProvider_checkbox.GetValue()
        self.spoofProvider = status
        self.config.pif['spoofProvider'] = status

    # -----------------------------------------------
    #                  onSpoofSignature
    # -----------------------------------------------
    def onSpoofSignature(self, event):
        self.spoofSignature_checkbox = event.GetEventObject()
        status = self.spoofSignature_checkbox.GetValue()
        self.spoofSignature = status
        self.config.pif['spoofSignature'] = status

    # -----------------------------------------------
    #                  onSpoofVendingSdk
    # -----------------------------------------------
    def onSpoofVendingSdk(self, event):
        self.spoofVendingSdk_checkbox = event.GetEventObject()
        status = self.spoofVendingSdk_checkbox.GetValue()
        self.spoofVendingSdk = status
        self.config.pif['spoofVendingSdk'] = status

    # -----------------------------------------------
    #                  onSpoofVendingFinger
    # -----------------------------------------------
    def onSpoofVendingFinger(self, event):
        self.spoofVendingFinger_checkbox = event.GetEventObject()
        status = self.spoofVendingFinger_checkbox.GetValue()
        self.spoofVendingFinger = status
        self.config.pif['spoofVendingFinger'] = status

    # -----------------------------------------------
    #                  onForceFirstAPI
    # -----------------------------------------------
    def onForceFirstAPI(self, event):
        self.force_first_api_checkbox = event.GetEventObject()
        status = self.force_first_api_checkbox.GetValue()
        print(f"Force First API is set to: {status}")
        self.config.pif['force_first_api'] = status
        if status:
            self.first_api = self.first_api_value
        else:
            self.first_api = None

    # -----------------------------------------------
    #                  onAutoUpdatePrint
    # -----------------------------------------------
    def onAutoUpdatePrint(self, event):
        self.auto_update_pif_checkbox = event.GetEventObject()
        status = self.auto_update_pif_checkbox.GetValue()
        print(f"Auto Update print is set to: {status}")
        self.config.pif['auto_update_pif_json'] = status

    # -----------------------------------------------
    #                  onAutoCheckPlayIntegrity
    # -----------------------------------------------
    def onAutoCheckPlayIntegrity(self, event):
        self.auto_check_pi_checkbox = event.GetEventObject()
        status = self.auto_check_pi_checkbox.GetValue()
        print(f"Auto Check Play Integrity is set to: {status}")
        self.config.pif['auto_check_play_integrity'] = status

    # -----------------------------------------------
    #                  onAutoRunMigrate
    # -----------------------------------------------
    def onAutoRunMigrate(self, event):
        self.auto_run_migrate_checkbox = event.GetEventObject()
        status = self.auto_run_migrate_checkbox.GetValue()
        print(f"Auto run migrate.sh is set to: {status}")
        self.config.pif['auto_run_migrate'] = status

    # -----------------------------------------------
    #                  runMigrate
    # -----------------------------------------------
    def runMigrate(self):
        try:
            print("Migrating pif to the latest Pifork format ...")
            device = get_phone(True)
            if not device.rooted:
                return
            if device:
                exec_cmd = "/data/adb/modules/playintegrityfix/migrate.sh -f"
                debug(f"exec_cmd: {exec_cmd}")
                res = device.exec_cmd(exec_cmd, True)
                if res:
                    print(res)

                self.LoadPif(self.pif_path)
            else:
                print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: device is not accessible.")
                return
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in runMigrate function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onE2J
    # -----------------------------------------------
    def onE2J(self, event):
        try:
            self._on_spin('start')
            self.console_stc.SetValue(self.P2J(self.console_stc.GetValue()))
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onE2J function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onJ2E
    # -----------------------------------------------
    def onJ2E(self, event):
        try:
            self._on_spin('start')
            self.console_stc.SetValue(self.J2P(self.console_stc.GetValue()))
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onJ2E function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  P2J
    # -----------------------------------------------
    def P2J(self, prop_str, sort_keys=None):
        try:
            if prop_str == '':
                return ''
            if is_valid_json(prop_str):
                # debug(f"Contents is already in json format.")
                return prop_str
            if sort_keys is None:
                sort_keys = self.sort_keys

            contentList = []
            # Split the input string into lines
            lines = re.split(r'\r\n|\n', prop_str)
            for line in lines:
                # Strip whitespace and split by '#' to remove comments
                stripped_line = line.strip().split('#')[0]
                # Check if the line contains an '=' character split into key value pair
                if '=' in stripped_line:
                    key_value_pair = stripped_line.split('=', 1)
                    contentList.append(key_value_pair)

            contentDict = dict(contentList)
            for k, v in contentList:
                for x in v.split('$')[1:]:
                    key = re.findall(r'\w+', x)[0]
                    v = v.replace(f'${key}', contentDict[key])
                contentDict[k] = v.strip()
            return json.dumps(contentDict, indent=4, sort_keys=sort_keys)
        except Exception:
            traceback.print_exc()

    # -----------------------------------------------
    #                  J2P
    # -----------------------------------------------
    def J2P(self, json_str, quiet=False):
        try:
            contentDict = json.loads(json_str)
        except Exception:
            try:
                contentDict = json5.loads(json_str)
            except Exception:
                if not quiet:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Not a valid json.")
                return json_str

        try:
            contentList = []
            for k, v in contentDict.items():
                if v:
                    contentList.append(f"{k}={v}")
            # Ensure Unix line endings
            key_value_format = "\n".join(contentList) + "\n"
            return key_value_format
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in J2P function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onEditTFTargets
    # -----------------------------------------------
    def onEditTFTargets(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated editing TargetedFix target.txt file.")
        print("==============================================================================")
        if self.tf_target_path:
            # Use the local tf_target.txt file instead of pulling from device
            config_path = get_config_path()
            local_target_file = os.path.join(config_path, 'tmp', 'tf_target.txt')

            # Ensure local file exists
            if not os.path.exists(local_target_file):
                with open(local_target_file, 'w', encoding='utf-8') as f:
                    f.write('')

            res = self.edit_local_file(local_target_file, self.tf_target_path)
            if res == 0:
                self.load_tf_targets()
        if event:
            event.Skip()

    # -----------------------------------------------
    #                  onEditTSTarget
    # -----------------------------------------------
    def onEditTSTarget(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated editing Tricky Store target.txt file.")
        print("==============================================================================")
        self.edit_file("/data/adb/tricky_store/target.txt")
        event.Skip()

    # -----------------------------------------------
    #                  onEditTSSP
    # -----------------------------------------------
    def onEditTSSP(self, event):
        print("\n==============================================================================")
        print(f" {datetime.now():%Y-%m-%d %H:%M:%S} User initiated editing Tricky Store security_patch.txt file.")
        print("==============================================================================")
        self.edit_file("/data/adb/tricky_store/security_patch.txt")
        event.Skip()

    # -----------------------------------------------
    #                  edit_local_file
    # -----------------------------------------------
    def edit_local_file(self, local_file_path, remote_file_path):
        try:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Edit local file: {local_file_path}.")

            # Show the file in the editor
            dlg = FileEditor(self, local_file_path, "text", width=1500, height=600)
            dlg.CenterOnParent()
            result = dlg.ShowModal()
            dlg.Destroy()

            if result == wx.ID_OK:
                # get the contents of modified file
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    contents = f.read()

                # push the file back to the device
                device = get_phone(True)
                if device and device.rooted:
                    res = device.push_file(local_file_path, remote_file_path, True)
                    if res != 0:
                        print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pushing the updated {remote_file_path} file. ...\n")
                        return -1

                    print(f"\nTargetedFix {remote_file_path} file has been modified!")
                    print(f"The updated file:")
                    print(f"___________________________________________________\n{contents}")
                    print("___________________________________________________\n")
                    return 0
            else:
                print(f"User cancelled editing {local_file_path} file.")
                return -1

        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function edit_local_file.")
            traceback.print_exc()
            return -1

    # -----------------------------------------------
    #                  edit_file
    # -----------------------------------------------
    def edit_file(self, filename):
        try:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Edit Tricky Store file: {filename}.")
            device = get_phone(True)
            if not device.rooted:
                return
            self._on_spin('start')
            config_path = get_config_path()
            # get the file portion from full path
            just_filename = os.path.basename(filename)
            ts_target_file = os.path.join(config_path, 'tmp', just_filename)
            # pull the file
            res = device.pull_file(filename, ts_target_file, True)
            if res != 0:
                debug(f"file: {filename} not found,\n")
                # create an empty ts_target_file
                with open(ts_target_file, 'w', encoding='ISO-8859-1', errors="replace") as f:
                    f.write('')
                print(f"An empty local {just_filename} file has been created.")
            # get the contents of the file
            encoding = detect_encoding(ts_target_file)
            with open(ts_target_file, 'r', encoding=encoding, errors="replace") as f:
                contents = f.read()
                self.device_pif = contents

            self._on_spin('stop')
            # Show the file in the editor
            dlg = FileEditor(self, ts_target_file, "text", width=1500, height=600)
            dlg.CenterOnParent()
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                # get the contents of modified ts_target_file
                with open(ts_target_file, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    contents = f.read()
                # push the file back to the device
                res = device.push_file(ts_target_file, filename, True)
                if res != 0:
                    print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error while pushing the updated {filename} file. ...\n")
                    return
                print(f"\nTricky Store {filename} file has been modified!")
                print(f"The updated {filename}:")
                print(f"___________________________________________________\n{contents}")
                print("___________________________________________________\n")
            else:
                print(f"User cancelled editing Tricky Store {filename} file.")
                return -1
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function edit_file.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onPushKeybox
    # -----------------------------------------------
    def onPushKeybox(self, event):
        try:
            with wx.FileDialog(self, _("Select keybox to push"), '', '', wildcard="Keybox files (*.xml)|*.xml", style=wx.FD_OPEN) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    print("User cancelled keybox push.")
                    return
                selected_file = fileDialog.GetPath()

            self._on_spin('start')
            device = get_phone()
            if device:
                # push the file
                res = device.push_file(selected_file, "/data/adb/tricky_store/keybox.xml", True)
                if res != 0:
                    print(f"Return Code: {res.returncode}")
                    print(f"Stdout: {res.stdout}")
                    print(f"Stderr: {res.stderr}")
                    print("Aborting ...\n")
                    return -1
        except Exception as e:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an error in function onPushKeybox.")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  onDisableUIAutomator
    # -----------------------------------------------
    def onDisableUIAutomator(self, event):
        self.disable_uiautomator_checkbox = event.GetEventObject()
        status = self.disable_uiautomator_checkbox.GetValue()
        print(f"Disable UIAutomator is set to: {status}")
        self.config.pif['disable_uiautomator'] = status

    # -----------------------------------------------
    #                  load_json_with_rules
    # -----------------------------------------------
    def load_json_with_rules(self, json_str, keep_unknown=False):
        try:
            if self.pif_format == 'prop':
                json_data = self.P2J(json_str)
            else:
                json_data = json_str

            if json_str == '':
                return ''

            # Load JSON string into a dictionary
            data = json5.loads(json_data)

            # Define the mapping rules
            mapping_rules = {
                "MANUFACTURER": "ro.product.manufacturer",
                "MODEL": "ro.product.model",
                "FINGERPRINT": "ro.build.fingerprint",
                "BRAND": "ro.product.brand",
                "PRODUCT": "ro.product.name",
                "DEVICE": "ro.product.device",
                "SECURITY_PATCH": "ro.build.version.security_patch",
                "*.security_patch": "ro.build.version.security_patch",
                "FIRST_API_LEVEL": "ro.product.first_api_level",
                "*api_level": "ro.product.first_api_level",
                "BUILD_ID": "ro.build.id",
                "ID": "ro.build.id",
                "VNDK_VERSION": "ro.vndk.version",
                "*.vndk_version": "ro.vndk.version",
                "INCREMENTAL": "ro.build.version.incremental",
                "TYPE": "ro.build.type",
                "TAGS": "ro.build.tags",
                "RELEASE": "ro.build.version.release"
            }

            # Create a new dictionary with the modified keys
            modified_data = {mapping_rules.get(key, key): value for key, value in data.items()}

            # Discard keys with empty values if the keep_unknown is not set
            if not keep_unknown:
                modified_data = {key: value for key, value in modified_data.items() if value != ""}

            return modified_data
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in load_json_with_rules function")
            traceback.print_exc()

    # -----------------------------------------------
    #                  onReProcess
    # -----------------------------------------------
    def onReProcess(self, event):
        try:
            print("Reprocessing Active Pif content ...")
            self._on_spin('start')
            active_pif = self.active_pif_stc.GetValue()
            processed_dict = self.load_json_with_rules(active_pif, self.keep_unknown)
            donor_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=self.first_api, sort_data=self.sort_keys, keep_all=self.keep_unknown)
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(donor_json_string))
            else:
                self.console_stc.SetValue(donor_json_string)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onReProcess function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')
            if event:
                event.Skip()

    # -----------------------------------------------
    #                  onReProcessJsonFiles
    # -----------------------------------------------
    def onReProcessJsonFiles(self, event):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User pressed ReProcess Json File(s)")
        wildcard = "Property files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, _("Choose one or multiple json files to reprocess"), wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dialog.ShowModal() == wx.ID_CANCEL:
            print("User cancelled file selection.")
            return
        paths = dialog.GetPaths()
        dialog.Destroy()

        # debug(f"Selected files: {paths}")
        try:
            self._on_spin('start')
            count = len(paths)
            i = 0
            for pathname in paths:
                i += 1
                debug(f"Reprocessing {i}/{count} {pathname} ...")
                with open(pathname, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    data = json5.load(f)
                json_string = json.dumps(data, indent=4, sort_keys=self.sort_keys)
                processed_dict = self.load_json_with_rules(json_string, self.keep_unknown)
                reprocessed_json_string = process_dict(the_dict=processed_dict, add_missing_keys=self.add_missing_keys_checkbox.IsChecked(), pif_flavor=self.pif_flavor, set_first_api=self.first_api, sort_data=self.sort_keys, keep_all=self.keep_unknown)
                if count == 1:
                    self.console_stc.SetValue(reprocessed_json_string)
                else:
                    with open(pathname, 'w', encoding='ISO-8859-1', errors="replace", newline='\n') as f:
                        f.write(reprocessed_json_string)
                        wx.YieldIfNeeded
        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onReProcessJsonFiles function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')
            if event:
                event.Skip()

    # -----------------------------------------------
    #                  onGetFrameworkPatcherCode
    # -----------------------------------------------
    def onGetFrameworkPatcherCode(self, event):
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User pressed onGetFrameworkPatcherCode Json File(s)")
        wildcard = "Property files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, _("Choose one or multiple json files to reprocess"), wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dialog.ShowModal() == wx.ID_CANCEL:
            print("User cancelled file selection.")
            return
        paths = dialog.GetPaths()
        dialog.Destroy()

        # debug(f"Selected files: {paths}")
        try:
            self._on_spin('start')
            count = len(paths)
            i = 0
            all_output_lines = []
            for pathname in paths:
                i += 1
                debug(f"Processing {i}/{count} {pathname} ...")
                with open(pathname, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    data = json5.load(f)

                # Extract and format the relevant key values
                keys_of_interest = ["MANUFACTURER", "MODEL", "FINGERPRINT", "BRAND", "PRODUCT", "DEVICE", "RELEASE", "ID", "INCREMENTAL", "TYPE", "TAGS", "SECURITY_PATCH"]
                output_lines = [
                    "// -------------------------------------------------------------------------------------------------------",
                    f"// // {pathname}"
                ]
                for key in keys_of_interest:
                    value = data.get(key, "")
                    output_lines.append(f'// map.put("{key}", "{value}");')

                all_output_lines.extend(output_lines)

            all_output_lines.append("// -------------------------------------------------------------------------------------------------------")
            final_output_text = "\n".join(all_output_lines)
            if self.pif_format == 'prop':
                self.console_stc.SetValue(self.J2P(final_output_text))
            else:
                self.console_stc.SetValue(final_output_text)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onGetFrameworkPatcherCode function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')
            if event:
                event.Skip()

    # -----------------------------------------------
    #                  onSavePif
    # -----------------------------------------------
    def onSavePif(self, event):
        active_data = self.active_pif_stc.GetValue()
        pif_string = None
        if active_data:
            if self.pif_format == 'prop':
                pif_string = self.P2J(active_data)
            else:
                pif_string = active_data

        pif_json = json5.loads(pif_string)
        manufacturer = ''
        with contextlib.suppress(Exception):
            manufacturer = pif_json['MANUFACTURER']
        if manufacturer == '':
            with contextlib.suppress(Exception):
                manufacturer = pif_json['BRAND']
        device = ''
        with contextlib.suppress(Exception):
            device = pif_json['DEVICE']
        fingerprint = ''
        with contextlib.suppress(Exception):
            fingerprint = pif_json['FINGERPRINT']
        build_id = ''
        if fingerprint != '':
            pattern = r'([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)\/([^:]*):([^\/]*)\/([^\/]*)$'
            match = re.search(pattern, fingerprint)
            if match and match.lastindex == 8:
                buildid = match[5]

        filename = f"{manufacturer}_{device}_{buildid}.json".replace(' ', '_')
        with wx.FileDialog(self, _("Save FP file"), '', filename, wildcard="Json files (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                print(f"User Cancelled saving pif")
                return     # the user changed their mind
            pathname = fileDialog.GetPath()
            with open(pathname, 'w', encoding='utf-8') as f:
                json.dump(pif_json, f, indent=4)

    # -----------------------------------------------
    #                  onSaveToFavorites
    # -----------------------------------------------
    def onSaveToFavorites(self, event):
        try:
            active_data = self.active_pif_stc.GetValue()
            active_pif = None
            if active_data:
                if self.pif_format == 'prop':
                    active_pif = self.P2J(active_data)
                else:
                    active_pif = active_data

            pif_hash = json_hexdigest(active_pif)
            if pif_hash in self.favorite_pifs:
                # Delete from favorites
                del self.favorite_pifs[pif_hash]
                pif_hash = None
                self.update_combo_box()
                # self.pif_combo_box.SetSelection(-1)
            else:
                # Add to favorites
                active_pif_json = json5.loads(active_pif)
                brand = '[NO BRAND]'
                model = '[NO MODEL]'
                id = ''
                with contextlib.suppress(KeyError):
                    brand = active_pif_json['BRAND']
                with contextlib.suppress(KeyError):
                    model = active_pif_json['MODEL']
                with contextlib.suppress(KeyError):
                    id = active_pif_json['ID']
                label = f"{brand} {model} {id}"

                dialog = wx.TextEntryDialog(None, _("Enter a label:"), _("Save Pif to Favorites"))
                dialog.SetValue(label)
                result = dialog.ShowModal()
                if result == wx.ID_OK:
                    label = dialog.GetValue()
                    print("Label:", label)
                    self.favorite_pifs.setdefault(pif_hash, {})["label"] = label
                    self.favorite_pifs.setdefault(pif_hash, {})["date_added"] = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
                    self.favorite_pifs.setdefault(pif_hash, {})["pif"] = active_pif_json
                    dialog.Destroy()
                elif result == wx.ID_CANCEL:
                    print("Dialog canceled")
                    dialog.Destroy()
                    return

            set_favorite_pifs(self.favorite_pifs)

            with open(get_favorite_pifs_file_path(), "w", encoding='ISO-8859-1', errors="replace") as f:
                json.dump(self.favorite_pifs, f, indent=4)

            # self.update_combo_box(pif_hash)
            self.ActivePifStcChange(None)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onSaveToFavorites function")
            traceback.print_exc()
        if event:
            event.Skip()

    # -----------------------------------------------
    #                  onImportFavorites
    # -----------------------------------------------
    def onImportFavorites(self, e):
        try:
            with wx.DirDialog(self, _("Select folder to Import Pifs"), style=wx.DD_DEFAULT_STYLE) as folderDialog:
                if folderDialog.ShowModal() == wx.ID_CANCEL:
                    print("User cancelled folder selection.")
                    return
                selected_folder = folderDialog.GetPath()

            self._on_spin('start')
            count = 0
            for dirpath, dirnames, filenames in os.walk(selected_folder):
                pif_files = [file for file in filenames if file.endswith(".json")]
                for pif_file in pif_files:
                    with open(os.path.join(dirpath, pif_file), 'r', encoding="ISO-8859-1", errors="replace") as f:
                        data = json5.load(f)
                    with contextlib.suppress(KeyError):
                        brand = data['BRAND']
                    with contextlib.suppress(KeyError):
                        model = data['MODEL']
                    with contextlib.suppress(KeyError):
                        id = data['ID']
                    sp = ''
                    with contextlib.suppress(KeyError):
                        sp = data['SECURITY_PATCH']
                    if sp != '':
                        label = f"{brand} {model} {sp}"
                    else:
                        label = f"{brand} {model} {id}"
                    pif_data = json.dumps(data, indent=4)
                    pif_hash = json_hexdigest(pif_data)
                    # Add to favorites
                    print(f"Importing: {label} ...")
                    count += 1
                    self.favorite_pifs.setdefault(pif_hash, {})["label"] = label
                    self.favorite_pifs.setdefault(pif_hash, {})["date_added"] = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
                    self.favorite_pifs.setdefault(pif_hash, {})["pif"] = json.loads(pif_data)
                    wx.YieldIfNeeded()
            print(f"Processed {count} pifs.")

            set_favorite_pifs(self.favorite_pifs)
            with open(get_favorite_pifs_file_path(), "w", encoding='ISO-8859-1', errors="replace") as f:
                json.dump(self.favorite_pifs, f, indent=4)

            # self.update_combo_box(pif_hash)
            self.update_combo_box(None)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in onImportFavorites function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        self._last_call_was_on_spin = True
        wx.YieldIfNeeded()
        if state == 'start':
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            wx.Yield()
            self.Parent._on_spin('start')
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            wx.Yield()
            self.Parent._on_spin('stop')

    # -----------------------------------------------
    #                  onResize
    # -----------------------------------------------
    def onResize(self, event):
        self.resizing = True
        stc_size = self.active_pif_stc.GetSize()
        x = stc_size.GetWidth()
        if not self._last_call_was_on_spin:
            self.active_pif_stc.SetScrollWidth(x - 60)
        self._last_call_was_on_spin = False
        self.console_stc.SetScrollWidth(x - 60)

        self.Layout()
        if event:
            event.Skip(True)

    # -----------------------------------------------
    #                  toast
    # -----------------------------------------------
    def toast(self, title, message):
        if self.config.show_notifications:
            notification = wx.adv.NotificationMessage(title, message, parent=None, flags=wx.ICON_INFORMATION)
            notification.SetIcon(images.Icon_dark_256.GetIcon())
            notification.Show()

    # -----------------------------------------------
    #                  calculate_combo_width
    # -----------------------------------------------
    def calculate_combo_width(self, combo_box):
        try:
            if combo_box.GetCount() == 0:
                # Let wx handle default size
                return -1

            # Get the device context to measure text
            dc = wx.ClientDC(combo_box)
            dc.SetFont(combo_box.GetFont())

            max_width = 0
            # Measure each item in the combo box
            for i in range(combo_box.GetCount()):
                text = combo_box.GetString(i)
                text_width, _ = dc.GetTextExtent(text)
                max_width = max(max_width, text_width)

            # Add some padding for the dropdown arrow and margins
            # Typical padding: 20px for dropdown arrow + 20px for margins
            optimal_width = max_width + 40

            # Set a reasonable minimum (80px) and maximum (400px)
            optimal_width = max(80, min(optimal_width, 400))

            return optimal_width
        except Exception:
            return -1  # Fallback to default sizing

    # -----------------------------------------------
    #                  update_combo_size
    # -----------------------------------------------
    def update_combo_size(self, combo_box):
        try:
            width = self.calculate_combo_width(combo_box)
            if width > 0:
                current_size = combo_box.GetSize()
                combo_box.SetMinSize((width, current_size.height))
                combo_box.SetSize((width, current_size.height))
                # Force layout update
                self.Layout()
        except Exception:
            # Ignore errors, keep default sizing
            pass

    # -----------------------------------------------
    #                  update_tf_button_states
    # -----------------------------------------------
    def update_tf_button_states(self):
        try:
            selected_text = self.tf_targets_combo.GetStringSelection()
            has_valid_target = selected_text and selected_text != _("TF Targets")
            has_targets = self.tf_targets_combo.GetCount() > 0 and not (self.tf_targets_combo.GetCount() == 1 and self.tf_targets_combo.GetString(0) == _("TF Targets"))

            self.tf_add_target_button.Enable(True)
            self.tf_delete_target_button.Enable(has_valid_target)
            self.tf_edit_targets_button.Enable(True)

            # Push Json enabled when target selected and active_pif has valid content
            if has_valid_target:
                active_data = self.active_pif_stc.GetValue().strip()
                has_valid_json = False
                if active_data:
                    try:
                        if self.pif_format == 'prop':
                            json_data = self.P2J(active_data)
                        else:
                            json_data = active_data
                        if json_data:
                            json.loads(json_data)
                            has_valid_json = True
                    except:
                        try:
                            json5.loads(json_data if 'json_data' in locals() else active_data)
                            has_valid_json = True
                        except:
                            has_valid_json = False
                self.tf_push_json_button.Enable(has_valid_json)
            else:
                self.tf_push_json_button.Enable(False)

        except Exception:
            print(f"\n❌ {datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception in update_tf_button_states function")
            traceback.print_exc()
        finally:
            self._on_spin('stop')
