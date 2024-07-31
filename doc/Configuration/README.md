# Configuration File
There are a bunch of parameters that can be configured in the [config_file.json](../../src/config_file.json).
The config_file.json is a json file that includes all configurable parameters for IAV-Distortion.
The json is structured according to different main topics which include the corresponding parameters.
These parameters will be described in the following.

## Configuration Parameters

| Topic                   | Parameter                          | Default value           | type | Description                                                                                                                                                                                        |
|-------------------------|------------------------------------|-------------------------|------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **"virtual_cars_pics"** |                                    |                         |      | **Contains dictionary of {`virtual_vehicle_id`: `image_name`}. Images have to be placed in `static/images/Virtual_Vehicles`. No limit for max images. But make sure to use correct vehicle id's!** |
|                         | "Virtual Vehicle 1"                | "D1FFAF51CB30_top.webp" | str  | Image file name                                                                                                                                                                                    |
|                         | "Virtual Vehicle 2"                | "E4FD708CB27D_top.webp" | str  | Image file name                                                                                                                                                                                    |
|                         | ...                                | ...                     | str  | Image file name                                                                                                                                                                                    |
|                         | "Virtual Vehicle _x_"              | ...                     | str  | Image file name                                                                                                                                                                                    |
| **"driver"**            |                                    |                         |      | **Parameters regarding the driver ui.**                                                                                                                                                            |
|                         | "driver_heartbeat_interval_ms"     | 5000                    | int  | Interval in ms used to send a heartbeat from a driver ui client to the server.                                                                                                                     |
|                         | "driver_heartbeat_timeout_s"       | 30                      | int  | Time after which a player gets removed from the game if the server didn't received a heartbeat from the client.                                                                                    |
|                         | "driver_reconnect_grace_period_s"  | 5                       | int  | If disconnected player reconnects to the server in this period after disconnecting, the player will remain in the game. Otherwise the player will be removed from the game.                        |
|                         | "driver_background_grace_period_s" | 30                      | int  | Period until a player will be removed from the game because he navigated away from the driver ui, to prevent inactive players remain in the game.                                                  |
| **"game_config"**       |                                    |                         |      | **Parameters regarding the game configuration.**                                                                                                                                                   |
|                         | "game_cfg_playing_time_limit_min"  | 5                       | int  | Period until a player will be removed from the game, because of his playing time.                                                                                                                  |
| **"environment"**       |                                    |                         |      | **Parameters regarding the game environment**                                                                                                                                                      |
|                         | "env_auto_discover_anki_cars"      | 1                       | bool | If True, the system scans periodically for Anki cars and automatically connects to them if they are **not placed on the charger**.                                                                 |


