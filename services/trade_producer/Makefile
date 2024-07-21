build:
	docker build -t trade-producer .

run-debug: build
	docker run --network=redpanda_network trade-producer
