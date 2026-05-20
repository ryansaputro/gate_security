"""
House Controller Interface - uses HouseUsecase for all operations.
"""

from usecases.house.interface import house_usecase


class HouseController:
    def __init__(self):
        self.uc = house_usecase


from interfaces.http.controllers.v1.house.list import list_houses  # noqa
from interfaces.http.controllers.v1.house.detail import get_house  # noqa
from interfaces.http.controllers.v1.house.create import create_house  # noqa
from interfaces.http.controllers.v1.house.update import update_house  # noqa
from interfaces.http.controllers.v1.house.delete import delete_house  # noqa

HouseController.list_houses = list_houses
HouseController.get_house = get_house
HouseController.create_house = create_house
HouseController.update_house = update_house
HouseController.delete_house = delete_house

controller = HouseController()
