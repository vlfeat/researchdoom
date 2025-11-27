#!/bin/bash
set -ex

ENGINE=./engines/chocolate/bin/rdm-record.sh
COCODOOM_DIR=/tmp/cocodoom-legacy-raw
COCODOOM_TMPDIR=/tmp/cocodoom-legacy-tmp
WAD_DIR=./data/wads

function get_lmp() {
    if test ! -e "${COCODOOM_TMPDIR}/lmps/run$1.lmp"
    then
        base=$(basename "$2")
        mkdir -p ${COCODOOM_TMPDIR}/lmps/run$1
        curl "$2" > ${COCODOOM_TMPDIR}/lmps/run$1/archive.zip
        (cd ${COCODOOM_TMPDIR}/lmps/run$1 ; curl "$2" | unzip -o archive.zip)
        lmpPath=$(find "${COCODOOM_TMPDIR}/lmps/run$1" -iname '*.lmp' -print0 | xargs -0 -I{} printf '%s\n' "{}" | LC_ALL=C sort | head -n1)
        cp -fv $lmpPath "${COCODOOM_TMPDIR}/lmps/run$1.lmp"
    fi
}

function record() {
    get_lmp $1 $3
    if test -e ${COCODOOM_DIR}/run$1/.done; then return ; fi
    mkdir -p ${COCODOOM_DIR}/run$1
    (
        set -e
        ${ENGINE} ${WAD_DIR}/$2.wad \
            ${COCODOOM_TMPDIR}/lmps/run$1.lmp \
            ${COCODOOM_DIR}/run$1
        touch ${COCODOOM_DIR}/run$1/.done
    )
}

# Original DOOMEDSDA demo files for CocoDoom
# url=http://doomedsda.us/lmps
# record 1 doom2 $url/945/1/30uvmax3.zip     # 1:34:50
# record 2 doom2 $url/945/1/lvall-13018.zip  # 1:30:18
# record 3 doom2 $url/945/1/lvallx5557.zip   # 55:57
# record 4 doom2 $url/945/2/30uv1402.zip     # 14:02
# record 5 doom2 $url/945/2/30uv1448.zip     # 14:48
# record 6 doom2 $url/945/2/30uv1617.zip     # 16:17

# Working equivalent (July 2026)
url=https://dsdarchive.com/files/demos/doom2

record 1 doom2-v1.9 $url/26819/lvall-9450.zip  # 1:34:50
record 2 doom2-v1.9 $url/26818/lvall-9018.zip  # 1:30:18
record 3 doom2-v1.9 $url/26813/lvallx5557.zip  # 55:57
record 4 doom2-v1.9 $url/26828/lvallx1402.zip  # 14:02
record 5 doom2-v1.9 $url/26831/lvallx1448.zip  # 14:48
# record 6 doom2-v1.9 $url/26832/lvallx1617.zip  # 16:17 (fails as this run is not for Chocolate Doom)
