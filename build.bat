python .\compile_po.py
pyinstaller --log-level=DEBUG ^
			--clean ^
            --noconfirm ^
            build-on-win.spec
