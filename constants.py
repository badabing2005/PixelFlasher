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

APPNAME = 'PixelFlasher'
CONFIG_FILE_NAME = 'PixelFlasher.json'
VERSION = '7.11.3.1'
SDKVERSION = '33.0.3'
MAIN_WIDTH = 1400
MAIN_HEIGHT = 1040
MAGISK_WIDTH = 1400
MAGISK_HEIGHT = 1040
PIF_WIDTH = 1150
PIF_HEIGHT = 840
POS_X = 40
POS_Y = 40
KNOWN_INIT_BOOT_DEVICES = ['panther', 'cheetah', 'lynx', 'tangorpro', 'felix', 'shiba', 'husky', 'aurora', 'eos', 'akita', 'tokay', 'caiman', 'komodo', 'comet', 'solios', 'seluna']
KNOWN_BAD_MAGISKS = ['7dbfba76:25207', 'e5641d5b:25208', '2717feac:25209', '981ccabb:25210', '69529ac5:25211', 'e2545e57:26001', '26.0:26000', 'a8c4a33e:26103']
PIF_UPDATE_URL = 'https://raw.githubusercontent.com/chiteroman/PlayIntegrityFix/main/update.json'
OSM0SIS_PIF_UPDATE_URL = 'https://raw.githubusercontent.com/osm0sis/PlayIntegrityFork/main/update.json'
TRICKYSTORE_UPDATE_URL = 'https://raw.githubusercontent.com/5ec1cff/TrickyStore/main/update.json' # non-existent, just a placeholder
PIF_JSON_PATH = '/data/adb/pif.json'
XIAOMI_URL = "https://sourceforge.net/projects/xiaomi-eu-multilang-miui-roms/rss?path=/xiaomi.eu/Xiaomi.eu-app"
FREEMANURL = "https://codeload.github.com/TheFreeman193/PIFS/zip/refs/heads/main"
SCRCPYURL = "https://github.com/Genymobile/scrcpy/releases/latest"
PIXEL_WATCHES = ['solios', 'seluna', 'eos', 'aurora', 'r11', 'r11btwifi']
MAGISK_PKG_NAME = 'com.topjohnwu.magisk'
MAGISK_ALPHA_PKG_NAME = 'io.github.vvb2060.magisk'
MAGISK_DELTA_PKG_NAME = 'io.github.huskydg.magisk'
KERNEL_SU_PKG_NAME = 'me.weishu.kernelsu'
KSU_NEXT_PKG_NAME = 'com.rifsxd.ksunext'
APATCH_PKG_NAME = 'me.bmax.apatch'
APATCH_NEXT_PKG_NAME = 'me.garfieldhan.apatch.next'
ZYGISK_NEXT_UPDATE_URL = 'https://api.nullptr.icu/android/zygisk-next/static/update.json'

# https://xdaforums.com/t/module-play-integrity-fix-safetynet-fix.4607985/page-518#post-89308909
BANNED_KERNELS = [
    '-AICP',
    '-arter97',
    '-blu_spark',
    '-CAF',
    '-cm-',
    '-crDroid',
    '-crdroid',
    '-CyanogenMod',
    '-Deathly',
    '-EAS-',
    '-eas-',
    '-ElementalX',
    '-Elite',
    '-franco',
    '-hadesKernel',
    '-Lineage-',
    '-lineage-',
    '-LineageOS',
    '-lineageos',
    '-mokee'
    '-MoRoKernel',
    '-Noble',
    '-Optimus',
    '-SlimRoms',
    '-Sultan',
    '-sultan'
]

SHADOW_BANNED_ISSUERS = [
    '13fd9052d73ab08658c44740d915f693',
    'b701bdebaa0e163c4983ef449cf2273a'
]

# Links menu data structure
LINKS_MENU_DATA = [
    # Format: (label, image_name, url)
    # Guides
    ("Homeboy76's Guide", "guide_24", "https://xdaforums.com/t/guide-november-6-2023-root-pixel-8-pro-unlock-bootloader-pass-safetynet-both-slots-bootable-more.4638510/#post-89128833/"),
    ("V0latyle's Guide", "guide_24", "https://xdaforums.com/t/guide-root-pixel-6-oriole-with-magisk.4356233/"),
    ("roirraW's Guide", "guide_24", "https://xdaforums.com/t/december-5-2022-tq1a-221205-011-global-012-o2-uk-unlock-bootloader-root-pixel-7-pro-cheetah-safetynet.4502805/"),
    None,  # Separator
    # FAQ and info
    ("osm0sis's PIF FAQ", "forum_24", "https://xdaforums.com/t/pif-faq.4653307/"),
    ("V0latyle's PI API Info", "forum_24", "https://xdaforums.com/t/info-play-integrity-api-replacement-for-safetynet.4479337"),
    ("chiteroman's PlayIntegrityFix", "forum_24", "https://xdaforums.com/t/module-play-integrity-fix-safetynet-fix.4607985"),
    ("Tricky Store (Support Thread)", "forum_24", "https://xdaforums.com/t/tricky-store-bootloader-keybox-spoofing.4683446"),
    None,  # Separator
    # GitHub repos
    ("osm0sis's PlayIntegrityFork", "github_24", "https://github.com/osm0sis/PlayIntegrityFork"),
    ("chiteroman's PlayIntegrityFix", "github_24", "https://github.com/chiteroman/PlayIntegrityFix"),
    ("5ec1cff's TrickyStore", "github_24", "https://github.com/5ec1cff/TrickyStore"),
    None,  # Separator
    # References
    ("Get the Google USB Driver", "android_24", "https://developer.android.com/studio/run/win-usb?authuser=1%2F"),
    ("Android Security Update Bulletins", "android_24", "https://source.android.com/docs/security/bulletin/"),
    ("Android Codenames, tags, and build numbers", "android_24", "https://source.android.com/docs/setup/reference/build-numbers"),
    None,  # Separator
    # Device images
    ("Full OTA Images for Pixel Phones / Tablets", "google_24", 'https://developers.google.com/android/ota'),
    ("Factory Images for Pixel Phones / Tablets", "google_24", 'https://developers.google.com/android/ota'),
    ("Full OTA Images for Pixel Watches", "google_24", 'https://developers.google.com/android/ota-watch'),
    ("Factory Images for Pixel Watches", "google_24", 'https://developers.google.com/android/images-watch'),
    None,  # Separator
    # Beta images
    ("Full OTA Images for Pixel Beta 16", "android_24", 'https://developer.android.com/about/versions/15/download-ota'),
    ("Factory Images for Pixel Beta 16", "android_24", 'https://developer.android.com/about/versions/15/download'),
]

# Help menu URLs and descriptions
HELP_MENU_ITEMS = {
    "issue": {
        "url": "https://github.com/badabing2005/PixelFlasher/issues/new",
        "description": "Report an Issue"
    },
    "feature": {
        "url": "https://github.com/badabing2005/PixelFlasher/issues/new",
        "description": "Feature Request"
    },
    "project": {
        "url": "https://github.com/badabing2005/PixelFlasher",
        "description": "PixelFlasher Project Page"
    },
    "forum": {
        "url": "https://xdaforums.com/t/pixelflasher-gui-tool-that-facilitates-flashing-updating-pixel-phones.4415453/",
        "description": "PixelFlasher Community (Forum)"
    }
}
