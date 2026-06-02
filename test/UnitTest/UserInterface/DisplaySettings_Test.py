from EnvironmentManagement.ConfigurationHandler import ConfigurationHandler


config_handler = ConfigurationHandler()


def test_normalize_bulletpoints_strips_spacing_and_markers():
    raw_bulletpoints = """
    - First point
    * Second point
    1. Third point

    Fourth point
    """

    assert config_handler.normalize_bulletpoints(raw_bulletpoints) == [
        "First point",
        "Second point",
        "Third point",
        "Fourth point",
    ]


def test_normalize_bulletpoints_accepts_list_input():
    raw_bulletpoints = ["  First  ", "", "Second", "   - Third"]

    assert config_handler.normalize_bulletpoints(raw_bulletpoints) == [
        "First",
        "Second",
        "Third",
    ]


def test_right_side_content_mode_prefers_bulletpoints_when_both_are_set():
    display_settings = {
        "disp_cm_qr_codes_enabled": True,
        "disp_cm_bulletpoints_enabled": True,
    }

    assert config_handler.get_right_side_content_mode(display_settings) == "bulletpoints"
