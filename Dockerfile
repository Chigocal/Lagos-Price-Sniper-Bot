# Use the standard Python lightweight image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your requirements file first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Create the data directory
RUN mkdir -p data

# Run your exact start command
CMD python -m http.server $PORT & PYTHONPATH=. python src/main.py