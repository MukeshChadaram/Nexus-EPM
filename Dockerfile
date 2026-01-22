# nexus-epm/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /usr/src/app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a place for the dbt profiles
RUN mkdir -p /root/.dbt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8502

# Default command: keeps container running so we can exec into it
CMD ["tail", "-f", "/dev/null"]