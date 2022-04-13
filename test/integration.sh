#!/bin/sh

#Integration "tests" for the script. It just runs stuff and makes sure nothing breaks
#An automated check to make sure the correct files are ran and skipped will eventually come
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
#Run a file for PR check
python source/script.py localhost 10000 python ./test/files/run.txt
