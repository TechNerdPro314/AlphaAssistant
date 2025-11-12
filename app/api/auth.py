# app/api/auth.py
from flask import request
from flask_restx import Namespace, Resource, fields
from app.models import User
from app import db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Создаем Namespace - это как "раздел" нашего API. Все эндпоинты здесь будут с префиксом /auth
api = Namespace('auth', description='Операции аутентификации')

# Модели для данных (DTO - Data Transfer Object)
# Flask-RESTx использует их для валидации входящих данных и для генерации документации
user_register_model = api.model('UserRegister', {
    'email': fields.String(required=True, description='Email пользователя'),
    'password': fields.String(required=True, description='Пароль пользователя'),
})

user_login_model = api.model('UserLogin', {
    'email': fields.String(required=True, description='Email пользователя'),
    'password': fields.String(required=True, description='Пароль пользователя'),
})

# Модель для ответа с токеном
token_model = api.model('Token', {
    'access_token': fields.String(description='JWT токен доступа')
})

user_me_model = api.model('UserMe', {
    'id': fields.Integer,
    'email': fields.String,
    'telegram_id': fields.String,
    'created_at': fields.DateTime
})

@api.route('/register')
class UserRegistration(Resource):
    @api.expect(user_register_model, validate=True) # Ожидаем данные в формате user_register_model
    @api.response(201, 'Пользователь успешно создан.')
    @api.response(400, 'Некорректный запрос.')
    @api.response(409, 'Пользователь с таким email уже существует.')
    def post(self):
        """Регистрация нового пользователя"""
        data = request.json
        if User.query.filter_by(email=data['email']).first():
            return {'message': 'Пользователь с таким email уже существует'}, 409 # Conflict

        new_user = User(email=data['email'])
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        
        return {'message': 'Пользователь успешно создан'}, 201

@api.route('/login')
class UserLogin(Resource):
    @api.expect(user_login_model, validate=True)
    @api.marshal_with(token_model) # Форматируем успешный ответ согласно token_model
    @api.response(401, 'Неверные учетные данные.')
    def post(self):
        """Вход пользователя и получение JWT токена"""
        data = request.json
        user = User.query.filter_by(email=data['email']).first()

        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}
        
        return {'message': 'Неверные учетные данные'}, 401

@api.route('/me')
class UserMe(Resource):
    @jwt_required() # Эта строка защищает эндпоинт. Нужен валидный JWT токен в заголовках.
    @api.marshal_with(user_me_model)
    @api.doc(security='jwt') # Указываем в документации, что нужен JWT
    def get(self):
        """Получение данных о текущем пользователе"""
        current_user_id = get_jwt_identity() # Получаем id пользователя из токена
        user = User.query.get(current_user_id)
        return user