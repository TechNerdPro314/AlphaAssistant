# app/api/profile.py

from flask import request
from flask_restx import Namespace, Resource, fields
from app.models import BusinessProfile
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

# Создаем Namespace для профиля
api = Namespace('profile', description='Операции с бизнес-профилем пользователя')

# Модель для данных (DTO), описывающая бизнес-профиль
business_profile_model = api.model('BusinessProfile', {
    'industry': fields.String(required=True, description='Отрасль бизнеса'),
    'company_size': fields.String(required=True, description='Размер компании (например, 1-10 сотрудников)'),
    'goals': fields.String(required=True, description='Основные цели и задачи бизнеса'),
})

# Модель для ответа, включающая ID и дату создания
business_profile_response_model = api.inherit('BusinessProfileResponse', business_profile_model, {
    'id': fields.Integer(readOnly=True),
    'user_id': fields.Integer(readOnly=True),
    'created_at': fields.DateTime(readOnly=True)
})


@api.route('/')
class ProfileResource(Resource):
    
    # Метод GET для получения профиля
    @api.doc(security='jwt') # Указываем в Swagger, что нужна авторизация
    @jwt_required() # Защищаем эндпоинт, требуем JWT токен
    @api.marshal_with(business_profile_response_model) # Форматируем ответ
    @api.response(404, 'Профиль не найден.')
    def get(self):
        """Получить бизнес-профиль текущего пользователя"""
        current_user_id = int(get_jwt_identity())
        profile = BusinessProfile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            api.abort(404, 'Профиль для данного пользователя не найден.')
            
        return profile

    # Метод POST для создания/обновления профиля
    @api.doc(security='jwt')
    @jwt_required()
    @api.expect(business_profile_model, validate=True) # Ожидаем данные в формате модели
    @api.marshal_with(business_profile_response_model)
    @api.response(201, 'Профиль успешно создан.')
    @api.response(200, 'Профиль успешно обновлен.')
    def post(self):
        """Создать или обновить бизнес-профиль текущего пользователя"""
        current_user_id = int(get_jwt_identity())
        data = request.json
        
        profile = BusinessProfile.query.filter_by(user_id=current_user_id).first()
        
        if profile:
            # Если профиль уже существует - обновляем его
            profile.industry = data['industry']
            profile.company_size = data['company_size']
            profile.goals = data['goals']
            db.session.commit()
            return profile, 200 # OK
        else:
            # Если профиля нет - создаем новый
            new_profile = BusinessProfile(
                user_id=current_user_id,
                industry=data['industry'],
                company_size=data['company_size'],
                goals=data['goals']
            )
            db.session.add(new_profile)
            db.session.commit()
            return new_profile, 201 
        
@api.route('/link_telegram')
class LinkTelegram(Resource):
    @api.doc(security='jwt')
    @jwt_required()
    @api.expect(api.model('LinkTelegramModel', {
        'telegram_id': fields.String(required=True, description='Уникальный ID пользователя в Telegram')
    }))
    @api.response(200, 'Telegram аккаунт успешно привязан.')
    @api.response(409, 'Этот Telegram аккаунт уже используется.')
    @api.response(404, 'Пользователь не найден.')
    def post(self):
        """Привязать Telegram ID к текущему пользователю"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            api.abort(404, 'Пользователь не найден.')

        data = request.json
        telegram_id = data['telegram_id']

        # Проверка, не занят ли этот telegram_id другим пользователем
        existing_user = User.query.filter_by(telegram_id=telegram_id).first()
        if existing_user and existing_user.id != current_user_id:
            api.abort(409, 'Этот Telegram аккаунт уже привязан к другому пользователю.')

        user.telegram_id = str(telegram_id) # Сохраняем как строку
        db.session.commit()
        return {'message': 'Telegram аккаунт успешно привязан.'}, 200