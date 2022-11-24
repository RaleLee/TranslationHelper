#!/bin/bash
#SBATCH -J trans
#SBATCH -p compute
#SBATCH -N 1
#SBATCH -t 2-20:00:00
#SBATCH -w gpu30
source ~/.bashrc
conda activate base

export http_proxy="http://192.168.1.254:7894"
export https_proxy="http://192.168.1.254:7894"
t="txt"
for file in $1/*
do
{
    filepath=`basename $file`
    #echo ${filepath:0-3:3}
    if [ ${filepath:0-3:3} = $t ];then
       echo $filepath
       python -u translate_jsonl.py -l=$2 -f=$1/$filepath
    fi
}&
done
wait
