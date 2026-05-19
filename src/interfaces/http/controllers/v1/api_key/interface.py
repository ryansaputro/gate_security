"""
API Key Controller - Manage API keys for authentication.
"""

from drivers.mongo.connection import Mongo


class ApiKeyController:
    def _get_db(self):
        return Mongo().get_db()


from interfaces.http.controllers.v1.api_key.create import create_key  # noqa
from interfaces.http.controllers.v1.api_key.list_keys import list_keys  # noqa
from interfaces.http.controllers.v1.api_key.revoke import revoke_key  # noqa

ApiKeyController.create_key = create_key
ApiKeyController.list_keys = list_keys
ApiKeyController.revoke_key = revoke_key

controller = ApiKeyController()
