#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p build

#go get github.com/erofs/go-erofs@latest
go mod tidy

GOOS=windows GOARCH=amd64 go build -o build/erofs-extract-windows-amd64.exe
GOOS=linux GOARCH=amd64 go build -o build/erofs-extract-linux-amd64
GOOS=darwin GOARCH=amd64 go build -o build/erofs-extract-macos-amd64
GOOS=darwin GOARCH=arm64 go build -o build/erofs-extract-macos-arm64

# lipo -create \
    # build/erofs-extract-macos-amd64 \
    # build/erofs-extract-macos-arm64 \
    # -output build/erofs-extract-macos-universal

chmod +x \
    build/erofs-extract-linux-amd64 \
    build/erofs-extract-macos-amd64 \
    build/erofs-extract-macos-arm64 #\
    # build/erofs-extract-macos-universal

ls -l build
