from DataModel.Vehicle import Vehicle


class EnvironmentManager:

    def __init__(self):
        pass

    @staticmethod
    def get_vehicle_list():
        vehicle1 = Vehicle("12:34:56", "dummy1")
        vehicle2 = Vehicle("78:90:01", "dummy2")
        vehicles = [vehicle1, vehicle2]
        return vehicles

    @staticmethod
    def get_player_uuid_mapping():

        player_uuid_map = {'1': "12:34:56",
                           '2': "78:90:01"}

        return player_uuid_map
