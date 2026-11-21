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
# For example, if your program is a web application, its interface could
# display a "Source" link that leads users to an archive of the code. There are
# many ways you could offer source, and different solutions will be better for
# different programs; see section 13 for the specific requirements.
#
# You should also get your employer (if you work as a programmer) or school, if
# any, to sign a "copyright disclaimer" for the program, if necessary. For more
# information on this, and how to apply and follow the GNU AGPL, see
# <https://www.gnu.org/licenses/>.

import datetime
import threading
import traceback
import wx
import wx.html
import wx.lib.wxpTag
import webbrowser
from constants import *
from runtime import get_bundle_dir
from runtime import check_latest_version
from runtime import get_config_file_path
from packaging.version import parse

from i18n import _
import self_update
from self_update import SelfUpdateError

# ============================================================================
#                               Class AboutDlg
# ============================================================================
class AboutDlg(wx.Dialog):
    text = '''
<html>
<body bgcolor="#DCDCDC" style="font-family: Arial; background-color: #DCDCDC;">
<center>
    <img src="{0}/images/icon-dark-64.png" width="64" height="64" alt="PixelFlasher">

    <h1>PixelFlasher</h1>
    <p>By Badabing</p>
    <h3>Version {1}</h3>

    {2}

    <p>Fork the <a style="color: #004CE5;" href="https://github.com/badabing2005/PixelFlasher/fork">project on
    GitHub</a> and help improve it for all!</p>

    <p> Beware! </p>
    <p> If you are asked to donate or pay money for this program, check your source. </p>
    <p> This program is free, will always remain totally free, ad free, even donation free.</p>

    <p>
        <wxp module="wx" class="Button">
            <param name="label" value="Close">
            <param name="id" value="ID_OK">
        </wxp>
    </p>
</center>
</body>
</html>
'''

    # ------------------------------------------------------------------
    #                       Function __init__
    # ------------------------------------------------------------------
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "About PixelFlasher")
        html = HtmlWindow(self, wx.ID_ANY, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            html.SetStandardFonts()

        self._update_in_progress = False
        self._cancel_event = None
        self._user_cancelled = False
        self._progress = None
        self.l_version = None
        self.update_button = None
        self.skip_button = None

        # check version if we are running the latest
        l_version = check_latest_version()
        if not l_version:
            return
        self.l_version = l_version
        update_available = parse(VERSION) < parse(l_version)
        if update_available:
            update_text = f"<p><b>Update</b> <a style=\"color: #004CE5;\" href=\"https://github.com/badabing2005/PixelFlasher/releases/latest\">Version v{l_version}</a> is available.</p>"
        else:
            update_text = "<p> You're up to date! </p>"

        txt = self.text.format(get_bundle_dir(), VERSION, update_text, datetime.datetime.now().year)
        html.SetPage(txt)
        ir = html.GetInternalRepresentation()
        html.SetMinSize((ir.GetWidth() + 25, ir.GetHeight() + 25))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND | wx.ALL, 5)

        # In-place update support: show action buttons when a newer version is
        # available and the running (frozen) binary belongs to a swappable
        # platform.
        if update_available and self_update.can_self_update():
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            # '&&' renders a literal ampersand in the button label
            self.update_button = wx.Button(self, label=_("Download Update && Restart"), size=(-1, 32))
            self.update_button.Bind(wx.EVT_BUTTON, self._on_update_now)
            button_sizer.Add(self.update_button, 0, wx.ALL, 5)

            self.skip_button = wx.Button(self, label=_("Skip This Version"), size=(-1, 32))
            self.skip_button.Bind(wx.EVT_BUTTON, self._on_skip_version)
            button_sizer.Add(self.skip_button, 0, wx.ALL, 5)
            sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)

        self.SetSizerAndFit(sizer)
        self.CentreOnParent(wx.BOTH)

    # ------------------------------------------------------------------
    #                       Function _on_update_now
    # ------------------------------------------------------------------
    def _on_update_now(self, event):
        if self._update_in_progress:
            return
        message_text = _("A new PixelFlasher version was detected.\nDownload and apply the update now?\nThe application will restart automatically.")
        confirm_dlg = wx.MessageDialog(self, message_text, _("Update PixelFlasher"), wx.YES_NO | wx.ICON_QUESTION)
        res = confirm_dlg.ShowModal()
        confirm_dlg.Destroy()
        if res != wx.ID_YES:
            return

        self._update_in_progress = True
        self._cancel_event = threading.Event()
        self._user_cancelled = False
        self._worker_done = threading.Event()
        self._worker_result = None
        self._worker_status = (None, _("Contacting GitHub ..."))
        self._worker_lock = threading.Lock()
        if self.update_button:
            self.update_button.Disable()
            self.update_button.SetLabel(_("Downloading update ..."))
        if self.skip_button:
            self.skip_button.Disable()
        self._progress = wx.ProgressDialog(_("Updating PixelFlasher"), _("Contacting GitHub ..."), style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._poll_timer, self._timer)
        self._timer.Start(100)
        threading.Thread(target=self._update_worker, daemon=True).start()

    # ------------------------------------------------------------------
    #                       Function _poll_timer
    # ------------------------------------------------------------------
    def _poll_timer(self, event):
        progress = self._progress
        if progress is not None:
            with self._worker_lock:
                percent, message = self._worker_status
            if percent is not None:
                keep_going, _skip = progress.Update(percent, message or '')
            else:
                keep_going, _skip = progress.Pulse()
            if not keep_going and not self._user_cancelled:
                self._user_cancelled = True
                if self._cancel_event:
                    self._cancel_event.set()

        if not self._worker_done.is_set():
            return

        # worker finished
        self._timer.Stop()
        if self._progress is not None:
            self._progress.Destroy()
            self._progress = None

        result = self._worker_result
        if result is None or result[0] != 'ok':
            err = (result[1] if result else _("Encountered an unexpected error during the update."))
            if not self._user_cancelled:
                error_dlg = wx.MessageDialog(self, err, _("Update Error"), wx.OK | wx.ICON_ERROR)
                error_dlg.ShowModal()
                error_dlg.Destroy()
            self._update_in_progress = False
            if self.update_button:
                self.update_button.Enable()
                self.update_button.SetLabel(_("Download Update && Restart"))
            if self.skip_button:
                self.skip_button.Enable()
            return

        # success
        try:
            frame = self.GetParent()
            if frame is not None:
                frame._pf_restart_pending = True
                if hasattr(frame, 'config'):
                    frame.config.pos_x, frame.config.pos_y = frame.GetPosition()
                    frame.config.save(get_config_file_path())
        except Exception:
            pass
        print(f"\n✅ {datetime.datetime.now():%Y-%m-%d %H:%M:%S} self_update: update applied, restarting ...")
        try:
            self.EndModal(wx.ID_OK)
        except Exception:
            pass
        try:
            self.Destroy()
        except Exception:
            pass
        try:
            wx.GetApp().ExitMainLoop()
        except Exception:
            pass

    # ------------------------------------------------------------------
    #                       Function _on_skip_version
    # ------------------------------------------------------------------
    def _on_skip_version(self, event):
        try:
            from runtime import get_config
            config = get_config()
            if config is not None:
                config.update_skip_version = self.l_version or ''
                config.save(get_config_file_path())
        except Exception:
            print(f"\n❌ {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Failed to save the skipped version")
            traceback.print_exc()
        self.EndModal(wx.ID_CANCEL)

    # ------------------------------------------------------------------
    #                       Function _update_worker
    # ------------------------------------------------------------------
    def _update_worker(self):
        def report(percent, status):
            with self._worker_lock:
                self._worker_status = (percent, status)
        try:
            swap_target = self_update.get_swap_target()
            if not swap_target:
                raise SelfUpdateError(_("Self-update is not supported for this build."))
            asset_name, target_path = swap_target
            self_update.trace(f"worker: download_and_verify_update begin (asset={asset_name})")
            asset_path = self_update.download_and_verify_update(asset_name, progress_cb=report, cancel_event=self._cancel_event, latest_version=self.l_version)
            self_update.trace(f"worker: downloaded+verified -> {asset_path}")
            with self._worker_lock:
                self._worker_status = (None, _("Staging update ..."))
            staged_path = self_update.stage_update(asset_path, target_path)
            self_update.trace(f"worker: staged -> {staged_path}")
            with self._worker_lock:
                self._worker_status = (None, _("Preparing restart ..."))
            self_update.apply_update_and_restart(target_path, staged_path)
            self_update.trace("worker: agent handed off; exiting")
            self._worker_result = ('ok', '')
        except SelfUpdateError as e:
            self._worker_result = ('err', str(e))
        except Exception:
            print(f"\n❌ {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Encountered an unexpected error during the in-app update")
            traceback.print_exc()
            self._worker_result = ('err', _("Encountered an unexpected error during the update."))
        finally:
            self._worker_done.set()


# ============================================================================
#                               Class HtmlWindow
# ============================================================================
class HtmlWindow(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())

