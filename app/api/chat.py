# app/api/chat.py
from flask import request
from flask_restx import Namespace, Resource, fields
from app.models import BusinessProfile, ChatSession, Message
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
# Импортируем наши новые сервисные функции из отдельного модуля
# Убираем импорт get_yandexgpt_response, так как теперь используем только GigaChat
from app.services.llm_clients import get_gigachat_response

api = Namespace('chat', description='Операции чата с ассистентом')

# --- Модели данных (DTOs) для валидации и документации ---

# Обновляем модель для входящего сообщения: убираем поле для выбора LLM
send_message_model = api.model('SendMessage', {
    'message_content': fields.String(required=True, description='Текст сообщения пользователя'),
    'session_id': fields.Integer(description='ID текущей сессии чата (если есть, для продолжения диалога)')
    # Убираем поле 'model', так как теперь используем только GigaChat
})

# Модель для одного сообщения в истории
message_model = api.model('Message', {
    'id': fields.Integer(readOnly=True),
    'role': fields.String(description='Роль (user или assistant)'),
    'content': fields.String(description='Текст сообщения'),
    'timestamp': fields.DateTime(readOnly=True)
})

# Модель для ответа от ассистента
assistant_message_response_model = api.model('AssistantMessageResponse', {
    'session_id': fields.Integer(description='ID сессии, в которой был дан ответ'),
    'assistant_message': fields.Nested(message_model, description='Сообщение, сгенерированное ассистентом')
})

# Модель для полной истории сессии
session_history_model = api.model('SessionHistory', {
    'id': fields.Integer(readOnly=True),
    'user_id': fields.Integer(readOnly=True),
    'created_at': fields.DateTime(readOnly=True),
    'messages': fields.List(fields.Nested(message_model), description='Список всех сообщений в сессии')
})


@api.route('/send_message')
class SendMessage(Resource):
    @api.doc(security='jwt')
    @jwt_required()
    @api.expect(send_message_model, validate=True)
    @api.marshal_with(assistant_message_response_model)
    def post(self):
        """Отправить сообщение ассистенту и получить ответ (только GigaChat)"""
        # Convert string back to integer for database operations
        current_user_id = int(get_jwt_identity())
        data = request.json
        user_message_content = data['message_content']
        session_id = data.get('session_id')
        # Убираем выбор модели, теперь всегда используем только GigaChat
        # model_choice = data.get('model', 'gigachat') 
        
        # Шаг 1: Управление сессией (найти существующую или создать новую)
        if session_id:
            session = ChatSession.query.get(session_id)
            if not session or session.user_id != current_user_id:
                api.abort(403, 'Доступ к данной сессии запрещен.')
        else:
            session = ChatSession(user_id=current_user_id)
            db.session.add(session)
            db.session.flush()  # Get the session ID before committing
        
        # Шаг 2: Сохранение сообщения пользователя в БД
        user_message = Message(session_id=session.id, role='user', content=user_message_content)
        db.session.add(user_message)
        
        # Шаг 3: Формирование промпта на основе профиля и истории
        profile = BusinessProfile.query.filter_by(user_id=current_user_id).first()
        history_messages = Message.query.filter_by(session_id=session.id).order_by(Message.timestamp.desc()).limit(10).all()
        history_messages.reverse()

        system_text = "Ты — полезный ассистент для малого бизнеса в РФ. Отвечай кратко и по делу."
        if profile:
            system_text += (f" Контекст о бизнесе пользователя: "
                            f"Отрасль - {profile.industry}, "
                            f"Размер компании - {profile.company_size}, "
                            f"Цели - {profile.goals}.")

        dialog_history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in history_messages])
        
        # Шаг 4: Вызов GigaChat API (теперь без выбора модели)
        assistant_response_content = get_gigachat_response(
            system_prompt=system_text,
            dialog_history=dialog_history_text,
            user_message=user_message_content
        )
        
        # Проверяем, является ли ответ ошибкой
        if assistant_response_content.startswith("Извините, произошла ошибка"):
            # Логируем ошибку, но не прерываем выполнение
            print(f"LLM Error: {assistant_response_content}")
        
        # Шаг 5: Сохранение ответа ассистента в БД
        assistant_message = Message(session_id=session.id, role='assistant', content=assistant_response_content)
        db.session.add(assistant_message)
        
        # Шаг 6: Фиксация транзакции
        db.session.commit()
        
        # Шаг 7: Возврат ответа клиенту
        return {'session_id': session.id, 'assistant_message': assistant_message}


@api.route('/session/<int:session_id>')
class SessionHistory(Resource):
    @api.doc(security='jwt')
    @jwt_required()
    @api.marshal_with(session_history_model)
    @api.response(403, 'Доступ запрещен.')
    @api.response(404, 'Сессия не найдена.')
    def get(self, session_id):
        """Получить историю сообщений для указанной сессии"""
        # Convert string back to integer for database operations
        current_user_id = int(get_jwt_identity())
        session = ChatSession.query.get_or_404(session_id, description=f"Сессия с ID {session_id} не найдена.")
        
        if session.user_id != current_user_id:
            api.abort(403, 'Доступ к данной сессии запрещен.')
            
        return session