import os
from flask import Flask
from config import config_by_name
from .extensions import db, login_manager, csrf, migrate
from .routes import main
from .models import User
import click

def create_app(config_name=None):
    config_name = config_name or os.environ.get("APP_ENV")
    if not config_name:
        raise RuntimeError("APP_ENV must be set.")
   
    if config_name not in config_by_name:
        raise RuntimeError(
            f"Unknown application environment: {config_name}"
        )
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    if config_name == "production":
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY must be set in production."
            )

        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            raise RuntimeError(
                "DATABASE_URL must be set in production."
            )
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = "main.login"
    app.register_blueprint(main)

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator account."""
        name = click.prompt("Admin name")
        email = click.prompt("Admin email").strip().lower()
        password = click.prompt(
            "Admin password",
            hide_input=True,
            confirmation_prompt=True,
        )
        from werkzeug.security import generate_password_hash
        from .models import User
        existing_user = User.query.filter_by(
            email=email
        ).first()
        if existing_user:
            click.echo(
                "A user with this email already exists."
            )
            return
        admin = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(
            f"Administrator '{email}' created successfully."
        )

    # Convenient for local development.
    # Use database migrations for production schema changes.
   
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))