@echo off
setlocal

set REGION=us-east-1
set BUCKET=research-agent-tfstate
set TABLE=research-agent-tf-locks

echo Creating S3 bucket: %BUCKET% in region: %REGION%

aws s3api create-bucket --bucket %BUCKET% --region %REGION% 2>nul
if %errorlevel% equ 0 (
    echo Bucket created.
) else (
    echo Bucket already exists, continuing.
)

echo Enabling versioning...
aws s3api put-bucket-versioning --bucket %BUCKET% --versioning-configuration Status=Enabled

echo Blocking public access...
aws s3api put-public-access-block --bucket %BUCKET% --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo Enabling server-side encryption...
aws s3api put-bucket-encryption --bucket %BUCKET% --server-side-encryption-configuration "{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}"

echo Creating DynamoDB table for state locking: %TABLE%
aws dynamodb create-table --table-name %TABLE% --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region %REGION% 2>nul
if %errorlevel% equ 0 (
    echo DynamoDB table created.
) else (
    echo DynamoDB table already exists, continuing.
)

echo.
echo Bootstrap complete.
echo   S3 bucket  : %BUCKET% (versioned, encrypted, private)
echo   DynamoDB   : %TABLE% (state locking)
echo.
echo Next step: cd terraform  then  terraform init  then  terraform apply

endlocal
