"""
Setting Controller - Upsert setting.
"""

from helpers.serializers.setting import SettingUpsert
from definitions.applications.response import SuccessResponse


def upsert_setting(self, body: SettingUpsert) -> SuccessResponse:
    """Create or update a setting."""
    repo = self._get_repo()
    repo.set_value(body.key, body.value)
    return SuccessResponse(data={"key": body.key, "value": body.value})
