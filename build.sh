#!/usr/bin/env bash
#rm -rf build dist
VERSION=2.1.0
NAME="PixelFlasher"
DIST_NAME="PixelFlasher"

pyinstaller --log-level=DEBUG \
            --noconfirm \
            --windowed \
            build-on-linux.spec
