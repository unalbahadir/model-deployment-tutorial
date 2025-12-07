#!/bin/bash

# EKS Cluster Setup Script
# This script creates an EKS cluster with all necessary components for the model deployment tutorial

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
CLUSTER_NAME="model-deployment-cluster"
REGION="eu-central-1"
NODE_TYPE="t3.medium"
NODE_MIN=2
NODE_MAX=5
NODE_DESIRED=2
K8S_VERSION="1.28"

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
    --node-type)
      NODE_TYPE="$2"
      shift 2
      ;;
    --node-min)
      NODE_MIN="$2"
      shift 2
      ;;
    --node-max)
      NODE_MAX="$2"
      shift 2
      ;;
    --node-desired)
      NODE_DESIRED="$2"
      shift 2
      ;;
    --k8s-version)
      K8S_VERSION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --cluster-name NAME     Cluster name (default: model-deployment-cluster)"
      echo "  --region REGION         AWS region (default: eu-central-1)"
      echo "  --node-type TYPE        EC2 instance type (default: t3.medium)"
      echo "  --node-min N            Minimum nodes (default: 2)"
      echo "  --node-max N            Maximum nodes (default: 5)"
      echo "  --node-desired N        Desired nodes (default: 2)"
      echo "  --k8s-version VERSION   Kubernetes version (default: 1.28)"
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
echo -e "${GREEN}EKS Cluster Setup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Configuration:"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  Region: $REGION"
echo "  Kubernetes Version: $K8S_VERSION"
echo "  Node Type: $NODE_TYPE"
echo "  Node Count: Min=$NODE_MIN, Desired=$NODE_DESIRED, Max=$NODE_MAX"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v eksctl &> /dev/null; then
    echo -e "${RED}ERROR: eksctl is not installed${NC}"
    echo "Install it from: https://eksctl.io/introduction/installation/"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl is not installed${NC}"
    echo "Install it from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Using AWS Account: $ACCOUNT_ID${NC}"
echo ""

# Create cluster configuration file
echo -e "${YELLOW}Creating cluster configuration...${NC}"
cat > /tmp/eks-cluster-config.yaml <<EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${CLUSTER_NAME}
  region: ${REGION}
  version: "${K8S_VERSION}"

iam:
  withOIDC: true

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: HighlyAvailable

nodeGroups:
  - name: ng-1
    instanceType: ${NODE_TYPE}
    desiredCapacity: ${NODE_DESIRED}
    minSize: ${NODE_MIN}
    maxSize: ${NODE_MAX}
    volumeSize: 20
    ssh:
      allow: false
    iam:
      withAddonPolicies:
        imageBuilder: true
        autoScaler: true
        awsLoadBalancerController: true
        cloudWatch: true
    labels:
      role: worker
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/${CLUSTER_NAME}: "owned"

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver
EOF

echo -e "${GREEN}✓ Cluster configuration created${NC}"
echo ""

# Create the cluster
echo -e "${YELLOW}Creating EKS cluster (this will take 15-20 minutes)...${NC}"
echo -e "${YELLOW}You can monitor progress in another terminal with:${NC}"
echo -e "${YELLOW}  aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query cluster.status${NC}"
echo ""

if eksctl create cluster -f /tmp/eks-cluster-config.yaml; then
    echo -e "${GREEN}✓ Cluster created successfully!${NC}"
else
    echo -e "${RED}✗ Cluster creation failed${NC}"
    exit 1
fi

# Update kubeconfig
echo ""
echo -e "${YELLOW}Updating kubeconfig...${NC}"
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
echo -e "${GREEN}✓ kubeconfig updated${NC}"

# Verify cluster access
echo ""
echo -e "${YELLOW}Verifying cluster access...${NC}"
if kubectl get nodes; then
    echo -e "${GREEN}✓ Successfully connected to cluster${NC}"
else
    echo -e "${RED}✗ Failed to connect to cluster${NC}"
    exit 1
fi

# Install AWS Load Balancer Controller
echo ""
echo -e "${YELLOW}Installing AWS Load Balancer Controller...${NC}"

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}Helm not found. Installing Helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# Create IAM policy for Load Balancer Controller
echo "Creating IAM policy for Load Balancer Controller..."
curl -o /tmp/iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not download IAM policy. You may need to create it manually.${NC}"
}

if [ -f /tmp/iam_policy.json ]; then
    POLICY_ARN=$(aws iam create-policy \
        --policy-name AWSLoadBalancerControllerIAMPolicy-${CLUSTER_NAME} \
        --policy-document file:///tmp/iam_policy.json \
        --query 'Policy.Arn' --output text 2>/dev/null || \
        aws iam list-policies --query "Policies[?PolicyName=='AWSLoadBalancerControllerIAMPolicy-${CLUSTER_NAME}'].Arn" --output text)
    
    if [ -n "$POLICY_ARN" ] && [ "$POLICY_ARN" != "None" ]; then
        echo -e "${GREEN}✓ IAM policy created/found: $POLICY_ARN${NC}"
        
        # Create service account
        eksctl create iamserviceaccount \
          --cluster=${CLUSTER_NAME} \
          --namespace=kube-system \
          --name=aws-load-balancer-controller \
          --attach-policy-arn=${POLICY_ARN} \
          --override-existing-serviceaccounts \
          --approve || echo -e "${YELLOW}Service account may already exist${NC}"
        
        # Install controller
        helm repo add eks https://aws.github.io/eks-charts
        helm repo update
        
        helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
          -n kube-system \
          --set clusterName=${CLUSTER_NAME} \
          --set serviceAccount.create=false \
          --set serviceAccount.name=aws-load-balancer-controller || \
          echo -e "${YELLOW}Controller may already be installed${NC}"
        
        echo -e "${GREEN}✓ AWS Load Balancer Controller installed${NC}"
    else
        echo -e "${YELLOW}Warning: Could not create/find IAM policy. Install Load Balancer Controller manually.${NC}"
    fi
fi

# Install Metrics Server (required for HPA)
echo ""
echo -e "${YELLOW}Installing Metrics Server (required for HPA)...${NC}"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml 2>/dev/null || \
    echo -e "${YELLOW}Metrics Server may already be installed${NC}"
echo -e "${GREEN}✓ Metrics Server installed${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Cluster Information:"
echo "  Name: $CLUSTER_NAME"
echo "  Region: $REGION"
echo "  Kubernetes Version: $K8S_VERSION"
echo ""
echo "Next Steps:"
echo "  1. Update k8s/deployment.yaml with your ECR registry:"
echo "     sed -i 's|<YOUR_ECR_REGISTRY>|${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com|g' k8s/deployment.yaml"
echo ""
echo "  2. Update k8s/secrets.yaml with your AWS credentials:"
echo "     cp k8s/secrets.yaml.example k8s/secrets.yaml"
echo "     # Edit k8s/secrets.yaml with your values"
echo ""
echo "  3. Deploy the application:"
echo "     kubectl apply -f k8s/configmap.yaml"
echo "     kubectl apply -f k8s/secrets.yaml"
echo "     kubectl apply -f k8s/deployment.yaml"
echo "     kubectl apply -f k8s/service.yaml"
echo "     kubectl apply -f k8s/hpa.yaml"
echo "     kubectl apply -f k8s/ingress.yaml"
echo ""
echo "  4. Check deployment status:"
echo "     kubectl get pods,svc,ingress,hpa"
echo ""
echo "  5. Get ALB URL (after ingress is created):"
echo "     kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
echo ""
echo "For detailed instructions, see: EKS_DEPLOYMENT_GUIDE.md"
echo ""

# Cleanup
rm -f /tmp/eks-cluster-config.yaml
rm -f /tmp/iam_policy.json

