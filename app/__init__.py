# app/__init__.py
from flask import Flask
from config import DevelopmentConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager  # Убедитесь, что LoginManager импортирован

# Создаем экземпляры расширений
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()

login_manager.login_view = "web.login"
login_manager.login_message = (
    "Пожалуйста, войдите, чтобы получить доступ к этой странице."
)
login_manager.login_message_category = (
    "error"  # Добавим категорию для красивого отображения
)


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """Эта функция нужна Flask-Login для загрузки пользователя из БД по ID из сессии."""
        return User.query.get(int(user_id))

    from app.api import blueprint as api_blueprint

    app.register_blueprint(api_blueprint)

    from app.web.routes import bp as web_blueprint

    app.register_blueprint(web_blueprint)

    return app
