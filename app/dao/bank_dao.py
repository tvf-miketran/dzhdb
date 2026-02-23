from sqlalchemy import asc, desc
from app.models.bank import Bank
from app import db
from typing import Optional, List


class BankDAO:

    # ---------- READ ----------
    @staticmethod
    def get_by_id(id: str) -> Optional[Bank]:
        """Get bank by UUID"""
        return Bank.query.filter_by(id=id).first()

    @staticmethod
    def get_by_name(name: str) -> Optional[Bank]:
        """Get bank by name"""
        return Bank.query.filter_by(name=name).first()
    
    @staticmethod
    def get_all() -> List[Bank]:
        """Get all banks"""
        return Bank.query.all()
    
    @staticmethod
    def get_all_filtered_sorted(
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """Get filtered and sorted banks with pagination"""
        query = Bank.query

        # Search in name
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(Bank.name.ilike(search_pattern))

        # Apply sorting
        sort_column = getattr(Bank, sort_by, Bank.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return query.paginate(page=page, per_page=per_page, error_out=False)
    

    # ---------- CREATE ----------
    @staticmethod
    def create(name: str) -> Bank:
        """Create new bank"""
        try:
            bank = Bank(name=name)
            db.session.add(bank)
            db.session.commit()
            return bank
        except Exception:
            db.session.rollback()
            raise

    # ---------- UPDATE ----------
    @staticmethod
    def update(id: str, name: str) -> Bank:
        """Update bank"""
        try:
            bank = BankDAO.get_by_id(id)
            
            if not bank:
                raise ValueError("Bank not found")
            
            # Validate name uniqueness (if changing)
            if name and name != bank.name:
                existing = BankDAO.get_by_name(name)
                if existing and existing.id != bank.id:
                    raise ValueError(f"Bank name '{name}' already exists")
            
            # Update name
            if name is not None:
                bank.name = name
            
            db.session.commit()
            return bank
        except Exception:
            db.session.rollback()
            raise

    # ---------- DELETE ----------
    @staticmethod
    def delete(id: str) -> bool:
        """Delete bank"""
        try:
            bank = BankDAO.get_by_id(id)
            
            if not bank:
                return False
            
            db.session.delete(bank)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise