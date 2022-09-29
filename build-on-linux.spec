# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['PixelFlasher.py'],
             pathex=[],
             binaries=[('bin/7zzs', 'bin')],
             datas=[("images", "images")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='PixelFlasher',
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon='images\\icon-256.ico',
        bootloader_ignore_signals=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None)
