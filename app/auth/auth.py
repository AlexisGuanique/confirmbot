
import requests
from app.database.database import save_user, delete_logged_in_user, get_logged_in_user


BASE_API_URL = "http://35.209.237.44/api/auth"

LOGIN_URL = f"{BASE_API_URL}/login"
VERIFY_TOKEN_URL = f"{BASE_API_URL}/verify-token"


def login(username, password):
    payload = {"username": username, "password": password}

    try:
        response = requests.post(LOGIN_URL, json=payload)

        try:
            response_data = response.json()
        except ValueError:
            return {"error": "Error al procesar la respuesta del servidor"}

        if response.status_code != 200:
            return response_data 

        if "access_token" in response_data:
            user_data = {
                "id": response_data.get("id"),
                "name": response_data.get("name"),
                "lastname": response_data.get("lastname"),
                "access_token": response_data.get("access_token"),
            }
            save_user(user_data)


            return response_data  

        return {"error": "Respuesta inesperada del servidor"}

    except requests.RequestException as e:
        print(f"Error de conexión: {e}")
        return {"error": "Error de conexión con el servidor"}


def logout():

    if delete_logged_in_user():
        return True
    else:
        return False


def verify_token():

    user = get_logged_in_user()

    if not user:
        return {"is_valid": False}  

    access_token = user.get("access_token")
    user_id = user.get("id")

    if not access_token:
        return {"is_valid": False}

    payload = {"access_token": access_token}
    url = f"{VERIFY_TOKEN_URL}/{user_id}"

    try:
        response = requests.post(url, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return response_data  
        else:
            return {"is_valid": False}

    except requests.RequestException as e:
        print(f"Error de conexión al verificar el token: {e}")
        return {"is_valid": False}
