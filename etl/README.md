## Data Pre-processing
ETL component is responsible to perfom data cleaning tasks:
* Fetch the csv dataset uploaded in the S3 data bucket.
* Re-order the columns in the dataset to provide input for model training in a specific format.
* Normalise the data to have proper column names.
* Normalise data to categorise student, retired, unemployed rows with 'not_working'
* Convert categorical variables into dummy/ indicator variables like 'marital_divorced','marital_married','marital_single', 'marital_unknown' for divorced, married, single, unknown values of marital columns.
* Split the data into 80% training & baseline, 19% to validation and 1% to testing datasets.
* Upload all the 4 created datasets to MLOps pipeline bucket under input folder.

### Glue Job Configurations
This is specified in the etljob.json
* --job-language: The script programming language. This value must be either scala or python. If this parameter is not present, the default is python.
* Timeout: Number (integer), at least 1. The job timeout in minutes. This is the maximum time that a job run can consume resources before it is terminated and enters TIMEOUT status.
* MaxCapacity: When you specify a Python shell job (JobCommand.Name="pythonshell"), you can allocate either 0.0625 or 1 DPU i.e. AWS Glue data processing units. A DPU is a relative measure of processing power that consists of 4 vCPUs of compute capacity and 16 GB of memory. 

## References:
* AWS Glue API: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api.html
* AWS Glue API Jobs: https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-jobs-job.html