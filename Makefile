.PHONY: help install test run docker-build docker-run docker-compose-up docker-compose-down k8s-deploy k8s-delete k8s-apply-hpa k8s-apply-ingress clean load-test

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make test              - Run tests"
	@echo "  make run               - Run the application locally"
	@echo "  make docker-build      - Build Docker image"
	@echo "  make docker-run        - Run Docker container"
	@echo "  make docker-compose-up - Start services with docker-compose"
	@echo "  make docker-compose-down - Stop docker-compose services"
	@echo "  make k8s-deploy        - Deploy to Kubernetes"
	@echo "  make k8s-apply-hpa     - Apply Horizontal Pod Autoscaler"
	@echo "  make k8s-apply-ingress - Apply Ingress configuration"
	@echo "  make k8s-delete        - Delete Kubernetes resources"
	@echo "  make load-test         - Run load test"
	@echo "  make clean            - Clean up generated files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run:
	python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t model-deployment-tutorial:latest .

docker-run:
	docker run -p 8000:8000 model-deployment-tutorial:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

k8s-deploy:
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml

k8s-apply-hpa:
	kubectl apply -f k8s/hpa.yaml

k8s-apply-ingress:
	kubectl apply -f k8s/ingress.yaml

k8s-delete:
	kubectl delete -f k8s/

load-test:
	chmod +x scripts/load_test.sh
	./scripts/load_test.sh http://localhost:8000/predict 10 100

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

