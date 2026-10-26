#!/usr/bin/env bash
set -euo pipefail

LIO_ROOT="$HOME/lio"
ROOT_SETUP="$LIO_ROOT/devel/setup.bash"

if [[ ! -f "$ROOT_SETUP" ]]; then
  echo "Missing $ROOT_SETUP" >&2
  echo "Run: cd $LIO_ROOT && catkin_make -DCMAKE_BUILD_TYPE=Release" >&2
  exit 2
fi

gnome-terminal --title="LIO - Livox Driver" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$ROOT_SETUP"'"
  roslaunch livox_ros_driver2 msg_MID360.launch
  exec bash
'

sleep 2

gnome-terminal --title="LIO - Point-LIO" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$ROOT_SETUP"'"
  roslaunch point_lio mapping_mid360.launch
  exec bash
'

sleep 3

gnome-terminal --title="LIO - ROG-Map" -- bash -lc '
  source /opt/ros/noetic/setup.bash
  source "'"$ROOT_SETUP"'"
  roslaunch rog_map_example pointlio_mid360.launch
  exec bash
'
