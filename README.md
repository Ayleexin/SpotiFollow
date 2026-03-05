# SpotiFollow

A desktop app to bulk follow (or unfollow) Spotify artists from your playlists.

![Python](https://img.shields.io/badge/Python-3.10+-green) ![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Spotify OAuth** — connect with your Client ID & Secret
- **Playlist browser** — view all your playlists with track counts, select one or multiple
- **Artist list** — see every artist from selected playlists with profile pictures
- **Already-followed indicators** — green checkmarks show which artists you already follow
- **Primary vs featured artists** — toggle to show/hide featured (non-primary) artists
- **Search & filter** — quickly find artists by name
- **Select all / deselect all** — works across all pages
- **Bulk follow & unfollow** — with progress bar and confirmation dialogs
- **Pagination** — handles playlists with hundreds of artists smoothly
- **Dark theme** — Spotify-inspired black & green UI

## Setup

### 1. Get Spotify API credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app (or use an existing one)
3. Add `http://127.0.0.1:8888/callback` as a **Redirect URI** in your app settings
4. Note your **Client ID** and **Client Secret**

### 2. Install & run

```bash
git clone https://github.com/Ayleexin/SpotiFollow.git
cd SpotiFollow
pip install -r requirements.txt
python main.py
```

Or on Windows, just double-click `run.bat`.

## Usage

1. Enter your **Client ID** and **Client Secret**, click **Connect**
2. Authorize in the browser window that opens
3. Select one or more playlists, click **Load Artists**
4. Browse artists — use search, toggle featured artists, select/deselect as needed
5. Click **Follow Selected** or **Unfollow Selected**

## Tech Stack

- **CustomTkinter** — modern dark-themed GUI
- **spotipy** — Spotify Web API wrapper
- **Pillow** — artist thumbnail processing
