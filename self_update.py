#!/usr/bin/env python
# coding=utf-8

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2026 Badabing2005
# SPDX-FileCopyrightText: 2025 Badabing2005
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If your software can interact with users remotely through a computer network,
# you should also make sure that it provides a way for users to get its source.

import fnmatch
import hashlib
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime

from packaging.version import parse

from constants import VERSION
from i18n import _
from runtime import debug, get_config_path, get_gh_release_object, gh_asset_utility, request_with_fallback

REPO_OWNER = 'badabing2005'
REPO_NAME = 'PixelFlasher'

PFNEW_SUFFIX = '.pfnew'

STALE_FILE_PATTERNS = ('*' + PFNEW_SUFFIX, 'pf_update.cmd', 'pf_update.sh')


# ============================================================================
#                               Class SelfUpdateError
# ============================================================================
class SelfUpdateError(Exception):
    pass


# ============================================================================
#                         Function get_swap_target
# ============================================================================
def get_swap_target():
    """
    Determine whether the running (frozen) binary can be swapped in place,
    and which release asset corresponds to it.

    Returns:
        (asset_name, target_path) on success, None when self-update is not
        supported on this platform/architecture.
    """
    if sys.platform == 'win32':
        # Windows x64 only for now.
        machine = platform.machine().upper()
        if machine in ('ARM64', 'AARCH64', 'X86', 'I686', 'I386'):
            return None
        return ('PixelFlasher.exe', os.path.abspath(sys.executable))

    return None


# ============================================================================
#                         Function can_self_update
# ============================================================================
def can_self_update():
    return getattr(sys, 'frozen', False) and get_swap_target() is not None


# ============================================================================
#                         Function _pad_version
# ============================================================================
def _pad_version(version_string):
    version = re.sub(r'^[vV]', '', str(version_string).strip())
    parts = version.split('.')
    if len(parts) < 4:
        parts += ['0'] * (4 - len(parts))
    return '.'.join(parts[:4])


# ============================================================================
#                         Function download_and_verify_update
# ============================================================================
def download_and_verify_update(asset_name, progress_cb=None, cancel_event=None, latest_version=None):
    """
    Download `asset_name` (and its .sha256 sidecar) from the latest GitHub
    release into <config_path>/tmp and verify the checksum.

    progress_cb:    optional callable(percent(int|None), status(str)) used to
                    feed the UI (called from the worker thread).
    cancel_event:   optional threading.Event; when set, the download aborts
                    (partial files are removed and SelfUpdateError is raised).
    latest_version: optional padded version string (e.g. '10.4.0.0') already
                    resolved by the caller; when supplied, the asset URL is
                    constructed directly from github.com without using
                    api.github.com (more robust on restricted networks).

    Returns the full path of the verified downloaded file.
    Raises SelfUpdateError on any failure (including cancellation).
    """

    def report(percent, status):
        if progress_cb:
            try:
                progress_cb(percent, status)
            except Exception:
                pass

    print(f"\nℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} self_update: checking latest release ...")
    _check_cancel(cancel_event)
    if latest_version:
        # bypass api.github.com entirely; latest_version is already padded
        tag_version = _pad_version(latest_version)
        asset_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/v{tag_version}/{asset_name}"
    else:
        report(None, _("Contacting GitHub ..."))
        release = get_gh_release_object(REPO_OWNER, REPO_NAME)
        if not release:
            raise SelfUpdateError(_("Could not fetch release information from GitHub."))

        tag = release.get('tag_name', '')
        tag_version = _pad_version(tag)
        asset_url = gh_asset_utility(release, re.escape(asset_name) + r'$', False)
        if not asset_url:
            raise SelfUpdateError(_("The asset %s was not found in release v%s.") % (asset_name, tag_version))

    try:
        if parse(VERSION) >= parse(tag_version):
            raise SelfUpdateError(_("The latest release (v%s) does not contain an update for this build.") % tag_version)
    except SelfUpdateError:
        raise
    except Exception as e:
        raise SelfUpdateError(_("Could not compare current version against release version (%s).") % tag_version) from e

    _check_cancel(cancel_event)
    report(None, _("Downloading %s ...") % asset_name)
    asset_path = _download_update_file(asset_url, asset_name, report, cancel_event)
    _check_cancel(cancel_event)

    report(None, _("Downloading checksum ..."))
    sha_path = _download_update_file(asset_url + '.sha256', asset_name + '.sha256', None, cancel_event)

    report(None, _("Verifying checksum ..."))
    expected_hash = _extract_hex_hash(sha_path)
    if not expected_hash:
        raise SelfUpdateError(_("Could not parse the checksum file for %s.") % asset_name)

    actual_hash = _sha256_file(asset_path)
    if expected_hash.lower() != actual_hash:
        debug(f"self_update: checksum mismatch expected={expected_hash} actual={actual_hash}")
        _safe_remove(asset_path)
        _safe_remove(sha_path)
        raise SelfUpdateError(_("Checksum verification failed for the downloaded update."))

    print(f"\n✅ {datetime.now():%Y-%m-%d %H:%M:%S} self_update: checksum verified for {asset_name}")
    return asset_path


# ============================================================================
#                         Function _check_cancel
# ============================================================================
def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise SelfUpdateError(_("Update cancelled."))


# ============================================================================
#                         Function _safe_remove
# ============================================================================
def _safe_remove(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


# ============================================================================
#                         Function _download_update_file
# ============================================================================
def _download_update_file(url, filename, report=None, cancel_event=None):
    """
    Download url to <config_path>/tmp/<filename> with a connect/read timeout,
    so a stalled connection cannot hang forever. Streams into place while
    reporting percent progress. Returns the local path or raises
    SelfUpdateError (also removes the partial file on failure).
    """
    try:
        response = request_with_fallback(method='GET', url=url, stream=True, timeout=(15, 30))
    except Exception as e:
        debug(f"self_update: download request failed: {e}\n{traceback.format_exc()}")
        raise SelfUpdateError(_("Network error while downloading the update.")) from e
    if isinstance(response, str) or response is None:
        raise SelfUpdateError(_("Network error while downloading the update."))

    try:
        total = int(response.headers.get('Content-Length') or 0)
    except (ValueError, TypeError):
        total = 0

    config_path = get_config_path()
    tmp_dir = os.path.join(config_path, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    target_path = os.path.join(tmp_dir, filename)
    downloaded = 0
    last_report = 0.0
    try:
        with open(target_path, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=256 * 1024):
                _check_cancel(cancel_event)
                if not chunk:
                    continue
                fd.write(chunk)
                downloaded += len(chunk)
                if report and total:
                    now = time.time()
                    if now - last_report >= 0.25 or downloaded == total:
                        last_report = now
                        mb_done = downloaded // (1024 * 1024)
                        mb_total = total // (1024 * 1024)
                        percent = min(99, int(downloaded * 100 / total))
                        report(percent, _("Downloading %s ... %d%% (%d MB of %d MB)") % (filename, percent, mb_done, mb_total))
                elif report:
                    now = time.time()
                    if now - last_report >= 1.0:
                        last_report = now
                        report(None, _("Downloading %s ... %d MB") % (filename, downloaded // (1024 * 1024)))
    except SelfUpdateError:
        _safe_remove(target_path)
        raise
    except Exception as e:
        _safe_remove(target_path)
        debug(f"self_update: download failed: {e}\n{traceback.format_exc()}")
        raise SelfUpdateError(_("The update download failed or was interrupted.")) from e
    finally:
        try:
            response.close()
        except Exception:
            pass

    if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
        _safe_remove(target_path)
        raise SelfUpdateError(_("Failed to download %s.") % filename)
    if total and os.path.getsize(target_path) != total:
        _safe_remove(target_path)
        raise SelfUpdateError(_("The update download is incomplete."))
    return target_path


# ============================================================================
#                         Function _extract_hex_hash
# ============================================================================
def _extract_hex_hash(sha_file_path):
    # Handles both sha256sum output ("<hash>  <name>") and Windows certutil
    # output which wraps the hash in header/footer text.
    try:
        with open(sha_file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        match = re.search(r'\b[a-fA-F0-9]{64}\b', content)
        return match.group() if match else None
    except Exception:
        return None


# ============================================================================
#                         Function _sha256_file
# ============================================================================
def _sha256_file(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as fp:
        while True:
            chunk = fp.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


# ============================================================================
#                         Function stage_update
# ============================================================================
def stage_update(asset_path, target_path):
    """
    Copy the verified download next to the target path, ready for the swap.
    Returns the staged file path. Raises SelfUpdateError if the installation
    directory is not writable.
    """
    staged_path = target_path + PFNEW_SUFFIX
    try:
        shutil.copyfile(asset_path, staged_path)
        # sanity check the copy made it over
        if os.path.getsize(asset_path) != os.path.getsize(staged_path):
            raise SelfUpdateError(_("The staged update file is incomplete."))
    except SelfUpdateError:
        raise
    except Exception as e:
        debug(f"self_update: staging failed: {e}\n{traceback.format_exc()}")
        raise SelfUpdateError(_("Could not write the update file to the application folder (permission denied?).")) from e
    return staged_path


# ============================================================================
#                         Function _get_wait_pid
# ============================================================================
def _get_wait_pid():
    """
    In a PyInstaller onefile build on Windows, the running Python process is
    a child of the PyInstaller bootloader process (same executable path).
    Wait for the parent bootloader PID so the swap only runs after both the
    Python child and the bootloader (and its _MEI cleanup) have exited.
    """
    my_pid = os.getpid()
    if getattr(sys, 'frozen', False):
        try:
            import psutil
            ppid = os.getppid()
            parent = psutil.Process(ppid)
            if os.path.normcase(os.path.abspath(parent.exe())) == os.path.normcase(os.path.abspath(sys.executable)):
                return ppid
        except Exception:
            pass
    return my_pid


# ============================================================================
#                         Function _build_clean_env
# ============================================================================
def _build_clean_env():
    """
    Return a copy of os.environ stripped of PyInstaller's internal variables
    and _MEIPASS references so neither the update helper nor the relaunched
    PixelFlasher.exe inherits the old bootloader's _MEI directory.
    """
    env = os.environ.copy()
    meipass = getattr(sys, '_MEIPASS', None)
    meipass_norm = os.path.normcase(os.path.abspath(meipass)) if meipass else None

    for key in list(env.keys()):
        upper = key.upper()
        if upper.startswith('_PYI_') or upper.startswith('PYINSTALLER_') or upper in ('_MEIPASS', '_MEIPASS2'):
            env.pop(key, None)
            continue
        if meipass_norm and upper == 'PATH':
            parts = [
                p for p in env[key].split(os.pathsep)
                if p and not os.path.normcase(os.path.abspath(p)).startswith(meipass_norm)
            ]
            env[key] = os.pathsep.join(parts)
        elif meipass_norm and env[key]:
            try:
                val_norm = os.path.normcase(os.path.abspath(env[key]))
                if val_norm == meipass_norm or val_norm.startswith(meipass_norm + os.sep):
                    env.pop(key, None)
            except Exception:
                pass
    return env


# ============================================================================
#                         Function _get_versioned_backup_path
# ============================================================================
def _get_versioned_backup_path(target_path, version=VERSION):
    """
    Build the versioned archive path for the current executable, e.g.:
        PixelFlasher.exe -> PixelFlasher_10.4.0.0.exe
    """
    base, ext = os.path.splitext(target_path)
    ver = str(version).strip()
    if ver:
        candidate = f"{base}_{ver}{ext}"
        if os.path.normcase(os.path.abspath(candidate)) != os.path.normcase(os.path.abspath(target_path)):
            return candidate
    return f"{base}_old{ext}"


# ============================================================================
#                         Function _write_windows_update_script
# ============================================================================
def _write_windows_update_script(script_path, staged_path, target_path, old_pid, restart_args):
    pfold_path = _get_versioned_backup_path(target_path)
    target_dir = os.path.dirname(target_path)
    quoted_args = ' '.join(f'"{str(a).replace(chr(34), "")}"' for a in (restart_args or []))
    relaunch_cmd = f'start "" /D "{target_dir}" "{target_path}"'
    if quoted_args:
        relaunch_cmd += f' {quoted_args}'

    lines = [
        '@echo off',
        'setlocal EnableExtensions',
        'set "LOG=%TEMP%\\pf_update.log"',
        f'set "STAGED={staged_path}"',
        f'set "TARGET={target_path}"',
        f'set "PFOLD={pfold_path}"',
        f'set "OLDPID={int(old_pid)}"',
        '>>"%LOG%" echo [%DATE% %TIME%] pf_update.cmd started: staged=%STAGED% target=%TARGET% backup=%PFOLD% old_pid=%OLDPID%',
        '',
        'REM 1. Wait up to 60s for the old instance (and PyInstaller bootloader) to exit',
        'for /L %%i in (1,1,60) do (',
        '    "%SystemRoot%\\System32\\tasklist.exe" /FI "PID eq %OLDPID%" /NH 2>nul | "%SystemRoot%\\System32\\find.exe" "%OLDPID%" >nul',
        '    if errorlevel 1 goto :old_gone',
        '    "%SystemRoot%\\System32\\ping.exe" -n 2 127.0.0.1 >nul 2>&1',
        ')',
        ':old_gone',
        '>>"%LOG%" echo [%DATE% %TIME%] old instance gone, waiting 2s for handle release',
        '"%SystemRoot%\\System32\\ping.exe" -n 3 127.0.0.1 >nul 2>&1',
        '',
        'REM 2. Move old binary to versioned backup (replace if it already exists; retry up to 30s)',
        'for /L %%i in (1,1,30) do (',
        '    if not exist "%TARGET%" goto :moved_old',
        '    if exist "%PFOLD%" (',
        '        attrib -R -S -H "%PFOLD%" >nul 2>&1',
        '        del /F /Q "%PFOLD%" >nul 2>&1',
        '    )',
        '    move /Y "%TARGET%" "%PFOLD%" >nul 2>&1',
        '    if not exist "%TARGET%" goto :moved_old',
        '    "%SystemRoot%\\System32\\ping.exe" -n 2 127.0.0.1 >nul 2>&1',
        ')',
        'if exist "%TARGET%" (',
        '    >>"%LOG%" echo [%DATE% %TIME%] ERROR: could not move target to %PFOLD%, aborting',
        '    goto :cleanup_self',
        ')',
        ':moved_old',
        '',
        'REM 3. Move staged .pfnew to target (retry up to 30s; rollback on failure)',
        'for /L %%i in (1,1,30) do (',
        '    if exist "%TARGET%" goto :swapped',
        '    if exist "%STAGED%" move /Y "%STAGED%" "%TARGET%" >nul 2>&1',
        '    if exist "%TARGET%" goto :swapped',
        '    "%SystemRoot%\\System32\\ping.exe" -n 2 127.0.0.1 >nul 2>&1',
        ')',
        'if not exist "%TARGET%" (',
        '    >>"%LOG%" echo [%DATE% %TIME%] ERROR: could not move staged to target, rolling back',
        '    move /Y "%PFOLD%" "%TARGET%" >nul 2>&1',
        '    goto :cleanup_self',
        ')',
        ':swapped',
        '>>"%LOG%" echo [%DATE% %TIME%] swap complete (kept old version at %PFOLD%), relaunching target',
        '"%SystemRoot%\\System32\\ping.exe" -n 2 127.0.0.1 >nul 2>&1',
        relaunch_cmd,
        '',
        ':cleanup_self',
        '>>"%LOG%" echo [%DATE% %TIME%] pf_update.cmd finished',
        '(goto) 2>nul & del /F /Q "%~f0" >nul 2>&1',
    ]
    with open(script_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write('\n'.join(lines) + '\n')


# ============================================================================
#                         Function _write_posix_update_script
# ============================================================================
def _write_posix_update_script(script_path, staged_path, target_path, old_pid, restart_args):
    pfold_path = _get_versioned_backup_path(target_path)
    target_dir = os.path.dirname(target_path)
    quoted_args = ' '.join(shlex.quote(str(a)) for a in (restart_args or []))
    lines = [
        '#!/bin/sh',
        'LOG="${TMPDIR:-/tmp}/pf_update.log"',
        f'STAGED={shlex.quote(staged_path)}',
        f'TARGET={shlex.quote(target_path)}',
        f'PFOLD={shlex.quote(pfold_path)}',
        f'TARGET_DIR={shlex.quote(target_dir)}',
        f'OLDPID={int(old_pid)}',
        'echo "[$(date "+%Y-%m-%d %H:%M:%S")] pf_update.sh started: staged=$STAGED target=$TARGET backup=$PFOLD old_pid=$OLDPID" >>"$LOG"',
        '',
        '# 1. Wait up to 60s for the old instance to exit',
        'i=0',
        'while [ "$i" -lt 60 ]; do',
        '    if ! kill -0 "$OLDPID" 2>/dev/null; then',
        '        break',
        '    fi',
        '    sleep 1',
        '    i=$((i + 1))',
        'done',
        'sleep 1',
        '',
        '# 2. Move old binary to versioned backup (replace if it already exists) and put staged binary in place',
        'rm -f "$PFOLD" 2>/dev/null',
        'if ! mv -f "$TARGET" "$PFOLD" 2>>"$LOG"; then',
        '    echo "[$(date "+%Y-%m-%d %H:%M:%S")] ERROR: could not move target to $PFOLD" >>"$LOG"',
        '    rm -f "$0" 2>/dev/null',
        '    exit 1',
        'fi',
        'if ! mv -f "$STAGED" "$TARGET" 2>>"$LOG"; then',
        '    echo "[$(date "+%Y-%m-%d %H:%M:%S")] ERROR: could not move staged to target, rolling back" >>"$LOG"',
        '    mv -f "$PFOLD" "$TARGET" 2>>"$LOG"',
        '    rm -f "$0" 2>/dev/null',
        '    exit 1',
        'fi',
        'chmod 755 "$TARGET" 2>/dev/null',
        '',
        '# 3. Relaunch updated binary (keep versioned backup)',
        'echo "[$(date "+%Y-%m-%d %H:%M:%S")] swap complete (kept old version at $PFOLD), relaunching target" >>"$LOG"',
        f'(cd "$TARGET_DIR" && "$TARGET" {quoted_args} >/dev/null 2>&1 &)',
        'echo "[$(date "+%Y-%m-%d %H:%M:%S")] pf_update.sh finished" >>"$LOG"',
        'rm -f "$0" 2>/dev/null',
        'exit 0',
    ]
    with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    try:
        os.chmod(script_path, 0o755)
    except Exception:
        pass


# ============================================================================
#                  Function apply_update_and_restart
# ============================================================================
def apply_update_and_restart(target_path, staged_path):
    """
    Generate a platform update script (pf_update.cmd on Windows, pf_update.sh
    on POSIX) in <config_path>/tmp, launch it hidden/detached with a clean
    environment, and return. The script waits for this process (and the
    PyInstaller bootloader) to exit, archives the old binary as
    PixelFlasher_<VERSION>.exe, moves the new binary into place, relaunches
    the updated app, and deletes itself.

    Returns True when the helper script was successfully launched (the caller
    must then exit the application). Raises SelfUpdateError otherwise.
    """
    old_pid = _get_wait_pid()
    restart_args = list(sys.argv[1:])

    tmp_dir = os.path.join(get_config_path(), 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    clean_env = _build_clean_env()

    if sys.platform == 'win32':
        script_path = os.path.join(tmp_dir, 'pf_update.cmd')
        try:
            _write_windows_update_script(script_path, staged_path, target_path, old_pid, restart_args)
        except Exception as e:
            debug(f"self_update: failed to write update script: {e}\n{traceback.format_exc()}")
            raise SelfUpdateError(_("Could not write the update helper script to the temp directory.")) from e
        comspec = os.environ.get('COMSPEC') or r'C:\Windows\System32\cmd.exe'
        cmd = [comspec, '/d', '/c', script_path]
    else:
        script_path = os.path.join(tmp_dir, 'pf_update.sh')
        try:
            _write_posix_update_script(script_path, staged_path, target_path, old_pid, restart_args)
        except Exception as e:
            debug(f"self_update: failed to write update script: {e}\n{traceback.format_exc()}")
            raise SelfUpdateError(_("Could not write the update helper script to the temp directory.")) from e
        cmd = ['/bin/sh', script_path]

    trace(f"apply_update_and_restart: launching script {script_path} (pid={os.getpid()} wait_pid={old_pid})")
    try:
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            except Exception:
                pass
            subprocess.Popen(
                cmd,
                cwd=os.path.dirname(target_path),
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            subprocess.Popen(
                cmd,
                cwd=os.path.dirname(target_path),
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )
    except Exception as e:
        debug(f"self_update: failed to launch update script: {e}\n{traceback.format_exc()}")
        raise SelfUpdateError(_("Could not start the update helper process.")) from e
    trace("apply_update_and_restart: script launched")
    return True


# ============================================================================
#                         Function trace
# ============================================================================
def trace(message):
    # for diagnosing update issues; writes to temp dir log.
    try:
        log_path = os.path.join(tempfile.gettempdir(), 'PixelFlasher_self_update.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} trace: {message}\n")
    except Exception:
        pass


# ============================================================================
#                         Function cleanup_stale_updates
# ============================================================================
def cleanup_stale_updates():
    """
    Remove leftover swap artifacts (*.pfold, *.pfnew) from
    previous update attempts. Called at startup, frozen builds only.
    """
    if not getattr(sys, 'frozen', False):
        return
    scan_dir = os.path.dirname(os.path.abspath(sys.executable))
    try:
        names = os.listdir(scan_dir)
    except Exception:
        return
    for name in names:
        if any(fnmatch.fnmatch(name, pattern) for pattern in STALE_FILE_PATTERNS):
            path = os.path.join(scan_dir, name)
            try:
                os.remove(path)
                print(f"ℹ️ {datetime.now():%Y-%m-%d %H:%M:%S} self_update: removed stale file {path}")
            except Exception:
                pass
