# dot_d_to_nc

This repository contains functions that allow a Bruker .d directory to be converted into a 
NetCDF file. 

The project is wrapped up using Docker, because Bruker only package their compiled C software for 
Linux and Windows. The Docker implementation uses Linux and the corresponding .so. 

## Usage

### Windows, Linux 

If you are on Windows or Linux AMD64 you can run the code directly. You will need to install the 
requirements using 

```python
pip install -r requirements.txt
```

You can then run the code on your PC. You have two options: if you want to just process a single 
file, you can use the flag ```--single``` and run the following command in the root of the project: 

```python 
python ./src/extract.py --single INPUT.d OUTPUT
```

Alternatively, if you have multiple .d directories that you want to process, you can use the 
--directory flag and run the following command:

```python
python ./src/extract.py --directory INPUT_DIR OUTPUT
```
This will process all the .d directories in the `INPUT_DIR` directory and save the output in the 
output directory `OUTPUT`.


where `INPUT.d` is the path to the Bruker .d directory and `OUTPUT` is the path where you want 
the output NetCDF files to be saved. Two output files per input file will be placed in this 
directory: the '_timedomain.nc' and '_fourier_domain.nc' files. These filenames are preceded by 
the name of the input ```.d``` directory.



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