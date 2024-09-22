start-redpanda:
	docker-compose -f redpandas-docker-compose.yml up -d

stop-redpanda:
	docker-compose -f redpandas-docker-compose.yml down

run-build-feature-pipeline:
	docker-compose -f feature-pipeline-docker-compose.yml up --build

run-build-backfill-pipeline:
	docker-compose -f backfill-pipeline-docker-compose.yml up --build
