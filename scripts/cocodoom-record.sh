#!/bin/bash

ENGINE=./engines/chocolate/bin/rdm-record.sh
COCODOOM_DIR=./data/cocodoom-raw
COCODOOM_TMPDIR=./data/tmp
WAD_DIR=./data/wads

function get_lmp() {
    if test ! -e "${COCODOOM_TMPDIR}/lmps/$1.lmp"
    then
        base=$(basename "$2")
        mkdir -p ${COCODOOM_TMPDIR}/lmps
        curl "$2" > ${COCODOOM_TMPDIR}/lmps/$1.zip
        (cd ${COCODOOM_TMPDIR}/lmps ; unzip -o $1.zip)
    fi
}

function record() {
    if test -e ${COCODOOM_DIR}/run$1/.done; then return ; fi
    mkdir -p ${COCODOOM_DIR}/run$1
    (
        set -e
        ${ENGINE} ${WAD_DIR}/$2.wad \
            ${COCODOOM_TMPDIR}/lmps/$3.lmp \
            ${COCODOOM_DIR}/run$1
        touch ${COCODOOM_DIR}/run$1/.done
    )
}

get_lmp 30uvmax3           http://doomedsda.us/lmps/945/1/30uvmax3.zip
get_lmp doom2max13018      http://doomedsda.us/lmps/945/1/lvall-13018.zip
get_lmp doom2d2allmax_829  http://doomedsda.us/lmps/945/1/lvallx5557.zip

record 1 doom2 30uvmax3
record 2 doom2 doom2max13018
record 3 doom2 doom2d2allmax_829
