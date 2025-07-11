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
#COPY src/libbaf2sql_c.so .
#COPY src/lambda_handler.py .
#COPY src/lambda_runner.py .

# Install Python requirements
RUN pip install -r requirements.txt

CMD ["python3", "./src/lambda_handler.py"]