#!/bin/bash

RECORD=./engines/chocolate/bin/rdm-record.sh
COCODOOM_DIR=./data/cocodoom
COCODOOM_TMPDIR=./data/tmp
WAD_DIR=./data/wads

runs="\
30uvmax3 \
doom2max13018 "

# doom2d2allmax_829 \

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
    mkdir -p $COCODOOM_DIR/run$1
    ${RECORD} ${WAD_DIR}/$2.wad \
              ${COCODOOM_TMPDIR}/lmps/$3.lmp \
              ${COCODOOM_DIR}/run$1
}


# http://doomedsda.us/wad945m240.html

get_lmp 30uvmax3      http://doomedsda.us/lmps/945/1/30uvmax3.zip
get_lmp doom2max13018 https://www.doomworld.com/vb/attachment.php?postid=1638449

record 1 doom2 30uvmax3
