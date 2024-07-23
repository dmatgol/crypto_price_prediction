build:
	docker build -t trade-producer .

build-no-cache:
	docker build --no-cache -t trade-producer .

run-debug: build
	docker run --network=redpanda_network trade-producer

run-local:
	python src/main.py
