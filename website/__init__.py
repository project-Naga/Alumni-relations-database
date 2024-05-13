from flask import Flask, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user
import json
from authlib.integrations.flask_client import OAuth
import config
import os

lm = LoginManager()
db = SQLAlchemy()
mysql = MySQL()
oauth = OAuth()
sql_host  = config.MYSQL_HOST
sql_user = config.MYSQL_USER
sql_pass = config.MYSQL_PASSWORD
sql_db = config.MYSQL_DB
sql_server = config.MYSQL_SERVER

with open('website/tables.json', 'r') as f:
  tables_dict = json.load(f)

def create_app():
    app = Flask(__name__, template_folder='../templates',static_folder='../static')
    app.config['MYSQL_HOST'] = sql_host 
    app.config['MYSQL_USER'] = sql_user
    app.config['MYSQL_PASSWORD'] = sql_pass
    app.config['MYSQL_DB'] = sql_db
    app.secret_key = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<\\xd5\xa2\xa0\x9fR"\xa1\xa8'

    sqlalchemy_config = 'mysql://'+str(sql_user)+':'+str(sql_pass)+'@'+str(sql_host)+'/'+str(sql_db)
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_config
    db.init_app(app)
    mysql.init_app(app)
    oauth.init_app(app)
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    from .models import Users, Admins

    with app.app_context():
        db.create_all()

    lm.login_view = 'auth.login'
    lm.init_app(app)

    @lm.user_loader
    def load_user(user_id):
        return Admins.query.get(int(user_id))
    return app 
