#!/usr/bin/env python

import gettext
import sys

import wx
import wx.stc as stc

from runtime import *

_ = gettext.gettext

# ============================================================================
#                               Class FileEditor
# ============================================================================
class FileEditor(wx.Dialog):
    def __init__(self, parent, file_path, language='batch', width=1500, height=600):
        super().__init__(parent=parent, title=_("File Editor"), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=(width, height))

        self.file_path = file_path
        self.language = language
        self.width = width
        self.height = height
        self.create_widgets()
        self.load_file()
        self.SetSize((self.width, self.height))

    def create_widgets(self):
        self.text_ctrl = stc.StyledTextCtrl(self, style=wx.HSCROLL)
        if sys.platform == "win32":
            if self.language == "batch":
                self.text_ctrl.SetLexer(stc.STC_LEX_BATCH)
                self.text_ctrl.StyleSetSpec(stc.STC_BAT_DEFAULT, "fore:#000000")
                self.text_ctrl.StyleSetSpec(stc.STC_BAT_COMMENT, "fore:#008000")
                self.text_ctrl.StyleSetSpec(stc.STC_BAT_WORD, "fore:#000000,bold,back:#FFFFFF")
                self.text_ctrl.SetKeyWords(0, " ".join(["if else goto echo set", "cd dir rd md del", "call start exit rem"]))
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_COMMAND, wx.Colour(0, 128, 192)) # command color
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_LABEL, wx.Colour(0, 128, 192)) # label color
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_COMMENT, wx.Colour(0, 128, 0)) # comment color
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_WORD, wx.Colour(0, 0, 255)) # keyword color
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_HIDE, wx.Colour(128, 128, 128)) # color for hidden text
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_IDENTIFIER, wx.Colour(255, 128, 0))  # variable text color
                self.text_ctrl.StyleSetForeground(stc.STC_BAT_OPERATOR , wx.Colour(255, 0, 255))  # operator text color
            elif self.language == "json":
                self.text_ctrl.SetLexer(stc.STC_LEX_JSON)
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_DEFAULT, "fore:#000000")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_NUMBER, "fore:#007F7F")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_STRING, "fore:#7F007F")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_PROPERTYNAME, "fore:#007F00")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_ESCAPESEQUENCE, "fore:#7F7F00")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_KEYWORD, "fore:#00007F,bold")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_OPERATOR, "fore:#7F0000")
        else:
            if self.language == "batch":
                self.text_ctrl.SetLexer(stc.STC_LEX_BASH)
                self.text_ctrl.StyleSetSpec(stc.STC_SH_DEFAULT, "fore:#000000")
                self.text_ctrl.StyleSetSpec(stc.STC_SH_COMMENTLINE , "fore:#008000")
                self.text_ctrl.StyleSetSpec(stc.STC_SH_WORD, "fore:#000000,bold,back:#FFFFFF")
                self.text_ctrl.SetKeyWords(0, " ".join(["if else elif fi echo set", "cd dir rd md rm", "exit"]))
                self.text_ctrl.StyleSetForeground(stc.STC_SH_OPERATOR , wx.Colour(0, 128, 192)) # operator color
                self.text_ctrl.StyleSetForeground(stc.STC_SH_STRING  , wx.Colour(205, 146, 93)) # label color
                self.text_ctrl.StyleSetForeground(stc.STC_SH_COMMENTLINE, wx.Colour(0, 128, 0)) # comment color
                self.text_ctrl.StyleSetForeground(stc.STC_SH_WORD, wx.Colour(0, 0, 255)) # keyword color
                self.text_ctrl.StyleSetForeground(stc.STC_SH_IDENTIFIER, wx.Colour(255, 128, 0))  # variable text color
            elif self.language == "json":
                self.text_ctrl.SetLexer(stc.STC_LEX_JSON)
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_DEFAULT, "fore:#000000")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_NUMBER, "fore:#007F7F")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_STRING, "fore:#7F007F")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_PROPERTYNAME, "fore:#007F00")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_ESCAPESEQUENCE, "fore:#7F7F00")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_KEYWORD, "fore:#00007F,bold")
                self.text_ctrl.StyleSetSpec(stc.STC_JSON_OPERATOR, "fore:#7F0000")

        self.text_ctrl.SetCaretForeground(wx.BLACK)
        self.text_ctrl.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.text_ctrl.SetMarginWidth(1, 30)

        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.text_ctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)

        self.open_folder = wx.Button(self, label=_("Open Folder"))
        self.open_shell = wx.Button(self, label=_("Open Shell"))
        self.save_button = wx.Button(self, label=_("Save and Continue"))
        self.cancel_button = wx.Button(self, label=_("Cancel and Abort"))
        if sys.platform in ["win32", "darwin"]:
            self.open_folder.SetToolTip(_(u"Open Folder in working directory"))
            self.open_shell.SetToolTip(_(u"Open command shell in working directory"))
        else:
            self.open_folder.SetToolTip(_(u"Open Folder in working directory\nNote: PF_FILEMANAGER needs to be set."))
            self.open_shell.SetToolTip(_(u"Open Terminal shell in working directory"))
        self.save_button.SetToolTip(_(u"Save the file and continue."))
        self.cancel_button.SetToolTip(_(u"Cancel and Abort."))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        sizer.Add(wx.StaticLine(self), proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        button_sizer.Add(self.open_folder, proportion=0, flag=wx.ALL, border=5)
        button_sizer.Add(self.open_shell, proportion=0, flag=wx.ALL, border=5)
        button_sizer.Add(self.save_button, proportion=0, flag=wx.ALL, border=5)
        button_sizer.Add(self.cancel_button, proportion=0, flag=wx.ALL, border=5)
        button_sizer.Add((0, 0), 1, wx.EXPAND, 5)
        sizer.Add(button_sizer, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        self.SetSizer(sizer)
        self.SetSize((1600, 900))  # set initial size of the editor window
        self.SetMinSize((400, 300))  # set minimum size of the editor window

        self.open_folder.Bind(wx.EVT_BUTTON, self.on_open_folder)
        self.open_shell.Bind(wx.EVT_BUTTON, self.on_open_shell)
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)
        # self.Bind(wx.EVT_SIZE, self._on_resize)

        # fix horizontal scroll bar
        self.text_ctrl.SetWrapMode(wx.stc.STC_WRAP_NONE)
        self.text_ctrl.SetUseHorizontalScrollBar(True)

        # disable vertical scrolling on mouse wheel
        self.text_ctrl.SetUseVerticalScrollBar(True)
        self.text_ctrl.SetScrollWidthTracking(True)
        self.text_ctrl.SetScrollWidth(1)

        # center the dialog
        self.CenterOnParent()

        # set tab width
        self.text_ctrl.SetTabWidth(4)

        # set indentation
        self.text_ctrl.SetIndent(4)

    def load_file(self):
        with open(self.file_path, 'r', encoding='ISO-8859-1', errors="replace") as f:
            contents = f.read()
            self.text_ctrl.SetValue(contents)

    def on_open_folder(self, event):
        open_folder(self.Parent, self.file_path, True)

    def on_open_shell(self, event):
        open_terminal(self.Parent, self.file_path, True)

    def on_save(self, event):
        with open(self.file_path, 'w', encoding='ISO-8859-1', errors="replace", newline='\n') as f:
            f.write(self.text_ctrl.GetValue())
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def _on_resize(self, event):
        width = self.Rect.Width
        height = self.Rect.Height
        print(f"width: {width}\nheight: {height}")
        event.Skip(True)
