# run.py
from app import create_app, db
from app.models import User, BusinessProfile, ChatSession, Message

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "BusinessProfile": BusinessProfile,
        "ChatSession": ChatSession,
        "Message": Message,
    }


if __name__ == "__main__":
    app.run(debug=True)
