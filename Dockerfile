FROM python:3.7-slim

WORKDIR /src

RUN apt-get update \
    && apt-get install -y build-essential python3-dev libblas3 liblapack3 liblapack-dev libblas-dev gfortran

# Create 3.7-python virtualenv 
RUN pip install --upgrade pip \
    && pip install poetry

# Copy source code
COPY . /src

# Install dependencies
RUN poetry config settings.virtualenvs.create false
RUN poetry install --no-interaction --no-dev

CMD poetry run streamlit run --server.enableCORS false --server.port $PORT app.py
