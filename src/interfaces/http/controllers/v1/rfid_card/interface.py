"""
RFID Card Controller Interface.
"""

from drivers.mongo.connection import Mongo
from repositories.rfid_card import RfidCardRepository


class RfidCardController:
    def _get_repo(self) -> RfidCardRepository:
        mongo = Mongo()
        return RfidCardRepository(mongo.get_db())


from interfaces.http.controllers.v1.rfid_card.list import list_cards  # noqa
from interfaces.http.controllers.v1.rfid_card.create import create_card  # noqa
from interfaces.http.controllers.v1.rfid_card.block import block_card  # noqa
from interfaces.http.controllers.v1.rfid_card.detail import get_card  # noqa

RfidCardController.list_cards = list_cards
RfidCardController.create_card = create_card
RfidCardController.block_card = block_card
RfidCardController.get_card = get_card

controller = RfidCardController()
