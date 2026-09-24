#!/usr/bin/env bash
set -euo pipefail

LIO_ROOT="$HOME/lio"

gnome-terminal --title="LIO - Livox Driver" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$LIO_ROOT"'/livox_ros_driver2/devel/livox_ros_driver2/setup.bash"
  roslaunch livox_ros_driver2 msg_MID360.launch
  exec bash
'

sleep 2

gnome-terminal --title="LIO - Point-LIO" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$LIO_ROOT"'/livox_ros_driver2/devel/livox_ros_driver2/setup.bash"
  source "'"$LIO_ROOT"'/Point-LIO/devel/setup.bash"
  roslaunch point_lio mapping_mid360.launch
  exec bash
'

sleep 3

gnome-terminal --title="LIO - ROG-Map" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$LIO_ROOT"'/ROG-Map/devel/setup.bash"
  roslaunch rog_map_example pointlio_mid360.launch
  exec bash
'
