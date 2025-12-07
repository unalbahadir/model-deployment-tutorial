# EKS CodeBuild Deployment Checklist

## ✅ Environment Variables in CodeBuild

Make sure you have these environment variables set in your CodeBuild project:

```
ECR_REPO_REGISTRY = 448772857649.dkr.ecr.eu-central-1.amazonaws.com
APP_NAME = model-deployment-tutorial
AWS_DEFAULT_REGION = eu-central-1
DEPLOY_TO_K8S = true                              ← You just added this
EKS_CLUSTER_NAME = model-deployment-cluster      ← You just added this
```

## ✅ Prerequisites Checklist

Before running the pipeline, verify:

### 1. EKS Cluster Exists
```bash
aws eks describe-cluster --name model-deployment-cluster --region eu-central-1
```

If the cluster doesn't exist, create it:
```bash
./scripts/setup_eks_cluster.sh --cluster-name model-deployment-cluster
```

### 2. CodeBuild IAM Role Has EKS Permissions

Your CodeBuild role needs these permissions:

**Required IAM Policies:**
- `AmazonEC2ContainerRegistryPowerUser` (for ECR push/pull)
- `CloudWatchLogsFullAccess` (for logging)
- EKS permissions (see below)

**EKS Permissions** (add to CodeBuild role):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:DescribeCluster",
                "eks:ListClusters"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "eks:DescribeCluster",
            "Resource": "arn:aws:eks:eu-central-1:448772857649:cluster/model-deployment-cluster"
        }
    ]
}
```

**Or attach this managed policy** (if available):
- `AmazonEKSClusterPolicy` (read-only access)

**For kubectl to work**, CodeBuild also needs permission to call `eks:DescribeCluster` to update kubeconfig.

### 3. Kubernetes Manifests Are Ready

**Required files:**
- ✅ `k8s/configmap.yaml` - Already exists
- ✅ `k8s/deployment.yaml` - Already exists (with placeholder)
- ✅ `k8s/service.yaml` - Already exists
- ✅ `k8s/hpa.yaml` - Already exists
- ✅ `k8s/ingress.yaml` - Already exists
- ⚠️ `k8s/secrets.yaml` - **You need to create this!**

**Create secrets.yaml:**
```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml
# Edit k8s/secrets.yaml with your actual values
```

**Important:** The buildspec will try to apply secrets.yaml. If it doesn't exist, the deployment will fail.

### 4. ECR Image Exists (or will be created)

The buildspec will:
1. Build the Docker image
2. Push to ECR
3. Deploy to EKS

Make sure the ECR repository exists:
```bash
aws ecr describe-repositories --repository-names model-deployment-tutorial --region eu-central-1
```

If it doesn't exist:
```bash
aws ecr create-repository --repository-name model-deployment-tutorial --region eu-central-1
```

### 5. AWS Load Balancer Controller Installed (for Ingress)

If you haven't installed it yet, the Ingress won't create an ALB. You can either:

**Option A:** Install it manually (recommended):
```bash
# Follow instructions in EKS_DEPLOYMENT_GUIDE.md Step 3
```

**Option B:** Let the deployment continue without Ingress (it will show a warning but won't fail)

## 🚀 Testing the Pipeline

### 1. Manual Build Test

1. Go to CodeBuild Console
2. Select your project: `model-deployment-tutorial-build`
3. Click "Start build"
4. Monitor the build logs

### 2. Check Build Logs

Look for these key messages:
- ✅ "Successfully authenticated to ECR"
- ✅ "Updating kubeconfig to access EKS cluster..."
- ✅ "Applying Kubernetes manifests..."
- ✅ "Waiting for Kubernetes rollout to complete..."
- ✅ "Kubernetes deploy and rollout completed."

### 3. Verify Deployment

After successful build, check your EKS cluster:

```bash
# Update kubeconfig
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster

# Check pods
kubectl get pods -l app=model-deployment-api

# Check services
kubectl get svc model-deployment-api-service

# Check ingress (if ALB controller is installed)
kubectl get ingress model-deployment-api-ingress
```

## 🐛 Common Issues

### Issue: "Access Denied" when updating kubeconfig
**Solution:** CodeBuild role needs `eks:DescribeCluster` permission

### Issue: "secrets.yaml not found"
**Solution:** Create `k8s/secrets.yaml` from `k8s/secrets.yaml.example`

### Issue: "Cannot connect to the server"
**Solution:** Verify EKS cluster name is correct in environment variable

### Issue: Ingress not creating ALB
**Solution:** Install AWS Load Balancer Controller (see EKS_DEPLOYMENT_GUIDE.md)

### Issue: Pods stuck in "ImagePullBackOff"
**Solution:** 
- Check ECR image exists and is accessible
- Verify ECR registry URL is correct
- Check pod can pull from ECR (may need IRSA or ECR permissions)

## 📝 Quick Verification Commands

```bash
# 1. Check EKS cluster exists
aws eks list-clusters --region eu-central-1

# 2. Check CodeBuild role permissions
aws iam get-role --role-name <YOUR_CODEBUILD_ROLE_NAME>

# 3. Check ECR repository
aws ecr describe-repositories --repository-names model-deployment-tutorial --region eu-central-1

# 4. Check if secrets.yaml exists
ls -la k8s/secrets.yaml

# 5. Test kubectl access (after updating kubeconfig)
kubectl get nodes
```

## ✅ Ready to Deploy?

Once all items above are checked:

1. ✅ Environment variables set in CodeBuild
2. ✅ EKS cluster exists
3. ✅ CodeBuild role has EKS permissions
4. ✅ `k8s/secrets.yaml` exists
5. ✅ ECR repository exists
6. ✅ (Optional) AWS Load Balancer Controller installed

**You're ready!** Push a commit or manually trigger the CodeBuild to deploy to EKS.

