build:
	docker build -t trade-processor .

run-live: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_INPUT_TOPIC=trades \
		-e KAFKA_OUTPUT_TOPIC=tick_imbalance_bars_live \
		-e KAFKA_CONSUMER_GROUP=trade_to_tick_imbalance_ohlc_live
		-v $(PWD)/logs:/app/logs \
		--name=trade-processor \
		trade-processor

run-historical: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_INPUT_TOPIC=trades_historical \
		-e KAFKA_OUTPUT_TOPIC=tick_imbalance_bars_historical \
		-e KAFKA_CONSUMER_GROUP=trade_to_tick_imbalance_ohlc_historical
		-v $(PWD)/logs:/app/logs \
		--name=trade-processor \
		trade-processor

run-local-historical:
	KAFKA_INPUT_TOPIC=trades_historical \
	KAFKA_OUTPUT_TOPIC=tick_imbalance_bars_historical \
	KAFKA_CONSUMER_GROUP=trade_to_tick_imbalance_ohlc_historical \
	poetry run python src/processing.py

run-local-live:
	KAFKA_INPUT_TOPIC=trades \
	KAFKA_OUTPUT_TOPIC=tick_imbalance_bars_live \
	KAFKA_CONSUMER_GROUP=trade_to_tick_imbalance_ohlc_live \
	poetry run python src/processing.py
