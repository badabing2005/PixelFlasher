import os
from urllib.parse import urlparse

import wx


def show_factory_image_dialog(parent, title, instruction, root_label, nodes, size=(850, 620), download_button=False):
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

    button_sizer = wx.BoxSizer(wx.HORIZONTAL)
    ok_button = wx.Button(dialog, wx.ID_OK)
    cancel_button = wx.Button(dialog, wx.ID_CANCEL)
    download_btn = None
    button_sizer.AddStretchSpacer()
    button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
    if download_button:
        download_btn = wx.Button(dialog, wx.ID_ANY, "Download")
        button_sizer.Add(download_btn, 0, wx.RIGHT, 5)
    button_sizer.Add(cancel_button, 0)
    ok_button.Enable(False)
    ok_button.SetDefault()
    if download_btn:
        download_btn.Enable(False)

    def update_button_states():
        selected_item = tree_ctrl.GetSelection()
        if selected_item and selected_item != root:
            item_data = tree_ctrl.GetItemData(selected_item)
            is_valid = item_data is not None
            ok_button.Enable(is_valid)
            if download_btn:
                url = item_data.get('url') if isinstance(item_data, dict) else None
                download_btn.Enable(is_valid and bool(url))
        else:
            ok_button.Enable(False)
            if download_btn:
                download_btn.Enable(False)

    def on_tree_selection(event):
        update_button_states()

    tree_ctrl.Bind(wx.EVT_TREE_SEL_CHANGED, on_tree_selection)

    def on_download(event):
        if not download_btn:
            return
        selected_item = tree_ctrl.GetSelection()
        if not selected_item or selected_item == root:
            return
        item_data = tree_ctrl.GetItemData(selected_item)
        if not isinstance(item_data, dict):
            return
        url = item_data.get('url')
        if not url:
            return
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) if parsed.path else ''
        if not filename:
            filename = "download"

        launched = wx.LaunchDefaultBrowser(url)
        if launched:
            wx.MessageBox(
                f"Opened in your browser. Use it to download:\n{filename}",
                "Download in Browser",
                style=wx.OK | wx.ICON_INFORMATION,
                parent=dialog,
            )
        else:
            wx.MessageBox(
                f"Unable to open default browser for:\n{url}",
                "Download Error",
                style=wx.OK | wx.ICON_ERROR,
                parent=dialog,
            )

    if download_btn:
        download_btn.Bind(wx.EVT_BUTTON, on_download)

    dialog_sizer = wx.BoxSizer(wx.VERTICAL)
    dialog_sizer.Add(instruction_label, 0, wx.ALL, 10)
    dialog_sizer.Add(tree_ctrl, 1, wx.EXPAND | wx.ALL, 10)
    dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
    dialog.SetSizer(dialog_sizer)
    update_button_states()

    selected_data = None
    if dialog.ShowModal() == wx.ID_OK:
        selected_item = tree_ctrl.GetSelection()
        if selected_item and selected_item != root:
            selected_data = tree_ctrl.GetItemData(selected_item)

    dialog.Destroy()
    return selected_data
