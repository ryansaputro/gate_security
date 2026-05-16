"""
Setting Controller - Get setting by key.
"""

from definitions.applications.response import SuccessResponse


def get_setting(self, key: str) -> SuccessResponse:
    """Get a setting value by key."""
    repo = self._get_repo()
    value = repo.get_value(key, default="")
    return SuccessResponse(data={"key": key, "value": value})
