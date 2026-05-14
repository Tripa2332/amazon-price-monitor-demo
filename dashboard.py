"""
Dashboard — Amazon Price Monitor
Dark/industrial UI con cancelación, progreso real, presets y carga desde .env.

Uso:
    pip install streamlit plotly python-dotenv
    streamlit run dashboard.py
"""

import glob
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import dotenv_values

# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Price Monitor", page_icon="📡", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #080810; color: #e2e8f0; }

[data-testid="stSidebar"] { background-color: #0d0d18 !important; border-right: 1px solid #1a1a2e; }
[data-testid="stSidebar"] * { color: #b0b8c8 !important; }
[data-testid="stSidebar"] .stMarkdown p {
    color: #f97316 !important; font-family: 'Space Mono', monospace !important;
    font-size: 0.62rem !important; letter-spacing: 0.18em !important; text-transform: uppercase !important;
}

.monitor-header {
    font-family: 'Space Mono', monospace; font-size: 2.2rem; font-weight: 700;
    background: linear-gradient(120deg, #f97316 0%, #fbbf24 60%, #fb923c 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    line-height: 1.1; letter-spacing: -0.04em;
}
.monitor-sub {
    font-family: 'Space Mono', monospace; font-size: 0.63rem; letter-spacing: 0.22em;
    color: #2d3748; text-transform: uppercase; margin-top: 4px; margin-bottom: 1.6rem;
}

.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1.2rem; }
.metric-card {
    background: #0f0f1c; border: 1px solid #1a1a2e; border-radius: 10px;
    padding: 1rem 1.2rem; position: relative; overflow: hidden;
}
.metric-card::after {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #f97316, #fbbf24);
}
.metric-label { font-size: 0.6rem; letter-spacing: 0.15em; text-transform: uppercase; color: #374151; font-family: 'Space Mono', monospace; margin-bottom: 5px; }
.metric-value { font-family: 'Space Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
.metric-hint  { font-size: 0.68rem; color: #22c55e; margin-top: 3px; }

.run-btn > button {
    background: linear-gradient(135deg, #f97316, #ea580c) !important;
    color: white !important; border: none !important; border-radius: 7px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.75rem !important;
    letter-spacing: 0.08em !important; padding: 0.55rem 1.4rem !important;
    box-shadow: 0 0 20px rgba(249,115,22,0.2) !important; transition: all 0.18s !important;
    width: 100%;
}
.run-btn > button:hover { transform: translateY(-2px) !important; box-shadow: 0 0 32px rgba(249,115,22,0.4) !important; }

.cancel-btn > button {
    background: linear-gradient(135deg, #7f1d1d, #dc2626) !important;
    color: white !important; border: none !important; border-radius: 7px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.75rem !important;
    letter-spacing: 0.08em !important; padding: 0.55rem 1.4rem !important;
    box-shadow: 0 0 20px rgba(220,38,38,0.2) !important; transition: all 0.18s !important;
    width: 100%;
}
.cancel-btn > button:hover { box-shadow: 0 0 32px rgba(220,38,38,0.4) !important; }

.stTabs [data-baseweb="tab-list"] { background: #0f0f1c; border-radius: 8px; padding: 3px; gap: 3px; border: 1px solid #1a1a2e; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #4a5568 !important; border-radius: 6px !important; font-family: 'Space Mono', monospace !important; font-size: 0.66rem !important; letter-spacing: 0.07em !important; }
.stTabs [aria-selected="true"] { background: #1a1a2e !important; color: #f97316 !important; }

hr { border-color: #1a1a2e !important; }

.offer-row {
    background: linear-gradient(90deg, rgba(249,115,22,0.05), transparent);
    border-left: 3px solid #f97316; padding: 10px 14px;
    border-radius: 0 8px 8px 0; margin-bottom: 8px;
}
.offer-badge {
    display: inline-block; background: #f97316; color: #000;
    font-family: 'Space Mono', monospace; font-size: 0.63rem; font-weight: 700;
    padding: 1px 8px; border-radius: 20px; margin-bottom: 4px;
}
.sec-label {
    font-family: 'Space Mono', monospace; font-size: 0.58rem; letter-spacing: 0.2em;
    text-transform: uppercase; color: #f97316; margin: 1.1rem 0 0.4rem;
}
.progress-wrap {
    background: #0f0f1c; border: 1px solid #1a1a2e; border-radius: 10px;
    padding: 1rem 1.4rem; margin-bottom: 0.8rem;
}
.progress-title {
    font-family: 'Space Mono', monospace; font-size: 0.68rem;
    color: #f97316; letter-spacing: 0.1em; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center;
}
.progress-bar-bg { background: #1a1a2e; border-radius: 4px; height: 8px; overflow: hidden; margin-bottom: 8px; }
.progress-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #f97316, #fbbf24); transition: width 0.5s ease; }
.progress-stats { font-size: 0.68rem; color: #4a5568; font-family: 'Space Mono', monospace; }
.progress-item { font-size: 0.68rem; color: #64748b; font-family: 'DM Sans', sans-serif; margin-top: 6px; font-style: italic; }

.env-badge {
    display: inline-block; background: #0f2a1a; color: #22c55e;
    font-family: 'Space Mono', monospace; font-size: 0.58rem;
    padding: 1px 7px; border-radius: 4px; border: 1px solid #166534; margin-left: 6px;
}
.preset-info { font-size: 0.7rem; color: #4a5568; font-family: 'Space Mono', monospace; margin-top: 2px; }

.stTextInput input, .stTextArea textarea {
    background: #0f0f1c !important; border: 1px solid #1a1a2e !important;
    color: #e2e8f0 !important; border-radius: 7px !important;
}
.stDataFrame { border: 1px solid #1a1a2e !important; border-radius: 10px !important; }
.log-box {
    background: #0a0a14; border: 1px solid #1a1a2e; border-radius: 8px;
    padding: 10px 14px; font-family: 'Space Mono', monospace; font-size: 0.65rem;
    color: #4a5568; max-height: 200px; overflow-y: auto; margin-top: 8px;
    line-height: 1.6;
}
.log-line-ok  { color: #22c55e; }
.log-line-err { color: #ef4444; }
.log-line-warn { color: #f59e0b; }
.log-line-info { color: #64748b; }
</style>
""", unsafe_allow_html=True)


# ── Archivos de estado (persisten entre reruns via disco) ──────────────────────
PROGRESS_FILE = Path(".monitor_progress.json")
LOG_FILE      = Path(".monitor_log.txt")
PID_FILE      = Path(".monitor_pid")


def leer_progreso() -> dict:
    try:
        return json.loads(PROGRESS_FILE.read_text()) if PROGRESS_FILE.exists() else {}
    except Exception:
        return {}

def leer_log(ultimas: int = 35) -> list[str]:
    try:
        if not LOG_FILE.exists():
            return []
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-ultimas:]
    except Exception:
        return []

def leer_pid() -> int | None:
    try:
        return int(PID_FILE.read_text()) if PID_FILE.exists() else None
    except Exception:
        return None

def proceso_vivo(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False

def limpiar_archivos_estado():
    for f in [PROGRESS_FILE, LOG_FILE, PID_FILE]:
        try:
            f.unlink()
        except FileNotFoundError:
            pass


# ── Presets ────────────────────────────────────────────────────────────────────
PRESETS = {
    "— manual —": [],
    "💻 Laptops & PCs": [
        "notebook lenovo thinkpad", "notebook dell xps", "notebook hp pavilion",
        "notebook asus vivobook", "notebook acer aspire", "macbook air m2",
        "notebook gaming msi", "notebook gaming asus rog", "notebook razer blade",
        "mini pc intel nuc", "desktop pc gaming", "all in one pc",
        "procesador intel core i7", "procesador amd ryzen 7", "procesador amd ryzen 5",
        "placa madre asus", "placa madre gigabyte", "gabinete pc gaming",
        "fuente poder 650w", "cooler cpu noctua",
    ],
    "🖥️ Monitores & Periféricos": [
        "monitor samsung 27 4k", "monitor lg 27 ips", "monitor dell ultrasharp",
        "monitor gaming 144hz", "monitor gaming 240hz", "monitor ultrawide 34",
        "teclado mecanico redragon", "teclado mecanico logitech", "teclado mecanico keychron",
        "mouse logitech mx master", "mouse razer deathadder", "mouse gaming corsair",
        "mousepad xl gaming", "webcam logitech c920", "webcam 4k streaming",
        "hub usb c", "docking station", "soporte monitor dual",
        "microfono blue yeti", "microfono streaming usb",
    ],
    "🎧 Audio & Headphones": [
        "auriculares sony wh1000xm5", "auriculares bose quietcomfort 45",
        "auriculares apple airpods pro", "auriculares samsung galaxy buds",
        "auriculares jabra evolve", "auriculares gaming hyperx cloud",
        "auriculares gaming steelseries arctis", "auriculares sennheiser hd",
        "parlante jbl charge 5", "parlante bose soundlink revolve",
        "parlante sonos one", "barra de sonido samsung",
        "auriculares true wireless sony wf", "auriculares true wireless jabra elite",
        "amplificador auriculares fiio",
    ],
    "📱 Smartphones & Tablets": [
        "iphone 15 pro", "iphone 15", "iphone 14",
        "samsung galaxy s24 ultra", "samsung galaxy s24", "samsung galaxy a55",
        "google pixel 8", "motorola edge 50", "xiaomi 14",
        "oneplus 12", "nothing phone 2",
        "tablet samsung galaxy tab s9", "ipad pro m4",
        "ipad air m2", "tablet lenovo tab p12",
        "smartwatch apple watch series 9", "smartwatch samsung galaxy watch 6",
        "smartwatch garmin forerunner 265",
    ],
    "📷 Fotografía & Video": [
        "camara sony alpha a7 iv", "camara canon eos r50", "camara nikon z30",
        "camara fujifilm xt5", "camara gopro hero 12",
        "lente 50mm sony fe", "lente 35mm canon rf",
        "estabilizador dji om 6", "drone dji mini 4 pro",
        "tripode profesional carbono", "luz led ring light",
        "capturadora video elgato 4k", "camara streaming logitech brio 4k",
        "memoria sd sandisk extreme 128gb", "disco externo ssd 2tb portátil",
    ],
    "🎮 Gaming": [
        "playstation 5 slim", "xbox series x", "nintendo switch oled",
        "joystick ps5 dualsense", "joystick xbox elite series 2",
        "silla gamer secretlab titan", "silla gamer dxracer formula",
        "escritorio gamer motorizado", "headset gaming astro a50",
        "monitor gaming 1ms 165hz 27", "teclado gaming razer huntsman",
        "mouse gaming razer viper v3", "alfombra gaming xl extended",
        "steam deck oled", "capturadora elgato hd60 x",
        "refrigeracion liquida corsair h150i", "ram ddr5 32gb corsair",
        "ssd nvme 1tb samsung 990 pro", "gpu rtx 4070 super", "gpu rx 7800 xt",
    ],
    "🏠 Hogar & Smart Home": [
        "smart tv samsung 55 neo qled", "smart tv lg oled 55 c3", "smart tv sony 65 bravia",
        "smart tv 43 4k hdr", "fire tv stick 4k max",
        "aire acondicionado split inverter 3000", "purificador aire dyson tp09",
        "aspiradora robot roomba j9", "aspiradora robot xiaomi s10",
        "microondas samsung 28l", "horno electrico conveccion",
        "cafetera nespresso vertuo", "cafetera philips 3200 lattego",
        "freidora aire philips xxl", "robot cocina cecofry",
        "lampara inteligente philips hue", "enchufe inteligente wifi",
        "camara seguridad exterior 4k", "timbre video ring pro",
        "termostato inteligente nest",
    ],
    "💪 Fitness & Deportes": [
        "cinta de correr plegable bluetooth", "bicicleta estatica smart",
        "remo indoor concept2 model d", "pesas rusas kettlebell 16kg",
        "mancuernas ajustables bowflex 552", "banco pesas ajustable incline",
        "colchoneta yoga premium 6mm", "rodillo espuma foam roller trigger",
        "smartwatch deportivo garmin fenix 7", "smartwatch polar vantage v3",
        "auriculares deporte jabra elite active", "botella termica hydro flask 32oz",
        "mochila trail running salomon", "monitor frecuencia cardiaca polar h10",
        "theragun percusión masajes",
    ],
    "🛋️ Muebles & Oficina": [
        "escritorio standing desk motorizado", "escritorio esquinero madera",
        "silla ergonomica herman miller aeron", "silla ergonomica steelcase leap",
        "soporte laptop ajustable aluminio", "soporte monitor brazo articulado",
        "organizador cables escritorio", "luz monitor led usb",
        "pizarra blanca magnética", "cajonera archivero metal",
        "estante industrial madera metal", "lampara escritorio led regulable",
        "alfombra vinilica oficina", "reposapiés ergonómico ajustable",
        "teclado ergonomico microsoft sculpt", "mouse ergonomico logitech mx vertical",
    ],
    "🔋 Almacenamiento & Redes": [
        "disco ssd interno 1tb samsung 870", "disco ssd interno 2tb crucial",
        "disco ssd nvme m2 1tb wd black", "disco duro externo 4tb seagate",
        "pendrive 128gb usb 3.2 samsung", "lector tarjetas sd usb c",
        "memoria ram 16gb ddr4 3200", "memoria ram 32gb ddr5 5600",
        "bateria portatil 20000mah anker", "cargador rapido 65w gan",
        "cable usb c 240w certificado", "adaptador usb c hub 10 en 1",
        "router wifi 6 ax asus", "router mesh tp link deco",
        "nas synology ds223", "ups bateria respaldo 1500va",
    ],
}

PLOTLY = dict(
    paper_bgcolor="#080810", plot_bgcolor="#0f0f1c",
    font=dict(color="#64748b", family="DM Sans"), gridcolor="#1a1a2e",
)
ORANGE_SCALE = ["#1a1a2e", "#7c3a00", "#f97316", "#fbbf24"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def cargar_reporte() -> pd.DataFrame:
    archivos = sorted(glob.glob("amazon_monitor_*.xlsx"), reverse=True)
    return pd.read_excel(archivos[0]) if archivos else pd.DataFrame()

def ultimo_archivo() -> str:
    archivos = sorted(glob.glob("amazon_monitor_*.xlsx"), reverse=True)
    return archivos[0] if archivos else ""

def fmt(n: float) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}k"
    return str(int(n))

def leer_env() -> dict:
    return dotenv_values(".env") if Path(".env").exists() else {}

def guardar_env(datos: dict):
    Path(".env").write_text("\n".join(f'{k}={v}' for k, v in datos.items() if v) + "\n")

def colorear_log(line: str) -> str:
    l = line.lower()
    if any(x in l for x in ["error", "exception", "traceback", "failed"]):
        return f'<span class="log-line-err">{line}</span>'
    if any(x in l for x in ["warning", "warn", "timeout", "bloqueo"]):
        return f'<span class="log-line-warn">{line}</span>'
    if any(x in l for x in ["✓", "completado", "✅", "encontrado", "procesado"]):
        return f'<span class="log-line-ok">{line}</span>'
    return f'<span class="log-line-info">{line}</span>'

# ── Wrapper script que escribe progreso a archivo ──────────────────────────────
WRAPPER_SCRIPT = """
import subprocess, sys, json, re, os
from pathlib import Path

PROGRESS_FILE = Path(".monitor_progress.json")
LOG_FILE      = Path(".monitor_log.txt")
PID_FILE      = Path(".monitor_pid")

PID_FILE.write_text(str(os.getpid()))
LOG_FILE.write_text("")

proc = subprocess.Popen(
    [sys.executable, "-u", "monitor_aws.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, bufsize=1, env=dict(os.environ),
)

progress = {"current": 0, "total": int(os.environ.get("TOTAL_PRODUCTOS", "1")),
            "ultimo": "", "status": "running"}

with open(LOG_FILE, "a", encoding="utf-8") as log:
    for line in proc.stdout:
        line = line.rstrip()
        log.write(line + "\\n")
        log.flush()

        m = re.search(r'completados?:\\s*(\\d+)/(\\d+)', line, re.IGNORECASE)
        if m:
            progress["current"] = int(m.group(1))
            progress["total"]   = int(m.group(2))

        m2 = re.search(r'Buscado:\\s*(.+?)\\s*---', line)
        if m2:
            progress["ultimo"] = m2.group(1).strip()

        PROGRESS_FILE.write_text(json.dumps(progress))

proc.wait()
progress["status"] = "done"
PROGRESS_FILE.write_text(json.dumps(progress))
try:
    PID_FILE.unlink()
except FileNotFoundError:
    pass
"""


# ── Cargar .env ────────────────────────────────────────────────────────────────
env_actual         = leer_env()
env_api_key        = env_actual.get("SCRAPER_API_KEY", "")
env_telegram_token = env_actual.get("TELEGRAM_BOT_TOKEN", "")
env_telegram_chat  = env_actual.get("TELEGRAM_CHAT_ID", "")
env_descuento      = int(env_actual.get("DESCUENTO_MINIMO", "20"))


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    env_loaded = bool(env_api_key)
    if env_loaded:
        st.markdown(f'⚙ API & Notificaciones <span class="env-badge">desde .env</span>', unsafe_allow_html=True)
    else:
        st.markdown("⚙ API & Notificaciones")

    api_key        = st.text_input("ScraperAPI Key",     value=env_api_key,        type="password", placeholder="scraperapi.com")
    telegram_token = st.text_input("Telegram Bot Token", value=env_telegram_token, type="password")
    telegram_chat  = st.text_input("Telegram Chat ID",   value=env_telegram_chat)

    if st.button("💾 Guardar en .env", use_container_width=True):
        guardar_env({
            "SCRAPER_API_KEY":    api_key,
            "TELEGRAM_BOT_TOKEN": telegram_token,
            "TELEGRAM_CHAT_ID":   telegram_chat,
            "DESCUENTO_MINIMO":   str(env_descuento),
        })
        st.success("Guardado ✓")

    st.markdown("🎛 Parámetros")
    descuento_alerta = st.slider("Descuento mínimo alerta (%)", 5, 80, env_descuento)
    max_pages        = st.slider("Páginas por producto",  1, 5, 2)
    max_workers      = st.slider("Búsquedas en paralelo", 1, 8, 4)

    st.markdown("🔭 Filtros de visualización")
    solo_descuento = st.toggle("Solo productos con descuento", False)
    precio_min     = st.number_input("Precio mín. USD", 0, value=0, step=5)
    precio_max     = st.number_input("Precio máx. USD (0 = sin límite)", 0, value=0, step=10)
    top_n          = st.slider("Top N mejores ofertas", 5, 50, 15)

    st.markdown("📋 Productos")
    preset_sel = st.selectbox("Preset de categoría", list(PRESETS.keys()))
    if preset_sel != "— manual —":
        st.markdown(f'<div class="preset-info">{len(PRESETS[preset_sel])} productos</div>', unsafe_allow_html=True)

    productos_txt = st.text_area(
        "Editá o agregá productos",
        height=200,
        value="\n".join(PRESETS[preset_sel]) if preset_sel != "— manual —" else
              "\n".join(["notebook lenovo","monitor samsung 27","auriculares sony",
                         "mouse logitech","disco ssd 1tb","iphone 15"]),
    )

    st.markdown("🏷 Etiqueta del reporte")
    nombre_cliente = st.text_input(
        "Nombre / cliente (opcional)",
        placeholder="ej: juan, tienda_xyz, gaming_mayo",
        help="Se agrega al nombre del Excel: amazon_monitor_YYYYMMDD_HHMM_juan.xlsx",
    )

    st.markdown("📂 Cargar reporte anterior")
    reporte_upload = st.file_uploader("Subir .xlsx", type=["xlsx"])


# ── Datos ──────────────────────────────────────────────────────────────────────
if reporte_upload:
    df_raw  = pd.read_excel(reporte_upload)
    archivo = reporte_upload.name
else:
    archivo = ultimo_archivo()
    df_raw  = cargar_reporte()

df = df_raw.copy()
if not df.empty:
    if solo_descuento and "Descuento %" in df.columns:
        df = df[df["Descuento %"] > 0]
    if precio_min > 0 and "Precio oferta (USD)" in df.columns:
        df = df[df["Precio oferta (USD)"] >= precio_min]
    if precio_max > 0 and "Precio oferta (USD)" in df.columns:
        df = df[df["Precio oferta (USD)"] <= precio_max]


# ── Header ─────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([4, 1])
with hc1:
    st.markdown('<div class="monitor-header">📡 PRICE MONITOR</div>', unsafe_allow_html=True)
    st.markdown('<div class="monitor-sub">Amazon · Real-time price intelligence · ARS/USD</div>', unsafe_allow_html=True)
with hc2:
    st.markdown(f"""
    <div style="text-align:right; padding-top:1.4rem;">
        <div style="font-family:Space Mono,monospace; font-size:0.6rem; color:#2d3748; text-transform:uppercase; letter-spacing:0.15em;">{datetime.now().strftime('%d %b %Y')}</div>
        <div style="font-family:Space Mono,monospace; font-size:1rem; color:#4a5568;">{datetime.now().strftime('%H:%M')}</div>
        {"<div style='font-size:0.58rem; color:#1e293b; font-family:Space Mono,monospace; margin-top:2px;'>"+archivo+"</div>" if archivo else ""}
    </div>""", unsafe_allow_html=True)


# ── Métricas ───────────────────────────────────────────────────────────────────
n_total    = len(df)
n_ofertas  = int((df["Descuento %"] >= descuento_alerta).sum()) if not df.empty and "Descuento %" in df.columns else 0
avg_precio = f"${df['Precio oferta (USD)'].mean():.0f}" if not df.empty and "Precio oferta (USD)" in df.columns else "—"
max_desc   = f"{int(df['Descuento %'].max())}%" if not df.empty and "Descuento %" in df.columns and df["Descuento %"].max() > 0 else "—"
dolar_blue = f"${df['Dólar blue'].iloc[0]:,.0f}" if not df.empty and "Dólar blue" in df.columns else "—"

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card">
    <div class="metric-label">Resultados</div>
    <div class="metric-value">{fmt(n_total)}</div>
    <div class="metric-hint">productos encontrados</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Ofertas ≥{descuento_alerta}%</div>
    <div class="metric-value">{n_ofertas}</div>
    <div class="metric-hint">descuento relevante</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Precio promedio</div>
    <div class="metric-value">{avg_precio}</div>
    <div class="metric-hint">USD · todos los productos</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Dólar blue</div>
    <div class="metric-value">{dolar_blue}</div>
    <div class="metric-hint">mayor descuento: {max_desc}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Estado del proceso ─────────────────────────────────────────────────────────
pid_actual  = leer_pid()
corriendo   = proceso_vivo(pid_actual)
progreso    = leer_progreso()

productos_lista = [p.strip() for p in productos_txt.splitlines() if p.strip()]

# ── Botones Ejecutar / Cancelar ────────────────────────────────────────────────
btn_col, prog_col = st.columns([1, 3])

with btn_col:
    if not corriendo:
        st.markdown('<div class="run-btn">', unsafe_allow_html=True)
        ejecutar = st.button("▶  EJECUTAR MONITOREO", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        cancelar = False
    else:
        st.markdown('<div class="cancel-btn">', unsafe_allow_html=True)
        cancelar = st.button("⏹  CANCELAR", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        ejecutar = False

# Lanzar
if ejecutar:
    if not api_key:
        st.error("Ingresá tu ScraperAPI Key en la barra lateral.")
    else:
        limpiar_archivos_estado()
        pd.DataFrame({"producto": productos_lista}).to_csv("productos.csv", index=False)

        # Escribir wrapper script temporalmente
        wrapper_path = Path("._monitor_wrapper.py")
        wrapper_path.write_text(WRAPPER_SCRIPT)

        env = {
            **os.environ,
            "SCRAPER_API_KEY":    api_key,
            "DESCUENTO_MINIMO":   str(descuento_alerta),
            "TOTAL_PRODUCTOS":    str(len(productos_lista)),
            "NOMBRE_REPORTE":     nombre_cliente.strip().replace(" ", "_") if nombre_cliente.strip() else "",
        }
        if telegram_token: env["TELEGRAM_BOT_TOKEN"] = telegram_token
        if telegram_chat:  env["TELEGRAM_CHAT_ID"]   = telegram_chat

        subprocess.Popen(
            [sys.executable, "-u", str(wrapper_path)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.8)
        st.rerun()

# Cancelar
if cancelar:
    pid = leer_pid()
    if pid:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                )
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    limpiar_archivos_estado()
    st.warning("⏹ Monitoreo cancelado.")
    time.sleep(0.5)
    st.rerun()

# ── Barra de progreso ──────────────────────────────────────────────────────────
with prog_col:
    status = progreso.get("status", "")

    if corriendo and status != "done":
        # Proceso vivo y no terminó — mostrar progreso y hacer rerun
        cur    = progreso.get("current", 0)
        total  = progreso.get("total", len(productos_lista)) or 1
        pct    = min(int((cur / total) * 100), 100)
        ultimo = progreso.get("ultimo", "")

        st.markdown(f"""
        <div class="progress-wrap">
            <div class="progress-title">
                <span>⚡ MONITOREANDO</span>
                <span style="color:#fbbf24">{cur} / {total} productos</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{pct}%"></div>
            </div>
            <div class="progress-stats">{pct}% completado</div>
            {"<div class='progress-item'>Último: "+ultimo+"</div>" if ultimo else ""}
        </div>
        """, unsafe_allow_html=True)

        log_lines = leer_log(30)
        if log_lines:
            colored = "".join(colorear_log(l) + "<br>" for l in log_lines)
            st.markdown(f'<div class="log-box">{colored}</div>', unsafe_allow_html=True)

        time.sleep(1.5)
        st.rerun()

    elif status == "done":
        # Terminó — mostrar completado, NO hacer rerun (deja ver los tabs)
        cur   = progreso.get("current", 0)
        total = progreso.get("total", 0)
        st.markdown(f"""
        <div class="progress-wrap">
            <div class="progress-title">
                <span style="color:#22c55e">✅ COMPLETADO</span>
                <span style="color:#22c55e">{cur} / {total} productos</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:100%; background: linear-gradient(90deg,#16a34a,#22c55e);"></div>
            </div>
            <div class="progress-stats" style="color:#22c55e">Resultados listos — recargá la página para actualizar las métricas</div>
        </div>
        """, unsafe_allow_html=True)
        # Limpiar estado para que el botón vuelva a "Ejecutar"
        limpiar_archivos_estado()

st.divider()


# ── Tabs ───────────────────────────────────────────────────────────────────────
if not df.empty:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋  Resultados",
        "🔥  Mejores ofertas",
        "📊  Gráficos",
        "🔬  Análisis",
    ])

    COLS = [c for c in [
        "Producto buscado", "Título", "Precio oferta (USD)", "Precio original (USD)",
        "Descuento %", "Precio oferta (ARS)", "Dólar blue", "Link", "Fecha",
    ] if c in df.columns]

    with tab1:
        buscar = st.text_input("🔎 Buscar en resultados", placeholder="ej: lenovo, sony, 4k...")
        df_v   = df.copy()
        if buscar:
            mask = (df_v["Título"].str.contains(buscar, case=False, na=False) |
                    df_v["Producto buscado"].str.contains(buscar, case=False, na=False))
            df_v = df_v[mask]
        st.caption(f"{len(df_v)} resultados")
        st.dataframe(df_v[COLS], use_container_width=True, height=440)
        if archivo and not reporte_upload:
            with open(archivo, "rb") as f:
                st.download_button("⬇ Descargar Excel", f, file_name=archivo,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        if "Descuento %" in df.columns:
            df_of = (df[df["Descuento %"] >= descuento_alerta]
                     .sort_values("Descuento %", ascending=False).head(top_n))
            if df_of.empty:
                st.info(f"Sin ofertas ≥ {descuento_alerta}% en el reporte actual.")
            else:
                for _, r in df_of.iterrows():
                    titulo = r["Título"][:95] + ("…" if len(r["Título"]) > 95 else "")
                    link   = r.get("Link", "#")
                    usd    = r.get("Precio oferta (USD)", 0)
                    orig   = r.get("Precio original (USD)", usd)
                    desc   = int(r.get("Descuento %", 0))
                    ars    = r.get("Precio oferta (ARS)", 0)
                    ahorro = orig - usd
                    st.markdown(f"""
                    <div class="offer-row">
                        <span class="offer-badge">{desc}% OFF</span>
                        <span style="font-size:0.63rem; color:#4a5568; font-family:Space Mono,monospace; margin-left:8px;">{r['Producto buscado']}</span>
                        <div style="font-size:0.88rem; color:#e2e8f0; margin:4px 0;">{titulo}</div>
                        <div style="font-size:0.78rem; color:#94a3b8;">
                            <b style="color:#fbbf24; font-size:0.95rem;">${usd:.2f}</b>
                            &nbsp;<s style="color:#374151;">${orig:.2f}</s>
                            &nbsp;·&nbsp; ahorrás <b style="color:#22c55e">${ahorro:.2f}</b>
                            &nbsp;·&nbsp; ARS <b>${int(ars):,}</b>
                            &nbsp;·&nbsp; <a href="{link}" target="_blank" style="color:#f97316; text-decoration:none;">Ver en Amazon ↗</a>
                        </div>
                    </div>""", unsafe_allow_html=True)

    with tab3:
        try:
            import plotly.express as px
            g1, g2 = st.columns(2)
            with g1:
                st.markdown('<div class="sec-label">Precio promedio por categoría (USD)</div>', unsafe_allow_html=True)
                df_cat = (df.groupby("Producto buscado")["Precio oferta (USD)"]
                          .mean().sort_values().tail(16).reset_index())
                df_cat.columns = ["Categoría", "Precio (USD)"]
                fig = px.bar(df_cat, x="Precio (USD)", y="Categoría", orientation="h",
                             color="Precio (USD)", color_continuous_scale=ORANGE_SCALE)
                fig.update_layout(paper_bgcolor=PLOTLY["paper_bgcolor"], plot_bgcolor=PLOTLY["plot_bgcolor"],
                                  font=PLOTLY["font"], coloraxis_showscale=False,
                                  margin=dict(l=0,r=0,t=4,b=0), height=370,
                                  xaxis=dict(gridcolor=PLOTLY["gridcolor"], zeroline=False),
                                  yaxis=dict(gridcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                st.markdown('<div class="sec-label">Distribución de descuentos (%)</div>', unsafe_allow_html=True)
                df_desc = df[df["Descuento %"] > 0]["Descuento %"]
                fig2 = px.histogram(df_desc, nbins=25, color_discrete_sequence=["#f97316"])
                fig2.update_layout(paper_bgcolor=PLOTLY["paper_bgcolor"], plot_bgcolor=PLOTLY["plot_bgcolor"],
                                   font=PLOTLY["font"], margin=dict(l=0,r=0,t=4,b=0), height=370, showlegend=False,
                                   xaxis=dict(title="Descuento %", gridcolor=PLOTLY["gridcolor"]),
                                   yaxis=dict(title="Cantidad",    gridcolor=PLOTLY["gridcolor"]))
                fig2.update_traces(marker_line_color="#080810", marker_line_width=1)
                st.plotly_chart(fig2, use_container_width=True)

            g3, g4 = st.columns(2)
            with g3:
                st.markdown('<div class="sec-label">Precio vs Descuento — mapa de oportunidades</div>', unsafe_allow_html=True)
                df_sc = df[df["Descuento %"] > 0].copy()
                fig3 = px.scatter(df_sc, x="Precio oferta (USD)", y="Descuento %",
                                  color="Producto buscado", hover_data=["Título"],
                                  color_discrete_sequence=px.colors.qualitative.Vivid)
                fig3.update_layout(paper_bgcolor=PLOTLY["paper_bgcolor"], plot_bgcolor=PLOTLY["plot_bgcolor"],
                                   font=PLOTLY["font"], margin=dict(l=0,r=0,t=4,b=0), height=370,
                                   xaxis=dict(gridcolor=PLOTLY["gridcolor"]),
                                   yaxis=dict(gridcolor=PLOTLY["gridcolor"]),
                                   legend=dict(font_size=9, bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig3, use_container_width=True)
            with g4:
                st.markdown('<div class="sec-label">Top 10 — mayor ahorro absoluto (USD)</div>', unsafe_allow_html=True)
                if "Precio original (USD)" in df.columns:
                    df2 = df.copy()
                    df2["Ahorro (USD)"] = (df2["Precio original (USD)"] - df2["Precio oferta (USD)"]).clip(lower=0)
                    top_ahorro = df2.nlargest(10, "Ahorro (USD)")[["Título","Ahorro (USD)","Descuento %"]].copy()
                    top_ahorro["Título corto"] = top_ahorro["Título"].str[:42] + "…"
                    fig4 = px.bar(top_ahorro, x="Ahorro (USD)", y="Título corto", orientation="h",
                                  color="Descuento %", color_continuous_scale=ORANGE_SCALE,
                                  hover_data=["Título","Descuento %"])
                    fig4.update_layout(paper_bgcolor=PLOTLY["paper_bgcolor"], plot_bgcolor=PLOTLY["plot_bgcolor"],
                                       font=PLOTLY["font"],
                                       coloraxis_colorbar=dict(title="Desc %", tickfont_size=9),
                                       margin=dict(l=0,r=0,t=4,b=0), height=370,
                                       xaxis=dict(gridcolor=PLOTLY["gridcolor"], zeroline=False),
                                       yaxis=dict(gridcolor="rgba(0,0,0,0)"))
                    st.plotly_chart(fig4, use_container_width=True)
        except ImportError:
            st.warning("Instalá plotly: `pip install plotly`")

    with tab4:
        st.markdown('<div class="sec-label">Resumen estadístico por categoría</div>', unsafe_allow_html=True)
        resumen = df.groupby("Producto buscado").agg(
            Resultados=("Título",              "count"),
            USD_min   =("Precio oferta (USD)", "min"),
            USD_prom  =("Precio oferta (USD)", "mean"),
            USD_max   =("Precio oferta (USD)", "max"),
            Desc_max  =("Descuento %",         "max"),
            Desc_prom =("Descuento %",         "mean"),
        ).round(2).sort_values("Desc_max", ascending=False).reset_index()
        resumen.columns = ["Categoría","Resultados","USD mín","USD prom","USD máx","Desc máx %","Desc prom %"]
        st.dataframe(resumen, use_container_width=True, height=380)

        st.markdown('<div class="sec-label">Distribución de precios por categoría (boxplot)</div>', unsafe_allow_html=True)
        try:
            import plotly.express as px
            cats_top = df["Producto buscado"].value_counts().head(12).index.tolist()
            df_box   = df[df["Producto buscado"].isin(cats_top)]
            fig_box  = px.box(df_box, x="Producto buscado", y="Precio oferta (USD)",
                              color="Producto buscado",
                              color_discrete_sequence=px.colors.qualitative.Vivid)
            fig_box.update_layout(paper_bgcolor=PLOTLY["paper_bgcolor"], plot_bgcolor=PLOTLY["plot_bgcolor"],
                                  font=PLOTLY["font"], margin=dict(l=0,r=0,t=4,b=0), height=420,
                                  showlegend=False,
                                  xaxis=dict(tickangle=-35, gridcolor=PLOTLY["gridcolor"]),
                                  yaxis=dict(gridcolor=PLOTLY["gridcolor"]))
            st.plotly_chart(fig_box, use_container_width=True)
        except ImportError:
            pass

else:
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem; color:#1e293b;">
        <div style="font-size:3rem; margin-bottom:1rem;">📡</div>
        <div style="font-family:Space Mono,monospace; font-size:0.75rem; letter-spacing:0.15em; text-transform:uppercase;">
            Sin datos — configurá productos y ejecutá el monitoreo
        </div>
    </div>""", unsafe_allow_html=True)

st.divider()
st.markdown(
    '<div style="font-family:Space Mono,monospace; font-size:0.56rem; color:#1a1a2e; text-align:center; letter-spacing:0.1em;">'
    'PRICE MONITOR · Rafael Orozco · joaquin23.or@gmail.com</div>',
    unsafe_allow_html=True,
)