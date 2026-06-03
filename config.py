from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True
    
    # SQLite для тестирования (файл app.db появится в корне проекта)
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///app.db"
    
    UPLOAD_FOLDER: str = "app/static/uploads/defects"
    CHAT_UPLOAD_FOLDER: str = "app/static/uploads/chat"
    PRIVATE_UPLOAD_FOLDER: str = "app/static/uploads/private"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024