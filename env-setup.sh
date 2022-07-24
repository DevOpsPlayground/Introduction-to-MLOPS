################################################################################
#############  Install necessary packages on EC2 instance       ################
################################################################################
sudo yum -y install jq bash-completion


################################################################################
#############  Create S3 bucket for storing model artifacts     ################
################################################################################
aws s3 mb "s3://${PIPELINE_BUCKET}" --region $AWS_DEFAULT_REGION &&\
aws s3api put-bucket-versioning --bucket "${PIPELINE_BUCKET}" \
--versioning-configuration Status=Enabled --region $AWS_DEFAULT_REGION


################################################################################
#############  Python setup with required libraries             ################
################################################################################
curl -O https://bootstrap.pypa.io/get-pip.py &&\
sudo python3 get-pip.py --user --no-warn-script-location &&\
rm get-pip.py &&\
python3 -m pip install -U pip boto3 numpy pandas wget awscli --user