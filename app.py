#!/usr/bin/env python3
"""台北市气象平台 - 基于 Open-Meteo 免费 API + 模拟数据回退"""

import requests
import json
import random
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 台北市坐标
TAIPEI_LAT = 25.0330
TAIPEI_LON = 121.5654
TZ = "Asia/Taipei"

# API 可用标志
API_AVAILABLE = True

def check_api():
    """检测 Open-Meteo API 是否可达"""
    global API_AVAILABLE
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": TAIPEI_LAT, "longitude": TAIPEI_LON,
            "current": "temperature_2m", "timezone": TZ
        }, timeout=5)
        API_AVAILABLE = r.status_code == 200
    except:
        API_AVAILABLE = False
    return API_AVAILABLE

# 启动时检测一次
check_api()

# WMO Weather Code → 中文描述 + 图标
WMO_MAP = {
    0:  ("晴", "sunny"),
    1:  ("晴時多雲", "partly-cloudy"),
    2:  ("多雲", "cloudy"),
    3:  ("陰天", "overcast"),
    45: ("霧", "fog"),
    48: ("霧凇", "fog"),
    51: ("小毛毛雨", "drizzle"),
    53: ("毛毛雨", "drizzle"),
    55: ("大毛毛雨", "drizzle"),
    61: ("小雨", "rain"),
    63: ("中雨", "rain"),
    65: ("大雨", "heavy-rain"),
    71: ("小雪", "snow"),
    73: ("中雪", "snow"),
    75: ("大雪", "heavy-snow"),
    80: ("陣雨", "showers"),
    81: ("大陣雨", "showers"),
    82: ("豪陣雨", "showers"),
    95: ("雷陣雨", "thunderstorm"),
    96: ("雷陣雨伴冰雹", "thunderstorm"),
    99: ("強雷陣雨伴冰雹", "thunderstorm"),
}

# 风力等级 (Beaufort scale, m/s)
def wind_level(ms):
    if ms < 0.3:  return "無風", 0
    if ms < 1.6:  return "軟風", 1
    if ms < 3.4:  return "輕風", 2
    if ms < 5.5:  return "微風", 3
    if ms < 8.0:  return "和風", 4
    if ms < 10.8: return "清風", 5
    if ms < 13.9: return "強風", 6
    if ms < 17.2: return "疾風", 7
    if ms < 20.8: return "大風", 8
    if ms < 24.5: return "烈風", 9
    if ms < 28.5: return "狂風", 10
    if ms < 32.7: return "暴風", 11
    return "颶風", 12


def weather_desc(code):
    return WMO_MAP.get(code, ("未知", "unknown"))


def fetch_open_meteo(endpoint="forecast", **params):
    """调用 Open-Meteo API"""
    if not API_AVAILABLE:
        return None
    base = f"https://api.open-meteo.com/v1/{endpoint}"
    defaults = {
        "latitude": TAIPEI_LAT,
        "longitude": TAIPEI_LON,
        "timezone": TZ,
    }
    defaults.update(params)
    try:
        r = requests.get(base, params=defaults, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Open-Meteo Error] {e}")
        return None


# ============================================================
#  模拟数据生成 (API 不可用时使用)
# ============================================================
def mock_current():
    """生成台北6月实时天气模拟数据"""
    now = datetime.now()
    base_temp = 30.0 + random.uniform(-3, 3)  # 台北6月典型温度
    feels_like = base_temp + random.uniform(2, 5)
    code = random.choice([0, 1, 1, 2, 3, 3, 61, 95])
    desc, icon = weather_desc(code)
    wl_name, wl_level = wind_level(random.uniform(0.5, 6.0))
    return {
        "time": now.strftime("%Y-%m-%dT%H:%M"),
        "temperature": round(base_temp, 1),
        "feels_like": round(feels_like, 1),
        "humidity": random.randint(60, 90),
        "weather_code": code,
        "weather_desc": desc,
        "weather_icon": icon,
        "wind_speed": round(random.uniform(0.5, 5.5), 1),
        "wind_direction": random.randint(0, 360),
        "wind_level": wl_name,
        "wind_level_num": wl_level,
        "pressure": random.randint(1003, 1013),
        "uv_index": random.randint(3, 11),
        "precipitation": round(random.uniform(0, 3), 1),
    }


def mock_forecast():
    """生成7日预报模拟数据"""
    days = []
    now = datetime.now()
    codes_pool = [0, 0, 1, 1, 2, 2, 3, 3, 61, 63, 80, 95]
    for i in range(7):
        d = now + timedelta(days=i)
        base_t = 31.0 + random.uniform(-3, 3)
        code = random.choice(codes_pool)
        desc, icon = weather_desc(code)
        sunrise = d.replace(hour=5, minute=random.randint(0, 10)).strftime("%Y-%m-%dT%H:%M")
        sunset = d.replace(hour=18, minute=random.randint(35, 45)).strftime("%Y-%m-%dT%H:%M")
        days.append({
            "date": d.strftime("%Y-%m-%d"),
            "temp_max": round(base_t + random.uniform(0, 3), 1),
            "temp_min": round(base_t - random.uniform(5, 8), 1),
            "precip_prob": random.randint(10, 80),
            "precip_sum": round(random.uniform(0, 12), 1),
            "weather_code": code,
            "weather_desc": desc,
            "weather_icon": icon,
            "sunrise": sunrise,
            "sunset": sunset,
            "uv_index": random.randint(4, 11),
            "wind_speed": round(random.uniform(1, 8), 1),
        })
    return {"days": days}


def mock_hourly():
    """生成48小时逐时预报模拟数据"""
    hours = []
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    base_temp = 30.0
    for i in range(48):
        h_time = now + timedelta(hours=i)
        hour = h_time.hour
        # 模拟昼夜温度变化
        if 0 <= hour < 6:
            temp = base_temp - 5 + random.uniform(-1, 1)
        elif 6 <= hour < 12:
            temp = base_temp + (hour - 6) * 1.0 + random.uniform(-1, 1)
        elif 12 <= hour < 18:
            temp = base_temp + 5 - (hour - 12) * 0.5 + random.uniform(-1, 1)
        else:
            temp = base_temp + 1 - (hour - 18) * 0.6 + random.uniform(-1, 1)

        code = random.choice([0, 1, 1, 2, 2, 3, 3, 61, 95])
        desc, icon = weather_desc(code)
        hours.append({
            "time": h_time.strftime("%Y-%m-%dT%H:%M"),
            "temperature": round(temp, 1),
            "feels_like": round(temp + random.uniform(2, 5), 1),
            "precip_prob": max(0, min(100, int(30 + random.gauss(0, 25)))),
            "weather_code": code,
            "weather_desc": desc,
            "weather_icon": icon,
            "wind_speed": round(random.uniform(0.5, 5.5), 1),
            "humidity": random.randint(60, 90),
        })
    return {"hours": hours}


def mock_air_quality():
    """生成空气质量模拟数据"""
    now = datetime.now()
    aqi = random.randint(15, 75)
    if aqi <= 20: level = ("優", "#50aa50")
    elif aqi <= 40: level = ("良好", "#a0d050")
    elif aqi <= 60: level = ("中等", "#f0e050")
    elif aqi <= 80: level = ("對敏感族群不健康", "#f0a030")
    elif aqi <= 100: level = ("不健康", "#e05050")
    else: level = ("非常不健康", "#a030a0")
    return {
        "time": now.strftime("%Y-%m-%dT%H:%M"),
        "aqi_eu": aqi,
        "aqi_us": random.randint(10, 120),
        "aqi_level": level[0],
        "aqi_color": level[1],
        "pm10": round(random.uniform(10, 60), 1),
        "pm2_5": round(random.uniform(5, 35), 1),
        "co": round(random.uniform(100, 500), 0),
        "no2": round(random.uniform(5, 40), 1),
        "so2": round(random.uniform(1, 10), 1),
        "o3": round(random.uniform(20, 80), 1),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/current")
def api_current():
    """实时天气"""
    data = fetch_open_meteo(
        current=[
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "weather_code", "wind_speed_10m", "wind_direction_10m",
            "pressure_msl", "uv_index", "precipitation"
        ]
    )
    if not data or "current" not in data:
        return jsonify(mock_current())

    c = data["current"]
    code = c["weather_code"]
    desc, icon = weather_desc(code)
    wl_name, wl_level = wind_level(c.get("wind_speed_10m", 0))

    return jsonify({
        "time": c["time"],
        "temperature": c["temperature_2m"],
        "feels_like": c["apparent_temperature"],
        "humidity": c["relative_humidity_2m"],
        "weather_code": code,
        "weather_desc": desc,
        "weather_icon": icon,
        "wind_speed": c.get("wind_speed_10m", 0),
        "wind_direction": c.get("wind_direction_10m", 0),
        "wind_level": wl_name,
        "wind_level_num": wl_level,
        "pressure": c.get("pressure_msl", 0),
        "uv_index": c.get("uv_index", 0),
        "precipitation": c.get("precipitation", 0),
    })


@app.route("/api/forecast")
def api_forecast():
    """七日预报"""
    data = fetch_open_meteo(
        daily=[
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_probability_max", "weather_code",
            "sunrise", "sunset", "uv_index_max",
            "wind_speed_10m_max", "precipitation_sum"
        ],
        forecast_days=7
    )
    if not data or "daily" not in data:
        return jsonify(mock_forecast())

    d = data["daily"]
    days = []
    for i in range(len(d["time"])):
        code = d["weather_code"][i]
        desc, icon = weather_desc(code)
        days.append({
            "date": d["time"][i],
            "temp_max": d["temperature_2m_max"][i],
            "temp_min": d["temperature_2m_min"][i],
            "precip_prob": d["precipitation_probability_max"][i],
            "precip_sum": d.get("precipitation_sum", [0]*7)[i],
            "weather_code": code,
            "weather_desc": desc,
            "weather_icon": icon,
            "sunrise": d.get("sunrise", [None]*7)[i],
            "sunset": d.get("sunset", [None]*7)[i],
            "uv_index": d.get("uv_index_max", [0]*7)[i],
            "wind_speed": d.get("wind_speed_10m_max", [0]*7)[i],
        })
    return jsonify({"days": days})


@app.route("/api/hourly")
def api_hourly():
    """48小时逐时预报"""
    data = fetch_open_meteo(
        hourly=[
            "temperature_2m", "precipitation_probability",
            "weather_code", "wind_speed_10m",
            "relative_humidity_2m", "apparent_temperature"
        ],
        forecast_hours=48
    )
    if not data or "hourly" not in data:
        return jsonify(mock_hourly())

    h = data["hourly"]
    hours = []
    for i in range(len(h["time"])):
        code = h["weather_code"][i]
        desc, icon = weather_desc(code)
        hours.append({
            "time": h["time"][i],
            "temperature": h["temperature_2m"][i],
            "feels_like": h["apparent_temperature"][i],
            "precip_prob": h["precipitation_probability"][i],
            "weather_code": code,
            "weather_desc": desc,
            "weather_icon": icon,
            "wind_speed": h["wind_speed_10m"][i],
            "humidity": h["relative_humidity_2m"][i],
        })
    return jsonify({"hours": hours})


@app.route("/api/air_quality")
def api_air_quality():
    """空气质量 (Open-Meteo Air Quality API)"""
    data = fetch_open_meteo(
        endpoint="air-quality",
        current=[
            "european_aqi", "us_aqi",
            "pm10", "pm2_5",
            "carbon_monoxide", "nitrogen_dioxide",
            "sulphur_dioxide", "ozone"
        ]
    )
    if not data or "current" not in data:
        return jsonify(mock_air_quality())

    c = data["current"]
    aqi = c.get("european_aqi", 0)

    # EAQI 等级
    if aqi <= 20: level = ("優", "#50aa50")
    elif aqi <= 40: level = ("良好", "#a0d050")
    elif aqi <= 60: level = ("中等", "#f0e050")
    elif aqi <= 80: level = ("對敏感族群不健康", "#f0a030")
    elif aqi <= 100: level = ("不健康", "#e05050")
    else: level = ("非常不健康", "#a030a0")

    return jsonify({
        "time": c["time"],
        "aqi_eu": aqi,
        "aqi_us": c.get("us_aqi", 0),
        "aqi_level": level[0],
        "aqi_color": level[1],
        "pm10": c.get("pm10", 0),
        "pm2_5": c.get("pm2_5", 0),
        "co": c.get("carbon_monoxide", 0),
        "no2": c.get("nitrogen_dioxide", 0),
        "so2": c.get("sulphur_dioxide", 0),
        "o3": c.get("ozone", 0),
    })


if __name__ == "__main__":
    print("台北市气象平台启动中...")
    print("访问地址: http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)
