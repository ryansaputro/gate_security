"""
Setting Controller - List all settings.
"""

from definitions.applications.response import SuccessResponse


def list_settings(self) -> SuccessResponse:
    """List all system settings."""
    repo = self._get_repo()
    settings = repo.find_many()
    return SuccessResponse(data=[{
        "id": s.id,
        "key": s.key,
        "value": s.value,
        "category": s.category,
        "description": s.description,
    } for s in settings])
