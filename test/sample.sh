#!/bin/sh

#Sample script to run the code
curl https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python/base/docker-compose.yml > ./test/docker-compose.yml
docker-compose -f ./test/docker-compose.yml up -d

#Run a directory
python source/script.py localhost 10000 python ./test/code/
#Reset between runs
python source/script.py localhost 10000 python ./test/files/run.txt -rbf true -dc "docker-compose -f ./test/docker-compose.yml"
docker-compose -f ./test/docker-compose.yml up -d
#Should ignore the files in the sub_dir directory
python source/script.py localhost 10000 python ./test/files/run.txt -ip ./test/files/ignore-files.txt
#Should ignore the sub_dir directory
python source/script.py localhost 10000 python ./test/files/run.txt -ip ./test/files/ignore-directories.txt
#Run a file for the PR check
python source/script.py localhost 10000 python ./test/files/run.txt
