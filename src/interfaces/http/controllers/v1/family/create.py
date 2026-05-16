"""
Family Controller - Create family.
"""

from helpers.serializers.family import FamilyCreate
from definitions.applications.response import SuccessResponse
from entities.family import Family, FamilyMember


def create_family(self, body: FamilyCreate) -> SuccessResponse:
    """Register a new family (KK)."""
    repo = self._get_repo()
    members = [FamilyMember(name=m.name, relation=m.relation, phone=m.phone, id_number=m.id_number) for m in body.members]
    entity = Family(
        house_id=body.house_id,
        head_name=body.head_name,
        head_phone=body.head_phone,
        head_id_number=body.head_id_number,
        members=members,
        total_members=len(members) + 1,
        status="active",
    )
    fid = repo.create(entity)
    f = repo.find_by_id(fid)
    return SuccessResponse(data={"id": f.id, "head_name": f.head_name, "status": f.status})
