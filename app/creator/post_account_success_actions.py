"""
Acciones **después del éxito** de la cuenta y **antes** de copiar la cookie.

El Creator llama ``run_after_account_success_before_cookie`` desde ``creator._procesar_exito``.
Prueba (desde la raíz del repo), con email y contraseña de la cuenta::

    python -m app.creator.post_account_success_actions --email "tu@correo.com" --password "zmZAj5m4Q&41"

Opcional: ``--browser-id 1`` si no quieres usar el navegador por defecto de la BD.

Resumen: … → Logout ×2 → imagen «Jobs Images» → clic Jobs → login with email → … → «Try Premium» final → cookie.
"""
from __future__ import annotations

import time

LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
IMAGE_TRY_PREMIUM = "Try Premium"
IMAGE_JOBS_IMAGES = "Jobs Images"
IMAGE_LOGIN_WITH_EMAIL = "Login With Email"
IMAGE_LINKEDIN_PERFECTO = "Linkedin Perfecto"

COORD_SEARCH_BAR = "search_bar_click"
COORD_USER_OPTIONS = "user_options_click"
COORD_LOGOUT = "logout_click"
COORD_JOBS = "jobs_click"
COORD_LOGIN_WITH_EMAIL = "login_with_email_click"
COORD_CLIC_EMAIL = "clic_email_click"
COORD_LINKEDIN_LOGO = "linkedin_logo_click"

TRY_PREMIUM_MAX_SEC = 120.0
TRY_PREMIUM_POLL_SEC = 2.0
JOBS_IMAGES_MAX_SEC = 120.0
JOBS_IMAGES_POLL_SEC = 2.0
LOGIN_WITH_EMAIL_MAX_SEC = 120.0
LOGIN_WITH_EMAIL_POLL_SEC = 2.0
LINKEDIN_PERFECTO_MAX_SEC = 120.0
LINKEDIN_PERFECTO_POLL_SEC = 2.0
PRE_WAIT_BEFORE_JOBS_SEARCH_SEC = 20.0
PRE_WAIT_BEFORE_LOGIN_WITH_EMAIL_SEARCH_SEC = 15.0
POST_SUBMIT_WAIT_BEFORE_LINKEDIN_PERFECTO_SEC = 15.0
POST_LOGO_WAIT_BEFORE_TRY_PREMIUM_SEC = 30.0
IMAGE_CONFIDENCE = 0.9


def _image_found_strict(image_name: str, *, browser_name=None) -> bool:
    """Doble verificación para bajar falsos positivos."""
    from app.creator.computer_actions import find_creator_image

    loc = find_creator_image(image_name, confidence=IMAGE_CONFIDENCE, browser_name=browser_name)
    if not loc:
        return False
    time.sleep(0.2)
    loc2 = find_creator_image(image_name, confidence=IMAGE_CONFIDENCE, browser_name=browser_name)
    return bool(loc2)


def _wait_jobs_images(*, browser_name=None) -> bool:
    t0 = time.time()
    print(f"[post-exito] Buscando imagen «{IMAGE_JOBS_IMAGES}» (hasta {int(JOBS_IMAGES_MAX_SEC)}s)…")
    while time.time() - t0 < JOBS_IMAGES_MAX_SEC:
        if _image_found_strict(IMAGE_JOBS_IMAGES, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_JOBS_IMAGES}» encontrada (doble verificación).")
            return True
        time.sleep(JOBS_IMAGES_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_JOBS_IMAGES}» a tiempo.")
    return False




def _wait_login_with_email_image(*, browser_name=None) -> bool:
    t0 = time.time()
    print(f"[post-exito] Buscando imagen «{IMAGE_LOGIN_WITH_EMAIL}» (hasta {int(LOGIN_WITH_EMAIL_MAX_SEC)}s)…")
    while time.time() - t0 < LOGIN_WITH_EMAIL_MAX_SEC:
        if _image_found_strict(IMAGE_LOGIN_WITH_EMAIL, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_LOGIN_WITH_EMAIL}» encontrada (doble verificación).")
            return True
        time.sleep(LOGIN_WITH_EMAIL_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_LOGIN_WITH_EMAIL}» a tiempo.")
    return False


def _wait_try_premium(*, browser_name=None) -> bool:
    t0 = time.time()
    print(f"[post-exito] Buscando imagen «{IMAGE_TRY_PREMIUM}» (hasta {int(TRY_PREMIUM_MAX_SEC)}s)…")
    while time.time() - t0 < TRY_PREMIUM_MAX_SEC:
        if _image_found_strict(IMAGE_TRY_PREMIUM, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_TRY_PREMIUM}» encontrada (doble verificación).")
            return True
        time.sleep(TRY_PREMIUM_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_TRY_PREMIUM}» a tiempo.")
    return False


def _wait_linkedin_perfecto(*, browser_name=None) -> bool:
    t0 = time.time()
    print(f"[post-exito] Buscando imagen «{IMAGE_LINKEDIN_PERFECTO}» (hasta {int(LINKEDIN_PERFECTO_MAX_SEC)}s)…")
    while time.time() - t0 < LINKEDIN_PERFECTO_MAX_SEC:
        if _image_found_strict(IMAGE_LINKEDIN_PERFECTO, browser_name=browser_name):
            print(f"[post-exito] Imagen «{IMAGE_LINKEDIN_PERFECTO}» encontrada (doble verificación).")
            return True
        time.sleep(LINKEDIN_PERFECTO_POLL_SEC)
    print(f"[post-exito] No apareció «{IMAGE_LINKEDIN_PERFECTO}» a tiempo.")
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

    account_email = (email or "").strip()
    account_password = _resolve_account_password(password)
    if not account_email:
        print("[post-exito] Falta email de la cuenta.")
        return False
    if not account_password:
        print("[post-exito] Falta contraseña (_get_password_usado / argumento).")
        return False

    if not get_image_path(IMAGE_TRY_PREMIUM, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_TRY_PREMIUM}» en la carpeta del navegador.")
        return False
    if not get_image_path(IMAGE_JOBS_IMAGES, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_JOBS_IMAGES}» en la carpeta del navegador.")
        return False
    if not get_image_path(IMAGE_LOGIN_WITH_EMAIL, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_LOGIN_WITH_EMAIL}» en la carpeta del navegador.")
        return False
    if not get_image_path(IMAGE_LINKEDIN_PERFECTO, browser_name=browser_name):
        print(f"[post-exito] Falta imagen «{IMAGE_LINKEDIN_PERFECTO}» en la carpeta del navegador.")
        return False

    c_bar = _coord(COORD_SEARCH_BAR)
    if not c_bar:
        print(f"[post-exito] Falta coordenada {COORD_SEARCH_BAR!r}")
        return False

    print("[post-exito] Clic barra de búsqueda → Ctrl+A → pegar URL feed → Enter")
    click_coordinates(c_bar)
    time.sleep(0.35)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.15)
    type_text(LINKEDIN_FEED_URL)
    time.sleep(0.2)
    press_key("enter")
    print("Esperando 30 segundos para que cargue la página...")
    time.sleep(30)

    if not _wait_try_premium(browser_name=browser_name):
        return False

    cu = _coord(COORD_USER_OPTIONS)
    lo = _coord(COORD_LOGOUT)
    jb = _coord(COORD_JOBS)
    lw = _coord(COORD_LOGIN_WITH_EMAIL)
    ce = _coord(COORD_CLIC_EMAIL)
    ll = _coord(COORD_LINKEDIN_LOGO)
    for key, label in [
        (cu, COORD_USER_OPTIONS),
        (lo, COORD_LOGOUT),
        (jb, COORD_JOBS),
        (lw, COORD_LOGIN_WITH_EMAIL),
        (ce, COORD_CLIC_EMAIL),
        (ll, COORD_LINKEDIN_LOGO),
    ]:
        if not key:
            print(f"[post-exito] Falta coordenada {label!r}")
            return False

    print("[post-exito] Clic opciones de usuario")
    click_coordinates(cu)
    time.sleep(1.0)
    print("[post-exito] Clic Logout")
    click_coordinates(lo)
    time.sleep(1.0)
    print("[post-exito] Segundo clic Logout")
    click_coordinates(lo)
    time.sleep(1.0)

    print(f"[post-exito] Esperando {int(PRE_WAIT_BEFORE_JOBS_SEARCH_SEC)}s antes de buscar Jobs Images…")
    time.sleep(PRE_WAIT_BEFORE_JOBS_SEARCH_SEC)
    if not _wait_jobs_images(browser_name=browser_name):
        return False
    print("[post-exito] Clic Jobs")
    click_coordinates(jb)
    time.sleep(0.5)

    print(f"[post-exito] Esperando {int(PRE_WAIT_BEFORE_LOGIN_WITH_EMAIL_SEARCH_SEC)}s antes de buscar Login With Email…")
    time.sleep(PRE_WAIT_BEFORE_LOGIN_WITH_EMAIL_SEARCH_SEC)
    if not _wait_login_with_email_image(browser_name=browser_name):
        return False
    print("[post-exito] Clic login with email")
    click_coordinates(lw)
    time.sleep(2.0)
    print("[post-exito] Clic Email → pegar email → Tab → pegar password → Tab×3 → Enter")
    click_coordinates(ce)
    time.sleep(0.3)
    type_text(account_email)
    time.sleep(0.15)
    press_key("tab")
    time.sleep(0.15)
    type_text(account_password)
    time.sleep(0.2)
    for _ in range(3):
        press_key("tab")
        time.sleep(0.1)
    press_key("enter")
    time.sleep(0.4)

    print(
        f"[post-exito] Esperando {int(POST_SUBMIT_WAIT_BEFORE_LINKEDIN_PERFECTO_SEC)}s "
        "antes de buscar Linkedin Perfecto…"
    )
    time.sleep(POST_SUBMIT_WAIT_BEFORE_LINKEDIN_PERFECTO_SEC)
    if not _wait_linkedin_perfecto(browser_name=browser_name):
        return False
    print("[post-exito] Clic logo LinkedIn")
    click_coordinates(ll)
    print(f"[post-exito] Esperando {int(POST_LOGO_WAIT_BEFORE_TRY_PREMIUM_SEC)}s antes de buscar Try Premium…")
    time.sleep(POST_LOGO_WAIT_BEFORE_TRY_PREMIUM_SEC)
    if not _wait_try_premium(browser_name=browser_name):
        return False
    print("[post-exito] Listo para tomar la cookie.")
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
