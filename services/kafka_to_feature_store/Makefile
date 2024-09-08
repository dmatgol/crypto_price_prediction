build:
	docker build -t volume_bars-to-feature-store .

run: build
	docker run \
		--network=redpanda_network \
		--env-file=.env \
		-e BROKER_ADDRESS=redpanda:9092 \
		-e INPUT_TOPIC=volume_bars \
		-v $(PWD)/logs:/app/logs \
		--name=volume_bars-to-feature-store \
		volume_bars-to-feature-store

run-local:
	poetry run python src/main.py
