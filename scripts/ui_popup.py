# -*- coding: utf-8 -*-
"""Rhino 8 Eto popup for quickly previewing web-based charts."""

import System
import os
import Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing

DEFAULT_URL = "https://public.flourish.studio/visualisation/28056071/"
MODE_URL = "Flourish URL"
MODE_ANIMATED = "Animated Treemap (local)"
JSON_VIS = "JSON (graph)"
JSON_DATA = "JSON (data only)"
_DIALOG = None


class WebGraphDialog(forms.Form):
    """Simple modeless form that embeds a web page in an Eto WebView."""

    def __init__(self, start_mode=MODE_URL):
        super(WebGraphDialog, self).__init__()

        self.Title = "Web Graph Prototype"
        self.ClientSize = drawing.Size(1100, 760)
        self.Padding = drawing.Padding(10)
        self.Resizable = True

        self.mode_dropdown = forms.DropDown()
        self.mode_dropdown.DataStore = [MODE_URL, MODE_ANIMATED, JSON_VIS, JSON_DATA]

        self.url_box = forms.TextBox()
        self.url_box.Text = DEFAULT_URL

        self.load_button = forms.Button()
        self.load_button.Text = "Load URL"

        self.reload_button = forms.Button()
        self.reload_button.Text = "Reload"

        self.close_button = forms.Button()
        self.close_button.Text = "Close"

        self.status_label = forms.Label()
        self.status_label.Text = "Paste an embed URL and click Load URL."
        self.web = forms.WebView()

        self.load_button.Click += self._on_load_clicked
        self.reload_button.Click += self._on_reload_clicked
        self.close_button.Click += self._on_close_clicked
        self.mode_dropdown.SelectedIndexChanged += self._on_mode_changed
        self.web.DocumentLoaded += self._on_document_loaded
        self.web.DocumentLoading += self._on_document_loading

        top_row = forms.StackLayout()
        top_row.Orientation = forms.Orientation.Horizontal
        top_row.Spacing = 6
        top_row.Items.Add(forms.StackLayoutItem(self.mode_dropdown, False))
        top_row.Items.Add(forms.StackLayoutItem(self.url_box, True))
        top_row.Items.Add(forms.StackLayoutItem(self.load_button, False))
        top_row.Items.Add(forms.StackLayoutItem(self.reload_button, False))
        top_row.Items.Add(forms.StackLayoutItem(self.close_button, False))

        header_layout = forms.StackLayout()
        header_layout.Orientation = forms.Orientation.Vertical
        header_layout.Spacing = 8
        header_layout.Items.Add(forms.StackLayoutItem(top_row, False))
        header_layout.Items.Add(forms.StackLayoutItem(self.status_label, False))

        splitter = forms.Splitter()
        splitter.Orientation = forms.Orientation.Vertical
        splitter.FixedPanel = forms.SplitterFixedPanel.Panel1
        splitter.Position = 72
        splitter.Panel1 = header_layout
        splitter.Panel2 = self.web
        self.Content = splitter

        self._set_mode(start_mode)
        self._load_current_url()

    def _load_current_url(self):
        """Navigate WebView to URL currently in textbox."""
        if self._current_mode() == MODE_ANIMATED:
            self._load_local_animated_treemap()
            return
        if self._current_mode() == JSON_VIS:
            self._load_local_ws_treemap()
            return
        if self._current_mode() == JSON_DATA:
            self._load_local_ws_data()
            return

        raw_url = (self.url_box.Text or "").strip()
        if not raw_url:
            self.status_label.Text = "URL is empty."
            return

        try:
            normalized_url = self._normalize_flourish_url(raw_url)
            if normalized_url != raw_url:
                self.url_box.Text = normalized_url

            self.web.Url = System.Uri(normalized_url)
            self.status_label.Text = "Loading..."
        except Exception as exc:
            self.status_label.Text = "Invalid URL: {0}".format(exc)

    def _load_local_animated_treemap(self):
        """Load local D3 animated treemap HTML in the WebView."""
        html_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "bin", "animated_treemap.html")
        )
        if not os.path.exists(html_path):
            self.status_label.Text = "Missing file: {0}".format(html_path)
            return

        try:
            self.web.Url = System.Uri(html_path)
            self.status_label.Text = "Loading local animated treemap..."
        except Exception as exc:
            self.status_label.Text = "Failed to load local file: {0}".format(exc)

    def _load_local_ws_treemap(self):
        """Load D3 treemap from localhost server (listener.py); page fetches /data.json."""
        try:
            self.web.Url = System.Uri("http://localhost:8080/ws_treemap.html")
            self.status_label.Text = "Loading from localhost. Start listener.py first (port 8080)."
        except Exception as exc:
            self.status_label.Text = "Failed to load: {0}".format(exc)

    def _load_local_ws_data(self):
        """Load data-only page from localhost server; fetches /data.json."""
        try:
            self.web.Url = System.Uri("http://localhost:8080/ws_data.html")
            self.status_label.Text = "Loading from localhost. Start listener.py first (port 8080)."
        except Exception as exc:
            self.status_label.Text = "Failed to load: {0}".format(exc)

    @staticmethod
    def _normalize_flourish_url(raw_url):
        """Convert known Flourish public URLs to embed URLs for WebView."""
        lower = raw_url.lower()
        if "public.flourish.studio/visualisation/" in lower and "/embed" not in lower:
            return raw_url.rstrip("/") + "/embed"
        return raw_url

    def _on_load_clicked(self, sender, e):
        self._load_current_url()

    def _on_mode_changed(self, sender, e):
        self._set_mode(self._current_mode())
        self._load_current_url()

    def _on_reload_clicked(self, sender, e):
        try:
            self.web.Reload()
            self.status_label.Text = "Reloading..."
        except Exception as exc:
            self.status_label.Text = "Reload failed: {0}".format(exc)

    def _on_close_clicked(self, sender, e):
        self.Close()

    def _on_document_loaded(self, sender, e):
        self.status_label.Text = "Page loaded."

    def _on_document_loading(self, sender, e):
        # Lightweight JS -> Rhino bridge placeholder.
        # In page JS:
        #   window.location.href = "myapp://eventName?foo=bar";
        uri = e.Uri
        if uri and uri.Scheme and uri.Scheme.lower() == "myapp":
            e.Cancel = True
            self.status_label.Text = "Bridge event: {0}{1}".format(uri.Host, uri.Query)

    def _set_mode(self, mode):
        options = [MODE_URL, MODE_ANIMATED, JSON_VIS, JSON_DATA]
        if mode not in options:
            mode = MODE_URL
        self.mode_dropdown.SelectedIndex = options.index(mode)

        is_url_mode = mode == MODE_URL
        self.url_box.Enabled = is_url_mode
        if is_url_mode:
            self.load_button.Text = "Load URL"
            self.status_label.Text = "Paste an embed URL and click Load URL."
        elif mode == JSON_VIS:
            self.load_button.Text = "Load Treemap"
            self.status_label.Text = "Local JSON treemap. Run listener.py first."
        elif mode == JSON_DATA:
            self.load_button.Text = "Load data"
            self.status_label.Text = "Raw JSON from watched file. Run listener.py first."
        else:
            self.load_button.Text = "Load Treemap"
            self.status_label.Text = "Load local animated treemap from bin folder."

    def _current_mode(self):
        idx = self.mode_dropdown.SelectedIndex
        if idx == 0: return MODE_URL
        if idx == 1: return MODE_ANIMATED
        if idx == 2: return JSON_VIS
        return JSON_DATA


def show_dialog(start_mode=MODE_URL):
    """Open dialog as Rhino-owned modeless popup."""
    global _DIALOG

    if _DIALOG is not None and _DIALOG.Visible:
        _DIALOG._set_mode(start_mode)
        _DIALOG._load_current_url()
        _DIALOG.BringToFront()
        return

    dlg = WebGraphDialog(start_mode=start_mode)
    dlg.Owner = Rhino.UI.RhinoEtoApp.MainWindow

    def _on_closed(sender, e):
        global _DIALOG
        _DIALOG = None

    dlg.Closed += _on_closed
    Rhino.UI.EtoExtensions.Show(dlg, Rhino.RhinoDoc.ActiveDoc)
    _DIALOG = dlg
