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
import sys
import os

# Find wx without importing it (since ARM64 .pyd can't load on x64)
# Get site-packages path from sys.path
site_packages = None
for path in sys.path:
    if 'site-packages' in path:
        site_packages = path
        break

if not site_packages:
    # Fallback: construct from sys.executable
    site_packages = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages')

wx_dir = os.path.join(site_packages, 'wx')

# Collect all wx files - both as datas and binaries
# This ensures ARM64 .pyd files are included even though they can't be analyzed
binaries = []
datas = []

# Manually collect all files from wx directory if it exists
if os.path.exists(wx_dir):
    for root, dirs, files in os.walk(wx_dir):
        for file in files:
            full_path = os.path.join(root, file)
            # Calculate relative path for destination
            rel_path = os.path.relpath(root, site_packages)
            
            # .pyd files go to binaries, everything else to datas
            if file.endswith('.pyd') or file.endswith('.dll'):
                binaries.append((full_path, rel_path))
            else:
                datas.append((full_path, rel_path))
    
    print(f"ARM64 Hook: Collected wx from {wx_dir}")
    print(f"ARM64 Hook: Found {len(binaries)} binary files")
    print(f"ARM64 Hook: Found {len(datas)} data files")
else:
    print(f"ARM64 Hook: WARNING - wx directory not found at {wx_dir}")
    # Try fallback using collect functions
    binaries = collect_dynamic_libs('wx')
    datas = collect_all('wx')
    print(f"ARM64 Hook (fallback): Found {len(binaries)} binary files")
    print(f"ARM64 Hook (fallback): Found {len(datas)} data files")
