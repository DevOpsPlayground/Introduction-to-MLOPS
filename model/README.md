## Model Training and Deployment
You have the option of providing separate Docker images for the training code and the inference code when creating a model for Amazon SageMaker, or you may merge them into a single Docker image. This strategy is also known as a BYOC (bring your own container) situation.

This component is responsible for model training on Amazon SageMaker using BYOC technique.

### Details on each file
* model.py 
    * train(): 
        * Load the training and validation datasets.
        * Create and run a Deep Neural Network based Regression algorithm.
        * Normalise the data using sklearn pre-processing normaliser to get a N-dimensional array.
        * Fit the model on training data and validate on validation data.
        * Save the model file and store on S3 bucket.
    * predict(): 
        * Takes the request payload as input
        * Convert the payload to numpy array
        * Send the converted payload for predictions

* app.py
    * Load the model and serve for prediction using nginx server and flask.

* trainingjob.json
    Contains the parametes necesssary to launch an Amazon SageMaker training job.
    * AlgorithmSpecification: Identifies the training container to use. Here, we'll use the ECR container created.
    * HyperParameters: Specify these algorithm-specific parameters to enable the estimation of model parameters during training. Hyperparameters can be tuned to optimize the learning process.
    * InputDataConfig: Describes the training dataset and the Amazon S3 location where it is stored.
    * OutputDataConfig: Identifies the Amazon S3 bucket where you want Amazon SageMaker to save the results of model training.
    * ResourceConfig: Identifies the resources, ML compute instances, and ML storage volumes to deploy for model training.
    * RoleARN: The Role that Amazon SageMaker assumes to perform tasks on your behalf during model training. 
    * StoppingCondition: To help cap training costs, use MaxRuntimeInSeconds to set a time limit for training. 

* Dockerfile
    * Describes the image that needs to be built for training and inferences.
    * This allows for a quick and easy deployment of custom ML containers.

* Assets
    * Contains the cloudformation template to deploy the ML model, create EndpointConfigurations and Endpoints for Development/QA and Production deployment.

* build.py
    * Extends the initial DEV or PROD stage configuration with the unique parameters that are specific to each execution of the pipeline.