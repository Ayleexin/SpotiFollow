import threading
import customtkinter
from config import (
    BG_COLOR, FRAME_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER,
    WHITE, LIGHT_GRAY, DARK_GRAY, ERROR_RED,
    FONT_HEADING, FONT_BODY, FONT_SMALL,
)

ITEMS_PER_PAGE = 300


class ArtistFrame(customtkinter.CTkFrame):
    def __init__(self, master, app, playlist_ids, playlist_names):
        super().__init__(master, fg_color=BG_COLOR)
        self.app = app
        self.playlist_ids = playlist_ids
        self.playlist_names = playlist_names

        # Data
        self.all_artists = {}       # artist_id -> {name, image_url, is_primary}
        self.follow_status = {}     # artist_id -> bool
        self.checkbox_vars = {}     # artist_id -> StringVar
        self.artist_rows = {}       # artist_id -> dict of widgets

        # Filter & pagination state
        self.show_featured = True
        self.search_text = ""
        self._search_timer = None
        self._current_page = 0
        self._sorted_visible = []

        self._build_ui()
        self._start_loading()

    def _build_ui(self):
        # === Header ===
        header = customtkinter.CTkFrame(self, fg_color=FRAME_COLOR, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        back_btn = customtkinter.CTkButton(
            header, text="< Back", width=80, height=32,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=lambda: self.app.show_playlist_screen(self._get_username()),
        )
        back_btn.pack(side="left", padx=15, pady=14)

        title_text = ", ".join(self.playlist_names)
        if len(title_text) > 60:
            title_text = title_text[:57] + "..."
        customtkinter.CTkLabel(
            header, text=f"Artists from: {title_text}",
            font=FONT_BODY, text_color=WHITE,
        ).pack(side="left", padx=10, pady=14)

        # === Toolbar ===
        toolbar = customtkinter.CTkFrame(self, fg_color=BG_COLOR)
        toolbar.pack(fill="x", padx=20, pady=(10, 5))

        # Search
        self.search_entry = customtkinter.CTkEntry(
            toolbar, width=250, height=32, fg_color=DARK_GRAY,
            border_color=DARK_GRAY, text_color=WHITE,
            placeholder_text="Search artists...",
        )
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Featured toggle
        self.featured_switch = customtkinter.CTkSwitch(
            toolbar, text="Show Featured",
            font=FONT_SMALL, text_color=LIGHT_GRAY,
            fg_color=DARK_GRAY, progress_color=SPOTIFY_GREEN,
            button_color=WHITE, button_hover_color=LIGHT_GRAY,
            command=self._on_featured_toggle,
        )
        self.featured_switch.select()
        self.featured_switch.pack(side="left", padx=(0, 15))

        # Select All / Deselect All
        customtkinter.CTkButton(
            toolbar, text="Select All", width=90, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._select_all,
        ).pack(side="left", padx=(0, 5))

        customtkinter.CTkButton(
            toolbar, text="Deselect All", width=90, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._deselect_all,
        ).pack(side="left", padx=(0, 15))

        # Counter
        self.counter_label = customtkinter.CTkLabel(
            toolbar, text="0 of 0 selected",
            font=FONT_SMALL, text_color=LIGHT_GRAY,
        )
        self.counter_label.pack(side="right")

        # === Scrollable artist list ===
        self.scroll_frame = customtkinter.CTkScrollableFrame(
            self, fg_color=BG_COLOR,
            scrollbar_button_color=DARK_GRAY,
            scrollbar_button_hover_color="#3a3a3a",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Loading label (inside scroll area)
        self.loading_label = customtkinter.CTkLabel(
            self.scroll_frame, text="", font=FONT_BODY, text_color=LIGHT_GRAY,
        )

        # === Pagination bar ===
        self.page_bar = customtkinter.CTkFrame(self, fg_color=BG_COLOR, height=40)
        self.page_bar.pack(fill="x", padx=20, pady=(5, 0))

        self.prev_btn = customtkinter.CTkButton(
            self.page_bar, text="< Prev", width=80, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._prev_page,
        )
        self.prev_btn.pack(side="left", padx=(0, 10))

        self.page_label = customtkinter.CTkLabel(
            self.page_bar, text="Page 1 of 1",
            font=FONT_SMALL, text_color=LIGHT_GRAY,
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = customtkinter.CTkButton(
            self.page_bar, text="Next >", width=80, height=28,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_SMALL,
            command=self._next_page,
        )
        self.next_btn.pack(side="right", padx=(10, 0))

        # === Action bar ===
        action_bar = customtkinter.CTkFrame(self, fg_color=FRAME_COLOR, height=70)
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        # Progress bar
        self.progress_bar = customtkinter.CTkProgressBar(
            action_bar, progress_color=SPOTIFY_GREEN, height=6,
            fg_color=DARK_GRAY,
        )
        self.progress_bar.set(0)

        # Status label
        self.status_label = customtkinter.CTkLabel(
            action_bar, text="", font=FONT_SMALL, text_color=SPOTIFY_GREEN,
        )
        self.status_label.pack(side="top", pady=(8, 0))

        btn_frame = customtkinter.CTkFrame(action_bar, fg_color=FRAME_COLOR)
        btn_frame.pack(side="bottom", pady=(0, 12))

        self.follow_btn = customtkinter.CTkButton(
            btn_frame, text="Follow Selected", width=160, height=36,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=WHITE, font=FONT_BODY,
            command=self._on_follow,
        )
        self.follow_btn.pack(side="left", padx=8)

        self.unfollow_btn = customtkinter.CTkButton(
            btn_frame, text="Unfollow Selected", width=160, height=36,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=ERROR_RED, font=FONT_BODY,
            command=self._on_unfollow,
        )
        self.unfollow_btn.pack(side="left", padx=8)

    def _get_username(self):
        try:
            user = self.app.client.sp.current_user()
            return user.get("display_name") or user.get("id", "User")
        except Exception:
            return "User"

    # === Loading ===

    def _start_loading(self):
        self.loading_label.configure(text="Scanning playlists for artists...")
        self.loading_label.pack(pady=30)
        thread = threading.Thread(target=self._load_artists_bg, daemon=True)
        thread.start()

    def _load_artists_bg(self):
        try:
            artists = self.app.client.get_artists_from_playlists(
                self.playlist_ids,
                progress_callback=lambda msg: self.after(
                    0, lambda m=msg: self.loading_label.configure(text=m)
                ),
            )
            self.after(0, lambda: self._on_artists_loaded(artists))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self.loading_label.configure(
                text=f"Error loading artists: {msg}"
            ))

    def _on_artists_loaded(self, artists):
        self.all_artists = artists
        self.loading_label.configure(text="Checking follow status...")
        thread = threading.Thread(target=self._check_follow_bg, daemon=True)
        thread.start()

    def _check_follow_bg(self):
        try:
            ids = list(self.all_artists.keys())
            status = self.app.client.check_follow_status(ids)
            self.after(0, lambda: self._on_follow_status_loaded(status))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self.loading_label.configure(
                text=f"Error checking follow status: {msg}"
            ))

    def _on_follow_status_loaded(self, status):
        self.follow_status = status
        self.loading_label.pack_forget()
        self._current_page = 0
        self._refresh_list()

    # === Rendering ===

    def _get_filtered_artists(self):
        result = {}
        for aid, artist in self.all_artists.items():
            if not self.show_featured and not artist.get("is_primary", True):
                continue
            if self.search_text and self.search_text.lower() not in artist["name"].lower():
                continue
            result[aid] = artist
        return result

    def _total_pages(self):
        count = len(self._sorted_visible)
        if count == 0:
            return 1
        return (count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    def _refresh_list(self):
        """Recompute filtered/sorted list and render current page."""
        visible = self._get_filtered_artists()
        self._sorted_visible = sorted(visible.items(), key=lambda x: x[1]["name"].lower())

        # Clamp page
        max_page = self._total_pages() - 1
        if self._current_page > max_page:
            self._current_page = max_page
        if self._current_page < 0:
            self._current_page = 0

        self._render_page()
        self._update_counter()
        self._update_page_controls()

    def _render_page(self):
        """Render only the current page of artists."""
        # Clear existing rows
        for widget in self.scroll_frame.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        self.artist_rows.clear()

        start = self._current_page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(self._sorted_visible))
        page_items = self._sorted_visible[start:end]

        placeholder = self.app.image_cache.get_placeholder()

        for aid, artist in page_items:
            if aid not in self.checkbox_vars:
                self.checkbox_vars[aid] = customtkinter.StringVar(value="off")
            var = self.checkbox_vars[aid]

            row = customtkinter.CTkFrame(
                self.scroll_frame, fg_color=DARK_GRAY, corner_radius=6,
            )
            row.pack(fill="x", pady=2)

            # Checkbox
            cb = customtkinter.CTkCheckBox(
                row, text="", variable=var,
                onvalue="on", offvalue="off",
                fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
                checkmark_color=WHITE, width=24,
                command=self._update_counter,
            )
            cb.pack(side="left", padx=(12, 8), pady=10)

            # Artist image
            img_label = customtkinter.CTkLabel(row, image=placeholder, text="")
            img_label.pack(side="left", padx=(0, 10), pady=5)

            # Load real image async
            if artist.get("image_url"):
                url = artist["image_url"]
                self.app.image_cache.get_image(
                    url,
                    callback=lambda img, lbl=img_label: self.after(
                        0, lambda: lbl.configure(image=img)
                    ),
                )

            # Artist name
            name_label = customtkinter.CTkLabel(
                row, text=artist["name"], font=FONT_BODY,
                text_color=WHITE, anchor="w",
            )
            name_label.pack(side="left", fill="x", expand=True, pady=10)

            # Featured tag
            if not artist.get("is_primary", True):
                customtkinter.CTkLabel(
                    row, text="feat.", font=FONT_SMALL,
                    text_color=LIGHT_GRAY,
                ).pack(side="right", padx=(0, 5), pady=10)

            # Follow indicator
            is_followed = self.follow_status.get(aid, False)
            indicator = customtkinter.CTkLabel(
                row,
                text="\u2714" if is_followed else "",
                text_color=SPOTIFY_GREEN if is_followed else BG_COLOR,
                font=FONT_BODY, width=30,
            )
            indicator.pack(side="right", padx=10, pady=10)

            self.artist_rows[aid] = {
                "frame": row,
                "checkbox": cb,
                "image_label": img_label,
                "name_label": name_label,
                "follow_indicator": indicator,
            }

    def _update_page_controls(self):
        total = self._total_pages()
        current = self._current_page + 1
        self.page_label.configure(text=f"Page {current} of {total}")
        self.prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total - 1 else "disabled")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()
            self._update_page_controls()
            # Scroll to top
            self.scroll_frame._parent_canvas.yview_moveto(0)

    def _next_page(self):
        if self._current_page < self._total_pages() - 1:
            self._current_page += 1
            self._render_page()
            self._update_page_controls()
            # Scroll to top
            self.scroll_frame._parent_canvas.yview_moveto(0)

    # === Filtering ===

    def _on_search_changed(self, event=None):
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._apply_search)

    def _apply_search(self):
        self.search_text = self.search_entry.get().strip()
        self._current_page = 0
        self._refresh_list()

    def _on_featured_toggle(self):
        self.show_featured = self.featured_switch.get() == 1
        self._current_page = 0
        self._refresh_list()

    # === Selection ===

    def _select_all(self):
        """Select all artists across ALL pages (not just current)."""
        visible = self._get_filtered_artists()
        for aid in visible:
            if aid not in self.checkbox_vars:
                self.checkbox_vars[aid] = customtkinter.StringVar(value="on")
            else:
                self.checkbox_vars[aid].set("on")
        self._update_counter()

    def _deselect_all(self):
        """Deselect all artists across ALL pages."""
        visible = self._get_filtered_artists()
        for aid in visible:
            if aid in self.checkbox_vars:
                self.checkbox_vars[aid].set("off")
        self._update_counter()

    def _update_counter(self):
        visible = self._get_filtered_artists()
        selected = sum(
            1 for aid in visible
            if self.checkbox_vars.get(aid) and self.checkbox_vars[aid].get() == "on"
        )
        total = len(visible)
        self.counter_label.configure(text=f"{selected} of {total} selected")

    # === Follow / Unfollow ===

    def _get_selected_ids(self):
        return [
            aid for aid, var in self.checkbox_vars.items()
            if var.get() == "on"
        ]

    def _set_action_state(self, enabled):
        state = "normal" if enabled else "disabled"
        self.follow_btn.configure(state=state)
        self.unfollow_btn.configure(state=state)

    def _on_follow(self):
        selected = self._get_selected_ids()
        to_follow = [aid for aid in selected if not self.follow_status.get(aid, False)]
        if not to_follow:
            self.status_label.configure(
                text="All selected artists are already followed",
                text_color=LIGHT_GRAY,
            )
            return

        self._show_follow_confirm(to_follow)

    def _show_follow_confirm(self, artist_ids):
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Confirm Follow")
        dialog.geometry("420x180")
        dialog.configure(fg_color=FRAME_COLOR)
        dialog.grab_set()
        dialog.transient(self.winfo_toplevel())
        dialog.after(10, lambda: dialog.focus_force())

        customtkinter.CTkLabel(
            dialog,
            text=f"Are you sure you want to follow\n{len(artist_ids)} artist(s)?",
            font=FONT_BODY, text_color=WHITE, justify="center",
        ).pack(pady=(30, 20))

        btn_frame = customtkinter.CTkFrame(dialog, fg_color=FRAME_COLOR)
        btn_frame.pack(pady=10)

        customtkinter.CTkButton(
            btn_frame, text="Cancel", width=120, height=34,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_BODY,
            command=dialog.destroy,
        ).pack(side="left", padx=10)

        customtkinter.CTkButton(
            btn_frame, text="Follow", width=120, height=34,
            fg_color=SPOTIFY_GREEN, hover_color=SPOTIFY_GREEN_HOVER,
            text_color=WHITE, font=FONT_BODY,
            command=lambda: self._do_follow(artist_ids, dialog),
        ).pack(side="left", padx=10)

    def _do_follow(self, artist_ids, dialog):
        dialog.destroy()
        self._set_action_state(False)
        self.status_label.configure(text="", text_color=SPOTIFY_GREEN)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 0), before=self.status_label)

        thread = threading.Thread(
            target=self._follow_bg, args=(artist_ids,), daemon=True
        )
        thread.start()

    def _follow_bg(self, artist_ids):
        def on_progress(completed, total):
            self.after(0, lambda: self.progress_bar.set(completed / total))

        try:
            count = self.app.client.follow_artists(artist_ids, progress_callback=on_progress)
            self.after(0, lambda: self._on_action_complete(f"Followed {count} artist(s)"))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._on_action_error(msg))

    def _on_unfollow(self):
        selected = self._get_selected_ids()
        to_unfollow = [aid for aid in selected if self.follow_status.get(aid, False)]
        if not to_unfollow:
            self.status_label.configure(
                text="None of the selected artists are currently followed",
                text_color=LIGHT_GRAY,
            )
            return

        self._show_unfollow_confirm(to_unfollow)

    def _show_unfollow_confirm(self, artist_ids):
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Confirm Unfollow")
        dialog.geometry("420x180")
        dialog.configure(fg_color=FRAME_COLOR)
        dialog.grab_set()
        dialog.transient(self.winfo_toplevel())
        dialog.after(10, lambda: dialog.focus_force())

        customtkinter.CTkLabel(
            dialog,
            text=f"Are you sure you want to unfollow\n{len(artist_ids)} artist(s)?",
            font=FONT_BODY, text_color=WHITE, justify="center",
        ).pack(pady=(30, 20))

        btn_frame = customtkinter.CTkFrame(dialog, fg_color=FRAME_COLOR)
        btn_frame.pack(pady=10)

        customtkinter.CTkButton(
            btn_frame, text="Cancel", width=120, height=34,
            fg_color=DARK_GRAY, hover_color="#3a3a3a",
            text_color=WHITE, font=FONT_BODY,
            command=dialog.destroy,
        ).pack(side="left", padx=10)

        customtkinter.CTkButton(
            btn_frame, text="Unfollow", width=120, height=34,
            fg_color=ERROR_RED, hover_color="#cc3333",
            text_color=WHITE, font=FONT_BODY,
            command=lambda: self._do_unfollow(artist_ids, dialog),
        ).pack(side="left", padx=10)

    def _do_unfollow(self, artist_ids, dialog):
        dialog.destroy()
        self._set_action_state(False)
        self.status_label.configure(text="", text_color=SPOTIFY_GREEN)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 0), before=self.status_label)

        thread = threading.Thread(
            target=self._unfollow_bg, args=(artist_ids,), daemon=True
        )
        thread.start()

    def _unfollow_bg(self, artist_ids):
        def on_progress(completed, total):
            self.after(0, lambda: self.progress_bar.set(completed / total))

        try:
            count = self.app.client.unfollow_artists(artist_ids, progress_callback=on_progress)
            self.after(0, lambda: self._on_action_complete(f"Unfollowed {count} artist(s)"))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._on_action_error(msg))

    def _on_action_complete(self, message):
        self.progress_bar.pack_forget()
        self._set_action_state(True)
        self.status_label.configure(text=message, text_color=SPOTIFY_GREEN)

        # Refresh follow status
        thread = threading.Thread(target=self._check_follow_bg, daemon=True)
        thread.start()

    def _on_action_error(self, message):
        self.progress_bar.pack_forget()
        self._set_action_state(True)
        self.status_label.configure(text=f"Error: {message}", text_color=ERROR_RED)
