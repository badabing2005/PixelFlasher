![Image of PixelFlasher Icon](/images/icon-256.png)
# PixelFlasher [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
This is a follow up to [PixelFlasher](/scripts/PixelFlasher.ps1) `Powershell™` script (which is now moved to `scripts` directory).
This is a total rewrite in Python™ using [wxPython](https://www.wxpython.org/) to provide a UI interface.
The executable which can be found in [releases section](https://github.com/badabing2005/PixelFlasher/releases) is self contained and does not require Python™ to be installed on the system.


## DESCRIPTION
As the name suggests this is an application to flash (update) Pixel™ phones (possibly all Google™ made phones/tablets, YMMV.)
The benefits of this application are:
- Simple UI interface, click and go. No more command line.
- Fully Automated.
- Ability to pre-patch factory image with Magisk (without user interaction) and perform upgrades without loosing root.
No more multiple reboots, or setting airplane mode and clearing storage to retain Safetynet passing.
(This Assumes that the phone was previously rooted with Magisk and setup to pass safetynet)
- Ability to flash custom ROM

## Prerequisites
- [Android SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools.html)
- [Android Pixel phone factory image](https://developers.google.com/android/images)

## Installation
PixelFlasher doesn't have to be installed, just double-click it and it'll start. Check the [releases section](https://github.com/badabing2005/PixelFlasher/releases) for downloads.
It is recommended that you place the executable in its own directory, as it creates temporary files in the application folder.

## Status
Scan the [list of open issues](https://github.com/badabing2005/PixelFlasher/issues) for bugs and pending features.

**Note**
This is my first wxPython based project. I got ideas and inspiration from [nodemcu-pyflasher](https://github.com/marcelstoer/nodemcu-pyflasher)
If you have constructive feedback as for how to improve the code please do reach out to me.

## Build it yourself
If you want to build this application yourself you need to:
**Setup**
- Download or clone the repository.
- Install [Python 3.x](https://www.python.org/downloads/) and [Pip](https://pip.pypa.io/en/stable/installing/) (it comes with Python™ if installed from `python.org`).
- Install virtualenv `pip install virtualenv`
- Create a virtual environment with `virtualenv --python <PATH_TO_PYTHON_EXE> venv`
- Activate the virtual environment with `.\venv\Scripts\activate`
- Run `pip install -r requirements.txt`

**Build**
Run `build.bat`

**Note**
If you run into troubles installing wxPython, you can download wxPython wheel file matching your version of Python™ from [here](https://wxpython.org/Phoenix/snapshot-builds/?C=M;O=D)
Look for `cp310` if your python™ version is 3.10
You install it with `pip`, for example this would be the command to install 3.10 version
`pip install wxPython-4.1.2a1.dev5308+2258f215-cp310-cp310-win_amd64.whl`

## Usage

![Image of PixelFlasher GUI](/images/gui.png)

1. First thing to do is select the factory image, the application will recognize the phone model from the image name.
2. If Android™ Platform Tools is already in your `PATH` environment, the application will detect it and pre-populate it.
Otherwise you'd have to select where it is installed.
If you have multiple versions, you can select another version, although it is best to always use the most recent version.
3. If you already have your phone connected to the PC, the application will detect all ADB connected devices and populate the combo Box.
Otherwise connect your phone to your PC, and hit the `Reload` button, then select your device from the list in the combo box.
4. Select this option if you want to pre-patch the image with Magisk, assuming that Magisk is already installed on your phone.
This would be the typical choice for monthly updates.
5. **Prepare Package**: Based on the choices made in the previous 4 steps, this step creates the proper package file to be flashed later.
If the phone is already rooted, the whole process is without user interaction.
Otherwise the PixelFlasher will launch Magisk on the phone and wait for the user to select stock boot.img which would already be transferred to the phone by the PixelFlasher and guide the user to make the proper choices in Magisk to create a patched boot.img before continuing for PixelFlasher to do the rest of the work.
6. Select the Flash Mode
    - **Keep Data**: In this mode `-w` flag is removed from the flash scripts so that data is not wiped. This is commonly known as `dirty flashing`
    - **WIPE all data**: As the name suggests, this will wipe your data, use it with caution! PixelFlasher will ask for confirmation during the flashing phase, if this mode is selected.
    - **Dry Run**: In this mode, the phone will reboot to bootloader, and then mimic the flash actions (i.e. reboot into bootloader) without actually flashing anything (it prints to the console the steps it would have performed if dry run was not chosen).
    This is handy for testing to check if the PixelFlasher properly is able to control fastboot commands.
7. **Flash Pixel Phone** This is the final step, to actually execute/flash the prepared package in the selected `Flash Mode`.
PixelFlasher will first present you the package content prepared in step 6, and ask for your confirmation if you want to proceed with flashing.
Please keep in mind that if you change options after you prepare a package, those options are not applied unless you update the package.
*For example if you create a package with patching selected, and then change that option before flashing, flashing will still apply the patch. For this reason the flashing step first presents you the package choices and asks for your confirmation.*

**Apply Custom ROM**:
This is for advanced users, please make sure to read the documentation of the chosen ROM, as each custom ROM instructions could be different.
To be clear, this is what PixelFlasher does internally when this mode is selected, please understand it, and don't use it if the selected ROM guide does not fit the bill. You've been warned.
- Keeps stock bootloader and radio images.
- Replaces the stock ROM image with the selected custom ROM image.
- Flashes in the chosen `Flash Mode` just like a stock image, i.e. bootloader, custom ROM and radio images in the original order that they were in the stock firmware.
- Patching `boot.img` can be performed if the option is selected.
- Flash Mode is also as described above in step 6.


## What's Next
- I want to speed up the zipping/unzipping process, as it currently takes about 3 minutes on my system to prepare an oriole patched package.
I have few ideas on how it can be improved, if you know how or have done similar work, please do reach out to me or submit a pull request.
- Although this project can be build for other platforms, it is currently not possible as it makes some basic windows assumptions. This could easily be addressed, however I do not have a Mac to build and or test.
- I'll eventually add Github Pipeline Actions to have the assets build automatically.


## Credits
- First and foremost [Magisk](https://github.com/topjohnwu/Magisk/releases) by [John Wu](https://github.com/topjohnwu) which made rooting Pixel™ phones possible, without it none of this would have mattered.
- Big thanks to [[ryder203]](https://www.t-ryder.de/), [[t-ryder]](https://forum.xda-developers.com/m/t-ryder.3705546/) for his valuable ideas, feedback and testing. Your contributions are very much appreciated.
- [[Homeboy76]](https://forum.xda-developers.com/m/homeboy76.4810220/) at [xda](https://forum.xda-developers.com/) for his excellent [guides](https://forum.xda-developers.com/t/guide-root-pixel-6-android-12-with-magisk.4388733/) on Pixel™ series phones.
This program could not have been possible without his easy to follow guides.
I strongly encourage all beginners to follow those guides rather than use this program, it is important to understand the basic steps involved before diving into one click tools or advanced tasks.
- Marcel Stör's [nodemcu-pyflasher](https://github.com/marcelstoer/nodemcu-pyflasher) source code which jump started my introduction to [wxPython](https://www.wxpython.org/) and eventually this program.
- Endless count of [xda](https://forum.xda-developers.com/) members and their posts that tirelessly answer questions and share tools. Too many to enumerate.
## Disclaimer
```
*******************************************************************************
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
*******************************************************************************
```
