import threading
import customtkinter
from config import (
    BG_COLOR, FRAME_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER,
    WHITE, LIGHT_GRAY, DARK_GRAY, ERROR_RED,
    FONT_HEADING, FONT_BODY, FONT_SMALL,
)


class PlaylistFrame(customtkinter.CTkFrame):
    def __init__(self, master, app, username):
        super().__init__(master, fg_color=BG_COLOR)
        self.app = app
        self.username = username
        self.playlist_data = []
        self.checkbox_vars = []

        self._build_ui()
        self._start_loading()

    def _build_ui(self):
        # Header bar
        header = customtkinter.CTkFrame(self, fg_color=FRAME_COLOR, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        back_btn = customtkinter.CTkButton(
            header, text="< Back", width=80, height=32,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self.app.show_auth_screen,
        )
        back_btn.pack(side="left", padx=15, pady=14)

        customtkinter.CTkLabel(
            header, text=f"Welcome, {self.username}",
            font=FONT_HEADING, text_color=WHITE,
        ).pack(side="left", padx=10, pady=14)

        self.load_btn = customtkinter.CTkButton(
            header, text="Load Artists", width=130, height=32,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=WHITE, font=FONT_BODY,
            command=self._on_load_artists,
        )
        self.load_btn.pack(side="right", padx=15, pady=14)

        # Toolbar
        toolbar = customtkinter.CTkFrame(self, fg_color=BG_COLOR)
        toolbar.pack(fill="x", padx=20, pady=(15, 5))

        customtkinter.CTkLabel(
            toolbar, text="Select playlists to scan",
            font=FONT_BODY, text_color=LIGHT_GRAY,
        ).pack(side="left")

        customtkinter.CTkButton(
            toolbar, text="Deselect All", width=90, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._deselect_all,
        ).pack(side="right", padx=(5, 0))

        customtkinter.CTkButton(
            toolbar, text="Select All", width=90, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._select_all,
        ).pack(side="right")

        # Scrollable playlist list
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, fg_color=BG_COLOR,
            scrollbar_button_color=DARK_GRAY,
            scrollbar_button_hover_color="#3a3a3a",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # Loading label
        self.loading_label = customtkinter.CTkLabel(
            self.scroll_frame, text="", font=FONT_BODY, text_color=LIGHT_GRAY,
        )

        # Error label
        self.error_label = customtkinter.CTkLabel(
            self, text="", font=FONT_SMALL, text_color=ERROR_RED,
        )
        self.error_label.pack(pady=(0, 10))

    def _start_loading(self):
        self.loading_label.configure(text="Loading your playlists...")
        self.loading_label.pack(pady=20)
        thread = threading.Thread(target=self._fetch_playlists_bg, daemon=True)
        thread.start()

    def _fetch_playlists_bg(self):
        try:
            playlists = self.app.client.get_playlists()
            self.after(0, lambda: self._populate_playlists(playlists))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._on_load_error(msg))

    def _on_load_error(self, message):
        self.loading_label.configure(text=f"Failed to load playlists: {message}")

    def _populate_playlists(self, playlists):
        self.loading_label.pack_forget()
        self.playlist_data = playlists
        self.checkbox_vars.clear()

        for pl in playlists:
            var = customtkinter.StringVar(value="off")
            self.checkbox_vars.append(var)

            row = customtkinter.CTkFrame(
                self.scroll_frame, fg_color=DARK_GRAY, height=50, corner_radius=6,
            )
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            cb = customtkinter.CTkCheckBox(
                row, text="", variable=var,
                onvalue="on", offvalue="off",
                fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
                checkmark_color=WHITE, width=24,
            )
            cb.pack(side="left", padx=(12, 8), pady=10)

            customtkinter.CTkLabel(
                row, text=pl["name"], font=FONT_BODY,
                text_color=WHITE, anchor="w",
            ).pack(side="left", fill="x", expand=True, pady=10)

            customtkinter.CTkLabel(
                row, text=f"{pl['track_count']} tracks",
                font=FONT_SMALL, text_color=LIGHT_GRAY,
            ).pack(side="right", padx=15, pady=10)

    def _select_all(self):
        for var in self.checkbox_vars:
            var.set("on")

    def _deselect_all(self):
        for var in self.checkbox_vars:
            var.set("off")

    def _on_load_artists(self):
        selected_ids = []
        selected_names = []
        for i, var in enumerate(self.checkbox_vars):
            if var.get() == "on":
                selected_ids.append(self.playlist_data[i]["id"])
                selected_names.append(self.playlist_data[i]["name"])

        if not selected_ids:
            self.error_label.configure(text="Select at least one playlist")
            return

        self.error_label.configure(text="")
        self.app.show_artist_screen(selected_ids, selected_names)
