# ⛅ WeatherScope Pro

> A feature-rich weather forecast and analysis desktop application built with **pure Python** and **Tkinter** — no external dependencies.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Lines](https://img.shields.io/badge/Lines%20of%20Code-1100%2B-purple?style=flat-square)
![API](https://img.shields.io/badge/API-OpenWeatherMap-orange?style=flat-square)

---

## ✨ Features

### 🌡 Current Weather
- Real-time temperature, feels-like, min/max
- Weather condition with emoji icons
- 12 detailed stat cards: humidity, pressure, wind, visibility, cloud cover, sunrise, sunset, moon phase, dew point, heat index, wind chill, Beaufort scale

### 📅 5-Day Forecast
- 40 forecast slots (every 3 hours)
- Grouped by day with time, icon, temperature, humidity, precipitation probability, and wind speed

### 📊 Interactive Charts
- **Line Chart** — temperature, humidity, precipitation %, wind speed, or pressure over time
- **Bar Chart** — precipitation probability for the next 16 slots
- **Wind Rose** — custom compass canvas showing wind direction and speed
- All charts are drawn using Tkinter Canvas (no matplotlib needed)

### 🔬 Deep Analysis
- Temperature stats: average, max, min, range across all 40 forecast slots
- Derived metrics: dew point, heat index (Steadman formula), wind chill (Environment Canada formula)
- Wind analysis: average, max, Beaufort scale rating, direction in compass notation
- Precipitation stats: average chance, total rainy slots (>50%), estimated total rainfall (mm)
- Sun data: sunrise/sunset times, day length in hours/minutes, approximate moon phase
- Forecast summary: best day (least rain), worst day (most rain), temperature trend (warming/stable/cooling)
- Comfort assessment and **clothing recommendation**

### 🕑 Search History
- Automatically stores the last 100 searches
- Double-click any entry to reload that city instantly
- Export full history to CSV
- One-click clear all history

### ★ Favorites
- Save any city as a favorite
- Load favorites from a dedicated popup window
- Persisted to `favorites.json` across sessions

### ⚙ Settings
- Enter and save your API key at runtime (no restart needed)
- Test API connectivity with one click
- Auto-refresh: set automatic re-fetch every 5, 10, or 30 minutes
- Units: Metric (°C / m/s), Imperial (°F / mph), Standard (Kelvin)

### 🖥 UI/UX
- Dark theme throughout with a GitHub-inspired color palette
- Tabbed interface for clean navigation
- Toast notifications for actions
- Live clock in status bar
- Scrollable panels for forecast and analysis

---

## 📸 Screenshot

```
┌──────────────────────────────────────────────────────────┐
│ ⛅ WeatherScope Pro v1.0    [Search Bar]   °C °F K  ★Fav │
├──────────────────────────────────────────────────────────┤
│  🌡 Current │ 📅 Forecast │ 📊 Charts │ 🔬 Analysis │ ... │
├──────────────────────────────────────────────────────────┤
│   ☀️  28°C    Sunny        ↑31° ↓24°  Feels 30°         │
│ ┌────────┐┌────────┐┌────────┐┌────────┐                 │
│ │💧 72%  ││📊1013hPa││💨3.2m/s││👁 10km │                 │
│ └────────┘└────────┘└────────┘└────────┘                 │
│ ┌────────┐┌────────┐┌────────┐┌────────┐                 │
│ │🌅 06:12││🌇 18:47││🌙 Wax. ││💦 21°C │                 │
│ └────────┘└────────┘└────────┘└────────┘                 │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/weatherscope-pro.git
cd weatherscope-pro
```

### 2. Get a Free API Key

1. Visit [openweathermap.org](https://openweathermap.org/api)
2. Sign up for a free account
3. Navigate to **API Keys** in your dashboard
4. Copy your key (free tier includes current weather + 5-day forecast)

### 3. Set Up Your `.env` File

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder:

```env
OPENWEATHER_API_KEY=your_actual_api_key_here
```

### 4. Run the App

```bash
python weather_app.py
```

That's it — no `pip install` required. 🎉

---

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| **Python**  | 3.7.6 or higher |
| **Tkinter** | Included with standard Python |
| **OS**      | Windows, macOS, Linux |
| **Internet**| Required for API calls |
| **pip installs** | **None** — zero dependencies |

### Linux Only (if tkinter is missing)

```bash
sudo apt-get install python3-tk    # Debian/Ubuntu
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch
```

---

## 📁 Project Structure

```
weatherscope-pro/
│
├── weather_app.py          # Main application (1100+ lines)
├── .env                    # Your API key (not committed to git)
├── .env.example            # Template for .env
├── requirements.txt        # No pip installs — documents stdlib usage
├── README.md               # This file
│
├── weather_history.json    # Auto-created: search history
└── favorites.json          # Auto-created: favorite cities
```

---

## 🏗 Architecture

```
WeatherApp (tk.Tk)
│
├── WeatherAPIClient          # urllib-based API calls to OpenWeatherMap
│   ├── get_current()         # /data/2.5/weather
│   └── get_forecast()        # /data/2.5/forecast (40 slots, 3hr)
│
├── WeatherData               # Parsed model for current weather
├── ForecastEntry             # Parsed model for one 3-hour slot
│
├── DataManager               # JSON-backed history + favorites
│
├── Custom Widgets
│   ├── LineChart (Canvas)    # Smooth filled line chart
│   ├── BarChart (Canvas)     # Rounded bar chart
│   ├── WindRose (Canvas)     # Compass with wind arrow
│   ├── StatCard (Frame)      # Info card with icon + value
│   ├── ScrollableFrame       # Scrollable container
│   └── ToastNotification     # Ephemeral popup message
│
└── Tabs
    ├── Current               # Hero display + 12 stat cards
    ├── Forecast              # 40-slot 5-day grid
    ├── Charts                # Line + Bar + Wind Rose
    ├── Analysis              # 25+ derived metrics
    ├── History               # Treeview + CSV export
    └── Settings              # API key, auto-refresh, units
```

---

## 📐 Science Behind the Metrics

### Dew Point (Magnus Formula)
```
γ = (a·T / (b+T)) + ln(RH/100)
Td = b·γ / (a−γ)   where a=17.27, b=237.7
```

### Heat Index (Steadman, Rothfusz)
Uses the official NWS formula — accounts for humidity's effect on perceived temperature.

### Wind Chill (Environment Canada)
```
WC = 13.12 + 0.6215·T − 11.37·V^0.16 + 0.3965·T·V^0.16
```
Valid for T ≤ 10°C and wind ≥ 4.8 km/h.

### Beaufort Scale
12-point scale from Calm (0) to Hurricane (12), mapped from wind speed in m/s.

### Moon Phase
Approximate calculation based on days elapsed since a known New Moon (Jan 6, 2000), modulo 29 days.

---

## 🗂 Data Persistence

| File | Contents | Format |
|------|----------|--------|
| `.env` | API key | Key=Value |
| `weather_history.json` | Last 100 searches | JSON array |
| `favorites.json` | Saved cities | JSON array |

All files are stored in the same directory as `weather_app.py`.

---

## 🔑 OpenWeatherMap API Usage

This app uses the **free tier** of OpenWeatherMap:

| Endpoint | Used For |
|----------|----------|
| `/data/2.5/weather` | Current conditions |
| `/data/2.5/forecast` | 5-day / 3-hour forecast |

The free tier allows **60 calls/minute** and **1,000,000 calls/month** — more than enough for personal use.

---

## 🛠 Customization

### Change Theme Colors
All colors are defined in the `COLORS` dictionary at the top of `weather_app.py`:

```python
COLORS = {
    "bg_dark":   "#0d1117",   # Main background
    "accent":    "#58a6ff",   # Primary accent (blue)
    "accent2":   "#3fb950",   # Green
    "accent3":   "#f78166",   # Red/orange
    ...
}
```

### Add More Cities to Favorites
Edit `favorites.json` directly:

```json
["London", "Tokyo", "New York", "Mumbai"]
```

### Extend Auto-Refresh Intervals
Add new options in `_build_settings_tab()`:

```python
for mins, label in [(0, "Off"), (5, "5 min"), (15, "15 min"), (60, "1 hour")]:
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- **OpenWeatherMap** for the free weather API
- **Python Tkinter** for the built-in GUI toolkit
- **Environment Canada** and **NOAA/NWS** for meteorological formulas

---

*Built with ❤️ in Python — no external dependencies, just the standard library.*