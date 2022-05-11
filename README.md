<img src="/images/icon-128.png" align="left" />
  <h1> PixelFlasher </h1>

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Github Releases](https://img.shields.io/github/downloads/badabing2005/PixelFlasher/total.svg?style=flat)](https://github.com/badabing2005/PixelFlasher/releases)

## DESCRIPTION

As the name suggests this is an application to flash (update) Pixel™ phones (possibly all Google™ made phones/tablets, **YMMV**.)  
PixelFlasher at its core is a UI layer (with bells and whistles) on top of adb / fastboot commands, hence many of its features can be used on non Pixel devices as well. (**YMMV**).  
The executables which can be found in [releases section](https://github.com/badabing2005/PixelFlasher/releases) is self contained and does not require Python™ to be installed on the system.

The application has two modes, normal mode (basic) and advanced mode (expert).

**Basic mode:** Should suit most users. Some of the features in basic mode are:

- Simple UI interface, click and go. No more command line, no more placing all files in one directory.
- `boot.img` management UI, select the boot.img file to patch and click the patch button.
Fully Automated patching with Magisk (without user interaction) and perform upgrades without losing root.  
No more manually extracting files transferring to the phone, patching / re-flashing and doing multiple reboots.  
No more setting airplane mode and clearing storage to retain Safetynet passing.
- Display details of `boot.img`.
  - Unique ID.
  - Origin (file it was extracted from).
  - Whether it is patched or not, and if it is patched.
    - What version of Magisk was used to patch it.
    - On what device it was patched.
    - Date of patching.
- Choose to keep data or wipe data while flashing.
- Ability to flash even if multiple devices are connected to the computer.
- Display information about the phone.
  - id
  - hardware
  - current installed firmware.
  - if it is rooted with Magisk.
  - Magisk version
  - List installed Magisk modules.
  - connection mode.
- Magisk modules management, enable / disable modules selectively, this comes in handy to disable suspect modules before an upgrade. Display:
  - Name
  - Version
  - Description
  - Enabled / Disabled.
- Display Android Platform Tools (SDK) version.
- Advanced features are hidden to keep the interface simple and easy to follow.
- A lot of checks and validations for smooth operation.
- Automatic check for program updates.

**Expert mode:** (should only be turned on by experienced users). In addition to the basic features, you get:

- The ability to flash custom ROM (with or without patching `boot.img`)
- Option to flash to both slots.
- Options to disable verity and or verification.
- Ability to change the active slot.
- Ability to live boot to custom `boot.img` (temporary root).
- Ability to boot to recovery.
- Ability to flash custom image: boot, recovery, radio, kernel, ...
- Ability to sideload an image.
- Lock / Unlock bootloader.
- SOS Disable Magisk modules to get out of bootloop (experimental).

## Prerequisites

- [Android SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools.html).
- [Android Pixel phone factory image](https://developers.google.com/android/images).
- Bootloader unlocked phone (see excellent guide links in credits section below).

## Installation

PixelFlasher doesn't have to be installed, just double-click it and it'll start.  
Check the [releases section](https://github.com/badabing2005/PixelFlasher/releases) for downloads.  
It is recommended that you place the executable in its own directory, as it creates temporary files in the application folder.

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

1. First thing to do is select Android™ Platform Tools, if Android™ Platform Tools is already in your `PATH` environment, the application will detect it and pre-populate it.  
Otherwise you'd have to select where it is installed.  
You can download the lastest Android™ Platform Tools by clicking the ![Image of link](/images/open-link-16.png) next to it.  
If you have multiple versions, you can select another version, although it is best to always use the most recent version (The selected version will be identified and displayed.)  
If you already have your phone connected to the PC, the application will detect all ADB connected devices (both in adb and fastboot mode) and populate the combo box (2).  
Otherwise connect your phone to your PC, and hit the `Reload` button and select your device.
2. Select your device from the list in the combo box.
The following information about the connected device is displayed.  
    - (1st field) Rooted devices will be identified with a checkmark ✓.
    **Note:** If you want PixelFlasher to detect root, or automatically use Magisk to patch boot.img, you need to grant root permissions to `shell` in Magisk.  
    ![Image of shell root access](/images/shell-root.png)
    - (1st field) Non-Rooted devices will be identified with a ✗.
    - (1st field) Devices in fastboot mode will be identified with a ? (in fastboot mode, root status cannot be determined).
    - (2nd field) (adb) or (f.b) to indicate connection mode adb / fastboot.
    - (3rd field) Device ID.
    - (4th field) Device hardware.
    - (5th field) Current running firmware (in fastboot mode current firmware cannot be determined).
3. Next select the factory image, the application will recognize the phone model from the image name.  
You can download factory images by clicking the ![Image of link](/images/open-link-16.png) next to it.
4. Process the factory image.
PixelFlasher will extract `boot.img` file from the factory image and populate it in the list below (5).  
5. Select `boot.img` from the list, the selected `boot.img` can be patched (6), or flashed (10).
6. Optional: Select this option if you want to patch the `boot.img` with Magisk. Magisk must already be installed on your phone.  
This would be the typical choice for monthly updates.  
This option will allow updating the phone without losing root (not even temporarily).  
**Note:** See note above for granting root permissions to `shell`.  
If the phone is already rooted, the whole process is without user interaction.  
Otherwise PixelFlasher will launch Magisk on the phone and wait for the user to select stock `boot.img` which would already be transferred to the phone by the PixelFlasher and guide the user to make the proper choices in Magisk to create a patched `boot.img` before continuing for PixelFlasher to do the rest of the work.
7. If you want to flash (10) a patched `boot.img` select the newly added entry.  
The following details are listed.  
    - ![Image of patched-boot](/images/patched-16.png) Indicates that the selection is patched.
    - Boot ID is (shortened for display only) md5 of `boot.img`
    - Package ID (shortened for display only) md5 of `boot.img` extracted from the image (This should be the same as Boot ID of an unpatched `boot.img`)
    - Package Signature is just the filename portion of the image (without the extension).
    - Patched with Magisk indicates the version of Magisk used to patch the image (if applicable).
    - Patched on Device indicates the device model that performed the patching. You should always use patched images that match the model of the device that it will be flashed on.
    - Date is the either the date the `boot.img` was extracted, or the date it was patched.
    - Package Path indicates the source of the `boot.img` file.
8. Select the Flash Mode
    - **Keep Data**: In this mode `-w` flag is removed from the flash scripts so that data is not wiped. This is commonly known as `dirty flashing`
    - **WIPE all data**: As the name suggests, this will wipe your data, use it with caution! PixelFlasher will ask for confirmation during the flashing phase, if this mode is selected.
    - **Dry Run**: In this mode, the phone will reboot to bootloader, and then mimic the flash actions (i.e. reboot into bootloader) without actually flashing anything (it prints to the console the steps it would have performed if dry run was not chosen).
    This is handy for testing to check if the PixelFlasher properly is able to control fastboot commands.
9. Optional: Open Magisk Modules Manager and disable (uncheck) modules known to cause issues during upgrades (the below list has never caused issues for me, so I keep them enabled **YMMV**).  
![Image of PixelFlasher GUI](/images/magisk-modules-manager.png)
10. **Flash Pixel Phone** This is the final step, to actually flash the phone in the selected `Flash Mode`.  
**Note**: Unlike the previous versions of the PixelFlasher, all the options are dynamic, i.e. depending on what you select before clicking the Flash button, there is no more concept of prepared package.
PixelFlasher will first present you the selected options and ask for your confirmation if you want to proceed with flashing.

### Expert Mode

To enable the export mode use the **File Menu | Advanced Configuration** and select `Enable Advanced Options`
![Image of PixelFlasher GUI](/images/advanced-options.png)
![Image of PixelFlasher GUI](/images/advanced-gui.png)

In this mode the following additional options are exposed (green bounding boxes), below notes are more for enumeration than a guide, as they should be trivial and obvious to an expert.

1. Option to Change the Active Slot (the inactive slot is automatically selected).  
Option to reboot to Recovery.
2. Options to Lock / Unlock bootloader, Option to disable Magisk modules when bootlooping.
3. Apply Custom ROM. This replaces the factory ROM image with the selected file.  
PixelFlasher extracts `boot.img` from the ROM image and displays below for selection or patching.
Please make sure to read the documentation of the chosen ROM, as each custom ROM instructions could be different.  
To be clear, this is what PixelFlasher does internally when this mode is selected, please understand it, and don't use it if the selected ROM guide does not fit the bill.
You've been warned!
    - Keeps stock bootloader and radio images.
    - Replaces the stock ROM image with the selected custom ROM image.
    - Flashes in the chosen `Flash Mode` just like a stock image, i.e. bootloader, custom ROM and radio images in the original order that they were in the stock firmware.
    - Patching `boot.img` can be performed if the option is selected. You can select any of the listed `boot.img`.
    - Flash Mode is similar to basic flash mode described above in step 7.  
4. Custom Flash. select this to switch from flashing a Factory Image to flashing a single file.
5. Browse to select a a valid image file (.img or .zip).  
Choose the dropdown to select image type.  
    - boot (can be flashed to Live or boot) - Expected file type .img
    - bootloader - Expected file type .img
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

## Credits

- First and foremost [Magisk](https://github.com/topjohnwu/Magisk/releases) by [John Wu](https://github.com/topjohnwu) which made rooting Pixel™ phones possible, without it none of this would have mattered.
- Big thanks to [[ryder203]](https://www.t-ryder.de/), [[t-ryder]](https://forum.xda-developers.com/m/t-ryder.3705546/) for his valuable ideas, feedback and testing. Your contributions are very much appreciated.
- [[Homeboy76]](https://forum.xda-developers.com/m/homeboy76.4810220/) and [[v0latyle]](https://forum.xda-developers.com/m/v0latyle.3690504/) at [xda](https://forum.xda-developers.com/) for their excellent guides [[here](https://forum.xda-developers.com/t/guide-root-pixel-6-android-12-with-magisk.4388733/) and [here](https://forum.xda-developers.com/t/guide-root-pixel-6-oriole-with-magisk.4356233/)] on Pixel™ series phones.
This program could not have been possible without their easy to follow guides.  
I strongly encourage all beginners to follow those guides rather than use this program, it is important to understand the basic steps involved before diving into one click tools or advanced tasks.
- Marcel Stör's [nodemcu-pyflasher](https://github.com/marcelstoer/nodemcu-pyflasher) source code which jump started my introduction to [wxPython](https://www.wxpython.org/) and eventually this program.
- [JackMcKew](https://github.com/JackMcKew) for pyinstaller Github Actions.
- Endless counts of [xda](https://forum.xda-developers.com/) members and their posts that tirelessly answer questions and share tools. Too many to enumerate.

## Disclaimer

```
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
