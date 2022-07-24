import os
import sys
import json
import re
import traceback
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from sklearn import preprocessing

tf.get_logger().setLevel('ERROR')

# Path prefix for Sagemaker to identify files in container
prefix = '/opt/ml'

# Path for data storage in Sagemaker
input_path = os.path.join(prefix, 'input/data')

# Path to log file generated as a result of failures
output_path = os.path.join(prefix, 'output')

# Create a model.tar.gz file 
model_path = os.path.join(prefix, 'model')

# Hyperparameters to be sent to training job estimator
param_path = os.path.join(prefix, 'input/config/hyperparameters.json')


# Model training function
def train():
    print("Training mode on...")
    
    try:
        # Path for training input files
        channel_name = 'training'
        training_path = os.path.join(input_path, channel_name)

        params = {}
        # Read in any hyperparameters that the are passed with the training job
        with open(param_path, 'r') as tc:
            is_float = re.compile(r'^\d+(?:\.\d+)$')
            is_integer = re.compile(r'^\d+$')
            for key, value in json.load(tc).items():

                # Check and convert values from string
                if is_float.match(value) is not None:
                    value = float(value)
                elif is_integer.match(value) is not None:
                    value = int(value)
                params[key] = value

        # Check if input files are present at the specified location
        input_files = [ os.path.join(training_path, file) for file in os.listdir(training_path) ]
        if len(input_files) == 0:
            raise ValueError(('There are no files in {}.\\n' +
                              'This usually indicates that the channel ({}) was incorrectly specified,\\n' +
                              'the data specification in S3 was incorrectly specified or the role specified\\n' +
                              'does not have permission to access the data.').format(training_path, 
                                                                                     channel_name))
        
        # Column names for the dataset in use
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
        
        # Load the training dataset
        train_data = pd.read_csv(os.path.join(training_path, 'train.csv'), sep=',', names=column_names)
        
        # Load the validation dataset
        val_data = pd.read_csv(os.path.join(training_path, 'validate.csv'), sep=',', names=column_names)

        # Split the data for training features and prediction column
        train_y = train_data['y_yes'].to_numpy()
        train_X = train_data.drop(['y_yes'], axis=1).to_numpy()

        val_y = val_data['y_yes'].to_numpy()
        val_X = val_data.drop(['y_yes'], axis=1).to_numpy()

        # Normalize the data
        train_X = preprocessing.normalize(train_X)
        val_X = preprocessing.normalize(val_X)
        
        # Configure early stopping to save model from overfitting
        early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.01, patience=10)
        
        # Build the DNN layers
        algorithm = 'TensorflowRegression'
        print("Training Algorithm: %s" % algorithm)

        # Initialize weight tensors with a normal "Xavier" distribution
        initializer = tf.keras.initializers.GlorotNormal()
        dense_layers = []

        # Build Deep layers
        for layer in range(int(params.get('layers'))):
            if layer == 0:
                dense_layers.append(Dense(params.get('dense_layer'), kernel_initializer=initializer, input_dim=57))
            else:
                dense_layers.append(Dense(params.get('dense_layer'), activation='relu'))

        # Add final linear `pass-through` layer
        dense_layers.append(Dense(1, activation='linear'))

        # Build the model
        model = Sequential(dense_layers)
        model.summary()
        
        # Compile and train the model
        model.compile(loss='mse', optimizer='adam', metrics=['mae','accuracy'])
        model.fit(
            train_X,
            train_y,
            validation_data=(val_X, val_y),
            batch_size=params.get('batch_size'),
            epochs=params.get('epochs'),
            shuffle=True,
            verbose=1,
            callbacks=[early_stop]
        )
        
        # Save the model as a single 'h5' file without the optimizer
        print("Saving Model ...")
        model.save(
            filepath=os.path.join(model_path, 'model.h5'),
            overwrite=True,
            include_optimizer=False,
            save_format="h5"
        )

    except Exception as e:
        # Write out an error file. This will be returned as the failureReason in the
        # `DescribeTrainingJob` result.
        trc = traceback.format_exc()
        with open(os.path.join(output_path, 'failure'), 'w') as s:
            s.write('Exception during training: ' + str(e) + '\\n' + trc)
            
        # Printing this causes the exception to be in the training job logs, as well.
        print('Exception during training: ' + str(e) + '\\n' + trc, file=sys.stderr)
        
        # A non-zero exit code causes the training job to be marked as Failed.
        sys.exit(255)

# Define function called for local testing
def predict(payload, algorithm):
    print("Local Testing Mode ...")

    if algorithm is None:
        raise ValueError("Please provide the algorithm specification")
    payload = np.asarray(payload) # Convert the payload to numpy array
    payload = payload.reshape(1, -1) # Vectorize the payload
    
    return algorithm.predict(payload).tolist()