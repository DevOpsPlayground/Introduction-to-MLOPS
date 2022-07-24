import os
import boto3
from botocore.exceptions import ClientError

s3 = boto3.resource('s3')
ecr = boto3.client('ecr')
code_commit = boto3.client('codecommit')


def check_bucket(bucket):
    """ Checks to confirm that a S3 Bucket exists.

    Args:
        bucket: String specifying the name of the S3 Bucket.
    """
    try:
        s3.meta.client.head_bucket(Bucket=bucket)
        print("Bucket: {} [".format(bucket)+u'\u2714'+"]")
    except ClientError as e:
        print("Bucket: {} [X]".format(bucket))
        print("Error Reason: \n{}\n".format(e))
        if bucket == os.environ['DATA_BUCKET']:
            print("Please refer to 'Module 2.1 - Training Data Bucket' to recreate the failed repository.")
        else:
            print("Please refer to 'Module 2.2 - ETL Data Bucket' to recreate the failed repository.")


def check_ecr(repo):
    """ Checks to confirm that an Elastic Container Registry exists.

    Args:
        repo: String specifying the name of the Elastic Container Registry.
    """
    reponame = "bankmarketing-{}".format(repo)
    try:
        ecr.describe_repositories(repositoryNames=[reponame])
        print("Elastic Container Repository: {} [".format(reponame)+u'\u2714'+"]")
    except ClientError as e:
        print("Elastic Container Repository: {} [X]".format(reponame))
        print("Error Reason: \n{}\n".format(e))
        print("Please refer to 'Module 2.4 - Container Image Repository' to recreate the failed repository.")


def main():
    """ Checks that the pipeline resources have been created correctly.
    """
    # Run alidation checks
    print("Validating Data Repositories Exist ...\n")
    check_bucket(os.environ['DATA_BUCKET'])
    check_bucket(os.environ['PIPELINE_BUCKET'])
    check_ecr(os.environ['MODEL_NAME'])


if __name__ == "__main__":
    main()