FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y \
    libgomp \
    libstdc++ \
    libgcc \
    && yum clean all

# Set work directory
WORKDIR /var/task

# Copy files
COPY requirements.txt .

# Install Python requirements
RUN pip3 install -r ./requirements.txt --target .

COPY src/ .
COPY 250702_davaoH2O_021.d /input_data/

## Default command for debugging or Lambda-style call
CMD ["handler.lambda_handler"]

# Default command for debugging or Lambda-style call
#CMD ["python3", "handler.lambda_handler.py"]