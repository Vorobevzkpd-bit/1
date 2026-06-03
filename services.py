from app.extensions import db
from .models import Employee, Item, IssuedItem

class WarehouseService:
    @staticmethod
    def get_positions():
        return []