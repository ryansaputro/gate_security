"""
Due Usecase - shared business logic for dues/iuran.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from entities.due import Due


class DueUsecase:
    def __init__(self):
        self._repo = None

    @property
    def repo(self):
        if self._repo is None:
            from drivers.mongo.connection import Mongo
            from repositories.due import DueRepository
            mongo = Mongo()
            self._repo = DueRepository(mongo.get_db())
        return self._repo

    def list(self, search: Optional[str] = None, status: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, family_id: Optional[str] = None, family_ids: Optional[List[str]] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Due], int, int, int]:
        """List dues with pagination, search, status filter, and month filter."""
        query = {}
        if search:
            query["$or"] = [
                {"period": {"$regex": search, "$options": "i"}},
                {"type": {"$regex": search, "$options": "i"}},
            ]
        if status and status in ("paid", "unpaid", "partial", "overdue"):
            query["status"] = status
        if year:
            query["year"] = year
        if month:
            query["month"] = month
        if family_id:
            query["familyId"] = family_id
        elif family_ids is not None:
            if family_ids:
                query["familyId"] = {"$in": family_ids}
            else:
                # Block has no families — return empty
                return [], 1, 1, 0
        total = self.repo.count(query)
        total_pages = max(1, (total + per_page - 1) // per_page)
        if page < 1:
            page = 1
        items = self.repo.find_many(
            filter=query,
            sort=[("year", -1), ("month", -1)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        return items, page, total_pages, total

    def enrich_with_family(self, dues_list: list) -> list:
        """Enrich serialized dues with family head_name and house block."""
        from bson import ObjectId as _OID
        from drivers.mongo.connection import Mongo
        db = Mongo().get_db()
        family_ids = set()
        for d in dues_list:
            fid = d.get("family_id")
            if fid:
                try:
                    family_ids.add(_OID(fid))
                except Exception:
                    pass
        family_map = {}
        house_ids = set()
        if family_ids:
            for f in db.families.find({"_id": {"$in": list(family_ids)}}):
                fid_str = str(f["_id"])
                family_map[fid_str] = {"head_name": f.get("headName", ""), "house_id": f.get("houseId", "")}
                if f.get("houseId"):
                    try:
                        house_ids.add(_OID(f["houseId"]))
                    except Exception:
                        pass
        house_map = {}
        if house_ids:
            for h in db.houses.find({"_id": {"$in": list(house_ids)}}):
                house_map[str(h["_id"])] = f"Blok {h.get('block', '')} No.{h.get('houseNumber', '')}"
        for d in dues_list:
            fid = d.get("family_id", "")
            fam = family_map.get(fid, {})
            head_name = fam.get("head_name", "-")
            house_label = house_map.get(fam.get("house_id", ""), "")
            d["family_head_name"] = f"{head_name} ({house_label})" if house_label else head_name
        return dues_list

    def find_by_id(self, due_id: str) -> Optional[Due]:
        """Get a single due by ID."""
        return self.repo.find_by_id(due_id)

    def create(self, family_id: str, period: str = "", type: str = "monthly",
               amount: int = 0, status: str = "unpaid", payment_method: str = "",
               paid_amount: int = 0, collector_name: str = "", notes: str = "",
               house_id: str = "") -> Due:
        """Create a new due record."""
        # Parse period to year/month
        year, month = 0, 0
        if period and "-" in period:
            parts = period.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                year, month = int(parts[0]), int(parts[1])
        entity = Due(
            family_id=family_id,
            house_id=house_id,
            period=period,
            year=year,
            month=month,
            type=type,
            amount=amount,
            paid_amount=paid_amount,
            status=status,
            payment_method=payment_method,
            collector_name=collector_name,
            notes=notes,
            paid_at=datetime.now() if status == "paid" else None,
        )
        due_id = self.repo.create(entity)
        return self.repo.find_by_id(due_id)

    def update(self, due_id: str, family_id: str = "", period: str = "",
               type: str = "monthly", amount: int = 0, paid_amount: int = 0,
               status: str = "unpaid", payment_method: str = "",
               collector_name: str = "", notes: str = "") -> Optional[Due]:
        """Update a due record."""
        existing = self.repo.find_by_id(due_id)
        if not existing:
            return None
        year, month = 0, 0
        if period and "-" in period:
            parts = period.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                year, month = int(parts[0]), int(parts[1])
        update_fields = {
            "familyId": family_id,
            "period": period,
            "year": year,
            "month": month,
            "type": type,
            "amount": amount,
            "paidAmount": paid_amount,
            "status": status,
            "paymentMethod": payment_method,
            "collectorName": collector_name,
            "notes": notes,
            "updatedAt": datetime.now(),
        }
        if status == "paid" and existing.status != "paid":
            update_fields["paidAt"] = datetime.now()
        self.repo.update_by_id(due_id, update_fields)
        return self.repo.find_by_id(due_id)

    def delete(self, due_id: str) -> bool:
        """Delete a due record."""
        existing = self.repo.find_by_id(due_id)
        if not existing:
            return False
        return self.repo.delete_by_id(due_id)

    def serialize(self, due: Due) -> dict:
        """Serialize due entity to dict."""
        return {
            "id": due.id,
            "family_id": due.family_id if hasattr(due, 'family_id') else "",
            "house_id": due.house_id if hasattr(due, 'house_id') else "",
            "period": due.period,
            "year": due.year,
            "month": due.month,
            "type": due.type,
            "amount": due.amount,
            "paid_amount": due.paid_amount,
            "status": due.status,
            "payment_method": due.payment_method,
            "collector_name": due.collector_name if hasattr(due, 'collector_name') else "",
            "notes": due.notes if hasattr(due, 'notes') else "",
            "due_date": due.due_date if hasattr(due, 'due_date') else None,
            "paid_at": due.paid_at if hasattr(due, 'paid_at') else None,
        }


# Singleton instance
due_usecase = DueUsecase()
