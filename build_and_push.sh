#!/usr/bin/env bash

# The argument to this script is the image name. This will be used as the image on the local
# machine and combined with the account and region to form the repository name for ECR.
image=$1
region=$2

if [ "$image" == "" ]
then
    echo "Usage: $0 <image-name>"
    exit 1
fi

if [ "$region" == "" ]
then
    region=${region:-us-east-2}
    echo "Setting region to us-east-2 by default"
fi

chmod +x model/serve

# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ]
then
    exit 255
fi


# repository_url="${account}.dkr.ecr.${region}.amazonaws.com/${image}:latest"
repository_url="${account}.dkr.ecr.${region}.amazonaws.com/${image}"
image_url="${account}.dkr.ecr.${region}.amazonaws.com/${image}"

echo "URL: " $repository_url


# If the repository doesn't exist in ECR, create it.

aws ecr describe-repositories --repository-names "${image}" > /dev/null 2>&1

if [ $? -ne 0 ]
then
    echo "Creating new AWS ECR repository..."
    aws ecr create-repository --repository-name "${image}" --region ${region} > /dev/null --tags Key=name,Value=${image} Key=APPLICATION,Value=INTENT Key=COST_CENTER,Value=INTENT Key=ENVIRONMENT,Value=DEV
    echo "Success"
fi

# Get the login command from ECR and execute it directly
echo "Login to AWS ECR"
$(aws ecr get-login-password --region ${region} | docker login --username AWS --password-stdin ${repository_url})

# Build the docker image locally with the image name and then push it to ECR
# with the full name.
docker build  -t ${image} .
docker tag ${image} ${image_url}

docker push ${image_url}
