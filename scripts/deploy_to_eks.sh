#!/bin/bash

# Quick deployment script for EKS
# This script deploys the application to an existing EKS cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
CLUSTER_NAME="model-deployment-cluster"
REGION="eu-central-1"
ECR_REGISTRY=""
NAMESPACE="default"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --cluster-name)
      CLUSTER_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --ecr-registry)
      ECR_REGISTRY="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --cluster-name NAME     EKS cluster name (default: model-deployment-cluster)"
      echo "  --region REGION         AWS region (default: eu-central-1)"
      echo "  --ecr-registry URL      ECR registry URL (e.g., 123456789.dkr.ecr.eu-central-1.amazonaws.com)"
      echo "  --namespace NAME        Kubernetes namespace (default: default)"
      echo "  --help                  Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EKS Application Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl is not installed${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    exit 1
fi

# Update kubeconfig
echo -e "${YELLOW}Updating kubeconfig...${NC}"
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
echo -e "${GREEN}✓ kubeconfig updated${NC}"

# Verify cluster access
echo -e "${YELLOW}Verifying cluster access...${NC}"
if kubectl get nodes &> /dev/null; then
    echo -e "${GREEN}✓ Successfully connected to cluster${NC}"
else
    echo -e "${RED}✗ Failed to connect to cluster${NC}"
    exit 1
fi

# Get ECR registry if not provided
if [ -z "$ECR_REGISTRY" ]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
    echo -e "${YELLOW}Using ECR registry: $ECR_REGISTRY${NC}"
fi

# Create namespace if it doesn't exist
if [ "$NAMESPACE" != "default" ]; then
    echo -e "${YELLOW}Creating namespace: $NAMESPACE${NC}"
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    kubectl config set-context --current --namespace=$NAMESPACE
fi

# Update deployment.yaml with ECR registry
echo -e "${YELLOW}Updating deployment.yaml with ECR registry...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Backup original deployment.yaml
cp "$PROJECT_ROOT/k8s/deployment.yaml" "$PROJECT_ROOT/k8s/deployment.yaml.bak"

# Replace ECR registry placeholder
sed -i.bak "s|<YOUR_ECR_REGISTRY>|$ECR_REGISTRY|g" "$PROJECT_ROOT/k8s/deployment.yaml"
echo -e "${GREEN}✓ deployment.yaml updated${NC}"

# Deploy ConfigMap
echo ""
echo -e "${YELLOW}Deploying ConfigMap...${NC}"
kubectl apply -f "$PROJECT_ROOT/k8s/configmap.yaml"
echo -e "${GREEN}✓ ConfigMap deployed${NC}"

# Deploy Secrets (check if it exists)
if [ -f "$PROJECT_ROOT/k8s/secrets.yaml" ]; then
    echo -e "${YELLOW}Deploying Secrets...${NC}"
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml"
    echo -e "${GREEN}✓ Secrets deployed${NC}"
else
    echo -e "${YELLOW}Warning: secrets.yaml not found. Using secrets.yaml.example as template.${NC}"
    echo "Please create k8s/secrets.yaml from k8s/secrets.yaml.example"
fi

# Deploy Deployment
echo -e "${YELLOW}Deploying Application...${NC}"
kubectl apply -f "$PROJECT_ROOT/k8s/deployment.yaml"
echo -e "${GREEN}✓ Deployment created${NC}"

# Deploy Service
echo -e "${YELLOW}Deploying Service...${NC}"
kubectl apply -f "$PROJECT_ROOT/k8s/service.yaml"
echo -e "${GREEN}✓ Service created${NC}"

# Deploy HPA
echo -e "${YELLOW}Deploying HPA...${NC}"
kubectl apply -f "$PROJECT_ROOT/k8s/hpa.yaml" || echo -e "${YELLOW}HPA may already exist${NC}"
echo -e "${GREEN}✓ HPA deployed${NC}"

# Deploy Ingress
echo -e "${YELLOW}Deploying Ingress...${NC}"
kubectl apply -f "$PROJECT_ROOT/k8s/ingress.yaml" || echo -e "${YELLOW}Ingress may already exist${NC}"
echo -e "${GREEN}✓ Ingress deployed${NC}"

# Wait for rollout
echo ""
echo -e "${YELLOW}Waiting for deployment rollout...${NC}"
kubectl rollout status deployment/model-deployment-api --timeout=5m
echo -e "${GREEN}✓ Deployment rollout complete${NC}"

# Show status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "Application Status:"
kubectl get pods -l app=model-deployment-api
echo ""
kubectl get svc model-deployment-api-service
echo ""
kubectl get hpa model-deployment-api-hpa
echo ""

# Get Ingress URL
INGRESS_HOST=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
if [ -n "$INGRESS_HOST" ]; then
    echo -e "${GREEN}Ingress URL: http://$INGRESS_HOST${NC}"
    echo ""
    echo "Test the API:"
    echo "  curl http://$INGRESS_HOST/health"
else
    echo -e "${YELLOW}Ingress is still being created. Check with:${NC}"
    echo "  kubectl get ingress model-deployment-api-ingress"
    echo ""
    echo "Once created, get the URL with:"
    echo "  kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
fi

echo ""
echo "Useful commands:"
echo "  kubectl get pods,svc,ingress,hpa"
echo "  kubectl logs -f deployment/model-deployment-api"
echo "  kubectl describe deployment model-deployment-api"

