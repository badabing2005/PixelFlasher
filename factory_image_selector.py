import wx


def show_factory_image_dialog(parent, title, instruction, root_label, nodes, size=(850, 620)):
    dialog = wx.Dialog(parent, title=title, size=size)
    instruction_label = wx.StaticText(dialog, label=instruction)
    tree_ctrl = wx.TreeCtrl(dialog, style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)
    root = tree_ctrl.AddRoot(root_label)

    def add_nodes(parent_item, items):
        if not isinstance(items, list):
            return
        for node in items:
            if not isinstance(node, dict):
                continue
            label = str(node.get('label', ''))
            item = tree_ctrl.AppendItem(parent_item, label)
            if 'data' in node:
                tree_ctrl.SetItemData(item, node.get('data'))
            children = node.get('children') or []
            if children:
                add_nodes(item, children)

    add_nodes(root, nodes)
    tree_ctrl.Expand(root)

    button_sizer = wx.StdDialogButtonSizer()
    ok_button = wx.Button(dialog, wx.ID_OK)
    cancel_button = wx.Button(dialog, wx.ID_CANCEL)
    button_sizer.AddButton(ok_button)
    button_sizer.AddButton(cancel_button)
    button_sizer.Realize()
    ok_button.Enable(False)

    def on_tree_selection(event):
        selected_item = tree_ctrl.GetSelection()
        if selected_item and selected_item != root:
            item_data = tree_ctrl.GetItemData(selected_item)
            ok_button.Enable(item_data is not None)
        else:
            ok_button.Enable(False)

    tree_ctrl.Bind(wx.EVT_TREE_SEL_CHANGED, on_tree_selection)

    dialog_sizer = wx.BoxSizer(wx.VERTICAL)
    dialog_sizer.Add(instruction_label, 0, wx.ALL, 10)
    dialog_sizer.Add(tree_ctrl, 1, wx.EXPAND | wx.ALL, 10)
    dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
    dialog.SetSizer(dialog_sizer)

    selected_data = None
    if dialog.ShowModal() == wx.ID_OK:
        selected_item = tree_ctrl.GetSelection()
        if selected_item and selected_item != root:
            selected_data = tree_ctrl.GetItemData(selected_item)

    dialog.Destroy()
    return selected_data
