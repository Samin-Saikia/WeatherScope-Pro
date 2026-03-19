"""
WeatherScope Pro - Feature-Rich Weather Forecast & Analysis Application
Author: WeatherScope Pro
Python: 3.7.6+  (Windows 7 32-bit compatible)
API:    OpenWeatherMap (https://openweathermap.org/api)

Icons: Pure ASCII text labels -- works on ALL systems including Win7 32-bit.
       No emoji, no Unicode symbols above U+00FF.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
import threading
import json
import os
import csv
import math
import time
import datetime
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict
from typing import Optional, List, Dict, Any, Tuple


# ---------------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------------------------------------------------------

APP_TITLE   = "WeatherScope Pro"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1200x800"
MIN_SIZE    = (900, 650)


# ---------------------------------------------------------------------------
# ASCII ICON SYSTEM
# All icons are short text tags that render on EVERY OS / Python / font.
# No emoji, no Unicode above ASCII range.
# ---------------------------------------------------------------------------

WEATHER_ICONS = {
    "Clear":        "[SUN]",
    "Clouds":       "[CLD]",
    "Rain":         "[RAN]",
    "Drizzle":      "[DRZ]",
    "Thunderstorm": "[STM]",
    "Snow":         "[SNW]",
    "Mist":         "[MST]",
    "Fog":          "[FOG]",
    "Haze":         "[HAZ]",
    "Smoke":        "[SMK]",
    "Dust":         "[DST]",
    "Sand":         "[SND]",
    "Ash":          "[ASH]",
    "Squall":       "[SQL]",
    "Tornado":      "[TRN]",
}

# Section header labels
SEC = {
    "temp":   "[ TEMPERATURE ]",
    "wind":   "[ WIND & ATMOSPHERE ]",
    "precip": "[ PRECIPITATION & HUMIDITY ]",
    "sun":    "[ SUN & SKY ]",
    "summary":"[ FORECAST SUMMARY ]",
}


# ---------------------------------------------------------------------------
# THEME SYSTEM  (Dark + Light)
# ---------------------------------------------------------------------------

DARK_THEME = {
    "bg_dark":   "#0d1117",
    "bg_panel":  "#161b22",
    "bg_card":   "#1c2128",
    "bg_hover":  "#21262d",
    "accent":    "#58a6ff",
    "accent2":   "#3fb950",
    "accent3":   "#f78166",
    "accent4":   "#d29922",
    "text_main": "#e6edf3",
    "text_sub":  "#8b949e",
    "text_dim":  "#484f58",
    "border":    "#30363d",
    "warm":      "#ff7b72",
    "cool":      "#79c0ff",
    "chart_bg":  "#0d1117",
    "name":      "Dark",
}

LIGHT_THEME = {
    "bg_dark":   "#f6f8fa",
    "bg_panel":  "#ffffff",
    "bg_card":   "#eaeef2",
    "bg_hover":  "#dde1e6",
    "accent":    "#0969da",
    "accent2":   "#1a7f37",
    "accent3":   "#cf222e",
    "accent4":   "#9a6700",
    "text_main": "#1f2328",
    "text_sub":  "#656d76",
    "text_dim":  "#afb8c1",
    "border":    "#d0d7de",
    "warm":      "#bc4c00",
    "cool":      "#0550ae",
    "chart_bg":  "#f6f8fa",
    "name":      "Light",
}

# Active theme (mutable dict updated on toggle)
COLORS = dict(DARK_THEME)


def apply_theme(theme):
    COLORS.update(theme)


# ---------------------------------------------------------------------------
# ENV LOADER
# ---------------------------------------------------------------------------

def load_env(filepath=".env"):
    env = {}
    if not os.path.exists(filepath):
        return env
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


ENV     = load_env()
API_KEY = ENV.get("OPENWEATHER_API_KEY", "")

# API Endpoints
BASE_URL     = "https://api.openweathermap.org/data/2.5"
CURRENT_URL  = BASE_URL + "/weather"
FORECAST_URL = BASE_URL + "/forecast"
AIR_URL      = BASE_URL + "/air_pollution"

# Unit labels
UNIT_LABELS = {
    "metric":   {"temp": "C",  "speed": "m/s", "system": "Metric"},
    "imperial": {"temp": "F",  "speed": "mph", "system": "Imperial"},
    "standard": {"temp": "K",  "speed": "m/s", "system": "Kelvin"},
}

HISTORY_FILE   = "weather_history.json"
FAVORITES_FILE = "favorites.json"


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

class WeatherData(object):
    def __init__(self, raw):
        self.raw     = raw
        self.city    = raw.get("name", "Unknown")
        self.country = raw.get("sys", {}).get("country", "")
        coord        = raw.get("coord", {})
        self.lat     = coord.get("lat", 0.0)
        self.lon     = coord.get("lon", 0.0)
        main         = raw.get("main", {})
        self.temp       = main.get("temp", 0)
        self.feels_like = main.get("feels_like", 0)
        self.temp_min   = main.get("temp_min", 0)
        self.temp_max   = main.get("temp_max", 0)
        self.humidity   = main.get("humidity", 0)
        self.pressure   = main.get("pressure", 0)
        weather_list    = raw.get("weather", [{}])
        self.condition   = weather_list[0].get("main", "Unknown")
        self.description = weather_list[0].get("description", "").capitalize()
        self.icon_code   = weather_list[0].get("icon", "01d")
        wind             = raw.get("wind", {})
        self.wind_speed  = wind.get("speed", 0)
        self.wind_deg    = wind.get("deg", 0)
        self.wind_gust   = wind.get("gust", 0)
        self.visibility  = raw.get("visibility", 0) / 1000.0
        self.clouds      = raw.get("clouds", {}).get("all", 0)
        rain             = raw.get("rain", {})
        self.rain_1h     = rain.get("1h", 0)
        snow             = raw.get("snow", {})
        self.snow_1h     = snow.get("1h", 0)
        sys_             = raw.get("sys", {})
        self.sunrise     = sys_.get("sunrise", 0)
        self.sunset      = sys_.get("sunset", 0)
        self.timezone    = raw.get("timezone", 0)
        self.dt          = raw.get("dt", int(time.time()))

    @property
    def icon(self):
        return WEATHER_ICONS.get(self.condition, "[WTH]")

    @property
    def wind_direction(self):
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                "S","SSW","SW","WSW","W","WNW","NW","NNW"]
        return dirs[round(self.wind_deg / 22.5) % 16]

    def local_time(self):
        local_dt = (datetime.datetime.utcfromtimestamp(self.dt)
                    + datetime.timedelta(seconds=self.timezone))
        return local_dt.strftime("%I:%M %p")

    def sunrise_time(self):
        local = (datetime.datetime.utcfromtimestamp(self.sunrise)
                 + datetime.timedelta(seconds=self.timezone))
        return local.strftime("%I:%M %p")

    def sunset_time(self):
        local = (datetime.datetime.utcfromtimestamp(self.sunset)
                 + datetime.timedelta(seconds=self.timezone))
        return local.strftime("%I:%M %p")


class ForecastEntry(object):
    def __init__(self, raw):
        self.dt      = raw.get("dt", 0)
        main         = raw.get("main", {})
        self.temp       = main.get("temp", 0)
        self.feels_like = main.get("feels_like", 0)
        self.temp_min   = main.get("temp_min", 0)
        self.temp_max   = main.get("temp_max", 0)
        self.humidity   = main.get("humidity", 0)
        self.pressure   = main.get("pressure", 0)
        weather_list    = raw.get("weather", [{}])
        self.condition   = weather_list[0].get("main", "Unknown")
        self.description = weather_list[0].get("description", "").capitalize()
        wind             = raw.get("wind", {})
        self.wind_speed  = wind.get("speed", 0)
        self.wind_deg    = wind.get("deg", 0)
        self.clouds      = raw.get("clouds", {}).get("all", 0)
        self.pop         = raw.get("pop", 0) * 100
        self.rain        = raw.get("rain", {}).get("3h", 0)
        self.snow        = raw.get("snow", {}).get("3h", 0)
        self.dt_txt      = raw.get("dt_txt", "")

    @property
    def icon(self):
        return WEATHER_ICONS.get(self.condition, "[WTH]")

    def time_str(self):
        return datetime.datetime.fromtimestamp(self.dt).strftime("%I:%M %p")

    def date_str(self):
        return datetime.datetime.fromtimestamp(self.dt).strftime("%a %b %d")


# ---------------------------------------------------------------------------
# API CLIENT
# ---------------------------------------------------------------------------

class WeatherAPIClient(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def _get(self, url, params):
        params["appid"] = self.api_key
        query    = urllib.parse.urlencode(params)
        full_url = url + "?" + query
        try:
            req = urllib.request.Request(
                full_url, headers={"User-Agent": "WeatherScopePro/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                err = json.loads(body)
                raise ValueError(err.get("message", "HTTP %d" % e.code))
            except (json.JSONDecodeError, ValueError):
                raise ValueError("HTTP Error %d: %s" % (e.code, e.reason))
        except urllib.error.URLError as e:
            raise ConnectionError("Network error: %s" % str(e.reason))
        except Exception as e:
            raise RuntimeError("Unexpected error: %s" % str(e))

    def get_current(self, city, units="metric"):
        return WeatherData(self._get(CURRENT_URL, {"q": city, "units": units}))

    def get_forecast(self, city, units="metric"):
        data = self._get(FORECAST_URL, {"q": city, "units": units, "cnt": 40})
        return [ForecastEntry(item) for item in data.get("list", [])]

    def validate_key(self):
        try:
            self._get(CURRENT_URL, {"q": "London", "units": "metric"})
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# DATA MANAGER
# ---------------------------------------------------------------------------

class DataManager(object):
    def __init__(self):
        self.history   = self._load(HISTORY_FILE, [])
        self.favorites = self._load(FAVORITES_FILE, [])

    def _load(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_history(self, city, weather, units):
        entry = {
            "city":        city,
            "country":     weather.country,
            "temp":        weather.temp,
            "condition":   weather.condition,
            "humidity":    weather.humidity,
            "wind_speed":  weather.wind_speed,
            "units":       units,
            "searched_at": datetime.datetime.now().isoformat(),
        }
        self.history.insert(0, entry)
        if len(self.history) > 100:
            self.history = self.history[:100]
        self._save(HISTORY_FILE, self.history)

    def clear_history(self):
        self.history = []
        self._save(HISTORY_FILE, self.history)

    def add_favorite(self, city):
        if city not in self.favorites:
            self.favorites.append(city)
            self._save(FAVORITES_FILE, self.favorites)

    def remove_favorite(self, city):
        if city in self.favorites:
            self.favorites.remove(city)
            self._save(FAVORITES_FILE, self.favorites)

    def is_favorite(self, city):
        return city in self.favorites

    def export_csv(self, filepath):
        if not self.history:
            return
        keys = list(self.history[0].keys())
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.history)


# ---------------------------------------------------------------------------
# SCIENCE / UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def dew_point(temp, humidity):
    a, b  = 17.27, 237.7
    rh    = max(humidity, 0.01)
    gamma = (a * temp / (b + temp)) + math.log(rh / 100.0)
    return (b * gamma) / (a - gamma)


def heat_index(temp_c, humidity):
    T  = temp_c * 9.0 / 5.0 + 32
    RH = humidity
    hi = (-42.379 + 2.04901523*T + 10.14333127*RH
          - 0.22475541*T*RH - 0.00683783*T*T
          - 0.05481717*RH*RH + 0.00122874*T*T*RH
          + 0.00085282*T*RH*RH - 0.00000199*T*T*RH*RH)
    return (hi - 32) * 5.0 / 9.0


def wind_chill(temp_c, wind_kmh):
    if temp_c > 10 or wind_kmh < 4.8:
        return temp_c
    return (13.12 + 0.6215*temp_c
            - 11.37*(wind_kmh**0.16)
            + 0.3965*temp_c*(wind_kmh**0.16))


def beaufort_scale(speed_ms):
    thresholds   = [0.3, 1.5, 3.3, 5.5, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6]
    descriptions = ["Calm", "Light air", "Light breeze", "Gentle breeze",
                     "Moderate breeze", "Fresh breeze", "Strong breeze",
                     "Near gale", "Gale", "Strong gale", "Storm",
                     "Violent storm", "Hurricane"]
    for i, t in enumerate(thresholds):
        if speed_ms < t:
            return i, descriptions[i]
    return 12, descriptions[12]


def moon_phase(date):
    known_new = datetime.date(2000, 1, 6)
    diff = (date - known_new).days % 29
    if   diff < 2:  return "New Moon"
    elif diff < 7:  return "Waxing Crescent"
    elif diff < 10: return "First Quarter"
    elif diff < 15: return "Waxing Gibbous"
    elif diff < 17: return "Full Moon"
    elif diff < 22: return "Waning Gibbous"
    elif diff < 25: return "Last Quarter"
    else:           return "Waning Crescent"


def group_forecast_by_day(entries):
    groups = {}
    for entry in entries:
        day = datetime.datetime.fromtimestamp(entry.dt).strftime("%Y-%m-%d")
        groups.setdefault(day, []).append(entry)
    return groups


def lighten_color(hex_color, amount=40):
    r = min(255, int(hex_color[1:3], 16) + amount)
    g = min(255, int(hex_color[3:5], 16) + amount)
    b = min(255, int(hex_color[5:7], 16) + amount)
    return "#%02x%02x%02x" % (r, g, b)


def blend_color(hex_color, bg_hex, alpha):
    r1 = int(hex_color[1:3], 16); g1 = int(hex_color[3:5], 16); b1 = int(hex_color[5:7], 16)
    r2 = int(bg_hex[1:3],    16); g2 = int(bg_hex[3:5],    16); b2 = int(bg_hex[5:7],    16)
    return "#%02x%02x%02x" % (
        int(r1*alpha + r2*(1-alpha)),
        int(g1*alpha + g2*(1-alpha)),
        int(b1*alpha + b2*(1-alpha)),
    )


# ---------------------------------------------------------------------------
# REPAINT REGISTRY
# ---------------------------------------------------------------------------

class RepaintRegistry(object):
    def __init__(self):
        self._items = []

    def register(self, widget):
        self._items.append(widget)

    def repaint_all(self):
        for w in self._items:
            try:
                w.repaint()
            except Exception:
                pass


REGISTRY = RepaintRegistry()


# ---------------------------------------------------------------------------
# CUSTOM WIDGETS
# ---------------------------------------------------------------------------

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super(ScrollableFrame, self).__init__(parent, **kwargs)
        self.canvas  = tk.Canvas(self, bg=COLORS["bg_dark"], highlightthickness=0)
        scrollbar    = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner   = tk.Frame(self.canvas, bg=COLORS["bg_dark"])
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<MouseWheel>", self._scroll)
        self.inner.bind("<MouseWheel>", self._scroll)

    def _scroll(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def repaint(self):
        self.canvas.configure(bg=COLORS["bg_dark"])
        self.inner.configure(bg=COLORS["bg_dark"])


class BarChart(tk.Canvas):
    def __init__(self, parent, data, color, title="", unit="", **kwargs):
        super(BarChart, self).__init__(parent, highlightthickness=0, **kwargs)
        self.data  = data
        self.color = color
        self.title = title
        self.unit  = unit
        self.bind("<Configure>", self._draw)

    def update_data(self, data):
        self.data = data
        self._draw()

    def repaint(self):
        self.configure(bg=COLORS["chart_bg"])
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        self.configure(bg=COLORS["chart_bg"])
        w = self.winfo_width();  h = self.winfo_height()
        if w < 10 or h < 10 or not self.data:
            return
        PL, PR, PT, PB = 52, 20, 28, 48
        cw = w - PL - PR;  ch = h - PT - PB

        if self.title:
            self.create_text(w//2, 13, text=self.title,
                             fill=COLORS["text_sub"], font=("Courier", 8))

        vals  = [v for _, v in self.data]
        min_v = min(vals) * 0.95 if vals else 0
        max_v = max(vals) * 1.05 if vals else 1
        if max_v == min_v:
            max_v = min_v + 1

        for i in range(5):
            y   = PT + ch - ch * i / 4
            val = min_v + (max_v - min_v) * i / 4
            self.create_line(PL, y, PL+cw, y, fill=COLORS["border"], dash=(2, 4))
            self.create_text(PL-4, y, text="%.0f" % val,
                             anchor="e", fill=COLORS["text_dim"], font=("Courier", 7))

        self.create_line(PL, PT, PL, PT+ch, fill=COLORS["border"])
        self.create_line(PL, PT+ch, PL+cw, PT+ch, fill=COLORS["border"])

        n    = len(self.data)
        slot = cw // n
        bw   = max(4, slot - 6)

        for i, (label, val) in enumerate(self.data):
            x  = PL + i*slot + (slot - bw)//2
            bh = int(ch * (val - min_v) / (max_v - min_v))
            y0 = PT + ch - bh
            y1 = PT + ch
            self.create_rectangle(x, y0, x+bw, y1, fill=self.color, outline="")
            self.create_rectangle(x, y0, x+bw, y0+3,
                                  fill=lighten_color(self.color), outline="")
            if bh > 16:
                self.create_text(x+bw//2, y0+4, text="%.0f" % val,
                                 fill=COLORS["text_main"], font=("Courier", 7), anchor="n")
            self.create_text(x+bw//2, PT+ch+10, text=label[:5],
                             fill=COLORS["text_sub"], font=("Courier", 7))


class LineChart(tk.Canvas):
    def __init__(self, parent, data, color, title="", unit="", **kwargs):
        super(LineChart, self).__init__(parent, highlightthickness=0, **kwargs)
        self.data  = data
        self.color = color
        self.title = title
        self.unit  = unit
        self.bind("<Configure>", self._draw)

    def update_data(self, data):
        self.data = data
        self._draw()

    def repaint(self):
        self.configure(bg=COLORS["chart_bg"])
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        self.configure(bg=COLORS["chart_bg"])
        w = self.winfo_width();  h = self.winfo_height()
        if w < 10 or h < 10 or not self.data:
            return
        PL, PR, PT, PB = 52, 20, 28, 48
        cw = w - PL - PR;  ch = h - PT - PB

        if self.title:
            self.create_text(w//2, 13, text=self.title,
                             fill=COLORS["text_sub"], font=("Courier", 8))

        vals  = [v for _, v in self.data]
        min_v = min(vals) - 2 if vals else 0
        max_v = max(vals) + 2 if vals else 1
        if max_v == min_v:
            max_v = min_v + 1

        for i in range(5):
            y   = PT + ch - ch * i / 4
            val = min_v + (max_v - min_v) * i / 4
            self.create_line(PL, y, PL+cw, y, fill=COLORS["border"], dash=(2, 4))
            self.create_text(PL-4, y, text="%.0f%s" % (val, self.unit),
                             anchor="e", fill=COLORS["text_dim"], font=("Courier", 7))

        self.create_line(PL, PT, PL, PT+ch, fill=COLORS["border"])
        self.create_line(PL, PT+ch, PL+cw, PT+ch, fill=COLORS["border"])

        n    = len(self.data)
        step = cw / max(n - 1, 1)

        def to_xy(i, val):
            return PL + i*step, PT + ch - ch*(val-min_v)/(max_v-min_v)

        pts = [to_xy(i, v) for i, (_, v) in enumerate(self.data)]

        # Filled area
        bg       = COLORS["chart_bg"]
        fill_col = blend_color(self.color, bg, 0.15)
        poly = [PL, PT+ch]
        for px, py in pts:
            poly += [px, py]
        poly += [PL+cw, PT+ch]
        self.create_polygon(poly, fill=fill_col, outline="")

        # Line segments
        for i in range(len(pts) - 1):
            self.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                             fill=self.color, width=2, smooth=True)

        # Dots + x-axis labels
        for i, (label, val) in enumerate(self.data):
            x, y = pts[i]
            self.create_oval(x-4, y-4, x+4, y+4,
                             fill=self.color, outline=COLORS["bg_card"])
            self.create_text(x, PT+ch+10, text=label[:5],
                             fill=COLORS["text_sub"], font=("Courier", 7))


class WindRose(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super(WindRose, self).__init__(parent, highlightthickness=0, **kwargs)
        self.angle = 0
        self.speed = 0.0
        self.bind("<Configure>", self._draw)

    def set_wind(self, angle, speed):
        self.angle = angle
        self.speed = speed
        self._draw()

    def repaint(self):
        self.configure(bg=COLORS["bg_card"])
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        self.configure(bg=COLORS["bg_card"])
        w  = self.winfo_width();  h = self.winfo_height()
        cx = w//2;  cy = h//2
        r  = min(cx, cy) - 12

        self.create_oval(cx-r, cy-r, cx+r, cy+r,
                         outline=COLORS["border"], width=2)
        self.create_oval(cx-r//2, cy-r//2, cx+r//2, cy+r//2,
                         outline=COLORS["border"], dash=(3, 5))

        for label, deg in [("N",0), ("E",90), ("S",180), ("W",270)]:
            rad = math.radians(deg - 90)
            tx  = cx + int((r+14)*math.cos(rad))
            ty  = cy + int((r+14)*math.sin(rad))
            self.create_text(tx, ty, text=label,
                             fill=COLORS["text_sub"], font=("Courier", 9, "bold"))

        for deg in [0, 45, 90, 135]:
            rad = math.radians(deg)
            self.create_line(cx+int(r*math.cos(rad)), cy+int(r*math.sin(rad)),
                             cx-int(r*math.cos(rad)), cy-int(r*math.sin(rad)),
                             fill=COLORS["border"], dash=(2, 6))

        rad = math.radians(self.angle - 90)
        ax  = cx + int((r-10)*math.cos(rad))
        ay  = cy + int((r-10)*math.sin(rad))
        self.create_line(cx, cy, ax, ay,
                         fill=COLORS["accent"], width=3,
                         arrow=tk.LAST, arrowshape=(12, 15, 5))
        self.create_oval(cx-4, cy-4, cx+4, cy+4,
                         fill=COLORS["accent"], outline="")
        self.create_text(cx, cy+r+18,
                         text="%.1f" % self.speed,
                         fill=COLORS["text_main"], font=("Courier", 10, "bold"))


class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value="--", color=None, **kwargs):
        super(StatCard, self).__init__(parent, bg=COLORS["bg_card"], **kwargs)
        self.configure(padx=12, pady=10)
        color = color or COLORS["accent"]
        self._color = color
        self._icon  = icon
        self._label = label

        top = tk.Frame(self, bg=COLORS["bg_card"])
        top.pack(fill="x")
        self._icon_lbl = tk.Label(top, text=icon, bg=COLORS["bg_card"], fg=color,
                                   font=("Courier", 10, "bold"))
        self._icon_lbl.pack(side="left")
        self._label_lbl = tk.Label(top, text=label,
                                    bg=COLORS["bg_card"], fg=COLORS["text_sub"],
                                    font=("Courier", 8))
        self._label_lbl.pack(side="left", padx=(6, 0), pady=(2, 0))

        self._val_lbl = tk.Label(self, text=value,
                                  bg=COLORS["bg_card"], fg=COLORS["text_main"],
                                  font=("Courier", 14, "bold"))
        self._val_lbl.pack(anchor="w")

    def update_value(self, value):
        self._val_lbl.configure(text=value)

    def repaint(self):
        self.configure(bg=COLORS["bg_card"])
        self._icon_lbl.configure(bg=COLORS["bg_card"],  fg=self._color)
        self._label_lbl.configure(bg=COLORS["bg_card"], fg=COLORS["text_sub"])
        self._val_lbl.configure(bg=COLORS["bg_card"],   fg=COLORS["text_main"])


class ToastNotification(object):
    def __init__(self, parent, message, color=None):
        color = color or COLORS["accent2"]
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        pw = parent.winfo_rootx() + parent.winfo_width()//2
        ph = parent.winfo_rooty() + 65
        self.win.geometry("320x38+%d+%d" % (pw-160, ph))
        self.win.configure(bg=COLORS["bg_panel"])
        tk.Label(self.win, text=message,
                 bg=COLORS["bg_panel"], fg=color,
                 font=("Courier", 10), padx=20).pack(expand=True, fill="both")
        parent.after(2500, self._close)

    def _close(self):
        try:
            self.win.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------------------------

class WeatherApp(tk.Tk):
    def __init__(self):
        super(WeatherApp, self).__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_SIZE)
        self.configure(bg=COLORS["bg_dark"])

        self.units        = tk.StringVar(value="metric")
        self.theme_name   = tk.StringVar(value="Dark")
        self.current_weather   = None
        self.forecast_entries  = []
        self.api_client        = WeatherAPIClient(API_KEY)
        self.data_manager      = DataManager()
        self.loading           = False
        self.auto_refresh_job      = None
        self.auto_refresh_interval = tk.IntVar(value=0)

        self._setup_styles()
        self._build_header()
        self._build_main()
        self._build_status_bar()

        if not API_KEY:
            self.after(500, self._warn_no_api_key)

    # ----------------------------------------------------------------
    # STYLES
    # ----------------------------------------------------------------

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        self._apply_ttk_styles(style)

    def _apply_ttk_styles(self, style=None):
        if style is None:
            style = ttk.Style(self)
        style.configure("TNotebook",
                         background=COLORS["bg_dark"], borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=COLORS["bg_panel"],
                         foreground=COLORS["text_sub"],
                         padding=[14, 7],
                         font=("Courier", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["bg_card"])],
                  foreground=[("selected", COLORS["accent"])])
        style.configure("Treeview",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_main"],
                         fieldbackground=COLORS["bg_card"],
                         rowheight=26,
                         font=("Courier", 8))
        style.configure("Treeview.Heading",
                         background=COLORS["bg_panel"],
                         foreground=COLORS["text_sub"],
                         font=("Courier", 8, "bold"))
        style.map("Treeview", background=[("selected", COLORS["accent"])])
        style.configure("Vertical.TScrollbar",
                         background=COLORS["bg_panel"],
                         troughcolor=COLORS["bg_dark"],
                         borderwidth=0)

    # ----------------------------------------------------------------
    # HEADER
    # ----------------------------------------------------------------

    def _build_header(self):
        self.header = tk.Frame(self, bg=COLORS["bg_panel"], height=64)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        logo = tk.Frame(self.header, bg=COLORS["bg_panel"])
        logo.pack(side="left", padx=18, pady=8)
        self._header_logo = tk.Label(logo, text="[WSP]",
                                      bg=COLORS["bg_panel"], fg=COLORS["accent"],
                                      font=("Courier", 18, "bold"))
        self._header_logo.pack(side="left")
        title_f = tk.Frame(logo, bg=COLORS["bg_panel"])
        title_f.pack(side="left", padx=8)
        self._header_title = tk.Label(title_f, text=APP_TITLE,
                                       bg=COLORS["bg_panel"], fg=COLORS["text_main"],
                                       font=("Courier", 13, "bold"))
        self._header_title.pack(anchor="w")
        self._header_ver = tk.Label(title_f, text="v" + APP_VERSION,
                                     bg=COLORS["bg_panel"], fg=COLORS["text_dim"],
                                     font=("Courier", 7))
        self._header_ver.pack(anchor="w")

        search_f = tk.Frame(self.header, bg=COLORS["bg_panel"])
        search_f.pack(side="left", padx=16, expand=True, fill="x", pady=12)

        self.search_var = tk.StringVar()
        self._search_entry = tk.Entry(search_f, textvariable=self.search_var,
                                       bg=COLORS["bg_dark"], fg=COLORS["text_main"],
                                       insertbackground=COLORS["accent"],
                                       relief="flat", font=("Courier", 11), width=26)
        self._search_entry.pack(side="left", ipady=7, ipadx=8, padx=(0, 8))
        self._search_entry.insert(0, "Enter city name...")
        self._search_entry.bind("<Return>", lambda e: self._search())
        self._search_entry.bind("<FocusIn>",
            lambda e: self._search_entry.delete(0, "end")
            if self._search_entry.get() == "Enter city name..." else None)

        self.search_btn = tk.Button(search_f, text="Search",
                                     bg=COLORS["accent"], fg=COLORS["bg_dark"],
                                     relief="flat", font=("Courier", 10, "bold"),
                                     padx=14, pady=6, cursor="hand2",
                                     command=self._search)
        self.search_btn.pack(side="left")

        right_f = tk.Frame(self.header, bg=COLORS["bg_panel"])
        right_f.pack(side="right", padx=12, pady=10)

        self.theme_btn = tk.Button(right_f, text="[ Light Mode ]",
                                    bg=COLORS["bg_card"], fg=COLORS["accent4"],
                                    relief="flat", font=("Courier", 8),
                                    padx=8, cursor="hand2",
                                    command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=4)

        self._fav_btn = tk.Button(right_f, text="[* Favorites]",
                                   bg=COLORS["bg_card"], fg=COLORS["accent4"],
                                   relief="flat", font=("Courier", 8),
                                   padx=8, cursor="hand2",
                                   command=self._show_favorites_window)
        self._fav_btn.pack(side="right", padx=4)

        units_f = tk.Frame(right_f, bg=COLORS["bg_panel"])
        units_f.pack(side="right", padx=8)
        tk.Label(units_f, text="Units:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_sub"], font=("Courier", 8)).pack(side="left")
        self._unit_rbs = []
        for label, val in [("C", "metric"), ("F", "imperial"), ("K", "standard")]:
            rb = tk.Radiobutton(units_f, text=label, variable=self.units, value=val,
                                bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                                selectcolor=COLORS["bg_dark"],
                                activebackground=COLORS["bg_panel"],
                                activeforeground=COLORS["accent"],
                                font=("Courier", 9), cursor="hand2",
                                command=self._on_unit_change)
            rb.pack(side="left", padx=3)
            self._unit_rbs.append(rb)

    # ----------------------------------------------------------------
    # NOTEBOOK
    # ----------------------------------------------------------------

    def _build_main(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_current  = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_forecast = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_charts   = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_analysis = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_history  = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_settings = tk.Frame(self.notebook, bg=COLORS["bg_dark"])

        self.notebook.add(self.tab_current,  text="  Current  ")
        self.notebook.add(self.tab_forecast, text="  Forecast  ")
        self.notebook.add(self.tab_charts,   text="  Charts  ")
        self.notebook.add(self.tab_analysis, text="  Analysis  ")
        self.notebook.add(self.tab_history,  text="  History  ")
        self.notebook.add(self.tab_settings, text="  Settings  ")

        self._build_current_tab()
        self._build_forecast_tab()
        self._build_charts_tab()
        self._build_analysis_tab()
        self._build_history_tab()
        self._build_settings_tab()

    # ----------------------------------------------------------------
    # STATUS BAR
    # ----------------------------------------------------------------

    def _build_status_bar(self):
        self._status_bar = tk.Frame(self, bg=COLORS["bg_panel"], height=26)
        self._status_bar.pack(fill="x", side="bottom")
        self._status_lbl = tk.Label(self._status_bar,
                                     text="Ready -- Enter a city to begin",
                                     bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                                     font=("Courier", 8), anchor="w")
        self._status_lbl.pack(side="left", padx=14, pady=4)
        self._clock_lbl = tk.Label(self._status_bar, text="",
                                    bg=COLORS["bg_panel"], fg=COLORS["text_dim"],
                                    font=("Courier", 8))
        self._clock_lbl.pack(side="right", padx=14, pady=4)
        self._tick()

    def _tick(self):
        now = datetime.datetime.now().strftime("%a %b %d  %I:%M:%S %p")
        self._clock_lbl.configure(text=now)
        self.after(1000, self._tick)

    # ----------------------------------------------------------------
    # CURRENT TAB
    # ----------------------------------------------------------------

    def _build_current_tab(self):
        self.cur_hero = tk.Frame(self.tab_current, bg=COLORS["bg_panel"], height=150)
        self.cur_hero.pack(fill="x")
        self.cur_hero.pack_propagate(False)

        left = tk.Frame(self.cur_hero, bg=COLORS["bg_panel"])
        left.pack(side="left", padx=24, pady=16)

        self.cur_icon_lbl = tk.Label(left, text="[WTH]",
                                      bg=COLORS["bg_panel"], fg=COLORS["accent"],
                                      font=("Courier", 28, "bold"), width=7)
        self.cur_icon_lbl.pack(side="left")

        temp_block = tk.Frame(left, bg=COLORS["bg_panel"])
        temp_block.pack(side="left", padx=16)
        self.cur_temp_lbl = tk.Label(temp_block, text="--",
                                      bg=COLORS["bg_panel"], fg=COLORS["text_main"],
                                      font=("Courier", 42, "bold"))
        self.cur_temp_lbl.pack(anchor="w")
        self.cur_desc_lbl = tk.Label(temp_block, text="Search for a city",
                                      bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                                      font=("Courier", 12))
        self.cur_desc_lbl.pack(anchor="w")
        self.cur_city_lbl = tk.Label(temp_block, text="",
                                      bg=COLORS["bg_panel"], fg=COLORS["text_dim"],
                                      font=("Courier", 9))
        self.cur_city_lbl.pack(anchor="w")

        right = tk.Frame(self.cur_hero, bg=COLORS["bg_panel"])
        right.pack(side="right", padx=24, pady=16, anchor="center")
        self.cur_minmax_lbl = tk.Label(right, text="",
                                        bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                                        font=("Courier", 10))
        self.cur_minmax_lbl.pack(anchor="e")
        self.cur_feels_lbl = tk.Label(right, text="",
                                       bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                                       font=("Courier", 10))
        self.cur_feels_lbl.pack(anchor="e")
        self.cur_coord_lbl = tk.Label(right, text="",
                                       bg=COLORS["bg_panel"], fg=COLORS["text_dim"],
                                       font=("Courier", 8))
        self.cur_coord_lbl.pack(anchor="e", pady=(6, 0))

        fav_f = tk.Frame(self.cur_hero, bg=COLORS["bg_panel"])
        fav_f.pack(side="right", padx=8, pady=16, anchor="s")
        self.add_fav_btn = tk.Button(fav_f, text="[+] Add Favorite",
                                      bg=COLORS["bg_card"], fg=COLORS["accent4"],
                                      relief="flat", font=("Courier", 8),
                                      padx=8, cursor="hand2",
                                      command=self._toggle_favorite)
        self.add_fav_btn.pack()

        cards_f = tk.Frame(self.tab_current, bg=COLORS["bg_dark"])
        cards_f.pack(fill="both", expand=True, padx=8, pady=8)

        self.stat_cards = {}
        card_cfgs = [
            ("humidity",   "[HUM]", "Humidity",    COLORS["accent"]),
            ("pressure",   "[PRE]", "Pressure",    COLORS["accent2"]),
            ("wind",       "[WND]", "Wind Speed",  COLORS["accent3"]),
            ("visibility", "[VIS]", "Visibility",  COLORS["accent4"]),
            ("clouds",     "[CLD]", "Cloud Cover", COLORS["cool"]),
            ("sunrise",    "[SRS]", "Sunrise",     COLORS["accent4"]),
            ("sunset",     "[SST]", "Sunset",      COLORS["warm"]),
            ("moon",       "[MON]", "Moon Phase",  COLORS["text_sub"]),
            ("dew",        "[DEW]", "Dew Point",   COLORS["accent"]),
            ("heat_idx",   "[HI]",  "Heat Index",  COLORS["warm"]),
            ("wind_chill", "[WC]",  "Wind Chill",  COLORS["cool"]),
            ("beaufort",   "[BFT]", "Beaufort",    COLORS["accent2"]),
        ]
        cols = 4
        for i, (key, icon, label, color) in enumerate(card_cfgs):
            row, col = divmod(i, cols)
            card = StatCard(cards_f, icon=icon, label=label, color=color)
            card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")
            self.stat_cards[key] = card
            REGISTRY.register(card)
        for c in range(cols):
            cards_f.columnconfigure(c, weight=1)
        for r in range(math.ceil(len(card_cfgs) / cols)):
            cards_f.rowconfigure(r, weight=1)

        self._cards_frame = cards_f

    # ----------------------------------------------------------------
    # FORECAST TAB
    # ----------------------------------------------------------------

    def _build_forecast_tab(self):
        top = tk.Frame(self.tab_forecast, bg=COLORS["bg_dark"])
        top.pack(fill="x", padx=10, pady=8)
        self._fc_header = tk.Label(
            top, text="5-Day / 40-Slot Forecast  (every 3 hours)",
            bg=COLORS["bg_dark"], fg=COLORS["text_sub"], font=("Courier", 9))
        self._fc_header.pack(side="left")

        self.forecast_scroll = ScrollableFrame(self.tab_forecast, bg=COLORS["bg_dark"])
        self.forecast_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.forecast_inner = self.forecast_scroll.inner
        REGISTRY.register(self.forecast_scroll)

    def _populate_forecast(self):
        for w in self.forecast_inner.winfo_children():
            w.destroy()
        if not self.forecast_entries:
            tk.Label(self.forecast_inner, text="No forecast data.",
                     bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                     font=("Courier", 10)).pack(pady=30)
            return

        grouped    = group_forecast_by_day(self.forecast_entries)
        unit       = UNIT_LABELS[self.units.get()]["temp"]
        speed_unit = UNIT_LABELS[self.units.get()]["speed"]

        for day_str, entries in grouped.items():
            day_dt    = datetime.datetime.strptime(day_str, "%Y-%m-%d")
            day_label = day_dt.strftime("%A, %B %d")

            dh = tk.Frame(self.forecast_inner, bg=COLORS["bg_dark"])
            dh.pack(fill="x", pady=(10, 3), padx=4)
            tk.Label(dh, text="-- " + day_label + " --",
                     bg=COLORS["bg_dark"], fg=COLORS["accent"],
                     font=("Courier", 10, "bold")).pack(side="left")

            slots_f = tk.Frame(self.forecast_inner, bg=COLORS["bg_dark"])
            slots_f.pack(fill="x", padx=4, pady=2)

            for entry in entries:
                card = tk.Frame(slots_f, bg=COLORS["bg_card"],
                                relief="flat", padx=10, pady=8)
                card.pack(side="left", padx=3, pady=2)
                tk.Label(card, text=entry.time_str(),
                         bg=COLORS["bg_card"], fg=COLORS["text_sub"],
                         font=("Courier", 7)).pack()
                tk.Label(card, text=entry.icon,
                         bg=COLORS["bg_card"], fg=COLORS["accent"],
                         font=("Courier", 11, "bold")).pack(pady=2)
                tk.Label(card, text="%d%s" % (entry.temp, unit),
                         bg=COLORS["bg_card"], fg=COLORS["text_main"],
                         font=("Courier", 12, "bold")).pack()
                tk.Label(card, text=entry.description[:14],
                         bg=COLORS["bg_card"], fg=COLORS["text_sub"],
                         font=("Courier", 7)).pack()
                tk.Label(card, text="H:%d%%" % entry.humidity,
                         bg=COLORS["bg_card"], fg=COLORS["cool"],
                         font=("Courier", 7)).pack(pady=(3, 0))
                tk.Label(card, text="P:%.0f%%" % entry.pop,
                         bg=COLORS["bg_card"], fg=COLORS["accent4"],
                         font=("Courier", 7)).pack()
                tk.Label(card, text="W:%.1f%s" % (entry.wind_speed, speed_unit),
                         bg=COLORS["bg_card"], fg=COLORS["text_dim"],
                         font=("Courier", 7)).pack()

    # ----------------------------------------------------------------
    # CHARTS TAB
    # ----------------------------------------------------------------

    def _build_charts_tab(self):
        top = tk.Frame(self.tab_charts, bg=COLORS["bg_dark"])
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Forecast Charts -- select data:",
                 bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                 font=("Courier", 9)).pack(side="left")

        self.chart_type_var = tk.StringVar(value="Temperature")
        self._chart_rbs = []
        for ct in ["Temperature", "Humidity", "Precip %", "Wind Speed", "Pressure"]:
            rb = tk.Radiobutton(top, text=ct, variable=self.chart_type_var, value=ct,
                                bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                                selectcolor=COLORS["bg_panel"],
                                activebackground=COLORS["bg_dark"],
                                activeforeground=COLORS["accent"],
                                font=("Courier", 8), cursor="hand2",
                                command=self._update_charts)
            rb.pack(side="left", padx=6)
            self._chart_rbs.append(rb)

        body = tk.Frame(self.tab_charts, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        wr_f = tk.Frame(body, bg=COLORS["bg_dark"])
        wr_f.pack(side="right", fill="y", padx=(6, 0))
        tk.Label(wr_f, text="Wind Dir",
                 bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                 font=("Courier", 8)).pack()
        self.wind_rose = WindRose(wr_f, width=140, height=140)
        self.wind_rose.pack()
        REGISTRY.register(self.wind_rose)

        charts_inner = tk.Frame(body, bg=COLORS["bg_dark"])
        charts_inner.pack(fill="both", expand=True)

        self.line_chart = LineChart(charts_inner, data=[], color=COLORS["accent"],
                                    title="Temperature Trend", unit="")
        self.line_chart.pack(fill="both", expand=True, pady=(0, 5))

        self.bar_chart = BarChart(charts_inner, data=[], color=COLORS["accent2"],
                                   title="Precipitation Probability (%)")
        self.bar_chart.pack(fill="both", expand=True)

        REGISTRY.register(self.line_chart)
        REGISTRY.register(self.bar_chart)

    def _update_charts(self, event=None):
        if not self.forecast_entries:
            return
        ct         = self.chart_type_var.get()
        unit       = UNIT_LABELS[self.units.get()]["temp"]
        speed_unit = UNIT_LABELS[self.units.get()]["speed"]
        entries    = self.forecast_entries[:16]

        def lbl(e):
            s = e.time_str()
            return s.replace(":00", "").replace(" ", "")

        if ct == "Temperature":
            data = [(lbl(e), e.temp)      for e in entries]
            self.line_chart.color = COLORS["accent"]
            self.line_chart.title = "Temperature (%s)" % unit
            self.line_chart.unit  = unit
        elif ct == "Humidity":
            data = [(lbl(e), e.humidity)  for e in entries]
            self.line_chart.color = COLORS["cool"]
            self.line_chart.title = "Humidity (%)"
            self.line_chart.unit  = "%"
        elif ct == "Precip %":
            data = [(lbl(e), e.pop)       for e in entries]
            self.line_chart.color = COLORS["accent4"]
            self.line_chart.title = "Precipitation Probability (%)"
            self.line_chart.unit  = "%"
        elif ct == "Wind Speed":
            data = [(lbl(e), e.wind_speed) for e in entries]
            self.line_chart.color = COLORS["accent3"]
            self.line_chart.title = "Wind Speed (%s)" % speed_unit
            self.line_chart.unit  = speed_unit
        elif ct == "Pressure":
            data = [(lbl(e), e.pressure)  for e in entries]
            self.line_chart.color = COLORS["accent2"]
            self.line_chart.title = "Pressure (hPa)"
            self.line_chart.unit  = "hPa"
        else:
            data = []

        self.line_chart.update_data(data)
        pop_data = [(lbl(e), e.pop) for e in entries]
        self.bar_chart.update_data(pop_data)

    # ----------------------------------------------------------------
    # ANALYSIS TAB
    # ----------------------------------------------------------------

    def _build_analysis_tab(self):
        scroll = ScrollableFrame(self.tab_analysis, bg=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._analysis_scroll = scroll
        inner = scroll.inner
        REGISTRY.register(scroll)

        self._analysis_labels = {}
        self._analysis_frames = []

        sections = [
            (SEC["temp"], [
                ("avg_temp",   "Average Forecast Temp"),
                ("max_temp",   "Max Forecast Temp"),
                ("min_temp",   "Min Forecast Temp"),
                ("temp_range", "Temperature Range"),
                ("dew_pt",     "Dew Point"),
                ("heat_idx",   "Heat Index"),
                ("wind_chll",  "Wind Chill"),
            ]),
            (SEC["wind"], [
                ("wind_avg",   "Avg Forecast Wind"),
                ("wind_max",   "Max Forecast Wind"),
                ("bft",        "Beaufort Scale"),
                ("dir",        "Wind Direction"),
                ("pressure",   "Pressure"),
                ("visibility", "Visibility"),
            ]),
            (SEC["precip"], [
                ("hum_avg",     "Avg Forecast Humidity"),
                ("hum_max",     "Max Forecast Humidity"),
                ("pop_avg",     "Avg Precipitation Chance"),
                ("rainy_slots", "Rainy 3hr Slots (>50%)"),
                ("total_rain",  "Total Forecast Rain (mm)"),
            ]),
            (SEC["sun"], [
                ("sunrise",    "Sunrise"),
                ("sunset",     "Sunset"),
                ("day_length", "Day Length"),
                ("moon",       "Moon Phase"),
                ("clouds_avg", "Avg Cloud Cover"),
                ("uv_comment", "UV Advisory"),
            ]),
            (SEC["summary"], [
                ("best_day",       "Best Forecast Day"),
                ("worst_day",      "Worst Day (most rain)"),
                ("trend",          "Temperature Trend"),
                ("comfort",        "Comfort Assessment"),
                ("recommendation", "What to Wear"),
            ]),
        ]

        for sec_title, fields in sections:
            div = tk.Frame(inner, bg=COLORS["border"], height=1)
            div.pack(fill="x", pady=(14, 4))
            self._analysis_frames.append(("div", div))

            hdr = tk.Label(inner, text=sec_title,
                           bg=COLORS["bg_dark"], fg=COLORS["accent"],
                           font=("Courier", 10, "bold"))
            hdr.pack(anchor="w")
            self._analysis_frames.append(("hdr", hdr))

            grid = tk.Frame(inner, bg=COLORS["bg_dark"])
            grid.pack(fill="x", pady=3)
            self._analysis_frames.append(("grid", grid))

            for r, (key, label) in enumerate(fields):
                lbl_w = tk.Label(grid, text=label,
                                 bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                                 font=("Courier", 8), width=30, anchor="w")
                lbl_w.grid(row=r, column=0, sticky="w", padx=8, pady=2)
                val_w = tk.Label(grid, text="--",
                                 bg=COLORS["bg_dark"], fg=COLORS["text_main"],
                                 font=("Courier", 8, "bold"), anchor="w")
                val_w.grid(row=r, column=1, sticky="w", padx=8, pady=2)
                self._analysis_labels[key] = val_w

    def _populate_analysis(self):
        if not self.current_weather or not self.forecast_entries:
            return
        w  = self.current_weather
        fc = self.forecast_entries
        unit       = UNIT_LABELS[self.units.get()]["temp"]
        speed_unit = UNIT_LABELS[self.units.get()]["speed"]

        temps   = [e.temp       for e in fc]
        winds   = [e.wind_speed for e in fc]
        humids  = [e.humidity   for e in fc]
        pops    = [e.pop        for e in fc]
        clouds_ = [e.clouds     for e in fc]

        avg_t = sum(temps)  / len(temps)
        max_t = max(temps)
        min_t = min(temps)

        dp  = dew_point(w.temp, w.humidity)
        hi  = heat_index(w.temp, w.humidity)
        wc  = wind_chill(w.temp, w.wind_speed * 3.6)
        bft_num, bft_desc = beaufort_scale(w.wind_speed)

        grouped = group_forecast_by_day(fc)
        day_pop = {}
        for d, ents in grouped.items():
            day_pop[d] = sum(e.pop for e in ents) / len(ents)
        best_d  = min(day_pop, key=day_pop.get)
        worst_d = max(day_pop, key=day_pop.get)
        best_s  = datetime.datetime.strptime(best_d,  "%Y-%m-%d").strftime("%A %b %d")
        worst_s = datetime.datetime.strptime(worst_d, "%Y-%m-%d").strftime("%A %b %d")

        half = len(temps) // 2
        h1   = sum(temps[:half]) / half
        h2   = sum(temps[half:]) / max(len(temps) - half, 1)
        diff = h2 - h1
        if   diff > 1:  trend = "Warming (+%.1f%s)" % (diff, unit)
        elif diff < -1: trend = "Cooling (%.1f%s)"  % (diff, unit)
        else:           trend = "Stable"

        if   w.temp < 0:  comfort = "Freezing"
        elif w.temp < 10: comfort = "Cold"
        elif w.temp < 18: comfort = "Cool"
        elif w.temp < 25: comfort = "Comfortable"
        elif w.temp < 32: comfort = "Warm"
        else:             comfort = "Hot"

        if   w.temp < 0:  wear = "Heavy winter coat, gloves, hat, thermals"
        elif w.temp < 10: wear = "Warm coat, scarf, and layers"
        elif w.temp < 18: wear = "Light jacket or sweater"
        elif w.temp < 25: wear = "T-shirt and jeans, maybe a light layer"
        else:             wear = "Light clothing + sunscreen"
        if w.rain_1h > 0 or any(e.pop > 50 for e in fc[:5]):
            wear += " + Umbrella"

        total_rain = sum(e.rain for e in fc)
        rainy      = sum(1 for e in fc if e.pop > 50)
        day_secs   = w.sunset - w.sunrise
        hours_dl, rem = divmod(day_secs, 3600)
        mins_dl = rem // 60

        vals = {
            "avg_temp":      "%.1f %s"  % (avg_t, unit),
            "max_temp":      "%.1f %s"  % (max_t, unit),
            "min_temp":      "%.1f %s"  % (min_t, unit),
            "temp_range":    "%.1f %s"  % (max_t - min_t, unit),
            "dew_pt":        "%.1f %s"  % (dp, unit),
            "heat_idx":      "%.1f %s"  % (hi, unit),
            "wind_chll":     "%.1f %s"  % (wc, unit),
            "wind_avg":      "%.1f %s"  % (sum(winds)/len(winds), speed_unit),
            "wind_max":      "%.1f %s"  % (max(winds), speed_unit),
            "bft":           "%d -- %s" % (bft_num, bft_desc),
            "dir":           "%s (%d deg)" % (w.wind_direction, w.wind_deg),
            "pressure":      "%d hPa"   % w.pressure,
            "visibility":    "%.1f km"  % w.visibility,
            "hum_avg":       "%.0f%%"   % (sum(humids)/len(humids)),
            "hum_max":       "%d%%"     % max(humids),
            "pop_avg":       "%.0f%%"   % (sum(pops)/len(pops)),
            "rainy_slots":   str(rainy),
            "total_rain":    "%.1f mm"  % total_rain,
            "sunrise":       w.sunrise_time(),
            "sunset":        w.sunset_time(),
            "day_length":    "%dh %dm"  % (hours_dl, mins_dl),
            "moon":          moon_phase(datetime.date.today()),
            "clouds_avg":    "%.0f%%"   % (sum(clouds_)/len(clouds_)),
            "uv_comment":    "Moderate -- wear SPF 30+" if w.clouds < 30 else "Reduced (cloudy)",
            "best_day":      best_s,
            "worst_day":     worst_s,
            "trend":         trend,
            "comfort":       comfort,
            "recommendation": wear,
        }
        for key, val in vals.items():
            if key in self._analysis_labels:
                self._analysis_labels[key].configure(text=val)

    # ----------------------------------------------------------------
    # HISTORY TAB
    # ----------------------------------------------------------------

    def _build_history_tab(self):
        toolbar = tk.Frame(self.tab_history, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=10, pady=8)
        self._hist_title = tk.Label(toolbar, text="Search History",
                                     bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                                     font=("Courier", 9))
        self._hist_title.pack(side="left")
        tk.Button(toolbar, text="Export CSV",
                  bg=COLORS["bg_card"], fg=COLORS["accent2"],
                  relief="flat", font=("Courier", 8), padx=8, cursor="hand2",
                  command=self._export_history).pack(side="right", padx=3)
        tk.Button(toolbar, text="Clear All",
                  bg=COLORS["bg_card"], fg=COLORS["accent3"],
                  relief="flat", font=("Courier", 8), padx=8, cursor="hand2",
                  command=self._clear_history).pack(side="right", padx=3)

        cols = ("City","Country","Temp","Condition","Humidity","Wind","Units","Searched At")
        self.history_tree = ttk.Treeview(self.tab_history, columns=cols,
                                          show="headings", height=20)
        widths = [100, 60, 70, 100, 80, 80, 70, 160]
        for col, w in zip(cols, widths):
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(self.tab_history, orient="vertical",
                            command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side="left", fill="both", expand=True,
                                padx=(10, 0), pady=(0, 10))
        vsb.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        self.history_tree.bind("<Double-1>", self._history_dbl_click)
        self._refresh_history_tree()

    def _refresh_history_tree(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for entry in self.data_manager.history:
            u   = entry.get("units", "metric")
            sym = UNIT_LABELS.get(u, {}).get("temp", "")
            self.history_tree.insert("", "end", values=(
                entry.get("city", ""),
                entry.get("country", ""),
                "%.1f %s" % (entry.get("temp", 0), sym),
                entry.get("condition", ""),
                "%d%%" % entry.get("humidity", 0),
                "%.1f"  % entry.get("wind_speed", 0),
                u,
                entry.get("searched_at", "")[:19],
            ))

    def _history_dbl_click(self, event):
        sel = self.history_tree.selection()
        if sel:
            vals = self.history_tree.item(sel[0], "values")
            if vals:
                self.search_var.set(vals[0])
                self._search()

    def _export_history(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export History")
        if path:
            self.data_manager.export_csv(path)
            ToastNotification(self, "Exported: " + os.path.basename(path))

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all search history?"):
            self.data_manager.clear_history()
            self._refresh_history_tree()
            ToastNotification(self, "History cleared.", COLORS["accent3"])

    # ----------------------------------------------------------------
    # SETTINGS TAB
    # ----------------------------------------------------------------

    def _build_settings_tab(self):
        scroll = ScrollableFrame(self.tab_settings, bg=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        inner = scroll.inner
        REGISTRY.register(scroll)

        def section(title):
            tk.Frame(inner, bg=COLORS["border"], height=1).pack(fill="x", pady=(14, 4))
            tk.Label(inner, text=title, bg=COLORS["bg_dark"],
                     fg=COLORS["accent"], font=("Courier", 10, "bold")).pack(anchor="w")

        # --- API Key ---
        section("API KEY")
        masked = (API_KEY[:6] + "..." + API_KEY[-4:]) if len(API_KEY) > 10 else (
                  "Not set" if not API_KEY else API_KEY)
        krow = tk.Frame(inner, bg=COLORS["bg_dark"])
        krow.pack(fill="x", pady=4)
        tk.Label(krow, text="Current key:", bg=COLORS["bg_dark"],
                 fg=COLORS["text_sub"], font=("Courier", 8)).pack(side="left")
        tk.Label(krow, text=masked, bg=COLORS["bg_dark"],
                 fg=COLORS["text_main"], font=("Courier", 8, "bold")).pack(side="left", padx=6)

        nrow = tk.Frame(inner, bg=COLORS["bg_dark"])
        nrow.pack(fill="x", pady=4)
        tk.Label(nrow, text="New key:", bg=COLORS["bg_dark"],
                 fg=COLORS["text_sub"], font=("Courier", 8)).pack(side="left")
        self.new_key_var = tk.StringVar()
        tk.Entry(nrow, textvariable=self.new_key_var, show="*",
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 insertbackground=COLORS["accent"], relief="flat",
                 font=("Courier", 9), width=36).pack(side="left", padx=6, ipady=4)
        tk.Button(nrow, text="Save", bg=COLORS["accent"], fg=COLORS["bg_dark"],
                  relief="flat", font=("Courier", 8, "bold"),
                  padx=8, cursor="hand2",
                  command=self._save_api_key).pack(side="left")

        tk.Button(inner, text="Test API Connection",
                  bg=COLORS["bg_card"], fg=COLORS["accent2"],
                  relief="flat", font=("Courier", 8), padx=10, pady=5,
                  cursor="hand2", command=self._test_api).pack(anchor="w", pady=5)

        # --- Appearance ---
        section("APPEARANCE")
        theme_row = tk.Frame(inner, bg=COLORS["bg_dark"])
        theme_row.pack(fill="x", pady=5)
        tk.Label(theme_row, text="Theme:", bg=COLORS["bg_dark"],
                 fg=COLORS["text_sub"], font=("Courier", 8)).pack(side="left")
        for tname in ["Dark", "Light"]:
            rb = tk.Radiobutton(theme_row, text=tname,
                                variable=self.theme_name, value=tname,
                                bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                                selectcolor=COLORS["bg_panel"],
                                activebackground=COLORS["bg_dark"],
                                font=("Courier", 9), cursor="hand2",
                                command=self._apply_theme_from_radio)
            rb.pack(side="left", padx=8)

        # --- Auto-refresh ---
        section("AUTO REFRESH")
        ref_row = tk.Frame(inner, bg=COLORS["bg_dark"])
        ref_row.pack(fill="x", pady=5)
        tk.Label(ref_row, text="Refresh every:", bg=COLORS["bg_dark"],
                 fg=COLORS["text_sub"], font=("Courier", 8)).pack(side="left")
        for mins, lbl in [(0,"Off"), (5,"5 min"), (10,"10 min"), (30,"30 min")]:
            rb = tk.Radiobutton(ref_row, text=lbl,
                                variable=self.auto_refresh_interval, value=mins,
                                bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                                selectcolor=COLORS["bg_panel"],
                                activebackground=COLORS["bg_dark"],
                                font=("Courier", 8), cursor="hand2",
                                command=self._on_refresh_change)
            rb.pack(side="left", padx=6)

        # --- About ---
        section("ABOUT")
        about = ("%s v%s\n"
                 "Pure Python + Tkinter  |  No pip installs required\n"
                 "Data: OpenWeatherMap API\n"
                 "Python 3.7.6+ / Windows 7 32-bit compatible\n"
                 "ASCII icon system -- renders on all systems"
                 % (APP_TITLE, APP_VERSION))
        tk.Label(inner, text=about, bg=COLORS["bg_dark"],
                 fg=COLORS["text_sub"], font=("Courier", 8),
                 justify="left").pack(anchor="w", pady=5)

    def _save_api_key(self):
        key = self.new_key_var.get().strip()
        if not key:
            messagebox.showwarning("Empty Key", "Please enter an API key.")
            return
        lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.startswith("OPENWEATHER_API_KEY"):
                lines[i] = "OPENWEATHER_API_KEY=%s\n" % key
                found = True
                break
        if not found:
            lines.append("\nOPENWEATHER_API_KEY=%s\n" % key)
        with open(".env", "w") as f:
            f.writelines(lines)
        self.api_client.api_key = key
        global API_KEY
        API_KEY = key
        ToastNotification(self, "API key saved. Restart to fully apply.", COLORS["accent2"])

    def _test_api(self):
        def _run():
            try:
                ok  = self.api_client.validate_key()
                msg = "API key valid!" if ok else "API key invalid."
                col = COLORS["accent2"] if ok else COLORS["accent3"]
                self.after(0, lambda: ToastNotification(self, msg, col))
            except Exception as ex:
                self.after(0, lambda: ToastNotification(
                    self, "Error: %s" % str(ex), COLORS["warm"]))
        threading.Thread(target=_run, daemon=True).start()

    def _on_refresh_change(self):
        if self.auto_refresh_job:
            self.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
        mins = self.auto_refresh_interval.get()
        if mins > 0 and self.current_weather:
            self._schedule_refresh(mins * 60 * 1000)

    def _schedule_refresh(self, ms):
        def _ref():
            if self.current_weather:
                self._search(city=self.current_weather.city)
            if self.auto_refresh_interval.get() > 0:
                self._schedule_refresh(self.auto_refresh_interval.get() * 60 * 1000)
        self.auto_refresh_job = self.after(ms, _ref)

    # ----------------------------------------------------------------
    # FAVORITES
    # ----------------------------------------------------------------

    def _toggle_favorite(self):
        if not self.current_weather:
            return
        city = self.current_weather.city
        if self.data_manager.is_favorite(city):
            self.data_manager.remove_favorite(city)
            self.add_fav_btn.configure(text="[+] Add Favorite")
            ToastNotification(self, "Removed %s from favorites." % city, COLORS["accent3"])
        else:
            self.data_manager.add_favorite(city)
            self.add_fav_btn.configure(text="[*] Saved!")
            ToastNotification(self, "Added %s to favorites." % city, COLORS["accent2"])

    def _show_favorites_window(self):
        win = tk.Toplevel(self)
        win.title("Favorites")
        win.configure(bg=COLORS["bg_dark"])
        win.geometry("300x380")
        win.transient(self)
        tk.Label(win, text="-- Favorite Cities --",
                 bg=COLORS["bg_dark"], fg=COLORS["accent"],
                 font=("Courier", 12, "bold")).pack(pady=14)
        lb = tk.Listbox(win, bg=COLORS["bg_card"], fg=COLORS["text_main"],
                        selectbackground=COLORS["accent"],
                        font=("Courier", 10), relief="flat",
                        borderwidth=0, activestyle="none")
        lb.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        for city in self.data_manager.favorites:
            lb.insert("end", "  " + city)

        def load():
            sel = lb.curselection()
            if sel:
                self.search_var.set(lb.get(sel[0]).strip())
                self._search()
                win.destroy()

        def remove():
            sel = lb.curselection()
            if sel:
                city = lb.get(sel[0]).strip()
                self.data_manager.remove_favorite(city)
                lb.delete(sel[0])

        btn_f = tk.Frame(win, bg=COLORS["bg_dark"])
        btn_f.pack(pady=6)
        tk.Button(btn_f, text="Load", bg=COLORS["accent"], fg=COLORS["bg_dark"],
                  relief="flat", font=("Courier", 9, "bold"), padx=14, cursor="hand2",
                  command=load).pack(side="left", padx=5)
        tk.Button(btn_f, text="Remove", bg=COLORS["accent3"], fg=COLORS["text_main"],
                  relief="flat", font=("Courier", 9), padx=14, cursor="hand2",
                  command=remove).pack(side="left", padx=5)

    # ----------------------------------------------------------------
    # THEME SYSTEM
    # ----------------------------------------------------------------

    def _toggle_theme(self):
        if COLORS["name"] == "Dark":
            self._switch_theme(LIGHT_THEME, "Light")
        else:
            self._switch_theme(DARK_THEME, "Dark")

    def _apply_theme_from_radio(self):
        if self.theme_name.get() == "Dark":
            self._switch_theme(DARK_THEME, "Dark")
        else:
            self._switch_theme(LIGHT_THEME, "Light")

    def _switch_theme(self, theme, name):
        apply_theme(theme)
        self.theme_name.set(name)
        next_lbl = "[ Light Mode ]" if name == "Dark" else "[ Dark Mode ]"
        self.theme_btn.configure(text=next_lbl)
        self._repaint_all()

    def _repaint_all(self):
        self.configure(bg=COLORS["bg_dark"])

        # Header
        self.header.configure(bg=COLORS["bg_panel"])
        self._header_logo.configure(bg=COLORS["bg_panel"],  fg=COLORS["accent"])
        self._header_title.configure(bg=COLORS["bg_panel"], fg=COLORS["text_main"])
        self._header_ver.configure(bg=COLORS["bg_panel"],   fg=COLORS["text_dim"])
        self._search_entry.configure(bg=COLORS["bg_dark"],  fg=COLORS["text_main"],
                                      insertbackground=COLORS["accent"])
        self.search_btn.configure(bg=COLORS["accent"], fg=COLORS["bg_dark"])
        self.theme_btn.configure(bg=COLORS["bg_card"],  fg=COLORS["accent4"])
        self._fav_btn.configure(bg=COLORS["bg_card"],   fg=COLORS["accent4"])
        for rb in self._unit_rbs:
            rb.configure(bg=COLORS["bg_panel"], fg=COLORS["text_sub"],
                         selectcolor=COLORS["bg_dark"],
                         activebackground=COLORS["bg_panel"],
                         activeforeground=COLORS["accent"])

        # Status bar
        self._status_bar.configure(bg=COLORS["bg_panel"])
        self._status_lbl.configure(bg=COLORS["bg_panel"], fg=COLORS["text_sub"])
        self._clock_lbl.configure(bg=COLORS["bg_panel"],  fg=COLORS["text_dim"])

        # Current tab hero
        self.cur_hero.configure(bg=COLORS["bg_panel"])
        for w in [self.cur_icon_lbl, self.cur_temp_lbl, self.cur_desc_lbl,
                  self.cur_city_lbl, self.cur_minmax_lbl, self.cur_feels_lbl,
                  self.cur_coord_lbl]:
            bg = COLORS["bg_panel"]
            if w == self.cur_icon_lbl:   fg = COLORS["accent"]
            elif w in (self.cur_temp_lbl,):    fg = COLORS["text_main"]
            elif w in (self.cur_desc_lbl, self.cur_minmax_lbl, self.cur_feels_lbl):
                fg = COLORS["text_sub"]
            else: fg = COLORS["text_dim"]
            w.configure(bg=bg, fg=fg)
        self.add_fav_btn.configure(bg=COLORS["bg_card"], fg=COLORS["accent4"])

        # Tab backgrounds
        self.tab_current.configure(bg=COLORS["bg_dark"])
        self.tab_forecast.configure(bg=COLORS["bg_dark"])
        self.tab_charts.configure(bg=COLORS["bg_dark"])
        self.tab_analysis.configure(bg=COLORS["bg_dark"])
        self.tab_history.configure(bg=COLORS["bg_dark"])
        self.tab_settings.configure(bg=COLORS["bg_dark"])
        self._cards_frame.configure(bg=COLORS["bg_dark"])

        # Forecast header + history title
        self._fc_header.configure(bg=COLORS["bg_dark"], fg=COLORS["text_sub"])
        self._hist_title.configure(bg=COLORS["bg_dark"], fg=COLORS["text_sub"])

        # Chart radio buttons
        for rb in self._chart_rbs:
            rb.configure(bg=COLORS["bg_dark"], fg=COLORS["text_sub"],
                         selectcolor=COLORS["bg_panel"],
                         activebackground=COLORS["bg_dark"],
                         activeforeground=COLORS["accent"])

        # ttk styles
        self._apply_ttk_styles()

        # Registered custom widgets
        REGISTRY.repaint_all()

        # Analysis labels
        for lbl in self._analysis_labels.values():
            lbl.configure(bg=COLORS["bg_dark"], fg=COLORS["text_main"])
        for kind, frm in self._analysis_frames:
            if kind == "div":
                frm.configure(bg=COLORS["border"])
            elif kind == "hdr":
                frm.configure(bg=COLORS["bg_dark"], fg=COLORS["accent"])
            elif kind == "grid":
                frm.configure(bg=COLORS["bg_dark"])

        # Rebuild forecast cards (they need their card bg updated)
        if self.forecast_entries:
            self._populate_forecast()

    # ----------------------------------------------------------------
    # SEARCH & FETCH
    # ----------------------------------------------------------------

    def _search(self, event=None, city=None):
        query = city or self.search_var.get().strip()
        if not query or query == "Enter city name...":
            messagebox.showwarning("Empty Search", "Please enter a city name.")
            return
        if self.loading:
            return
        self._set_loading(True, "Fetching weather for %s..." % query)
        units = self.units.get()
        threading.Thread(target=self._fetch_data, args=(query, units), daemon=True).start()

    def _fetch_data(self, city, units):
        try:
            weather  = self.api_client.get_current(city, units)
            forecast = self.api_client.get_forecast(city, units)
            self.after(0, lambda: self._on_data_loaded(weather, forecast, units))
        except Exception as e:
            self.after(0, lambda err=e: self._on_data_error(str(err)))

    def _on_data_loaded(self, weather, forecast, units):
        self.current_weather  = weather
        self.forecast_entries = forecast

        self._update_current_tab(weather, units)
        self._populate_forecast()
        self._update_charts()
        self._populate_analysis()

        self.data_manager.add_history(weather.city, weather, units)
        self._refresh_history_tree()

        fav = self.data_manager.is_favorite(weather.city)
        self.add_fav_btn.configure(text="[*] Saved!" if fav else "[+] Add Favorite")

        if weather.wind_speed > 0:
            self.wind_rose.set_wind(weather.wind_deg, weather.wind_speed)

        self._set_loading(False,
            "Updated: %s, %s  --  %s" % (
                weather.city, weather.country,
                datetime.datetime.now().strftime("%H:%M:%S")))
        self._on_refresh_change()

    def _on_data_error(self, error):
        self._set_loading(False, "Error: " + error)
        messagebox.showerror("Fetch Error",
                              "Could not retrieve weather data:\n" + error)

    def _on_unit_change(self):
        if self.current_weather:
            self._search(city=self.current_weather.city)

    def _update_current_tab(self, w, units):
        unit       = UNIT_LABELS[units]["temp"]
        speed_unit = UNIT_LABELS[units]["speed"]

        self.cur_icon_lbl.configure(text=w.icon)
        self.cur_temp_lbl.configure(text="%d %s" % (w.temp, unit))
        self.cur_desc_lbl.configure(text=w.description)
        self.cur_city_lbl.configure(
            text="%s, %s   Local: %s" % (w.city, w.country, w.local_time()))
        self.cur_minmax_lbl.configure(
            text="High: %d%s   Low: %d%s" % (w.temp_max, unit, w.temp_min, unit))
        self.cur_feels_lbl.configure(
            text="Feels like %d %s" % (w.feels_like, unit))
        self.cur_coord_lbl.configure(
            text="Lat %.2f  Lon %.2f" % (w.lat, w.lon))

        dp  = dew_point(w.temp, w.humidity)
        hi  = heat_index(w.temp, w.humidity)
        wc  = wind_chill(w.temp, w.wind_speed * 3.6)
        bft_num, bft_desc = beaufort_scale(w.wind_speed)

        self.stat_cards["humidity"].update_value("%d%%" % w.humidity)
        self.stat_cards["pressure"].update_value("%d hPa" % w.pressure)
        self.stat_cards["wind"].update_value(
            "%.1f %s  %s" % (w.wind_speed, speed_unit, w.wind_direction))
        self.stat_cards["visibility"].update_value("%.1f km" % w.visibility)
        self.stat_cards["clouds"].update_value("%d%%" % w.clouds)
        self.stat_cards["sunrise"].update_value(w.sunrise_time())
        self.stat_cards["sunset"].update_value(w.sunset_time())
        self.stat_cards["moon"].update_value(moon_phase(datetime.date.today()))
        self.stat_cards["dew"].update_value("%.1f %s" % (dp, unit))
        self.stat_cards["heat_idx"].update_value("%.1f %s" % (hi, unit))
        self.stat_cards["wind_chill"].update_value("%.1f %s" % (wc, unit))
        self.stat_cards["beaufort"].update_value("%d -- %s" % (bft_num, bft_desc))

    def _set_loading(self, state, msg=""):
        self.loading = state
        self.search_btn.configure(
            text="Loading..." if state else "Search",
            state="disabled" if state else "normal")
        if msg:
            self._status_lbl.configure(text=msg)

    def _warn_no_api_key(self):
        messagebox.showwarning(
            "API Key Missing",
            "No API key found!\n\n"
            "Create a .env file in the app folder with:\n\n"
            "    OPENWEATHER_API_KEY=your_key_here\n\n"
            "Free key at: openweathermap.org/api")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    app = WeatherApp()
    app.mainloop()


if __name__ == "__main__":
    main()