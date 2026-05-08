# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# (Make sure you have a requirements.txt with slack_bolt, sqlalchemy, psycopg2-binary, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's code into the container
COPY . .

# Command to run when the container starts
CMD ["python", "bot.py"]