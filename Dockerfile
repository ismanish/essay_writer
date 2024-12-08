FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for the SQLite database
RUN mkdir -p /app/data

# Set environment variable for database path
ENV DB_PATH=/app/data/chat_history.db

# Expose the port the app runs on
EXPOSE 7860

CMD ["python", "app.py"]
