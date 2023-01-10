
# package import
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn import metrics

<<<<<<< Updated upstream
import joblib
=======
import pickle
>>>>>>> Stashed changes
import pandas as pd 
import numpy as np 

from google.cloud import bigquery
from google.cloud import aiplatform
from google.cloud import storage
import argparse
import os
import sys

<<<<<<< Updated upstream
=======
print('complete pkg imports')

>>>>>>> Stashed changes
# import argument to local variables
parser = argparse.ArgumentParser()
# the passed param, dest: a name for the param, default: if absent fetch this param from the OS, type: type to convert to, help: description of argument
parser.add_argument('--penalty', dest = 'penalty', default = 'l2', type = str, help = 'Penalty term')
parser.add_argument('--solver', dest = 'solver', default = 'newton-cg', type = str, help = 'Logistic regression solver')
parser.add_argument('--var_target', dest = 'var_target', type=str)
parser.add_argument('--var_omit', dest = 'var_omit', type=str)
parser.add_argument('--project_id', dest = 'project_id', type=str)
parser.add_argument('--bq_project', dest = 'bq_project', type=str)
parser.add_argument('--bq_dataset', dest = 'bq_dataset', type=str)
parser.add_argument('--bq_table', dest = 'bq_table', type=str)
parser.add_argument('--region', dest = 'region', type=str)
parser.add_argument('--experiment', dest = 'experiment', type=str)
parser.add_argument('--series', dest = 'series', type=str)
parser.add_argument('--experiment_name', dest = 'experiment_name', type=str)
parser.add_argument('--run_name', dest = 'run_name', type=str)
parser.add_argument('--bucket', dest = 'bucket', type=str)
parser.add_argument('--uri', dest = 'uri', type=str)
parser.add_argument('--blob', dest = 'blob', type=str)
parser.add_argument('--timestamp', dest = 'timestamp', type=str)
args = parser.parse_args()

<<<<<<< Updated upstream
VAR_OMIT = str(args.var_omit).split(' ')
=======
VAR_OMIT = str(args.var_omit).split('-')
VAR_TARGET = str(args.var_target)
VAR_OMIT_CLEAN = VAR_OMIT.append(VAR_TARGET)

print('complete args')
>>>>>>> Stashed changes

# clients
bq = bigquery.Client(project = args.project_id)
aiplatform.init(project = args.project_id, location = args.region)

<<<<<<< Updated upstream
=======
print('complete clients')

>>>>>>> Stashed changes
# Vertex AI Experiment
expRun = aiplatform.ExperimentRun.create(run_name = args.run_name, experiment = args.experiment_name)
expRun.log_params({'experiment': args.experiment, 'series': args.series, 'project_id': args.project_id})

<<<<<<< Updated upstream
=======
print('complete init exp log')

>>>>>>> Stashed changes
# get schema from bigquery source
query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{args.bq_table}'"
schema = bq.query(query).to_dataframe()

# get number of classes from bigquery source
nclasses = bq.query(query = f'SELECT DISTINCT {args.var_target} FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE {args.var_target} is not null').to_dataframe()
nclasses = nclasses.shape[0]
expRun.log_params({'data_source': f'bq://{args.bq_project}.{args.bq_dataset}.{args.bq_table}', 'nclasses': nclasses, 'var_split': 'splits', 'var_target': args.var_target})

<<<<<<< Updated upstream
train_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'TRAIN'"
train = bq.query(train_query).to_dataframe()
X_train = train.loc[:, ~train.columns.isin(VAR_OMIT)]
y_train = train[args.var_target]

val_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'VALIDATE'"
val = bq.query(val_query).to_dataframe()
X_val = val.loc[:, ~val.columns.isin(VAR_OMIT)]
y_val = val[args.var_target]

test_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'TEST'"
test = bq.query(test_query).to_dataframe()
X_test = test.loc[:, ~test.columns.isin(VAR_OMIT)]
y_test = test[args.var_target]
=======
print('complete bq classes')

train_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'TRAIN'"
train = bq.query(train_query).to_dataframe()
X_train = train.loc[:, ~train.columns.isin(VAR_OMIT_CLEAN)]
y_train = train[VAR_TARGET].astype('int')

val_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'VALIDATE'"
val = bq.query(val_query).to_dataframe()
X_val = val.loc[:, ~val.columns.isin(VAR_OMIT_CLEAN)]
y_val = val[VAR_TARGET].astype('int')

test_query = f"SELECT * FROM {args.bq_project}.{args.bq_dataset}.{args.bq_table} WHERE splits = 'TEST'"
test = bq.query(test_query).to_dataframe()
X_test = test.loc[:, ~test.columns.isin(VAR_OMIT_CLEAN)]
y_test = test[VAR_TARGET].astype('int')

print('complete training datasets')
>>>>>>> Stashed changes

# Logistic Regression
# instantiate the model 
logistic = LogisticRegression(solver=args.solver, penalty=args.penalty)

# Define a Standard Scaler to normalize inputs
scaler = StandardScaler()

expRun.log_params({'solver': args.solver, 'penalty': args.penalty})

<<<<<<< Updated upstream
=======
print('complete model definition')

>>>>>>> Stashed changes
# define pipeline
pipe = Pipeline(steps=[("scaler", scaler), ("logistic", logistic)])

# define grid search model
model = pipe.fit(X_train, y_train)

<<<<<<< Updated upstream
=======
print('complete model training')

>>>>>>> Stashed changes
# test evaluations:
y_pred = model.predict(X_test)
test_acc = metrics.accuracy_score(y_test, y_pred) 
test_prec = metrics.precision_score(y_test, y_pred)
test_rec = metrics.recall_score(y_test, y_pred)
test_rocauc = metrics.roc_auc_score(y_test, y_pred)
expRun.log_metrics({'test_accuracy': test_acc, 'test_precision': test_prec, 'test_recall': test_rec, 'test_roc_auc': test_rocauc})

# val evaluations:
y_pred_val = model.predict(X_val)
val_acc = metrics.accuracy_score(y_val, y_pred_val) 
val_prec = metrics.precision_score(y_val, y_pred_val)
val_rec = metrics.recall_score(y_val, y_pred_val)
val_rocauc = metrics.roc_auc_score(y_val, y_pred_val)
expRun.log_metrics({'validation_accuracy': val_acc, 'validation_precision': val_prec, 'validation_recall': val_rec, 'validation_roc_auc': val_rocauc})

# training evaluations:
y_pred_training = model.predict(X_train)
training_acc = metrics.accuracy_score(y_train, y_pred_training) 
training_prec = metrics.precision_score(y_train, y_pred_training)
training_rec = metrics.recall_score(y_train, y_pred_training)
training_rocauc = metrics.roc_auc_score(y_train, y_pred_training)
expRun.log_metrics({'training_accuracy': training_acc, 'training_precision':training_prec, 'training_recall': training_rec, 'training_roc_auc': training_rocauc})

# output the model save files
<<<<<<< Updated upstream
joblib.dump(model, 'model.joblib') # the model needs to be named model.joblib is order for model upload to be successful
=======
with open('model.pkl','wb') as f:
    pickle.dump(model,f)
>>>>>>> Stashed changes

# Upload the model to GCS
bucket = storage.Client().bucket(args.bucket)
blob = bucket.blob(args.blob)
<<<<<<< Updated upstream
blob.upload_from_filename('model.joblib')

expRun.log_params({'model.save': f'{args.uri}/models/{args.timestamp}/model'})
expRun.end_run()
=======
blob.upload_from_filename('model.pkl')

expRun.log_params({'model.save': f'{args.uri}/models/{args.timestamp}/model'})
expRun.end_run()

print('complete model upload')
>>>>>>> Stashed changes
