from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.shared.permissions import login_required, permission_required
from app.extensions import db
from .models import Employee, Item, ItemNorm, IssuedItem
from .services import WarehouseService

bp = Blueprint('warehouse_ppe', __name__, url_prefix='/warehouse')

@bp.route('/employees')
@login_required
@permission_required('view_warehouse')
def employees_list():
    show_all = request.args.get('all', '0') == '1'
    query = Employee.query
    if not show_all:
        query = query.filter_by(active=True)
    employees = query.order_by(Employee.full_name).all()
    return render_template('warehouse_ppe/employees.html', employees=employees, show_all=show_all)

@bp.route('/employee/<int:emp_id>')
@login_required
@permission_required('view_warehouse')
def employee_card(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    issuances = IssuedItem.query.filter_by(employee_id=emp_id).order_by(IssuedItem.date_issued.desc()).all()
    norms = WarehouseService.get_norms_for_position(emp.position or '')
    items = Item.query.order_by(Item.name).all()
    positions = WarehouseService.get_positions()
    return render_template('warehouse_ppe/employee_card.html', emp=emp, issuances=issuances, norms=norms, items=items, positions=positions)

@bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@permission_required('manage_warehouse')
def employee_add():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        position = request.form.get('position')
        department = request.form.get('department')
        badge = request.form.get('badge_number')
        personnel = request.form.get('personnel_number')
        hire_date = request.form.get('hire_date')
        if not full_name:
            flash('ФИО обязательно', 'danger')
            return redirect(url_for('warehouse_ppe.employee_add'))
        WarehouseService.add_employee(full_name, position, department, badge, personnel, hire_date)
        flash('Сотрудник добавлен', 'success')
        return redirect(url_for('warehouse_ppe.employees_list'))
    positions = WarehouseService.get_positions()
    return render_template('warehouse_ppe/employee_add.html', positions=positions)

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

@bp.route('/issue', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def issue_item():
    emp_id = request.form.get('employee_id')
    item_id = request.form.get('item_id')
    quantity = float(request.form.get('quantity', 1))
    date_issued = request.form.get('date_issued')
    if not emp_id or not item_id:
        flash('Не указан сотрудник или предмет', 'danger')
        return redirect(request.referrer or url_for('warehouse_ppe.employees_list'))
    WarehouseService.issue_item(int(emp_id), int(item_id), quantity, date_issued)
    flash('Выдача зафиксирована', 'success')
    return redirect(url_for('warehouse_ppe.employee_card', emp_id=emp_id))

@bp.route('/return/<int:issue_id>', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def return_item(issue_id):
    if WarehouseService.return_item(issue_id):
        flash('Возврат зафиксирован', 'success')
    else:
        flash('Ошибка возврата', 'danger')
    return redirect(request.referrer or url_for('warehouse_ppe.employees_list'))

@bp.route('/employee/<int:emp_id>/write_off_expired', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def write_off_expired(emp_id):
    count = WarehouseService.write_off_expired(emp_id)
    flash(f'Списано позиций: {count}', 'success')
    return redirect(url_for('warehouse_ppe.employee_card', emp_id=emp_id))

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

@bp.route('/norms')
@login_required
@permission_required('view_warehouse')
def norms_list():
    norms = db.session.query(ItemNorm, Item).join(Item, ItemNorm.item_id == Item.id).order_by(ItemNorm.position, Item.name).all()
    items = Item.query.all()
    positions = WarehouseService.get_positions()
    return render_template('warehouse_ppe/norms.html', norms=norms, items=items, positions=positions)

@bp.route('/norms/add', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def norm_add():
    position = request.form.get('position')
    item_id = request.form.get('item_id')
    quantity = float(request.form.get('quantity', 1))
    period = request.form.get('period_months')
    if not position or not item_id:
        flash('Укажите должность и предмет', 'danger')
        return redirect(url_for('warehouse_ppe.norms_list'))
    norm = ItemNorm(position=position, item_id=int(item_id), quantity=quantity, period_months=period or None)
    db.session.add(norm)
    db.session.commit()
    flash('Норма добавлена', 'success')
    return redirect(url_for('warehouse_ppe.norms_list'))

@bp.route('/norms/delete/<int:norm_id>', methods=['POST'])
@login_required
@permission_required('manage_warehouse')
def norm_delete(norm_id):
    ItemNorm.query.filter_by(id=norm_id).delete()
    db.session.commit()
    flash('Норма удалена', 'success')
    return redirect(url_for('warehouse_ppe.norms_list'))

@bp.route('/journal')
@login_required
@permission_required('view_warehouse')
def journal():
    operations = db.session.query(IssuedItem, Employee, Item).join(Employee, IssuedItem.employee_id == Employee.id).join(Item, IssuedItem.item_id == Item.id).order_by(IssuedItem.date_issued.desc()).all()
    return render_template('warehouse_ppe/journal.html', operations=operations)

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

@bp.route('/employee/upload', methods=['GET', 'POST'])
@login_required
@permission_required('manage_warehouse')
def employee_upload():
    if request.method == 'POST':
        # Здесь будет обработка Excel – пока заглушка
        flash('Загрузка через Excel будет добавлена позже', 'info')
        return redirect(url_for('warehouse_ppe.employees_list'))
    return render_template('warehouse_ppe/employee_upload.html')