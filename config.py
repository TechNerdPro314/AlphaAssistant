# config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour instead of default 15 minutes
    
    # GigaChat credentials
    # To use GigaChat, you need to:
    # 1. Register at https://developers.sber.ru/studio
    # 2. Create a new project and get your API key
    # 3. Encode your API key in Base64 format
    # 4. Add it to your .env file as GIGACHAT_AUTH_CREDENTIALS=your_base64_encoded_key
    GIGACHAT_AUTH_CREDENTIALS = os.environ.get('GIGACHAT_AUTH_CREDENTIALS')
    
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')