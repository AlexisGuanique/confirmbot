"""
Acciones **después del éxito** de la cuenta y **antes** de copiar la cookie.

El Creator llama ``run_after_account_success_before_cookie`` desde ``creator._procesar_exito``.
Prueba (desde la raíz del repo), con email y contraseña de la cuenta::

    python -m app.creator.post_account_success_actions --email "tu@correo.com" --password "zmZAj5m4Q&41"

Opcional: ``--browser-id 1`` si no quieres usar el navegador por defecto de la BD.

Resumen: … → login → F5 → caso 1 / 2 según imagen; si no hay ninguna, **caso 3** (cerrar pestaña, nueva, LinkedIn, 10s, re-detectar) → «Try Premium» → cookie.
"""
from __future__ import annotations

import time

IMAGE_LINKEDIN_PERFECTO = "Linkedin Perfecto"
IMAGE_TRY_PREMIUM = "Try Premium"
IMAGE_EUROPA = "Europa"

COORD_NEW_TAB = "new_tab_click"
COORD_LINKEDIN_NEW_TAB = "linkedin_new_tab_click"
COORD_PASTE_PASSWORD = "paste_password_click"
COORD_CLIC_EMAIL = "clic_email_click"
COORD_CLOSE_TAB = "close_tab_click"
COORD_USER_OPTIONS = "user_options_click"
COORD_LOGOUT = "logout_click"
COORD_EUROPA = "europa_click"
LINKEDIN_PERFECTO_MAX_SEC = 60.0
LINKEDIN_PERFECTO_POLL_SEC = 2.0
TRY_PREMIUM_MAX_SEC = 60.0
TRY_PREMIUM_POLL_SEC = 2.0
POST_NEW_TAB_WAIT_SEC = 1.0
POST_LINKEDIN_LOAD_WAIT_SEC = 7.5
POST_REFRESH_WAIT_SEC = 15.0
POST_AFTER_REFRESH_SETTLE_SEC = 3.0
POST_AFTER_F5_EXTRA_WAIT_SEC = 10.0
POST_CASE_DETECT_MAX_SEC = 10.0
POST_CASE_DETECT_POLL_SEC = 1.5
POST_SECOND_CASE_WAIT_SEC = 7.5
POST_LOGOUT_BEFORE_CLOSE_TAB_WAIT_SEC = 8.0
# Caso 3: tras F5 no apareció Try Premium ni Linkedin Perfecto — reapertura de pestaña y segunda detección.
POST_CASE3_LINKEDIN_LOAD_WAIT_SEC = 10.0
POST_CASE3_DETECT_MAX_SEC = 45.0
IMAGE_CONFIDENCE = 0.9


def _europa_observer_configured(coordinates, *, browser_name=None) -> bool:
    """
    El observador Europa solo aplica si hay imagen «Europa» en la carpeta del navegador
    y coordenada ``europa_click``; si falta cualquiera, se omite por completo.
    Cualquier error aquí se trata como «no configurado» para no detener el flujo.
    """
    from app.creator.image_config import get_image_path

    try:
        if not coordinates:
            return False
        if not get_image_path(IMAGE_EUROPA, browser_name=browser_name):
            return False
        if not (coordinates.get(COORD_EUROPA) or "").strip():
            return False
        return True
    except Exception:
        return False


def _image_found_strict(image_name: str, *, browser_name=None) -> bool:
    """Doble verificación para bajar falsos positivos."""
    from app.creator.computer_actions import find_creator_image

    loc = find_creator_image(image_name, confidence=IMAGE_CONFIDENCE, browser_name=browser_name)
    if not loc:
        return False
    time.sleep(0.2)
    loc2 = find_creator_image(image_name, confidence=IMAGE_CONFIDENCE, browser_name=browser_name)
    return bool(loc2)


def _wait_linkedin_perfecto(*, browser_name=None, max_sec: float | None = None, coordinates=None) -> bool:
    t0 = time.time()
    limit = LINKEDIN_PERFECTO_MAX_SEC if max_sec is None else max(0.1, min(LINKEDIN_PERFECTO_MAX_SEC, max_sec))
    print(f"[post-exito] Buscando imagen «{IMAGE_LINKEDIN_PERFECTO}» (hasta {int(limit)}s)…")
    while time.time() - t0 < limit:
        if _europa_observer_configured(coordinates, browser_name=browser_name):
            observe_europa_and_click_if_present(coordinates, browser_name=browser_name)
        if _image_found_strict(IMAGE_LINKEDIN_PERFECTO, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_LINKEDIN_PERFECTO}» encontrada (doble verificación).")
            return True
        time.sleep(LINKEDIN_PERFECTO_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_LINKEDIN_PERFECTO}» a tiempo.")
    return False


def _wait_try_premium(*, browser_name=None, max_sec: float | None = None, coordinates=None) -> bool:
    t0 = time.time()
    limit = TRY_PREMIUM_MAX_SEC if max_sec is None else max(0.1, min(TRY_PREMIUM_MAX_SEC, max_sec))
    print(f"[post-exito] Buscando imagen «{IMAGE_TRY_PREMIUM}» (hasta {int(limit)}s)…")
    while time.time() - t0 < limit:
        if _europa_observer_configured(coordinates, browser_name=browser_name):
            observe_europa_and_click_if_present(coordinates, browser_name=browser_name)
        if _image_found_strict(IMAGE_TRY_PREMIUM, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_TRY_PREMIUM}» encontrada (doble verificación).")
            return True
        time.sleep(TRY_PREMIUM_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_TRY_PREMIUM}» a tiempo.")
    return False


def _wait_try_premium_or_linkedin(*, browser_name=None, max_sec: float | None = None, coordinates=None) -> str | None:
    """
    Detecta cuál caso tomar (Try Premium vs pantalla de login Linkedin Perfecto).

    - ``max_sec is None``: primer barrido tras F5 (usa ``POST_CASE_DETECT_MAX_SEC``).
    - ``max_sec`` explícito: tope en segundos (p. ej. caso 3 con ``POST_CASE3_DETECT_MAX_SEC``).
    """
    t0 = time.time()
    limit = POST_CASE_DETECT_MAX_SEC if max_sec is None else max(0.1, float(max_sec))
    print(
        f"[post-exito] Detectando caso («{IMAGE_TRY_PREMIUM}» o «{IMAGE_LINKEDIN_PERFECTO}») "
        f"hasta {int(limit)}s…"
    )
    while time.time() - t0 < limit:
        if _europa_observer_configured(coordinates, browser_name=browser_name):
            observe_europa_and_click_if_present(coordinates, browser_name=browser_name)
        if _image_found_strict(IMAGE_TRY_PREMIUM, browser_name=browser_name):
            print(f"[post-exito] Caso detectado: «{IMAGE_TRY_PREMIUM}».")
            return "try_premium"
        if _image_found_strict(IMAGE_LINKEDIN_PERFECTO, browser_name=browser_name):
            print(f"[post-exito] Caso detectado: «{IMAGE_LINKEDIN_PERFECTO}».")
            return "linkedin_perfecto"
        time.sleep(POST_CASE_DETECT_POLL_SEC)
    print("[post-exito] No se detectó Try Premium ni Linkedin Perfecto a tiempo.")
    return None


def observe_europa_and_click_if_present(coordinates, *, browser_name=None) -> bool:
    """
    Observador: si la imagen «Europa» está en pantalla (doble verificación),
    hace clic en la coordenada ``europa_click`` tras **1 s** de espera (no es inmediato).
    Si falta imagen en disco, no está en pantalla o falla el clic, devuelve False y
    **no interrumpe** el flujo que lo llamó (tampoco ante excepciones).

    En el flujo principal solo se llama cuando ``_europa_observer_configured`` es True
    (imagen + coordenada); sin esa configuración no se intenta detección ni clic.
    """
    from app.creator.computer_actions import click_coordinates
    from app.creator.image_config import get_image_path

    try:
        if not coordinates:
            return False
        if not get_image_path(IMAGE_EUROPA, browser_name=browser_name):
            return False
        coord = (coordinates.get(COORD_EUROPA) or "").strip()
        if not coord:
            return False
        if not _image_found_strict(IMAGE_EUROPA, browser_name=browser_name):
            return False
        print("[post-exito] Observador Europa: imagen detectada; esperando 1s antes del clic…")
        time.sleep(1.0)
        print(f"[post-exito] Observador Europa: clic en «{COORD_EUROPA}»")
        if not click_coordinates(coord, double_click=False):
            print("[post-exito] Observador Europa: falló el clic en la coordenada.")
            return False
        time.sleep(0.5)
        return True
    except Exception as e:
        print(
            f"[post-exito] Observador Europa: error no crítico (se continúa el ciclo): "
            f"{type(e).__name__}: {e}"
        )
        return False


def _resolve_account_password(password: str) -> str:
    account_password = ""
    try:
        from app.creator.creator import _get_password_usado

        account_password = (_get_password_usado() or "").strip()
    except Exception:
        pass
    if not account_password:
        account_password = (password or "").strip()
    return account_password


def run_after_account_success_before_cookie(
    coordinates,
    email,
    password,
    filepath,
    *,
    exito_image_name=None,
    browser_id=None,
    browser_name=None,
):
    from app.creator.computer_actions import click_coordinates, press_key, type_text
    from app.creator.image_config import get_image_path
    import pyautogui

    def _coord(key: str):
        c = (coordinates.get(key) or "").strip()
        return c if c else None

    def _click_or_fail(coord: str, label: str) -> bool:
        if not click_coordinates(coord, double_click=False):
            print(f"[post-exito] Falló clic en {label}.")
            return False
        return True

    def _focus_clear_and_paste(coord: str, label: str, text: str) -> bool:
        """Hace clic en el campo, limpia contenido y pega texto."""
        if not _click_or_fail(coord, label):
            return False
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.1)
        press_key("backspace")
        time.sleep(0.1)
        if not type_text(text):
            print(f"[post-exito] Falló pegado en {label}.")
            return False
        time.sleep(0.15)
        return True

    def _run_relogin_case2_sequence() -> bool:
        """Secuencia completa para el caso 2 con reintento de reapertura."""
        def _reopen_and_wait_linkedin() -> bool:
            if not _click_or_fail(ct, COORD_CLOSE_TAB):
                return False
            time.sleep(0.8)
            print("[post-exito] Clic abrir nueva pestaña")
            if not _click_or_fail(nt, COORD_NEW_TAB):
                return False
            time.sleep(POST_NEW_TAB_WAIT_SEC)
            print("[post-exito] Clic LinkedIn en nueva pestaña (favoritos)")
            if not _click_or_fail(lnt, COORD_LINKEDIN_NEW_TAB):
                return False
            print(f"[post-exito] Esperando {int(POST_LINKEDIN_LOAD_WAIT_SEC)}s para carga de LinkedIn…")
            time.sleep(POST_LINKEDIN_LOAD_WAIT_SEC)
            if not _wait_linkedin_perfecto(browser_name=browser_name, coordinates=coordinates):
                return False
            return True

        if not _reopen_and_wait_linkedin():
            print("[post-exito] No apareció Linkedin Perfecto; reintentando cerrar/reabrir pestaña una vez…")
            if not _reopen_and_wait_linkedin():
                return False

        print("[post-exito] Completar casilla email")
        if not _focus_clear_and_paste(ce, COORD_CLIC_EMAIL, (email or "").strip()):
            return False
        print("[post-exito] Completar casilla password")
        if not _focus_clear_and_paste(cp, COORD_PASTE_PASSWORD, account_password):
            return False
        print("[post-exito] Enter para enviar login (caso 2)")
        press_key("enter")
        print(f"[post-exito] Esperando {int(POST_SECOND_CASE_WAIT_SEC)}s antes de validar Try Premium…")
        time.sleep(POST_SECOND_CASE_WAIT_SEC)
        return _wait_try_premium(browser_name=browser_name, coordinates=coordinates)

    account_email = (email or "").strip()
    account_password = _resolve_account_password(password)
    if not account_email:
        print("[post-exito] Falta email de la cuenta.")
        return False
    if not account_password:
        print("[post-exito] Falta contraseña (_get_password_usado / argumento).")
        return False

    if not get_image_path(IMAGE_LINKEDIN_PERFECTO, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_LINKEDIN_PERFECTO}» en la carpeta del navegador.")
        return False
    if not get_image_path(IMAGE_TRY_PREMIUM, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_TRY_PREMIUM}» en la carpeta del navegador.")
        return False

    nt = _coord(COORD_NEW_TAB)
    lnt = _coord(COORD_LINKEDIN_NEW_TAB)
    cp = _coord(COORD_PASTE_PASSWORD)
    ce = _coord(COORD_CLIC_EMAIL)
    ct = _coord(COORD_CLOSE_TAB)
    cu = _coord(COORD_USER_OPTIONS)
    lo = _coord(COORD_LOGOUT)

    for key, label in [
        (nt, COORD_NEW_TAB),
        (lnt, COORD_LINKEDIN_NEW_TAB),
        (ct, COORD_CLOSE_TAB),
        (ce, COORD_CLIC_EMAIL),
        (cp, COORD_PASTE_PASSWORD),
        (cu, COORD_USER_OPTIONS),
        (lo, COORD_LOGOUT),
    ]:
        if not key:
            print(f"[post-exito] Falta coordenada {label!r}")
            return False

    print("[post-exito] Clic abrir nueva pestaña")
    if not _click_or_fail(nt, COORD_NEW_TAB):
        return False
    print(f"[post-exito] Esperando {int(POST_NEW_TAB_WAIT_SEC)}s antes del siguiente clic…")
    time.sleep(POST_NEW_TAB_WAIT_SEC)

    print("[post-exito] Clic LinkedIn en nueva pestaña (favoritos)")
    if not _click_or_fail(lnt, COORD_LINKEDIN_NEW_TAB):
        return False
    print(f"[post-exito] Esperando {int(POST_LINKEDIN_LOAD_WAIT_SEC)}s para carga de LinkedIn…")
    time.sleep(POST_LINKEDIN_LOAD_WAIT_SEC)

    if not _wait_linkedin_perfecto(browser_name=browser_name, coordinates=coordinates):
        return False

    print("[post-exito] Completar casilla email")
    if not _focus_clear_and_paste(ce, COORD_CLIC_EMAIL, account_email):
        return False
    print("[post-exito] Completar casilla password")
    if not _focus_clear_and_paste(cp, COORD_PASTE_PASSWORD, account_password):
        return False

    print("[post-exito] Enter para enviar login")
    press_key("enter")
    time.sleep(0.5)

    print(f"[post-exito] Esperando {int(POST_REFRESH_WAIT_SEC)}s antes de refrescar…")
    time.sleep(POST_REFRESH_WAIT_SEC)
    print("[post-exito] Refrescar LinkedIn con F5")
    press_key("f5")
    time.sleep(POST_AFTER_REFRESH_SETTLE_SEC)
    print(f"[post-exito] Esperando {int(POST_AFTER_F5_EXTRA_WAIT_SEC)}s extra tras F5…")
    time.sleep(POST_AFTER_F5_EXTRA_WAIT_SEC)

    case_detected = _wait_try_premium_or_linkedin(browser_name=browser_name, coordinates=coordinates)
    if case_detected is None:
        print(
            "[post-exito] Caso 3: tras F5 no apareció Try Premium ni Linkedin Perfecto; "
            "recuperación: cerrar pestaña → nueva pestaña → LinkedIn → "
            f"{int(POST_CASE3_LINKEDIN_LOAD_WAIT_SEC)}s → re-detectar."
        )
        print("[post-exito] Caso 3: cerrar pestaña")
        if not _click_or_fail(ct, COORD_CLOSE_TAB):
            return False
        time.sleep(0.8)
        print("[post-exito] Caso 3: nueva pestaña")
        if not _click_or_fail(nt, COORD_NEW_TAB):
            return False
        time.sleep(POST_NEW_TAB_WAIT_SEC)
        print("[post-exito] Caso 3: clic LinkedIn (favoritos; necesario para ver las plantillas)")
        if not _click_or_fail(lnt, COORD_LINKEDIN_NEW_TAB):
            return False
        print(
            f"[post-exito] Caso 3: esperando {int(POST_CASE3_LINKEDIN_LOAD_WAIT_SEC)}s antes de re-verificar…"
        )
        time.sleep(POST_CASE3_LINKEDIN_LOAD_WAIT_SEC)
        case_detected = _wait_try_premium_or_linkedin(
            browser_name=browser_name,
            max_sec=POST_CASE3_DETECT_MAX_SEC,
            coordinates=coordinates,
        )
        if case_detected is None:
            print("[post-exito] Caso 3: sin Try Premium ni Linkedin Perfecto tras recuperación.")
            return False
        if case_detected == "try_premium":
            print(
                "[post-exito] Caso 3: Try Premium tras recuperación "
                "(sesión deslogueada tras F5); listo para tomar cookie."
            )
            return True
        print("[post-exito] Caso 3: Linkedin Perfecto tras recuperación; login y búsqueda de Try Premium.")
        if not _focus_clear_and_paste(ce, COORD_CLIC_EMAIL, account_email):
            return False
        if not _focus_clear_and_paste(cp, COORD_PASTE_PASSWORD, account_password):
            return False
        print("[post-exito] Enter para enviar login (caso 3)")
        press_key("enter")
        time.sleep(0.5)
        print(f"[post-exito] Esperando {int(POST_SECOND_CASE_WAIT_SEC)}s antes de buscar Try Premium…")
        time.sleep(POST_SECOND_CASE_WAIT_SEC)
        if not _wait_try_premium(browser_name=browser_name, coordinates=coordinates):
            return False
        print("[post-exito] Caso 3 completado: Try Premium detectado, listo para tomar cookie.")
        return True

    # Caso 1: si Try Premium aparece, completar secuencia de deslogueo y re-login rápido.
    if case_detected == "try_premium":
        print("[post-exito] Caso 1: Try Premium detectado -> deslogueo de usuario.")
        print("[post-exito] Clic opciones de usuario")
        if not _click_or_fail(cu, COORD_USER_OPTIONS):
            return False
        time.sleep(1.0)
        print("[post-exito] Clic Logout")
        if not _click_or_fail(lo, COORD_LOGOUT):
            return False
        time.sleep(1.0)
        print(f"[post-exito] Esperando {int(POST_LOGOUT_BEFORE_CLOSE_TAB_WAIT_SEC)}s tras Logout antes de cerrar pestaña…")
        time.sleep(POST_LOGOUT_BEFORE_CLOSE_TAB_WAIT_SEC)

        print("[post-exito] Post-logout: cerrar pestaña, abrir nueva y volver a LinkedIn.")
        if not _click_or_fail(ct, COORD_CLOSE_TAB):
            return False
        time.sleep(0.8)
        print("[post-exito] Clic abrir nueva pestaña")
        if not _click_or_fail(nt, COORD_NEW_TAB):
            return False
        time.sleep(POST_NEW_TAB_WAIT_SEC)
        print("[post-exito] Clic LinkedIn en nueva pestaña (favoritos)")
        if not _click_or_fail(lnt, COORD_LINKEDIN_NEW_TAB):
            return False
        print(f"[post-exito] Esperando {int(POST_LINKEDIN_LOAD_WAIT_SEC)}s para carga de LinkedIn…")
        time.sleep(POST_LINKEDIN_LOAD_WAIT_SEC)
        if not _wait_linkedin_perfecto(browser_name=browser_name, coordinates=coordinates):
            return False

        print("[post-exito] Completar casilla email")
        if not _focus_clear_and_paste(ce, COORD_CLIC_EMAIL, account_email):
            return False
        print("[post-exito] Completar casilla password")
        if not _focus_clear_and_paste(cp, COORD_PASTE_PASSWORD, account_password):
            return False
        print("[post-exito] Enter para enviar login (caso 1)")
        press_key("enter")
        print(f"[post-exito] Esperando {int(POST_SECOND_CASE_WAIT_SEC)}s antes de buscar Try Premium…")
        time.sleep(POST_SECOND_CASE_WAIT_SEC)
        if not _wait_try_premium(browser_name=browser_name, coordinates=coordinates):
            return False
        print("[post-exito] Caso 1 completado: Try Premium detectado, listo para tomar cookie.")
        return True

    # Caso 2: no entró en caso 1; rehacer login con reapertura de pestaña.
    print("[post-exito] Caso 2: rehacer login con cierre/reapertura de pestaña.")
    if not _run_relogin_case2_sequence():
        return False
    print("[post-exito] Caso 2 completado: Try Premium detectado, listo para tomar cookie.")
    return True


def _run_cli() -> int:
    import argparse
    import tempfile
    from pathlib import Path

    from app.database.database import (
        get_browser_by_id,
        get_creator_coordinates,
        get_default_browser,
    )

    def bid_or_default(x):
        if x is not None:
            return x
        b = get_default_browser()
        return b["id"] if b else None

    fp_default = str(Path(tempfile.gettempdir()) / "confirmbot_post_success_cli_filepath.txt")
    p = argparse.ArgumentParser()
    p.add_argument("--browser-id", type=int, default=None)
    p.add_argument("--email", default="cli_test@example.invalid")
    p.add_argument("--password", default="cli_test_password")
    p.add_argument("--filepath", default=fp_default)
    p.add_argument("--exito-image", default=None)
    a = p.parse_args()

    bid = bid_or_default(a.browser_id)
    if bid is None:
        print("[post-exito] Sin navegador en BD.")
        return 1
    coords = get_creator_coordinates(bid)
    if not coords:
        print(f"[post-exito] Sin coordenadas Creator (browser_id={bid}).")
        return 1
    b = get_browser_by_id(bid)
    name = b["name"] if b else None
    print(f"[info] browser_id={bid} name={name!r}")
    run_after_account_success_before_cookie(
        coords,
        a.email,
        a.password,
        a.filepath,
        exito_image_name=a.exito_image,
        browser_id=bid,
        browser_name=name,
    )
    print("[ok] Listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_cli())
