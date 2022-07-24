import os
import sys
import boto3
import numpy as np
import pandas as pd
import sklearn
from sklearn import preprocessing
from awsglue.utils import getResolvedOptions
from io import StringIO

# Helper function to split dataset (80/15/5)
def split_data(df, train_percent=0.8, validate_percent=0.19, seed=None):
    """ Splitting the data into train, test and validation datasets
    Args:
        df: dataset to perform the split
        train_percent: percentage of training data
        validate_percent: percentage of validation data
    """
    np.random.seed()
    perm = np.random.permutation(df.index)
    m = len(df.index)
    train_end = int(train_percent * m)
    validate_end = int(validate_percent * m) + train_end
    train = df.iloc[perm[:train_end]]
    validate = df.iloc[perm[train_end:validate_end]]
    test = df.iloc[perm[validate_end:]]

    return [('train', train), ('test', test), ('validate', validate), ('baseline', train)]


def normalise_data(data):
    """ Normalising and preparing data for model training
    """
    education_mapping_1 = {'basic.4y': 'basic',"basic.6y": "basic","basic.9y": "basic"}
    education_mapping_2 = {"university.degree": "university degree"}
    education_mapping_3 = {"high.school": "high school"}
    education_mapping_4 = {"professional.course": "professional course"}
    data["education"] = data["education"].replace(education_mapping_1)
    data["education"] = data["education"].replace(education_mapping_2)
    data["education"] = data["education"].replace(education_mapping_3)
    data["education"] = data["education"].replace(education_mapping_4)
    
    job_admin = {"admin.": "admin"}
    data["job"] = data["job"].replace(job_admin)
    
    data['no_previous_contact'] = np.where(data['pdays'] == 999, 1, 0)                        # Indicator variable to capture when pdays takes a value of 999
    data['not_working'] = np.where(np.in1d(data['job'], 
                                               ['student', 'retired', 'unemployed']), 1, 0)   # Indicator for individuals not actively employed
    model_data = pd.get_dummies(data)
    model_data = pd.concat([model_data['y_yes'], model_data.drop(['y_no', 'y_yes'], axis=1)], axis=1)

    return model_data


# Get job args
args = getResolvedOptions(sys.argv, ['S3_INPUT_BUCKET', 'S3_INPUT_KEY_PREFIX', 'S3_OUTPUT_BUCKET', 'S3_OUTPUT_KEY_PREFIX'])

# Downloading the data from S3 into a Dataframe
column_names = ['age', 'job', 'marital', 'education', 'default', 'housing', 'loan',
                'contact','month','day_of_week','campaign','pdays',
                'previous', 'poutcome', 'y']

client = boto3.client('s3')
bucket_name = args['S3_INPUT_BUCKET']
object_key = os.path.join(args['S3_INPUT_KEY_PREFIX'], 'bankmarketing.csv')

print("Downloading input data from S3 ...\n")
csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)
body = csv_obj['Body']
csv_string = body.read().decode('utf-8')
data = pd.read_csv(StringIO(csv_string), sep=',', names=column_names)

# Encoding the categorical variables
print("Encoding Features ...\n")
data =  normalise_data(data)

# Re-order data to better separate features
data = data[['y_yes','age','campaign','pdays','previous','no_previous_contact',
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
           'day_of_week_wed','poutcome_failure','poutcome_nonexistent','poutcome_success']]

# Create train, test and validate datasets
print("Creating dataset splits ...\n")
datasets = split_data(data)

# Upload data to S3 as .csv file while separating validation set
for file_name, partition_name in datasets:
    if file_name == 'test':
        print("Writing {} data ...\n".format(file_name))
        np.savetxt(file_name+'.csv', partition_name, delimiter=',', fmt='%s')
        boto3.Session().resource('s3').Bucket(args['S3_OUTPUT_BUCKET']).Object(os.path.join(args['S3_OUTPUT_KEY_PREFIX'], 'testing', file_name+'.csv')).upload_file(file_name+'.csv')
    
    elif file_name == 'baseline':
        print("Writing {} data ...\n".format(file_name))
        np.savetxt(
            file_name+'.csv',
            partition_name,
            delimiter=',', 
            fmt='%s', 
            header='y_yes,age,campaign,pdays,previous,no_previous_contact,not_working,\
            job_admin,job_blue-collar,job_entrepreneur,job_housemaid,job_management,\
            job_retired,job_self-employed,job_services,job_student,job_technician,\
            job_unemployed,job_unknown,marital_divorced,marital_married,marital_single,\
            marital_unknown,education_basic,\
            education_high school,education_illiterate,education_professional course,\
            education_university degree,education_unknown,default_no,default_unknown,\
            default_yes,housing_no,housing_unknown,housing_yes,loan_no,loan_unknown,\
            loan_yes,contact_cellular,contact_telephone,month_apr,month_aug,month_dec,\
            month_jul,month_jun,month_mar,month_may,month_nov,month_oct,month_sep,\
            day_of_week_fri,day_of_week_mon,day_of_week_thu,day_of_week_tue,\
            day_of_week_wed,poutcome_failure,poutcome_nonexistent,poutcome_success'
        )
        boto3.Session().resource('s3').Bucket(args['S3_OUTPUT_BUCKET']).Object(os.path.join(args['S3_OUTPUT_KEY_PREFIX'], 'baseline', file_name+'.csv')).upload_file(file_name+'.csv')
    
    else:
        print("Writing {} data ...\n".format(file_name))
        np.savetxt(file_name+'.csv', partition_name, delimiter=',', fmt='%s')
        boto3.Session().resource('s3').Bucket(args['S3_OUTPUT_BUCKET']).Object(os.path.join(args['S3_OUTPUT_KEY_PREFIX'], 'training', file_name+'.csv')).upload_file(file_name+'.csv')

print("Done writing to S3 ...\n")