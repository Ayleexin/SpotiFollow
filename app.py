import customtkinter
from config import BG_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT
from spotify_client import SpotifyClient
from image_cache import ImageCache


class SpotiFollowApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpotiFollow")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(fg_color=BG_COLOR)
        self.minsize(800, 600)

        # Shared state
        self.client = SpotifyClient()
        self.image_cache = ImageCache()

        # Container
        self.container = customtkinter.CTkFrame(self, fg_color=BG_COLOR)
        self.container.pack(fill="both", expand=True)

        self._current_frame = None
        self.show_auth_screen()

    def _clear_screen(self):
        if self._current_frame is not None:
            self._current_frame.destroy()
            self._current_frame = None

    def show_auth_screen(self):
        from auth import AuthFrame
        self._clear_screen()
        self._current_frame = AuthFrame(self.container, self)
        self._current_frame.pack(fill="both", expand=True)

    def show_playlist_screen(self, username):
        from playlists import PlaylistFrame
        self._clear_screen()
        self._current_frame = PlaylistFrame(self.container, self, username)
        self._current_frame.pack(fill="both", expand=True)

    def show_artist_screen(self, playlist_ids, playlist_names):
        from artists import ArtistFrame
        self._clear_screen()
        self._current_frame = ArtistFrame(
            self.container, self, playlist_ids, playlist_names
        )
        self._current_frame.pack(fill="both", expand=True)
