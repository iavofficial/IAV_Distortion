# Default Showcase

This page describes a typical showcase, starting with the basic setup and including possible extensions.
This instruction is intended for users of the race track.
Preparations on developer level (e.g. adding new cars and images for these cars) is not described here.
These instructions assume that you have a prepared set.

## Main Components

- Racetrack (4x curves, 1x starting line, 1x straigt)
- Anki-Cars (incl. charger)
- Raspberry Pi running IAV Distortion (incl. power supply)
- 3 tablets (incl. charger)

optional:
- monitor (incl. cables: power, hdmi, hdmi-adapter)

## Setting up the track

1. Put the track pices together to form an oval
2. Set up the Raspberry Pi somewhere near the track and power it on
3. Set up the charger for the Anki Cars (charge the cars if needed)
4. Connect all devices to be used with the track to the WIFI of the Raspberry Pi
    - Scan to connect: <img src="..\..\src\UserInterface\static\images\QR_wifi_access_distortion-ap.PNG" style="width:100%;max-width:150px">
    - SSID: distortion-ap
    - pw: iavDistortion_2024
    
5. Place the tablets near the race track
    - 1x tablet for the staff
    - 2x tablets for visitors

*optional:*

5. Setup the monitor
    - a.) connect it to the micro HDMI port of the Raspberry Pi
    - b.) connect it to a laptop or use the display of a laptop (connect the laptop to the same WIFI)

> [!NOTE]
> The monitor is needed if you plan to use the virtual track and cars.

## Commissioning

1. Take the staff tablett and open the control page via any browser
    - either saved as a favorit
    - scan: <img src="..\QR_staff_url.PNG" style="width:100%;max-width:150px">
    - or: 192.168.1.1:5000/staff
2. Login by entering the password (provided with the track)
3. Place two Anki Cars on the track
    - the cars should be automatically discovered and connected to the game shortly after taking them from the charger
    - LED of the car turns blue and the car pops up in the "List of Players/Cars"
4. Take the two visitor tablets and open the driver ui
    - either saved as a favorit
    - scan: <img src="..\..\src\UserInterface\static\images\QR_driver_url.PNG" style="width:100%;max-width:150px">
    - or: 192.168.1.1:5000/driver

## Bsic Usage - no virtual track

> [!NOTE]
> Please check the configuration parameter [*Number of items on track*](#config_number_of_items) .

Place two Anki cars on the track.
Open the driver ui on the visitor tablets, so that they will be assigned to the cars.
For each set a moderate speed.
Use the left and right arrow to navigate against one track border once to calibrate the cars postiion to ensure correct handling.

Let interesting visitors control the cars.
After a short time activate a hacking scenario via the staff control page.
Use this as a conversation starter.
Reset the hacking scenario (set to scenario 0).


## Configuration

> [!NOTE]
> Normally the configuration is done by the track organizer and you don't have to configure anything.<br>
> Only some basic settings are described here.
> For other settings please contact the organizer of the track.

The settings can be accessed under the "Configuratio" tab of the staff ui.

### Track Settings

There are some settings you might want to adjust according to your specific show case.
Uner "Advanced Settings" in the "Configuration" tab, you can configure the following items:

**Playing Time [min]**: if this value is set to 0 there is no limit.
If you want to limit the playing time for a player you can set this value to a integer value >0.
Then a play will be kicked from the game after the specified amount of minutes to make sure other player in the queue get a chance for playing to.
(Reasonable if audiance can use their own devices.)


**Auto connect cars**: if activated, the Anki cars will be discovered and connected automatically when taken from the charging station.
If you have trouble with connecting the cars, you might want to try to turn it off and manually try to connect the cars.
Normally it is recommended to have it activated.

<a name="config_number_of_items"></a>

**Number of items on track**: This setting controls how many items (which enable the temporary protection against hacking) will spawn on the track.
If you don't use the virtual track, it is recommended to set the value to 0 to prevent confusion by randomly activating items on the track.
If the virtual track is used, the recommended number of items is 2.

In the menu "Minigame Settings" you can configure minigames for hacking and taking over cars.
Since this feature has not been finished yet it is recommended to deactivate all games listet under **Available Minigames**

To ensute that all these settings are applied, please restart the game after hitting the button "Apply Changes..."

### Car Map and themes

The car map can be configured in the "Display Settings" menu under the "Configuration" tab. (http://192.168.1.1:5000/staff/configuration/config_display_settings).

Here you can configure individual colors for the differen elements of the car map.
You can also enable or disable the slogan (on top of the car map) or insert an individual one.

You can also choose what will be shown on right side of the screen.
You can choose 
- **qr-codes** (connect to wifi and enter driver seat), if you want the audiance to also use their own devices
- **bullet points**, if you want to emphasize some USPs
- **disable**, to only show the track

If you choos the bullet points, a text field appears in wich you can write your bullet points.
Each row will be used a new bullet point.

The settings are applied as soon as you click the button "Apply changes..."

You can also apply themes which change the overall appearance (car map, car models, staff and driver ui's).
These will automatically override all current display settings with the default settings according to the themes.
You can adjust them afterwards.
