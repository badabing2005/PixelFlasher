#!/usr/bin/env python

import os
import subprocess
import re
import wx
import json
import time
import shutil
import zipfile
import ntpath
import sys
import math

from config import VERSION
from phone import Device
from runtime import *


# ============================================================================
#                               Function check_platform_tools
# ============================================================================
def check_platform_tools(self):
    if sys.platform == "win32":
        adb_binary = 'adb.exe'
        fastboot_binary = 'fastboot.exe'
    else:
        adb_binary = 'adb'
        fastboot_binary = 'fastboot'
    if self.config.platform_tools_path:
        adb = os.path.join(self.config.platform_tools_path, adb_binary)
        fastboot = os.path.join(self.config.platform_tools_path, fastboot_binary)
        if os.path.exists(fastboot) and os.path.exists(adb):
            print(f"Selected Platform Tools Path: {self.config.platform_tools_path}.")
            adb = os.path.join(self.config.platform_tools_path, adb_binary)
            fastboot = os.path.join(self.config.platform_tools_path, fastboot_binary)
            set_adb(adb)
            set_fastboot(fastboot)
            identify_sdk_version(self)
            print(f"SDK Version: {get_sdk_version()}")
            return
        else:
            print("ERROR: The selected path %s does not have adb and or fastboot" % self.config.platform_tools_path)
            self.config.platform_tools_path = None
            set_adb(None)
            set_fastboot(None)

    if not self.config.platform_tools_path:
        print("Looking for Android Platform Tools in system PATH environment ...")
        adb = which(adb_binary)
        if adb:
            folder_path = os.path.dirname(adb)
            print("Found Android Platform Tools in %s" % folder_path)
            adb = os.path.join(folder_path, adb_binary)
            fastboot = os.path.join(folder_path, fastboot_binary)
            set_adb(adb)
            set_fastboot(fastboot)
            if os.path.exists(get_fastboot()):
                self.config.platform_tools_path = folder_path
                identify_sdk_version(self)
                print(f"SDK Version: {get_sdk_version()}")
            else:
                print(f"fastboot is not found in: {self.config.platform_tools_path}")
                self.config.platform_tools_path = None
                set_adb(None)
                set_fastboot(None)
        else:
            print("Android Platform Tools is not found.")
    try:
        if self.config.platform_tools_path:
            self.platform_tools_picker.SetPath(self.config.platform_tools_path)
        else:
            self.platform_tools_picker.SetPath('')
    except:
        pass
    identify_sdk_version(self)


# ============================================================================
#                               Function identify_sdk_version
# ============================================================================
def identify_sdk_version(self):
    sdk_version = None
    # Let's grab the adb version
    if get_adb():
        theCmd = "\"%s\" --version" % get_adb()
        response = run_shell(theCmd)
        for line in response.stdout.split('\n'):
            if 'Version' in line:
                sdk_version = line.split()[1]
                debug("Found ADB Version: %s in %s" % (sdk_version, self.config.platform_tools_path))
                set_sdk_version(sdk_version)


# ============================================================================
#                               Function get_package_ready
# ============================================================================
def get_package_ready(self, src, includeFlashMode = False, includeTitle = False):
    message = ''
    if os.path.exists(src):
        with open(src, 'r') as f:
            data = json.load(f)
        p_device = data['device']
        p_patch_boot = data['patch_boot']
        p_custom_rom = data['custom_rom']
        p_custom_rom_path = data['custom_rom_path']
        message = ''
        if includeTitle:
            message +=  "The package is of the following state.\n\n"
        message += "Patch Boot:           %s\n" % str(p_patch_boot)
        message += "Custom Rom:           %s\n" % str(p_custom_rom)
        if p_custom_rom:
            message += "Custom Rom File:      %s\n" % p_custom_rom_path
        if includeFlashMode:
            message += "Flash Mode:           %s\n" % self.config.flash_mode
        message += "\n"
    return message


# ============================================================================
#                               Function set_package_ready
# ============================================================================
def set_package_ready(self, file_path):
    data = {
        'device': self.config.device,
        'patch_boot': self.config.patch_boot,
        'custom_rom': self.config.custom_rom,
        'custom_rom_path': self.config.custom_rom_path,
    }
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
#                               Function debug
# ============================================================================
def debug(message):
    if get_verbose():
        print("debug: %s" % message)


# ============================================================================
#                               Function run_shell
# ============================================================================
# We use this when we want to capture the returncode and also selectively
# output what we want to console. Nothing is sent to console, both stdout and
# stderr are only available when the call is completed.
def run_shell(cmd):
    try:
        response = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return response
    except Exception as e:
        raise e


# ============================================================================
#                               Function run_shell2
# ============================================================================
# This one pipes the stdout and stderr to Console text widget in realtime,
# no returncode is available.
def run_shell2(cmd):
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
#                               Function select_firmware
# ============================================================================
def select_firmware(self):
    firmware = ntpath.basename(self.config.firmware_path)
    filename, extension = os.path.splitext(firmware)
    extension = extension.lower()
    if extension == '.zip':
        print(f"The following firmware {firmware} is selected.")
        firmware = firmware.split("-")
        try:
            set_firmware_model(firmware[0])
            set_firmware_id(firmware[0] + "-" + firmware[1])
        except Exception as e:
            set_firmware_model(None)
            set_firmware_id(None)
        if get_firmware_id():
            set_flash_button_state(self)
    else:
        print(f"ERROR: The selected file {firmware} is not a zip file.")
        self.config.firmware_path = None
        self.firmware_picker.SetPath('')


# ============================================================================
#                               Function set_flash_button_state
# ============================================================================
def set_flash_button_state(self):
    try:
        src = os.path.join(get_firmware_id(), "Package_Ready.json")
        if os.path.exists(src):
            self.flash_button.Enable()
            print("\nPrevious flashable package is found for the selected firmware!")
            message = get_package_ready(self, src, includeTitle=True)
            print(message)
        else:
            self.flash_button.Disable()
            if self.config.firmware_path:
                print("\nNo previous flashable package is found for the selected firmware!")
    except:
        self.flash_button.Disable()


# ============================================================================
#                               Function prepare_package
# ============================================================================
def prepare_package(self):
    print("")
    print("==============================================================================")
    print("  PixelFlasher %s             Preparing Package                               " % VERSION)
    print("==============================================================================")

    # get device
    device = get_phone()

    # Make sure factory image is selected
    if not get_firmware_model():
        print("ERROR: Select a valid factory image.")
        return

    # Make sure platform-tools is set and adb and fastboot are found
    if not self.config.platform_tools_path:
        print("ERROR: Select Android Platform Tools (ADB)")
        return

    # Make sure Phone is connected
    if not device:
        print("ERROR: Select an ADB connection (phone)")
        return

    # Make sure Phone model matches firmware model
    if get_firmware_model() != device.hardware:
        print(f"ERROR: Android device model {device.hardware} does not match firmware model {get_firmware_model()}")
        return

    start = time.time()
    cwd = os.getcwd()
    package_dir = get_firmware_id()
    package_dir_full = os.path.join(cwd, package_dir)

    # disable Flash Button
    self.flash_button.Disable()

    # Delete the previous folder if it exists
    if os.path.exists(package_dir_full):
        try:
            print(f"Found a previous package {package_dir} deleting ...")
            shutil.rmtree(package_dir_full)
        except OSError as e:
            print(f"Error: {e.filename} - {e.strerror}.")
            print("ERROR: Could not delete the previous package.")
            print("Aborting ...")
            return

    # See if the bundled 7zip is found.
    path_to_7z = os.path.join(get_bundle_dir(),'bin', '7z.exe')
    debug(f"Resource Dir: {path_to_7z}")
    if os.path.exists(path_to_7z):
        print("Found Bundled 7zip.\nzip/unzip operations will be faster")
    else:
        print("Could not find bundled 7zip.\nzip/unzip operations will be slower")
        path_to_7z = None

    # Unzip the factory image
    startUnzip1 = time.time()
    print("Unzipping Image: %s into %s ..." % (self.config.firmware_path, cwd))
    if path_to_7z:
        theCmd = f"\"{path_to_7z}\" x -bd -y \"{self.config.firmware_path}\""
        debug(theCmd)
        res = run_shell(theCmd)
    else:
        try:
            with zipfile.ZipFile(self.config.firmware_path, 'r') as zip_ref:
                zip_ref.extractall(cwd)
                zip_ref.close()
        except Exception as e:
            raise e
    endUnzip1 = time.time()
    print("Unzip time1: %s seconds"%(math.ceil(endUnzip1 - startUnzip1)))

    # double check if unpacked directory exists, this should match firmware_id from factory image name
    if os.path.exists(package_dir):
        print("Unzipped into %s folder." % package_dir)
    else:
        print("ERROR: Unzipped folder %s not found." % package_dir)
        # if bundled 7zip fails, let's try with Python libraries and see if that works.
        if path_to_7z:
            debug("returncode is: %s" %res.returncode)
            debug("stdout is: %s" %res.stdout)
            debug("stderr is: %s" %res.stderr)
            print("Disabling bundled 7zip ...")
            path_to_7z = None
            print("Trying unzip again with python libraries ...")
            startUnzip1 = time.time()
            try:
                with zipfile.ZipFile(self.config.firmware_path, 'r') as zip_ref:
                    zip_ref.extractall(cwd)
            except Exception as e:
                raise e
            endUnzip1 = time.time()
            print("Unzip time1.1: %s seconds"%(math.ceil(endUnzip1 - startUnzip1)))
            # double check if unpacked directory exists, this should match firmware_id from factory image name
            if os.path.exists(package_dir):
                print("Unzipped into %s folder." % package_dir)
            else:
                print("ERROR: Unzipped folder %s not found again." % package_dir)
                print("Aborting ...")
                return
        else:
            print("Aborting ...")
            return

    # delete flash-all.sh and flash-base.sh
    os.remove(os.path.join(package_dir_full, "flash-all.sh"))
    os.remove(os.path.join(package_dir_full, "flash-base.sh"))

    # if custom rom is selected, copy it to the flash folder
    if self.config.advanced_options and self.config.custom_rom:
        if self.config.custom_rom_path:
            rom_file = ntpath.basename(self.config.custom_rom_path)
            rom_file_full = os.path.join(package_dir_full, rom_file)
            image_file = rom_file
            image_file_full = rom_file_full
            image_id = get_custom_rom_id()
            if os.path.exists(self.config.custom_rom_path):
                shutil.copy(self.config.custom_rom_path, rom_file_full, follow_symlinks=True)
            else:
                print(f"ERROR: Custom ROM file: {self.config.custom_rom_path} is not found")
                print("Aborting ...")
                return
        else:
            print("ERROR: Custom ROM file is not set")
            print("Aborting ...")
            return
    else:
        image_id = 'image-' + package_dir
        image_file = image_id + ".zip"
        image_file_full = os.path.join(package_dir_full, image_file)

    # Initialize fastboot_option
    fastboot_options = f"-s {device.id} ##PLACEHOLDER## "

    # ---------------------------
    # create flash flash-wipe.bat
    # ---------------------------
    src = os.path.join(package_dir_full, "flash-all.bat")
    dest = os.path.join(package_dir_full, "flash-wipe-data.txt")
    fin = open(src, "rt")
    data = fin.read()

    data = data.replace('pause >nul', '')

    if self.config.custom_rom:
        rom_src = 'update image-' + package_dir + '.zip'
        rom_dst = 'update ' + rom_file
        data = data.replace(rom_src, rom_dst)

    data = data.replace('fastboot', "\"%s\" %s" % (get_fastboot(), fastboot_options))

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
    data = data.replace('pause >nul', '')

    if self.config.custom_rom:
        rom_src = 'update image-' + package_dir + '.zip'
        rom_dst = 'update ' + rom_file
        data = data.replace(rom_src, rom_dst)

    data = data.replace('fastboot', "\"%s\" %s" % (get_fastboot(), fastboot_options))

    fin.close()
    fin = open(os.path.join(package_dir_full, "flash-keep-data.txt"), "wt")
    fin.write(data)
    fin.close()

    # ----------------------------
    # create flash file-dryRun.bat
    # ----------------------------
    fin = open(src, "rt")
    data = fin.read()

    data = data.replace('fastboot flash', "echo \"%s\" %s flash" % (get_fastboot(), fastboot_options))
    data = data.replace('fastboot -w update', "echo \"%s\" %s update" % (get_fastboot(), fastboot_options))
    data = data.replace('pause >nul', 'fastboot reboot')

    if self.config.custom_rom:
        rom_src = 'update image-' + package_dir + '.zip'
        rom_dst = 'update ' + rom_file
        data = data.replace(rom_src, rom_dst)

    data = data.replace('fastboot reboot', "\"%s\" -s %s reboot" % (get_fastboot(), device.id))

    fin.close()
    fin = open(os.path.join(package_dir_full, "flash-dry-run.txt"), "wt")
    fin.write(data)
    fin.close()

    # delete flash-all.bat
    os.remove(os.path.join(package_dir_full, "flash-all.bat"))

    # Do this only if patch is checked.
    if self.config.patch_boot:
        # unzip image (we only need to unzip the full image if we cannot find 7zip)
        # with 7zip we extract a single file, and then put it back later, without full unzip
        startUnzip2 = time.time()
        boot_img_folder = os.path.join(package_dir_full, image_id)
        if path_to_7z:
            print("Extracting boot.img from %s ..." % (image_file))
            theCmd = "\"%s\" x -bd -y -o\"%s\" \"%s\" boot.img" % (path_to_7z, package_dir_full, image_file_full)
            debug("%s" % theCmd)
            res = run_shell(theCmd)
        else:
            try:
                print("Extracting %s ..." % (image_file))
                with zipfile.ZipFile(image_file_full, 'r') as zip_ref:
                    zip_ref.extractall(boot_img_folder)
            except Exception as e:
                raise e
            # check if unpacked directory exists, move boot.img
            if os.path.exists(boot_img_folder):
                print("Unzipped into %s folder." %(boot_img_folder))
                src = os.path.join(boot_img_folder, "boot.img")
                dest = os.path.join(package_dir_full, "boot.img")
                os.rename(src, dest)
                os.rename(image_file_full, image_file_full + ".orig")
            else:
                print("ERROR: Unzipped folder %s not found." %(boot_img_folder))
                print("Aborting ...")
                return
        endUnzip2 = time.time()
        print("Unzip time2: %s seconds"%(math.ceil(endUnzip2 - startUnzip2)))

        # delete existing boot.img
        print("Deleting boot.img from phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell rm -f %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode != 0:
            print("ERROR: Encountered an error.")
            print(res.stderr)
            print("Aborting ...")
            return

        # check if delete worked.
        print("Making sure boot.img is not on the phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell ls -l %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 1
        if res.returncode != 1:
            print("ERROR: boot.img Delete Failed!")
            print(res.stdout)
            print("Aborting ...")
            return

        # delete existing magisk_patched.img
        print("Deleting magisk_patched.img from phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell rm -f %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode != 0:
            print("ERROR: Encountered an error.")
            print(res.stderr)
            print("Aborting ...")
            return

        # check if delete worked.
        print("Making sure magisk_patched.img is not on the phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell ls -l %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 1
        if res.returncode != 1:
            print(res.stdout)
            print("ERROR: boot.img delete failed!")
            print("Aborting ...")
            return

        # Transfer boot.img to the phone
        print("Transfering boot.img to the phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s push \"%s\" %s/boot.img" % (get_adb(), device.id, os.path.join(package_dir_full, "boot.img"), self.config.phone_path)
        debug("%s" % theCmd)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode != 0:
            print("ERROR: Encountered an error.")
            print(res.stderr)
            print("Aborting ...")
            return
        else:
            print(res.stdout)

        # check if transfer worked.
        print("Making sure boot.img is found on the phone in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell ls -l %s/boot.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect 0
        if res.returncode != 0:
            print("ERROR: boot.img is not found!")
            print(res.stderr)
            print("Aborting ...")
            return

        if not device.rooted:
            print("Magisk Tools not found on the phone")
            # Check to see if Magisk is installed
            print("Looking for Magisk app ...")
            if not device.magisk_version:
                print("Unable to find magisk on the phone, perhaps it is hidden?")
                # Message to Launch Manually and Patch
                title = "Magisk not found"
                message =  "WARNING: Magisk is not found on the phone\n\n"
                message += "This could be either because it is hidden, or it is not installed\n\n"
                message += "Please manually launch Magisk on your phone.\n"
                message += "- Click on `Install` and choose\n"
                message += "- `Select and Patch a File`\n"
                message += "- select boot.img in %s \n" % self.config.phone_path
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
                    return
            else:
                print("Found Magisk app on the phone.")
                print("Launching Magisk ...")
                theCmd = "\"%s\" -s %s shell monkey -p %s -c android.intent.category.LAUNCHER 1" % (get_adb(), device.id, get_magisk_package())
                res = run_shell(theCmd)
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
                message += "- select boot.img in %s \n" % self.config.phone_path
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
                    return
        else:
            startPatch = time.time()
            print(f"Detected a rooted phone with Magisk Tools: {device.magisk_version}")
            print("Creating patched boot.img ...")
            theCmd = "\"%s\" -s %s shell \"su -c \'export KEEPVERITY=true; export KEEPFORCEENCRYPT=true; ./data/adb/magisk/boot_patch.sh /sdcard/Download/boot.img; mv ./data/adb/magisk/new-boot.img /sdcard/Download/magisk_patched.img\'\"" % (get_adb(), device.id)
            res = run_shell2(theCmd)
            endPatch = time.time()
            print("Patch time: %s seconds"%(math.ceil(endPatch - startPatch)))

        # check if magisk_patched.img got created.
        print("")
        print("Looking for magisk_patched.img in %s ..." % (self.config.phone_path))
        theCmd = "\"%s\" -s %s shell ls %s/magisk_patched*.img" % (get_adb(), device.id, self.config.phone_path)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode == 1:
            print("ERROR: magisk_patched*.img not found")
            print(res.stderr)
            print("Aborting ...")
            return
        else:
            magisk_patched = res.stdout.strip()
            print("Found %s" %magisk_patched)

        # Transfer back boot.img
        print("Pulling %s from the phone ..." % (magisk_patched))
        theCmd = "\"%s\" -s %s pull %s \"%s\""  % (get_adb(), device.id, magisk_patched, os.path.join(package_dir_full, "magisk_patched.img"))
        debug("%s" % theCmd)
        res = run_shell(theCmd)
        # expect ret 0
        if res.returncode == 1:
            print("ERROR: Unable to pull magisk_patched.img from phone.")
            print(res.stderr)
            print("Aborting ...")
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
            theCmd = "\"%s\" a \"%s\" boot.img" % (path_to_7z, image_file_full)
            debug("%s" % theCmd)
            os.chdir(package_dir_full)
            res = run_shell(theCmd)
            os.chdir(cwd)
        else:
            src = os.path.join(package_dir_full, "magisk_patched.img")
            dest = os.path.join(package_dir_full, image_id, "boot.img")
            shutil.copy(src, dest, follow_symlinks=True)
            dir_name = os.path.join(package_dir, image_id)
            dest = os.path.join(package_dir_full, image_file)
            print("")
            print("Zipping  %s ..." % dir_name)
            print("Please be patient as this is a slow process and could take some time.")
            shutil.make_archive(dir_name, 'zip', dir_name)
        if os.path.exists(dest):
            print("Package is successfully created!")
            # create a marker file to confirm successful package creation, this will be checked by Flash command
            src = os.path.join(package_dir_full, "Package_Ready.json")
            set_package_ready(self, src)
            self.flash_button.Enable()
        else:
            print("ERROR: Encountered an error while preparing the package.")
            print("Aborting ...")
        endZip = time.time()
        print("Zip time: %s seconds"%(math.ceil(endZip - startZip)))
    else:
        print("Package is successfully created!")
        src = os.path.join(package_dir_full, "Package_Ready.json")
        set_package_ready(self, src)
        self.flash_button.Enable()

    end = time.time()
    print("Total elapsed time: %s seconds"%(math.ceil(end - start)))


# ============================================================================
#                               Function flash_phone
# ============================================================================
def flash_phone(self):
    if not get_adb():
        print("ERROR: Android Platform Tools must be set.")
        return

    device = get_phone()
    if not device.id:
        print("ERROR: You must first select a valid adb device.")
        return

    cwd = os.getcwd()
    package_dir = get_firmware_id()
    package_dir_full = os.path.join(cwd, package_dir)
    message = ''

    # if advanced options is set, and we have flash options ...
    if self.config.advanced_options:
        fastboot_options = ''
        if self.config.flash_both_slots:
            fastboot_options += '--slot all '
        if self.config.disable_verity:
            fastboot_options += '--disable-verity '
        if self.config.disable_verification:
            fastboot_options += '--disable-verification '
        message  = "Custom Flash Options: %s\n" % str(self.config.advanced_options)
        message += "Disable Verity:       %s\n" % str(self.config.disable_verity)
        message += "Disable Verification: %s\n" % str(self.config.disable_verification)
        message += "Flash Both Slots:     %s\n" % str(self.config.flash_both_slots)

    # delete previous flash-phone.bat file if it exists
    dest = os.path.join(package_dir_full, "flash-phone.bat")
    if os.path.exists(dest):
        os.remove(dest)

    # if we are in custom Flash mode
    if self.config.advanced_options and self.config.flash_mode == 'customFlash':
        image_mode = get_image_mode()
        if image_mode and get_image_path():
            title = "Advanced Flash Options"
            # create flash-phone.bat based on the custom options.
            f = open(dest.strip(), "w")
            f.write("@ECHO OFF\n")
            f.write(f":: This is a generated file by PixelFlasher v{VERSION}\n\n")
            f.write("PATH=%PATH%;\"%SYSTEMROOT%\System32\"\n")
            if image_mode == 'image':
                action = "update"
                msg  = "Flash:                "
            elif image_mode == 'boot' and self.live_boot_radio_button.Value:
                action = "boot"
                msg  = "Live Boot to:         "
            else:
                action = f"flash {image_mode}"
                msg  = "Flash:                "
            theCmd = f"\"{get_fastboot()}\" -s {device.id} {fastboot_options} {action} \"{get_image_path()}\""
            f.write(f"{theCmd}\n")
            f.close()
            message += f"{msg}{get_image_path()} to {image_mode}\n\n"
    else:
        # do the package flash mode
        pr = os.path.join(get_firmware_id(), "Package_Ready.json")
        if not os.path.exists(pr):
            print("ERROR: You must first prepare a patched firmware package.")
            print("       Press the `Prepare Package` Button!")
            print("")
            return

        # Make sure Phone model matches firmware model
        if get_firmware_model() != device.hardware:
            print("ERROR: Android device model %s does not match firmware Model %s" % (device.hardware, get_firmware_model()))
            return

        # replace placholder with fastboot_options.
        if self.config.flash_mode == 'dryRun':
            src = os.path.join(package_dir_full, "flash-dry-run.txt")
        elif self.config.flash_mode == 'keepData':
            src = os.path.join(package_dir_full, "flash-keep-data.txt")
        elif self.config.flash_mode == 'wipeData':
            src = os.path.join(package_dir_full, "flash-wipe-data.txt")
        else:
            print("ERROR: Bad Flash Mode!")
            print("Aborting ...")
            return
        fin = open(src, "rt")
        data = fin.read()
        data = data.replace('##PLACEHOLDER##', fastboot_options)
        fin.close()
        fin = open(dest, "wt")
        fin.write(data)
        fin.close()

        title = "Package Flash Options"
        message += get_package_ready(self, pr, includeFlashMode=True)

    # common part for package or custom flash
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
        return

    print("")
    print("==============================================================================")
    print(" PixelFlasher %s              Flashing Phone                                  " % VERSION)
    print("==============================================================================")
    startFlash = time.time()

    # Reboot to bootloader if in adb mode
    if device.mode == 'adb':
        device.reboot_bootloader()
        print("Waiting 5 seconds ...")
        time.sleep(5)
        device.refresh_phone_mode()

    # vendor_dlkm needs to be flashed in fastbootd mode
    if self.config.advanced_options and self.config.flash_mode == 'customFlash' and get_image_mode() == 'vendor_dlkm':
        device.reboot_fastboot()
        print("Waiting 5 seconds ...")
        time.sleep(5)

    # if in bootloader mode, Start flashing
    if device.mode == 'f.b' and get_fastboot():
        print(f"Flashing device {device.id} ...")
        # confirm for wipe data
        if self.config.flash_mode == 'wipeData':
            print("Flash Mode: Wipe Data")
            dlg = wx.MessageDialog(None, "You have selected to WIPE data\nAre you sure want to continue?",'Wipe Data',wx.YES_NO | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result != wx.ID_YES:
                print("User canceled flashing.")
                return

        theCmd = os.path.join(cwd, package_dir, "flash-phone.bat")
        os.chdir(package_dir)
        theCmd = "\"%s\"" % theCmd
        debug(theCmd)
        run_shell2(theCmd)
        print("Done!")
        endFlash = time.time()
        print("Flashing elapsed time: %s seconds"%(math.ceil(endFlash - startFlash)))
        os.chdir(cwd)
    else:
        print(f"ERROR: Device {device.id} not in bootloader mode.")
        print("Aborting ...")

