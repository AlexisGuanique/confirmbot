"""Navegación de prueba (Google): solo uso por CLI; el Creator ya no guarda coordenadas warmup en BD/UI."""
from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Optional

import pyautogui

from app.creator.computer_actions import click_coordinates, press_key, type_text
from app.database.database import (
    get_creator_coordinates,
    get_default_browser,
)
from app.creator.browse_warmup_queries import WARMUP_SEARCH_QUERIES

GOOGLE_URL = "https://www.google.com"

COORD_ADDRESS_BAR = "warmup_address_bar_click"
COORD_SEARCH_BOX = "warmup_google_search_box_click"
COORD_SERP_1 = "warmup_serp_result_click_1"
COORD_SERP_2 = "warmup_serp_result_click_2"


def resolve_browser_id(browser_id: Optional[int] = None) -> Optional[int]:
    if browser_id is not None:
        return browser_id
    b = get_default_browser()
    return b["id"] if b else None


def _check_bot_running() -> bool:
    try:
        from app.auth.auth import bot_running

        return bool(bot_running)
    except Exception:
        return True


def _should_continue_warmup(respect_bot_stop: bool) -> bool:
    if not respect_bot_stop:
        return True
    return _check_bot_running()


def run_browse_warmup_before_linkedin(browser_id: int, *, respect_bot_stop: bool = True) -> bool:
    """
    Abre Google, ejecuta una búsqueda y opcionalmente clics en resultados.
    Si no hay ``warmup_google_search_box_click`` configurado, no hace nada y devuelve True.

    Args:
        respect_bot_stop: Si es True (flujo Creator), se respeta ``auth.bot_running``.
            En False (prueba por CLI), se ejecuta aunque el bot esté en ``stopped``.
    """
    coords = get_creator_coordinates(browser_id)
    if not coords:
        print("⚠️ Warmup: sin coordenadas de navegador.")
        return True

    search_box = (coords.get(COORD_SEARCH_BOX) or "").strip()
    if not search_box:
        print(
            "ℹ️ Warmup omitido: no hay coordenadas en BD (warmup_google_search_box_click). "
            "El Creator ya no incluye esa fila; este script es solo para pruebas manuales si mantienes columnas heredadas."
        )
        return True

    if not _should_continue_warmup(respect_bot_stop):
        print("🛑 Warmup cancelado (bot detenido).")
        return False

    pyautogui.PAUSE = 0.05
    pyautogui.FAILSAFE = False

    print("🌐 Warmup: abriendo Google…")
    addr = (coords.get(COORD_ADDRESS_BAR) or "").strip()
    if addr:
        if not click_coordinates(addr):
            print("⚠️ Warmup: falló clic en barra de direcciones.")
            return False
    else:
        print("⌨️ Warmup: Ctrl+L (barra de direcciones)…")
        pyautogui.hotkey("ctrl", "l")
    time.sleep(0.35)

    if not type_text(GOOGLE_URL):
        print("⚠️ Warmup: no se pudo escribir la URL.")
        return False
    time.sleep(0.12)
    if not press_key("enter"):
        return False

    time.sleep(random.uniform(2.8, 4.8))
    if not _should_continue_warmup(respect_bot_stop):
        return False

    print(f"🖱️ Warmup: clic en caja de búsqueda ({search_box})…")
    if not click_coordinates(search_box):
        print("⚠️ Warmup: falló clic en caja de búsqueda.")
        return False
    time.sleep(random.uniform(0.2, 0.45))

    query = random.choice(WARMUP_SEARCH_QUERIES)
    print(f"⌨️ Warmup: búsqueda «{query}»…")
    if not type_text(query):
        return False
    time.sleep(0.12)
    if not press_key("enter"):
        return False

    time.sleep(random.uniform(3.2, 6.0))
    if not _should_continue_warmup(respect_bot_stop):
        return False

    if random.random() < 0.75:
        pyautogui.scroll(-random.randint(2, 6))
        time.sleep(random.uniform(0.35, 0.9))

    for label, key in (
        ("resultado 1", COORD_SERP_1),
        ("resultado 2", COORD_SERP_2),
    ):
        c = (coords.get(key) or "").strip()
        if not c:
            continue
        if not _should_continue_warmup(respect_bot_stop):
            return False
        print(f"🖱️ Warmup: clic {label} ({c})…")
        if not click_coordinates(c):
            print(f"⚠️ Warmup: falló clic {label}.")
            return False
        time.sleep(random.uniform(1.0, 2.4))

    print("✅ Warmup de navegación completado.")
    return True


def _cli_main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Warmup: Google + búsqueda + clics (misma lógica que antes de LinkedIn en Creator).",
    )
    p.add_argument(
        "--browser-id",
        type=int,
        default=None,
        metavar="ID",
        help="ID en tabla browsers (si se omite, navegador por defecto)",
    )
    p.add_argument(
        "--honor-bot-running",
        action="store_true",
        help="Si se indica, cancela el warmup cuando auth.bot_running es False (como en el Creator).",
    )
    args = p.parse_args(argv)

    bid = resolve_browser_id(args.browser_id)
    if bid is None:
        print("⚠️ Sin navegador; usa --browser-id o define un navegador por defecto.")
        return 1

    respect = bool(args.honor_bot_running)
    if not respect:
        print("ℹ️ Prueba standalone: se ignora bot_running (el Creator sigue respetando la señal de parada).")

    return 0 if run_browse_warmup_before_linkedin(bid, respect_bot_stop=respect) else 1


if __name__ == "__main__":
    sys.exit(_cli_main())
