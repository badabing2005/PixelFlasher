# -*- coding: utf-8 -*-
"""
PyInstaller hook for google namespace package.
This ensures all google.protobuf modules are properly included.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules from google.protobuf
hiddenimports = collect_submodules('google.protobuf')

# Also collect any data files
datas = collect_data_files('google.protobuf')

# Explicitly ensure the google namespace is included
hiddenimports += [
    'google',
    'google.protobuf',
    'google.protobuf.descriptor',
    'google.protobuf.message', 
    'google.protobuf.reflection',
    'google.protobuf.symbol_database',
    'google.protobuf.descriptor_pb2',
    'google.protobuf.internal',
    'google.protobuf.internal.api_implementation',
]
