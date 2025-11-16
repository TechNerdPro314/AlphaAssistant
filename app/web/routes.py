# app/web/routes.py
import requests
from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user, login_required
from . import bp
from app.models import User
from app import db

API_BASE_URL = "http://127.0.0.1:5000/api/v1"


@bp.route("/")
def index():
    return render_template("login.html", title="Вход")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.chat"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
            )
            if response.status_code == 200:
                user = User.query.filter_by(email=email).first()
                login_user(user, remember=True)

                session["jwt_token"] = response.json()["access_token"]

                return redirect(url_for("web.chat"))
            else:
                flash("Неверный email или пароль")
        except requests.RequestException:
            flash("Сервис временно недоступен")

    return render_template("login.html", title="Вход")


@bp.route("/logout")
def logout():
    logout_user()
    session.pop("jwt_token", None)
    return redirect(url_for("web.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.chat"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                json={"email": email, "password": password},
            )
            if response.status_code == 201:
                flash("Регистрация прошла успешно! Теперь вы можете войти.")
                return redirect(url_for("web.login"))
            else:
                flash(response.json().get("message", "Произошла ошибка"))
        except requests.RequestException:
            flash("Сервис временно недоступен")

    return render_template("register.html", title="Регистрация")


@bp.route("/chat")
@login_required
def chat():
    jwt_token = session.get("jwt_token")
    if not jwt_token:
        # Если токена нет в сессии, разлогиниваем
        logout_user()
        return redirect(url_for("web.login"))

    return render_template("chat.html", title="Чат с ассистентом", jwt_token=jwt_token)
