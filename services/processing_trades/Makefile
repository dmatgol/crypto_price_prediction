build:
	docker build -t trade-processor .

run: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_INPUT_TOPIC=trades \
		-e KAFKA_OUTPUT_TOPIC=volume_bars \
		-v $(PWD)/logs:/app/logs \
		--name=trade-processor \
		trade-processor

run-local:
	poetry run python src/processing.py
