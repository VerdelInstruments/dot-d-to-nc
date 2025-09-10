#!/bin/bash

# runs the docker container
# mounting a directory so we can extract the files
# mounting an input. the file is the one i sent James
# /var/task is the working directory
# shouldn't quite need 15 gb but it is pretty memory intensive
# needs to be amd64 for the .so files from Bruker
# takes the data from /input_data (which we mounted) and puts it in /var/task/output, which is also locally mounted
docker run --rm -it \
  --memory=20g \
  -v "$(pwd)/output:/var/task/output" \
  -v "$(pwd)/250702_davaoH2O_021.d:/input_data" \
  -w /var/task \
  --platform linux/amd64 \
  conversion-service python3 extract.py --single /input_data ./output

