## System Testing 
It is common practice to test the components once they are deployed to QA environments. 
This acts like a quality check, to validate the BYOC scenario to serve trained model as Amazon SageMaker Endpoint and to check if the model trained and deployed on QA meets the performance threshold.

### Flow of System Testing Step Functions
1. Execute the Evaluate Endpoint lambda function by passing the SageMaker Hosted Endpoint and testing data details.
2. Capture the details in evaluation.json file, which is stored in S3, for audit and tracking.
3. Check the result from evaluate endpoint lambda against threshold value.
4. If the threshold obtained from evaluation is above the preset threshold, the model is rejected and the System test failure is reported to CodePipeline
5. If the threshold obtained from evaluation is below the preset threshold, the model is approved for production.
6. Execute a baseline job to analyze an input dataset. Model Monitor provides a built-in container that provides the ability to suggest the constraints automatically for CSV and flat JSON input. This sagemaker-model-monitor-analyzer container also provides you with a range of model monitoring capabilities, including constraint validation against a baseline, and emitting Amazon CloudWatch metrics. The container stores the baseline statistics in a file called statistics.json, and the constraints in a file called constraints.json.
7. Production model is then registered for the version of model and metadata to model package group. By storing the model version in the registry, we can track all of the models that are trained, and approved, to solve our particular ML problem.

## References
* Baseline Constraints: https://aws.amazon.com/blogs/big-data/test-data-quality-at-scale-with-deequ/