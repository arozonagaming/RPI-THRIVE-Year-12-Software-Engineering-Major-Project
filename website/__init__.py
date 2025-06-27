from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    database_pwd = "Nas1zI9IYRaZu3LA"

    # Secret key for session management
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'

    # Supabase PostgreSQL connection
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://postgres.ahrzxoczqecscfwmqwuo:{database_pwd}@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres'
    )

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models and create tables
    from .models import User, Plant
    with app.app_context():
        db.create_all()

    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'views.landing'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app