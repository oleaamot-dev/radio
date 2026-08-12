#!/usr/bin/env python3
"""
GNOME Radio – objektorientert Python-implementasjon
=====================================================

Bygget med GTK4 og PyGObject, i samme ånd som resten av
Aamot Innovation sine GNOME-verktøy (GTK4/Python-stilen brukt
i GNOME Noark5 Client og GNOME Photo Companion).

Arkitektur:
    Station          – dataklasse som representerer én radiostasjon
    StationLibrary    – innlasting, lagring og søk i stasjonslisten
    RadioPlayer       – innkapsler GStreamer-avspilling (playbin)
    RadioWindow       – GTK4-vinduet (View), lytter på RadioPlayer-signaler
    RadioApplication  – Gtk.Application, kobler alt sammen

Kjør med:
    python3 gnome_radio_oop.py

Avhengigheter (Debian/Ubuntu):
    sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-gstreamer-1.0 \
                      gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                      gstreamer1.0-plugins-ugly gstreamer1.0-libav
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Adw, Gst, GLib, Gio, GObject  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("gnome-radio")

APP_ID = "com.aamotinnovation.GnomeRadio"
CONFIG_DIR = Path.home() / ".config" / "gnome-radio"
STATIONS_FILE = CONFIG_DIR / "stations.json"


# ---------------------------------------------------------------------------
# Domenemodell
# ---------------------------------------------------------------------------

@dataclass
class Station:
    """Representerer én radiostasjon."""

    name: str
    url: str
    genre: str = "Ukjent"
    country: str = "Norge"
    favorite: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Station":
        return Station(
            name=data.get("name", "Ukjent stasjon"),
            url=data["url"],
            genre=data.get("genre", "Ukjent"),
            country=data.get("country", "Norge"),
            favorite=data.get("favorite", False),
        )


class PlaybackState(Enum):
    STOPPED = auto()
    BUFFERING = auto()
    PLAYING = auto()
    PAUSED = auto()
    ERROR = auto()


# ---------------------------------------------------------------------------
# Stasjonsbibliotek
# ---------------------------------------------------------------------------

class StationLibrary:
    """Holder styr på alle kjente stasjoner: innlasting, lagring, søk."""

    DEFAULT_STATIONS = [
        Station("NRK P1", "https://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h",
                genre="Allmennradio"),
        Station("NRK P2", "https://lyd.nrk.no/nrk_radio_p2_mp3_h", genre="Kultur"),
        Station("NRK P3", "https://lyd.nrk.no/nrk_radio_p3_mp3_h", genre="Musikk"),
        Station("Radio Norge", "https://http-live.sr.se/p3-mp3-192",
                genre="Musikk", country="Norge"),
        Station("NRK Klassisk", "https://lyd.nrk.no/nrk_radio_klassisk_mp3_h",
                genre="Klassisk"),
    ]

    def __init__(self, storage_path: Path = STATIONS_FILE) -> None:
        self._storage_path = storage_path
        self._stations: list[Station] = []
        self.load()

    # -- persistens ---------------------------------------------------

    def load(self) -> None:
        if self._storage_path.exists():
            try:
                raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
                self._stations = [Station.from_dict(s) for s in raw]
                logger.info("Lastet %d stasjoner fra %s", len(self._stations),
                            self._storage_path)
                return
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                logger.warning("Kunne ikke lese stasjonsfil (%s), bruker standard", exc)
        self._stations = list(self.DEFAULT_STATIONS)

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = [s.to_dict() for s in self._stations]
        self._storage_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                       encoding="utf-8")

    # -- CRUD -----------------------------------------------------------

    def add(self, station: Station) -> None:
        self._stations.append(station)
        self.save()

    def remove(self, station: Station) -> None:
        self._stations = [s for s in self._stations if s.url != station.url]
        self.save()

    def toggle_favorite(self, station: Station) -> None:
        station.favorite = not station.favorite
        self.save()

    def all(self) -> list[Station]:
        return list(self._stations)

    def favorites(self) -> list[Station]:
        return [s for s in self._stations if s.favorite]

    def search(self, query: str) -> list[Station]:
        q = query.strip().lower()
        if not q:
            return self.all()
        return [
            s for s in self._stations
            if q in s.name.lower() or q in s.genre.lower() or q in s.country.lower()
        ]


# ---------------------------------------------------------------------------
# Avspiller (GStreamer-innkapsling)
# ---------------------------------------------------------------------------

class RadioPlayer(GObject.Object):
    """
    Innkapsler en GStreamer 'playbin' for strømmeavspilling.

    Emitterer GObject-signaler slik at UI-laget (RadioWindow) kan
    reagere på tilstandsendringer uten å kjenne til GStreamer.
    """

    __gsignals__ = {
        "state-changed": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "station-changed": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        "error": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        Gst.init(None)
        self._playbin = Gst.ElementFactory.make("playbin", "player")
        if self._playbin is None:
            raise RuntimeError("Klarte ikke å opprette GStreamer 'playbin'-element")

        self._current_station: Optional[Station] = None
        self._state = PlaybackState.STOPPED
        self._volume = 1.0

        bus = self._playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_bus_error)
        bus.connect("message::buffering", self._on_bus_buffering)
        bus.connect("message::state-changed", self._on_bus_state_changed)

    # -- offentlig API ----------------------------------------------------

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def current_station(self) -> Optional[Station]:
        return self._current_station

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        self._playbin.set_property("volume", self._volume)

    def play(self, station: Station) -> None:
        self._current_station = station
        self._playbin.set_state(Gst.State.NULL)
        self._playbin.set_property("uri", station.url)
        self._playbin.set_property("volume", self._volume)
        self._playbin.set_state(Gst.State.PLAYING)
        self._set_state(PlaybackState.BUFFERING)
        self.emit("station-changed", station)

    def stop(self) -> None:
        self._playbin.set_state(Gst.State.NULL)
        self._set_state(PlaybackState.STOPPED)

    def toggle_pause(self) -> None:
        if self._state == PlaybackState.PLAYING:
            self._playbin.set_state(Gst.State.PAUSED)
            self._set_state(PlaybackState.PAUSED)
        elif self._state in (PlaybackState.PAUSED, PlaybackState.STOPPED):
            self._playbin.set_state(Gst.State.PLAYING)
            self._set_state(PlaybackState.PLAYING)

    # -- interne hjelpere ---------------------------------------------------

    def _set_state(self, new_state: PlaybackState) -> None:
        self._state = new_state
        self.emit("state-changed", new_state)

    def _on_bus_error(self, _bus, message) -> None:
        err, debug = message.parse_error()
        logger.error("GStreamer-feil: %s (%s)", err, debug)
        self._set_state(PlaybackState.ERROR)
        self.emit("error", str(err))
        self._playbin.set_state(Gst.State.NULL)

    def _on_bus_buffering(self, _bus, message) -> None:
        percent = message.parse_buffering()
        if percent < 100:
            self._set_state(PlaybackState.BUFFERING)
        else:
            self._set_state(PlaybackState.PLAYING)

    def _on_bus_state_changed(self, _bus, message) -> None:
        if message.src != self._playbin:
            return
        _old, new, _pending = message.parse_state_changed()
        if new == Gst.State.PLAYING and self._state != PlaybackState.PLAYING:
            self._set_state(PlaybackState.PLAYING)


# ---------------------------------------------------------------------------
# UI-lag
# ---------------------------------------------------------------------------

class StationRow(Gtk.ListBoxRow):
    """Én rad i stasjonslisten. Rent visningsobjekt, ingen forretningslogikk."""

    def __init__(self, station: Station, on_favorite_toggle: Callable[[Station], None]):
        super().__init__()
        self.station = station

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                      margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        name_label = Gtk.Label(label=station.name, xalign=0)
        name_label.add_css_class("title-4")
        meta_label = Gtk.Label(label=f"{station.genre} · {station.country}", xalign=0)
        meta_label.add_css_class("dim-label")
        text_box.append(name_label)
        text_box.append(meta_label)

        fav_button = Gtk.ToggleButton()
        fav_button.set_icon_name(
            "starred-symbolic" if station.favorite else "non-starred-symbolic"
        )
        fav_button.set_active(station.favorite)
        fav_button.connect("toggled", lambda _b: on_favorite_toggle(station))

        box.append(text_box)
        box.append(fav_button)
        self.set_child(box)


class RadioWindow(Adw.ApplicationWindow):
    """Hovedvinduet. Observerer RadioPlayer og delegerer handlinger til det."""

    def __init__(self, app: "RadioApplication") -> None:
        super().__init__(application=app, title="GNOME Radio")
        self.set_default_size(420, 640)

        self._library = app.library
        self._player = app.player
        self._player.connect("state-changed", self._on_state_changed)
        self._player.connect("station-changed", self._on_station_changed)
        self._player.connect("error", self._on_player_error)

        self._build_ui()
        self._populate_station_list(self._library.all())

    # -- oppbygging av UI ---------------------------------------------------

    def _build_ui(self) -> None:
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        search_entry = Gtk.SearchEntry(placeholder_text="Søk etter stasjon, sjanger …")
        search_entry.connect("search-changed", self._on_search_changed)
        header.set_title_widget(search_entry)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._station_list = Gtk.ListBox()
        self._station_list.add_css_class("boxed-list")
        self._station_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._station_list.connect("row-activated", self._on_row_activated)

        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self._station_list)
        scroller.set_margin_top(8)
        scroller.set_margin_start(8)
        scroller.set_margin_end(8)
        root.append(scroller)

        root.append(self._build_playback_bar())
        toolbar_view.set_content(root)
        self.set_content(toolbar_view)

    def _build_playback_bar(self) -> Gtk.Widget:
        bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                      margin_top=8, margin_bottom=12, margin_start=16, margin_end=16)

        self._now_playing_label = Gtk.Label(label="Ingen stasjon valgt", xalign=0)
        self._now_playing_label.add_css_class("title-3")

        self._status_label = Gtk.Label(label="Stoppet", xalign=0)
        self._status_label.add_css_class("dim-label")

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._play_pause_button = Gtk.Button(icon_name="media-playback-start-symbolic")
        self._play_pause_button.connect("clicked", lambda _b: self._player.toggle_pause())

        stop_button = Gtk.Button(icon_name="media-playback-stop-symbolic")
        stop_button.connect("clicked", lambda _b: self._player.stop())

        volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.05)
        volume_scale.set_value(self._player.volume)
        volume_scale.set_hexpand(True)
        volume_scale.connect("value-changed",
                              lambda s: setattr(self._player, "volume", s.get_value()))

        controls.append(self._play_pause_button)
        controls.append(stop_button)
        controls.append(volume_scale)

        bar.append(self._now_playing_label)
        bar.append(self._status_label)
        bar.append(controls)
        return bar

    # -- stasjonslisten -----------------------------------------------------

    def _populate_station_list(self, stations: list[Station]) -> None:
        child = self._station_list.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self._station_list.remove(child)
            child = next_child

        for station in stations:
            row = StationRow(station, on_favorite_toggle=self._on_favorite_toggle)
            self._station_list.append(row)

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        results = self._library.search(entry.get_text())
        self._populate_station_list(results)

    def _on_row_activated(self, _listbox, row: StationRow) -> None:
        self._player.play(row.station)

    def _on_favorite_toggle(self, station: Station) -> None:
        self._library.toggle_favorite(station)

    # -- reaksjoner på RadioPlayer-signaler ---------------------------------

    def _on_state_changed(self, _player, state: PlaybackState) -> None:
        labels = {
            PlaybackState.STOPPED: "Stoppet",
            PlaybackState.BUFFERING: "Bufrer …",
            PlaybackState.PLAYING: "Spiller av",
            PlaybackState.PAUSED: "Pause",
            PlaybackState.ERROR: "Feil ved avspilling",
        }
        self._status_label.set_label(labels.get(state, ""))
        icon = "media-playback-pause-symbolic" if state == PlaybackState.PLAYING \
            else "media-playback-start-symbolic"
        self._play_pause_button.set_icon_name(icon)

    def _on_station_changed(self, _player, station: Station) -> None:
        self._now_playing_label.set_label(station.name)

    def _on_player_error(self, _player, message: str) -> None:
        toast = Adw.Toast(title=f"Kunne ikke spille av: {message}")
        # Krever Adw.ToastOverlay for full funksjon; her nøyer vi oss med logging.
        logger.error("Avspillingsfeil: %s", message)


# ---------------------------------------------------------------------------
# Applikasjon
# ---------------------------------------------------------------------------

class RadioApplication(Adw.Application):
    """Gtk.Application-underklasse. Eier de langlevde objektene."""

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID,
                          flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.library = StationLibrary()
        self.player = RadioPlayer()
        self._window: Optional[RadioWindow] = None

    def do_activate(self) -> None:  # noqa: N802 (GTK-navnekonvensjon)
        if self._window is None:
            self._window = RadioWindow(self)
        self._window.present()


def main() -> int:
    app = RadioApplication()
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
