from app.extensions import db
from .models import Employee, Item, ItemNorm, IssuedItem, Position
from datetime import datetime, timedelta

class WarehouseService:
    @staticmethod
    def get_positions():
        return [p.name for p in Position.query.order_by(Position.name).all()]

    @staticmethod
    def add_employee(full_name, position, department, badge_number, personnel_number, hire_date):
        emp = Employee(
            full_name=full_name,
            position=position,
            department=department,
            badge_number=badge_number,
            personnel_number=personnel_number,
            hire_date=hire_date,
            active=True
        )
        db.session.add(emp)
        db.session.commit()
        return emp.id

    @staticmethod
    def find_employee_by_badge(badge):
        return Employee.query.filter_by(badge_number=badge, active=True).first()

    @staticmethod
    def issue_item(employee_id, item_id, quantity, date_issued):
        item = Item.query.get(item_id)
        if not item:
            raise ValueError("Предмет не найден")
        expire_date = None
        if item.wear_period:
            dt = datetime.strptime(date_issued, '%Y-%m-%d')
            expire_date = (dt + timedelta(days=item.wear_period * 30.44)).strftime('%Y-%m-%d')
        issued = IssuedItem(
            employee_id=employee_id,
            item_id=item_id,
            quantity=quantity,
            date_issued=date_issued,
            date_expire=expire_date,
            status='issued'
        )
        db.session.add(issued)
        db.session.commit()
        return issued.id

    @staticmethod
    def return_item(issue_id):
        issued = IssuedItem.query.get(issue_id)
        if issued and issued.status == 'issued':
            issued.status = 'returned'
            issued.date_returned = datetime.now().strftime('%Y-%m-%d')
            db.session.commit()
            return True
        return False

    @staticmethod
    def write_off_expired(employee_id):
        today = datetime.now().strftime('%Y-%m-%d')
        expired = IssuedItem.query.filter(
            IssuedItem.employee_id == employee_id,
            IssuedItem.status == 'issued',
            IssuedItem.date_expire <= today
        ).all()
        count = 0
        for item in expired:
            item.status = 'written_off'
            item.notes = 'Списано по сроку'
            count += 1
        db.session.commit()
        return count

    @staticmethod
    def get_norms_for_position(position):
        norms = db.session.query(ItemNorm, Item).join(Item, ItemNorm.item_id == Item.id).filter(ItemNorm.position == position).all()
        return [{'name': n.Item.name, 'type': n.Item.type, 'quantity': n.ItemNorm.quantity, 'period_months': n.ItemNorm.period_months, 'unit': n.Item.unit} for n in norms]