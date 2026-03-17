import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import threading
import sqlite3
import json
import math
from datetime import datetime, timedelta

# =====================================================================
# 1. DATABASE ENGINE (SQLite3)
# =====================================================================
class AppDatabase:
    def __init__(self, db_name="apex_weather.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                                key TEXT PRIMARY KEY, value TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                city TEXT, lat REAL, lon REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()
        # Insert defaults
        self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('units', 'metric')")
        self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'Dark')")
        self.conn.commit()

    def get_setting(self, key):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.cursor.fetchone()
        return res[0] if res else None

    def update_setting(self, key, value):
        self.cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def add_history(self, city, lat, lon):
        self.cursor.execute("INSERT INTO history (city, lat, lon) VALUES (?, ?, ?)", (city, lat, lon))
        self.conn.commit()

    def get_history(self, limit=5):
        self.cursor.execute("SELECT city, lat, lon FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

# =====================================================================
# 2. CUSTOM VECTOR ICON ENGINE (Pure Math Drawing)
# =====================================================================
class VectorIcon(tk.Canvas):
    def __init__(self, master, size=100, **kwargs):
        super().__init__(master, width=size, height=size, bg="#242424", highlightthickness=0, **kwargs)
        self.size = size
        self.center = size / 2

    def draw_sun(self):
        self.delete("all")
        c = self.center
        r = self.size * 0.25
        self.create_oval(c-r, c-r, c+r, c+r, fill="#FFD700", outline="#FFA500", width=2)
        for i in range(8):
            angle = i * (math.pi / 4)
            x1, y1 = c + math.cos(angle) * (r + 5), c + math.sin(angle) * (r + 5)
            x2, y2 = c + math.cos(angle) * (r + 15), c + math.sin(angle) * (r + 15)
            self.create_line(x1, y1, x2, y2, fill="#FFD700", width=3, capstyle="round")

    def draw_cloud(self):
        self.delete("all")
        c = self.center
        self.create_oval(c-30, c-10, c+10, c+30, fill="#E0E0E0", outline="")
        self.create_oval(c-10, c-25, c+30, c+25, fill="#E0E0E0", outline="")
        self.create_oval(c+10, c-5, c+40, c+25, fill="#E0E0E0", outline="")
        self.create_rectangle(c-20, c+5, c+30, c+30, fill="#E0E0E0", outline="")

    def draw_rain(self):
        self.draw_cloud()
        c = self.center
        self.create_line(c-15, c+35, c-20, c+45, fill="#4DA6FF", width=2)
        self.create_line(c+5, c+35, c, c+45, fill="#4DA6FF", width=2)
        self.create_line(c+25, c+35, c+20, c+45, fill="#4DA6FF", width=2)

    def set_icon(self, wmo_code):
        if wmo_code in [0, 1]: self.draw_sun()
        elif wmo_code in [2, 3, 45, 48]: self.draw_cloud()
        elif wmo_code >= 50: self.draw_rain()
        else: self.draw_cloud()

# =====================================================================
# 3. INTERACTIVE GRAPH ENGINE
# =====================================================================
class InteractiveGraph(tk.Canvas):
    def __init__(self, master, width=700, height=200, **kwargs):
        super().__init__(master, width=width, height=height, bg="#242424", highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.data = []
        self.labels = []
        self.bind("<Motion>", self.on_hover)
        self.tooltip = None

    def plot(self, data, labels):
        self.delete("all")
        self.data, self.labels = data, labels
        if not data: return
        
        pad_y = 40
        pad_x = 30
        min_v, max_v = min(data) - 2, max(data) + 2
        v_range = max_v - min_v if max_v != min_v else 1
        x_step = (self.w - 2*pad_x) / (len(data) - 1)
        
        self.points = []
        for i, val in enumerate(data):
            x = pad_x + i * x_step
            y = self.h - pad_y - ((val - min_v) / v_range * (self.h - 2*pad_y))
            self.points.append((x, y, val, labels[i]))

        # Draw Grid & Curve
        for i in range(4):
            y_line = pad_y + i * ((self.h - 2*pad_y)/3)
            self.create_line(pad_x, y_line, self.w-pad_x, y_line, fill="#333", dash=(2, 4))

        for i in range(len(self.points) - 1):
            x1, y1, _, _ = self.points[i]
            x2, y2, _, _ = self.points[i+1]
            self.create_line(x1, y1, x2, y2, fill="#3B8ED0", width=3, smooth=True)
            self.create_oval(x1-4, y1-4, x1+4, y1+4, fill="#1F6AA5", outline="#FFF", width=1, tags="node")
            
        # Draw last node
        lx, ly, _, _ = self.points[-1]
        self.create_oval(lx-4, ly-4, lx+4, ly+4, fill="#1F6AA5", outline="#FFF", width=1, tags="node")

    def on_hover(self, event):
        self.delete("tooltip")
        for x, y, val, lbl in self.points:
            if abs(event.x - x) < 10 and abs(event.y - y) < 10:
                self.create_rectangle(x-20, y-35, x+25, y-10, fill="#111", outline="#3B8ED0", tags="tooltip")
                self.create_text(x+2, y-22, text=f"{lbl}: {val}°", fill="#FFF", font=("Arial", 9), tags="tooltip")
                break

# =====================================================================
# 4. CUSTOM UI WIDGETS
# =====================================================================
class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title, value="--", subtitle="", **kwargs):
        super().__init__(master, corner_radius=15, fg_color="#1E1E1E", border_width=1, border_color="#2A2A2A", **kwargs)
        self.lbl_title = ctk.CTkLabel(self, text=title, font=("Arial", 11, "bold"), text_color="#3B8ED0")
        self.lbl_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.lbl_val = ctk.CTkLabel(self, text=value, font=("Arial", 28, "bold"), text_color="#FFFFFF")
        self.lbl_val.pack(anchor="w", padx=15)
        
        self.lbl_sub = ctk.CTkLabel(self, text=subtitle, font=("Arial", 10), text_color="#888888")
        self.lbl_sub.pack(anchor="w", padx=15, pady=(0, 15))

    def update_data(self, val, sub=""):
        self.lbl_val.configure(text=val)
        if sub: self.lbl_sub.configure(text=sub)

# =====================================================================
# 5. MAIN APPLICATION
# =====================================================================
class ApexWeather(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = AppDatabase()
        
        # Core Setup
        self.title("ApexWeather | Enterprise Edition")
        self.geometry("1300x850")
        self.minsize(1100, 700)
        ctk.set_appearance_mode(self.db.get_setting("theme"))
        ctk.set_default_color_theme("blue")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.current_lat = None
        self.current_lon = None
        
        self.build_sidebar()
        self.build_main_container()
        self.build_dashboard()
        self.build_forecast_view()
        self.build_aqi_view()
        
        self.show_frame("dashboard")
        self.load_history()

    # -----------------------------------------------------------------
    # UI CONSTRUCTION
    # -----------------------------------------------------------------
    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#111111")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.sidebar, text="APEX WEATHER", font=("Impact", 28), text_color="#3B8ED0").pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text="System Online", font=("Arial", 10), text_color="#00FF00").pack(pady=(0, 30))

        self.btn_dash = self.create_nav_btn("📊 Dashboard", "dashboard")
        self.btn_fore = self.create_nav_btn("📅 7-Day Forecast", "forecast")
        self.btn_aqi = self.create_nav_btn("🍃 Air Quality", "aqi")

        # History Frame
        ctk.CTkLabel(self.sidebar, text="RECENT SEARCHES", font=("Arial", 10, "bold"), text_color="#666").pack(pady=(30, 10), anchor="w", padx=20)
        self.history_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=10)

        # Settings
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self.toggle_theme)
        if self.db.get_setting("theme") == "Dark": self.theme_switch.select()
        self.theme_switch.pack(side="bottom", pady=20, padx=20, anchor="w")

    def create_nav_btn(self, text, view_name):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", anchor="w", 
                            hover_color="#222", font=("Arial", 14), command=lambda: self.show_frame(view_name))
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def build_main_container(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Search Bar Top
        self.top_bar = ctk.CTkFrame(self.main_container, height=70, fg_color="#1A1A1A", corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(self.top_bar, textvariable=self.search_var, placeholder_text="Enter City Name or Coordinates...", 
                                         width=400, height=40, font=("Arial", 14), border_width=1)
        self.search_entry.pack(side="left", padx=30, pady=15)
        self.search_entry.bind("<Return>", lambda e: self.start_fetch_thread())

        self.btn_search = ctk.CTkButton(self.top_bar, text="ANALYZE", width=120, height=40, command=self.start_fetch_thread)
        self.btn_search.pack(side="left")

        # Container for changing views
        self.views_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.views_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.views_container.grid_rowconfigure(0, weight=1)
        self.views_container.grid_columnconfigure(0, weight=1)

    def build_dashboard(self):
        self.frm_dash = ctk.CTkScrollableFrame(self.views_container, fg_color="transparent")
        
        # Hero Section
        self.hero = ctk.CTkFrame(self.frm_dash, corner_radius=20, fg_color="#242424")
        self.hero.pack(fill="x", pady=(0, 20))
        
        self.icon_canvas = VectorIcon(self.hero, size=150)
        self.icon_canvas.pack(side="left", padx=30, pady=20)
        
        info_frame = ctk.CTkFrame(self.hero, fg_color="transparent")
        info_frame.pack(side="left", pady=30, fill="both", expand=True)
        
        self.lbl_city = ctk.CTkLabel(info_frame, text="Awaiting Sync...", font=("Arial", 42, "bold"))
        self.lbl_city.pack(anchor="w")
        self.lbl_temp = ctk.CTkLabel(info_frame, text="--°", font=("Arial", 64, "bold"), text_color="#3B8ED0")
        self.lbl_temp.pack(anchor="w", pady=5)
        self.lbl_desc = ctk.CTkLabel(info_frame, text="Please enter a location to begin atmospheric analysis.", font=("Arial", 16, "italic"), text_color="#AAA")
        self.lbl_desc.pack(anchor="w")

        # Graph Section
        ctk.CTkLabel(self.frm_dash, text="24-HOUR TEMPERATURE TRAJECTORY", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.graph = InteractiveGraph(self.frm_dash)
        self.graph.pack(fill="x", pady=(0, 20))

        # Metrics Grid
        self.grid_frame = ctk.CTkFrame(self.frm_dash, fg_color="transparent")
        self.grid_frame.pack(fill="x")
        self.grid_frame.columnconfigure((0,1,2,3), weight=1)
        
        self.cards = {
            "humidity": MetricCard(self.grid_frame, "HUMIDITY", "--"),
            "wind": MetricCard(self.grid_frame, "WIND SPEED", "--"),
            "pressure": MetricCard(self.grid_frame, "PRESSURE", "--"),
            "uv": MetricCard(self.grid_frame, "UV INDEX", "--")
        }
        self.cards["humidity"].grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.cards["wind"].grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.cards["pressure"].grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.cards["uv"].grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    def build_forecast_view(self):
        self.frm_fore = ctk.CTkScrollableFrame(self.views_container, fg_color="transparent")
        ctk.CTkLabel(self.frm_fore, text="7-DAY ATMOSPHERIC FORECAST", font=("Arial", 24, "bold")).pack(anchor="w", pady=20)
        self.fore_container = ctk.CTkFrame(self.frm_fore, fg_color="transparent")
        self.fore_container.pack(fill="both", expand=True)

    def build_aqi_view(self):
        self.frm_aqi = ctk.CTkFrame(self.views_container, fg_color="transparent")
        ctk.CTkLabel(self.frm_aqi, text="AIR QUALITY INDEX (AQI)", font=("Arial", 24, "bold")).pack(anchor="w", pady=20)
        
        self.aqi_hero = ctk.CTkFrame(self.frm_aqi, height=200, corner_radius=20, fg_color="#242424")
        self.aqi_hero.pack(fill="x", pady=10)
        
        self.lbl_aqi_val = ctk.CTkLabel(self.aqi_hero, text="--", font=("Arial", 80, "bold"), text_color="#10B981")
        self.lbl_aqi_val.pack(pady=(30, 0))
        self.lbl_aqi_desc = ctk.CTkLabel(self.aqi_hero, text="Awaiting Data", font=("Arial", 18))
        self.lbl_aqi_desc.pack(pady=(0, 30))

        self.aqi_grid = ctk.CTkFrame(self.frm_aqi, fg_color="transparent")
        self.aqi_grid.pack(fill="x", pady=20)
        self.aqi_grid.columnconfigure((0,1,2), weight=1)
        
        self.cards["pm10"] = MetricCard(self.aqi_grid, "PM 10", "--", "Particulate Matter")
        self.cards["pm25"] = MetricCard(self.aqi_grid, "PM 2.5", "--", "Fine Particulates")
        self.cards["co"] = MetricCard(self.aqi_grid, "CARBON MONOXIDE", "--", "CO Gas")
        
        self.cards["pm10"].grid(row=0, column=0, padx=5, sticky="ew")
        self.cards["pm25"].grid(row=0, column=1, padx=5, sticky="ew")
        self.cards["co"].grid(row=0, column=2, padx=5, sticky="ew")

    # -----------------------------------------------------------------
    # ROUTING & LOGIC
    # -----------------------------------------------------------------
    def show_frame(self, name):
        for frm in [self.frm_dash, self.frm_fore, self.frm_aqi]:
            frm.grid_forget()
            
        if name == "dashboard": self.frm_dash.grid(row=0, column=0, sticky="nsew")
        elif name == "forecast": self.frm_fore.grid(row=0, column=0, sticky="nsew")
        elif name == "aqi": self.frm_aqi.grid(row=0, column=0, sticky="nsew")

    def toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == 1 else "Light"
        ctk.set_appearance_mode(mode)
        self.db.update_setting("theme", mode)

    def load_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        hist = self.db.get_history()
        for city, lat, lon in hist:
            btn = ctk.CTkButton(self.history_frame, text=city, fg_color="transparent", anchor="w",
                                hover_color="#333", command=lambda c=city: self.quick_search(c))
            btn.pack(fill="x", pady=2)

    def quick_search(self, city):
        self.search_var.set(city)
        self.start_fetch_thread()

    # -----------------------------------------------------------------
    # API ENGINE (Multi-threaded)
    # -----------------------------------------------------------------
    def start_fetch_thread(self):
        query = self.search_var.get().strip()
        if not query: return
        self.btn_search.configure(state="disabled", text="ANALYZING...")
        threading.Thread(target=self.fetch_all_data, args=(query,), daemon=True).start()

    def fetch_all_data(self, query):
        try:
            # 1. Geocoding API
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=1"
            geo_res = requests.get(geo_url).json()
            if "results" not in geo_res:
                self.after(0, lambda: messagebox.showerror("Error", "Location not found in geospatial database."))
                return

            loc = geo_res["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            city_name = f"{loc['name']}, {loc.get('country', '')}"
            
            self.db.add_history(loc['name'], lat, lon)

            # 2. Primary Weather API (Complex Dataset)
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,surface_pressure,uv_index&daily=weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset&timezone=auto"
            w_data = requests.get(w_url).json()

            # 3. Air Quality API (Secondary Source)
            aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=european_aqi,pm10,pm2_5,carbon_monoxide&timezone=auto"
            aqi_data = requests.get(aqi_url).json()

            self.after(0, lambda: self.update_ui(city_name, w_data, aqi_data))
            self.after(0, self.load_history)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Network Fault", str(e)))
        finally:
            self.after(0, lambda: self.btn_search.configure(state="normal", text="ANALYZE"))

    def update_ui(self, city, w_data, aqi_data):
        curr = w_data["current_weather"]
        hr = w_data["hourly"]
        dl = w_data["daily"]
        aqi_curr = aqi_data["current"]

        # Dashboard Update
        self.lbl_city.configure(text=city.upper())
        self.lbl_temp.configure(text=f"{int(curr['temperature'])}°C")
        self.lbl_desc.configure(text=self.get_wmo_desc(curr['weathercode']))
        self.icon_canvas.set_icon(curr['weathercode'])

        # Cards
        self.cards["humidity"].update_data(f"{hr['relativehumidity_2m'][0]}%")
        self.cards["wind"].update_data(f"{curr['windspeed']} km/h")
        self.cards["pressure"].update_data(f"{hr['surface_pressure'][0]} hPa")
        self.cards["uv"].update_data(f"{hr['uv_index'][0]}")

        # Graph
        t_data = hr['temperature_2m'][:24]
        t_lbls = [str(i)+":00" for i in range(24)]
        self.graph.plot(t_data, t_lbls)

        # Forecast Update
        for widget in self.fore_container.winfo_children(): widget.destroy()
        for i in range(7):
            row = ctk.CTkFrame(self.fore_container, fg_color="#1E1E1E", corner_radius=10)
            row.pack(fill="x", pady=5, padx=20)
            
            date_obj = datetime.strptime(dl['time'][i], "%Y-%m-%d")
            day_str = date_obj.strftime("%A, %b %d")
            
            ctk.CTkLabel(row, text=day_str, font=("Arial", 16, "bold"), width=150, anchor="w").pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(row, text=self.get_wmo_desc(dl['weathercode'][i]), width=200, anchor="w").pack(side="left", padx=20)
            ctk.CTkLabel(row, text=f"Max: {dl['temperature_2m_max'][i]}°C", text_color="#FF6B6B", font=("Arial", 14, "bold")).pack(side="left", padx=20)
            ctk.CTkLabel(row, text=f"Min: {dl['temperature_2m_min'][i]}°C", text_color="#4DA6FF", font=("Arial", 14, "bold")).pack(side="left", padx=20)

        # AQI Update
        aqi_val = aqi_curr['european_aqi']
        self.lbl_aqi_val.configure(text=str(aqi_val))
        if aqi_val < 50:
            self.lbl_aqi_val.configure(text_color="#10B981")
            self.lbl_aqi_desc.configure(text="Air Quality is Good. Safe for outdoor activities.")
        elif aqi_val < 100:
            self.lbl_aqi_val.configure(text_color="#F59E0B")
            self.lbl_aqi_desc.configure(text="Air Quality is Moderate. Acceptable for most individuals.")
        else:
            self.lbl_aqi_val.configure(text_color="#EF4444")
            self.lbl_aqi_desc.configure(text="Air Quality is Poor. Sensitive groups should stay indoors.")

        self.cards["pm10"].update_data(f"{aqi_curr['pm10']} µg/m³")
        self.cards["pm25"].update_data(f"{aqi_curr['pm2_5']} µg/m³")
        self.cards["co"].update_data(f"{aqi_curr['carbon_monoxide']} µg/m³")

    def get_wmo_desc(self, code):
        mapping = {
            0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing Rime Fog", 51: "Light Drizzle", 53: "Moderate Drizzle",
            61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain", 71: "Slight Snow",
            73: "Moderate Snow", 80: "Rain Showers", 81: "Violent Rain Showers",
            95: "Thunderstorm", 96: "Thunderstorm with Hail"
        }
        return mapping.get(code, "Unknown Atmospheric Condition")

if __name__ == "__main__":
    app = ApexWeather()
    app.mainloop()