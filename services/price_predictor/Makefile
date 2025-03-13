run-local-train:
	poetry shell & poetry run python src/train.py

run-local-inference:
	poetry shell & poetry run python src/predictor.py

run-local-api:
	poetry shell & poetry run uvicorn src.api:app --reload --port 8001
