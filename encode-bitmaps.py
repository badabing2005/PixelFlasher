#!/usr/bin/env python

"""
This is a way to save the startup time when running img2py on lots of
files...
"""

import os
from wx.tools import img2py

command_lines = [
    "-a -F -i -n about-24 images/about-24.png images.py",
    "-a -F -i -n about-64 images/about-64.png images.py",
    "-a -F -i -n add-24 images/add-24.png images.py",
    "-a -F -i -n settings-24 images/settings-24.png images.py",
    "-a -F -i -n settings-64 images/settings-64.png images.py",
    "-a -F -i -n backup-24 images/backup-24.png images.py",
    "-a -F -i -n backup-64 images/backup-64.png images.py",
    "-a -F -i -n blank images/blank.png images.py",
    "-a -F -i -n boot-24 images/boot-24.png images.py",
    "-a -F -i -n bottom-24 images/bottom-24.png images.py",
    "-a -F -i -n bug-24 images/bug-24.png images.py",
    "-a -F -i -n custom-patch-24 images/custom-patch-24.png images.py",
    "-a -F -i -n delete-24 images/delete-24.png images.py",
    "-a -F -i -n exit-24 images/exit-24.png images.py",
    "-a -F -i -n feature-24 images/feature-24.png images.py",
    "-a -F -i -n flash-24 images/flash-24.png images.py",
    "-a -F -i -n flash-32 images/flash-32.png images.py",
    "-a -F -i -n folder-24 images/folder-24.png images.py",
    "-a -F -i -n forum-24 images/forum-24.png images.py",
    "-a -F -i -n github-24 images/github-24.png images.py",
    "-a -F -i -n guide-24 images/guide-24.png images.py",
    "-a -F -i -n Icon-256 images/icon-256.png images.py",
    "-a -F -i -n Icon-dark-256 images/icon-dark-256.png images.py",
    "-a -F -i -n install-apk-24 images/install-apk-24.png images.py",
    "-a -F -i -n install-apk-64 images/install-apk-64.png images.py",
    "-a -F -i -n install-magisk-24 images/install-magisk-24.png images.py",
    "-a -F -i -n install-magisk-64 images/install-magisk-64.png images.py",
    "-a -F -i -n left-24 images/left-24.png images.py",
    "-a -F -i -n lock-24 images/lock-24.png images.py",
    "-a -F -i -n lock-64 images/lock-64.png images.py",
    "-a -F -i -n magisk-24 images/magisk-24.png images.py",
    "-a -F -i -n magisk-64 images/magisk-64.png images.py",
    "-a -F -i -n official-16 images/official-16.png images.py",
    "-a -F -i -n official-24 images/official-24.png images.py",
    "-a -F -i -n open-link-24 images/open-link-24.png images.py",
    "-a -F -i -n open-link-red-24 images/open-link-red-24.png images.py",
    "-a -F -i -n packages-24 images/packages-24.png images.py",
    "-a -F -i -n packages-64 images/packages-64.png images.py",
    "-a -F -i -n partition-24 images/partition-24.png images.py",
    "-a -F -i -n partition-64 images/partition-64.png images.py",
    "-a -F -i -n paste-24 images/paste-24.png images.py",
    "-a -F -i -n paste-up-24 images/paste-up-24.png images.py",
    "-a -F -i -n smart-paste-up-24 images/smart-paste-up-24.png images.py",
    "-a -F -i -n paste-down-24 images/paste-down-24.png images.py",
    "-a -F -i -n patch-24 images/patch-24.png images.py",
    "-a -F -i -n patched-16 images/patched-16.png images.py",
    "-a -F -i -n patched-24 images/patched-24.png images.py",
    "-a -F -i -n process_file-24 images/process_file-24.png images.py",
    "-a -F -i -n reboot-24 images/reboot-24.png images.py",
    "-a -F -i -n reboot-64 images/reboot-64.png images.py",
    "-a -F -i -n reboot-System-24 images/reboot-system-24.png images.py",
    "-a -F -i -n reboot-system-64 images/reboot-system-64.png images.py",
    "-a -F -i -n reboot-bootloader-24 images/reboot-bootloader-24.png images.py",
    "-a -F -i -n reboot-bootloader-64 images/reboot-bootloader-64.png images.py",
    "-a -F -i -n reboot-fastbootd-24 images/reboot-fastbootd-24.png images.py",
    "-a -F -i -n reboot-fastbootd-64 images/reboot-fastbootd-64.png images.py",
    "-a -F -i -n reboot-download-24 images/reboot-download-24.png images.py",
    "-a -F -i -n reboot-download-64 images/reboot-download-64.png images.py",
    "-a -F -i -n reboot-recovery-24 images/reboot-recovery-24.png images.py",
    "-a -F -i -n reboot-recovery-64 images/reboot-recovery-64.png images.py",
    "-a -F -i -n reboot-safe-mode-24 images/reboot-safe-mode-24.png images.py",
    "-a -F -i -n reboot-safe-mode-64 images/reboot-safe-mode-64.png images.py",
    "-a -F -i -n reboot-sideload-24 images/reboot-sideload-24.png images.py",
    "-a -F -i -n reboot-sideload-64 images/reboot-sideload-64.png images.py",
    "-a -F -i -n right-24 images/right-24.png images.py",
    "-a -F -i -n scan-24 images/scan-24.png images.py",
    "-a -F -i -n shell-24 images/shell-24.png images.py",
    "-a -F -i -n shell-64 images/shell-64.png images.py",
    "-a -F -i -n shell-64-disabled images/shell-64-disabled.png images.py",
    "-a -F -i -n scrcpy-24 images/scrcpy-24.png images.py",
    "-a -F -i -n scrcpy-64 images/scrcpy-64.png images.py",
    "-a -F -i -n shield-24 images/shield-24.png images.py",
    "-a -F -i -n shield-64 images/shield-64.png images.py",
    "-a -F -i -n sos-24 images/sos-24.png images.py",
    "-a -F -i -n sos-64 images/sos-64.png images.py",
    "-a -F -i -n Splash images/splash.png images.py",
    "-a -F -i -n Splash-dark images/splash-dark.png images.py",
    "-a -F -i -n support-24 images/support-24.png images.py",
    "-a -F -i -n switch-slot-24 images/switch-slot-24.png images.py",
    "-a -F -i -n switch-slot-64 images/switch-slot-64.png images.py",
    "-a -F -i -n top-24 images/top-24.png images.py",
    "-a -F -i -n unlock-24 images/unlock-24.png images.py",
    "-a -F -i -n unlock-64 images/unlock-64.png images.py",
    "-a -F -i -n update-check-24 images/update-check-24.png images.py",
    "-a -F -i -n wifi-adb-24 images/wifi-adb-24.png images.py",
    "-a -F -i -n slot-a-48 images/slot-a-48.png images.py",
    "-a -F -i -n slot-b-48 images/slot-b-48.png images.py",
    "-a -F -i -n rooted images/rooted.png images.py",
    "-a -F -i -n watch-green-24 images/watch-green-24.png images.py",
    "-a -F -i -n watch-blue-24 images/watch-blue-24.png images.py",
    "-a -F -i -n phone-green-24 images/phone-green-24.png images.py",
    "-a -F -i -n phone-blue-24 images/phone-blue-24.png images.py",
    "-a -F -i -n disable-24 images/disable-24.png images.py",
    "-a -F -i -n enable-24 images/enable-24.png images.py",
    "-a -F -i -n download-16 images/download-16.png images.py",
    "-a -F -i -n download-24 images/download-24.png images.py",
    "-a -F -i -n uninstall-24 images/uninstall-24.png images.py",
    "-a -F -i -n launch-24 images/launch-24.png images.py",
    "-a -F -i -n kill-24 images/kill-24.png images.py",
    "-a -F -i -n clear-24 images/clear-24.png images.py",
    "-a -F -i -n check-24 images/check-24.png images.py",
    "-a -F -i -n uncheck-24 images/uncheck-24.png images.py",
    "-a -F -i -n clipboard-24 images/clipboard-24.png images.py",
    "-a -F -i -n push-24 images/push-24.png images.py",
    "-a -F -i -n push-cart-24 images/push-cart-24.png images.py",
    "-a -F -i -n json-24 images/json-24.png images.py",
    "-a -F -i -n xml-24 images/xml-24.png images.py",
    "-a -F -i -n alert-red-24 images/alert-red-24.png images.py",
    "-a -F -i -n alert-gray-24 images/alert-gray-24.png images.py",
    "-a -F -i -n pif-24 images/pif-24.png images.py",
    "-a -F -i -n pif-64 images/pif-64.png images.py",
    "-a -F -i -n heart-red-24 images/heart-red-24.png images.py",
    "-a -F -i -n heart-gray-24 images/heart-gray-24.png images.py",
    "-a -F -i -n import-24 images/import-24.png images.py",
    "-a -F -i -n cancel-ota-24 images/cancel-ota-24.png images.py",
    "-a -F -i -n factory-24 images/factory-24.png images.py",
    "-a -F -i -n cloud-24 images/cloud-24.png images.py",
    "-a -F -i -n star-green-24 images/star-green-24.png images.py",
    "-a -F -i -n e2j-24 images/e2j-24.png images.py",
    "-a -F -i -n save-24 images/save-24.png images.py",
    "-a -F -i -n kernelsu-24 images/kernelsu-24.png images.py",
    "-a -F -i -n apatch-24 images/apatch-24.png images.py",
]

if __name__ == "__main__":
    # first delete the existing images.py
    if os.path.exists("images.py"):
        os.remove("images.py")

    # create images.py with proper header
    with open('images.py', "w", encoding="ISO-8859-1", errors="replace") as f:
        header = """
#----------------------------------------------------------------------
# This file was generated by encode-bitmaps.py
#
from wx.lib.embeddedimage import PyEmbeddedImage

#----------------------------------------------------------------------
SmallUpArrow = PyEmbeddedImage(
    b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAADxJ"
    b"REFUOI1jZGRiZqAEMFGke2gY8P/f3/9kGwDTjM8QnAaga8JlCG3CAJdt2MQxDCAUaOjyjKMp"
    b"cRAYAABS2CPsss3BWQAAAABJRU5ErkJggg==")

#----------------------------------------------------------------------
SmallDnArrow = PyEmbeddedImage(
    b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAEhJ"
    b"REFUOI1jZGRiZqAEMFGke9QABgYGBgYWdIH///7+J6SJkYmZEacLkCUJacZqAD5DsInTLhDR"
    b"bcPlKrwugGnCFy6Mo3mBAQChDgRlP4RC7wAAAABJRU5ErkJggg==")

        """
        # header = "#----------------------------------------------------------------------\n"
        # header += "# This file was generated by encode-bitmaps.py\n"
        # header += "#\n"
        # header += "from wx.lib.embeddedimage import PyEmbeddedImage\n\n"
        f.write(header)

    # add all the images
    for line in command_lines:
        args = line.split()
        img2py.main(args)

