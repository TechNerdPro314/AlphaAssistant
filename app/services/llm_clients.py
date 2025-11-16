# app/services/llm_clients.py
import requests
import uuid
from flask import current_app


def get_gigachat_token():
    auth_credentials_base64 = current_app.config["GIGACHAT_AUTH_CREDENTIALS"]

    if auth_credentials_base64:
        auth_credentials_base64 = auth_credentials_base64.strip("\"'")

    if not auth_credentials_base64:
        print("Ошибка конфигурации: GIGACHAT_AUTH_CREDENTIALS не найден в .env")
        return None, "Ошибка: Учетные данные для GigaChat не настроены."

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {auth_credentials_base64}",
    }

    payload = {"scope": "GIGACHAT_API_PERS"}

    try:
        response = requests.post(
            url, headers=headers, data=payload, verify=False, timeout=10
        )
        response.raise_for_status()

        token_data = response.json()
        return token_data["access_token"], None
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if e.response else "No response from server"
        print(f"Ошибка получения токена GigaChat: {e}\nDetails: {error_details}")
        return (
            None,
            f"Ошибка аутентификации GigaChat. Проверьте ваш GIGACHAT_AUTH_CREDENTIALS.",
        )


def get_gigachat_response(system_prompt, dialog_history, user_message):
    """Отправляет запрос к GigaChat API и возвращает ответ."""
    access_token, error = get_gigachat_token()
    if error:
        return error

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    messages = [{"role": "system", "content": system_prompt}]
    for line in dialog_history.split("\n"):
        if ": " in line:
            role, content = line.split(": ", 1)
            messages.append({"role": role.lower(), "content": content})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "GigaChat:latest",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, verify=False, timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if e.response else "No response from server"
        print(f"Ошибка при обращении к GigaChat API: {e}\nDetails: {error_details}")
        return f"Извините, произошла ошибка при обращении к GigaChat."
    except KeyError as e:
        print(f"Ошибка обработки ответа от GigaChat API: отсутствует ключ {e}")
        return f"Извините, произошла ошибка при обработке ответа от GigaChat."
