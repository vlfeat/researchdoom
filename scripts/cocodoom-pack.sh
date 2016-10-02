#!/bin/bash

COCODOOM_VER=1.0
COCODOOM_DIR=./data/cocodoom
base=$(dirname "${COCODOOM_DIR}")
cocodoom=$(basename "${COCODOOM_DIR}")

(
    set -e
    tmpfile=$cocodoom/files-full.txt
    cd $base
    cat $cocodoom/images-full.txt | sed -e "s/^/$cocodoom\//" > $tmpfile
    cat $cocodoom/images-full.txt | sed -e "s/^/$cocodoom\//" -e "s/rgb/depth/" >> $tmpfile
    cat $cocodoom/images-full.txt | sed -e "s/^/$cocodoom\//" -e "s/rgb/objects/" >> $tmpfile
    echo >> $tmpfile
    printf "%s\n" $cocodoom/map-full-{train,val,test}.json >>  $tmpfile
    printf "%s\n" $cocodoom/run-full-{train,val,test}.json >>  $tmpfile
    echo $tmpfile
    tar zcvhf cocodoom-full-v${COCODOOM_VER}.tar.gz -T $tmpfile
)

(
    set -e
    tmpfile=$cocodoom/files.txt
    cd $base
    cat $cocodoom/images.txt | sed -e "s/^/$cocodoom\//" > $tmpfile
    echo >> $tmpfile
    printf "%s\n" $cocodoom/map-{train,val,test}.json >>  $tmpfile
    printf "%s\n" $cocodoom/run-{train,val,test}.json >>  $tmpfile
    echo $tmpfile
    tar zcvhf cocodoom-v${COCODOOM_VER}.tar.gz -T $tmpfile
)

