# Endpoint and Pipeline Guide

## 🚀 CodePipeline Trigger

### Will CodePipeline trigger on push?

**Yes, if CodePipeline is properly configured!** Here's how it works:

1. **CodePipeline Setup Required:**
   - CodePipeline must be created and connected to your GitHub repository
   - A webhook must be configured in GitHub (usually automatic when using CodeStar connection)
   - The pipeline should be watching the `main` branch (or your default branch)

2. **How to Verify:**
   ```bash
   # Check if pipeline exists
   aws codepipeline list-pipelines --region eu-central-1
   
   # Check pipeline status
   aws codepipeline get-pipeline --name model-deployment-tutorial-pipeline --region eu-central-1
   ```

3. **Manual Trigger (if needed):**
   - Go to CodePipeline Console → Your pipeline → "Release change"
   - Or use AWS CLI:
     ```bash
     aws codepipeline start-pipeline-execution --name model-deployment-tutorial-pipeline --region eu-central-1
     ```

4. **What Happens on Push:**
   ```
   GitHub Push
      ↓
   CodePipeline (Source Stage)
      ↓
   CodeBuild (Build Stage)
      ├── Build Docker image
      ├── Push to ECR
      └── Deploy to EKS (if DEPLOY_TO_K8S=true)
   ```

### If CodePipeline is NOT set up:

You can still trigger CodeBuild directly:
- Go to CodeBuild Console → Your project → "Start build"
- Or use AWS CLI:
  ```bash
  aws codebuild start-build --project-name model-deployment-tutorial-build --region eu-central-1
  ```

---

## 🌐 Endpoint URL

### Getting Your Endpoint URL

After deployment, your application will be accessible via an **AWS Application Load Balancer (ALB)** created by the Ingress resource.

### Step 1: Wait for Ingress to Create ALB

The ALB takes 2-5 minutes to be created after the Ingress is applied.

### Step 2: Get the ALB Hostname

**Option A: Using kubectl (Recommended)**
```bash
# Update kubeconfig first
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster

# Get the ALB hostname
kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Option B: Using AWS CLI**
```bash
# List all ALBs
aws elbv2 describe-load-balancers --region eu-central-1 --query 'LoadBalancers[?contains(LoadBalancerName, `k8s`)].DNSName' --output text

# Or get specific ALB (after you know the name)
aws elbv2 describe-load-balancers --region eu-central-1 --query 'LoadBalancers[?contains(LoadBalancerName, `model-deployment`)].DNSName' --output text
```

**Option C: Check in AWS Console**
1. Go to **EC2 Console** → **Load Balancers**
2. Look for an ALB with name containing `k8s` or `model-deployment`
3. Copy the **DNS name**

### Step 3: Test the Endpoint

Once you have the ALB hostname (e.g., `k8s-default-modelde-xxxxx-xxxxx.eu-central-1.elb.amazonaws.com`):

```bash
# Set the ALB URL
ALB_URL=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health check
curl http://$ALB_URL/health

# Get API documentation
curl http://$ALB_URL/docs

# Make a prediction
curl -X POST "http://$ALB_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 259,
    "movie_id": 298,
    "age": 21,
    "gender": "M",
    "occupation_new": "student",
    "release_year": 1997.0,
    "Action": 0,
    "Adventure": 1,
    "War": 1,
    "user_total_ratings": 2,
    "user_liked_ratings": 2,
    "user_like_rate": 1.0
  }'
```

### Alternative: Port Forward (for Testing)

If the ALB isn't ready yet, you can use port-forward:

```bash
# Port forward to local machine
kubectl port-forward svc/model-deployment-api-service 8000:80

# Test locally
curl http://localhost:8000/health
```

---

## 📋 Quick Reference Commands

### Check Deployment Status
```bash
# Update kubeconfig
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster

# Check pods
kubectl get pods -l app=model-deployment-api

# Check services
kubectl get svc

# Check ingress (ALB)
kubectl get ingress model-deployment-api-ingress

# Check ingress details
kubectl describe ingress model-deployment-api-ingress
```

### Get Endpoint URL (One-liner)
```bash
# Get ALB URL
kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' && echo

# Or save to variable
export ALB_URL=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Your endpoint: http://$ALB_URL"
```

### Monitor Pipeline
```bash
# Check CodePipeline status
aws codepipeline get-pipeline-state --name model-deployment-tutorial-pipeline --region eu-central-1

# Check CodeBuild status
aws codebuild list-builds-for-project --project-name model-deployment-tutorial-build --region eu-central-1 --max-items 1
```

---

## 🔍 Troubleshooting

### Issue: Ingress shows no hostname

**Possible causes:**
1. AWS Load Balancer Controller not installed
2. ALB still being created (wait 2-5 minutes)
3. Ingress not applied yet

**Solutions:**
```bash
# Check if Load Balancer Controller is running
kubectl get deployment -n kube-system aws-load-balancer-controller

# Check controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check ingress events
kubectl describe ingress model-deployment-api-ingress
```

### Issue: Pipeline not triggering on push

**Possible causes:**
1. CodePipeline not created
2. Webhook not configured in GitHub
3. Branch name mismatch

**Solutions:**
1. Verify pipeline exists:
   ```bash
   aws codepipeline list-pipelines --region eu-central-1
   ```
2. Check GitHub webhook:
   - Go to GitHub repo → Settings → Webhooks
   - Verify webhook exists and is active
3. Manually trigger pipeline to test

### Issue: Endpoint returns 503 or timeout

**Possible causes:**
1. Pods not ready
2. Service not routing correctly
3. Health check failing

**Solutions:**
```bash
# Check pod status
kubectl get pods -l app=model-deployment-api

# Check pod logs
kubectl logs -l app=model-deployment-api --tail=50

# Check service endpoints
kubectl get endpoints model-deployment-api-service

# Test health endpoint directly on pod
kubectl exec -it <pod-name> -- curl http://localhost:8000/health
```

---

## 📝 Notes

1. **ALB Creation Time:** The ALB takes 2-5 minutes to be created after Ingress is applied
2. **Custom Domain:** The ingress.yaml has a placeholder hostname (`model-deployment-api.example.com`). You can update it with your own domain and add an SSL certificate ARN for HTTPS
3. **HTTPS:** To enable HTTPS, uncomment and update the `alb.ingress.kubernetes.io/certificate-arn` annotation in `k8s/ingress.yaml`
4. **Cost:** ALB has a cost (~$0.0225/hour). Consider deleting the ingress if not needed for testing

---

## ✅ Quick Test Script

Save this as `test-endpoint.sh`:

```bash
#!/bin/bash

# Update kubeconfig
aws eks update-kubeconfig --region eu-central-1 --name model-deployment-cluster

# Wait for ingress to be ready
echo "Waiting for Ingress to be ready..."
kubectl wait --for=condition=ready ingress/model-deployment-api-ingress --timeout=5m

# Get ALB URL
ALB_URL=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

if [ -z "$ALB_URL" ]; then
    echo "ERROR: ALB hostname not found. Check if AWS Load Balancer Controller is installed."
    exit 1
fi

echo "✅ ALB URL: http://$ALB_URL"
echo ""
echo "Testing health endpoint..."
curl -s http://$ALB_URL/health | jq . || curl -s http://$ALB_URL/health
echo ""
echo "✅ Endpoint is ready! Test it at: http://$ALB_URL"
echo "📚 API Docs: http://$ALB_URL/docs"
```

Make it executable and run:
```bash
chmod +x test-endpoint.sh
./test-endpoint.sh
```

---

**Your endpoint will be available at:** `http://<ALB_HOSTNAME>` once the deployment completes! 🚀

