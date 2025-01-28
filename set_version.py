#!/usr/bin/env python3

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

"""
A Script To easily change the version number in all involved files.
"""
import fileinput
import os
import re

cwd = os.getcwd()
file1 = os.path.join(cwd, 'build-on-mac.spec')
file2 = os.path.join(cwd, 'build.sh')
file3 = os.path.join(cwd, 'constants.py')
file4 = os.path.join(cwd, 'windows-metadata.yaml')
file5 = os.path.join(cwd, 'windows-version-info.txt')
file6 = os.path.join(cwd, 'build-on-mac-intel-only.spec')

s1 = r"\s+(version=)'(\d+\.\d+\.\d+.\d+)',"
s2 = r"(VERSION=)(\d+\.\d+\.\d+.\d+)"
s3 = r"(VERSION = )'(\d+\.\d+\.\d+.\d+)'"
s4 = r"(Version: )(\d+\.\d+\.\d+.\d+)"

s5_1 = r"(filevers=)\((\d+\,\d+\,\d+,\d+)\)"
s5_2 = r"(prodvers=)\((\d+\,\d+\,\d+,\d+)\)"
s5_3 = r"(FileVersion', )u'(\d+\.\d+\.\d+.\d+)'"
s5_4 = r"(ProductVersion', )u'(\d+\.\d+\.\d+.\d+)'"
s5 = (s5_1, s5_2, s5_3, s5_4)

alist = [(file1, s1), (file2, s2), (file3, s3), (file4, s4), (file6, s1)]

# ============================================================================
#                               Function get_values
# ============================================================================
def get_values(thelist, update):
    # for index, tuple in enumerate(thelist):
    for tuple in thelist:
        file = tuple[0]
        s = tuple[1]
        with open(file, "rt", encoding='ISO-8859-1', errors="replace") as fin:
            data = fin.read()
        r = re.findall(s, data)
        print(file)
        if r:
            print(f"\t{r[0][0]}{r[0][1]}")
            if update:
                set_values(file, r[0][1], target_version)
        else:
            print("\tNO MATCH IS FOUND.")


    print(file5)
    with open(file5, "rt", encoding='ISO-8859-1', errors="replace") as fin:
        data = fin.read()
    for item in s5:
        r = re.findall(item, data)
        if r:
            print(f"\t{r[0][0]}{r[0][1]}")
    if r and update:
        set_values(file5, r[0][1], target_version)
        source_comma_version = r[0][1].replace('.', ',')
        set_values(file5, source_comma_version, target_comma_version)


# ============================================================================
#                               Function set_values
# ============================================================================
def set_values(file, search, replace):
    with open (file, 'r' ) as f:
        content = f.read()
        # content_new = re.sub(search, replace, content, flags = re.M)
        content_new = content.replace(search, replace)
    print(f"\t\tReplacing {search} with {replace} ...")
    with open(file, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
        f.write(content_new)


# ============================================================================
#                               MAIN
# ============================================================================
target_version = ''
print("Getting current values ...")
get_values(alist, False)
target_version = input("\nEnter the new Version: ")
target_comma_version = target_version.replace('.', ',')
print(f"\nSetting Versions to: {target_version} ...")
get_values(alist, True)
print("Getting updated values ...")
get_values(alist, False)

