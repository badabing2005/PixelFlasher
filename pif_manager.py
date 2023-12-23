#!/usr/bin/env python

import wx
import wx.stc as stc
import traceback
import images as images
import json
import json5
import re
from datetime import datetime
from runtime import *

# ============================================================================
#                               Class MagiskModules
# ============================================================================
class PifManager(wx.Dialog):
    def __init__(self, *args, parent=None, config=None, **kwargs):
        self.config = config
        wx.Dialog.__init__(self, parent, *args, **kwargs, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.config = config
        self.SetTitle("Pif Manager")
        self.pif_json_path = PIF_JSON_PATH
        self.device_pif = ''

        self.pi_app = 'gr.nikolasspyr.integritycheck'
        self.coords = Coords()
        self.enable_buttons = False
        self.pif_exists = False
        self.advanced_props_support = False

        # Active pif label
        self.active_pif_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"Active Pif")
        self.active_pif_label.SetToolTip(u"Loaded Pif (from Device)")
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.active_pif_label.SetFont(font)
        # Modified status
        self.pif_modified_image = wx.StaticBitmap(parent=self)
        self.pif_modified_image.SetBitmap(images.alert_gray_24.GetBitmap())
        self.pif_modified_image.SetToolTip(u"Active pif is not modified.")
        #
        self.pif_version_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"")
        self.pif_version_label.SetToolTip(u"Pif Module")

        # Active Pif
        self.active_pif_stc = stc.StyledTextCtrl(self)
        self.active_pif_stc.SetLexer(stc.STC_LEX_JSON)
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_DEFAULT, "fore:#000000")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_NUMBER, "fore:#007F7F")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_STRING, "fore:#7F007F")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_PROPERTYNAME, "fore:#007F00")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_ESCAPESEQUENCE, "fore:#7F7F00")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_KEYWORD, "fore:#00007F,bold")
        self.active_pif_stc.StyleSetSpec(stc.STC_JSON_OPERATOR, "fore:#7F0000")
        self.active_pif_stc.SetCaretForeground(wx.BLACK)
        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.active_pif_stc.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.active_pif_stc.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.active_pif_stc.SetUseHorizontalScrollBar(True)
        self.active_pif_stc.SetTabWidth(4)
        self.active_pif_stc.SetIndent(4)

        # Console label
        self.console_label = wx.StaticText(parent=self, id=wx.ID_ANY, label=u"Output")
        self.console_label.SetToolTip(u"Console Output:\nIt could be the json output of processed prop\or it could be the Play Integrity Check result.\n\nThis is not what currently is on the device.")
        font = wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.console_label.SetFont(font)
        # Paste Up
        self.paste_selection = wx.BitmapButton(parent=self, id=wx.ID_ANY, bitmap=wx.NullBitmap, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BU_AUTODRAW)
        self.paste_selection.SetBitmap(images.paste_up_24.GetBitmap())
        self.paste_selection.SetToolTip(u"Paste the console content to Active pif.")
        self.paste_selection.Enable(False)

        # Console
        self.console_stc = stc.StyledTextCtrl(self)
        self.console_stc.SetLexer(stc.STC_LEX_JSON)
        self.console_stc.StyleSetSpec(stc.STC_JSON_DEFAULT, "fore:#000000")
        self.console_stc.StyleSetSpec(stc.STC_JSON_NUMBER, "fore:#007F7F")
        self.console_stc.StyleSetSpec(stc.STC_JSON_STRING, "fore:#7F007F")
        self.console_stc.StyleSetSpec(stc.STC_JSON_PROPERTYNAME, "fore:#007F00")
        self.console_stc.StyleSetSpec(stc.STC_JSON_ESCAPESEQUENCE, "fore:#7F7F00")
        self.console_stc.StyleSetSpec(stc.STC_JSON_KEYWORD, "fore:#00007F,bold")
        self.console_stc.StyleSetSpec(stc.STC_JSON_OPERATOR, "fore:#7F0000")
        self.console_stc.SetCaretForeground(wx.BLACK)
        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.console_stc.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)
        self.console_stc.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.console_stc.SetUseHorizontalScrollBar(True)
        self.console_stc.SetTabWidth(4)
        self.console_stc.SetIndent(4)

        # Ok button
        self.close_button = wx.Button(self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0)

        # Create pif.json button
        self.create_pif_button = wx.Button(self, wx.ID_ANY, u"Create pif.json", wx.DefaultPosition, wx.DefaultSize, 0)
        self.create_pif_button.SetToolTip(u"Create pif.json")
        self.create_pif_button.Enable(False)

        # Reload pif.json button
        self.reload_pif_button = wx.Button(self, wx.ID_ANY, u"Reload pif.json", wx.DefaultPosition, wx.DefaultSize, 0)
        self.reload_pif_button.SetToolTip(u"Reload pif.json from device.")
        self.reload_pif_button.Enable(False)

        # Process build.prop button
        self.process_build_prop_button = wx.Button(self, wx.ID_ANY, u"Process build.prop(s)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.process_build_prop_button.SetToolTip(u"Process build.prop to extract pif.json.")

        # Check for Auto Push pif.json
        self.auto_push_pif_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=u"Auto Update pif.json", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.auto_push_pif_checkbox.SetToolTip(u"After Processing build.props, the pif.json is automatically pushed to the device and the GMS process is killed.")
        self.auto_push_pif_checkbox.Enable(False)

        # Check for Auto Check Play Integrity
        self.auto_check_pi_checkbox = wx.CheckBox(parent=self, id=wx.ID_ANY, label=u"Auto Check Play Integrity", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
        self.auto_check_pi_checkbox.SetToolTip(u"After saving (pushing) pif.json, automatically run Play Integrity Check.")
        self.auto_check_pi_checkbox.Enable(False)

        # option button PI Selectedion
        self.pi_option = wx.RadioBox(self, choices=["Play Integrity API Checker", "Simple Play Integrity Checker", "TB Checker", "Play Store"], style=wx.RA_VERTICAL)

        # Play Integrity API Checker button
        self.pi_checker_button = wx.Button(self, wx.ID_ANY, u"Play Integrity Check", wx.DefaultPosition, wx.DefaultSize, 0)
        self.pi_checker_button.SetToolTip(u"Play Integrity API Checker\nNote: Need to install app from Play store.")

        # Get Xiaomi Pif button
        self.xiaomi_pif_button = wx.Button(self, wx.ID_ANY, u"Get Xiaomi Pif", wx.DefaultPosition, wx.DefaultSize, 0)
        self.xiaomi_pif_button.SetToolTip(u"Get Xiaomi.eu pif\nEasy to start but is not recommended as it gets banned quickly.\nRecommended to find your own.")

        # Make the buttons the same size
        button_width = self.pi_option.GetSize()[0] + 10
        self.create_pif_button.SetMinSize((button_width, -1))
        self.reload_pif_button.SetMinSize((button_width, -1))
        self.process_build_prop_button.SetMinSize((button_width, -1))
        self.auto_push_pif_checkbox.SetMinSize((button_width, -1))
        self.auto_check_pi_checkbox.SetMinSize((button_width, -1))
        self.pi_checker_button.SetMinSize((button_width, -1))
        self.xiaomi_pif_button.SetMinSize((button_width, -1))

        h_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 10)
        h_buttons_sizer.Add(self.close_button, 0, wx.ALL, 20)
        h_buttons_sizer.Add((0, 0), 1, wx.EXPAND, 10)

        v_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        v_buttons_sizer.Add(self.create_pif_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.reload_pif_button, 0, wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        v_buttons_sizer.AddStretchSpacer()
        v_buttons_sizer.Add(self.process_build_prop_button, 0, wx.TOP | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.auto_push_pif_checkbox, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.auto_check_pi_checkbox, 0, wx.ALL, 10)
        v_buttons_sizer.Add(self.pi_option, 0, wx.TOP, 10)
        v_buttons_sizer.Add(self.pi_checker_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 10)
        v_buttons_sizer.Add(self.xiaomi_pif_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 10)

        console_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        console_label_sizer.AddSpacer(10)
        console_label_sizer.Add(self.console_label, 0, wx.ALIGN_CENTER_VERTICAL)
        console_label_sizer.AddStretchSpacer()
        console_label_sizer.Add(self.paste_selection, 0, wx.ALIGN_CENTER_VERTICAL)

        stc_sizer = wx.BoxSizer(wx.VERTICAL)
        stc_sizer.Add(self.active_pif_stc, 1, wx.EXPAND | wx.ALL, 10)
        stc_sizer.Add(console_label_sizer, 0, wx.TOP, 10)
        stc_sizer.Add(self.console_stc, 1, wx.EXPAND | wx.ALL, 10)

        outside_stc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outside_stc_sizer.Add(stc_sizer, 1, wx.EXPAND | wx.ALL, 0)
        outside_stc_sizer.Add(v_buttons_sizer, 0, wx.EXPAND | wx.ALL, 0)

        active_pif_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.active_pif_label, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(10)
        active_pif_label_sizer.Add(self.pif_modified_image, 0, wx.ALIGN_CENTER_VERTICAL)
        active_pif_label_sizer.AddSpacer(100)
        active_pif_label_sizer.Add(self.pif_version_label, 0, wx.ALIGN_CENTER_VERTICAL)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(active_pif_label_sizer, 0, wx.TOP, 10)
        vSizer.Add(outside_stc_sizer, 1, wx.EXPAND, 0)
        vSizer.Add(h_buttons_sizer, 0, wx.EXPAND, 10)

        self.SetSizer(vSizer)
        self.SetMinSize((400, 300))
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.close_button.Bind(wx.EVT_BUTTON, self.onClose)
        self.create_pif_button.Bind(wx.EVT_BUTTON, self.onCreatePifProp)
        self.reload_pif_button.Bind(wx.EVT_BUTTON, self.load_reload_pif)
        self.process_build_prop_button.Bind(wx.EVT_BUTTON, self.onProcessBuildProp)
        self.pi_checker_button.Bind(wx.EVT_BUTTON, self.onPiChecker)
        self.xiaomi_pif_button.Bind(wx.EVT_BUTTON, self.onXiaomiPif)
        self.pi_option.Bind(wx.EVT_RADIOBOX, self.onPiSelection)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_SHOW, self.onShow)
        self.paste_selection.Bind(wx.EVT_BUTTON, self.onPasteSelection)
        self.active_pif_stc.Bind(wx.stc.EVT_STC_CHANGE, self.onActivePifStcChange)
        self.console_stc.Bind(wx.stc.EVT_STC_CHANGE, self.onConsoleStcChange)

        # init button states
        self.init()

        # Autosize the dialog
        self.active_pif_stc.PostSizeEventToParent()
        self.SetSizerAndFit(vSizer)

        print("\nOpening Pif Manager ...")

    # -----------------------------------------------
    #              Function onShow
    # -----------------------------------------------
    def onShow(self, event):
        if self.IsShown():
            if self.config:
                size = (self.config.pif_width, self.config.pif_height)
            else:
                size=(PIF_WIDTH, PIF_HEIGHT)
            self.SetSize(size)
        event.Skip()

    # -----------------------------------------------
    #              Function init
    # -----------------------------------------------
    def init(self, refresh=False):
        device = get_phone()
        if not device.rooted:
            return
        modules = device.get_magisk_detailed_modules(refresh)

        self.create_pif_button.Enable(True)
        self.reload_pif_button.Enable(False)
        self.auto_push_pif_checkbox.Enable(False)
        self.auto_check_pi_checkbox.Enable(False)
        self.pi_checker_button.Enable(False)
        self.enable_buttons = False
        self.pif_version_label.SetLabel('')

        if modules:
            for module in modules:
                if module.id == "playintegrityfix" and "Play Integrity" in module.name:
                    if module.name == "Play Integrity Fork":
                        self.pif_json_path = '/data/adb/modules/playintegrityfix/custom.pif.json'
                        if int(module.versionCode) > 4000:
                            print("Advanced props support enabled.")
                            self.advanced_props_support = True
                    elif module.name != "Play Integrity NEXT":
                        self.pif_json_path = '/data/adb/pif.json'
                    if module.version in ["PROPS-v2.1", "PROPS-v2.0"]:
                        self.pif_json_path = '/data/adb/modules/playintegrityfix/pif.json'
                    self.create_pif_button.Enable(False)
                    self.reload_pif_button.Enable(True)
                    self.auto_push_pif_checkbox.Enable(True)
                    self.auto_check_pi_checkbox.Enable(True)
                    self.pi_checker_button.Enable(True)
                    self.enable_buttons = True
                    self.pif_version_label.SetLabel(f"{module.name} \tVersion: {module.version}")
                    self.check_pif_json()
                    if self.pif_exists:
                        self.load_reload_pif(None)

    # -----------------------------------------------
    #                  check_pif_json
    # -----------------------------------------------
    def check_pif_json(self):
        device = get_phone()
        if not device.rooted:
            return
        # check for presence of pif.json
        res, tmp = device.check_file(self.pif_json_path, True)
        if res == 1:
            self.pif_exists = True
            self.reload_pif_button.Enable(True)
            self.create_pif_button.SetLabel("Update pif.json")
            self.create_pif_button.SetToolTip(u"Update pif.json.")
        else:
            self.pif_exists = False
            self.reload_pif_button.Enable(False)
            self.create_pif_button.SetLabel("Create pif.json")
            self.create_pif_button.SetToolTip(u"Create pif.json.")
        self.onActivePifStcChange(None)

    # -----------------------------------------------
    #                  onPiSelection
    # -----------------------------------------------
    def onPiSelection(self, event):
        option = event.GetString()

        if option == "Play Integrity API Checker":
            print("Play Integrity API Checker option selected")
            self.pi_app = 'gr.nikolasspyr.integritycheck'

        elif option == "Simple Play Integrity Checker":
            print("Simple Play Integrity Checker option selected")
            self.pi_app = 'com.henrikherzig.playintegritychecker'

        elif option == "TB Checker":
            print("TB Checker option selected")
            self.pi_app = 'krypton.tbsafetychecker'

        elif option == "Play Store":
            print("Play Store option selected")
            self.pi_app = 'com.android.vending'

    # -----------------------------------------------
    #                  __del__
    # -----------------------------------------------
    def __del__(self):
        pass

    # -----------------------------------------------
    #                  onClose
    # -----------------------------------------------
    def onClose(self, e):
        dialog_size = self.GetSize()
        dialog_x, dialog_y = dialog_size.GetWidth(), dialog_size.GetHeight()
        self.Parent.config.pif_width = dialog_x
        self.Parent.config.pif_height = dialog_y
        self.Close()

    # -----------------------------------------------
    #                  load_reload_pif
    # -----------------------------------------------
    def load_reload_pif(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            self._on_spin('start')
            config_path = get_config_path()
            pif_prop = os.path.join(config_path, 'tmp', 'pif.json')
            if self.reload_pif_button.Enabled:
                # pull the file
                res = device.pull_file(self.pif_json_path, pif_prop, True)
                if res != 0:
                    print("Aborting ...\n")
                    # puml("#red:Failed to pull pif.prop from the phone;\n}\n")
                    self._on_spin('stop')
                    return
            else:
                # we need to create one.
                with open(pif_prop, 'w') as file:
                    pass
            # get the contents of modified pif.json
            with open(pif_prop, 'r', encoding='ISO-8859-1', errors="replace") as f:
                contents = f.read()
                self.device_pif = contents
            self.active_pif_stc.SetValue(contents)

        except Exception as e:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Exception during pip Load process.")
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onCreatePifProp
    # -----------------------------------------------
    def onCreatePifProp(self, e):
        self.create_update_pif()

    # -----------------------------------------------
    #                  onUpdatePifProp
    # -----------------------------------------------
    def onUpdatePifProp(self, e):
        self.create_update_pif()

    # -----------------------------------------------
    #                  create_update_pif
    # -----------------------------------------------
    def create_update_pif(self):
        device = get_phone()
        if not device.rooted:
            return

        self._on_spin('start')
        config_path = get_config_path()
        pif_prop = os.path.join(config_path, 'tmp', 'pif.json')

        json_data = self.active_pif_stc.GetValue()
        if json_data:
            try:
                data = json.loads(json_data)
            except Exception:
                try:
                    data = json5.loads(json_data)
                except Exception:
                    print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Not a valid json.")
                    return
        else:
            print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} ERROR: Not a valid json.")
            return

        # Save the data as normal JSON
        with open(pif_prop, 'w', encoding="ISO-8859-1", errors="replace", newline='\n') as f:
            json.dump(data, f, indent=4)

        # push the file
        res = device.push_file(pif_prop, self.pif_json_path, True)
        if res != 0:
            print("Aborting ...\n")
            # puml("#red:Failed to push pif.json from the phone;\n}\n")
            self._on_spin('stop')
            return -1

        self.device_pif = data

        print("Killing Google GMS  ...")
        res = device.perform_package_action(pkg='com.google.android.gms.unstable', action='killall')
        if res.returncode != 0:
            print("Error killing GMS.")
        else:
            print("Killing Google GMS succeeded.")

        # Auto test Play Integrity
        if self.auto_check_pi_checkbox.IsEnabled() and self.auto_check_pi_checkbox.IsChecked():
            print("Auto Testing Play Integrity ...")
            self.onPiChecker(None)
        self.check_pif_json()
        self.load_reload_pif(None)
        self._on_spin('stop')

    # -----------------------------------------------
    #                  get_pi_app_coords
    # -----------------------------------------------
    def get_pi_app_coords(self, child=None):
        try:
            device = get_phone()
            if not device.rooted:
                return
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} Getting coordinates for {self.pi_app}")

            # pull view
            config_path = get_config_path()
            pi_app_xml = os.path.join(config_path, 'tmp', 'pi_app.xml')

            if self.pi_app == 'gr.nikolasspyr.integritycheck':
                return  device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "CHECK", False)

            elif self.pi_app == 'com.henrikherzig.playintegritychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Make Play Integrity Request", False)

            elif self.pi_app == 'krypton.tbsafetychecker':
                return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Run Play Integrity Check", False)

            elif self.pi_app == 'com.android.vending':
                if child == 'user':
                    # This needs custom handling, as there is no identifiable string to look for
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "PixelFlasher_Playstore", True)
                if child == 'settings':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Settings", True)
                if child == 'general':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "General", True)
                if child == 'scroll':
                    return device.swipe_up()
                if child == 'developer_options':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Developer options", True)
                if child == 'test':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Check integrity", False)
                if child == 'dismiss':
                    return device.ui_action('/data/local/tmp/pi.xml', pi_app_xml, "Dismiss", False)

        except IOError:
            traceback.print_exc()

    # -----------------------------------------------
    #                  onXiaomiPif
    # -----------------------------------------------
    def onXiaomiPif(self, e):
        try:
            self._on_spin('start')
            xiaomi_pif = get_xiaomi_pif()
            self.console_stc.SetValue(xiaomi_pif)
        except IOError:
            traceback.print_exc()
        self._on_spin('stop')

    # -----------------------------------------------
    #                  onPiChecker
    # -----------------------------------------------
    def onPiChecker(self, e):
        try:
            device = get_phone()
            if not device.rooted:
                return
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User Pressed Play Integrity API Checker.")
            self._on_spin('start')

            # We need to kill TB Checker to make sure we read fresh values
            if self.pi_option.Selection in [2, 3]:
                res = device.perform_package_action(self.pi_app, 'kill', False)

            # launch the app
            res = device.perform_package_action(self.pi_app, 'launch', False)
            if res == -1:
                print(f"Error: during launching app {self.pi_app}.")
                self._on_spin('stop')
                return -1

            # See if we have coordinates saved
            coords = self.coords.query_entry(device.id, self.pi_app)
            coord_dismiss = None
            if coords is None:
                # For Play Store, we need to save multiple coordinates
                if self.pi_option.Selection == 3:
                    # Get coordinates for the first time
                    # user
                    coord_user = self.get_pi_app_coords(child='user')
                    if coord_user == -1:
                        print(f"Error: during tapping {self.pi_app} [user] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "user", coord_user)

                    # settings
                    coord_settings = self.get_pi_app_coords(child='settings')
                    if coord_settings == -1:
                        print(f"Error: during tapping {self.pi_app} [settings] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "settings", coord_settings)

                    # general
                    coord_general = self.get_pi_app_coords(child='general')
                    if coord_general == -1:
                        print(f"Error: during tapping {self.pi_app} [general] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "general", coord_general)
                    # page scroll
                    coord_scroll = self.get_pi_app_coords(child='scroll')
                    if coord_scroll == -1:
                        print(f"Error: during swipping {self.pi_app} [scroll] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "scroll", coord_scroll)
                    # Developer Options
                    coord_developer_options = self.get_pi_app_coords(child='developer_options')
                    if coord_developer_options == -1:
                        print(f"Error: during tapping {self.pi_app} [developer_options] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "developer_options", coord_developer_options)
                    # Check Integrity
                    coord_test = self.get_pi_app_coords(child='test')
                    if coord_test == -1:
                        print(f"Error: during tapping {self.pi_app} [Check Integrity] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
                    self.coords.update_nested_entry(device.id, self.pi_app, "test", coord_test)
                    coords = coord_test
                else:
                    # Get coordinates for the first time
                    coords = self.get_pi_app_coords()
                    if coords is not None and coords != -1:
                        # update coords.json
                        self.coords.update_entry(device.id, self.pi_app, coords)
                    else:
                        print("Error: Could not get coordinates.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]
                            self.coords.save_data()
                        self._on_spin('stop')
                        return -1
            elif self.pi_option.Selection == 3:
                coord_user = self.coords.query_nested_entry(device.id, self.pi_app, "user")
                coord_settings = self.coords.query_nested_entry(device.id, self.pi_app, "settings")
                coord_general = self.coords.query_nested_entry(device.id, self.pi_app, "general")
                coord_scroll = self.coords.query_nested_entry(device.id, self.pi_app, "scroll")
                coord_developer_options = self.coords.query_nested_entry(device.id, self.pi_app, "developer_options")
                coord_test = self.coords.query_nested_entry(device.id, self.pi_app, "test")
                coord_dismiss = self.coords.query_nested_entry(device.id, self.pi_app, "dismiss")
                if coord_user is None or coord_user == '' or coord_settings is None or coord_settings == '' or coord_general is None or coord_general == '' or coord_developer_options is None or coord_developer_options == '' or coord_test is None or coord_test == '':
                    print(f"\nError: coordinates for {self.pi_app} is missing from settings\nPlease run the test again so that PixelFlasher can try to get fresh new coordinates.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1

                # user
                res = device.click(coord_user)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [user] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1
                time.sleep(1)
                # settings
                res = device.click(coord_settings)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [settings] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1
                time.sleep(1)
                # general
                res = device.click(coord_general)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [general] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1
                time.sleep(1)
                res = device.swipe(coord_scroll)
                if res == -1:
                    print(f"Error: during swiping {self.pi_app} [scroll] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1
                time.sleep(1)
                # developer_options
                res = device.click(coord_developer_options)
                if res == -1:
                    print(f"Error: during tapping {self.pi_app} [developer_options] screen.")
                    if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                        del self.coords.data[device.id][self.pi_app]
                        self.coords.save_data()
                    self._on_spin('stop')
                    return -1
                time.sleep(1)
                # test
                coords = coord_test

            # Click on coordinates
            res = device.click(coords)
            if res == -1:
                print(f"\nError: coordinates for {self.pi_app} is missing from settings\nPlease run the test again so that PixelFlasher can try to get fresh new coordinates.")
                if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                    del self.coords.data[device.id][self.pi_app]
                    self.coords.save_data()
                self._on_spin('stop')
                return -1

            # pull view
            config_path = get_config_path()
            pi_xml = os.path.join(config_path, 'tmp', 'pi.xml')
            time.sleep(5)
            res = device.ui_action('/data/local/tmp/pi.xml', pi_xml)
            if res == -1:
                print(f"Error: during uiautomator {self.pi_app}.")
                self._on_spin('stop')
                return -1

            # extract result
            if self.pi_option.Selection == 0:
                res = process_pi_xml_piac(pi_xml)
            if self.pi_option.Selection == 1:
                res = process_pi_xml_spic(pi_xml)
            if self.pi_option.Selection == 2:
                res = process_pi_xml_tb(pi_xml)
            if self.pi_option.Selection == 3:
                res = process_pi_xml_ps(pi_xml)
                # dismiss
                if coord_dismiss is None or coord_dismiss == '' or coord_dismiss == -1:
                    coord_dismiss = self.get_pi_app_coords(child='dismiss')
                    if coord_dismiss == -1:
                        print(f"Error: getting coordinates for {self.pi_app} [dismiss] screen.")
                        if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                            del self.coords.data[device.id][self.pi_app]['dismiss']
                            self.coords.save_data()
                        self._on_spin('stop')
                    self.coords.update_nested_entry(device.id, self.pi_app, "dismiss", coord_dismiss)

            if res == -1:
                print(f"Error: during processing the response from {self.pi_app}.")
                self._on_spin('stop')
                return -1

            self.console_stc.SetValue('')
            if res is None or res == '':
                if device.id in self.coords.data and self.pi_app in self.coords.data[device.id]:
                    del self.coords.data[device.id][self.pi_app]['dismiss']
            else:
                self.console_stc.SetValue(res)

        except IOError:
            traceback.print_exc()
        self._on_spin('stop')


    # -----------------------------------------------
    #                  sort_prop
    # -----------------------------------------------
    def sort_prop(self, file_path):
        filename = os.path.basename(file_path)
        if filename == "build.prop":
            return 1
        elif filename == "system-build.prop":
            return 2
        elif filename == "system.prop":
            return 3
        elif filename == "product-build.prop":
            return 4
        elif filename == "product.prop":
            return 5
        elif filename == "vendor-build.prop":
            return 6
        elif filename == "vendor.prop":
            return 7
        else:
            return 999


    # -----------------------------------------------
    #                  onProcessBuildProp
    # -----------------------------------------------
    def onProcessBuildProp(self, e):
        # sourcery skip: dict-assign-update-to-union
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} User pressed Process build.prop")
        wildcard = "Property files (*.prop)|*.prop|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Choose property files to open", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dialog.ShowModal() == wx.ID_CANCEL:
            print("User cancelled file selection.")
            return

        paths = dialog.GetPaths()
        dialog.Destroy()
        sorted_paths = sorted(paths, key=self.sort_prop)

        print(f"Selected files: {sorted_paths}")

        try:
            self._on_spin('start')
            processed_dict = {}
            for pathname in reversed(sorted_paths):
                with open(pathname, 'r', encoding='ISO-8859-1', errors="replace") as f:
                    content = f.readlines()

                contentList = [x.strip().split('#')[0].split('=', 1) for x in content if '=' in x.split('#')[0]]
                contentDict = dict(contentList)

                # Update processed_dict with entries from the current file
                # In place Union operator below fails on Windows 2019 build, so use the update method instead.
                # processed_dict |= contentDict
                processed_dict.update(contentDict)

                # Apply the substitution to the values in processed_dict
                for k, v in contentDict.items():
                    for x in v.split('$')[1:]:
                        key = re.findall(r'\w+', x)[0]
                        v = v.replace(f'${key}', processed_dict[key])
                    processed_dict[k] = v.strip()

            # PRODUCT
            keys = ['ro.product.name', 'ro.product.system.name', 'ro.product.product.name', 'ro.product.vendor.name']
            ro_product_name = get_first_match(processed_dict, keys)

            # DEVICE
            keys = ['ro.product.device', 'ro.product.system.device', 'ro.product.product.device', 'ro.product.vendor.device', 'ro.build.product']
            ro_product_device = get_first_match(processed_dict, keys)

            # MANUFACTURER
            keys = ['ro.product.manufacturer', 'ro.product.system.manufacturer', 'ro.product.product.manufacturer', 'ro.product.vendor.manufacturer']
            ro_product_manufacturer = get_first_match(processed_dict, keys)

            # BRAND
            keys = ['ro.product.brand', 'ro.product.system.brand', 'ro.product.product.brand', 'ro.product.vendor.brand']
            ro_product_brand = get_first_match(processed_dict, keys)

            # MODEL
            keys = ['ro.product.model', 'ro.product.system.model', 'ro.product.product.model', 'ro.product.vendor.model']
            ro_product_model = get_first_match(processed_dict, keys)

            # FINGERPRINT
            keys = ['ro.build.fingerprint', 'ro.system.build.fingerprint', 'ro.product.build.fingerprint', 'ro.vendor.build.fingerprint']
            ro_build_fingerprint = get_first_match(processed_dict, keys)

            # SECURITY_PATCH
            keys = ['ro.build.version.security_patch', 'ro.vendor.build.security_patch']
            ro_build_version_security_patch = get_first_match(processed_dict, keys)

            # FIRST_API_LEVEL
            keys = ['ro.product.first_api_level', 'ro.board.first_api_level', 'ro.board.api_level', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.build.version.sdk', 'ro.system.build.version.sdk', 'ro.vendor.build.version.sdk', 'ro.product.build.version.sdk']
            ro_product_first_api_level = get_first_match(processed_dict, keys)
            if ro_product_first_api_level and int(ro_product_first_api_level) > 32:
                ro_product_first_api_level = '32'

            # BUILD_ID
            keys = ['ro.build.id']
            ro_build_id = get_first_match(processed_dict, keys)
            if ro_build_id is None or ro_build_id == '':
                pattern = r'[^\/]*\/[^\/]*\/[^:]*:[^\/]*\/([^\/]*)\/[^\/]*\/[^\/]*'
                match = re.search(pattern, ro_build_fingerprint)
                if match:
                    ro_build_id = match[1]

            # VNDK_VERSION
            keys = ['ro.vndk.version', 'ro.product.vndk.version']
            ro_vndk_version = get_first_match(processed_dict, keys)

            if ro_build_fingerprint is None or ro_build_fingerprint == '':
                keys = ['ro.build.version.release']
                ro_build_version_release = get_first_match(processed_dict, keys)

                keys = ['ro.build.version.incremental']
                ro_build_version_incremental = get_first_match(processed_dict, keys)

                keys = ['ro.build.type']
                ro_build_type = get_first_match(processed_dict, keys)

                keys = ['ro.build.tags']
                ro_build_tags = get_first_match(processed_dict, keys)

                ro_build_fingerprint = f"{ro_product_brand}/{ro_product_name}/{ro_product_device}:{ro_build_version_release}/{ro_build_id}/{ro_build_version_incremental}:{ro_build_type}/{ro_build_tags}"

            donor_data = {
                "PRODUCT": ro_product_name,
                "DEVICE": ro_product_device,
                "MANUFACTURER": ro_product_manufacturer,
                "BRAND": ro_product_brand,
                "MODEL": ro_product_model,
                "FINGERPRINT": ro_build_fingerprint,
                "SECURITY_PATCH": ro_build_version_security_patch,
                "BUILD_ID": ro_build_id,
                "VNDK_VERSION": ro_vndk_version
            }
            if self.advanced_props_support:
                donor_data["DEVICE_INITIAL_SDK_INT"] = ro_product_first_api_level
                donor_data["*api_level"] = ro_product_first_api_level
                donor_data["*.security_patch"] = ro_build_version_security_patch
                donor_data["*.build.id"] = ro_build_id
                donor_data["VERBOSE_LOGS"] = "0"
            else:
                donor_data["FIRST_API_LEVEL"] = ro_product_first_api_level

            donor_json = json.dumps(donor_data, indent=4)

            self.console_stc.SetValue(donor_json)
            # print(donor_json)

            # Auto Push pif.json
            if self.auto_push_pif_checkbox.IsEnabled() and self.auto_push_pif_checkbox.IsChecked():
                self.active_pif_stc.SetValue(self.console_stc.GetValue())
                self.onUpdatePifProp(None)

                # Auto test Play Integrity
                if self.auto_check_pi_checkbox.IsEnabled() and self.auto_check_pi_checkbox.IsChecked():
                    print("Auto Testing Play Integrity ...")
                    self.onPiChecker(None)

        except IOError:
            wx.LogError(f"Cannot process file: '{pathname}'.")
            traceback.print_exc()
        self._on_spin('stop')


    # -----------------------------------------------
    #                  onContextMenu
    # -----------------------------------------------
    def onContextMenu(self, event):
        menu = wx.Menu()
        copy_item = menu.Append(wx.ID_COPY, "Copy")
        select_all_item = menu.Append(wx.ID_SELECTALL, "Select All")
        self.Bind(wx.EVT_MENU, self.onCopy, copy_item)
        self.Bind(wx.EVT_MENU, self.onSelectAll, select_all_item)

        self.PopupMenu(menu)
        menu.Destroy()

    # -----------------------------------------------
    #                  onConsoleStcChange
    # -----------------------------------------------
    def onConsoleStcChange(self, event):
        json_data = self.console_stc.GetValue()

        if json_data:
            try:
                json.loads(json_data)
                self.paste_selection.Enable(True)
            except Exception:
                try:
                    json5.loads(json_data)
                    self.paste_selection.Enable(True)
                except Exception:
                    self.paste_selection.Enable(False)
        else:
            self.paste_selection.Enable(False)
        event.Skip()

    # -----------------------------------------------
    #                  onActivePifStcChange
    # -----------------------------------------------
    def onActivePifStcChange(self, event):
        json_data = self.active_pif_stc.GetValue()

        if not self.enable_buttons:
            self.create_pif_button.Enable(False)
            return

        if json_data:
            try:
                json.loads(json_data)
                self.create_pif_button.Enable(True)
            except Exception:
                try:
                    json5.loads(json_data)
                    self.create_pif_button.Enable(True)
                except Exception:
                    self.create_pif_button.Enable(False)
        else:
            self.create_pif_button.Enable(False)

        if json_data != self.device_pif:
            self.pif_modified_image.SetBitmap(images.alert_red_24.GetBitmap())
            self.pif_modified_image.SetToolTip(u"The contents is different than what is currently on the device.\nUpdate pif.json before testing.")
        else:
            self.pif_modified_image.SetBitmap(images.alert_gray_24.GetBitmap())
            self.pif_modified_image.SetToolTip(u"Active pif is not modified.")

        if event:
            event.Skip()

    # -----------------------------------------------
    #                  onPasteSelection
    # -----------------------------------------------
    def onPasteSelection(self, event):
        self.active_pif_stc.SetValue(self.console_stc.GetValue())
        event.Skip()

    # -----------------------------------------------
    #                  onCopy
    # -----------------------------------------------
    def onCopy(self, event):
        self.console_stc.CopySelectedText()

    # -----------------------------------------------
    #                  onSelectAll
    # -----------------------------------------------
    def onSelectAll(self, event):
        self.console_stc.SelectAll()

    # -----------------------------------------------
    #                  _on_spin
    # -----------------------------------------------
    def _on_spin(self, state):
        wx.YieldIfNeeded()
        if state == 'start':
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
            self.Parent._on_spin('start')
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.Parent._on_spin('stop')

    # -----------------------------------------------
    #                  onResize
    # -----------------------------------------------
    def onResize(self, event):
        self.resizing = True
        stc_size = self.active_pif_stc.GetSize()
        x = stc_size.GetWidth()
        self.active_pif_stc.SetScrollWidth(x - 30)
        self.console_stc.SetScrollWidth(x - 30)

        self.Layout()
        event.Skip(True)

