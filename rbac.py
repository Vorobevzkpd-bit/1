from flask import session, g
from app.extensions import db
from app.modules.auth.models import User, Role, Permission, RolePermission

def _load_permissions():
    """Загружает права текущего пользователя и сохраняет в g.user_perms"""
    if 'user_id' not in session:
        g.user_perms = set()
        return
    user = User.query.get(session['user_id'])
    if not user or not user.role_id:
        g.user_perms = set()
        return
    # Получаем все разрешения для роли пользователя
    perms = db.session.query(Permission.name).join(RolePermission).filter(RolePermission.role_id == user.role_id).all()
    g.user_perms = {p[0] for p in perms}

def has_permission(perm_name):
    """Проверяет, есть ли у пользователя разрешение"""
    if 'user_id' not in session:
        return False
    if not hasattr(g, 'user_perms'):
        _load_permissions()
    return perm_name in g.user_perms

def has_any_permission(perm_list):
    """Проверяет наличие хотя бы одного из разрешений"""
    return any(has_permission(p) for p in perm_list)