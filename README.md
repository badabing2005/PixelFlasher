# PixelFlasher
A Powershell script to update a previously rooted Pixel phone with a new factory image and retain root and derivatives as before.

## DESCRIPTION
The benefits of this script is that an upgrade is performed in a single flash / reboot step, and the phone remains rooted as it was prior to the update.
So if you had safety net passing, it will be the same, you won't need to do the multiple steps of airplane mode, clear storage, reboot ...

The script automates all of the following steps:
- Checks for the factory image
- Unpacks factory image
- Checks for dependencies (adb, fastboot, 7zip, ...)
- Unzips the factory image
- Extracts unpatched boot.img
- Deletes flash-all.sh and flash-base.sh (just for extra precaution)
- Patches flash-all.bat and removes the wipe option
- Checks and validates phone connection
- Checks and validates that the phone model matches the factory image
- Transfers stock boot.img to the phone
- Detects if Magisk Tools is installed.
- If it is, which usually is, it automatically invokes and creates a patched boot.img  
  If Magisk Tools is not found it launches Magisk and waits for the user to complete the patching on the phone.
- Transfers patched boot.img to the PC
- Replaces stock boot.img with patched boot.img
- Repackages the image zip with patched boot.img
- Reboots to bootloader
- Launches flash_all.bat to update the phone

## Prerequisites
- [Android SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools.html)
- [Android Pixel phone factory image](https://developers.google.com/android/images)
- [7z.exe from 7-Zip](https://www.7-zip.org/)

## Setup
- Download or clone the repository
- Make sure the prerequisities are met

The easiest way to run this
- copy the factory image into the script directory,
- make sure, adb.exe, fastboot.exe, and 7z.exe are in the environment path
- start powershell in the script directory
- run `./PixelFlasher.ps1` and follow the prompts.

### Note: 
To be extra cautious, the script is very verbose and prompts for confirmation on every step of the process.
Once comfortable with the steps, these confirmation prompts can be turned off by passing `-y` argument.
Example: `./PixelFlasher.ps1 -y`

There are many other arguments available for various options.
See `./PixelFlasher.ps1 -help` for usage.

## Notice
This script should theoretically work for any Pixel phone by passing the `phoneModel` parameter, however I have only tested it on Pixel 6 (oriole) which is set as the default.

## Troubleshooting
If your run into issues executing this Powershell script, it is probably due to the Powershell Execution Policy (Microsoft feature).
By default, PowerShell's execution policy is set to Restricted; this means that scripts will not run.
You can check [this](https://www.mssqltips.com/sqlservertip/2702/setting-the-powershell-execution-policy/) article to learn how to allow the script to run.
You can also check [this](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.2) document to learn all about Powershell Execution policy.
