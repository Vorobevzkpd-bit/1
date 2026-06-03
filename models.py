from app.extensions import db
from datetime import datetime

class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    personnel_number = db.Column(db.String(50))
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    hire_date = db.Column(db.String(20))
    badge_number = db.Column(db.String(50), unique=True)
    active = db.Column(db.Boolean, default=True)

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20))  # 'СИЗ' или 'Инструмент'
    unit = db.Column(db.String(20), default='шт.')
    wear_period = db.Column(db.Integer)  # срок носки в месяцах
    description = db.Column(db.Text)

class ItemNorm(db.Model):
    __tablename__ = 'item_norms'
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, default=1)
    period_months = db.Column(db.Integer)

class IssuedItem(db.Model):
    __tablename__ = 'issued_items'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, default=1)
    date_issued = db.Column(db.String(20), nullable=False)
    date_expire = db.Column(db.String(20))
    date_returned = db.Column(db.String(20))
    status = db.Column(db.String(20), default='issued')  # issued, returned, written_off
    notes = db.Column(db.Text)