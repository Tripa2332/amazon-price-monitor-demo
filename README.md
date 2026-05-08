# Amazon Price Monitor - Demo de Web Scraping

Este repositorio contiene una demo funcional de scraping de Amazon para extraer precios, descuento y enlaces de productos, y guardar los resultados en un archivo Excel.

## Qué hace este proyecto

- Lee una lista de productos desde `productos.csv`
- Realiza búsquedas en Amazon con `requests` + `BeautifulSoup`
- Usa concurrencia con `concurrent.futures` para procesar varios productos en paralelo
- Muestra progreso de ejecución por producto y por página
- Usa reintentos automáticos para manejar `429` y errores de red temporales
- Registra warnings y errores con logging estructurado
- Cuenta con type hints y docstrings para mayor calidad de código
- Extrae título, precio actual, precio original, descuento y enlace del producto
- Convierte los valores USD a ARS usando el valor del dólar blue
- Genera un informe en formato Excel con los datos recolectados

## Tecnología utilizada

- Python 3.8+
- requests
- BeautifulSoup
- pandas
- python-dotenv

Además se usa `concurrent.futures` para paralelizar la búsqueda y `requests` con reintentos para manejar mejor respuestas 429 y errores temporales.

## Archivos del repositorio

- `monitor_aws.py` — script principal de scraping
- `productos.csv` — lista de términos a buscar
- `README.md` — documentación del proyecto
- `.gitignore` — evita subir claves y archivos generados

## Instalación

1. Crea y activa un entorno virtual (recomendado):

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate    # Windows
```

2. Instala dependencias:

```bash
pip install requests pandas python-dotenv beautifulsoup4
```

3. Crea un archivo `.env` con tu clave de ScraperAPI:

```env
SCRAPER_API_KEY=tu_api_key
```

## Uso

1. Ajusta `productos.csv` con los productos o términos que quieras monitorear.
2. Ejecuta el script:

```bash
python monitor_aws.py
```

3. Se generará un archivo `amazon_monitor_YYYYMMDD_HHMM.xlsx` con los resultados.

## Resultados esperados

El script imprime en consola el avance de la búsqueda y genera un Excel con columnas como:

- El código incluye type hints, docstrings y logging, lo que lo hace más profesional para presentarlo como proyecto técnico.

- Producto buscado
- Título
- Precio oferta (USD)
- Precio original (USD)
- Descuento %
- Precio oferta (ARS)
- Precio original (ARS)
- Dólar blue
- Link
- Fecha

## Autor

Este proyecto fue desarrollado como demo de scraping web. Para consultas o colaboraciones, contactame.

