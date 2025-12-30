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

"""Audit translation catalogs against the English reference."""

import argparse
from collections import Counter
from pathlib import Path
import sys

import polib


# -----------------------------------------------
#           entry_key function
# -----------------------------------------------
def entry_key(entry):
    return (entry.msgctxt or None, entry.msgid, entry.msgid_plural or None)


# -----------------------------------------------
#           format_key function
# -----------------------------------------------
def format_key(key):
    context, msgid, plural = key
    parts = [msgid]
    if plural:
        parts.append(f"[plural: {plural}]")
    if context:
        parts.append(f"(context: {context})")
    return " ".join(parts)


# -----------------------------------------------
#           load_entries function
# -----------------------------------------------
def load_entries(po_path):
    try:
        catalog = polib.pofile(str(po_path))
    except (OSError, IOError) as exc:
        sys.exit(f"Failed reading {po_path}: {exc}")
    return [entry for entry in catalog if not entry.obsolete]


# -----------------------------------------------
#           analyze_catalogs function
# -----------------------------------------------
def analyze_catalogs(locale_dir, reference_path):
    reference_entries = load_entries(reference_path)
    reference_keys = {entry_key(entry) for entry in reference_entries}

    reports = []
    for po_path in sorted(locale_dir.rglob("pixelflasher.po")):
        if po_path.resolve() == reference_path.resolve():
            continue
        target_entries = load_entries(po_path)
        target_keys = [entry_key(entry) for entry in target_entries]

        missing = sorted(reference_keys.difference(target_keys))
        extra = sorted(set(target_keys).difference(reference_keys))
        duplicates = sorted({key for key, count in Counter(target_keys).items() if count > 1})

        if missing or duplicates or extra:
            reports.append((po_path, missing, duplicates, extra))

    return reports


# -----------------------------------------------
#           print_reports function
# -----------------------------------------------
def print_reports(reports):
    if not reports:
        print("All translation catalogs match the English reference.")
        return

    for po_path, missing, duplicates, extra in reports:
        print(f"== {po_path} ==")
        if missing:
            print("  Missing entries:")
            for key in missing:
                print(f"    - {format_key(key)}")
        if duplicates:
            print("  Duplicate entries:")
            for key in duplicates:
                print(f"    - {format_key(key)}")
        if extra:
            print("  Extra entries (not in English):")
            for key in extra:
                print(f"    - {format_key(key)}")
        print()


# -----------------------------------------------
#           parse_args function
# -----------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compare translation catalogs against English.")
    parser.add_argument(
        "--locale-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "locale",
        help="Root locale directory containing language subfolders.",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path(__file__).resolve().parent / "locale" / "en" / "LC_MESSAGES" / "pixelflasher.po",
        help="Path to the English reference pixelflasher.po file.",
    )
    return parser.parse_args(argv)


# ============================================================================
#                               Function Main
# ============================================================================
def main(argv=None):
    args = parse_args(argv)
    locale_dir = args.locale_dir
    reference_path = args.reference

    if not reference_path.is_file():
        sys.exit(f"Reference catalog not found: {reference_path}")
    if not locale_dir.is_dir():
        sys.exit(f"Locale directory not found: {locale_dir}")

    reports = analyze_catalogs(locale_dir, reference_path)
    print_reports(reports)


if __name__ == "__main__":
    main()
