#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


# Uninstall only
if [[ "$1" == "--uninstall" || "$1" == "-u" ]]; then
    echo "Uninstalling Oasis platform (docker compose down only)..."

    set +e
    docker compose -f $SCRIPT_DIR/portainer.yaml down --remove-orphans
    docker compose -f $SCRIPT_DIR/oasis-platform.yml down --remove-orphans
    docker compose -f $SCRIPT_DIR/oasis-ui.yml down --remove-orphans
    set -e

    echo "Uninstall complete."
    exit 0
fi


export $(grep -v '^#' .env | xargs)

export VERS_MDK=latest
export VERS_API=dev
export VERS_WORKER=dev
export VERS_UI=latest
export VERS_PIWIND='stable/2.3.x'

export SERVER_IMG=coreoasis/api_server
export WORKER_IMG=coreoasis/model_worker
export GIT_PIWIND=OasisPiWind

MSG=$(cat <<-END
Do you want to reinstall?
Note: This will wipe uploaded exposure and run data from the local API.
END
)


# Check for prev install and offer to clean wipe
if [[ $(docker volume ls | grep OasisData -c) -gt 1 || -d $SCRIPT_DIR/$GIT_PIWIND ]]; then
    while true; do read -r -n 1 -p "${MSG:-Continue?} [y/n]: " REPLY
        case $REPLY in
          [yY]) echo ; WIPE=1; break ;;
          [nN]) echo ; WIPE=0; break ;;
          *) printf " \033[31m %s \n\033[0m" "invalid input"
        esac
    done

    if [[ "$WIPE" == 1 ]]; then
        docker compose -f $SCRIPT_DIR/portainer.yaml down --remove-orphans

        printf "Deleting docker container:\n"
        set +e
        docker compose -f $SCRIPT_DIR/oasis-platform.yml -f $SCRIPT_DIR/oasis-ui.yml down --remove-orphans
        set -e
        printf "Deleting docker data: \n"
        rm -rf $SCRIPT_DIR/$GIT_PIWIND
        docker volume ls | grep OasisData | awk 'BEGIN { FS = "[ \t\n]+" }{ print $2 }' | xargs -r docker volume rm
    else
        echo "-- Reinstall aborted -- "
        exit 1
    fi
fi


# --- Clone PiWind ---------------------------------------------------------- #

mkdir -p $SCRIPT_DIR/$GIT_PIWIND
cd $SCRIPT_DIR/$GIT_PIWIND
git clone --depth 1 --branch $VERS_PIWIND https://github.com/OasisLMF/$GIT_PIWIND.git .
git checkout $VERS_PIWIND

# --- RUN Oasis Platform & UI ----------------------------------------------- #

cd $SCRIPT_DIR

set +e
docker pull ${WORKER_IMG:-coreoasis/model_worker}:${VERS_WORKER}
docker pull ${SERVER_IMG:-coreoasis/api_server}:${VERS_API}
docker pull ${PYTHONUI_IMG-coreoasis/oasispythonui_app}:${VERS_API:-latest}
set -e

# RUN OasisPlatform / OasisUI / Portainer
docker compose -f $SCRIPT_DIR/oasis-platform.yml up -d --no-build
docker compose -f $SCRIPT_DIR/oasis-ui.yml build --no-cache
docker compose -f $SCRIPT_DIR/oasis-ui.yml up -d
