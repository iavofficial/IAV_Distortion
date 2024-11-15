#!/bin/bash

# script to setup an accesspoint on raspberry pi

function configure_password() {
    while true; do
        while true; do
            read -s -p "2. Enter password for your accesspoint (at least 8 charakters): " password
            echo
            if [[ ${#password} -ge 8 ]]; then
                # accept input, since it has at least 6 charakters
                break
            else
                echo "Password must be at least 6 characters long. Please try again."
            fi
        done
            read -s -p "2.1 Confirm password: " password2
            echo
            if [ "$password" = "$password2" ]; then
                echo "Passwords match. Password will be used..."
                ap_password=$password
                break
            else
                echo "Passwords do not match. Please try again."
            fi
    done
}

function configure_ip_address() {
    while true; do
        read -p "3. Enter ip-address for your accesspoint: " ip_addr
                    
        read -p "3.1 Confirm ip-address: " ip_addr2
        echo
        if [ "$ip_addr" = "$ip_addr2" ]; then
            echo "IP addresses match. IP address will be used..."
            ap_ip_addr=$ip_addr
            break
        else
            echo "IP addresses do not match. Please try again."
        fi
    done
}


echo "Setup an accesspoint on your system:"
while true; do
    read -p "1. Choose a name for your accesspoint: " ap_name
    if [[ ${#ap_name} -ge 4 ]]; then
    # accept input, since it has at least 4 charakters
    break
    else
    echo "Accesspoint name must be at least 4 characters long. Please try again."
    fi
done

configure_password
configure_ip_address

echo "4. Setting up accesspoint. Please wait..."
sudo nmcli con add type wifi ifname wlan0 mode ap con-name "$ap_name" ssid "$ap_name"
sudo nmcli con modify "$ap_name" 802-11-wireless.band a ipv4.method shared ipv4.addresses "$ap_ip_addr/24"
sudo nmcli con modify "$ap_name" ipv6.method ignore
sudo nmcli con modify "$ap_name" 802-11-wireless-security.key-mgmt wpa-psk
sudo nmcli con modify "$ap_name" 802-11-wireless-security.psk "$ap_password"
sudo nmcli con modify "$ap_name" connection.autoconnect yes connection.autoconnect-priority 0
sudo nmcli connection modify "$ap_name" 802-11-wireless.ap-isolation 1

read -p "Do you want to activate the accesspoint now? (y/n) " -n 1 -r
echo    # move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo nmcli con up $ap_name
echo "Accesspoint activated"
else
    echo "Accesspoint configured, but not activated."
fi

