import os
from flask import Flask, request
from flask_migrate import Migrate
from user_agents import parse
import datetime

from .db import db, VisitorStats

migrate = Migrate(render_as_batch=True)

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "NOTHING_IS_SECRET")
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/expense_tracker'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.after_request
    def after_request_(response):
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    from .views.auth import auth
    from .views.home import home
    from .views.settings import settings

    blueprints = [auth, home, settings]

    @app.before_request
    def app_before_data():
        if request.endpoint != "static":
            user_agent = parse(request.user_agent.string)
            browser = user_agent.browser.family
            device = user_agent.get_device()
            operating_system = user_agent.get_os()
            bot = user_agent.is_bot

            stat = VisitorStats(
                browser=browser,
                device=device,
                operating_system=operating_system,
                is_bot=bot
            )
            db.session.add(stat)
            db.session.commit()

    for bp in blueprints:
        app.register_blueprint(bp)

    return app
