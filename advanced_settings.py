#!/usr/bin/env python

import gettext
import wx
import images as images
from runtime import *

_ = gettext.gettext

# ============================================================================
#                               Class AdvancedSettings
# ============================================================================
class AdvancedSettings(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        self.SetTitle(_("Advanced Configuration Settings"))

        vSizer = wx.BoxSizer(wx.VERTICAL)
        warning_sizer = wx.BoxSizer(wx.HORIZONTAL)
        warning_text = _('''WARNING!
This is advanced configuration.
Unless you know what you are doing,
you should not be enabling it.

YOU AND YOU ALONE ARE RESPONSIBLE FOR ANYTHING THAT HAPPENS TO YOUR DEVICE.
THIS TOOL IS CODED WITH THE EXPRESS ASSUMPTION THAT YOU ARE FAMILIAR WITH
ADB, MAGISK, ANDROID, AND ROOT.
IT IS YOUR RESPONSIBILITY TO ENSURE THAT YOU KNOW WHAT YOU ARE DOING.
''')
        # warning label
        self.warning_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=warning_text, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.ALIGN_CENTER_HORIZONTAL)
        self.warning_label.Wrap(-1)
        self.warning_label.SetForegroundColour(wx.Colour(255, 0, 0))
        warning_sizer.Add(self.warning_label, proportion=0, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=80)
        vSizer.Add(warning_sizer, proportion=0, flag=wx.EXPAND, border=5)

        # advanced options
        advanced_options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.advanced_options_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Enable Advanced Options"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.advanced_options_checkbox.SetToolTip(_(u"Expert mode"))
        advanced_options_sizer.Add(self.advanced_options_checkbox, proportion=0, flag=wx.ALL, border=5)
        vSizer.Add(advanced_options_sizer, proportion=0, flag=wx.EXPAND, border=5)

        # static line
        staticline = wx.StaticLine(parent=self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LI_HORIZONTAL)
        vSizer.Add(staticline, proportion=0, flag=wx.EXPAND, border=5)

        # gap
        # vSizer.Add((0, 20), proportion=0, flag=0, border=5)

        fgs1 = wx.FlexGridSizer(cols=2, vgap=10, hgap=10)
        # this makes the second column expandable (index starts at 0)
        fgs1.AddGrowableCol(1, 1)

        # Magisk Package name
        package_name_label = wx.StaticText(parent=self, label=_(u"Magisk Package Name"))
        self.package_name = wx.TextCtrl(parent=self, id=-1, size=(-1, -1))
        self.package_name.SetToolTip(_(u"If you have hidden Magisk,\nset this to the hidden package name."))
        self.reset_magisk_pkg = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.reset_magisk_pkg.SetBitmap(images.scan_24.GetBitmap())
        self.reset_magisk_pkg.SetToolTip(_(u"Resets package name to default: com.topjohnwu.magisk"))
        package_name_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        package_name_sizer.Add(self.package_name, proportion=1, flag=wx.ALL, border=0)
        package_name_sizer.Add(self.reset_magisk_pkg, proportion=0, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=5)

        # only add if we're on linux
        if sys.platform.startswith("linux"):
            # Linux File Explorer
            file_explorer_label = wx.StaticText(self, label=_(u"Linux File Explorer:"))
            file_explorer_label.SetSize(self.package_name.GetSize())
            self.file_explorer = wx.TextCtrl(self, -1, size=(300, -1))
            self.file_explorer.SetToolTip(_(u"Set full path to File Explorer.\nDefault: Nautilus"))
            file_explorer_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
            file_explorer_sizer.Add((20, 0), proportion=0, flag=wx.ALL, border=5)
            file_explorer_sizer.Add(self.file_explorer, proportion=0, flag=wx.LEFT, border=10)

            # Linux Shell
            shell_label = wx.StaticText(parent=self, label=_(u"Linux Shell:"))
            shell_label.SetSize(self.package_name.GetSize())
            self.shell = wx.TextCtrl(parent=self, id=wx.ID_ANY, size=(300, -1))
            self.shell.SetToolTip(_(u"Set full path to Linux Shell.\nDefault: gnome-terminal"))
            shell_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
            shell_sizer.Add((20, 0), proportion=0, flag=wx.ALL, border=5)
            shell_sizer.Add(self.shell, proportion=0, flag=wx.LEFT, border=10)

        # Offer Patch methods
        self.patch_methods_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Offer Patch Methods"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.patch_methods_checkbox.SetToolTip(_(u"When patching the choice of method is presented."))
        self.recovery_patch_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Patching Recovery Partition"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.recovery_patch_checkbox.SetToolTip(_(u"Enabling this will show an option to patch a recovery partition.\nThis should be kept disabled unless you have an old device.\n(most A-only devices launched with Android 9, legacy SAR)"))

        # Use Busybox Shell
        self.use_busybox_shell_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Use Busybox Shell"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.use_busybox_shell_checkbox.SetToolTip(_(u"When creating a patch, if this is checked, busybox ash will be used as shell."))

        # Enable Low Memory
        self.low_mem_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"System has low memory"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.low_mem_checkbox.SetToolTip(_(u"Use this option to sacrifice speed in favor of memory."))

        # Extra img extraction
        self.extra_img_extracts_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Extra img extraction"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.extra_img_extracts_checkbox.SetToolTip(_(u"When checked and available in payload.bin\nAlso extract vendor_boot.img, vendor_kernel_boot.img, dtbo.img, super_empty.img"))

        # Show Notifications
        self.show_notifications_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Show notifications"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.show_notifications_checkbox.SetToolTip(_(u"When checked PixelFlasher will display system toast notifications."))

        # Always Create boot.tar
        self.create_boot_tar_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Always create boot.tar"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.create_boot_tar_checkbox.SetToolTip(_(u"When checked, PixelFlasher always creates boot.tar of the patched boot file.\nIf unchecked, only for Samsung firmware boot.tar will be created."))
        self.create_boot_tar_checkbox.Disable()

        # Check for updates options
        self.check_for_update_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Check for updates"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_update_checkbox.SetToolTip(_(u"Checks for available updates on startup"))

        # Check for Minimum Disk space options
        self.check_for_disk_space_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Check for Minumum Disk (5Gb)"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_disk_space_checkbox.SetToolTip(_(u"Enforces minimum disk space of 5 Gb to allow flashing.\nThis avoids storage related issues."))

        # Check for Bootloader unlocked options
        self.check_for_bootloader_unlocked_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Check for bootloader unlocked"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.check_for_bootloader_unlocked_checkbox.SetToolTip(_(u"Checks to make sure bootloader is unlocked before flashing."))

        # Force codepage
        self.force_codepage_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Force codepage to"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.force_codepage_checkbox.SetToolTip(_(u"Uses specified code page instead of system code page"))
        self.code_page = wx.TextCtrl(parent=self, id=wx.ID_ANY, size=(-1, -1))

        # Delete Bundle libs
        self.delete_bundled_libs_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_(u"Delete bundled libs"))
        self.delete_bundled_libs_label.SetToolTip(_(u"The listed libraries would be deleted from the PF bundle to allow system defined ones to be used."))
        self.delete_bundled_libs = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.delete_bundled_libs.ShowCancelButton(True)
        self.delete_bundled_libs.SetDescriptiveText(_("Example: libreadline.so.8, libgdk*"))
        self.delete_bundled_libs.ShowSearchButton(False)

        # Use Custom Font
        self.use_custom_font_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=_(u"Use Custom Fontface"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.use_custom_font_checkbox.SetToolTip(_(u"Use custom font for monospace fonts\nMight require PixelFlasher restart to properly apply to the Console window."))

        # Font Selection
        fonts = wx.FontEnumerator()
        fonts.EnumerateFacenames(wx.FONTENCODING_SYSTEM, fixedWidthOnly=True)
        font_list = fonts.GetFacenames(wx.FONTENCODING_SYSTEM, fixedWidthOnly=True)
        self.font = wx.ListBox(parent=self, id=wx.ID_ANY, size=(300, 100), choices=font_list)
        self.font_size = wx.SpinCtrl(parent=self, id=wx.ID_ANY, min=6, max=50, initial=self.Parent.config.pf_font_size)
        self.sample = wx.StaticText(parent=self, id=wx.ID_ANY, label=_("Sample "))
        fonts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        fonts_sizer.Add(self.font, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=0)
        fonts_sizer.Add(self.font_size, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        fonts_sizer.Add(self.sample, proportion=1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=5)
        self.font.SetSelection(-1)
        self.font_size.SetToolTip(_('Select font size'))
        self._onFontSelect(None)

        # scrcpy 1st row widgets, select path
        self.scrcpy_path_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=_(u"Srccpy Path"))
        self.srccpy_link = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.srccpy_link.SetBitmap(bitmap=images.open_link_24.GetBitmap())
        self.srccpy_link.SetToolTip(_("Download Srccpy"))
        self.scrcpy_path_picker = wx.FilePickerCtrl(parent=self, id=wx.ID_ANY, path=wx.EmptyString, message=_(u"Select scrcpy executable"), wildcard=_(u"Scrcpy executable (*.exe;*)|*.exe;*"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.FLP_USE_TEXTCTRL)

        self.scrcpy_path_picker.SetToolTip(_("Select scrcpy executable"))
        self.scrcpy_h1sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.scrcpy_h1sizer.Add(window=self.scrcpy_path_label, proportion=0, flag=wx.EXPAND)
        self.scrcpy_h1sizer.AddSpacer(10)
        self.scrcpy_h1sizer.Add(window=self.srccpy_link, proportion=0, flag=wx.EXPAND)
        self.scrcpy_h1sizer.AddSpacer(10)
        self.scrcpy_h1sizer.Add(window=self.scrcpy_path_picker, proportion=1, flag=wx.EXPAND)

        # scrcpy 2nd row flags
        self.scrcpy_flags = wx.SearchCtrl(self, style=wx.TE_LEFT)
        self.scrcpy_flags.ShowCancelButton(True)
        self.scrcpy_flags.SetDescriptiveText(_("Flags / Arguments (Example: --video-bit-rate 2M --max-fps=30 --max-size 1024)"))
        self.scrcpy_flags.ShowSearchButton(False)

        # build the sizers for scrcpy
        scrcpy_sb = wx.StaticBox(self, -1, _("Scrcpy settings"))
        scrcpy_vsizer = wx.StaticBoxSizer(scrcpy_sb, wx.VERTICAL)
        scrcpy_vsizer.Add(self.scrcpy_h1sizer, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        scrcpy_vsizer.Add(self.scrcpy_flags, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        #
        scrcpy_outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scrcpy_outer_sizer.AddSpacer(20)
        scrcpy_outer_sizer.Add(scrcpy_vsizer, proportion=1, flag=wx.EXPAND, border=10)
        scrcpy_outer_sizer.AddSpacer(20)

        # add the widgets to the grid in two columns, first fix size, the second expandable.
        fgs1.Add(package_name_label, 0, wx.EXPAND)
        fgs1.Add(package_name_sizer, 1, wx.EXPAND)

        # Set Widget values from config
        self.advanced_options_checkbox.SetValue(self.Parent.config.advanced_options)
        self.package_name.SetValue(self.Parent.config.magisk)
        self.patch_methods_checkbox.SetValue(self.Parent.config.offer_patch_methods)
        self.recovery_patch_checkbox.SetValue(self.Parent.config.show_recovery_patching_option)
        self.use_busybox_shell_checkbox.SetValue(self.Parent.config.use_busybox_shell)
        self.low_mem_checkbox.SetValue(self.Parent.config.low_mem)
        self.extra_img_extracts_checkbox.SetValue(self.Parent.config.extra_img_extracts)
        self.show_notifications_checkbox.SetValue(self.Parent.config.show_notifications)
        self.create_boot_tar_checkbox.SetValue(self.Parent.config.create_boot_tar)
        self.check_for_update_checkbox.SetValue(self.Parent.config.update_check)
        self.check_for_disk_space_checkbox.SetValue(self.Parent.config.check_for_disk_space)
        self.check_for_bootloader_unlocked_checkbox.SetValue(self.Parent.config.check_for_bootloader_unlocked)
        self.force_codepage_checkbox.SetValue(self.Parent.config.force_codepage)
        self.delete_bundled_libs.SetValue(self.Parent.config.delete_bundled_libs)
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

            # only add if we're on linux
            fgs1.Add(file_explorer_label, 0, wx.EXPAND)
            fgs1.Add(file_explorer_sizer, 1, wx.EXPAND)
            fgs1.Add(shell_label, 0, wx.EXPAND)
            fgs1.Add(shell_sizer, 1, wx.EXPAND)

        fgs1.Add(self.patch_methods_checkbox, 0, wx.EXPAND)
        fgs1.Add(self.recovery_patch_checkbox, 0, wx.EXPAND)

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

        fgs1.Add(self.force_codepage_checkbox, 0, wx.EXPAND)
        fgs1.Add(self.code_page, 1, wx.EXPAND)

        fgs1.Add(self.delete_bundled_libs_label, 0, wx.EXPAND)
        fgs1.Add(self.delete_bundled_libs, 1, wx.EXPAND)

        fgs1.Add(self.use_custom_font_checkbox, 0, wx.EXPAND)
        fgs1.Add(fonts_sizer, 1, wx.EXPAND)

        # add flexgrid to vSizer
        vSizer.Add(fgs1, proportion=0, flag=wx.ALL | wx.EXPAND, border=20)

        # Add more stuff after the flexgrid
        vSizer.Add(scrcpy_outer_sizer, proportion=1, flag=wx.EXPAND)

        # gap
        vSizer.Add((0, 20), proportion=0, flag=0, border=5)

        # buttons
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=5)
        self.ok_button = wx.Button(parent=self, id=wx.ID_ANY, label=_(u"OK"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        buttons_sizer.Add(self.ok_button, proportion=0, flag=wx.ALL, border=20)
        self.cancel_button = wx.Button(parent=self, id=wx.ID_ANY, label=_(u"Cancel"), pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        buttons_sizer.Add(self.cancel_button, proportion=0, flag=wx.ALL, border=20)
        buttons_sizer.Add((0, 0), proportion=1, flag=wx.EXPAND, border=5)
        vSizer.Add(buttons_sizer, proportion=0, flag=wx.EXPAND, border=5)

        self.SetSizer(vSizer)
        self.Layout()

        # Connect Events
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOk)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancel)
        self.font.Bind(wx.EVT_LISTBOX, self._onFontSelect)
        self.font_size.Bind(wx.EVT_SPINCTRL, self._onFontSelect)
        self.reset_magisk_pkg.Bind(wx.EVT_BUTTON, self._onResetMagiskPkg)
        self.patch_methods_checkbox.Bind(wx.EVT_CHECKBOX, self._on_offer_patch_methods)
        self.use_custom_font_checkbox.Bind(wx.EVT_CHECKBOX, self._on_use_custom_fontface)

        # Enable / Disable Widgets
        self.enable_disable_widgets()

        # Autosize the dialog
        self.SetSizerAndFit(vSizer)

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

    def _onResetMagiskPkg(self, e):
        self.package_name.Label = 'com.topjohnwu.magisk'

    def _onCancel(self, e):
        self.EndModal(wx.ID_CANCEL)

    def _onOk(self, e):
        if self.advanced_options_checkbox.GetValue() != self.Parent.config.advanced_options:
            print(_(f"Setting Enable Advanced Options to: %S") % self.advanced_options_checkbox.GetValue())
        self.Parent.config.advanced_options = self.advanced_options_checkbox.GetValue()

        if self.patch_methods_checkbox.GetValue() != self.Parent.config.offer_patch_methods:
            print(_(f"Setting Offer Patch Methods to: %s") % self.patch_methods_checkbox.GetValue())
        self.Parent.config.offer_patch_methods = self.patch_methods_checkbox.GetValue()

        if self.recovery_patch_checkbox.GetValue() != self.Parent.config.show_recovery_patching_option:
            print(_(f"Setting Offer Patch Methods to: %s") % self.recovery_patch_checkbox.GetValue())
        self.Parent.config.show_recovery_patching_option = self.recovery_patch_checkbox.GetValue()

        if self.use_busybox_shell_checkbox.GetValue() != self.Parent.config.use_busybox_shell:
            print(_(f"Setting Use Busybox Shell to: %s") % self.use_busybox_shell_checkbox.GetValue())
        self.Parent.config.use_busybox_shell = self.use_busybox_shell_checkbox.GetValue()

        if self.low_mem_checkbox.GetValue() != self.Parent.config.low_mem:
            print(_(f"Setting Low Memory to: %s") % self.low_mem_checkbox.GetValue())
        self.Parent.config.low_mem = self.low_mem_checkbox.GetValue()
        set_low_memory(self.low_mem_checkbox.GetValue())

        if self.extra_img_extracts_checkbox.GetValue() != self.Parent.config.extra_img_extracts:
            print(_(f"Setting Extra img extraction to: %s") % self.extra_img_extracts_checkbox.GetValue())
        self.Parent.config.extra_img_extracts = self.extra_img_extracts_checkbox.GetValue()

        if self.show_notifications_checkbox.GetValue() != self.Parent.config.show_notifications:
            print(_(f"Setting Show notifications to: %s") % self.show_notifications_checkbox.GetValue())
        self.Parent.config.show_notifications = self.show_notifications_checkbox.GetValue()

        if self.create_boot_tar_checkbox.GetValue() != self.Parent.config.create_boot_tar:
            print(_(f"Setting Always create boot.tar: %s") % self.create_boot_tar_checkbox.GetValue())
        self.Parent.config.create_boot_tar = self.create_boot_tar_checkbox.GetValue()

        if self.check_for_update_checkbox.GetValue() != self.Parent.config.update_check:
            print(_(f"Setting Check for updates to: %s") % self.check_for_update_checkbox.GetValue())
        self.Parent.config.update_check = self.check_for_update_checkbox.GetValue()

        if self.check_for_disk_space_checkbox.GetValue() != self.Parent.config.check_for_disk_space:
            print(_(f"Setting Check for Miminum Disk Space to: %s") % self.check_for_disk_space_checkbox.GetValue())
        self.Parent.config.check_for_disk_space = self.check_for_disk_space_checkbox.GetValue()

        if self.check_for_bootloader_unlocked_checkbox.GetValue() != self.Parent.config.check_for_bootloader_unlocked:
            print(_(f"Setting Check for Miminum Disk Space to: %s") % self.check_for_bootloader_unlocked_checkbox.GetValue())
        self.Parent.config.check_for_bootloader_unlocked = self.check_for_bootloader_unlocked_checkbox.GetValue()

        if self.package_name.GetValue():
            with contextlib.suppress(Exception):
                if self.package_name.GetValue() != self.Parent.config.magisk:
                    print(_(f"Setting Magisk Package Name to: %s") % self.package_name.GetValue())
                set_magisk_package(self.package_name.GetValue())
                self.Parent.config.magisk = self.package_name.GetValue()

        if sys.platform.startswith("linux"):
            with contextlib.suppress(Exception):
                if self.file_explorer.GetValue() != self.Parent.config.linux_file_explorer:
                    print(_(f"Setting Linux File Explorer to: %s") % self.file_explorer.GetValue())
                self.Parent.config.linux_file_explorer = self.file_explorer.GetValue()

            with contextlib.suppress(Exception):
                if self.shell.GetValue() != self.Parent.config.linux_shell:
                    print(_(f"Setting Linux Shell to: %s") % self.shell.GetValue())
                set_linux_shell(self.shell.GetValue())
                self.Parent.config.linux_shell = self.shell.GetValue()

        self.Parent.config.force_codepage = self.force_codepage_checkbox.GetValue()
        if self.code_page.GetValue() and self.code_page.GetValue().isnumeric():
            self.Parent.config.custom_codepage = int(self.code_page.GetValue())

        value = self.delete_bundled_libs.GetValue()
        if value is None:
            value = ''
        if value != self.Parent.config.delete_bundled_libs:
            print(_(f"Setting Delete bundled libs to: %s") % value)
            self.Parent.config.delete_bundled_libs = value

        font_settings_changed = False
        if self.use_custom_font_checkbox.GetValue() != self.Parent.config.customize_font:
            print(_("Enabling Custom Font"))
            font_settings_changed = True
        if self.font.GetStringSelection() != self.Parent.config.pf_font_face:
            print(_(f"Setting Application Font to: %s") % self.font.GetStringSelection())
            if self.use_custom_font_checkbox.GetValue():
                font_settings_changed = True
        if self.font_size.GetValue() != self.Parent.config.pf_font_size:
            print(_(f"Setting Application Font Size to: %s") % self.font_size.GetValue())
            if self.use_custom_font_checkbox.GetValue():
                font_settings_changed = True
        self.Parent.config.customize_font = self.use_custom_font_checkbox.GetValue()
        self.Parent.config.pf_font_face = self.font.GetStringSelection()
        self.Parent.config.pf_font_size = self.font_size.GetValue()

        value = self.scrcpy_path_picker.GetPath()
        if value is None:
            value = ''
        if value != self.Parent.config.scrcpy['path'] and os.path.exists(value):
            print(_(f"Setting scrcpy path path to: %s") % value)
            self.Parent.config.scrcpy['path'] = value

        value = self.scrcpy_flags.GetValue()
        if value is None:
            value = ''
        if value != self.Parent.config.scrcpy['flags']:
            print(_(f"Setting scrcpy flags to: %s") % value)
            self.Parent.config.scrcpy['flags'] = value

        # update the runtime config
        set_config(self.Parent.config)

        if font_settings_changed:
            self.Parent.set_ui_fonts()

        self.EndModal(wx.ID_OK)
