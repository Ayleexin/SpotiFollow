import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import REDIRECT_URI, SCOPE, BATCH_SIZE


class SpotifyClient:
    def __init__(self):
        self.sp = None

    def authenticate(self, client_id, client_secret):
        """Authenticate with Spotify. Opens browser for OAuth. Returns display name."""
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        user = self.sp.current_user()
        return user["display_name"] or user["id"]

    def get_playlists(self):
        """Fetch all user playlists. Returns list of dicts with id, name, track_count, image_url."""
        playlists = []
        results = self.sp.current_user_playlists(limit=50)
        while True:
            for item in results["items"]:
                image_url = item["images"][0]["url"] if item.get("images") else None
                playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "track_count": item["tracks"]["total"],
                    "image_url": image_url,
                })
            if results["next"]:
                results = self.sp.next(results)
            else:
                break
        return playlists

    def get_artists_from_playlists(self, playlist_ids, progress_callback=None):
        """
        Fetch all unique artists from the given playlists.
        Returns dict: {artist_id: {name, image_url, is_primary}}
        """
        artist_map = {}

        for playlist_id in playlist_ids:
            results = self.sp.playlist_tracks(playlist_id)
            tracks = results["items"]
            while results["next"]:
                results = self.sp.next(results)
                tracks.extend(results["items"])

            if progress_callback:
                progress_callback(f"Processing {len(tracks)} tracks...")

            for item in tracks:
                track = item.get("track")
                if not track or not track.get("artists"):
                    continue
                for i, artist in enumerate(track["artists"]):
                    aid = artist.get("id")
                    if aid is None:
                        continue
                    if aid not in artist_map:
                        artist_map[aid] = {
                            "name": artist["name"],
                            "is_primary": i == 0,
                        }
                    elif i == 0 and not artist_map[aid]["is_primary"]:
                        artist_map[aid]["is_primary"] = True

        # Fetch full artist metadata (images) in batches of 20
        # (sp.artists() can hit URI length limits with larger batches)
        METADATA_BATCH = 20
        artist_ids = list(artist_map.keys())
        for i in range(0, len(artist_ids), METADATA_BATCH):
            batch = artist_ids[i : i + METADATA_BATCH]
            try:
                full_artists = self.sp.artists(batch)
                for fa in full_artists["artists"]:
                    if fa and fa["id"] in artist_map:
                        images = fa.get("images", [])
                        image_url = None
                        if images:
                            suitable = [img for img in images if img.get("width", 0) >= 64]
                            if suitable:
                                image_url = suitable[-1]["url"]
                            else:
                                image_url = images[0]["url"]
                        artist_map[fa["id"]]["image_url"] = image_url
            except Exception:
                for aid in batch:
                    if "image_url" not in artist_map.get(aid, {}):
                        artist_map[aid]["image_url"] = None

        for aid in artist_map:
            if "image_url" not in artist_map[aid]:
                artist_map[aid]["image_url"] = None

        return artist_map

    def check_follow_status(self, artist_ids):
        """Check follow status for a list of artist IDs. Returns {id: bool}."""
        status = {}
        ids = list(artist_ids)
        for i in range(0, len(ids), BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            results = self.sp.current_user_following_artists(batch)
            for j, is_followed in enumerate(results):
                status[batch[j]] = is_followed
        return status

    def follow_artists(self, artist_ids, progress_callback=None):
        """Follow artists in batches. Calls progress_callback(completed, total) after each batch."""
        ids = list(artist_ids)
        total = len(ids)
        completed = 0
        for i in range(0, total, BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            self.sp.user_follow_artists(batch)
            completed += len(batch)
            if progress_callback:
                progress_callback(completed, total)
        return total

    def unfollow_artists(self, artist_ids, progress_callback=None):
        """Unfollow artists in batches. Calls progress_callback(completed, total) after each batch."""
        ids = list(artist_ids)
        total = len(ids)
        completed = 0
        for i in range(0, total, BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            self.sp.user_unfollow_artists(batch)
            completed += len(batch)
            if progress_callback:
                progress_callback(completed, total)
        return total
