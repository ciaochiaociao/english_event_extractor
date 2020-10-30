#!/bin/bash
counter=0
CUR_PATH=$PWD
EEE_PATH=./EventEntityExtractor
for file in *.log
do
  if [ -f "$file" ]; then
      rm ./*.log
  fi
done

if [ $# -eq 1 ]
then
    DATA_PATH=$1
elif [ $# -eq 0 ]
then
    DATA_PATH=./data/films
else
    echo "no data path received, terminate."
    exit 1
fi

for data_file in $DATA_PATH/*; do
    cp $data_file .
    fp=${data_file##./*/}
    counter=$((counter+1))
    echo '===' $counter - $fp '==='
#     python3 main.py $fp > /dev/null 2>&1
    python3 main.py "$fp" 1>> stdout.log 2>> stderr.log
    echo 'generation of required files: done'
    cd "$EEE_PATH" || exit
    ./Release/JEE
    echo 'event entity extraion: done'
    cd "$CUR_PATH" || exit
    mv ./EventEntityExtractor/output/joint.results.txt ./output/${fp}.event.entity
    rm $fp
    mv $fp.json corenlp_jsons/
    echo $fp finished: `date "+%H:%M:%S"`
done