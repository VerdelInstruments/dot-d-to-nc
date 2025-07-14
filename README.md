# dot_d_to_nc

This repository contains functions that allow a Bruker .d directory, or a series of them,  to be 
converted into a NetCDF file. 

Because Bruker only compile their code for Linux and Windows, this repository contains a 
Dockerfile that can be used to spin up a container on MacOS that will successfully run the 
file conversion. 

## Usage

### Windows, Linux 

If you are on Windows or Linux AMD64 you can run the code directly. You will need to install the 
required Python packages using 

```python
pip install -r requirements.txt
```

You can then run the code on your PC. You have two options: if you want to just process a single 
file, you can use the flag ```--single``` and run the following command in the root of the project: 

```python 
python ./src/extract.py --single INPUT.d OUTPUT
```

where `INPUT.d` is the path to the Bruker .d directory and `OUTPUT` is the path where you want 
the output NetCDF files to be saved. Two output files will be placed in the output 
directory: the '_timedomain.nc' and '_fourier_domain.nc' files. These filenames are preceded by 
the name of the input ```.d``` directory.


Alternatively, if you have multiple .d directories that you want to process, you can use the 
--directory flag and run the following command:

```python
python ./src/extract.py --directory INPUT_DIR OUTPUT
```
This will process all the .d directories in the `INPUT_DIR` directory and save the output in the 
output directory `OUTPUT`.




### Docker (for Mac users)

Since the Bruker software is not available for Mac, you can use Docker to run the code in a 
Linux container. To begin with, you must have Docker installed. 

**NOTE**: This is a highly memory-intensive program. You need to make sure that you have set 
Docker's memory limit to around 15 GB. 

To set the memory limit for Docker: 
- On macOS or Windows, open Docker Desktop
- Go to: Settings > Resources > Memory
- Increase to 16 GB and click "Apply & Restart"

You must then build the Docker image, using this command: 

```bash
 docker build --file Dockerfile --platform linux/amd64 -t conversion-service . 
```

Once you have built the container, you can run it using 

```bash
docker run --platform linux/amd64 -v "$(pwd)/INPUT.d:/input" -v "$(pwd)/output:/output" 
conversion-service python3 extract.py /input /output
```

when you are in the root of the directory. 