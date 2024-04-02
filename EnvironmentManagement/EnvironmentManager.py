from DataModel.Vehicle import Vehicle


class EnvironmentManager:

    def __init__(self):
        self._player_uuid_map = {}
        self._active_anki_cars = None
        self.staff_ui = None

        self._find_active_anki_cars()

    def set_staff_ui(self, staff_ui):
        self.staff_ui = staff_ui
        return

    def get_player_uuid_mapping(self):
        return self._player_uuid_map

    def set_player_uuid_mapping(self, player_id: str, uuid: str):
        self._player_uuid_map.update({player_id: uuid})
        print("added uuid")
        self._update_staff_ui()
        return

    def _find_active_anki_cars(self):
        # Funktion zum Fahrzeuge Suchen und Verbinden
        # BLE device suchen
        # mit Device verbinden
        # vehicle initialisieren

        vehicle1 = Vehicle("12:34:56", "dummyCar1")
        vehicle2 = Vehicle("78:90:01", "dummyCar2")
        self._active_anki_cars = [vehicle1, vehicle2]
        return

    def get_vehicle_list(self):
        return self._active_anki_cars

    def remove_vehicle(self, uuid_to_remove: str):
        player_to_remove = ''
        for player, uuid in self._player_uuid_map.items():
            if uuid == uuid_to_remove:
                player_to_remove = player

        if player_to_remove != '':
            del self._player_uuid_map[player_to_remove]
            self._update_staff_ui()

        self._active_anki_cars = [vehicle for vehicle in self._active_anki_cars if vehicle.uuid != uuid_to_remove]
        return

    def _update_staff_ui(self):
        if self.staff_ui is not None:
            self.staff_ui.update_map_of_uuids(self._player_uuid_map)
        else:
            print("staff_ui instance is not yet set!")
        return
