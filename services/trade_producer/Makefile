build:
	docker build -t trade-producer .

build-no-cache:
	docker build --no-cache -t trade-producer .

run: build
	docker run \
		--network=redpanda_network \
		-e KAFKA_BROKER_ADDRESS=redpanda:9092 \
		-e KAFKA_TOPIC=trade \
		-v $(PWD)/logs:/app/logs \
		-p 8000:8000 \
		trade-producer

run-local:
	poetry run python src/main.py
