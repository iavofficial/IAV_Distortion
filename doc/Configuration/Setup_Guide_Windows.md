# Setup

1. Install Python 3.11
1. Execute this command in cmd in any directory (make sure, cmd is using Python 3.11 for this if you have other versions installed too!):
```console
C:\...> pip install pipenv
```
1. Clone project from Github
1. Execute the file IAV_Distortion/src/get_dependencies.sh
1. Execute this command in IAV_Distortion/src 
```console
...\IAV_Distortion> pipenv install -d
```

# Starting the project

```console
...\IAV_Distortion\src> pipenv run python main.py
```
The project will start at IP 0.0.0.0:5000

It will then be available at: 
	
	localhost:5000/[endpoint]

Nothing is available at:

	localhost:5000

so don't worry if that URL won't even load

# Endpoints

Here is a list of endpoints to check if the project is running correctly:
    
    localhost:5000/driver
		- Should show GUI elements for car controls
	localhost:5000//staff
		- Should show a login page
	localhost:5000//car_map
		- Should show a track or a message displaying that there is no track configured yet

These are not all possible endpoints.

# Track

If there is no track configured one must be added manually before a race can be started. This can be done by manually adding a track in the config file or scanning one using a physical car.

## Via config file

In the config_file.json in /src a track can be added as an attribute. What follows is an example track. It's not a good example, but it should work to see if anything can be rendered. Just add this to the config file:

    "track": [
		{
			"type": "LocationService.TrackPieces.StartPieceAfterLine",
			"rotation": 90,
			"physical_id": 33,
			"length": 210,
			"diameter": 184,
			"start_line_width": 21
		},
		{
			"type": "LocationService.TrackPieces.StraightPiece",
			"rotation": 90,
			"physical_id": 33,
			"length": 210,
			"diameter": 184,
			"start_line_width": 21
		},
		{
			"type": "LocationService.TrackPieces.StartPieceBeforeLine",
			"rotation": 90,
			"physical_id": 33,
			"length": 210,
			"diameter": 184,
			"start_line_width": 21
		}
	]