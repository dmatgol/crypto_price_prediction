build:
	docker build -t trade-producer .

build-no-cache:
	docker build --no-cache -t trade-producer .

run-historical: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_TOPIC=trades_historical \
		-e LIVE_OR_HISTORICAL=historical \
		-e LAST_N_DAYS=3 \
		-e CACHE_DIR_HISTORICAL_DATA=/tmp/historical_trade_data \
		-v $(PWD)/logs:/app/logs \
		-v /tmp/historical_trade_data:/tmp/historical_trade_data \
		-p 8000:8000 \
		--name=trade-producer \
		trade-producer

run-live: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_TOPIC=trades \
		-e LIVE_OR_HISTORICAL=live \
		-v $(PWD)/logs:/app/logs \
		-p 8000:8000 \
		--name=trade-producer \
		trade-producer

run-local-historical:
	LIVE_OR_HISTORICAL=historical \
	LAST_N_DAYS=2 \
	KAFKA_TOPIC=trades_historical \
	CACHE_DIR_HISTORICAL_DATA=/tmp/historical_trade_data \
	poetry run python src/main.py

run-local-live:
	LIVE_OR_HISTORICAL=live poetry run python src/main.py
