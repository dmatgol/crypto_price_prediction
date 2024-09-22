build:
	docker build -t volume_bars-to-feature-store .

run-historical: build
	docker run \
		--network=redpanda_network \
		--env-file=.env \
		--env-file=credentials.env \
		-e BROKER_ADDRESS=redpanda:9092 \
		-e INPUT_TOPIC=volume_bars_historical \
		-e BUFFER_SIZE=40000 \
		-e LIVE_OR_HISTORICAL=historical \
		-v $(PWD)/logs:/app/logs \
		--name=volume_bars-to-feature-store \
		volume_bars-to-feature-store

run-live: build
	docker run \
		--network=redpanda_network \
		--env-file=.env \
		--env-file=credentials.env \
		-e BROKER_ADDRESS=redpanda:9092 \
		-e INPUT_TOPIC=volume_bars \
		-e BUFFER_SIZE=1 \
		-e LIVE_OR_HISTORICAL=live \
		-v $(PWD)/logs:/app/logs \
		--name=volume_bars-to-feature-store \
		volume_bars-to-feature-store

run-local-historical:
	LIVE_OR_HISTORICAL=historical \
	BUFFER_SIZE=1000 \
	INPUT_TOPIC=volume_bars_historical \
	poetry run python src/main.py

run-local-live:
	LIVE_OR_HISTORICAL=live BUFFER_SIZE=1 poetry run python src/main.py
