# AWS Account Setup Guide for Model Deployment Tutorial

This guide will help you set up a new AWS account for the model deployment and monitoring tutorial.

## Table of Contents

1. [Creating an AWS Account](#creating-an-aws-account)
2. [Initial Account Configuration](#initial-account-configuration)
3. [IAM Setup](#iam-setup)
4. [Required AWS Services Setup](#required-aws-services-setup)
5. [Cost Management](#cost-management)
6. [Security Best Practices](#security-best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 1. Creating an AWS Account

### Step 1: Sign Up for AWS

1. Go to [AWS Sign Up Page](https://aws.amazon.com/)
2. Click **"Create an AWS Account"**
3. Enter your email address and choose a password
4. Choose an **AWS account name** (e.g., "ML-Tutorial-Account")

### Step 2: Account Information

1. **Contact Information**:
   - Full name
   - Company name (optional)
   - Phone number
   - Country/Region

2. **Payment Information**:
   - Credit card (required, but won't be charged unless you use paid services)
   - Billing address

### Step 3: Identity Verification

- AWS will call your phone number to verify
- Enter the verification code when prompted

### Step 4: Support Plan Selection

- Choose **"Basic Plan"** (free) for the tutorial
- You can upgrade later if needed

### Step 5: Account Confirmation

- Check your email and click the confirmation link
- Your AWS account is now active!

**Note**: It may take a few minutes for your account to be fully activated.

---

## 2. Initial Account Configuration

### Step 1: Sign In to AWS Console

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Sign in with your email and password

### Step 2: Choose a Region

- Select a region close to you (e.g., `eu-central-1`, `eu-west-1`)
- **Important**: Most services are region-specific
- For this tutorial, we'll use `eu-central-1` (N. Virginia)

### Step 3: Enable MFA (Multi-Factor Authentication)

**Highly Recommended for Security**

1. Click on your account name (top right)
2. Select **"Security credentials"**
3. Under **"Multi-factor authentication (MFA)"**, click **"Assign MFA device"**
4. Choose **"Virtual MFA device"** (use an app like Google Authenticator)
5. Scan QR code and enter two consecutive codes

---

## 3. IAM Setup

### Step 1: Create an IAM User (Don't Use Root Account)

**Never use root account credentials for daily operations!**

1. Go to **IAM** service
2. Click **"Users"** → **"Add users"**
3. User name: `ml-tutorial-user`
4. Select **"Provide user access to the AWS Management Console"**
5. Choose **"I want to create an IAM user"**
6. Set a console password (or auto-generate)
7. Click **"Next"**

### Step 2: Attach Policies

1. Select **"Attach policies directly"**
2. Attach these policies:
   - `AmazonS3FullAccess` (for S3)
   - `CloudWatchFullAccess` (for CloudWatch)
   - `AmazonAthenaFullAccess` (for Athena)
   - `AmazonEC2ContainerRegistryFullAccess` (for ECR)
   - `AmazonECS_FullAccess` (for ECS, if using)
   - `IAMFullAccess` (for creating roles, be careful in production)

**Note**: In production, use least-privilege policies!

3. Click **"Next"** → **"Create user"**

### Step 3: Create Access Keys

1. Click on the user you just created
2. Go to **"Security credentials"** tab
3. Click **"Create access key"**
4. Choose **"Application running outside AWS"**
5. Click **"Next"** → **"Create access key"**
6. **IMPORTANT**: Download the CSV file or copy:
   - Access Key ID
   - Secret Access Key
   - **You won't be able to see the secret key again!**

### Step 4: Configure AWS CLI (Optional but Recommended)

```bash
# Install AWS CLI (if not installed)
# macOS: brew install awscli
# Linux: sudo apt-get install awscli
# Windows: Download from AWS website

# Configure credentials
aws configure

# Enter:
# AWS Access Key ID: [your access key]
# AWS Secret Access Key: [your secret key]
# Default region name: eu-central-1
# Default output format: json
```

---

## 4. Required AWS Services Setup

### 4.1 Amazon S3 (Simple Storage Service)

**Purpose**: Store model files and prediction logs

1. Go to **S3** service
2. Click **"Create bucket"**
3. Bucket name: `ml-tutorial-models-[your-name]` (must be globally unique)
4. Region: `eu-central-1`
5. **Uncheck** "Block all public access" (or configure as needed)
6. Click **"Create bucket"**

**Create folders**:
- `models/` - for model files
- `predictions/` - for prediction logs
- `athena-results/` - for Athena query results

**Upload model**:
```bash
aws s3 cp model.txt s3://ml-tutorial-models-[your-name]/models/model.txt
```

### 4.2 Amazon ECR (Elastic Container Registry)

**Purpose**: Store Docker images

1. Go to **ECR** service
2. Click **"Create repository"**
3. Repository name: `model-deployment-tutorial`
4. Visibility: **Private**
5. Click **"Create repository"**

**Get login command**:
```bash
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.eu-central-1.amazonaws.com
```

Replace `[ACCOUNT_ID]` with your AWS account ID (found in top-right of console).

### 4.3 CloudWatch Logs

**Purpose**: Application logging and monitoring

1. Go to **CloudWatch** service
2. Click **"Log groups"** → **"Create log group"**
3. Log group name: `model-deployment-tutorial`
4. Retention: **7 days** (to save costs)
5. Click **"Create"**

### 4.4 Amazon Athena

**Purpose**: Query prediction logs stored in S3

1. Go to **Athena** service
2. First-time setup:
   - Click **"Get started"**
   - Set up query result location in S3:
     - S3 path: `s3://ml-tutorial-models-[your-name]/athena-results/`
3. Create database:
   ```sql
   CREATE DATABASE ml_tutorial;
   ```
4. Create table (run in Query Editor):
   ```sql
   CREATE EXTERNAL TABLE IF NOT EXISTS ml_tutorial.model_predictions (
     user_id int,
     movie_id int,
     prediction double,
     inference_time_ms double,
     model_version string,
     timestamp string
   )
   ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
   LOCATION 's3://ml-tutorial-models-[your-name]/predictions/';
   ```

### 4.5 Amazon ECS (Optional - for container deployment)

**Purpose**: Run containers

1. Go to **ECS** service
2. Click **"Get started"** (first time)
3. Or create cluster manually:
   - Cluster name: `ml-tutorial-cluster`
   - Infrastructure: **AWS Fargate** (serverless)
   - Click **"Create"**

---

## 5. Cost Management

### Free Tier Limits

AWS Free Tier includes (for 12 months):
- **S3**: 5 GB storage, 20,000 GET requests
- **ECR**: 500 MB storage
- **CloudWatch**: 10 custom metrics, 5 GB log ingestion
- **Athena**: 1 TB data scanned/month (first 12 months)
- **Lambda**: 1 million requests/month
- **EC2**: 750 hours/month of t2.micro

### Cost Optimization Tips

1. **Set up Billing Alerts**:
   - Go to **Billing** → **Budgets**
   - Create budget: $10/month (or your limit)
   - Set up email alerts

2. **Clean up resources**:
   - Delete unused S3 objects
   - Stop/terminate unused EC2 instances
   - Delete old CloudWatch logs

3. **Use appropriate instance sizes**:
   - Start small, scale up as needed

4. **Monitor costs**:
   - Check **Cost Explorer** regularly
   - Review **Billing Dashboard**

### Estimated Tutorial Costs

- **S3**: ~$0.10/month (if under 5 GB)
- **CloudWatch**: ~$0.50/month (if under free tier)
- **Athena**: Free for first 1 TB/month
- **ECR**: Free for first 500 MB
- **ECS Fargate**: ~$0.04/hour per task (not in free tier)

**Total estimated cost**: $5-20/month for tutorial usage

---

## 6. Security Best Practices

### 1. Never Share Credentials
- Don't commit access keys to Git
- Use environment variables or AWS Secrets Manager

### 2. Use IAM Roles (Not Access Keys) When Possible
- For EC2, ECS, Lambda: use IAM roles
- Access keys only for local development

### 3. Enable MFA
- Required for root account
- Recommended for IAM users

### 4. Regular Access Review
- Review IAM users and permissions regularly
- Remove unused access keys

### 5. Use Least Privilege
- Only grant minimum required permissions
- Don't use `*FullAccess` policies in production

### 6. Enable CloudTrail
- Go to **CloudTrail** service
- Enable logging for audit trail

### 7. Secure S3 Buckets
- Use bucket policies
- Enable versioning for important data
- Enable encryption

---

## 7. Troubleshooting

### Issue: "Access Denied" Errors

**Solution**:
1. Check IAM user permissions
2. Verify access keys are correct
3. Check resource policies (S3 bucket, etc.)

### Issue: Can't Create Resources

**Solution**:
1. Check service limits
2. Verify region selection
3. Check IAM permissions

### Issue: High Costs

**Solution**:
1. Check Cost Explorer
2. Review active resources
3. Delete unused resources
4. Set up billing alerts

### Issue: Can't Access ECR

**Solution**:
1. Verify ECR repository exists
2. Check IAM permissions
3. Verify login command is correct
4. Check region matches

---

## 8. Verification Checklist

Before starting the tutorial, verify:

- [ ] AWS account created and activated
- [ ] MFA enabled on root account
- [ ] IAM user created with access keys
- [ ] AWS CLI configured (optional)
- [ ] S3 bucket created
- [ ] ECR repository created
- [ ] CloudWatch log group created
- [ ] Athena database and table created
- [ ] Billing alerts configured
- [ ] Model file uploaded to S3 (optional)

---

## 9. Quick Reference

### AWS Account ID
- Found in top-right corner of AWS Console
- Format: 12-digit number

### Regions
- **eu-central-1**: N. Virginia (cheapest, most services)
- **us-west-2**: Oregon
- **eu-west-1**: Ireland
- **ap-southeast-1**: Singapore

### Important URLs
- AWS Console: https://console.aws.amazon.com/
- AWS Documentation: https://docs.aws.amazon.com/
- AWS Free Tier: https://aws.amazon.com/free/
- AWS Support: https://aws.amazon.com/support/

---

## 10. Next Steps

After completing this setup:

1. **Follow the tutorial** using your AWS account
2. **Monitor costs** regularly
3. **Clean up resources** after tutorial
4. **Explore AWS services** further

---

## Support

If you encounter issues:

1. Check AWS documentation
2. Review AWS forums
3. Contact AWS support (if on paid plan)
4. Check tutorial troubleshooting section

---

**Remember**: Always clean up resources after the tutorial to avoid unexpected charges!

