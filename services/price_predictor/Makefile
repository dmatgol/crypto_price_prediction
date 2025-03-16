run-local-train:
	poetry shell & poetry run python src/train.py

run-local-inference:
	poetry shell & poetry run python src/predictor.py

run-local-api:
	poetry shell & poetry run uvicorn src.api:app --reload --port 80

build:
	docker build -f Dockerfile -t price-predictor ..

run-docker-train: build
	docker run \
		--env-file=.env \
		--env-file=.credentials.env \
		-e TRAIN_OR_INFERENCE=train \
		-v $(PWD)/logs:/app/logs \
		--name=price-predictor-train \
		price-predictor

run-docker-inference: build
	docker run \
		--env-file=.env \
		--env-file=.credentials.env \
		-e TRAIN_OR_INFERENCE=inference \
		-v $(PWD)/logs:/app/logs \
		-p 80:80 \
		--name=price-predictor-api \
		price-predictor
