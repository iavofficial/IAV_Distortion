from DataModel.Vehicle import Vehicle

class EnvironmentManager:

    def __init__(self):
        self._player_uuid_map = {}
        self._active_anki_cars = None

        self._find_active_anki_cars()

    def get_player_uuid_mapping(self):
        return self._player_uuid_map

    def set_player_uuid_mapping(self, player_id: str, uuid: str):
        self._player_uuid_map.update({player_id: uuid})
        return

    def _find_active_anki_cars(self):
        vehicle1 = Vehicle("12:34:56", "dummyCar1")
        vehicle2 = Vehicle("78:90:01", "dummyCar2")
        self._active_anki_cars = [vehicle1, vehicle2]
        return

    def get_vehicle_list(self):
        return self._active_anki_cars





