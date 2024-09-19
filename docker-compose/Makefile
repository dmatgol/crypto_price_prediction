start-redpanda:
	docker-compose -f redpandas-docker-compose.yml up -d

stop-redpanda:
	docker-compose -f redpandas-docker-compose.yml down

build-feature-pipeline:
	docker-compose -f feature-pipeline-docker-compose.yml up --build

build-backfill-pipeline:
	docker-compose -f backfill-pipeline-docker-compose.yml up --build
