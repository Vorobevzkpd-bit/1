from flask import Flask, session
from app.config import Settings
from app.extensions import db, migrate, cache
from app.shared.permissions import login_required
from app.shared.rbac import has_permission, has_any_permission
from datetime import datetime
import os

def create_app():
    settings = Settings()
    app = Flask(__name__)
    app.config.from_object(settings)
    
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    
    # Создание папок для загрузок
    for folder in [app.config['UPLOAD_FOLDER'], app.config['CHAT_UPLOAD_FOLDER'], app.config['PRIVATE_UPLOAD_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
    
    # Контекстные процессоры
    @app.context_processor
    def inject_user():
        return {
            'full_name': session.get('full_name', 'Гость'),
            'role': session.get('role', '')
        }
    
    @app.context_processor
    def inject_permissions():
        return dict(
            has_permission=has_permission,
            has_any_permission=has_any_permission
        )
    
    @app.context_processor
    def inject_now():
        months = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                  'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
        now_func = datetime.now
        return {
            'now': now_func,
            'current_month_name': months[now_func().month - 1]
        }
    
    # Регистрация Blueprint'ов
    from app.modules.auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.modules.main.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.modules.quality.routes import bp as quality_bp
    app.register_blueprint(quality_bp)
    
    from app.modules.control.routes import bp as control_bp
    app.register_blueprint(control_bp)
    
    from app.modules.finished_goods.routes import bp as finished_goods_bp
    app.register_blueprint(finished_goods_bp)
    
    from app.modules.warehouse_ppe.routes import bp as warehouse_ppe_bp
    app.register_blueprint(warehouse_ppe_bp)
    
    from app.modules.chat.routes import bp as chat_bp
    app.register_blueprint(chat_bp)
    
    from app.modules.protocols.routes import bp as protocols_bp
    app.register_blueprint(protocols_bp)
    
    from app.modules.documents.routes import bp as documents_bp
    app.register_blueprint(documents_bp)
    
    from app.modules.admin.routes import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    from app.modules.invoice.routes import bp as invoice_bp
    app.register_blueprint(invoice_bp)
    
    from app.modules.production.routes import bp as production_bp
    app.register_blueprint(production_bp)
    
    # Регистрация модуля email
    from app.modules.email.routes import bp as email_bp
    app.register_blueprint(email_bp)
    
    return app