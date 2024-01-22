#!/bin/bash

# ANSI color codes
GREEN='\e[32m'
RED='\e[31m'
RESET='\e[0m'

# 1.Obtained sudo privileges
echo "1.Obtained sudo privileges.."
sudo echo "Obtained sudo privileges ok"

# 2.Restarting Bluetooth service
echo "2.Restarting Bluetooth service..."
sudo systemctl restart bluetooth.service

sleep 1

# 3. Clear the connected bluetooth AML devices
echo "3.Clear the connected bluetooth AML devices..."
raw_device_info=$(bluetoothctl -- devices)

device_info=$(echo "$raw_device_info" | grep "Device")

if [ -z "$device_info" ]; then
    echo "No devices found. No need to clean the BLE info, exiting script."
fi

device_array=()
device_idx=0
while IFS= read -r line; do
    device_array+=("$line")
done <<< "$device_info"

target_name="VEWDT5W"
removed_message_ok="Device has been removed"
removed_message_fail="Failed to remove device"

for device in "${device_array[@]}"; do
    current_device_with_idx="dev_${device_idx}"
    echo "${current_device_with_idx}: $device"

    # find the device contains the target name
    if [[ $device == *"$target_name"* ]]; then
        target_address=$(echo "$device" | awk '{print $2}')
        echo "  Removing device ${current_device_with_idx}..."
        result=$(bluetoothctl -- remove "$target_address")
        
        if [[ $result == *"$removed_message_ok"* ]]; then
            echo "  ${current_device_with_idx} has been removed."
        elif [[ $result == *"$removed_message_fail"* ]]; then
            echo "  ${current_device_with_idx} failed to be removed."
            echo -e "  ${RED}Clean the BLE info fail, exiting script.${RESET}"
            exit 1
        else
            echo "  Unknown error occurred."
        fi
    else
        echo "  ${current_device_with_idx} is not the target device, skip."
    fi

    ((device_idx++))
    sleep 0.5
done

echo -e "${GREEN}Clean the BLE info successfully.${RESET}"