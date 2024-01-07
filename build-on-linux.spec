# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['PixelFlasher.py'],
             pathex=[],
             binaries=[('bin/7zzs', 'bin')],
             datas=[("images/icon-64.png", "images"), ('bin/busybox_arm64-v8a', 'bin'), ('bin/busybox_armeabi-v7a', 'bin'), ('bin/busybox_x86', 'bin'), ('bin/busybox_x86_64', 'bin'), ('bin/aapt2_arm64-v8a', 'bin'), ('bin/aapt2_armeabi-v7a', 'bin'), ('bin/aapt2_x86', 'bin'), ('bin/aapt2_x86_64', 'bin'), ('bin/avbctl', 'bin'), ('bin/update_engine_client', 'bin')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['bin/busybox_arm64-v8a', 'bin/busybox_armeabi-v7a', 'bin/busybox_x86', 'bin/busybox_x86_64', 'bin/aapt2_arm64-v8a', 'bin/aapt2_armeabi-v7a', 'bin/aapt2_x86', 'bin/aapt2_x86_64', 'bin/avbctl', 'bin/update_engine_client'],
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
