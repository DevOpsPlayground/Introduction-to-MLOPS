import os
import io
import json
import logging
import boto3
import time
import botocore
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.metrics import mean_squared_error
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")
sm_client = boto3.client("sagemaker-runtime")


def evaluate_model(bucket, key, endpoint_name):
    """
    Description:
    ------------
    Executes model predictions on the testing dataset.
    
    :bucket: (str) Pipeline S3 Bucket.
    :key: (str) Path to "testing" dataset.
    :endpoint_name: (str) Name of the 'Dev' endpoint to test.

    :returns: Lists of ground truth, prediction labels and response times.
    
    """
    column_names = ['y_yes','age','campaign','pdays','previous','no_previous_contact',
           'not_working','job_admin','job_blue-collar','job_entrepreneur',
           'job_housemaid','job_management','job_retired','job_self-employed',
           'job_services','job_student','job_technician','job_unemployed',
           'job_unknown','marital_divorced','marital_married','marital_single',
           'marital_unknown','education_basic', 'education_high school',
           'education_illiterate','education_professional course',
           'education_university degree','education_unknown','default_no','default_unknown',
           'default_yes','housing_no','housing_unknown','housing_yes','loan_no','loan_unknown',
           'loan_yes','contact_cellular','contact_telephone','month_apr','month_aug','month_dec',
           'month_jul','month_jun','month_mar','month_may','month_nov','month_oct','month_sep',
           'day_of_week_fri','day_of_week_mon','day_of_week_thu','day_of_week_tue',
           'day_of_week_wed','poutcome_failure','poutcome_nonexistent','poutcome_success']

    response_times = []
    predictions = []
    y_test = []
    obj = s3.get_object(Bucket=bucket, Key=key)
    test_df = pd.read_csv(io.BytesIO(obj['Body'].read()), names=column_names)
    y = test_df['y_yes'].to_numpy()
    X = test_df.drop(['y_yes'], axis=1).to_numpy()
    X = preprocessing.normalize(X)
    
    # Cycle through each row of the data to get a prediction
    for row in range(len(X)):
        payload = ",".join(map(str, X[row]))
        elapsed_time = time.time()
        try:
            response = sm_client.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType = "text/csv",
                Body=payload
            )
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            logger.error(error_message)
            raise Exception(error_message)
        response_times.append(time.time() - elapsed_time)
        result = np.asarray(response['Body'].read().decode('utf-8').rstrip('\n'))
        predictions.append(float(result))
        y_test.append(float(y[row]))
    
    return y_test, predictions, response_times


def handler(event, context):
    logger.info("## Environment Variables ##")
    logger.info(os.environ)
    logger.info("## Event ##")
    logger.info(event)
    
    # Ensure variables passed from Model Evaluation Step
    if ("Bucket" in event):
        bucket = event["Bucket"]
        logger.info(bucket)
    else:
        raise KeyError("S3 'Bucket' not found in Lambda event!")
        
    if ("Key" in event):
        key = event["Key"]
        logger.info(key)
    else:
        raise KeyError("S3 'Key' not found in Lambda event!")
        
    if ("Output_Key" in event):
        output_key = event["Output_Key"]
        logger.info(output_key)
    else:
        raise KeyError("S3 'Output_Uri' not found in Lambda event!")
        
    if ("Endpoint_Name" in event):
        endpoint_name = event["Endpoint_Name"]
        logger.info(endpoint_name)
    else:
        raise KeyError("'SageMaker Endpoint Name' not found in Lambda event!")
    
    # Get the evaluation results from SageMaker hosted model
    logger.info("Evaluating SageMaker Hosted Model ...")
    y, y_pred, times = evaluate_model(bucket, key, endpoint_name)
    logger.info("got the evaluations")
    
    # Calculate the metrics
    mse = mean_squared_error(y, y_pred)
    rmse = mean_squared_error(y, y_pred, squared=False)
    std = np.std(np.array(y) - np.array(y_pred))

    # Save Metrics to S3 for Model Package
    logger.info("Root Mean Square Error: {}".format(rmse))
    logger.info("Average Endpoint Response Time: {:.2f}s".format(np.mean(times)))
    report_dict = {
        "regression_metrics": {
            "mse": {
                "value": mse,
                "standard_deviation": std
            },
        },
    }
    try:
        s3.put_object(
            Bucket=bucket,
            Key="{}/{}".format(output_key, "evaluation.json"),
            Body=json.dumps(report_dict, indent=4)
        )
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message)

    # Return results
    logger.info("Done!")
    return {
        "statusCode": 200,
        "Result": rmse,
        "AvgResponseTime": "{:.2f} seconds".format(np.mean(times))
    }
