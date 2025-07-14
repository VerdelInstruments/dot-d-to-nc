FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libgomp1 \
    libstdc++6 \
    libgcc-s1 \
    libc6 \
    && apt-get clean

# Set work directory
WORKDIR /var/task

# Copy files
COPY . .
COPY ./lambda_package/libbaf2sql_c.so .
COPY ./lambda_package/lambda_handler.py .
COPY ./lambda_package/lambda_runner.py .


# Install Python requirements
RUN pip install -r requirements.txt

# Default command for debugging or Lambda-style call
CMD ["python3", "lambda_handler.py"]