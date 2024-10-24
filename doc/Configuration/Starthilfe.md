# Setup

1. Python 3.11 installieren
2. Projekt von GitHub clonen
3. cmd starten
4. folgende Commands ausführen:
```console
C:\...> pip install pipenv
...
C:\...> cd Projektverzeichnis
...\IAV_Distortion> pipenv install
```

# Starten

```console
...\IAV_Distortion> cd src
...\IAV_Distortion\src> pipenv run python main.py
```
Projekt startet auf IP 0.0.0.0:5000
Ist dann im Browser erreichbar über z.B. localhost:5000/[endpunkt]

# Endpunkte

Zum Testen kann der Endpunkt der Fahrersteuerung unter 
    
    localhost:5000/driver

erreicht werden. Es sollten dann entsprechende Steuerelemente für die Fahrzeugkontrolle angezeigt werden.

Weitere Endpunkte sind:
- /staff
- /car_map

# Strecke

Standardmäßig ist keine Strecke ausgewählt. Dementsprechend wird unter dem Endpunkt auch keine Map angezeigt, sondern ein Ersatztext.

In der config_file.json in /src kann als Attribute track eine Strecke definiert werden, die dann gerendert werden kann. Einfach als weiteres Attribut in die JSON einfügen. Beispiel folgt (kein gutes Beispiel, kann aber angezeigt werden):

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