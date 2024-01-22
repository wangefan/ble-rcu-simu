#!/bin/bash

# ANSI color codes
GREEN='\e[32m'
RED='\e[31m'
RESET='\e[0m'

scan_thread() {
  echo "Remote begin to scan.."
  result=$(ssh "$ssh_user@$target_ip" "bluetoothctl --timeout 20 scan on")
}
echo "1.Obtained sudo privileges.."
sudo echo "Obtained sudo privileges ok"
ssh_user="root"
target_rcu_name="$1"
echo "target_rcu_name = $target_rcu_name"
# 檢查是否有指定 IP 參數
if [ -n "$2" ]; then
  target_ip="$2"
else
  # 檢查是否有之前成功登入的 IP
  if [ -f "last_successful_ip.txt" ]; then
    target_ip=$(cat last_successful_ip.txt)
  else
    # 要求使用者輸入 IP
    read -p "Enter the target IP: " target_ip
  fi
fi
echo "target_ip = $target_ip"

# 嘗試 SSH 連接
ssh_result=$(ssh -o BatchMode=yes -o ConnectTimeout=5 "$ssh_user@$target_ip" "echo 1")
echo "ssh_result = $ssh_result"

# 檢查 SSH 連接結果
if [ "$ssh_result" == "1" ]; then
  echo "SSH connection successful to $target_ip"
  echo "$target_ip" > last_successful_ip.txt

  dev_enforce_status=$(ssh -o BatchMode=yes -o ConnectTimeout=5 "$ssh_user@$target_ip" "getenforce")
  echo "result of getenforce: $dev_enforce_status"
  if [ "$dev_enforce_status" != "Disabled" ]; then
    # 如果不是 Disabled，則將 SELinux 狀態設為 Permissive
    $(ssh -o BatchMode=yes -o ConnectTimeout=5 "$ssh_user@$target_ip" "setenforce 0")
  fi

  device_to_remove=$(ssh "$ssh_user@$target_ip" "bluetoothctl -- devices Paired")
  while IFS= read -r line; do
    device_array_remove+=("$line")
  done <<< "$device_to_remove"

  device_idx=0
  removed_message_ok="Device has been removed"
  removed_message_fail="Failed to remove device"

  for device in "${device_array_remove[@]}"; do
    current_device_with_idx="dev_${device_idx}"
    echo "${current_device_with_idx}: $device"
    target_address=$(echo "$device" | awk '{print $2}')
    echo "  Removing device ${current_device_with_idx}..."
    result=$(ssh "$ssh_user@$target_ip" "bluetoothctl -- remove $target_address")
    
    if [[ $result == *"$removed_message_ok"* ]]; then
        echo "  ${current_device_with_idx} has been removed."
    elif [[ $result == *"$removed_message_fail"* ]]; then
        echo "  ${current_device_with_idx} failed to be removed."
        echo -e "  ${RED}Clean the BLE info fail, exiting script.${RESET}"
        exit 1
    else
        echo "  Unknown error occurred."
    fi
    ((device_idx++))
  done

  echo "Start to scan..:"
  scan_thread & 
  
  num_get_device=15
  found=0
  for ((i = 1; i <= num_get_device; i++)); do
    device_discovered=$(ssh "$ssh_user@$target_ip" "bluetoothctl -- devices")
    #echo "device_discovered = $device_discovered"
    #device_discovered_array=($(read_lines_to_array "$device_discovered"))
    while IFS= read -r line; do
      device_discovered_array+=("$line")
    done <<< "$device_discovered"
    for device in "${device_discovered_array[@]}"; do
      if [[ $device == *"$target_rcu_name"* ]]; then
        echo "Found $device"
        found=1
        # Begin to connect
        target_address=$(echo "$device" | awk '{print $2}')
        device_discovered=$(ssh "$ssh_user@$target_ip" "bluetoothctl -- pair $target_address") 
        sleep 2
        device_discovered=$(ssh "$ssh_user@$target_ip" "bluetoothctl -- connect $target_address") 
        echo -e "${GREEN}Connect to $target_address ok! Finish.${RESET}"
        break
      fi
    done
    
    if [ "$found" -eq 1 ]; then
      break
    else
      sleep 1
    fi
  done
  if [ "$found" -eq -0 ]; then
    echo -e "${RED}No deivces found, finsh.${RESET}"
  fi
else
  echo "SSH connection failed to $target_ip"
  exit 1
fi
