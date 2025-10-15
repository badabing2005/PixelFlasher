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
VERSION = '8.8.2.3'
SDKVERSION = '33.0.3'
MAIN_WIDTH = 1400
MAIN_HEIGHT = 1040
MAGISK_WIDTH = 1400
MAGISK_HEIGHT = 1040
PIF_WIDTH = 1150
PIF_HEIGHT = 840
POS_X = 40
POS_Y = 40

KNOWN_BAD_MAGISKS = ['7dbfba76:25207', 'e5641d5b:25208', '2717feac:25209', '981ccabb:25210', '69529ac5:25211', 'e2545e57:26001', '26.0:26000', 'a8c4a33e:26103']
PIF_UPDATE_URL = 'https://raw.githubusercontent.com/chiteroman/PlayIntegrityFix/main/update.json'
OSM0SIS_PIF_UPDATE_URL = 'https://raw.githubusercontent.com/osm0sis/PlayIntegrityFork/main/update.json'
TRICKYSTORE_UPDATE_URL = 'https://raw.githubusercontent.com/5ec1cff/TrickyStore/main/update.json' # non-existent, just a placeholder
TARGETEDFIX_UPDATE_URL = 'https://raw.githubusercontent.com/VisionR1/TargetedFix/main/update.json'
PIF_JSON_PATH = '/data/adb/pif.json'
XIAOMI_URL = "https://sourceforge.net/projects/xiaomi-eu-multilang-miui-roms/rss?path=/xiaomi.eu/Xiaomi.eu-app"
FREEMANURL = "https://codeload.github.com/TheFreeman193/PIFS/zip/refs/heads/main"
SCRCPYURL = "https://github.com/Genymobile/scrcpy/releases/latest"
MAGISK_PKG_NAME = 'com.topjohnwu.magisk'
MAGISK_ALPHA_PKG_NAME = 'io.github.vvb2060.magisk'
MAGISK_DELTA_PKG_NAME = 'io.github.huskydg.magisk'
KERNEL_SU_PKG_NAME = 'me.weishu.kernelsu'
KSU_NEXT_PKG_NAME = 'com.rifsxd.ksunext'
SUKISU_PKG_NAME = 'com.sukisu.ultra'
WILD_KSU_PKG_NAME = 'com.twj.wksu'
APATCH_PKG_NAME = 'me.bmax.apatch'
APATCH_NEXT_PKG_NAME = 'me.garfieldhan.apatch.next'
ZYGISK_NEXT_UPDATE_URL = 'https://api.nullptr.icu/android/zygisk-next/static/update.json'
ANDROID_CANARY_VERSION = 'CANARY_r01'
TARGETEDFIX_CONFIG_PATH = '/data/adb/modules/targetedfix/config'

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
    'b701bdebaa0e163c4983ef449cf2273a',
    '584822661981e2594d89c04bc0783243',
    '3136911470354531551',
    'd3b58d3f52707d233376e4b38bedcbd6',
    '10023936558530442420',
    '51680223b7de7ec84b51dc9a51c52b38',
    '3439b76c89282dadba8d72bf6e1091b9'
]

# Language names for the language selection menu
LANGUAGE_NAMES = {
    'en': 'English',
    'ar': 'العربية (Arabic)',
    'cs': 'Čeština (Czech)',
    'da': 'Dansk (Danish)',
    'de': 'Deutsch (German)',
    'el': 'Ελληνικά (Greek)',
    'es': 'Español (Spanish)',
    'fr': 'Français (French)',
    'he': 'עברית (Hebrew)',
    'hu': 'Magyar (Hungarian)',
    'it': 'Italiano (Italian)',
    'ja': '日本語 (Japanese)',
    'ko': '한국어 (Korean)',
    'nl': 'Nederlands (Dutch)',
    'pl': 'Polski (Polish)',
    'pt': 'Português (Portuguese)',
    'ro': 'Română (Romanian)',
    'ru': 'Русский (Russian)',
    'sv': 'Svenska (Swedish)',
    'uk': 'Українська (Ukrainian)',
    'vi': 'Tiếng Việt (Vietnamese)',
    'zh_CN': '简体中文 (Simplified Chinese)',
    'zh_TW': '繁體中文 (Traditional Chinese)'
}
