# PyInstaller hook for cryptography
# Excludes the Rust extension (_rust.abi3.so) which may be single-arch on macOS
# This allows the build to proceed even if the binary is not universal2

from PyInstaller.utils.hooks import get_module_file_attribute
import os

def get_binaries():
    """Exclude cryptography's Rust extension from collection."""
    # Return empty list to prevent collection of the problematic binary
    return []

def get_hidden_imports():
    """Include hidden imports from cryptography that won't use the Rust extension."""
    return [
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.backends',
    ]

# Prevent strict arch validation for this module
excludedimports = ['cryptography.hazmat.bindings._rust']
