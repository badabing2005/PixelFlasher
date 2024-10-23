<img src="/images/icon-dark-128.png" alt="PixelFlasher Icon" align="left" />
  <h1> PixelFlasher </h1>

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Github Releases](https://img.shields.io/github/downloads/badabing2005/PixelFlasher/total.svg?style=flat)](https://github.com/badabing2005/PixelFlasher/releases)

## DESCRIPTION

As the name suggests this is an application to flash (update) Pixel™ phones (possibly all Google™ made phones/tablets, YMMV.)  
PixelFlasher at its core is a UI layer (with bells and whistles) on top of adb / fastboot commands, hence many of its features can be used on non Pixel devices as well. (YMMV).  
The executable which can be found in [releases section](https://github.com/badabing2005/PixelFlasher/releases) is self contained and does not require Python™ to be installed on the system.

The application has two modes, normal mode (basic) and advanced mode (expert).

**Basic mode:** Should suit most users. Some of the features in basic mode are:

- Simple UI interface, click and go. No more command line, no more placing all files in one directory.
- `boot.img` / `init_boot.img` management UI, select the boot / init_boot file to patch and click the patch button.
Fully Automated patching with Magisk (without manual steps) and perform upgrades without losing root.  
No more manually extracting files transferring to the phone, patching / re-flashing and doing multiple reboots.  
No more setting airplane mode and clearing storage to retain Safetynet / Play Integrity passing.
- Display details of `boot.img` (or `init_boot.img` for Pixel 7 or newer devices).
  - SHA1 checksum.
  - Origin (file it was extracted from).
  - Whether it is patched or not, and if it is patched.
    - What version of Magisk was used to patch it.
    - On what device it was patched.
    - Date of patching.
    - The SHA1 of the source boot.img file.
  - Option to Live boot from a choice of boot.img or patched image.
  - Flash just the boot / init_boot image.
- Choose to keep data or wipe data while flashing (Full OTA flashing always keeps data).
- Ability to flash even if multiple devices are connected to the computer.
- Option to flash to inactive slot (Full OTA always flashes to inactive slot).
- Display information about the phone.
  - ID
  - Hardware model.
  - Device architecture.
  - Current installed firmware (build).
  - If it is rooted with Magisk.
  - Magisk version (Magisk Tools).
  - Magisk Manager version (the app).
  - List installed Magisk modules.
  - Connection mode (Adb | Fastboot | Sideload | Recovery).
  - Bootloader version.
  - Active slot.
  - Android OS API version.
  - Convenient quick links to download Android platform tools or device firmware.
  - And a lot more...
- Magisk Manager installation UI, [screenshot](images/Magisk-Installer.png). Supported versions:
  - stable (official)
  - beta (official)
  - canary (official)
  - debug (official)
  - delta
  - special builds that disable modules (used to recover from bootloops due to bad module(s) when safe mode does not work).
- Magisk Backup Manager, [screenshot](images/Magisk-Backup-Manager.png).
  - List all Magisk backups currently on the device.
  - Highlight the one that is backup of the current installed version.
  - Delete backups.
  - Manually add backup from PC.
  - Auto Backup: PixelFlasher figures out what needs to be backed up, and if it finds it on the PC, it creates the backup.
- Magisk settings management, [screenshot](images/magisk-settings.png):
  - Enable / disable Magisk modules, this comes in handy to disable suspect modules before an upgrade.
  - Install Magisk module.
  - Enable / disable Zygisk.
  - Enable / disable Magisk denylist.
  - Add / remove application to Magisk denylist (through PixelFlasher's App Manger).
  - Grant / deny / SU permissions to an app, with control of (through PixelFlasher's App Manger):
    - Enable / disable notifications
    - Enable / disable logging
    - Grant until (Forever, 10 min, 20 min, 30 min, 60 min)
  - Revoke SU permissions
- Display Android Platform Tools (SDK) version and warn / block if the version is old.
- Install APK (an app) file from the computer onto the device.
- Wireless Manager, to wirelessly connect to adb debug or adb wireless with pairing support.
- Advanced features are hidden to keep the interface simple and easy to follow.
- Easily open ADB shell to the device.
- Support for Genymotion Scrcpy to mirror Android devices (video and audio) via USB or over TCP/IP, and allows to control the device with the keyboard and the mouse of the computer.
- A lot of checks and validations for smooth operation with quite verbose console output to inform about every step of the operation.
- Automatic check for program updates.
- Package (Application) Manager, [screenshot](images/Package-Manager.png):
  - Disable (Freeze)
  - Enable
  - Uninstall
  - Install APK
  - Download APK
  - Multi-Select
  - Show Package Details.
  - Add app to Magisk denylist.
  - Control app's superuser permissions, [screenshot](images/su-permissions.png).

**Expert mode:** (should only be turned on by experienced users). In addition to the basic features, you get:

- The ability to flash custom ROM (with or without patching `boot` / `init_boot`)
- Option to flash to both slots.
- Options to disable verity and or verification.
- Ability to change the active slot.
- Ability to live boot to custom `boot` / `init_boot` (temporary root).
- Ability to boot to recovery, fastbootd, safe mode, download mode and sideload.
- Ability to flash custom image: boot, recovery, radio, kernel, ...
- Ability to sideload an image.
- Lock / Unlock bootloader.
- Option to gain temporary root (good for testing or checking things out).
- SOS Disable Magisk modules to get out of bootloop (experimental).
- Force option when flashing.
- Option to skip rebooting.
- Option to wipe.
- Partition Manager:
  - Erase single or multi partitions.
  - Dump / create backup of single or multi partitions and save to PC.

## Prerequisites

- [Android SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools.html).
- Android Pixel phone [factory image](https://developers.google.com/android/images) or Android Pixel phone [full OTA image](https://developers.google.com/android/ota).
- Bootloader unlocked phone (see excellent guide links in credits section below).
- On Windows: The latest [Google USB drivers](https://developer.android.com/studio/run/win-usb?authuser=1%2F) installed in adb and fastboot modes.
- On MacOS: [Allow USB Accessory to connect](https://support.apple.com/en-us/102282) (very important!).
- On Linux: [User needs to be added](https://developer.android.com/studio/run/device#setting-up) to `plugdev` group.

## Installation

PixelFlasher doesn't have to be installed, just double-click it and it'll start.  
Check the [releases section](https://github.com/badabing2005/PixelFlasher/releases) for downloads.  

### Supported platforms  

- Windows
- macOS. Download the DMG or Install via [Homebrew](https://brew.sh) by a single command:

  ```bash
  brew install badabing2005/pixelflasher/pixelflasher
  ```

- Linux (See [this](https://github.com/badabing2005/PixelFlasher/issues/23) if you're having issues with a Linux build.)

## Status

Scan the [list of open issues](https://github.com/badabing2005/PixelFlasher/issues) for bugs and pending features.

**Note**
This is my first wxPython based project. I got ideas and inspiration from [nodemcu-pyflasher](https://github.com/marcelstoer/nodemcu-pyflasher).  
If you have constructive feedback as for how to improve the code please do reach out to me.

## Build it yourself

If you want to build this application yourself you need to:
**Setup**

- Download or clone the repository.
- Install [Python 3.x](https://www.python.org/downloads/) and [Pip](https://pip.pypa.io/en/stable/installing/) (it comes with Python™ if installed from `python.org`)  
_See note below if building on MacOS._
- Install virtualenv `pip3 install virtualenv`
- Create a virtual environment with:
  - On Windows: `virtualenv --python <PATH_TO_PYTHON_EXE> venv`
  - On Linux / MacOS: `python3 -m venv venv`
- Activate the virtual environment with:
  - On Windows: `.\venv\Scripts\activate`
  - On Linux / MacOS: `. venv/bin/activate`
- Run `pip3 install -r requirements.txt`

**A note on Linux:** As described on the [downloads section of `wxPython`](https://www.wxpython.org/pages/downloads/), wheels for Linux are complicated and may require you to run something like this to install `wxPython` correctly:

```bash
# Assuming you are running it on Ubuntu 20.04 LTS with GTK3
pip install -U \
    -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 \
    wxPython
```

**A note on Windows**
If you run into troubles installing wxPython on Windows, you can download wxPython wheel file matching your version of Python™ from [here](https://wxpython.org/Phoenix/snapshot-builds/?C=M;O=D)
Look for `cp310` if your python™ version is 3.10
You install it with `pip`, for example this would be the command to install 3.10 version.

```bash
pip install wxPython-4.1.2a1.dev5308+2258f215-cp310-cp310-win_amd64.whl
```

**A Note on MacOS**
Don't install Python™ on MacOS, instead
`brew install wxpython`, this will install Python™ 3.9.12, the installed wxPython will only work with this version of Python.
If python 3.9.12 is not in the system path, you can find it here:  
`/usr/local/Cellar/python@3.9/3.9.12/Frameworks/Python.framework/Versions/3.9/bin`  
It is advised that you add this to your system `PATH`
On MacOS, you should also install `create-dmg`

```bash
brew install node graphicsmagick imagemagick 
npm install --global create-dmg
```

**Build**
Run `build.bat` on Windows or `build.sh` on Linux / MacOS.

## Usage

### Basic Mode

![Image of PixelFlasher GUI](/images/basic-gui.png)

1. First thing to do is select Android™ Platform Tools, you'd have to select where it is installed (unpacked).
You can download the latest Android™ Platform Tools by clicking the ![Image of link](/images/open-link-16.png) next to it.  
If you have multiple versions, you can select another version, although it is best to always use the most recent version (The selected version will be identified and displayed.)  
2. Hit the `Scan` button to detect connected devices, the application will detect all connected devices  
(in adb, fastboot, sideload, recovery modes) and populate the combo box (2).
3. Select your device from the list in the combo box.
The following information about the connected device is displayed.  
    - (1st field) Rooted devices will be identified with a checkmark ✓.
    **Note:** If you want PixelFlasher to detect root, or automatically use Magisk to patch boot.img, you need to grant root permissions to `shell` in Magisk.  
    ![Image of shell root access](/images/shell-root.png)
    - (1st field) Non-Rooted devices will be identified with a ✗.
    - (1st field) Devices in fastboot mode will be identified with a ? (in fastboot mode, root status cannot be determined).
    - (2nd field) (adb), (f.b), (sid) or (rec) to indicate connection mode adb / fastboot / sideload / recovery.
    - (3rd field) Device ID.
    - (4th field) Device hardware.
    - (5th field) Current running firmware (in fastboot mode current firmware cannot be determined).
4. Next select the full OTA (recommended) or factory zip file (don't unzip), the application will recognize the phone model from the image name and validate the SHA-256 checksum.  
You can download [factory images](https://developers.google.com/android/images) by clicking the ![Image of link](/images/open-link-16.png) next to it.
You can download full OTA images from [here](https://developers.google.com/android/ota).
**Note:** Because both firmware package and full OTA are complete images, you can upgrade to any newer version without worrying about jumping versions (downgrades with factory image are possible only with wipe data).
5. Process the full OTA or factory image.
PixelFlasher will extract `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) file from the image and populate it in the list below (5).  
6. Select `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) from the list, the selected file can be patched (6), or flashed (10).
7. Optional: Select this option if you want to patch the `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) with Magisk. If Magisk is not already installed on your phone, PixelFlasher will install it for you.
Your phone does not need to be rooted to create a patched file.
This would be the typical choice for monthly updates.  
This option will allow updating the phone without losing root (not even temporarily).  
**Note:** See note above for granting root permissions to `shell`.  
Whether the phone is rooted or not, the whole process is without any manual step.  
8. If you want to flash (10) a patched `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) select the newly added entry.  
The following details are listed.  
    - ![Image of patched-boot](/images/patched-16.png) Indicates that the selection is patched.
    - **SHA1** is (shortened for display only) sha1 of `boot.img` (or `init_boot.img` for Pixel 7 or newer devices)
    - **Source SHA1** (shortened for display only) SHA1 of source `boot.img` extracted from the image (This should be the same as SHA1 of an unpatched `boot.img`)
    - **Package Fingerprint** is just the filename portion of the image (without the extension).
    - **Patched with Version** indicates the version of Magisk / KernelSU / Apatch used to patch the image (if applicable).
    - **Patched Method** indicates what method PixelFlasher used to create a patch (possible options: `root`, `app`, `uiautomator`, `manual`)
    - **Patched on Device** indicates the device model that performed the patching. You should always use patched images that match the model of the device that it will be flashed on.
    - **Date** is the either the date the `boot.img` was extracted, or the date it was patched.
    - **Package Path** indicates the file from which `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) was extracted.
9. Select the Flash Mode, PixelFlasher will automatically select applicable flash mode based on the selected image type.
    - If full OTA image is selected in step 4:
      - **Full OTA**: Will flash full OTA image in sideload mode.
      Features of this mode:
        - This will always flash to **inactive slot only**, (hence why the option to flash to both slots is disabled) similar to how OTA updates happen on the phone.
        - It will always be **Keep Data**, there is no option for **Wipe**, hence why the option is disabled.
        - If something goes wrong during flashing, the active flash is unaffected and the phone boots back to active functional slot.
        - If you flash to both slots (ie flash twice in a row) then both slots would be bootable.
        - Your phone's bootloader does not have to be unlocked to be able to flash full OTA image (stock boot only).
        - You cannot downgrade with OTA, the version being installed has to be equal or higher.
    - If factory firmware is selected in step 4:
      - **Keep Data**: In this mode `-w` flag is removed from the flash scripts so that data is not wiped. This is commonly known as `dirty flashing`.
      - **WIPE all data**: As the text suggests, this will wipe your data, use it with caution!  
      If this mode is selected PixelFlasher will ask for confirmation during the flashing phase.
      - **Dry Run**: In this mode, the phone will reboot to bootloader, and then mimic the flash actions (i.e. reboot into bootloader) without actually flashing anything (it prints to the console the steps it would have performed if dry run was not chosen).
      This is handy for testing to check if the PixelFlasher properly is able to control fastboot commands.
10. Optional: Open Magisk Modules Manager and disable (uncheck) modules known to cause issues during upgrades (highly recommended). (The list below has never caused issues for me, so I keep them enabled YMMV).  
![Image of PixelFlasher GUI](/images/magisk-modules-manager.png)
11. **Flash Pixel Phone** This is the final step, to actually flash the phone in the selected `Flash Mode`.  
**Note**: Unlike the previous versions of the PixelFlasher, all the options are dynamic, i.e. depending on what you select before clicking the Flash button, there is no more concept of prepared package.
PixelFlasher will first present you the selected options and ask for your confirmation if you want to proceed with flashing.
12. Monitor the **console** output and observe the performed actions and their outcomes.
13. In case of trouble, click on **Support** button to generate encrypted and optionally sanitized (redacted) support logs archive.

### Expert Mode

To enable the export mode use the **File Menu | Advanced Configuration** and select `Enable Advanced Options`
![Image of PixelFlasher GUI](/images/advanced-options.png)
![Image of PixelFlasher GUI](/images/advanced-gui.png)

In this mode the following additional options are exposed (green bounding boxes), below notes are more for enumeration than a guide, as they should be trivial and obvious to an expert.

1. Option to Change the Active Slot (the inactive slot is automatically selected).  
Options to reboot to Recovery, Download, Safe Mode.
2. Options to Lock / Unlock bootloader, Option to disable Magisk modules when bootlooping, partitions manager.
3. Apply Custom ROM. This replaces the factory ROM image with the selected file.  
PixelFlasher extracts `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) from the ROM image and displays below for selection or patching.
Please make sure to read the documentation of the chosen ROM, as each custom ROM instructions could be different.  
To be clear, this is what PixelFlasher does internally when this mode is selected, please understand it, and don't use it if the selected ROM guide does not fit the bill.
You've been warned!
    - Keeps stock bootloader and radio images.
    - Replaces the stock ROM image with the selected custom ROM image.
    - Flashes in the chosen `Flash Mode` just like a stock image, i.e. bootloader, custom ROM and radio images in the original order that they were in the stock firmware.
    - Patching `boot.img` (or `init_boot.img` for Pixel 7 or newer devices) can be performed if the option is selected. You can select any of the listed files.
    - Flash Mode is similar to basic flash mode described above in step 7.  
4. Custom Flash. select this to switch from flashing a Factory Image to flashing a single file.
5. Browse to select a a valid image file (.img or .zip).
Or select a boot.img from the list above and click on the paste button to paste the selected boot.img into the file selection.
Choose the dropdown to select image type.  
    - boot (can be flashed to Live or boot) - Expected file type .img
    - bootloader - Expected file type .img
    - init_boot - Expected file type .img
    - dtbo - Expected file type .img
    - product - Expected file type .img
    - radio - Expected file type .img
    - recovery - Expected file type .img
    - super_empty - Expected file type .img
    - system - Expected file type .img
    - system_ext - Expected file type .img
    - system_other - Expected file type .img
    - vbmeta - Expected file type .img
    - vbmeta_system - Expected file type .img
    - vbmeta_vendor - Expected file type .img
    - vendor - Expected file type .img
    - vendor_boot - Expected file type .img
    - vendor_dlkm (the device will be put into fastbootd mode during this operation) - Expected file type .img
    - image - Expected file type .zip
    - SIDELOAD - Expected file type .zip  
Select the appropriate flash options.
**Note:** For Tensor devices (Pixel 6 or newer devices) When `Flash to both slots` option is selected, Pixelflasher flashes each slot individually to overcome a Google bug that fails with the option `--slot=all`

## Credits

- First and foremost [Magisk](https://github.com/topjohnwu/Magisk/releases) by [John Wu](https://github.com/topjohnwu) which made rooting Pixel™ phones possible, without it none of this would have mattered.
- Big thanks to [[ryder203]](https://www.t-ryder.de/), [[t-ryder]](https://xdaforums.com/m/t-ryder.3705546/) for his valuable ideas, feedback and testing. Your contributions are very much appreciated.
- [[Homeboy76]](https://xdaforums.com/m/homeboy76.4810220/), [[v0latyle]](https://xdaforums.com/m/v0latyle.3690504/) and [[roirraW-edor-ehT]](https://xdaforums.com/m/roirraw-edor-eht.2560614/) at [xda](https://xdaforums.com/) for their excellent guides [[here](https://xdaforums.com/t/guide-november-6-2023-root-pixel-8-pro-unlock-bootloader-pass-safetynet-both-slots-bootable-more.4638510/#post-89128833/), [here](https://xdaforums.com/t/guide-pixel-6-oriole-unlock-bootloader-update-root-pass-safetynet.4356233/) and [here](https://xdaforums.com/t/november-6-2023-ud1a-231105-004-magisk-stable-v26-4-released-unlock-bootloader-root-pixel-8-pro-husky-safetynet.4633839/)] on Pixel™ series phones.
This program could not have been possible without their easy to follow guides.  
I strongly encourage all beginners to follow those guides rather than use this program, it is important to understand the basic steps involved before diving into one click tools or advanced tasks.
- Marcel Stör's [nodemcu-pyflasher](https://github.com/marcelstoer/nodemcu-pyflasher) source code which jump started my introduction to [wxPython](https://www.wxpython.org/) and eventually this program.
- [wxPython Team](https://wxpython.org/) for their cross-platform GUI toolkit for Python.
- [JackMcKew](https://github.com/JackMcKew) for pyinstaller Github Actions.
- Endless counts of [xda](https://xdaforums.com/) members and their posts that tirelessly answer questions and share tools. Too many to enumerate.
- Artwork / graphics / icons, designed and supplied by: [[ryder203]](https://www.t-ryder.de/), [[t-ryder]](https://xdaforums.com/m/t-ryder.3705546/) based on [material-design-icons](https://github.com/google/material-design-icons/blob/master/LICENSE)
- vm03's [payload_dumper](https://github.com/vm03/payload_dumper) source code to extract images from payload.bin files.

## Troubleshooting

If you need support or assistance, please **generate and provide a support file** from within PixelFlasher.
You can hit that big Support button on the main screen, or select it from the Help menu.
The generated support.zip file is encrypted and optionally sanitized (redacted) to keep your sensitive information (username device id ...) private.

- If your anti-virus program is telling you that PixelFlasher is a malware, or you are concerned in any way, please check [this post](https://xdaforums.com/t/pixelflasher-a-gui-tool-for-flashing-updating-rooting-managing-pixel-phones.4415453/post-89090938) about false positives.

## Disclaimer

```text
********************************************************************************
PLEASE DO YOUR PART AND READ / SEARCH / RESEARCH BEFORE USING THIS PROGRAM
AND/OR ATTEMPTING ANY MODIFICATIONS ON YOUR DEVICE.
THIS PROGRAM ASSUMES THAT YOU ALREADY KNOW HOW TO AND HAVE ALREADY UNLOCKED
YOUR BOOTLOADER, ALREADY ROOTED YOUR DEVICE, AND KNOW HOW TO USE ANDROID SDK
PLATFORM-TOOLS, ETC.
THIS TOOL IS SIMPLY MY QUICK WAY OF UPDATING THE FIRMWARE WHILE ROOTED WITH
MAGISK, WITHOUT LOSING DATA / REQUIRING A WIPE.

MODIFYING YOUR DEVICE COMES WITH INHERENT RISKS, AND IT'S NOT MY RESPONSIBILITY
IF YOU LOSE YOUR DATA OR BRICK YOUR DEVICE. THE TOOL I SHARE HAVE WORKED FOR ME,
BUT THAT DOESN'T MEAN THAT YOU MAY NOT RUN INTO PROBLEMS. **BACKUP YOUR DATA.**
********************************************************************************
```
