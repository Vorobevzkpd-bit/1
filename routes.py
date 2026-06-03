# ============================================================================
# Файл: app/modules/warehouse_ppe/routes.py
# ============================================================================
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.shared.permissions import login_required, permission_required
from app.extensions import db
from .models import Employee, Item, IssuedItem
from app.modules.documents.services import log_document   # добавлен импорт
from datetime import datetime, timedelta

bp = Blueprint('warehouse_ppe', __name__, url_prefix='/warehouse')

# ------------------- СОТРУДНИКИ -------------------
@bp.route('/employees')
@login_required
@permission_required('view_warehouse')
def employees_list():
    employees = Employee.query.all()
    return render_template('warehouse_ppe/employees.html', employees=employees)

@bp.route('/employee/<int:emp_id>')
@login_required
@permission_required('view_warehouse')
def employee_card(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    issuances = IssuedItem.query.filter_by(employee_id=emp_id).order_by(IssuedItem.date_issued.desc()).all()
    items = Item.query.order_by(Item.name).all()
    return render_template('warehouse_ppe/employee_card.html', emp=emp, issuances=issuances, items=items)

@bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@permission_required('manage_warehouse')
def employee_add():
    if request.method == 'POST':
        emp = Employee(
            full_name=request.form.get('full_name'),
            position=request.form.get('position'),
            department=request.form.get('department'),
            badge_number=request.form.get('badge_number'),
            personnel_number=request.form.get('personnel_number'),
            hire_date=request.form.get('hire_date'),
            active=True
        )
        db.session.add(emp)
        db.session.commit()
        flash('Сотрудник добавлен', 'success')
        return redirect(url_for('warehouse_ppe.employees_list'))
    return render_template('warehouse_ppe/employee_add.html')

@bp.route('/employee/<int:emp_id>/edit', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def employee_edit(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    emp.full_name = request.form.get('full_name')
    emp.position = request.form.get('position')
    emp.department = request.form.get('department')
    emp.badge_number = request.form.get('badge_number')
    db.session.commit()
    flash('Данные обновлены', 'success')
    return redirect(url_for('warehouse_ppe.employee_card', emp_id=emp_id))

@bp.route('/employee/<int:emp_id>/delete', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def employee_delete(emp_id):
    IssuedItem.query.filter_by(employee_id=emp_id).delete()
    Employee.query.filter_by(id=emp_id).delete()
    db.session.commit()
    flash('Сотрудник удалён', 'success')
    return redirect(url_for('warehouse_ppe.employees_list'))

# ------------------- ВЫДАЧА И ВОЗВРАТ -------------------
@bp.route('/issue', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def issue_item():
    emp_id = request.form.get('employee_id')
    item_id = request.form.get('item_id')
    quantity = float(request.form.get('quantity', 1))
    date_issued = request.form.get('date_issued')
    item = Item.query.get(item_id)
    date_expire = None
    if item and item.wear_period:
        dt = datetime.strptime(date_issued, '%Y-%m-%d')
        date_expire = (dt + timedelta(days=item.wear_period * 30.44)).strftime('%Y-%m-%d')
    issued = IssuedItem(
        employee_id=emp_id,
        item_id=item_id,
        quantity=quantity,
        date_issued=date_issued,
        date_expire=date_expire,
        status='issued'
    )
    db.session.add(issued)
    db.session.commit()
    
    # Логирование выдачи
    emp = Employee.query.get(emp_id)
    log_document(
        doc_type='ppe_issue',
        doc_id=issued.id,
        title=f"Выдача {item.name} сотруднику {emp.full_name}",
        user_id=session['user_id'],
        employee_name=emp.full_name
    )
    
    flash('Выдача зафиксирована', 'success')
    return redirect(url_for('warehouse_ppe.employee_card', emp_id=emp_id))

@bp.route('/return/<int:issue_id>', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def return_item(issue_id):
    issued = IssuedItem.query.get_or_404(issue_id)
    if issued.status == 'issued':
        issued.status = 'returned'
        issued.date_returned = datetime.now().strftime('%Y-%m-%d')
        db.session.commit()
        
        # Логирование возврата
        log_document(
            doc_type='ppe_return',
            doc_id=issue_id,
            title=f"Возврат {issued.item.name} от {issued.employee.full_name}",
            user_id=session['user_id'],
            employee_name=issued.employee.full_name
        )
        
        flash('Возврат зафиксирован', 'success')
    else:
        flash('Этот предмет уже возвращён или списан', 'warning')
    return redirect(request.referrer or url_for('warehouse_ppe.employees_list'))

@bp.route('/employee/<int:emp_id>/write_off_expired', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def write_off_expired(emp_id):
    today = datetime.now().strftime('%Y-%m-%d')
    expired = IssuedItem.query.filter(
        IssuedItem.employee_id == emp_id,
        IssuedItem.status == 'issued',
        IssuedItem.date_expire <= today
    ).all()
    count = 0
    for item in expired:
        item.status = 'written_off'
        item.notes = 'Списано по сроку'
        count += 1
    db.session.commit()
    flash(f'Списано позиций: {count}', 'success')
    return redirect(url_for('warehouse_ppe.employee_card', emp_id=emp_id))

# ------------------- ПРЕДМЕТЫ -------------------
@bp.route('/items')
@login_required
@permission_required('view_warehouse')
def items_list():
    items = Item.query.order_by(Item.type, Item.name).all()
    return render_template('warehouse_ppe/items.html', items=items)

@bp.route('/items/add', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def item_add():
    name = request.form.get('name')
    item_type = request.form.get('type')
    unit = request.form.get('unit', 'шт.')
    wear = request.form.get('wear_period')
    desc = request.form.get('description')
    if not name or not item_type:
        flash('Название и тип обязательны', 'danger')
        return redirect(url_for('warehouse_ppe.items_list'))
    item = Item(name=name, type=item_type, unit=unit, wear_period=wear or None, description=desc)
    db.session.add(item)
    db.session.commit()
    flash('Предмет добавлен', 'success')
    return redirect(url_for('warehouse_ppe.items_list'))

# ------------------- НОРМЫ ВЫДАЧИ (заглушки) -------------------
@bp.route('/norms')
@login_required
@permission_required('view_warehouse')
def norms_list():
    return render_template('warehouse_ppe/norms.html', norms=[], items=[], positions=[])

@bp.route('/norms/add', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def norm_add():
    flash('Функция добавления норм будет реализована позже', 'info')
    return redirect(url_for('warehouse_ppe.norms_list'))

@bp.route('/norms/delete/<int:norm_id>', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def norm_delete(norm_id):
    flash('Функция удаления норм будет реализована позже', 'info')
    return redirect(url_for('warehouse_ppe.norms_list'))

# ------------------- ЖУРНАЛ ОПЕРАЦИЙ -------------------
@bp.route('/journal')
@login_required
@permission_required('view_warehouse')
def journal():
    operations = []
    return render_template('warehouse_ppe/journal.html', operations=operations)

# ------------------- ЗАГРУЗКА СОТРУДНИКОВ ИЗ EXCEL (заглушка) -------------------
@bp.route('/employee/upload', methods=['GET', 'POST'])
@login_required
@permission_required('manage_warehouse')
def employee_upload():
    if request.method == 'POST':
        flash('Загрузка из Excel будет доступна позже', 'info')
        return redirect(url_for('warehouse_ppe.employees_list'))
    return render_template('warehouse_ppe/employee_upload.html')

# ------------------- API ПОИСК ПО КАРТЕ -------------------
@bp.route('/api/find_employee_by_badge')
@login_required
@permission_required('view_warehouse')
def find_employee_by_badge():
    badge = request.args.get('badge', '').strip()
    if not badge:
        return jsonify({'found': False})
    emp = Employee.query.filter_by(badge_number=badge, active=True).first()
    if emp:
        return jsonify({'found': True, 'id': emp.id, 'full_name': emp.full_name, 'position': emp.position, 'badge': emp.badge_number})
    return jsonify({'found': False})