#!/usr/bin/env python

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2024 Badabing2005
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
VERSION = '7.4.2.2'
SDKVERSION = '33.0.3'
MAIN_WIDTH = 1400
MAIN_HEIGHT = 1040
MAGISK_WIDTH = 1400
MAGISK_HEIGHT = 1040
PIF_WIDTH = 1150
PIF_HEIGHT = 840
POS_X = 40
POS_Y = 40
KNOWN_INIT_BOOT_DEVICES = ['panther', 'cheetah', 'lynx', 'tangorpro', 'felix', 'shiba', 'husky', 'aurora', 'eos', 'akita', 'tokay', 'caiman', 'komodo', 'comet', 'selene', 'helios', 'luna', 'sol']
KNOWN_BAD_MAGISKS = ['7dbfba76:25207', 'e5641d5b:25208', '2717feac:25209', '981ccabb:25210', '69529ac5:25211', 'e2545e57:26001', '26.0:26000', 'a8c4a33e:26103']
FACTORY_IMAGES_FOR_PIXEL_DEVICES = 'https://developers.google.com/android/images'
FULL_OTA_IMAGES_FOR_PIXEL_DEVICES = 'https://developers.google.com/android/ota'
FACTORY_IMAGES_FOR_WATCH_DEVICES = 'https://developers.google.com/android/images-watch'
FULL_OTA_IMAGES_FOR_WATCH_DEVICES = 'https://developers.google.com/android/ota-watch'
FACTORY_IMAGES_FOR_BETA = 'https://developer.android.com/about/versions/15/download'
FULL_OTA_IMAGES_FOR_BETA = 'https://developer.android.com/about/versions/15/download-ota'
PIF_UPDATE_URL = 'https://raw.githubusercontent.com/chiteroman/PlayIntegrityFix/main/update.json'
OSM0SIS_PIF_UPDATE_URL = 'https://raw.githubusercontent.com/osm0sis/PlayIntegrityFork/main/update.json'
TRICKYSTORE_UPDATE_URL = 'https://raw.githubusercontent.com/5ec1cff/TrickyStore/main/update.json' # non-existent, just a placeholder
PIF_JSON_PATH = '/data/adb/pif.json'
XIAOMI_URL = "https://sourceforge.net/projects/xiaomi-eu-multilang-miui-roms/rss?path=/xiaomi.eu/Xiaomi.eu-app"
FREEMANURL = "https://codeload.github.com/TheFreeman193/PIFS/zip/refs/heads/main"
SCRCPYURL = "https://github.com/Genymobile/scrcpy/releases/latest"
PIXEL_WATCHES = ['selene', 'helios', 'luna', 'sol', 'eos', 'aurora', 'r11', 'r11btwifi']
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
MAGISK_PKG_NAME = 'com.topjohnwu.magisk'
MAGISK_ALPHA_PKG_NAME = 'io.github.vvb2060.magisk'
MAGISK_DELTA_PKG_NAME = 'io.github.huskydg.magisk'
KERNEL_SU_PKG_NAME = 'me.weishu.kernelsu'
APATCH_PKG_NAME = 'me.bmax.apatch'
ZYGISK_NEXT_UPDATE_URL = 'https://api.nullptr.icu/android/zygisk-next/static/update.json'
