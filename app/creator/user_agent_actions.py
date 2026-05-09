"""
User-Agent en el creator: legado desacoplado del flujo del bot.

El valor que acompaña cada cookie viene de `creator_setting.user_agent`
(enviado por el servidor). No hay automatización de extensión ni rotación
de UA desde aquí.

Se mantienen `COORD_*` y la firma de `run_user_agent_extension_click` por
compatibilidad con código o scripts que importen este módulo.
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Tuple

from app.database.database import get_creator_user_agent_for_saved_account, get_default_browser

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
    """
    Sin UI/automatización: devuelve el User-Agent guardado para el navegador.

    Returns:
        (éxito, user_agent) — éxito si hay UA no vacío en creator_setting.
    """
    ua = get_creator_user_agent_for_saved_account(browser_id)
    if ua:
        return True, ua
    print("⚠️ Sin user_agent en creator_setting; el servidor debe enviarlo para este navegador.")
    return False, None


def run_user_agent_step1(browser_id: int) -> Tuple[bool, Optional[str]]:
    """Alias; mismo comportamiento que run_user_agent_extension_click."""
    return run_user_agent_extension_click(browser_id)


def _cli_main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Muestra / comprueba User-Agent en creator_setting para un navegador "
            "(sin acciones de ratón ni extensión)."
        ),
    )
    p.add_argument(
        "--browser-id",
        type=int,
        default=None,
        metavar="ID",
        help="ID en tabla browsers (si se omite, navegador por defecto)",
    )
    args = p.parse_args(argv)

    bid = resolve_browser_id(args.browser_id)
    if bid is None:
        print("⚠️ Sin navegador; usa --browser-id o define un navegador por defecto en la app.")
        return 1

    ok, ua = run_user_agent_extension_click(bid)
    if ok and ua:
        print(f"✅ User-Agent en BD ({len(ua)} caracteres).")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(_cli_main())
