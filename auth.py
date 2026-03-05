import threading
import customtkinter
from config import (
    BG_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER,
    WHITE, LIGHT_GRAY, ERROR_RED, DARK_GRAY,
    FONT_TITLE, FONT_BODY, FONT_SMALL,
)


class AuthFrame(customtkinter.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=BG_COLOR)
        self.app = app

        # Centered inner container
        inner = customtkinter.CTkFrame(self, fg_color=BG_COLOR)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        customtkinter.CTkLabel(
            inner, text="SpotiFollow", font=FONT_TITLE,
            text_color=SPOTIFY_GREEN,
        ).pack(pady=(0, 5))

        # Subtitle
        customtkinter.CTkLabel(
            inner, text="Connect your Spotify account",
            font=FONT_SMALL, text_color=LIGHT_GRAY,
        ).pack(pady=(0, 30))

        # Client ID
        customtkinter.CTkLabel(
            inner, text="Client ID", font=FONT_SMALL,
            text_color=WHITE, anchor="w",
        ).pack(fill="x", padx=5)
        self.client_id_entry = customtkinter.CTkEntry(
            inner, width=350, height=38, fg_color=DARK_GRAY,
            border_color=DARK_GRAY, text_color=WHITE,
            placeholder_text="Enter your Spotify Client ID",
        )
        self.client_id_entry.pack(pady=(2, 15))

        # Client Secret
        customtkinter.CTkLabel(
            inner, text="Client Secret", font=FONT_SMALL,
            text_color=WHITE, anchor="w",
        ).pack(fill="x", padx=5)
        self.client_secret_entry = customtkinter.CTkEntry(
            inner, width=350, height=38, fg_color=DARK_GRAY,
            border_color=DARK_GRAY, text_color=WHITE, show="*",
            placeholder_text="Enter your Spotify Client Secret",
        )
        self.client_secret_entry.pack(pady=(2, 25))

        # Connect button
        self.connect_btn = customtkinter.CTkButton(
            inner, text="Connect", width=350, height=42,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=WHITE, font=FONT_BODY,
            command=self._on_connect,
        )
        self.connect_btn.pack(pady=(0, 15))

        # Error label
        self.error_label = customtkinter.CTkLabel(
            inner, text="", font=FONT_SMALL,
            text_color=ERROR_RED, wraplength=340,
        )
        self.error_label.pack()

    def _on_connect(self):
        client_id = self.client_id_entry.get().strip()
        client_secret = self.client_secret_entry.get().strip()

        if not client_id or not client_secret:
            self.error_label.configure(text="Please fill in both fields")
            return

        self.connect_btn.configure(state="disabled", text="Connecting...")
        self.error_label.configure(text="")

        thread = threading.Thread(
            target=self._authenticate_bg,
            args=(client_id, client_secret),
            daemon=True,
        )
        thread.start()

    def _authenticate_bg(self, client_id, client_secret):
        try:
            username = self.app.client.authenticate(client_id, client_secret)
            self.after(0, lambda: self.app.show_playlist_screen(username))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._on_auth_error(msg))

    def _on_auth_error(self, message):
        self.connect_btn.configure(state="normal", text="Connect")
        self.error_label.configure(text=f"Authentication failed: {message}")
