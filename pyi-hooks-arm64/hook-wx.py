#
# Copyright (C) 2026 Badabing2005
# SPDX-FileCopyrightText: 2026 Badabing2005
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

# -*- coding: utf-8 -*-
"""
PyInstaller hook for wxPython on Windows ARM64.

This hook forces collection of the entire wx package including ARM64 .pyd files
that PyInstaller cannot analyze when running on x64 hardware.
"""

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs
import wx
import os

# Get the wx package directory
wx_dir = os.path.dirname(wx.__file__)

# Collect all wx files - both as datas and binaries
# This ensures ARM64 .pyd files are included even though they can't be analyzed
binaries = collect_dynamic_libs('wx')
datas = collect_all('wx')

print(f"ARM64 Hook: Collected wx from {wx_dir}")
print(f"ARM64 Hook: Found {len(binaries)} binary files")
print(f"ARM64 Hook: Found {len(datas[0])} data files")
