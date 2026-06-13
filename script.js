// ===== 天气图标映射 (文本图标) =====
const ICON_MAP = {
    "sunny":        "☀️",
    "partly-cloudy": "⛅",
    "cloudy":        "☁️",
    "overcast":      "☁️",
    "fog":           "🌫️",
    "drizzle":       "🌦️",
    "rain":          "🌧️",
    "heavy-rain":    "🌧️",
    "snow":          "❄️",
    "heavy-snow":    "❄️",
    "showers":       "🌦️",
    "thunderstorm":  "⛈️",
    "unknown":       "🌡️",
};

// ===== 工具函数 =====
function formatTime(isoStr) {
    if (!isoStr) return "--";
    const d = new Date(isoStr + "T08:00:00");
    return d.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false });
}
function formatHour(isoStr) {
    const d = new Date(isoStr);
    return d.getHours() + ":00";
}
function formatDateCN(isoStr) {
    if (!isoStr) return "--";
    const d = new Date(isoStr + "T08:00:00");
    return `${d.getMonth() + 1}/${d.getDate()}`;
}
function dayName(isoStr) {
    const d = new Date(isoStr + "T08:00:00");
    const names = ["週日", "週一", "週二", "週三", "週四", "週五", "週六"];
    return names[d.getDay()];
}

// ===== 数据加载 =====
let hourlyChart = null;
let tempChart = null;
let forecastData = null;

async function fetchJSON(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        console.error(`Failed to fetch ${url}:`, e);
        return null;
    }
}

async function refreshAll() {
    document.getElementById("updateTime").textContent = "更新中...";
    const [current, forecast, hourly, aqi] = await Promise.all([
        fetchJSON("/api/current"),
        fetchJSON("/api/forecast"),
        fetchJSON("/api/hourly"),
        fetchJSON("/api/air_quality"),
    ]);

    const now = new Date();
    document.getElementById("updateTime").textContent =
        `最后更新: ${now.toLocaleTimeString("zh-TW")}`;
    document.getElementById("dataTimestamp").textContent =
        `数据时间: ${now.toLocaleString("zh-TW")}`;

    if (current) renderCurrent(current);
    if (forecast) { forecastData = forecast; renderForecast(forecast); renderSunCard(forecast); }
    if (hourly) { renderHourlyChart(hourly); renderHourlyTable(hourly); renderHourlyPreview(hourly); }
    if (aqi) renderAQI(aqi);
}

// ===== 实时天气 =====
function renderCurrent(data) {
    const icon = ICON_MAP[data.weather_icon] || "🌡️";
    const windDir = getWindDir(data.wind_direction);

    document.getElementById("currentCard").innerHTML = `
        <div class="current-main">
            <div class="current-temp-group">
                <div class="weather-icon-lg">${icon}</div>
                <div class="current-temp">${Math.round(data.temperature)}°</div>
                <div class="current-desc">${data.weather_desc}</div>
                <div class="current-feels">體感 ${Math.round(data.feels_like)}°C</div>
            </div>
            <div class="current-details">
                <div class="detail-item">
                    <div class="detail-label">濕度</div>
                    <div class="detail-value">${data.humidity}<span class="detail-unit">%</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">風速</div>
                    <div class="detail-value">${data.wind_speed}<span class="detail-unit">m/s</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">風向</div>
                    <div class="detail-value">${windDir}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">風力</div>
                    <div class="detail-value">${data.wind_level}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">氣壓</div>
                    <div class="detail-value">${Math.round(data.pressure)}<span class="detail-unit">hPa</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">紫外線</div>
                    <div class="detail-value">${data.uv_index}</div>
                </div>
            </div>
        </div>
    `;
}

function getWindDir(deg) {
    const dirs = ["北", "北北東", "東北", "東北東", "東", "東南東", "東南", "南南東",
                   "南", "南南西", "西南", "西南西", "西", "西北西", "西北", "北北西"];
    const idx = Math.round(deg / 22.5) % 16;
    return dirs[idx] || "無";
}

// ===== 空气质量 =====
function renderAQI(data) {
    const color = data.aqi_color || "#50aa50";
    document.getElementById("aqiCard").innerHTML = `
        <div class="aqi-display">
            <div class="aqi-circle" style="background:${color}">${data.aqi_eu}</div>
            <div style="font-size:16px;font-weight:600;color:#e2e8f0">${data.aqi_level}</div>
            <div style="font-size:12px;color:#64748b">欧洲空气质量指数</div>
        </div>
        <div class="aqi-detail-grid">
            <div class="aqi-detail-item"><span>PM2.5</span><span>${data.pm2_5?.toFixed(1) ?? "--"} µg/m³</span></div>
            <div class="aqi-detail-item"><span>PM10</span><span>${data.pm10?.toFixed(1) ?? "--"} µg/m³</span></div>
            <div class="aqi-detail-item"><span>O₃</span><span>${data.o3?.toFixed(1) ?? "--"} µg/m³</span></div>
            <div class="aqi-detail-item"><span>NO₂</span><span>${data.no2?.toFixed(1) ?? "--"} µg/m³</span></div>
            <div class="aqi-detail-item"><span>CO</span><span>${data.co?.toFixed(0) ?? "--"} µg/m³</span></div>
            <div class="aqi-detail-item"><span>SO₂</span><span>${data.so2?.toFixed(1) ?? "--"} µg/m³</span></div>
        </div>
    `;
}

// ===== 逐时迷你预览 =====
function renderHourlyPreview(data) {
    const hours = data.hours.slice(0, 8);
    let html = '<div class="hourly-mini">';
    hours.forEach(h => {
        const icon = ICON_MAP[h.weather_icon] || "🌡️";
        html += `
            <div class="hourly-mini-item">
                <div class="time">${formatHour(h.time)}</div>
                <div class="icon-s">${icon}</div>
                <div class="temp">${Math.round(h.temperature)}°</div>
                <div class="rain">${h.precip_prob}%</div>
            </div>`;
    });
    html += '</div>';
    document.getElementById("hourlyPreview").innerHTML = html;
}

// ===== 日出日落 =====
function renderSunCard(forecast) {
    if (!forecast.days || forecast.days.length === 0) return;
    const today = forecast.days[0];
    const sunrise = formatTime(today.sunrise);
    const sunset = formatTime(today.sunset);

    document.getElementById("sunCard").innerHTML = `
        <div class="sun-display">
            <div style="font-size:13px;color:#64748b">${today.date}</div>
            <div class="sun-row">
                <div class="sun-item">
                    <div class="sun-icon">🌅</div>
                    <div class="sun-time">${sunrise}</div>
                    <div class="sun-label">日出</div>
                </div>
                <div class="sun-divider"></div>
                <div class="sun-item">
                    <div class="sun-icon">🌇</div>
                    <div class="sun-time">${sunset}</div>
                    <div class="sun-label">日落</div>
                </div>
            </div>
        </div>
    `;
}

// ===== 七日预报 =====
function renderForecast(data) {
    if (!data.days) return;
    let html = '<div class="forecast-grid">';
    data.days.forEach(day => {
        const icon = ICON_MAP[day.weather_icon] || "🌡️";
        html += `
            <div class="forecast-day">
                <div class="day-name">${dayName(day.date)}</div>
                <div class="day-date">${formatDateCN(day.date)}</div>
                <div class="day-icon">${icon}</div>
                <div class="day-desc">${day.weather_desc}</div>
                <div class="day-temps">
                    <span>${Math.round(day.temp_max)}°</span>
                    <span class="day-temp-lo">${Math.round(day.temp_min)}°</span>
                </div>
                <div class="day-rain">💧 ${day.precip_prob}%</div>
            </div>`;
    });
    html += '</div>';
    document.getElementById("forecastGrid").innerHTML = html;
}

// ===== 48小时逐时图表 =====
function renderHourlyChart(data) {
    const ctx = document.getElementById("hourlyChart").getContext("2d");
    if (hourlyChart) hourlyChart.destroy();

    const labels = data.hours.map(h => formatHour(h.time));
    const temps = data.hours.map(h => h.temperature);
    const rainProbs = data.hours.map(h => h.precip_prob);

    hourlyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "温度 (°C)",
                    data: temps,
                    borderColor: "#f59e0b",
                    backgroundColor: "rgba(245, 158, 11, 0.1)",
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y",
                    pointRadius: 1,
                    pointHoverRadius: 5,
                },
                {
                    label: "降雨機率 (%)",
                    data: rainProbs,
                    borderColor: "#60a5fa",
                    backgroundColor: "rgba(96, 165, 250, 0.15)",
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y1",
                    pointRadius: 1,
                    pointHoverRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "#94a3b8", usePointStyle: true, padding: 20 }
                },
            },
            scales: {
                x: {
                    ticks: { color: "#64748b", maxTicksLimit: 24, maxRotation: 0 },
                    grid: { color: "rgba(51,65,85,0.3)" },
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    title: { display: true, text: "°C", color: "#f59e0b" },
                    ticks: { color: "#94a3b8" },
                    grid: { color: "rgba(51,65,85,0.3)" },
                },
                y1: {
                    type: "linear",
                    display: true,
                    position: "right",
                    title: { display: true, text: "%", color: "#60a5fa" },
                    ticks: { color: "#94a3b8", max: 100 },
                    grid: { drawOnChartArea: false },
                },
            },
        },
    });
}

// ===== 逐时表格 =====
function renderHourlyTable(data) {
    let html = '<table class="hourly-table"><thead><tr>';
    html += '<th>时间</th><th>天气</th><th>温度</th><th>體感</th><th>降雨</th><th>濕度</th><th>風速</th>';
    html += '</tr></thead><tbody>';
    data.hours.forEach(h => {
        const icon = ICON_MAP[h.weather_icon] || "🌡️";
        const rainClass = h.precip_prob > 50 ? "rain-high" : "";
        html += `<tr>
            <td>${formatHour(h.time)}</td>
            <td>${icon} ${h.weather_desc}</td>
            <td>${Math.round(h.temperature)}°</td>
            <td>${Math.round(h.feels_like)}°</td>
            <td class="${rainClass}">${h.precip_prob}%</td>
            <td>${h.humidity}%</td>
            <td>${h.wind_speed} m/s</td>
        </tr>`;
    });
    html += '</tbody></table>';
    document.getElementById("hourlyTable").innerHTML = html;
}

// ===== 启动 =====
document.addEventListener("DOMContentLoaded", refreshAll);
  
