from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Users(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(22))
    email = db.Column(db.String(35), unique=True)
    password = db.Column(db.String(150))
    address = db.column(db.String(150))
    linkedin = db.column(db.String(150))
    phone = db.column(db.String(15))
    
    def get_id(self):
        return(self.user_id)

class Admins(db.Model, UserMixin):
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(22))
    admin_email = db.Column(db.String(35), unique=True)
    password = db.Column(db.String(150))

    def get_id(self):
        return(self.admin_id)
