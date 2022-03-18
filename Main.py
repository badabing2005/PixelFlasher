#!/usr/bin/env python

import wx
import wx.adv
import wx.lib.inspection
import wx.lib.mixins.inspection
import subprocess

import sys
import os
import json
import images as images
import locale
import zipfile
import shutil
import re
import time
import ntpath

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except:
    pass


# see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
locale.setlocale(locale.LC_ALL, 'C')

__version__ = "1.1.1"
__width__ = 1200
__height__ = 800

# ============================================================================
#                               Class Config
# ============================================================================
class Config():
    def __init__(self):
        self.flash_mode = 'dryRun'
        self.firmware_path = None
        self.platform_tools_path = None
        self.device = None
        self.phone_model = None
        self.adb_id = None
        self.adb_model = None
        self.rooted = None
        self.firmware_id = None
        self.firmware_model = None
        self.phone_path = '/storage/emulated/0/Download'
        self.magisk = 'com.topjohnwu.magisk'
        self.adb = None
        self.fastboot = None
        self.width = __width__
        self.height = __height__
        self.patch_boot = True
        self.custom_rom = False
        self.custom_rom_path = None
        self.disable_verification = False
        self.disable_verity = False
        self.flash_vbmeta = False
        self.version = __version__
        self.custom_rom_id = None

    @classmethod
    def load(cls, file_path):
        conf = cls()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
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
                conf.flash_vbmeta = data['flash_vbmeta']
                conf.version = data['version']
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
            'flash_vbmeta': self.flash_vbmeta,
            'version': __version__
        }
        with open(file_path, 'w') as f:
            # json.dump(data, f, indent=4, sort_keys=True)
            json.dump(data, f, indent=4)


# ============================================================================
#                               Class RedirectText
# ============================================================================
class RedirectText():
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl
        cwd = os.getcwd()
        logfile = os.path.join(cwd, "PixelFlasher.log")
        self.logfile = open(logfile, "w")

    def write(self,string):
        self.out.WriteText(string)
        if self.logfile.closed:
            pass
        else:
            self.logfile.write(string)


# ============================================================================
#                               Class PixelFlasher
# ============================================================================
class PixelFlasher(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(__width__, __height__),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self._config = Config.load(self._get_config_file_path())
        checkPlatformTools(self)

        self._build_status_bar()
        self._set_icons()
        self._build_menu_bar()
        self._init_ui()

        sys.stdout = RedirectText(self.console_ctrl)
        sys.stderr = RedirectText(self.console_ctrl)

        self.Centre(wx.BOTH)
        self.Show(True)
        print("Connect your device")

    def _set_icons(self):
        self.SetIcon(images.Icon.GetIcon())

    def _build_status_bar(self):
        self.statusBar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
        self.statusBar.SetStatusWidths([-2, -1])
        status_text = "Welcome to PixelFlasher %s" % __version__
        self.statusBar.SetStatusText(status_text, 0)

    def _build_menu_bar(self):
        self.menuBar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        wx.App.SetMacExitMenuItemId(wx.ID_EXIT)
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit PixelFlasher")
        self.Bind(wx.EVT_MENU, self._on_exit_app, exit_item)
        self.menuBar.Append(file_menu, "&File")

        # Help menu
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ABOUT, '&About PixelFlasher', 'About')
        self.Bind(wx.EVT_MENU, self._on_help_about, help_item)
        self.menuBar.Append(help_menu, '&Help')

        self.SetMenuBar(self.menuBar)

    def OnClose(self, event):
        self._config.save(self._get_config_file_path())
        wx.Exit()

    def OnResize(self, event):
        self._config.width = self.Rect.Width
        self._config.height = self.Rect.Height
        event.Skip(True)

    # Menu methods
    def _on_exit_app(self, event):
        self._config.save(self._get_config_file_path())
        self.Close(True)

    def _on_help_about(self, event):
        from About import AboutDlg
        about = AboutDlg(self)
        about.ShowModal()
        about.Destroy()

    def report_error(self, message):
        self.console_ctrl.SetValue(message)

    def log_message(self, message):
        self.console_ctrl.AppendText(message)

    def _select_configured_device(self):
        count = 0
        for item in self.choice.GetItems():
            if item == self._config.device:
                self.choice.Select(count)
                break
            count += 1
        if self._config.device:
            # replace multiple spaces with a single space and then split on space
            deviceID = ' '.join(self._config.device.split())
            deviceID = deviceID.split()
            isRooted = deviceID[0]
            if isRooted == '✓':
                self._config.rooted = True
            else:
                self._config.rooted = False
            self._config.adb_id = deviceID[1]
            self._config.adb_model = deviceID[2]
        else:
            self._config.adb_id = None
            self._config.adb_model = None

    @staticmethod
    def _get_config_file_path():
        return wx.StandardPaths.Get().GetUserConfigDir() + "/PixelFlasher.json"

    #-----------------------------------------------------------------------------
    #                                   _init_ui
    #-----------------------------------------------------------------------------
    def _init_ui(self):
        def on_select_device(event):
            choice = event.GetEventObject()
            self._config.device = choice.GetString(choice.GetSelection())
            # replace multiple spaces with a single space and then split on space
            deviceID = ' '.join(self._config.device.split())
            deviceID = deviceID.split()
            isRooted = deviceID[0]
            if isRooted == '✓':
                self._config.rooted = True
            else:
                self._config.rooted = False
            self._config.adb_id = deviceID[1]
            self._config.adb_model = deviceID[2]

        def on_reload(event):
            if self._config.adb:
                print("")
                self.choice.SetItems(getConnectedDevices(self, 'adb'))
                self._config.device = None
                self._config.adb_id = None
                self._config.adb_model = None
            else:
                print("Please set Android Platform Tools Path first.")

        def on_select_platform_tools(event):
            self._config.platform_tools_path = event.GetPath().replace("'", "")
            checkPlatformTools(self)

        def on_select_firmware(event):
            self._config.firmware_path = event.GetPath().replace("'", "")
            firmware = ntpath.basename(self._config.firmware_path)
            firmware = firmware.split("-")
            try:
                self._config.firmware_model = firmware[0]
                self._config.firmware_id = firmware[0] + "-" + firmware[1]
            except Exception as e:
                self._config.firmware_model = None
                self._config.firmware_id = None

        def on_select_custom_rom(event):
            self._config.custom_rom_path = event.GetPath().replace("'", "")
            rom_file = ntpath.basename(self._config.custom_rom_path)
            self._config.custom_rom_id = os.path.splitext(rom_file)[0]

        def on_mode_changed(event):
            radio_button = event.GetEventObject()
            if radio_button.GetValue():
                self._config.flash_mode = radio_button.mode

        def add_mode_radio_button(sizer, index, flash_mode, label, tooltip):
            style = wx.RB_GROUP if index == 0 else 0
            radio_button = wx.RadioButton(panel, name="mode-%s" % flash_mode, label="%s" % label, style=style)
            radio_button.Bind(wx.EVT_RADIOBUTTON, on_mode_changed)
            radio_button.mode = flash_mode
            if flash_mode == self._config.flash_mode:
                radio_button.SetValue(True)
            else:
                radio_button.SetValue(False)
            radio_button.SetToolTip(tooltip)
            sizer.Add(radio_button)
            sizer.AddSpacer(10)

        def on_patch_boot(event):
            patch_checkBox = event.GetEventObject()
            status = patch_checkBox.GetValue()
            self._config.patch_boot = status

        def on_custom_rom(event):
            custom_rom_checkBox = event.GetEventObject()
            status = custom_rom_checkBox.GetValue()
            self._config.custom_rom = status
            if status:
                custom_rom.Enable()
            else:
                custom_rom.Disable()


        # -----------------
        # Prepare Operation
        # -----------------
        def on_prepare(event):
            print("")
            print("==============================================================================")
            print("                              Preparing Package                               ")
            print("==============================================================================")

            # Make sure factory image is selected
            if not self._config.firmware_model:
                print("ERROR: Select a valid factory image.")
                return

            # Make sure platform-tools is set and adb.exe and fastboot.exe are found
            if not self._config.platform_tools_path:
                print("ERROR: Select Android Platform Tools (ADB)")
                return

            # Make sure Phone is connected
            if not self._config.device:
                print("ERROR: Select an ADB connection (phone)")
                return

            # Make sure Phone model matches firmware model
            if self._config.firmware_model != self._config.adb_model:
                print("ERROR: Android device model %s does not match firmware model %s" % (self._config.adb_model, self._config.firmware_model))
                return

            wait = wx.BusyCursor()
            start = time.time()
            cwd = os.getcwd()
            package_dir = self._config.firmware_id
            package_dir_full = os.path.join(cwd, self._config.firmware_id)

            # disable Flash Button
            flash_button.Disable()

            # Delete the previous folder if it exists
            if os.path.exists(package_dir_full):
                try:
                    print("Found a previous package %s deleting ..." % package_dir)
                    shutil.rmtree(package_dir_full)
                except OSError as e:
                    print("Error: %s - %s." % (e.filename, e.strerror))
                    print("ERROR: Could not delete the previous package.")
                    print("Aborting ...")
                    return

            # See if the bundled 7zip is found.
            path_to_7z = (resource_path(os.path.join('bin', '7z.exe')))
            #print("\nResource Dir: %s" % path_to_7z)
            if os.path.exists(path_to_7z):
                print("Found Bundled 7zip.\nzip/unzip operations will be faster")
            else:
                print("Could not find bundled 7zip.\nzip/unzip operations will be slower")
                path_to_7z = None

            # Unzip the factory image
            startUnzip1 = time.time()
            print("Unzipping Image: %s into %s ..." % (self._config.firmware_path, cwd))
            if path_to_7z:
                theCmd = [path_to_7z, 'x', "-bd", "-y", self._config.firmware_path]
                res = runShell(theCmd)
            else:
                try:
                    with zipfile.ZipFile(self._config.firmware_path, 'r') as zip_ref:
                        zip_ref.extractall(cwd)
                except Exception as e:
                    del wait
                    raise e
            endUnzip1 = time.time()
            print("Unzip time1: %s"%(endUnzip1 - startUnzip1,))

            # double check if unpacked directory exists, this should match firmware_id from factory image name
            if os.path.exists(package_dir):
                print("Unzipped into %s folder." % package_dir)
            else:
                print("ERROR: Unzipped folder %s not found." % package_dir)
                print("Aborting ...")
                del wait
                return

            # delete flash-all.sh and flash-base.sh
            os.remove(os.path.join(package_dir_full, "flash-all.sh"))
            os.remove(os.path.join(package_dir_full, "flash-base.sh"))

            # if custom rom is selected, copy it to the flash folder
            if self._config.custom_rom:
                if self._config.custom_rom_path:
                    rom_file = ntpath.basename(self._config.custom_rom_path)
                    rom_file_full = os.path.join(package_dir_full, rom_file)
                    image_file = rom_file
                    image_file_full = rom_file_full
                    image_id = self._config.custom_rom_id
                    if os.path.exists(self._config.custom_rom_path):
                        shutil.copy(self._config.custom_rom_path, rom_file_full, follow_symlinks=True)
                    else:
                        print("ERROR: Custom ROM file: %s is not found" % self._config.custom_rom_path)
                        print("Aborting ...")
                        return
                else:
                    print("ERROR: Custom ROM file is not set")
                    print("Aborting ...")
                    return
            else:
                image_id = 'image-' + self._config.firmware_id
                image_file = image_id + ".zip"
                image_file_full = os.path.join(package_dir_full, image_file)

            #
            # If flash_vbmeta is enabled, extract vbmeta.img to the flash folder
            # This is special use case condition and should not be used in normal cases.
            # skip_reboot is only needed for special cases like flashing vbmeta with verification disabled
            #
            skip_reboot = ''
            if self._config.flash_vbmeta:
                skip_reboot = ' --skip-reboot '
                print("Extracting vbmeta.img from %s ..." % (image_file))
                if os.path.exists(path_to_7z):
                    theCmd = [path_to_7z, 'x', "-bd", "-y", "-o" + package_dir_full, image_file_full, 'vbmeta.img']
                    res = runShell(theCmd)
                else:
                    with zipfile.ZipFile(os.path.join(package_dir_full, "image-" + self._config.firmware_id + ".zip"), 'r') as zip_ref:
                        zip_ref.extract('vbmeta.img', package_dir_full)
                if not os.path.exists(os.path.join(package_dir_full, 'vbmeta.img')):
                    print("ERROR: Could not extract vbmeta.img")
                    print("Aborting ...")
                    return

            # ---------------------------
            # create flash flash-wipe.bat
            # ---------------------------
            src = os.path.join(package_dir_full, "flash-all.bat")
            dest = os.path.join(package_dir_full, "flash-wipe-data.bat")
            fin = open(src, "rt")
            data = fin.read()

            if self._config.flash_vbmeta:
                flash_vbmeta = 'fastboot flash vbmeta '
                if self._config.disable_verity:
                    flash_vbmeta += '--disable-verity '
                if self._config.disable_verification:
                    flash_vbmeta += '--disable-verification '
                flash_vbmeta += 'vbmeta.img'
                data = data.replace('echo Press any key to exit...', flash_vbmeta)
                data = data.replace('pause >nul', 'fastboot reboot')
            else:
                data = data.replace('echo Press any key to exit...', '')
                data = data.replace('pause >nul', '')

            if self._config.custom_rom:
                rom_src = 'update image-' + self._config.firmware_id + '.zip'
                rom_dst = skip_reboot + 'update ' + rom_file
                data = data.replace(rom_src, rom_dst)
            else:
                data = data.replace('update', skip_reboot + 'update')

            data = data.replace('fastboot', self._config.fastboot + ' -s ' + self._config.adb_id)

            fin.close()
            fin = open(dest, "wt")
            fin.write(data)
            fin.close()

            # ------------------------------
            # create flash file-keepData.bat
            # ------------------------------
            fin = open(src, "rt")
            data = fin.read()

            data = data.replace('fastboot -w update', 'fastboot update')

            if self._config.flash_vbmeta:
                flash_vbmeta = 'fastboot flash vbmeta '
                if self._config.disable_verity:
                    flash_vbmeta += '--disable-verity '
                if self._config.disable_verification:
                    flash_vbmeta += '--disable-verification '
                flash_vbmeta += 'vbmeta.img'
                data = data.replace('echo Press any key to exit...', flash_vbmeta)
                data = data.replace('pause >nul', 'fastboot reboot')
            else:
                data = data.replace('echo Press any key to exit...', '')
                data = data.replace('pause >nul', '')

            if self._config.custom_rom:
                rom_src = 'update image-' + self._config.firmware_id + '.zip'
                rom_dst = skip_reboot + 'update ' + rom_file
                data = data.replace(rom_src, rom_dst)
            else:
                data = data.replace('update', skip_reboot + 'update')

            data = data.replace('fastboot', self._config.fastboot + ' -s ' + self._config.adb_id)

            fin.close()
            fin = open(os.path.join(package_dir_full, "flash-keep-data.bat"), "wt")
            fin.write(data)
            fin.close()

            # ----------------------------
            # create flash file-dryRun.bat
            # ----------------------------
            fin = open(src, "rt")
            data = fin.read()

            data = data.replace('fastboot flash', 'echo fastboot flash')
            data = data.replace('fastboot -w update', 'echo fastboot update')
            data = data.replace('pause >nul', 'fastboot reboot')

            if self._config.flash_vbmeta:
                flash_vbmeta = 'echo fastboot flash vbmeta '
                if self._config.disable_verity:
                    flash_vbmeta += '--disable-verity '
                if self._config.disable_verification:
                    flash_vbmeta += '--disable-verification '
                flash_vbmeta += 'vbmeta.img'
                data = data.replace('echo Press any key to exit...', flash_vbmeta)
            else:
                data = data.replace('echo Press any key to exit...', '')

            data = data.replace('fastboot reboot', self._config.fastboot + ' -s ' + self._config.adb_id + ' reboot')

            if self._config.custom_rom:
                rom_src = 'update image-' + self._config.firmware_id + '.zip'
                rom_dst = skip_reboot + 'update ' + rom_file
                data = data.replace(rom_src, rom_dst)
            else:
                data = data.replace('update', skip_reboot + 'update')

            fin.close()
            fin = open(os.path.join(package_dir_full, "flash-dry-run.bat"), "wt")
            fin.write(data)
            fin.close()

            #
            # delete flash-all.bat
            #
            os.remove(os.path.join(package_dir_full, "flash-all.bat"))

            # Do this only if patch is checked.
            if self._config.patch_boot:
                # unzip image (we only need to unzip the full image if we cannot find 7zip)
                # with 7zip we extract a single file, and then put it back later, without full unzip
                startUnzip2 = time.time()
                boot_img_folder = os.path.join(package_dir_full, image_id)
                if path_to_7z:
                    print("Extracting boot.img from %s ..." % (image_file))
                    theCmd = [path_to_7z, 'x', "-bd", "-y", "-o" + package_dir_full, image_file_full, 'boot.img']
                    res = runShell(theCmd)
                else:
                    try:
                        print("Extracting %s ..." % (image_file))
                        with zipfile.ZipFile(image_file_full, 'r') as zip_ref:
                            zip_ref.extractall(boot_img_folder)
                    except Exception as e:
                        del wait
                        raise e
                    # check if unpacked directory exists, mv boot.img
                    if os.path.exists(boot_img_folder):
                        print("Unzipped into %s folder." %(boot_img_folder))
                        src = os.path.join(boot_img_folder, "boot.img")
                        dest = os.path.join(package_dir_full, "boot.img")
                        os.rename(src, dest)
                        os.rename(image_file_full, image_file_full + ".orig")
                    else:
                        print("ERROR: Unzipped folder %s not found." %(boot_img_folder))
                        print("Aborting ...")
                        del wait
                        return
                endUnzip2 = time.time()
                print("Unzip time2: %s"%(endUnzip2 - startUnzip2,))

                # delete existing boot.img
                print("Deleting boot.img from phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell rm -f %s/boot.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 0
                if res.returncode != 0:
                    print("ERROR: Encountered an error.")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return

                # check if delete worked.
                print("Making sure boot.img is not on the phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell ls -l %s/boot.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 1
                if res.returncode != 1:
                    print("ERROR: boot.img Delete Failed!")
                    print(res.stdout)
                    print("Aborting ...")
                    del wait
                    return

                # delete existing magisk_patched.img
                print("Deleting magisk_patched.img from phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell rm -f %s/magisk_patched*.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 0
                if res.returncode != 0:
                    print("ERROR: Encountered an error.")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return

                # check if delete worked.
                print("Making sure magisk_patched.img is not on the phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell ls -l %s/magisk_patched*.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 1
                if res.returncode != 1:
                    print(res.stdout)
                    print("ERROR: boot.img delete failed!")
                    print("Aborting ...")
                    del wait
                    return

                # Transfer boot.img to the phone
                print("Transfering boot.img to the phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " push %s/boot.img %s/boot.img" % (package_dir_full, self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 0
                if res.returncode != 0:
                    print("ERROR: Encountered an error.")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return
                else:
                    print(res.stdout)

                # check if transfer worked.
                print("Making sure boot.img is found on the phone in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell ls -l %s/boot.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect 0
                if res.returncode != 0:
                    print("ERROR: boot.img is not found!")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return

                # See if magisk tools is installed
                # print("Checking to see if Magisk Tools is installed on the phone ...")
                # theCmd = self._config.adb + " -s " + self._config.adb_id + " shell \"su -c \'ls -l /data/adb/magisk/\'\""
                # res = runShell(theCmd)
                # # expect ret 0
                # if res.returncode != 0:
                if not self._config.rooted:
                    print("Magisk Tools not found on the phone")
                    # Check to see if Magisk is installed
                    print("Looking for Magisk app ...")
                    theCmd = self._config.adb + " -s " + self._config.adb_id + " shell pm list packages " + self._config.magisk
                    res = runShell(theCmd)
                    if res.stdout.strip() != "package:" + self._config.magisk:
                        print("Unable to find magisk on the phone, perhaps it is hidden?")
                        # Message to Launch Manually and Patch
                        title = "Magisk not found"
                        message =  "WARNING: Magisk is not found on the phone\n\n"
                        message += "This could be either because it is hidden, or it is not installed\n\n"
                        message += "Please manually launch Magisk on your phone.\n"
                        message += "- Click on `Install` and choose\n"
                        message += "- `Select and Patch a File`\n"
                        message += "- select boot.img in %s \n" % self._config.phone_path
                        message += "- Then hit `LET's GO`\n\n"
                        message += "Click OK when done to continue.\n"
                        message += "Hit CANCEL to abort."
                        dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
                        result = dlg.ShowModal()
                        if result == wx.ID_OK:
                            print("User pressed ok.")
                        else:
                            print("User pressed cancel.")
                            print("Aborting ...")
                            del wait
                            return
                    else:
                        print("Found Magisk app on the phone.")
                        print("Launching Magisk ...")
                        theCmd = self._config.adb + " -s " + self._config.adb_id + " shell monkey -p " + self._config.magisk + " -c android.intent.category.LAUNCHER 1"
                        res = runShell(theCmd)
                        if res.returncode != 0:
                            print("ERROR: Magisk could not be launched")
                            print(res.stderr)
                            print("Please launch Magisk manually.")
                        else:
                            print("Magisk should now be running on the phone.")
                        # Message Dialog Here to Patch Manually
                        title = "Magisk found"
                        message =  "Magisk should now be running on your phone.\n\n"
                        message += "If it is not, you  can try starting in manually\n\n"
                        message += "Please follow these steps in Magisk.\n"
                        message += "- Click on `Install` and choose\n"
                        message += "- `Select and patch a file`\n"
                        message += "- select boot.img in %s \n" % self._config.phone_path
                        message += "- Then hit `LET's GO`\n\n"
                        message += "Click OK when done to continue.\n"
                        message += "Hit CANCEL to abort."
                        dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
                        result = dlg.ShowModal()
                        if result == wx.ID_OK:
                            print("User Pressed Ok.")
                        else:
                            print("User Pressed Cancel.")
                            print("Aborting ...")
                            del wait
                            return
                else:
                    startPatch = time.time()
                    print("Magisk Tools detected.")
                    print("Creating patched boot.img ...")
                    theCmd = self._config.adb + " -s " + self._config.adb_id + " shell \"su -c \'export KEEPVERITY=true; export KEEPFORCEENCRYPT=true; ./data/adb/magisk/boot_patch.sh /sdcard/Download/boot.img; mv ./data/adb/magisk/new-boot.img /sdcard/Download/magisk_patched.img\'\""
                    res = runShell2(theCmd)
                    endPatch = time.time()
                    print("Patch time: %s"%(endPatch - startPatch,))

                # check if magisk_patched.img got created.
                print("")
                print("Looking for magisk_patched.img in %s ..." % (self._config.phone_path))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " shell ls %s/magisk_patched*.img" % (self._config.phone_path)
                res = runShell(theCmd)
                # expect ret 0
                if res.returncode == 1:
                    print("ERROR: magisk_patched*.img not found")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return
                else:
                    magisk_patched = res.stdout.strip()
                    print("Found %s" %magisk_patched)

                # Transfer back boot.img
                print("Pulling %s from the phone ..." % (magisk_patched))
                theCmd = self._config.adb + " -s " + self._config.adb_id + " pull " + magisk_patched + " " + package_dir_full + "/magisk_patched.img"
                res = runShell(theCmd)
                # expect ret 0
                if res.returncode == 1:
                    print("ERROR: Unable to pull magisk_patched.img from phone.")
                    print(res.stderr)
                    print("Aborting ...")
                    del wait
                    return

                # Replace Boot.img and create a zip file
                print("Replacing boot.img with patched version ...")
                startZip = time.time()
                if path_to_7z:
                    # ren boot.img to boot.img.orig
                    src = os.path.join(package_dir_full, "boot.img")
                    dest = os.path.join(package_dir_full, "boot.img.orig")
                    shutil.copy(src, dest, follow_symlinks=True)
                    # copy magisk_patched to boot.img
                    src = os.path.join(package_dir_full, "magisk_patched.img")
                    dest = os.path.join(package_dir_full, "boot.img")
                    shutil.copy(src, dest, follow_symlinks=True)
                    theCmd = [path_to_7z, 'a', image_file_full, 'boot.img']
                    os.chdir(package_dir_full)
                    res = runShell(theCmd)
                    os.chdir(cwd)
                else:
                    src = os.path.join(package_dir_full, "magisk_patched.img")
                    dest = os.path.join(package_dir_full, image_id, "boot.img")
                    shutil.copy(src, dest, follow_symlinks=True)
                    dir_name = os.path.join(self._config.firmware_id, image_id)
                    dest = os.path.join(package_dir_full, image_file)
                    print("")
                    print("Zipping  %s ..." % dir_name)
                    print("Please be patient as this is a slow process and could take some time.")
                    shutil.make_archive(dir_name, 'zip', dir_name)
                if os.path.exists(dest):
                    print("Package is successfully created!")
                    # create a marker file to confirm successful package creation, this will be checked by Flash command
                    src = os.path.join(package_dir_full, "Package_Ready.json")
                    package_ready(self, src)
                    flash_button.Enable()
                else:
                    print("ERROR: Encountered an error while preparing the package.")
                    print("Aborting ...")
                endZip = time.time()
                print("Zip time: %s"%(endZip - startZip,))
            else:
                print("Package is successfully created!")
                src = os.path.join(package_dir_full, "Package_Ready.json")
                package_ready(self, src)
                flash_button.Enable()

            end = time.time()
            print("Total elapsed time: %s"%(end - start,))
            del wait

        # ---------------
        # Flash Operation
        # ---------------
        def on_flash(event):
            wait = wx.BusyCursor()
            src = os.path.join(self._config.firmware_id, "Package_Ready.json")
            if os.path.exists(src):
                # Load Package_Ready.json
                with open(src, 'r') as f:
                    data = json.load(f)
                p_device = data['device']
                p_patch_boot = data['patch_boot']
                p_custom_rom = data['custom_rom']
                p_custom_rom_path = data['custom_rom_path']
                p_flash_vbmeta = data['flash_vbmeta']
                p_disable_verity = data['disable_verity']
                p_disable_verification = data['disable_verification']
                title = "Package State"
                message =  "WARNING: The prepared package is of the following state.\n\n"
                message += "Patch Boot: %s\n" % p_patch_boot
                message += "Custom Rom: %s\n" % p_custom_rom
                message += "Flash Mode: %s\n" % self._config.flash_mode
                if p_flash_vbmeta:
                    message += "Flash vbmeta: %s\n" % p_flash_vbmeta
                    message += "Disable Verity: %s\n" % p_disable_verity
                    message += "Disable Verification: %s\n" % p_disable_verification
                message += "\n"
                message += "If this is what you want to flash\n"
                message += "Press OK to continue.\n"
                message += "or CANCEL to abort.\n"
                print(message)
                dlg = wx.MessageDialog(None, message, title, wx.CANCEL | wx.OK | wx.ICON_EXCLAMATION)
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    print("User Pressed Ok.")
                else:
                    print("User Pressed Cancel.")
                    print("Aborting ...")
                    del wait
                    return

                if self._config.adb:
                    if self._config.adb_id:
                        # Make sure Phone model matches firmware model
                        if self._config.firmware_model != self._config.adb_model:
                            print("ERROR: Android device model %s does not match firmware Model %s" % (self._config.adb_model, self._config.firmware_model))
                            return
                        print("")
                        print("==============================================================================")
                        print("                              Flashing Phone                                  ")
                        print("==============================================================================")
                        startFlash = time.time()
                        # Reboot to bootloader
                        print("Rebooting the phone into bootloader mode ...")
                        theCmd = self._config.adb + " -s " + self._config.adb_id + " reboot bootloader"
                        res = runShell(theCmd)
                        # expect ret 0
                        if res.returncode != 0:
                            # First check if the device is already in fastboot mode
                            devices = getConnectedDevices(self, 'fastboot')
                            if self._config.adb_id not in devices:
                                print("ERROR: Encountered an error.")
                                print(res.stderr)
                                print("Aborting ...")
                                return
                        print(res.stdout)
                        # Start flashing
                        cwd = os.getcwd()
                        if self._config.flash_mode == 'dryRun':
                            print("Flash Mode: Dry Run")
                            theCmd = os.path.join(cwd, self._config.firmware_id, "flash-dry-run.bat")
                        elif self._config.flash_mode == 'keepData':
                            print("Flash Mode: Keep Data")
                            theCmd = os.path.join(cwd, self._config.firmware_id, "flash-keep-data.bat")
                        elif self._config.flash_mode == 'wipeData':
                            print("Flash Mode: Wipe Data")
                            dlg = wx.MessageDialog(None, "You have selected to WIPE data\nAre you sure want to continue?",'Wipe Data',wx.YES_NO | wx.ICON_EXCLAMATION)
                            result = dlg.ShowModal()
                            if result == wx.ID_YES:
                                pass
                            else:
                                print("User canceled flashing.")
                                return
                            theCmd = os.path.join(cwd, self._config.firmware_id, "flash-wipe-data.bat")
                        else:
                            print("Flash Mode: UNKNOWN [%s]" % self._config.flash_mode)
                            print("Aborting ...")
                            return
                        os.chdir(self._config.firmware_id)
                        runShell2(theCmd)
                        print("Done!")
                        endFlash = time.time()
                        print("Flashing elapsed time: %s"%(endFlash - startFlash,))
                        os.chdir(cwd)
                    else:
                        print("ERROR: You must first select a valid adb device.")
                else:
                    print("ERROR: Android Platform Tools must be set.")
            else:
                print("ERROR: You must first prepare a patched firmware package.")
                print("       Press the `Prepare Package` Button!")
                print("")
            del wait

        # ---------------
        # Clear Operation
        # ---------------
        def on_clear(event):
            self.console_ctrl.SetValue("")


        # ==============
        # UI Setup Here
        # ==============
        self.SetSize(self._config.width, self._config.height)
        panel = wx.Panel(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # 10 rows, 2 columns, 10 hgap, 10 vgap
        fgs = wx.FlexGridSizer(11, 2, 10, 10)

        self.choice = wx.Choice(panel, choices=getConnectedDevices(self, 'adb'))
        self.choice.SetFont( wx.Font( 9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Consolas" ) )

        self.choice.Bind(wx.EVT_CHOICE, on_select_device)
        self._select_configured_device()

        reload_button = wx.Button(panel, label="Reload")
        reload_button.Bind(wx.EVT_BUTTON, on_reload)
        reload_button.SetToolTip("Reload adb device list")

        file_picker = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, on_select_firmware)
        file_picker.SetToolTip("Select Pixel Firmware")
        if self._config.firmware_path:
            if os.path.exists(self._config.firmware_path):
                file_picker.SetPath(self._config.firmware_path)
                firmware = ntpath.basename(self._config.firmware_path)
                firmware = firmware.split("-")
                try:
                    self._config.firmware_model = firmware[0]
                    self._config.firmware_id = firmware[0] + "-" + firmware[1]
                except Exception as e:
                    self._config.firmware_model = None
                    self._config.firmware_id = None

        dir_picker = wx.DirPickerCtrl(panel, style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
        dir_picker.Bind(wx.EVT_DIRPICKER_CHANGED, on_select_platform_tools)
        dir_picker.SetToolTip("Select Android Platform-Tools Folder\nWhere adb and fastboot are located.")
        if self._config.platform_tools_path and self._config.adb and self._config.fastboot:
            dir_picker.SetPath(self._config.platform_tools_path)

        device_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        device_boxsizer.Add(self.choice, 1, wx.EXPAND)
        device_boxsizer.Add(reload_button, flag=wx.LEFT, border=10)

        custom_rom_checkbox = wx.CheckBox( panel, wx.ID_ANY, u"Apply Custom ROM", wx.DefaultPosition, wx.DefaultSize, 0 )
        custom_rom_checkbox.Bind( wx.EVT_CHECKBOX, on_custom_rom )
        custom_rom_checkbox.SetValue(self._config.custom_rom)
        custom_rom_checkbox.SetToolTip("Caution: Make sure you read the selected ROM documentation.\nThis might not work for your ROM")

        custom_rom = wx.FilePickerCtrl(panel, style=wx.FLP_USE_TEXTCTRL)
        custom_rom.Bind(wx.EVT_FILEPICKER_CHANGED, on_select_custom_rom)
        custom_rom.SetToolTip("Select Custom ROM")
        if self._config.custom_rom_path:
            if os.path.exists(self._config.custom_rom_path):
                custom_rom.SetPath(self._config.custom_rom_path)
                self._config.custom_rom_id = os.path.splitext(ntpath.basename(self._config.custom_rom_path))[0]
        if self._config.custom_rom:
            custom_rom.Enable()
        else:
            custom_rom.Disable()

        patch_checkBox = wx.CheckBox( panel, wx.ID_ANY, u"Patch boot.img\nusing Magisk", wx.DefaultPosition, wx.DefaultSize, 0 )
        patch_checkBox.Bind( wx.EVT_CHECKBOX, on_patch_boot )
        patch_checkBox.SetValue(self._config.patch_boot)
        patch_checkBox.SetToolTip("This requires Magisk installed on the phone")

        mode_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        mode = self._config.flash_mode
        # add_mode_radio_button(sizer, index, flash_mode, label, tooltip)
        add_mode_radio_button(mode_boxsizer, 0, 'keepData', "Keep Data", "Data will be kept intact.")
        add_mode_radio_button(mode_boxsizer, 1, 'wipeData', "WIPE all data", "CAUTION: This will wipe your data")
        add_mode_radio_button(mode_boxsizer, 2, 'dryRun', "Dry Run", "Dry Run, no flashing will be done.\nThe phone will reboot to fastboot and then\nback to normal.\nThis is for testing.")

        flash_button = wx.Button(panel, -1, "Flash Pixel Phone", wx.DefaultPosition, wx.Size( -1,50 ))
        flash_button.Bind(wx.EVT_BUTTON, on_flash)
        flash_button.SetToolTip("Flashes (with Flash Mode Settings) the selected phone with the prepared Image.")
        if self._config.firmware_id:
            if os.path.exists(os.path.join(self._config.firmware_id, "Package_Ready.json")):
                flash_button.Enable()
            else:
                flash_button.Disable()

        prepare_button = wx.Button(panel, -1, "Prepare Package", wx.DefaultPosition, wx.Size( -1,50 ))
        prepare_button.Bind(wx.EVT_BUTTON, on_prepare)
        prepare_button.SetToolTip("Prepares a Patched Factory Image for later Flashing")


        self.console_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY )
        self.console_ctrl.SetFont(wx.Font(8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL))
        self.console_ctrl.SetBackgroundColour(wx.WHITE)
        self.console_ctrl.SetForegroundColour(wx.BLUE)
        self.console_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLUE))

        device_label = wx.StaticText(panel, label="ADB Connected Devices")
        file_label = wx.StaticText(panel, label="Pixel Phone Factory Image")
        platform_tools_label = wx.StaticText(panel, label="Android Platform Tools")

        mode_label = wx.StaticText(panel, label="Flash Mode")
        console_label = wx.StaticText(panel, label="Console")

        clear_button = wx.Button(panel, -1, "Clear Console")
        clear_button.Bind(wx.EVT_BUTTON, on_clear)

        fgs.AddMany([
                    file_label, (file_picker, 1, wx.EXPAND),
                    platform_tools_label, (dir_picker, 1, wx.EXPAND),
                    device_label, (device_boxsizer, 1, wx.EXPAND),
                    (wx.StaticText(panel, label="")), (wx.StaticText(panel, label="")),
                    custom_rom_checkbox, (custom_rom, 1, wx.EXPAND),
                    patch_checkBox, (prepare_button, 1, wx.EXPAND),
                    mode_label, mode_boxsizer,
                    (wx.StaticText(panel, label="")), (flash_button, 1, wx.EXPAND),
                    (console_label, 1, wx.EXPAND), (self.console_ctrl, 1, wx.EXPAND),
                    (wx.StaticText(panel, label="")), (clear_button, 1, wx.EXPAND)])
        fgs.AddGrowableRow(8, 1)
        fgs.AddGrowableCol(1, 1)
        hbox.Add(fgs, proportion=2, flag=wx.ALL | wx.EXPAND, border=15)
        panel.SetSizer(hbox)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnResize)


# ============================================================================
#                               Function checkPlatformTools
# ============================================================================
def checkPlatformTools(cls):
    if cls._config.platform_tools_path:
        cls._config.adb = os.path.join(cls._config.platform_tools_path, "adb.exe")
        cls._config.fastboot = os.path.join(cls._config.platform_tools_path, "fastboot.exe")
        if os.path.exists(cls._config.fastboot) and os.path.exists(cls._config.adb):
            cls._config.adb = os.path.join(cls._config.platform_tools_path, "adb.exe")
            cls._config.fastboot = os.path.join(cls._config.platform_tools_path, "fastboot.exe")
            return
        else:
            cls._config.platform_tools_path = None
            cls._config.adb = None
            cls._config.fastboot = None

    if not cls._config.platform_tools_path:
        adb = which("adb.exe")
        if adb:
            folder_path = os.path.dirname(adb)
            cls._config.adb = os.path.join(folder_path, "adb.exe")
            cls._config.fastboot = os.path.join(folder_path, "fastboot.exe")
            if os.path.exists(cls._config.fastboot):
                cls._config.platform_tools_path = folder_path
            else:
                cls._config.platform_tools_path = None
                cls._config.adb = None
                cls._config.fastboot = None


# ============================================================================
#                               Function getConnectedDevices
# ============================================================================
def getConnectedDevices(cls, mode):
    devices = []
    if cls._config.adb:
        wait = wx.BusyCursor()
        if mode == 'adb':
            theCmd = cls._config.adb + " devices"
            lookFor = '\tdevice'
        elif mode == 'fastboot':
            theCmd = cls._config.fastboot + " devices"
            lookFor = '\tfastboot'
        else:
            print("ERROR: Unknown device mode: [%s]" % mode)
            return devices
        response = runShell2(theCmd)

        #iterate through the output and select only the devices that are online
        # Split on newline
        for device in response.stdout.split('\n'):
            # Look for tab + device to exclude 'List of devices attached' string

            if lookFor in device:
                # split on tab
                deviceID = device.split("\t")
                # get adb info about the device
                if mode == 'adb':
                    if cls._config.platform_tools_path:
                        theCmd = cls._config.adb + " -s %s shell getprop ro.hardware" % deviceID[0]
                        hardware = runShell(theCmd)
                        # remove any whitespace including tab and newline
                        hardware = ''.join(hardware.stdout.split())
                        theCmd = cls._config.adb + " -s %s shell getprop ro.build.fingerprint" % deviceID[0]
                        fingerprint = runShell(theCmd)
                        # remove any whitespace including tab and newline
                        fingerprint = ''.join(fingerprint.stdout.split())
                        build = fingerprint.split('/')[3]
                        # See if magisk tools is installed
                        theCmd = cls._config.adb + " -s %s shell \"su -c \'ls -l /data/adb/magisk/\'\"" % deviceID[0]
                        res = runShell(theCmd)
                        # expect ret 0
                        if res.returncode == 0:
                            magiskTools = '✓'
                        else:
                            magiskTools = '✗'
                    else:
                        print("Error: ADB is not found in system path")
                    # Format with padding
                    devices.append("{:<4}{:<25}{:<12}{:<25}".format(magiskTools, deviceID[0], hardware, build))
                else:
                    devices.append(deviceID[0])
        del wait
    return devices


# ============================================================================
#                               Function package_ready
# ============================================================================
def package_ready(self, file_path):
    data = {
        'device': self._config.device,
        'patch_boot': self._config.patch_boot,
        'custom_rom': self._config.custom_rom,
        'custom_rom_path': self._config.custom_rom_path,
    }
    if self._config.flash_vbmeta:
        data['flash_vbmeta'] = self._config.flash_vbmeta
        data['disable_verity'] = self._config.disable_verity
        data['disable_verification'] = self._config.disable_verification

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


# ============================================================================
#                               Function purge
# ============================================================================
# This function delete multiple files matching a pattern
def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir, f))


# ============================================================================
#                               Function RunShell
# ============================================================================
# We use this when we want to capture the returncode and also selectively output what we want to console
# Nothing is sent to console, both stdout and stderr are only available when the call is completed.
def runShell(cmd):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return response
    except Exception as e:
        raise e


# ============================================================================
#                               Function RunShell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime, no returncode is available.
def runShell2(cmd):
    class obj(object):
        pass

    response = obj()
    proc = subprocess.Popen("%s" % cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print
    stdout = ''
    while True:
        line = proc.stdout.readline()
        wx.Yield()
        if line.strip() == "":
            pass
        else:
            print(line.strip())
            stdout += line
        if not line: break
    proc.wait()
    response.stdout = stdout
    return response


# ============================================================================
#                               Function resource_path
# ============================================================================
# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
#                               Class App
# ============================================================================
class App(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        # see https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
        self.ResetLocale()
        # wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
        self.SetAppName("PixelFlasher")

        frame = PixelFlasher(None, "PixelFlasher")
        # frame.SetClientSize(frame.FromDIP(wx.Size(__width__, __height__)))
        # frame.SetClientSize(wx.Size(__width__, __height__))
        frame.Show()

        return True


# ============================================================================
#                               Function Main
# ============================================================================
def main():
    app = App(False)
    app.MainLoop()


# ---------------------------------------------------------------------------3
if __name__ == '__main__':
    __name__ = 'Main'
    main()

