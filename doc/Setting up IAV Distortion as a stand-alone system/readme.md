# IAV Distortion as stand-alone system
Since IAV Distortion is designed to be easily used on events, it is designed to be able to run on its own without the need of additional equipment like a network router or anything else.
To be able to run the system as a stand-alone system, it has to provide an access point other devices can connect to.
In the following it is described how to configure a Raspberry Pi (running Raspberry OS - Debian version 12 (bookworm)) for this porous.

## Configuration Parameter
The following table shows a list of configuration parameters you have to set during the configuration process.
You can choose the value for these values by your own.
Make sure to remember them, especially the set password ;).

| Parameter                        | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| <network_connection_name>        | Name for the network configuration in Linux                                 |
| <your_accesspoint_SSID_name>     | Displayed name of the network (can be the same as <network_connection_name> |
| <ip-adress_of_pi_as_accesspoint> | Gateway IP-adress. (Used to open webinterfaces)                             |
| <your_password>                  | Password for connecting to the access point.                                |

## Configuration via command line
In the following it is described how the Raspberry Pi can be configured as an access point using the network management tool 'nmcli' included on the Pi in the command line.
You may adapt the configuration to your needs.
Alternatively an access point can also be configured using the graphical interface of the pi (will not be described here).

Type in or copy the following command in the command line.
Replace the parameters (see table above) with your chosen values.

1. The following command adds a new connection for the network interface "wlan0". The connection mode is set with " WP" for the access point. The <your_accesspoint_name> parameter is used to configure the name under which the network is later visible.
```
~$ sudo nmcli con add type WiFi ifname wlan0 mode WP con-name <network_connection_name> SSID "<your_accesspoint_SSID_name>" AutoConnect true
```
2. The following command configures the use of 2.4GHz (compatible with more devices) and specifies the IP address (<ip-address_of_pi_as_access_point>) of the access point.
```
~$ sudo nmcli con modify <network_connection_name> 802-11-wireless.band bg ipv4.method shared ipv4.address <ip-address_of_pi_as_accesspoint>/24
```
3. The following command disables IPv6.
```
~$ sudo nmcli con modify <network_connection_name> ipv6.method disabled
```
4. Configure encryption method to WPA
```
~$ sudo nmcli con modify <network_connection_name> wifi-sec.key-mgmt wpa-psk
```
5. Configure the password (<your_password>) for the access point.
```
~$ sudo nmcli con modify <network_connection_name> wifi-sec.psk "<your_password>"
```
6. Automatically activate the access point with the highest priority.
```
~$ sudo nmcli con modify <network_connection_name> connection.autoconnect yes connection.autoconnect-priority 0
```
7. Activate client isolation.
```
~$ nmcli connection modify <network_connection_name> 802-11-wireless.ap isolation 1
```
8. Activate the access point
```
~$ sudo nmcli con up <network_connection_name>
```
