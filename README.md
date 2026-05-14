# 📡 Amazon Price Monitor

Monitor de precios automatizado para Amazon con alertas por Telegram, dashboard web y conversión ARS/USD en tiempo real.

---

## ✨ Características

- 🔍 Búsqueda en paralelo de múltiples productos simultáneamente
- 💵 Conversión automática USD → ARS usando dólar blue en tiempo real
- 🔔 Alertas por Telegram cuando se detectan ofertas con descuento configurable
- 📊 Dashboard web con gráficos, filtros y análisis por categoría
- ⚡ Cancelación del monitoreo en tiempo real desde el dashboard
- 📋 Presets de productos por categoría (tecnología, gaming, hogar, etc.)
- 🗂️ Configuración guardable en `.env` directamente desde la UI
- 📈 Progreso en vivo durante la ejecución
- 📁 Exportación a Excel con todos los datos

---

## 🚀 Inicio rápido

### 1. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install requests pandas python-dotenv beautifulsoup4 streamlit plotly
```

### 2. Configurar variables de entorno

Crear un archivo `.env` (o configurar desde el dashboard):

```env
SCRAPER_API_KEY=tu_api_key           # scraperapi.com — gratis hasta 1000 req/mes
TELEGRAM_BOT_TOKEN=tu_bot_token      # opcional — alertas automáticas
TELEGRAM_CHAT_ID=tu_chat_id          # opcional
DESCUENTO_MINIMO=20                  # % mínimo para activar alerta
```

### 3. Configurar productos

Editar `productos.csv` (o hacerlo desde el dashboard):

```
producto
notebook lenovo
iphone 15
monitor samsung 27
```

### 4. Ejecutar

**Dashboard web (recomendado):**
```bash
streamlit run dashboard.py
```

**Modo consola:**
```bash
python monitor_aws.py
```

---

## 🔔 Configurar alertas por Telegram

1. Buscá **@BotFather** en Telegram → `/newbot` → copiá el token
2. Buscá **@userinfobot** → mandá cualquier mensaje → copiá tu Chat ID
3. Pegá ambos en el `.env` o desde el sidebar del dashboard
4. Configurá `DESCUENTO_MINIMO` según tu criterio

Las alertas incluyen: nombre, precio actual vs original, % de descuento, precio en ARS y link directo.

---

## 🌐 Dashboard Web

`dashboard.py` incluye:

- Sidebar con configuración completa (API keys, filtros, parámetros)
- Carga automática de variables desde `.env` con indicador visual
- Botón de **cancelar monitoreo** en tiempo real
- **Barra de progreso** con productos completados / total
- **Log en vivo** durante la ejecución
- **Presets** de productos por categoría (laptops, gaming, hogar, etc.)
- 4 tabs: Resultados · Mejores ofertas · Gráficos · Análisis
- 4 gráficos Plotly: precio por categoría, distribución descuentos, scatter precio/descuento, top ahorro
- Boxplot de distribución de precios por categoría
- Búsqueda en tiempo real dentro de los resultados
- Descarga del Excel generado

---

## 🏗️ Arquitectura

```
monitor_aws.py          ← Scraper Amazon (ScraperAPI + BeautifulSoup)
telegram_notifier.py    ← Módulo de alertas por Telegram
dashboard.py            ← Interfaz web con Streamlit
productos.csv           ← Lista de productos a monitorear
.env                    ← Claves de API (no se sube al repo)
```

---

## ⚙️ Tecnología

- **Python 3.8+**
- `requests` + `BeautifulSoup4` — scraping Amazon
- `pandas` — procesamiento y exportación Excel
- `streamlit` — dashboard web
- `plotly` — gráficos interactivos
- `concurrent.futures` — paralelismo
- `python-dotenv` — gestión de claves
- [dolarapi.com](https://dolarapi.com) — cotización dólar blue en tiempo real
- [scraperapi.com](https://scraperapi.com) — proxy para Amazon (gratis hasta 1000 req/mes)

---

## 📁 Archivos

| Archivo | Descripción |
|---|---|
| `monitor_aws.py` | Scraper principal Amazon |
| `telegram_notifier.py` | Módulo de alertas Telegram |
| `dashboard.py` | Dashboard web Streamlit |
| `productos.csv` | Lista de productos a monitorear |
| `.env` | Variables de entorno (no incluido en repo) |
| `.gitignore` | Excluye claves y archivos generados |

---

## 👤 Autor

Desarrollado por **Rafael Orozco** — automatizaciones y scraping con Python.

📧 joaquin23.or@gmail.com