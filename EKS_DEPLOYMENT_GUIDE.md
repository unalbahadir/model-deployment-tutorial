# Amazon EKS Deployment Guide

This guide walks you through deploying the model deployment tutorial to Amazon EKS (Elastic Kubernetes Service).

## 📋 Prerequisites

- ✅ AWS Account with appropriate permissions
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ `kubectl` installed ([installation guide](https://kubernetes.io/docs/tasks/tools/))
- ✅ `eksctl` installed ([installation guide](https://eksctl.io/introduction/installation/))
- ✅ Docker installed (for building images)
- ✅ ECR repository created (already done: `model-deployment-tutorial`)
- ✅ GitHub repository with code pushed

## 🏗️ Architecture Overview

```
GitHub Repo
    ↓ (Webhook)
AWS CodePipeline
    ↓
AWS CodeBuild
    ↓
Amazon ECR (Docker Registry)
    ↓
Amazon EKS Cluster
    ├── Deployment (3 replicas)
    ├── Service (ClusterIP)
    ├── Ingress (ALB)
    └── HPA (Auto-scaling)
```

## 📝 Step-by-Step Deployment

### Step 1: Create EKS Cluster

#### Option A: Using eksctl (Recommended)

1. **Create cluster configuration file** (`eks-cluster-config.yaml`):

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: model-deployment-cluster
  region: eu-central-1
  version: "1.28"

iam:
  withOIDC: true  # Required for IRSA (IAM Roles for Service Accounts)

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: HighlyAvailable

nodeGroups:
  - name: ng-1
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 2
    maxSize: 5
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
      k8s.io/cluster-autoscaler/model-deployment-cluster: "owned"

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver
```

2. **Create the cluster**:

```bash
eksctl create cluster -f eks-cluster-config.yaml
```

This will take 15-20 minutes. The command will:
- Create VPC, subnets, and networking
- Create EKS control plane
- Create node groups
- Configure kubectl automatically
- Set up OIDC provider for IRSA

#### Option B: Using AWS Console

1. Go to **EKS Console** → **Clusters** → **Create cluster**
2. Configure:
   - **Name**: `model-deployment-cluster`
   - **Kubernetes version**: 1.28 or latest
   - **Cluster service role**: Create new or use existing
   - **VPC**: Create new or use existing
   - **Subnets**: Select at least 2 subnets in different AZs
   - **Security groups**: Default or custom
   - **Enable logging**: CloudWatch (optional but recommended)
3. Click **Create**
4. After cluster is created, add **Node Group**:
   - **Node group name**: `ng-1`
   - **Node IAM role**: Create new with required policies
   - **Instance type**: `t3.medium`
   - **Desired capacity**: 2
   - **Min size**: 2
   - **Max size**: 5
   - **Disk size**: 20 GB

#### Option C: Using Terraform/CloudFormation

See AWS documentation for infrastructure-as-code options.

---

### Step 2: Configure kubectl

If using `eksctl`, kubectl is automatically configured. Otherwise:

```bash
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster
```

**Verify connection**:

```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

---

### Step 3: Install AWS Load Balancer Controller

The AWS Load Balancer Controller is required for the Ingress resource to create ALB.

1. **Create IAM policy**:

```bash
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json
```

2. **Create IAM role and service account** (using eksctl):

```bash
eksctl create iamserviceaccount \
  --cluster=model-deployment-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::<YOUR_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve
```

3. **Install AWS Load Balancer Controller using Helm**:

```bash
# Add EKS Helm chart repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Install controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=model-deployment-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

4. **Verify installation**:

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
```

---

### Step 4: Install Cluster Autoscaler (Optional but Recommended)

For automatic node scaling:

1. **Create IAM policy**:

```bash
cat > cluster-autoscaler-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeScalingActivities",
                "autoscaling:DescribeTags",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeLaunchTemplateVersions"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "ec2:DescribeImages",
                "ec2:GetInstanceTypesFromInstanceRequirements",
                "eks:DescribeNodegroup"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name ClusterAutoscalerPolicy \
    --policy-document file://cluster-autoscaler-policy.json
```

2. **Create service account**:

```bash
eksctl create iamserviceaccount \
  --cluster=model-deployment-cluster \
  --namespace=kube-system \
  --name=cluster-autoscaler \
  --attach-policy-arn=arn:aws:iam::<YOUR_ACCOUNT_ID>:policy/ClusterAutoscalerPolicy \
  --override-existing-serviceaccounts \
  --approve
```

3. **Install Cluster Autoscaler**:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Edit the deployment to add cluster name
kubectl -n kube-system annotate deployment.apps/cluster-autoscaler \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"

kubectl -n kube-system set env deployment.apps/cluster-autoscaler \
  -c cluster-autoscaler \
  AWS_REGION=eu-central-1 \
  CLUSTER_NAME=model-deployment-cluster
```

---

### Step 5: Set Up IAM Roles for Service Accounts (IRSA)

For secure AWS access from pods (recommended over access keys):

1. **Create IAM policy for application**:

```bash
cat > app-iam-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:eu-central-1:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetDatabase",
                "glue:GetTable"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy \
    --policy-name ModelDeploymentAppPolicy \
    --policy-document file://app-iam-policy.json
```

2. **Create service account with IAM role**:

```bash
eksctl create iamserviceaccount \
  --cluster=model-deployment-cluster \
  --namespace=default \
  --name=model-deployment-sa \
  --attach-policy-arn=arn:aws:iam::<YOUR_ACCOUNT_ID>:policy/ModelDeploymentAppPolicy \
  --override-existing-serviceaccounts \
  --approve
```

3. **Update deployment.yaml** to use the service account (see Step 6).

---

### Step 6: Prepare Kubernetes Manifests

1. **Update `k8s/deployment.yaml`**:

The deployment.yaml is already configured with the ECR registry:
```yaml
image: 448772857649.dkr.ecr.eu-central-1.amazonaws.com/model-deployment-tutorial:latest
```

**Note:** The buildspec.yaml will automatically update this image tag during CI/CD with the build number (e.g., `:123`), but for manual deployments, the `:latest` tag will be used.

2. **Add service account to deployment** (if using IRSA):

Add to `k8s/deployment.yaml` in the `spec.template.spec` section:

```yaml
serviceAccountName: model-deployment-sa
```

3. **Update `k8s/secrets.yaml`**:

Copy from example and update with your values:

```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml
# Edit k8s/secrets.yaml with your actual values
```

**Note**: If using IRSA, you can remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from secrets.

4. **Update `k8s/ingress.yaml`**:

- Update the hostname: `model-deployment-api.example.com` → your domain
- (Optional) Add SSL certificate ARN for HTTPS

---

### Step 7: Deploy Application

1. **Create namespace** (optional, using default):

```bash
# Or create a dedicated namespace
kubectl create namespace model-deployment
kubectl config set-context --current --namespace=model-deployment
```

2. **Deploy ConfigMap**:

```bash
kubectl apply -f k8s/configmap.yaml
```

3. **Deploy Secrets**:

```bash
kubectl apply -f k8s/secrets.yaml
```

4. **Deploy Application**:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

5. **Deploy HPA** (Horizontal Pod Autoscaler):

```bash
kubectl apply -f k8s/hpa.yaml
```

6. **Deploy Ingress** (for external access):

```bash
kubectl apply -f k8s/ingress.yaml
```

---

### Step 8: Verify Deployment

1. **Check pods**:

```bash
kubectl get pods
kubectl get pods -o wide
kubectl describe pod <pod-name>  # If issues
```

2. **Check services**:

```bash
kubectl get svc
```

3. **Check ingress**:

```bash
kubectl get ingress
kubectl describe ingress model-deployment-api-ingress
```

Wait for the ALB to be created (2-3 minutes), then get the ALB URL:

```bash
kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

4. **Check HPA**:

```bash
kubectl get hpa
```

5. **Test the API**:

```bash
# Get ALB URL
ALB_URL=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health check
curl http://$ALB_URL/health

# Or if using port-forward for testing
kubectl port-forward svc/model-deployment-api-service 8000:80
curl http://localhost:8000/health
```

---

### Step 9: Configure CI/CD (CodeBuild/CodePipeline)

1. **Update CodeBuild environment variables**:

Go to CodeBuild → Your project → Edit → Environment → Additional configuration:

```
ECR_REPO_REGISTRY = 448772857649.dkr.ecr.eu-central-1.amazonaws.com
APP_NAME = model-deployment-tutorial
AWS_DEFAULT_REGION = eu-central-1
DEPLOY_TO_K8S = true
EKS_CLUSTER_NAME = model-deployment-cluster
```

**✅ These values are already configured in your CodeBuild project!**

2. **Update CodeBuild IAM role**:

Add these policies to your CodeBuild role:
- `AmazonEKSClusterPolicy` (or custom policy with EKS permissions)
- `AmazonEKSWorkerNodePolicy` (if needed)
- `AmazonEC2ContainerRegistryPowerUser` (for ECR)

3. **Update buildspec.yaml**:

The buildspec.yaml already includes Kubernetes deployment. It will:
- Update kubeconfig
- Apply all Kubernetes manifests
- Wait for rollout

4. **Test the pipeline**:

Push a commit to trigger the pipeline, or manually start a build.

---

## 🔧 Advanced Configuration

### Custom Domain with SSL

1. **Request ACM certificate**:

```bash
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS \
  --region eu-central-1
```

2. **Validate certificate** (add DNS records)

3. **Update ingress.yaml**:

```yaml
annotations:
  alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:eu-central-1:ACCOUNT:certificate/CERT_ID
```

4. **Update host in ingress.yaml**:

```yaml
rules:
- host: api.yourdomain.com
```

### Monitoring with Prometheus and Grafana

1. Install Prometheus Operator
2. Configure ServiceMonitor for your application
3. Set up Grafana dashboards

### Log Aggregation

- Use CloudWatch Container Insights
- Or deploy Fluent Bit for log aggregation

---

## 🔐 Security Best Practices

1. ✅ **Use IRSA** instead of access keys in secrets
2. ✅ **Enable Pod Security Standards** (Pod Security Admission)
3. ✅ **Use Network Policies** to restrict pod-to-pod communication
4. ✅ **Enable encryption at rest** for EBS volumes
5. ✅ **Use Secrets Manager** or External Secrets Operator
6. ✅ **Enable audit logging** for EKS cluster
7. ✅ **Regularly update** Kubernetes and node AMIs
8. ✅ **Use least privilege** IAM policies

---

## 🐛 Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Check if image exists in ECR
aws ecr describe-images --repository-name model-deployment-tutorial --region eu-central-1
```

### Ingress not creating ALB

```bash
# Check AWS Load Balancer Controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check ingress events
kubectl describe ingress model-deployment-api-ingress

# Verify controller is running
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### HPA not scaling

```bash
# Check HPA status
kubectl describe hpa model-deployment-api-hpa

# Check metrics server
kubectl top nodes
kubectl top pods

# Verify metrics server is installed
kubectl get deployment metrics-server -n kube-system
```

### Cannot connect to cluster

```bash
# Update kubeconfig
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster

# Verify IAM permissions
aws eks describe-cluster --name model-deployment-cluster --region eu-central-1
```

### CodeBuild deployment fails

- Verify CodeBuild role has EKS permissions
- Check EKS cluster name is correct
- Verify kubectl is available in CodeBuild (it is, via buildspec)
- Check CloudWatch logs for CodeBuild

---

## 📊 Monitoring

### CloudWatch Container Insights

Enable Container Insights for EKS:

```bash
aws eks update-cluster-config \
  --name model-deployment-cluster \
  --logging '{"enable":[{"types":["api","audit","authenticator","controllerManager","scheduler"]}]}' \
  --region eu-central-1
```

### View Logs

```bash
# Pod logs
kubectl logs -f deployment/model-deployment-api

# All pods in namespace
kubectl logs -f -l app=model-deployment-api

# Previous container (if crashed)
kubectl logs -f deployment/model-deployment-api --previous
```

### Metrics

```bash
# Node metrics
kubectl top nodes

# Pod metrics
kubectl top pods

# HPA metrics
kubectl get hpa
```

---

## 🚀 Quick Reference Commands

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes

# Application
kubectl get pods,svc,ingress,hpa
kubectl logs -f deployment/model-deployment-api
kubectl describe deployment model-deployment-api

# Scaling
kubectl scale deployment model-deployment-api --replicas=5
kubectl autoscale deployment model-deployment-api --min=2 --max=10 --cpu-percent=70

# Updates
kubectl set image deployment/model-deployment-api api=<NEW_IMAGE>
kubectl rollout status deployment/model-deployment-api
kubectl rollout undo deployment/model-deployment-api

# Debugging
kubectl exec -it <pod-name> -- /bin/bash
kubectl port-forward svc/model-deployment-api-service 8000:80
```

---

## 📚 Additional Resources

- [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)
- [eksctl Documentation](https://eksctl.io/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

---

## ✅ Deployment Checklist

- [ ] EKS cluster created
- [ ] kubectl configured
- [ ] AWS Load Balancer Controller installed
- [ ] Cluster Autoscaler installed (optional)
- [ ] IRSA configured for application (optional but recommended)
- [ ] ECR image pushed
- [ ] Kubernetes manifests updated (ECR registry, secrets, etc.)
- [ ] ConfigMap deployed
- [ ] Secrets deployed
- [ ] Deployment deployed
- [ ] Service deployed
- [ ] HPA deployed
- [ ] Ingress deployed
- [ ] ALB created and accessible
- [ ] Application responding to requests
- [ ] CI/CD pipeline configured
- [ ] Monitoring and logging configured

---

## 🎯 Next Steps

1. **Set up monitoring** with CloudWatch Container Insights
2. **Configure alerts** for pod failures, high CPU, etc.
3. **Set up backup** for persistent data (if any)
4. **Implement blue-green deployments** for zero-downtime updates
5. **Set up network policies** for security
6. **Configure resource quotas** and limits
7. **Set up GitOps** with ArgoCD or Flux

Your application is now running on Amazon EKS! 🚀

