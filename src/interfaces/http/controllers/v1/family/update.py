"""
Family Controller - Update family.
"""

from fastapi import HTTPException
from helpers.serializers.family import FamilyUpdate
from definitions.applications.response import SuccessResponse


def update_family(self, family_id: str, body: FamilyUpdate) -> SuccessResponse:
    """Update family data."""
    repo = self._get_repo()
    existing = repo.find_by_id(family_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Family not found")
    update = {}
    if body.head_name:
        update["headName"] = body.head_name
    if body.head_phone:
        update["headPhone"] = body.head_phone
    if body.status:
        update["status"] = body.status
    if body.members is not None:
        update["members"] = [{"name": m.name, "relation": m.relation, "phone": m.phone, "idNumber": m.id_number} for m in body.members]
        update["totalMembers"] = len(body.members) + 1
    if update:
        repo.update_by_id(family_id, update)
    f = repo.find_by_id(family_id)
    return SuccessResponse(data={"id": f.id, "head_name": f.head_name, "status": f.status})
