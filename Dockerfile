FROM python:3.10-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.5.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy project files
COPY . /app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
