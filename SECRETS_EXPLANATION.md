# Secrets Management Explanation

## Why `.example` Extension?

I created **both** `secrets.yaml.example` and `secrets.yaml` for different purposes:

### `secrets.yaml.example`
- **Purpose**: Template/documentation file
- **Contains**: Placeholder values and comments
- **Safe to commit**: ✅ Yes (no real secrets)
- **Use case**: Reference for what secrets are needed

### `secrets.yaml`
- **Purpose**: Actual secrets file for deployment
- **Contains**: Placeholder values that need to be replaced
- **Safe to commit**: ⚠️ Only if using placeholders (not real secrets)
- **Use case**: Ready-to-use template that you fill in with real values

## Best Practices

### For Tutorial/Development:
1. Use `secrets.yaml` with placeholder values
2. Replace placeholders with actual values before deployment
3. **Never commit real secrets to Git**

### For Production:
1. **Use IAM Roles for Pods (IRSA)** instead of access keys
2. Use AWS Secrets Manager or External Secrets Operator
3. Never store secrets in YAML files in Git
4. Use Kubernetes secrets created from external sources

## How to Use

### Option 1: Edit secrets.yaml directly
```bash
# Edit k8s/secrets.yaml with your actual values
vim k8s/secrets.yaml

# Apply
kubectl apply -f k8s/secrets.yaml
```

### Option 2: Create from example
```bash
# Copy example
cp k8s/secrets.yaml.example k8s/secrets.yaml

# Edit with your values
vim k8s/secrets.yaml

# Apply
kubectl apply -f k8s/secrets.yaml
```

### Option 3: Use kubectl create secret (recommended)
```bash
kubectl create secret generic model-deployment-secrets \
  --from-literal=AWS_ACCESS_KEY_ID=your-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-secret \
  --from-literal=S3_BUCKET=your-bucket
```

### Option 4: Use AWS Secrets Manager (production)
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name model-deployment/secrets \
  --secret-string file://secrets.json

# Use External Secrets Operator to sync to K8s
```

## Security Notes

⚠️ **Important**: 
- The `secrets.yaml` file contains placeholder values
- **Replace all `REPLACE_WITH_*` values** before deployment
- **Never commit real secrets** to version control
- Add `k8s/secrets.yaml` to `.gitignore` if you put real values in it
- In production, use IAM roles (IRSA) instead of access keys

## Current Setup

Both files are provided:
- `k8s/secrets.yaml.example` - Safe template (can commit)
- `k8s/secrets.yaml` - Ready-to-use template (replace values)

You can use either one, but `secrets.yaml` is more convenient as it's ready to edit and deploy.

