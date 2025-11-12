# config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # YandexGPT credentials
    YANDEX_FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID')
    YANDEX_API_KEY = os.environ.get('YANDEX_API_KEY')

    # GigaChat credentials
    GIGACHAT_AUTH_CREDENTIALS = os.environ.get('GIGACHAT_AUTH_CREDENTIALS')
    
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')