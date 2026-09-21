# EROFS extractor builder

Run:

```bash
cd erofs-builder
go mod tidy
chmod +x build_all.sh
./build_all.sh
```

If go mod tidy still fails because the module/version is not published or the tag is different, the fallback is:
```
go get github.com/erofs/go-erofs@latest
go mod tidy
./build_all.sh
```
