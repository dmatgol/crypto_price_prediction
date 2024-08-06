# crypto_price_prediction

A real-time ML system that predicts short-term crypto prices

## Installation

```sh
poetry install
```

## Usage
poetry run python -m crypto_price_prediction

## Runing Tests
poetry run pytest

## Docker
- Build the image
docker build -t crypto_price_prediction .

- Run the container
docker run -it --rm crypto_price_prediction


# TODO:
- [x] Improve configuration file validation with pydantic settings
- [x] Set up grafana and prometheus
    - [x] Run prometheus and grafana locally with docker compose
    - [x] Install prometheus python client
    - [x] Monitor trade latency
- [] Build a grafana dashboard
- [] Create a docker-compose for our trade-producer
