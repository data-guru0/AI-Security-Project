#!/bin/bash
set -e

REGION=${1:-us-east-1}
BUCKET="research-agent-tfstate"
TABLE="research-agent-tf-locks"

echo "Creating S3 bucket: $BUCKET in region: $REGION"

if [ "$REGION" = "us-east-1" ]; then
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$REGION" 2>/dev/null && echo "Bucket created." || echo "Bucket already exists, continuing."
else
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION" 2>/dev/null && echo "Bucket created." || echo "Bucket already exists, continuing."
fi

echo "Enabling versioning on S3 bucket..."
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

echo "Blocking public access on S3 bucket..."
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "Enabling server-side encryption on S3 bucket..."
aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

echo "Creating DynamoDB table for Terraform state locking: $TABLE"
aws dynamodb create-table \
  --table-name "$TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" 2>/dev/null && echo "DynamoDB table created." || echo "DynamoDB table already exists, continuing."

echo ""
echo "Bootstrap complete."
echo "  S3 bucket  : $BUCKET (versioned, encrypted, private)"
echo "  DynamoDB   : $TABLE (state locking)"
echo ""
echo "Next step: cd terraform && terraform init && terraform apply"
