"""Acción User-Agent standalone: solo primer clic en extensión."""
from __future__ import annotations

import argparse
import sys
import time
from typing import Optional, Tuple

import pyautogui
import pyperclip

from app.creator.computer_actions import click_coordinates
from app.database.database import (
    get_creator_coordinates,
    get_default_browser,
    get_next_creator_user_agent_random,
)

COORD_EXTENSION = "user_agent_extension_click"
COORD_PLACE = "user_agent_extract_click"
COORD_APPLY = "user_agent_apply_click"
COORD_OUTSIDE = "user_agent_outside_click"


def resolve_browser_id(browser_id: Optional[int] = None) -> Optional[int]:
    if browser_id is not None:
        return browser_id
    b = get_default_browser()
    return b["id"] if b else None


def run_user_agent_extension_click(browser_id: int) -> Tuple[bool, Optional[str]]:
    """Secuencia completa: abrir extensión, colocar/pegar UA, aplicar y clic fuera.

    Returns:
        (éxito, user_agent_aplicado) — el string es el UA pegado desde el pool (mismo que usa la sesión).
    """
    coords = get_creator_coordinates(browser_id)
    if not coords:
        print("⚠️ No hay coordenadas para este navegador.")
        return False, None
    raw = (coords.get(COORD_EXTENSION) or "").strip()
    place = (coords.get(COORD_PLACE) or "").strip()
    apply_click = (coords.get(COORD_APPLY) or "").strip()
    outside_click = (coords.get(COORD_OUTSIDE) or "").strip()
    if not raw:
        print(f"⚠️ Falta '{COORD_EXTENSION}' en la configuración del navegador.")
        return False, None
    if not place:
        print(f"⚠️ Falta '{COORD_PLACE}' en la configuración del navegador.")
        return False, None
    if not apply_click:
        print(f"⚠️ Falta '{COORD_APPLY}' en la configuración del navegador.")
        return False, None
    if not outside_click:
        print(f"⚠️ Falta '{COORD_OUTSIDE}' en la configuración del navegador.")
        return False, None
    print(f"🖱️ Clic en extensión user agent ({raw})…")
    if not click_coordinates(raw):
        print("⚠️ No se pudo completar el clic (revisa coordenadas o posición del ratón).")
        return False, None
    time.sleep(1)
    print(f"🖱️ Clic en colocar user agent ({place})…")
    if not click_coordinates(place):
        print("⚠️ No se pudo completar el segundo clic (revisa coordenadas).")
        return False, None

    # Esperar y seleccionar todo el texto del campo
    time.sleep(0.5)
    pyautogui.PAUSE = 0.05
    pyautogui.FAILSAFE = False
    print("⌨️ Ctrl+A (seleccionar texto actual)…")
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)

    # Obtener un UA aleatorio del pool sin repetir hasta agotar
    next_ua = get_next_creator_user_agent_random()
    if not next_ua:
        print("⚠️ No hay User-Agents disponibles en el pool local.")
        return False, None

    pyperclip.copy(next_ua)
    time.sleep(0.1)
    print(f"⌨️ Ctrl+V (pegando UA aleatorio de {len(next_ua)} caracteres)…")
    pyautogui.hotkey("ctrl", "v")

    print(f"🖱️ Clic aplicar user agent ({apply_click})…")
    if not click_coordinates(apply_click):
        print("⚠️ No se pudo completar el clic en aplicar user agent.")
        return False, None

    time.sleep(0.5)
    print(f"🖱️ Clic fuera de la extensión ({outside_click})…")
    if not click_coordinates(outside_click):
        print("⚠️ No se pudo completar el clic fuera de la extensión.")
        return False, None

    time.sleep(0.2)
    print("⌨️ Refresco limpio del navegador (Ctrl+F5)…")
    pyautogui.hotkey("ctrl", "f5")

    print("✅ User-Agent pegado, aplicado y navegador refrescado.")
    return True, next_ua


def run_user_agent_step1(browser_id: int) -> Tuple[bool, Optional[str]]:
    """Alias explícito para probar solo el primer clic."""
    return run_user_agent_extension_click(browser_id)


def _cli_main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="User agent actions standalone: solo primer clic en extensión.",
    )
    p.add_argument("--browser-id", type=int, default=None, metavar="ID", help="ID en tabla browsers (si se omite, navegador por defecto)")
    args = p.parse_args(argv)

    bid = resolve_browser_id(args.browser_id)
    if bid is None:
        print("⚠️ Sin navegador; usa --browser-id o define un navegador por defecto en la app.")
        return 1

    ok, _ua = run_user_agent_step1(bid)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_cli_main())
