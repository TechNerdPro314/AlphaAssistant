# run.py
from app import create_app, db
from app.models import User, BusinessProfile, ChatSession, Message

# Создаем экземпляр приложения, используя нашу фабрику
app = create_app()

# Этот блок кода позволяет нам получить доступ к моделям в интерактивной оболочке flask shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'BusinessProfile': BusinessProfile,
        'ChatSession': ChatSession,
        'Message': Message
    }

if __name__ == '__main__':
    # Запуск приложения. debug=True автоматически перезагружает сервер при изменениях
    app.run(debug=True)