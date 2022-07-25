################################################################################
############# Parameters required for Hands-on Exercise         ################
################################################################################
unset AWS_DEFAULT_REGION
unset AWS_ACCOUNT_ID
unset MODEL_NAME
unset VERIFY_ROLE_ARN
unset DATA_BUCKET
unset PIPELINE_BUCKET
export AWS_DEFAULT_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
aws configure set default.region ${AWS_DEFAULT_REGION}
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
export MODEL_NAME="{ModelName}"
export VERIFY_ROLE_ARN="arn\:aws\:iam::${AWS_ACCOUNT_ID}\:role/${MODEL_NAME}"
export DATA_BUCKET="data-${AWS_DEFAULT_REGION}-${AWS_ACCOUNT_ID}"
export PIPELINE_BUCKET="mlops-${AWS_DEFAULT_REGION}-${MODEL_NAME}"
echo "export AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID" >> ~/.bashrc
echo "export VERIFY_ROLE_ARN=$VERIFY_ROLE_ARN" >> ~/.bashrc
echo "export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION" >> ~/.bashrc
echo "export DATA_BUCKET=$DATA_BUCKET" >> ~/.bashrc
echo "export PIPELINE_BUCKET=$PIPELINE_BUCKET" >> ~/.bashrc
echo "export MODEL_NAME=$MODEL_NAME" >> ~/.bashrc


################################################################################
############# Command to upload Lambda functions to S3 and      ################
#############    replace the local references in CloudFormation ################
#############    template.                                      ################
################################################################################
cd ~/environment/Introduction-to-MLOPS/pipeline
aws cloudformation package --template-file mlops-pipeline.yml \
--s3-bucket $PIPELINE_BUCKET \
--s3-prefix bankmarketing-pipeline-{ModelName}/artifacts \
--output-template-file mlops-pipeline-output.yml


################################################################################
############# Command to create the CloudFormation stack        ################
################################################################################
aws cloudformation create-stack --stack-name bankmarketing-pipeline-{ModelName} \
--template-body file://~/environment/Introduction-to-MLOPS/pipeline/mlops-pipeline-output.yml \
--parameters $(printf "$parameters" "bankmarketing-{ModelName}" "latest" "{ModelName}" "{ModelName}") \
--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
