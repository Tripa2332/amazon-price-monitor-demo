"""
Módulo de notificaciones por Telegram para Amazon Price Monitor.
Envía alertas cuando un producto supera el umbral de descuento configurado.
"""

import logging
import os
import requests
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DESCUENTO_MINIMO = int(os.getenv("DESCUENTO_MINIMO", "20"))  # % mínimo para alertar


def enviar_mensaje(texto: str) -> bool:
    """Enviar un mensaje de texto al chat de Telegram configurado."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram no configurado (TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID faltante)")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("Error enviando mensaje a Telegram: %s", e)
        return False


def alertar_ofertas(resultados: List[Dict[str, Any]], umbral: int = DESCUENTO_MINIMO) -> int:
    """
    Filtrar resultados con descuento >= umbral y enviar alerta por Telegram.
    Retorna la cantidad de alertas enviadas.
    """
    ofertas = [r for r in resultados if r.get("Descuento %", 0) >= umbral]

    if not ofertas:
        logger.info("Sin ofertas con descuento >= %s%%", umbral)
        return 0

    # Agrupar por producto buscado
    productos_vistos: Dict[str, List[Dict]] = {}
    for o in ofertas:
        key = o["Producto buscado"]
        productos_vistos.setdefault(key, []).append(o)

    enviados = 0
    for producto, items in productos_vistos.items():
        # Tomar el de mayor descuento
        mejor = max(items, key=lambda x: x.get("Descuento %", 0))
        texto = (
            f"🔥 <b>OFERTA DETECTADA</b>\n\n"
            f"🔍 <b>Búsqueda:</b> {mejor['Producto buscado']}\n"
            f"📦 <b>Producto:</b> {mejor['Título'][:80]}...\n"
            f"💵 <b>Precio:</b> ${mejor['Precio oferta (USD)']:.2f} "
            f"<s>${mejor['Precio original (USD)']:.2f}</s>\n"
            f"📉 <b>Descuento:</b> {mejor['Descuento %']}%\n"
            f"💰 <b>En ARS:</b> ${mejor['Precio oferta (ARS)']:,}\n"
            f"🔗 <a href='{mejor['Link']}'>Ver en Amazon</a>\n"
            f"📅 {mejor['Fecha']}"
        )
        if enviar_mensaje(texto):
            enviados += 1
            logger.info("✅ Alerta enviada para: %s (%s%% off)", producto, mejor['Descuento %'])

    return enviados