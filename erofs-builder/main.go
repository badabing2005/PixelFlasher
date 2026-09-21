// Small wrapper around github.com/erofs/go-erofs used to build
// platform-specific `erofs-extract` binaries included by PixelFlasher.
//
// This file is a thin wrapper and the underlying EROFS parsing
// functionality is provided by the upstream project `go-erofs`.
package main

import (
    "io"
    "io/fs"
    "log"
    "os"
    "path/filepath"

    "github.com/erofs/go-erofs"
)

func main() {
    if len(os.Args) < 3 {
        log.Fatalf("usage: %s <l|x> <image> [file]", os.Args[0])
    }

    command := os.Args[1]
    imagePath := os.Args[2]

    f, err := os.Open(imagePath)
    if err != nil {
        log.Fatalf("Failed to open image: %v", err)
    }
    defer f.Close()

    img, err := erofs.Open(f)
    if err != nil {
        log.Fatalf("Failed to parse EROFS: %v", err)
    }

    switch command {
    case "l":
        err = fs.WalkDir(img, ".", func(path string, d os.DirEntry, err error) error {
            if err != nil {
                return err
            }
            if !d.IsDir() {
                log.Println(path)
            }
            return nil
        })
        if err != nil {
            log.Fatalf("Failed to list contents: %v", err)
        }

    case "x":
        if len(os.Args) < 4 {
            log.Fatalf("usage: %s x <image> <file>", os.Args[0])
        }
        filePath := os.Args[3]
        localName := filepath.Base(filePath)

        src, err := img.Open(filePath)
        if err != nil {
            log.Fatalf("Failed to open file: %v", err)
        }
        defer src.Close()

        dst, err := os.OpenFile(localName, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
        if err != nil {
            log.Fatalf("Failed to create file: %v", err)
        }
        defer dst.Close()

        if _, err = io.Copy(dst, src); err != nil {
            log.Fatalf("Failed to copy file: %v", err)
        }

    default:
        log.Fatalf("unknown command %q", command)
    }
}
