# app/services/llm_clients.py
import requests
import uuid
from flask import current_app

# --- GigaChat Client ---

def get_gigachat_token():
    """
    Получает временный токен доступа для GigaChat API, используя единый ключ авторизации.
    """
    # Получаем единый ключ из конфигурации
    auth_credentials_base64 = current_app.config['GIGACHAT_AUTH_CREDENTIALS']
    
    if not auth_credentials_base64:
        print("Ошибка конфигурации: GIGACHAT_AUTH_CREDENTIALS не найден в .env")
        return None, "Ошибка: Учетные данные для GigaChat не настроены."

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    # Формируем заголовки. Теперь аутентификация передается в заголовке 'Authorization'.
    # Это стандартный способ для OAuth2 Client Credentials.
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {auth_credentials_base64}' # Используем наш ключ
    }
    
    payload = {'scope': 'GIGACHAT_API_PERS'}
    
    try:
        # В запросе больше не нужен параметр 'auth', так как все есть в заголовках
        response = requests.post(url, headers=headers, data=payload, verify=False, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data['access_token'], None
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if e.response else "No response from server"
        print(f"Ошибка получения токена GigaChat: {e}\nDetails: {error_details}")
        return None, f"Ошибка аутентификации GigaChat. Проверьте ваш GIGACHAT_AUTH_CREDENTIALS."


def get_gigachat_response(system_prompt, dialog_history, user_message):
    """Отправляет запрос к GigaChat API и возвращает ответ. (Этот код не меняется)"""
    access_token, error = get_gigachat_token()
    if error:
        return error

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    messages = [{"role": "system", "content": system_prompt}]
    for line in dialog_history.split('\n'):
        if ': ' in line:
            role, content = line.split(': ', 1)
            messages.append({"role": role.lower(), "content": content})
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": "GigaChat:latest",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if e.response else "No response from server"
        print(f"Ошибка при обращении к GigaChat API: {e}\nDetails: {error_details}")
        return f"Извините, произошла ошибка при обращении к GigaChat."

# --- YandexGPT Client ---

def get_yandexgpt_response(system_prompt, dialog_history, user_message):
    """Отправляет запрос к API YandexGPT и возвращает текстовый ответ."""
    api_key = current_app.config['YANDEX_API_KEY']
    folder_id = current_app.config['YANDEX_FOLDER_ID']
    
    if not api_key or not folder_id:
        print("Ошибка конфигурации: Ключи API для YandexGPT не найдены.")
        return "Ошибка: Ключи API для YandexGPT не настроены в конфигурации."

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {api_key}"}
    
    # YandexGPT предпочитает более простую структуру: системный промпт и один промпт от пользователя,
    # который содержит всю историю и новый вопрос.
    full_user_prompt = f"История диалога:\n{dialog_history}\n\nТекущий вопрос: {user_message}"
    
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": "2000"},
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": full_user_prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['result']['alternatives'][0]['message']['text']
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к YandexGPT API: {e}")
        error_details = e.response.text if e.response else 'No response from server'
        print(f"Ответ от сервера: {error_details}")
        return f"Извините, произошла ошибка при обращении к ассистенту. (Детали: {e})"