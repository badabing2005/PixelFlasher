# -*- mode: python -*-

block_cipher = None

a = Analysis(['PixelFlasher.py'],
             binaries=[('bin/7zz', 'bin')],
            datas=[
                ("images/icon-64.png", "images"),
                ("images/icon-dark-64.png", "images"),
                ('bin/busybox_arm64-v8a', 'bin'),
                ('bin/busybox_armeabi-v7a', 'bin'),
                ('bin/busybox_x86', 'bin'),
                ('bin/busybox_x86_64', 'bin'),
                ('bin/aapt2_arm64-v8a', 'bin'),
                ('bin/aapt2_armeabi-v7a', 'bin'),
                ('bin/aapt2_x86', 'bin'),
                ('bin/aapt2_x86_64', 'bin'),
                ('bin/avbctl', 'bin'),
                ('bin/update_engine_client_r28', 'bin'),
                ('bin/update_engine_client_r72', 'bin'),
                ('android_versions.json', '.'),
                ('android_devices.json', '.'),
                ('testkey_rsa4096.pem', '.')
            ],
             hiddenimports=['_cffi_backend'],
             hookspath=[],
             runtime_hooks=[],
            excludes=[
                'bin/busybox_arm64-v8a',
                'bin/busybox_armeabi-v7a',
                'bin/busybox_x86',
                'bin/busybox_x86_64',
                'bin/aapt2_arm64-v8a',
                'bin/aapt2_armeabi-v7a',
                'bin/aapt2_x86',
                'bin/aapt2_x86_64',
                'bin/avbctl',
                'bin/update_engine_client_r28',
                'bin/update_engine_client_r72'
            ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='PixelFlasher',
          target_arch='universal2',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='images/icon-dark-256.icns')
app = BUNDLE(exe,
             name='PixelFlasher.app',
             version='7.11.3.1',
             icon='./images/icon-dark-256.icns',
             bundle_identifier='com.badabing.pixelflasher')
