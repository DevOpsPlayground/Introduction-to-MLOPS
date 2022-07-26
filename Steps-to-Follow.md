# Steps to Create your First MLOps Pipeline

* Step-1: [Get the Code](#get-the-code)
* Step-2: [Configure Environment](#configure-environment)
* Step-3: [Create required Resources for CodePipeline](#create-required-resources-for-codepipeline)
* Step-4: [Create CodePipeline](#create-codepipeline)
* Step-5: [Simulate load on production endpoint](#simulate-load-on-production-endpoint)
* Step-6: [Instance Clean-up](#instance-clean-up)


## Get the Code
```
git clone https://github.com/DevOpsPlayground/Introduction-to-MLOPS.git
```

## Configure Environment 
1.	Edit the bash script helper-cmds.sh
2.	Replace `{ModelName}` with the a unique name for your model (in the format {firstname}{random 2 digits}) 
    Example: afroz19
3.	Save the file
4.	Copy the contents under the header "Parameters required for Hands-on Exercise" of the file and run-on terminal
5.	After the commands are executed successfully, run the below command:
    ```
    cd ~/workdir/Introduction-to-MLOPS/
    bash env-setup.sh
    ```
6.	Create an ECR repository with name bankmarketing-{modelname}
7.	Run the below command to check if all the resources are created successfully.
    ```
    cd ~/workdir/Introduction-to-MLOPS/utils
    python3 validate_resource.py
    ```

## Create required Resources for CodePipeline
1.	Set the Parameters for CloudFormation template
    ```
    unset parameters
    parameters="$parameters ParameterKey=ImageRepoName,ParameterValue=%s"
    parameters="$parameters ParameterKey=ImageTagName,ParameterValue=%s"
    parameters="$parameters ParameterKey=ModelName,ParameterValue=%s"
    parameters="$parameters ParameterKey=RoleName,ParameterValue=%s"
    ```
2.	Run below command to upload lambda functions to s3 bucket and replace local references in CloudFormation template
    _The command with replaced model names can be found in helper-cmds.sh_
    ```
    cd ~/workdir/Introduction-to-MLOPS/pipeline 
    aws cloudformation package --template-file mlops-pipeline.yml \
    --s3-bucket $PIPELINE_BUCKET \
    --s3-prefix bankmarketing-pipeline-{ModelName}/artifacts \
    --output-template-file mlops-pipeline-output.yml
    ```
3.	Execute below command to run the CloudFormation stack
    _The command with replaced model names can be found in helper-cmds.sh_
    ```
    aws cloudformation create-stack --stack-name bankmarketing-pipeline-{ModelName} \
    --template-body file://~/workdir/Introduction-to-MLOPS/pipeline/mlops-pipeline-output.yml \
    --parameters $(printf "$parameters" "bankmarketing-{ModelName}" "latest" "{ModelName}" "{ModelName}") \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
    ```
4.	Navigate to CloudFormation using AWS Management Console and check for the stack with the name provided above `bankmarketing-pipeline-{ModelName}`
5.	Wait until the status for stack is CREATE_COMPLETE

## Create CodePipeline
### Pipeline Settings
1. Navigate to CodePipeline using AWS Management Console
2. Click on **Create pipeline** button and enter the below details for _Pipeline settings_
    | Property Name | Value                                                                                    |
    | :------------ | :----------------------------------------------------------------------------------------|
    | Pipeline name | `bankmarketing-pipeline-{ModelName}`                                                     |
    | Service role  | Choose Existing service role with Role name: `arn:aws:iam::{AccountId}:role/{ModelName}` |
    | Advanced Settings: Artifact Store | Choose Custom location: `mlops-eu-west-1-{ModelName}`                | 
3. Click on **Next**

### Add Source Stage
1.	Add a Source Stage
    1.	Add a ModelSource action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `ModelSource`                |
        | Action Provider          | `AWS CodeCommit`             |
        | Repository name          | `mlops`                      |
        | Branch name              | `master`                     |
        | Change detection options | `AWS CodePipeline`           |
        | Output artifact format   | `CodePipeline default`       |
        | Output artifacts         | `ModelSourceOutput`          |

    2.	Add a ETLSource action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `ETLSource`                  |
        | Action Provider          | `AWS CodeCommit`             |
        | Repository name          | `mlops`                      |
        | Branch name              | `etl`                        | 
        | Change detection options | `AWS CodePipeline`           |
        | Output artifact format   | `CodePipeline default`       |
        | Output artifacts         | `EtlSourceOutput`            |
        
    3.	Add a DataSource action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `DataSource`                 |
        | Action Provider          | `Amazon S3`                  |
        | Bucket                   | `data-{region}-{accountId}`  |
        | S3 object key            | `input/raw/bankmarketing.csv`|
        | Change detection options | `AWS CodePipeline`           |
        | Output artifact format   | `CodePipeline default`       |
        | Output artifacts         | `DataSourceOutput`           |
        
    4.	Add a TestSource action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `TestSource`                 |
        | Action Provider          | `AWS CodeCommit`             |
        | Repository name          | `mlops`                      |
        | Branch name              | `test`                       |
        | Change detection options | `AWS CodePipeline`           |
        | Output artifact format   | `CodePipeline default`       |
        | Output artifacts         | `TestSourceOutput`           |

### Add Build Stage
2.	Add a new Build stage
    1. Add a BuildImage action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `BuildImage`                 |
        | Action Provider          | `AWS CodeBuild`              |
        | Region                   | `Europe (Ireland)`           |
        | Input artifacts          | `ModelSourceOutput`          |
        | Project name             | `mlops-buildimage-{ModelName}`|
        | Build type               | `Single build`               |
        | Output artifacts         | `BuildImageOutput`           | 

### Add ETL Stage
3. Add ETL stage
    1.	Add a GlueJob action with below configurations
        | Property Name            | Value                        |
        | :----------------------- | :----------------------------|
        | Action name              | `GlueJob`                    |
        | Action Provider          | `AWS Lambda`                 |
        | Region                   | `Europe (Ireland)`           |
        | Input artifacts          | `ETLSourceOutput`            |
        | Function name            | `etl-launch-job-{ModelName}` |
	 
### Add ETLApproval Stage
4.	Add ETLApproval stage
    1.	Add a ApproveETL action with below configurations
        | Property Name            | Value                               |
        | :----------------------- | :-----------------------------------|
        | Action name              | `ApproveETL`                        |
        | Action Provider          | `Manual approval`                   |
        | Comments                 | `Did the Glue job run successfully?`|

### Add Train Stage
5.	Add Train stage 
    1.	Add a TrainModel action with below configurations
        | Property Name            | Value                             |
        | :----------------------- | :-------------------------------- |
        | Action name              | `TrainModel`                      |
        | Action Provider          | `AWS Lambda`                      |
        | Region                   | `Europe (Ireland)`                |
        | Input artifacts          | `ModelSourceOutput`               |
        | Function name            | `training-launch-job-{modelname}` |
        | User parameters          | `mlops-pipeline-{modelname}`      |
        | Output artifacts         | `ModelTrainOutput`                |
 
### Add TrainApproval stage
6.	Add TrainApproval Stage
    1.	Add a ApproveTrain action with below configurations
        | Property Name            | Value                                   |
        | :----------------------- | :-------------------------------------- |
        | Action name              | `ApproveTrain`                          |
        | Action Provider          | `Manual approval`                       |
        | Comments                 | `Did the training job run successfully?`|

### Add DeployDev stage
7.	Add DeployDev Stage
    1.	Add a BuildDevDeployment action with below configurations
        | Property Name            | Value                                                         |
        | :----------------------- | :------------------------------------------------------------ |
        | Action name              | `BuildDevDeployment`                                          |
        | Action Provider          | `AWS CodeBuild`                                               |
        | Region                   | `Europe (Ireland)`                                            |
        | Input artifacts          | `ModelSourceOutput`                                           |
        | Project name             | `mlops-build-deployment-{modelname}`                          |
        | Environment Variable	   |  **Name:** `STAGE`, **Value:** `Dev`, **Type:** `Plaintext`   |
        | Build type               | `Single build`                                                |
        | Output artifacts	       | `BuildDevOutput`                                              |

    2.	Add a DeployDevModel action group with below configurations
        | Property Name            | Value                                                                     |
        | :----------------------- | :------------------------------------------------------------------------ |
        | Action name              | `DeployDevModel`                                                          |
        | Action Provider          | `AWS CloudFormation`                                                      |
        | Region                   | `Europe (Ireland)`                                                        |
        | Input artifacts          | `BuildDevOutput`                                                          |
        | Action mode              | `Replace a failed stack`                                                  |
        | Stack name               | `bankmarketing-pipeline-{modelname}-deploy-dev`                           |
        | Template                 | **Artifact name:** `BuildDevOutput`, **File name:** `deploy-model-Dev.yml`|
        | Template Configuration   | Use configuration file (set to enable) <br/> **Artifact name:** `BuildDevOutput` <br/> **File name:** `Dev-config-export.json`|
        | Capabilities             | `CAPABILITY_NAMED_IAM`                                                    |
        | Role name                | `arn:aws:iam::{AccountId}:role/{modelname}`                               |
        | Output artifacts         | `DeployDevOutput`                                                         |
 
### Add SystemTest Stage
8.	Add SystemTest stage
    1.	Add a BuildTestingWorkflow action with below configurations
        | Property Name            | Value                             |
        | :----------------------- | :-------------------------------- |
        | Action name              | `BuildTestingWorkflow`            |
        | Action Provider          | `AWS CodeBuild`                   |
        | Region                   | `Europe (Ireland)`                |
        | Input artifacts          | `TestSourceOutput`                |
        | Project name             | `mlops-buildworkflow-{modelname}` |
        | Build type               | `Single build`                    |
        | Output artifacts         | `BuildTestingWorkflowOutput`      | 

    2.	Add a ExecuteSystemTest action group with below configurations to add a next step in the stage
        _Copy the AccountId by clicking the username on the top_
        | Property Name            | Value                             |
        | :----------------------- | :-------------------------------- |
        | Action name              | `ExecuteSystemTest`               |
        | Action Provider          | `AWS Step Functions`              |
        | Region                   | `Europe (Ireland)`                |
        | Input artifacts          | `BuildTestingWorkflowOutput`      |
        | State machine ARN        | `arn:aws:states:eu-west-1:{AccountId}:stateMachine:bankmarketing-pipeline-{modelname}-systemtest` |
        | Input type               | `File path`                       |
        | Input                    | `input.json`                      |
        | Output artifacts         | `SystemTestingOutput`             | 

 
### Add DeployPrd Stage
9.	Add DeployPrd stage
    1.	Add a BuildPrdDeployment action with below configurations
        | Property Name            | Value                                                         |
        | :----------------------- | :------------------------------------------------------------ |
        | Action name              | `BuildPrdDeployment`                                          |
        | Action Provider          | `AWS CodeBuild`                                               |
        | Region                   | `Europe (Ireland)`                                            |
        | Input artifacts          | `ModelSourceOutput`                                           |
        | Project name             | `mlops-build-deployment-{modelname}`                          |
        | Environment Variable	   |  **Name:** `STAGE`, **Value:** `Prd`, **Type:** `Plaintext`   |
        | Build type               | `Single build`                                                |
        | Output artifacts	       | `BuildPrdOutput`                                              |

    2.	Add a DeployPrdModel action group with below configurations
        | Property Name            | Value                                                                     |
        | :----------------------- | :------------------------------------------------------------------------ |
        | Action name              | `DeployPrdModel`                                                          |
        | Action Provider          | `AWS CloudFormation`                                                      |
        | Region                   | `Europe (Ireland)`                                                        |
        | Input artifacts          | `BuildPrdOutput`                                                          |
        | Action mode              | `Create or update a stack`                                                |
        | Stack name               | `bankmarketing-pipeline-{modelname}-deploy-prd`                           |
        | Template	               | **Artifact name:** `BuildPrdOutput`, **File name:** `deploy-model-Prd.yml`|
        | Template Configuration   | Use configuration file (set to enable) <br/> **Artifact name:** `BuildPrdOutput` <br/> **File name:** `Prd-config-export.json`|
        | Capabilities             | `CAPABILITY_NAMED_IAM`                                                    |
        | Role name                | `arn:aws:iam::{AccountId}:role/{modelname}`                               |
        | Output artifacts         | `DeployPrdOutput`                                                         |
        
## Simulate load on production endpoint
1.	Open the file prod_load.py under Introduction-to-MLOPS/utils
2.	Replace `{ModelName}` with the Model Name used in the exercise
3.	On terminal run the below command
    ```
    cd ~/environment/Introduction-to-MLOPS/utils
    python3 prod_load.py
    ```
4.	Navigate to Amazon SageMaker --> Inference --> Endpoints
5.	Click on the endpoint with name `{ModelName}-prd-endpoint`
6.	Scroll to view Monitor section on the endpoint
7.	Click on View invocation metrics
8.	Select the metrics invocations, InvocationPerInstance, ModelLatency

## Instance Clean-up
1.	Navigate to CloudFormation Console
2.	Delete the following resources in reverse order of creation
    1.	`{PipelineName}-deploy-prd`
    2.	`{PipelineName}-systemtest`
    3.	`{PipelineName}-deploy-dev`
    4.	`{PipelineName}`
3.	Navigate to S3 Console: Search for the bucket with name `mlops-{RegionName}-{ModelName}`
4.	Navigate to ECR Console and delete the repository with name: `bankmarketing-{ModelName}`
