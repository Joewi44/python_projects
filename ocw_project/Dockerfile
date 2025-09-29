FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for geospatial packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgeos-dev \
    proj-bin \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install --no-cache-dir -e .

EXPOSE 5006
ENV IN_DOCKER=1

CMD ["python", "ocw_project/cli.py"]