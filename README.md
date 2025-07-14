# dot_d_to_nc

This repository contains functions that allow a Bruker .d directory to be converted into a 
NetCDF file. 

The project is wrapped up using Docker, because Bruker only package their compiled C software for 
Linux and Windows. The Docker implementation uses Linux and the corresponding .so. 

## Usage

The Docker image can be run with the following command:

```bash
docker run --platform linux/amd64 -v "$(pwd)/INPUT.d:/input" -v "$(pwd)/output:/output" 
conversion-service python3 extract.py /input /output
```

Naturally, this assumes you have the Docker image running. If not, you can build it using

```bash
 docker build --file Dockerfile --platform linux/amd64 -t conversion-service . 
```

when you are in the root of the directory. 