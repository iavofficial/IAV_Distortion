from VehicleManagement.FleetController import FleetController

def test_scan_for_anki_cars():
    mut = FleetController()

    found_vehicles = mut.scan_for_anki_cars()

    mut.__del__()
    assert len(found_vehicles) == 2