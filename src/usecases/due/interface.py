"""
Due Usecase - shared business logic for dues/iuran.
List + find_by_id only (no create/update from admin panel).
"""

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

    def list(self, search: Optional[str] = None, status: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Due], int, int, int]:
        """List dues with pagination, search, status filter, and month filter. Returns (items, page, total_pages, total)."""
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
        # Collect unique family_ids
        family_ids = set()
        for d in dues_list:
            fid = d.get("family_id")
            if fid:
                try:
                    family_ids.add(_OID(fid))
                except Exception:
                    pass
        # Batch lookup families
        family_map = {}  # id -> {head_name, house_id}
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
        # Batch lookup houses
        house_map = {}
        if house_ids:
            for h in db.houses.find({"_id": {"$in": list(house_ids)}}):
                house_map[str(h["_id"])] = f"Blok {h.get('block', '')} No.{h.get('houseNumber', '')}"
        # Enrich
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

    def serialize(self, due: Due) -> dict:
        """Serialize due entity to dict."""
        return {
            "id": due.id,
            "family_id": due.family_id if hasattr(due, 'family_id') else "",
            "period": due.period,
            "year": due.year,
            "month": due.month,
            "type": due.type,
            "amount": due.amount,
            "paid_amount": due.paid_amount,
            "status": due.status,
            "payment_method": due.payment_method,
            "due_date": due.due_date if hasattr(due, 'due_date') else None,
        }


# Singleton instance
due_usecase = DueUsecase()
