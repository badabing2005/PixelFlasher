#!/usr/bin/env python3
"""
A Script To easily change the version number in all involved files.
"""
import fileinput
import os
import re

cwd = os.getcwd()
file1 = os.path.join(cwd, 'build-on-mac.spec')
file2 = os.path.join(cwd, 'build.sh')
file3 = os.path.join(cwd, 'config.py')
file4 = os.path.join(cwd, 'windows-metadata.yaml')
file5 = os.path.join(cwd, 'windows-version-info.txt')

s1 = r"\s+(version=)'(\d\.\d\.\d.\d)',"
s2 = r"(VERSION=)(\d\.\d\.\d.\d)"
s3 = r"(VERSION = )'(\d\.\d\.\d.\d)'"
s4 = r"(Version: )(\d\.\d\.\d.\d)"

s5_1 = r"(filevers=)\((\d\,\d\,\d,\d)\)"
s5_2 = r"(prodvers=)\((\d\,\d\,\d,\d)\)"
s5_3 = r"(FileVersion', )u'(\d\.\d\.\d.\d)'"
s5_4 = r"(ProductVersion', )u'(\d\.\d\.\d.\d)'"
s5 = (s5_1, s5_2, s5_3, s5_4)

alist = [(file1, s1), (file2, s2), (file3, s3), (file4, s4)]

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

