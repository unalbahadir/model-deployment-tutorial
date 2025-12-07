# AWS Deployment Guide - GitHub + CodeBuild + CodePipeline + ECR

This guide walks you through deploying the model deployment tutorial to AWS using GitHub, AWS CodeBuild, AWS CodePipeline, and Amazon ECR.

## 📋 Prerequisites

- ✅ AWS Account with appropriate permissions
- ✅ GitHub repository (public or private)
- ✅ AWS CLI configured (`aws configure`)
- ✅ Docker installed and working
- ✅ ECR repository created (already done: `model-deployment-tutorial`)

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
Amazon ECS / EKS / EC2 (Your choice)
```

## 📝 Step-by-Step Setup

### Step 1: Prepare GitHub Repository

1. **Push your code to GitHub:**
```bash
# If not already done
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

2. **Get your GitHub repository URL:**
   - Note: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`

---

### Step 2: Create GitHub Personal Access Token

GitHub requires a Personal Access Token for CodePipeline to access your repository.

1. **Go to GitHub Settings:**
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Create new token:**
   - Click "Generate new token (classic)"
   - Name: `AWS-CodePipeline-Access`
   - Expiration: Choose appropriate (e.g., 90 days)
   - Scopes: Select `repo` (full control of private repositories)
   - Click "Generate token"

3. **Copy the token immediately** (you won't see it again!)
   - Save it securely - you'll need it for CodePipeline

---

### Step 3: Create IAM Role for CodeBuild

CodeBuild needs permissions to push to ECR and deploy to your infrastructure.

1. **Go to IAM Console:**
   - AWS Console → IAM → Roles → Create role

2. **Select trusted entity:**
   - Trusted entity type: AWS service
   - Use case: CodeBuild
   - Click Next

3. **Attach policies:**
   - `AmazonEC2ContainerRegistryPowerUser` (for ECR push/pull)
   - `CloudWatchLogsFullAccess` (for logging)
   - If deploying to EKS: `AmazonEKSClusterPolicy` (or create custom policy)
   - If deploying to ECS: `AmazonECS_FullAccess`
   - Click Next

4. **Name the role:**
   - Role name: `CodeBuild-ModelDeployment-Role`
   - Description: "Role for CodeBuild to deploy model deployment tutorial"
   - Click Create role

5. **Note the Role ARN** (you'll need it later)

---

### Step 4: Create CodeBuild Project

1. **Go to CodeBuild Console:**
   - AWS Console → CodeBuild → Build projects → Create build project

2. **Project configuration:**
   - **Project name**: `model-deployment-tutorial-build`
   - **Description**: "Build and push Docker image to ECR"

3. **Source:**
   - Source provider: GitHub
   - Connection: Create new connection (if first time)
     - Click "Connect to GitHub"
     - Authorize AWS to access GitHub
     - Select your repository
   - Repository: Select your GitHub repository
   - Branch: `main` (or your default branch)

4. **Environment:**
   - Environment image: Managed image
   - Operating system: Amazon Linux 2
   - Runtime(s): Standard
   - Image: `aws/codebuild/standard:7.0` (or latest)
   - Image version: Always use the latest
   - Environment type: Linux
   - Compute: 
     - Compute type: `BUILD_GENERAL1_SMALL` (or larger if needed)
   - Service role: Select `CodeBuild-ModelDeployment-Role` (created in Step 3)

5. **Buildspec:**
   - Buildspec name: `buildspec.yaml` (already in your repo)
   - Or use inline buildspec (see below)

6. **Artifacts:**
   - Type: No artifact (we're pushing to ECR directly)

7. **Logs:**
   - CloudWatch Logs: Enabled
   - Group name: `/aws/codebuild/model-deployment-tutorial`
   - Stream name: `build-logs`

8. **Click Create build project**

---

### Step 5: Configure Environment Variables in CodeBuild

1. **Go to your CodeBuild project:**
   - CodeBuild → Build projects → `model-deployment-tutorial-build` → Edit

2. **Go to Environment → Additional configuration:**

3. **Add environment variables:**
   ```
   ECR_REPO_REGISTRY = 448772857649.dkr.ecr.eu-central-1.amazonaws.com
   APP_NAME = model-deployment-tutorial
   AWS_DEFAULT_REGION = eu-central-1
   DEPLOY_TO_K8S = false  # Set to true if deploying to Kubernetes
   EKS_CLUSTER_NAME = model-deployment-cluster  # Only if DEPLOY_TO_K8S=true
   ```

4. **Save changes**

---

### Step 6: Create CodePipeline

1. **Go to CodePipeline Console:**
   - AWS Console → CodePipeline → Pipelines → Create pipeline

2. **Pipeline settings:**
   - Pipeline name: `model-deployment-tutorial-pipeline`
   - Service role: Create new service role (or use existing)
   - Role name: `CodePipeline-ModelDeployment-Role`
   - Artifact store: Default location (or custom S3 bucket)
   - Click Next

3. **Source stage:**
   - Source provider: GitHub (Version 2)
   - Connection: Select the connection created in Step 4
   - Repository name: Select your repository
   - Branch name: `main`
   - Output artifact format: CodePipeline default
   - Click Next

4. **Build stage:**
   - Build provider: AWS CodeBuild
   - Project name: `model-deployment-tutorial-build` (created in Step 4)
   - Build type: Single build
   - Output artifacts: Leave default
   - Click Next

5. **Deploy stage (Optional):**
   - You can add deployment stages here:
     - **ECS**: Deploy to ECS service
     - **EKS**: Deploy to Kubernetes (using kubectl)
     - **CloudFormation**: Deploy infrastructure
   - For now, you can skip this and deploy manually
   - Click Skip deploy stage (or add your deployment)

6. **Review and create:**
   - Review all settings
   - Click Create pipeline

---

### Step 7: Test the Pipeline

1. **Trigger the pipeline:**
   - CodePipeline will automatically start on first creation
   - Or manually: Pipeline → Release change

2. **Monitor the build:**
   - Watch the pipeline progress in CodePipeline console
   - Check CodeBuild logs if there are errors

3. **Verify ECR:**
   - Go to ECR → `model-deployment-tutorial` repository
   - You should see your Docker image with tags: `latest` and build number

---

## 🔧 Advanced Configuration

### Option A: Deploy to Amazon ECS

1. **Create ECS Cluster:**
```bash
aws ecs create-cluster --cluster-name model-deployment-cluster --region eu-central-1
```

2. **Create ECS Task Definition:**
   - Use the ECR image: `448772857649.dkr.ecr.eu-central-1.amazonaws.com/model-deployment-tutorial:latest`
   - Configure CPU, memory, ports, environment variables

3. **Add Deploy Stage to CodePipeline:**
   - Deploy provider: Amazon ECS
   - Cluster name: `model-deployment-cluster`
   - Service name: `model-deployment-service`
   - Image filename: `imagedefinitions.json` (CodeBuild creates this)

### Option B: Deploy to Amazon EKS

**📘 For detailed EKS deployment instructions, see [EKS_DEPLOYMENT_GUIDE.md](./EKS_DEPLOYMENT_GUIDE.md)**

Quick setup:

1. **Create EKS cluster** (using the setup script):
   ```bash
   ./scripts/setup_eks_cluster.sh --cluster-name model-deployment-cluster
   ```

2. **Deploy application** (using the deployment script):
   ```bash
   ./scripts/deploy_to_eks.sh --cluster-name model-deployment-cluster
   ```

3. **Or configure CI/CD:**
   - Update CodeBuild environment variables:
     - `DEPLOY_TO_K8S = true`
     - `EKS_CLUSTER_NAME = model-deployment-cluster`
   - The buildspec.yaml will automatically deploy to EKS
   - Make sure CodeBuild role has EKS permissions

4. **Kubernetes manifests:**
   - Your `k8s/` folder contains all necessary manifests
   - CodeBuild will apply them automatically when `DEPLOY_TO_K8S=true`

### Option C: Deploy to EC2

1. **Create EC2 instance** with Docker installed
2. **Add Deploy stage** using AWS Systems Manager or SSH
3. **Pull and run** the Docker image from ECR

---

## 📝 Buildspec Configuration

Your `buildspec.yaml` is already configured! It:

1. ✅ Logs into ECR
2. ✅ Builds Docker image with platform-specific build
3. ✅ Tags image with `latest` and build number
4. ✅ Pushes to ECR
5. ✅ Optionally deploys to Kubernetes

**Key environment variables needed:**
- `ECR_REPO_REGISTRY`: Your ECR registry URL
- `APP_NAME`: `model-deployment-tutorial`
- `AWS_DEFAULT_REGION`: `eu-central-1`
- `DEPLOY_TO_K8S`: `true` or `false`
- `EKS_CLUSTER_NAME`: Your EKS cluster name (if using K8s)

---

## 🔐 Security Best Practices

1. **Use IAM Roles** (not access keys) for CodeBuild
2. **Store secrets in AWS Secrets Manager** or Parameter Store
3. **Use GitHub App** instead of Personal Access Token (more secure)
4. **Enable encryption** for artifacts in S3
5. **Use least privilege** IAM policies
6. **Enable CloudTrail** for audit logging

---

## 🐛 Troubleshooting

### Build Fails: "Cannot connect to Docker daemon"
- **Solution**: CodeBuild uses Docker-in-Docker, which should work automatically
- Check if buildspec uses `docker build` correctly

### Build Fails: "Access Denied" to ECR
- **Solution**: Check CodeBuild role has `AmazonEC2ContainerRegistryPowerUser` policy
- Verify ECR repository exists and is in correct region

### Build Fails: "GitHub authentication failed"
- **Solution**: Regenerate GitHub Personal Access Token
- Update CodePipeline source connection

### Pipeline doesn't trigger on push
- **Solution**: Check webhook in GitHub repository settings
- Verify CodePipeline source connection is active

### Kubernetes deployment fails
- **Solution**: Verify `kubectl` is available in CodeBuild
- Check CodeBuild role has EKS permissions
- Verify EKS cluster name is correct
- Check kubeconfig is updated correctly

---

## 📊 Monitoring

1. **CodePipeline Console:**
   - View pipeline execution history
   - See stage-by-stage progress
   - Check for errors

2. **CodeBuild Console:**
   - View detailed build logs
   - Check build metrics
   - See build duration and costs

3. **CloudWatch Logs:**
   - Build logs: `/aws/codebuild/model-deployment-tutorial`
   - Pipeline logs: `/aws/codepipeline/model-deployment-tutorial-pipeline`

4. **CloudWatch Metrics:**
   - Build success/failure rates
   - Build duration
   - Pipeline execution times

---

## 🚀 Quick Start Commands

### Create Everything via AWS CLI

```bash
# 1. Create CodeBuild project
aws codebuild create-project \
  --name model-deployment-tutorial-build \
  --source type=GITHUB,location=https://github.com/YOUR_USERNAME/YOUR_REPO.git \
  --artifacts type=NO_ARTIFACTS \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL \
  --service-role arn:aws:iam::448772857649:role/CodeBuild-ModelDeployment-Role

# 2. Create CodePipeline
aws codepipeline create-pipeline \
  --pipeline-name model-deployment-tutorial-pipeline \
  --pipeline file://pipeline-definition.json
```

---

## 📚 Additional Resources

- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)
- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [GitHub Actions Alternative](https://docs.github.com/en/actions) - See `.github/workflows/deploy.yml`

---

## ✅ Checklist

- [ ] GitHub repository created and code pushed
- [ ] GitHub Personal Access Token created
- [ ] IAM role for CodeBuild created
- [ ] ECR repository exists (`model-deployment-tutorial`)
- [ ] CodeBuild project created
- [ ] CodeBuild environment variables configured
- [ ] CodePipeline created
- [ ] Pipeline successfully builds and pushes to ECR
- [ ] Docker image visible in ECR
- [ ] (Optional) Deployment stage configured

---

## 🎯 Next Steps

1. **Test the pipeline** by pushing a commit to GitHub
2. **Monitor the build** in CodeBuild console
3. **Verify the image** in ECR console
4. **Deploy to your infrastructure** (ECS/EKS/EC2)
5. **Set up monitoring** and alerts

Your CI/CD pipeline is now ready! 🚀

