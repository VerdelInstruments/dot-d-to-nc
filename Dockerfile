FROM ubuntu:22.04

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
COPY requirements.txt .

# Install Python requirements
RUN pip3 install -r ./requirements.txt --target .

# Install boto3 for S3 operations
RUN pip3 install boto3 --target .

COPY src/ .
COPY extract_s3.py .

CMD ["python3", "extract.py"]
