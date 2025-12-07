#!/bin/bash

# Quick script to get the ALB endpoint URL

set -e

CLUSTER_NAME="${EKS_CLUSTER_NAME:-model-deployment-cluster}"
REGION="${AWS_DEFAULT_REGION:-eu-central-1}"

echo "Getting endpoint URL for cluster: $CLUSTER_NAME"
echo ""

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME > /dev/null 2>&1

# Wait for ingress if it doesn't exist yet
if ! kubectl get ingress model-deployment-api-ingress > /dev/null 2>&1; then
    echo "⚠️  Ingress not found. Make sure the deployment has completed."
    exit 1
fi

# Get ALB hostname
ALB_URL=$(kubectl get ingress model-deployment-api-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -z "$ALB_URL" ]; then
    echo "⏳ ALB is still being created. This usually takes 2-5 minutes."
    echo ""
    echo "Check status with:"
    echo "  kubectl get ingress model-deployment-api-ingress"
    echo ""
    echo "Or check AWS Load Balancer Controller logs:"
    echo "  kubectl logs -n kube-system deployment/aws-load-balancer-controller"
    exit 1
fi

echo "✅ ALB Endpoint:"
echo ""
echo "   http://$ALB_URL"
echo ""
echo "📋 Quick Test Commands:"
echo ""
echo "   # Health check"
echo "   curl http://$ALB_URL/health"
echo ""
echo "   # API Documentation"
echo "   curl http://$ALB_URL/docs"
echo ""
echo "   # Make a prediction"
echo "   curl -X POST http://$ALB_URL/predict \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"user_id\": 259, \"movie_id\": 298, \"age\": 21, \"gender\": \"M\", \"occupation_new\": \"student\", \"release_year\": 1997.0, \"Action\": 0, \"Adventure\": 1, \"War\": 1, \"user_total_ratings\": 2, \"user_liked_ratings\": 2, \"user_like_rate\": 1.0}'"
echo ""

