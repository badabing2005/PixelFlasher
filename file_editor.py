import wx
import wx.stc as stc

class FileEditor(wx.Dialog):
    def __init__(self, parent, file_path):
        # super().__init__(parent=None, title="File Editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        super().__init__(parent=parent, title="File Editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.file_path = file_path
        self.create_widgets()
        self.load_file()

    def create_widgets(self):
        self.text_ctrl = stc.StyledTextCtrl(self, style=wx.HSCROLL)
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

        self.text_ctrl.SetCaretForeground(wx.BLACK)
        self.text_ctrl.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.text_ctrl.SetMarginWidth(1, 30)

        font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.text_ctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, font)

        self.save_button = wx.Button(self, label="Save and Continue")
        self.cancel_button = wx.Button(self, label="Cancel and Abort")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        sizer.Add(wx.StaticLine(self), proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.save_button, proportion=0, flag=wx.RIGHT, border=5)
        button_sizer.Add(self.cancel_button, proportion=0)
        sizer.Add(button_sizer, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        self.SetSizer(sizer)
        self.SetSize((1600, 900))  # set initial size of the editor window
        self.SetMinSize((400, 300))  # set minimum size of the editor window

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
        with open(self.file_path, 'r') as f:
            contents = f.read()
            self.text_ctrl.SetValue(contents)

    def on_save(self, event):
        with open(self.file_path, 'w', errors="replace", newline='\n') as f:
            f.write(self.text_ctrl.GetValue())
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def _on_resize(self, event):
        width = self.Rect.Width
        height = self.Rect.Height
        print(f"width: {width}\nheight: {height}")
        event.Skip(True)
