import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, session
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32),
        DATABASE_URL=os.getenv('DATABASE_URL', ''), MAX_CONTENT_LENGTH=100_000,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    if test_config:
        app.config.update(test_config)
    url = app.config['DATABASE_URL']
    if not url:
        raise RuntimeError('Set DATABASE_URL in .env. Create the MySQL database before running flask init-db.')
    if url.startswith('mysql://'):
        url = 'mysql+pymysql://' + url[len('mysql://'):]
    if not url.startswith('mysql+pymysql://') and not app.config.get('TESTING'):
        raise RuntimeError('Use a mysql+pymysql:// DATABASE_URL. SQLite is reserved for isolated tests.')
    kwargs = {'pool_pre_ping': True}
    if url.startswith('mysql'):
        kwargs['connect_args'] = {'connect_timeout': 5, 'read_timeout': 15, 'write_timeout': 15}
    engine = create_engine(url, **kwargs)
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, record):
            connection.execute('PRAGMA foreign_keys=ON')
    app.extensions['db_session'] = sessionmaker(engine, expire_on_commit=False)
    app.extensions['db_engine'] = engine

    @app.context_processor
    def csrf_context():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {'csrf_token': session['csrf_token']}

    @app.before_request
    def protect_forms():
        if request.method == 'POST':
            token = session.get('csrf_token', '')
            if not token or not secrets.compare_digest(token, request.form.get('csrf_token', '')):
                abort(400, 'Refresh the page and submit again.')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        return response

    from .routes import main
    app.register_blueprint(main)
    from .commands import register_commands
    register_commands(app)
    return app
