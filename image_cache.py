import io
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from PIL import Image, ImageDraw
import customtkinter
from config import ARTIST_IMAGE_SIZE, DARK_GRAY


class ImageCache:
    def __init__(self, size=None, max_workers=8):
        self._size = size or ARTIST_IMAGE_SIZE
        self._cache = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._placeholder = None

    def get_placeholder(self):
        """Returns a gray circle placeholder CTkImage."""
        if self._placeholder is None:
            img = Image.new("RGBA", self._size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([0, 0, self._size[0] - 1, self._size[1] - 1], fill=DARK_GRAY)
            self._placeholder = customtkinter.CTkImage(
                light_image=img, dark_image=img, size=self._size
            )
        return self._placeholder

    def get_image(self, url, callback):
        """
        Get an image by URL. If cached, calls callback immediately.
        Otherwise starts async download and calls callback(ctk_image) when done.
        callback will be called from a worker thread — caller must use .after()
        to update widgets.
        """
        if url is None:
            return

        with self._lock:
            if url in self._cache:
                callback(self._cache[url])
                return

        self._executor.submit(self._download_and_cache, url, callback)

    def _download_and_cache(self, url, callback):
        try:
            raw = urlopen(url, timeout=10).read()
            pil_img = Image.open(io.BytesIO(raw))
            pil_img = pil_img.resize(self._size, Image.LANCZOS)
            ctk_img = customtkinter.CTkImage(
                light_image=pil_img, dark_image=pil_img, size=self._size
            )
            with self._lock:
                self._cache[url] = ctk_img
            callback(ctk_img)
        except Exception:
            pass  # Keep placeholder on failure
