#!/bin/sh

export UN=$(id -nu)
RCU_WORKIN_FOLDER=$(dirname "$PWD")
echo "RCU_WORKIN_FOLDER = ${RCU_WORKIN_FOLDER}"
RCU_WORKIN_FOLDER_NAME=$(basename ${RCU_WORKIN_FOLDER})
echo "RCU_WORKIN_FOLDER_NAME = ${RCU_WORKIN_FOLDER_NAME}"
sudo docker run -it --net=host --cap-add=NET_ADMIN \
	-v ${RCU_WORKIN_FOLDER}:/home/${UN}/${RCU_WORKIN_FOLDER_NAME}/ \
    -w /home/${UN}/${RCU_WORKIN_FOLDER_NAME} \
	--privileged \
    tivo-sim-rcu-sys:latest /bin/bash
