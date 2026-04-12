#!/bin/bash

#────────────────────────────────────────────────────────────────────────
echo  "start initialize-bash-shell.bash..."


# ローカルネットワーク内でロボットのホスト名を探し、IPアドレスに解決する
# 'HSRB_HOSTNAME' はコンテナ起動時に ./RUN-DOCKER-CONTAINER.bashによって'~/.bashrc' で記述される想定
HSRB_IP=`getent hosts ${HSRB_HOSTNAME} | cut -d ' ' -f 1`
echo "HSRB_HOSTNAME: '${HSRB_HOSTNAME}"
echo "HSRB_IP: '${HSRB_IP}'."
if [ -z "${HSRB_IP}" ]; then
  # ロボットのホスト名が見つからない場合、デフォルトのDockerネットワーク ('docker0') を使って 'ROS_IP' を設定
  export ROS_IP=$(LANG=C /sbin/ifconfig docker0 | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*')
  echo "Failed to resolve host name '${HSRB_HOSTNAME}'"
  echo "ROS_IP is set from docker0:'${ROS_IP}'"
else
  # ロボットのホスト名が見つかった場合、その通信インターフェースを使って 'ROS_IP' を設定
  # TODO: PythonではなくBashで実装する
  export ROS_IP=`python /graspgen/docker/print-interface-ip.py ${HSRB_IP}`
  echo "ROS_IP is set to '${ROS_IP}' "
  echo "From HSRB_HOSTNAME: '${HSRB_HOSTNAME}' and"
  echo "From HSRB_IP: ${HSRB_IP}."
fi
if [ -z "${ROS_IP}" ]; then
  # それでも 'ROS_IP' が空の場合、安全のため docker0 を使用
  export ROS_IP=$(LANG=C /sbin/ifconfig docker0 | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*')
  echo "Failed to determine ROS_IP."
  echo "ROS_IP is set from docker0:'${ROS_IP}'"
fi

export ROS_HOME=~/.ros

# ─────────────────────────────────────────────────────────────────────────
#────────────────────────────────────────────────────────────────────────
# Prompt color settings

MODE=""
MODE_START=$'\e[0m'
MODE_END=$'\e[0m'

if [ -n "${HSR_DOCKER_MODE:-}" ]; then
  if [ "${HSR_DOCKER_MODE}" = "sim_mode" ]; then
    MODE="<sim_mode>"
    MODE_START=$'\e[44;1;37m'   # white on blue
    MODE_END=$'\e[0m'
  elif [ "${HSR_DOCKER_MODE}" = "hsrb_mode" ]; then
    MODE="<hsrb_mode>"
    MODE_START=$'\e[41;1;37m'   # white on red
    MODE_END=$'\e[0m'
  fi
fi

HOST_START=$'\e[1;36m'   # cyan
PATH_START=$'\e[1;34m'   # dark blue
PROMPT_END=$'\e[0m'

if [ "$(id -u)" -eq 0 ]; then
  PROMPT_MARK="#"
else
  PROMPT_MARK="$"
fi

build_prompt() {
  PS1=""
  if [ -n "${MODE}" ]; then
    PS1+="\[${MODE_START}\]${MODE}\[${MODE_END}\] "
  fi
  PS1+="\[${HOST_START}\]\u@\h\[${PROMPT_END}\]:"
  PS1+="\[${PATH_START}\]\w\[${PROMPT_END}\]${PROMPT_MARK} "
}

#────────────────────────────────────────────────────────────────────────
# mode apply

if [ -n "${HSR_DOCKER_MODE:-}" ]; then
  if [ "${HSR_DOCKER_MODE}" = "sim_mode" ]; then
    export ROS_MASTER_URI="http://localhost:11311"
    build_prompt
    export PS1
  elif [ "${HSR_DOCKER_MODE}" = "hsrb_mode" ]; then
    export ROS_MASTER_URI="http://hsrb31.local:11311"
    build_prompt
    export PS1
  fi
else
  sim_mode() {
    export HSR_DOCKER_MODE="sim_mode"
    export ROS_MASTER_URI="http://localhost:11311"
    MODE="<sim_mode>"
    MODE_START=$'\e[44;1;37m'
    MODE_END=$'\e[0m'
    build_prompt
    export PS1
  }

  hsrb_mode() {
    export HSR_DOCKER_MODE="hsrb_mode"
    export ROS_MASTER_URI="http://hsrb31.local:11311"
    MODE="<hsrb_mode>"
    MODE_START=$'\e[41;1;37m'
    MODE_END=$'\e[0m'
    build_prompt
    export PS1
  }
fi
export LANG=ja_JP.UTF-8
