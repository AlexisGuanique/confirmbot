"""
Rotación de proxy: coordenadas en BD + enlace en creator_setting.

Flujo: navegador → Enter → pausa 2 s → barra búsqueda → pegar URL → Enter → 3 s → cerrar navegador.
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Optional

import pyautogui

from app.creator.computer_actions import type_text
from app.database.database import get_creator_coordinates, get_creator_setting, get_default_browser

# --- Clic izquierdo en Windows (mouse_event; más fiable que pyautogui.click) --------------------
if sys.platform == "win32":
    import ctypes

    _DOWN, _UP = 0x0002, 0x0004

    def _left_click_here() -> None:
        u = ctypes.windll.user32
        u.mouse_event(_DOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        u.mouse_event(_UP, 0, 0, 0, 0)
else:

    def _left_click_here() -> None:
        pyautogui.mouseDown(button="left")
        time.sleep(0.05)
        pyautogui.mouseUp(button="left")

# --- Constantes ---------------------------------------------------------------------------------
COORD_KEYS = {
    "browser": "proxy_rotation_browser_click",
    "search": "proxy_rotation_search_bar_click",
    "close": "proxy_rotation_close_browser_click",
}

TIMING = {
    "move": 0.45,
    "settle": 0.35,
    "snap": 0.05,
    "after_snap": 0.05,
    "after_first_enter": 2.0,
    "before_enter": 0.2,
    "after_search_click": 0.2,
    "after_paste": 0.15,
    "after_url_enter": 3.0,
    "start_delay": 0.25,
}

POS_TOLERANCE_PX = 8


# --- Coordenadas → movimiento + clic ------------------------------------------------------------
def _parse_xy(raw: str) -> Optional[tuple[int, int]]:
    if "x" not in raw:
        return None
    try:
        a, b = raw.lower().split("x", 1)
        return int(a.strip()), int(b.strip())
    except ValueError:
        return None


def click_at_coord_string(raw: str) -> bool:
    """Mueve el cursor a raw ('123x456'), espera y hace clic izquierdo."""
    xy = _parse_xy(raw)
    if not xy:
        print(f"⚠️ Formato inválido: {raw}")
        return False
    x, y = xy
    pyautogui.PAUSE = 0.01
    pyautogui.FAILSAFE = False

    print(f"   → Posicionando cursor en ({x}, {y})…")
    pyautogui.moveTo(x, y, duration=TIMING["move"])
    time.sleep(TIMING["settle"])
    pyautogui.moveTo(x, y, duration=TIMING["snap"])
    time.sleep(TIMING["after_snap"])

    cur = pyautogui.position()
    if abs(cur.x - x) > POS_TOLERANCE_PX or abs(cur.y - y) > POS_TOLERANCE_PX:
        print(f"   ⚠️ Puntero ({cur.x}, {cur.y}) vs objetivo ({x}, {y}); clic en posición actual.")

    print("   → Clic izquierdo…")
    if sys.platform == "win32":
        _left_click_here()
    else:
        pyautogui.click(int(x), int(y), clicks=1, button="left")
    time.sleep(0.05)
    return True


def press_enter() -> None:
    print("   → Tecla Enter…")
    pyautogui.press("enter")


# --- Carga de BD -------------------------------------------------------------------------------
def _coord(coords: dict[str, Any], key: str) -> Optional[str]:
    s = (coords.get(key) or "").strip()
    return s or None


def _load_context(browser_id: int) -> Optional[dict[str, str]]:
    """Devuelve browser, search, close, link o None (y ya imprime el error)."""
    coords = get_creator_coordinates(browser_id)
    if not coords:
        print("⚠️ No hay coordenadas para este navegador.")
        return None

    rb = _coord(coords, COORD_KEYS["browser"])
    rs = _coord(coords, COORD_KEYS["search"])
    rc = _coord(coords, COORD_KEYS["close"])
    if not rb:
        print(f"⚠️ Falta '{COORD_KEYS['browser']}' (modal rotación proxy).")
        return None
    if not rs:
        print(f"⚠️ Falta '{COORD_KEYS['search']}' (modal rotación proxy).")
        return None
    if not rc:
        print(f"⚠️ Falta '{COORD_KEYS['close']}' (modal rotación proxy).")
        return None

    st = get_creator_setting(browser_id) or {}
    link = (st.get("proxy_rotation_link") or "").strip()
    if not link:
        print("⚠️ No hay enlace de rotación guardado en la app.")
        return None

    return {"browser": rb, "search": rs, "close": rc, "link": link}


# --- Flujo principal ---------------------------------------------------------------------------
def run_proxy_rotation_flow(browser_id: int) -> bool:
    ctx = _load_context(browser_id)
    if not ctx:
        return False

    # 1) Navegador + Enter
    print(f"🖱️ Paso 1 — navegador: {ctx['browser']}")
    time.sleep(TIMING["start_delay"])
    if not click_at_coord_string(ctx["browser"]):
        return False
    time.sleep(TIMING["before_enter"])
    press_enter()

    # 2) Pausa
    print(f"   → Espera {TIMING['after_first_enter']:.0f} s…")
    time.sleep(TIMING["after_first_enter"])

    # 3) Barra de búsqueda
    print(f"🖱️ Paso 2 — barra búsqueda: {ctx['search']}")
    if not click_at_coord_string(ctx["search"]):
        return False

    # 4) Pegar URL + Enter
    time.sleep(TIMING["after_search_click"])
    link = ctx["link"]
    print(f"   → Pegar enlace ({len(link)} caracteres)…")
    if not type_text(link):
        print("❌ No se pudo pegar el enlace.")
        return False
    time.sleep(TIMING["after_paste"])
    press_enter()

    # 5) Tras Enter del pegado: 3 s y clic «cerrar navegador»
    print(f"   → Espera {TIMING['after_url_enter']:.0f} s (después del Enter del enlace)…")
    time.sleep(TIMING["after_url_enter"])
    print(f"🖱️ Paso 3 — cerrar navegador: {ctx['close']}")
    if not click_at_coord_string(ctx["close"]):
        return False

    print("✅ Flujo rotación proxy completado.")
    return True


def resolve_browser_id(browser_id: Optional[int] = None) -> Optional[int]:
    if browser_id is not None:
        return browser_id
    b = get_default_browser()
    return b["id"] if b else None


def run_proxy_rotation_from_settings(
    browser_id: Optional[int] = None,
    require_rotation_enabled: bool = True,
) -> bool:
    bid = resolve_browser_id(browser_id)
    if bid is None:
        print("⚠️ Sin navegador predeterminado; usa --browser-id o crea uno en la app.")
        return False

    if require_rotation_enabled:
        st = get_creator_setting(bid)
        if st is not None and not st.get("proxy_rotation_enabled"):
            print("⚠️ Rotación proxy deshabilitada en la configuración del creator.")
            return False

    return run_proxy_rotation_flow(bid)


# --- CLI ----------------------------------------------------------------------------------------
def _cli_main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Rotación proxy: navegador, Enter, pausa, búsqueda, URL, Enter, 3s, cerrar navegador.",
    )
    p.add_argument("--browser-id", type=int, default=None, metavar="ID", help="ID en tabla browsers")
    p.add_argument("--force", action="store_true", help="Ignorar si rotación proxy está desactivada en BD")
    args = p.parse_args(argv)
    ok = run_proxy_rotation_from_settings(
        browser_id=args.browser_id,
        require_rotation_enabled=not args.force,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_cli_main())
