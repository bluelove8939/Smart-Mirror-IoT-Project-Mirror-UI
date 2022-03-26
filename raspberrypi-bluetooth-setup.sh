bluetoothctl -- system-alias 'Smart Mirror(SSS001)'
bluetoothctl -- discoverable-timeout 0  # device is always discoverable
bluetoothctl -- discoverable on  # turn on discoverable

sudo sdptool add --channel=1 SP  # add RFCOMM service to port 1
sudo chmod 777 /var/run/sdp  # sdp permission setting