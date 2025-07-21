#!/usr/bin/env bash

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

rm -rf build dist
VERSION=8.3.1.0
NAME="PixelFlasher"
DIST_NAME="PixelFlasher"

pushd "$(dirname "$0")"

if [[ $OSTYPE == 'darwin'* ]]; then
    if [[ $(arch) == 'arm64' ]]; then
        echo "Building macOS Universal Binary"
        specfile=build-on-mac.spec
    else
        echo "Building for macOS"
        specfile=build-on-mac-intel-only.spec
    fi
else
    echo "Building for Linux"
    specfile=build-on-linux.spec
fi

if ! command -v python3 &> /dev/null
then
    PYTHON=python
else
    PYTHON=python3
fi
$PYTHON ./compile_po.py

pyinstaller --log-level=DEBUG \
            --noconfirm \
            $specfile

if [[ $OSTYPE == 'darwin'* ]]; then
    # https://github.com/sindresorhus/create-dmg
    echo "List before creating DMG"
    ls -l ./ dist/
    chmod +x dist/$NAME.app/Contents/MacOS/$NAME
    create-dmg "dist/$NAME.app"
    echo "List after creating DMG"
    ls -l ./ dist/
    mv "$NAME $VERSION.dmg" "dist/$DIST_NAME.dmg"
fi

popd
ls -l build/ dist/

