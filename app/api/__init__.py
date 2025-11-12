# app/api/__init__.py
from flask import Blueprint
from flask_restx import Api

# Импортируем все наши "разделы" (namespaces) из соседних файлов
from .auth import api as auth_ns 
from .profile import api as profile_ns
from .chat import api as chat_ns

# --- ВОТ КЛЮЧЕВАЯ ЧАСТЬ ---
# Эта строка создает объект Blueprint и присваивает его переменной 'blueprint'
# Именно эту переменную не смог найти Python в вашем коде.
blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

# Настраиваем JWT для кнопки "Authorize" в Swagger UI
authorizations = {
    'jwt': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    }
}

# Инициализируем объект Api, передавая ему наш blueprint
api = Api(
    blueprint,
    title='AlphaAssistant API',
    version='1.0',
    description='API для бизнес-помощника на базе LLM',
    authorizations=authorizations,
    security='jwt'
)

# Добавляем все наши разделы в основной объект API
api.add_namespace(auth_ns)
api.add_namespace(profile_ns)
api.add_namespace(chat_ns)