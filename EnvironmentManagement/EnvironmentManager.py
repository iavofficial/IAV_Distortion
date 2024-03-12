from DataModel.Vehicle import Vehicle


class EnvironmentManager:

    def __init__(self):
        pass

    def get_vehicle_list(self):
        vehicle1 = Vehicle("12:34:56", "dummy1")
        vehicle2 = Vehicle("78:90:01", "dummy2")
        vehicles = [vehicle1, vehicle2]
        return vehicles