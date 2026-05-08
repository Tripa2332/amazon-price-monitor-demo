import concurrent.futures
import logging
import random
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from typing import Any, Dict, List
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def format_progress_status(current: int, total: int) -> str:
    """Return a simple progress status string."""
    return f"{current}/{total}"

load_dotenv()
API_KEY = os.getenv("SCRAPER_API_KEY")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET"]),
)

SESSION = requests.Session()
adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)
SESSION.headers.update(HEADERS)


df_productos = pd.read_csv("productos.csv")
PRODUCTOS = df_productos["producto"].tolist()
logger.info(f"📋 {len(PRODUCTOS)} productos cargados desde productos.csv")

def obtener_dolar() -> float:
    """Obtener el valor del dólar blue desde la API externa."""
    response = SESSION.get("https://dolarapi.com/v1/dolares/blue", timeout=15)
    venta = response.json().get("venta")
    return float(venta) if venta else 1200.0

def buscar_precios(query: str, dolar: float, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Buscar productos en Amazon vía ScraperAPI y devolver resultados estructurados."""
    url = "http://api.scraperapi.com"
    resultados: List[Dict[str, Any]] = []
    total_processed = 0

    for page in range(1, max_pages + 1):
        params = {
            "api_key": API_KEY,
            "url": f"https://www.amazon.com/s?k={query.replace(' ', '+')}&page={page}",
        }
        resp = SESSION.get(url, params=params, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        print(f"\r    Página {page}/{max_pages}", end="", flush=True)

        if resp.status_code == 404:
            logger.warning("    Página %s: 404 no encontrada (posible página eliminada o bloqueo)", page)
            continue

        if resp.status_code != 200:
            logger.warning("    Página %s: status %s", page, resp.status_code)
            continue

        if "captcha" in resp.text.lower() or "automated access" in resp.text.lower():
            logger.warning("    Página %s: posible bloqueo de Amazon", page)

        items_raw = soup.select("div[data-component-type='s-search-result'], div.s-result-item, div[data-asin]")
        seen_asins = set()
        items = []
        for item in items_raw:
            asin = item.get("data-asin")
            if asin:
                asin = asin.strip()
                if asin and asin not in seen_asins:
                    seen_asins.add(asin)
                    items.append(item)

        logger.info("    Página %s: %s items encontrados", page, len(items))
        processed = 0

        for item in items[:40]:
            
          
            titulo_el = (
                item.select_one("h2 a span") or
                item.select_one("h2 span.a-text-normal") or
                item.select_one("h2 span") or
                item.select_one("span.a-size-medium.a-color-base.a-text-normal") or
                item.select_one("span.a-size-base-plus.a-color-base.a-text-normal") or
                item.select_one("span.a-size-base-plus.a-color-base.a-text-bold") or
                item.select_one("[data-cel-widget='search_result_1'] h2 a span") or
                item.select_one("[data-cy='title-recipe'] span")
            )
            precio_el = item.select_one(".a-price-whole")
            precio_fraction_el = item.select_one(".a-price-fraction")
            precio_offscreen = item.select_one(".a-price .a-offscreen")
            precio_original_el = item.select_one(".a-text-price .a-offscreen")
            link_el = item.select_one("h2 a[href]")

            precio_usd_str = ""
            if precio_el:
                precio_usd_str = precio_el.text.replace(",", "").strip() + (precio_fraction_el.text if precio_fraction_el else "")
            elif precio_offscreen:
                precio_usd_str = precio_offscreen.text.replace("$", "").replace(",", "").strip()

            if titulo_el and precio_usd_str:
                processed += 1
                precio_usd = float(precio_usd_str)
                precio_orig_text = precio_original_el.get_text().replace("$", "").replace(",", "").strip() if precio_original_el else None
                precio_orig = float(precio_orig_text) if precio_orig_text else precio_usd
                descuento = round((1 - precio_usd / precio_orig) * 100) if precio_orig > precio_usd else 0

                
                link = ""
                for a in item.select("a[href]"):
                    href = a.get("href", "")
                    if "/dp/" in href and "sspa" not in href and "javascript" not in href:
                        asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
                        link = f"https://www.amazon.com/dp/{asin}"
                        break

                resultados.append({
                    "Producto buscado":      query,
                    "Título":                titulo_el.get_text(strip=True),
                    "Precio oferta (USD)":   precio_usd,
                    "Precio original (USD)": precio_orig,
                    "Descuento %":           descuento,
                    "Precio oferta (ARS)":   round(precio_usd * dolar),
                    "Precio original (ARS)": round(precio_orig * dolar),
                    "Dólar blue":            dolar,
                    "Link":                  link,
                    "Fecha":                 datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
        total_processed += processed
        logger.info("      Procesados: %s de %s", processed, min(40, len(items)))
        if not items:
            break

        if page < max_pages:
            time.sleep(random.uniform(0.5, 1.0))

    print()
    logger.info("    Total procesados para '%s': %s", query, total_processed)
    return resultados


def main() -> None:
    """Ejecutar búsqueda para todos los productos y guardar los resultados en Excel."""
    dolar = obtener_dolar()
    logger.info("💵 Dólar blue hoy: $%s", dolar)

    todos = []
    total = len(PRODUCTOS)
    start_time = time.time()

    max_workers = min(4, total)
    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_product = {
            executor.submit(buscar_precios, p, dolar): (i, p)
            for i, p in enumerate(PRODUCTOS, 1)
        }

        for future in concurrent.futures.as_completed(future_to_product):
            i, p = future_to_product[future]
            try:
                resultados_producto = future.result()
                todos.extend(resultados_producto)
                processed_count += 1
                print(f"\rProductos completados: {processed_count}/{total}", end="", flush=True)
                logger.info("Buscado: %s --- %s/%s | resultados: %s", p, i, total, len(resultados_producto))
            except Exception as exc:
                logger.error("Error buscando %s: %s", p, exc)
    print()

    if todos:
        df = pd.DataFrame(todos)
        nombre = f"amazon_monitor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        df.to_excel(nombre, index=False)
        elapsed = time.time() - start_time
        logger.info("\n✓ %s — %s productos", nombre, len(todos))
        logger.info("Tiempo total aproximado: %.2f segundos", elapsed)
    else:
        logger.info("Sin resultados")


if __name__ == "__main__":
    main()