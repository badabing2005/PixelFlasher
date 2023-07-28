#!/usr/bin/env bash
rm -rf build dist
VERSION=5.5.1.1
NAME="PixelFlasher"
DIST_NAME="PixelFlasher"

pushd "$(dirname "$0")"

# Check if venv exists and enter it. Create it first if not.
if [ -d "./venv/" ] 
then
    echo "Activating virtual environment"
    . venv/bin/activate 
else
    echo "Virtual environment not found. Creating venv and entering."
    python3 -m venv venv
    . venv/bin/activate 
fi

# Install/update requirements
pip3 install -r requirements.txt

if [[ $OSTYPE == 'darwin'* ]]; then
    echo "Building for MacOS"
    specfile=build-on-mac.spec
else
    echo "Building for Linux"
    specfile=build-on-linux.spec
fi

pyinstaller --log-level=DEBUG \
            --noconfirm \
            $specfile

if [[ $OSTYPE == 'darwin'* ]]; then
    # https://github.com/sindresorhus/create-dmg
    create-dmg "dist/$NAME.app"
    mv "$NAME $VERSION.dmg" "dist/$DIST_NAME.dmg"
fi

popd
