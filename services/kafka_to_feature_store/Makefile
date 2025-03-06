build:
	docker build -t tick-imbalance-to-feature-store .

run-historical: build
	docker run \
		--network=redpanda_network \
		--env-file=.env \
		--env-file=credentials.env \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e INPUT_TOPIC=tick_imbalance_bars_historical \
		-e BUFFER_SIZE=400 \
		-e LIVE_OR_HISTORICAL=historical \
		-v $(PWD)/logs:/app/logs \
		--name=tick-imbalance-to-feature-store \
		tick-imbalance-to-feature-store

run-live: build
	docker run \
		--network=redpanda_network \
		--env-file=.env \
		--env-file=credentials.env \
		-e BROKER_ADDRESS=redpanda:9092 \
		-e INPUT_TOPIC=tick_imbalance_bars_LIVE \
		-e BUFFER_SIZE=1 \
		-e LIVE_OR_HISTORICAL=live \
		-e CREATE_NEW_CONSUMER_GROUP=True \
		-v $(PWD)/logs:/app/logs \
		--name=tick-imbalance-to-feature-store \
		tick-imbalance-to-feature-store

run-local-historical:
	LIVE_OR_HISTORICAL=historical \
	BUFFER_SIZE=10000 \
	CREATE_NEW_CONSUMER_GROUP=True \
	INPUT_TOPIC=tick_imbalance_bars_historical \
	poetry run python src/main.py

run-local-live:
	LIVE_OR_HISTORICAL=live BUFFER_SIZE=1 poetry run python src/main.py
