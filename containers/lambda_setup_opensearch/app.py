# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import tempfile
import os
matplotlib_temp_dir = tempfile.TemporaryDirectory()
huggingface_temp_dir = tempfile.TemporaryDirectory()
os.environ['MPLCONFIGDIR'] = matplotlib_temp_dir.name # this gives matplotlib a writable directory in Lambda
os.environ['HF_HOME'] = huggingface_temp_dir.name # this gives huggingface a writable directory in Lambda
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, helpers
from opensearch_py_ml.ml_models import SentenceTransformerModel
from opensearch_py_ml.ml_commons import MLCommonClient
import cfnresponse

def handler(event, context):
    print("Starting handler.")
    print("Event:", event)
    print("Context:", context)

    # Set success flag as true by default
    success_flag = True

    # If the event RequestType is Delete or Update then there is nothing to do; return success
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return True
    else:

        # Get the OpenSearch endpoint created by the stack
        try:
            host = event['ResourceProperties']['OpenSearchServiceDomainEndpoint']
        except:
            print("Error getting OpenSearch Domain endpoint from context.")
            success_flag = False
        else:
            print("The endpoint for the OpenSearch domain is:", host)
    
        # Set names for the summary index, full text index, and pipeline
        summary_index_name = "chatbot-summary"
        full_text_index_name = "chatbot-full_text"
        pipeline_id = "chatbot-nlp-pipeline"
        
        try:
            session = boto3.session.Session()
            region_name = session.region_name
        except:
            print("Error getting region.")
            success_flag = False
        else:
            print("Region is", region_name)
    
        # Get a client for the OpenSearch endpoint
        print("Getting client for OpenSearch endpoint...")
        try:
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, region_name)
            opensearch_client = OpenSearch(
                hosts = [{'host': host, 'port': 443}],
                http_auth = auth,
                use_ssl = True,
                verify_certs = True,
                connection_class = RequestsHttpConnection
            )
        except:
            print("Error getting OpenSearch client.")
            success_flag = False
        else:
            print("Got OpenSearch client.")
        
        # Make OpenSearch cluster setting for ml_commons only_run_on_ml_mode to false
        print("Making OpenSearch cluster setting for ml_commons_only_run_on_ml_mode to false...")
        try:
            s = b'{"transient":{"plugins.ml_commons.only_run_on_ml_node": false}}'
            opensearch_client.cluster.put_settings(body=s)
        except:
            print("Error setting OpenSearch cluster setting for ml_commons_only_run_on_ml_mode to false.")
            success_flag = False
        else:
            print("Success setting OpenSearch cluster setting for ml_commons_only_run_on_ml_mode to false.")
        
        # Read back the settings
        try:
            print(opensearch_client.cluster.get_settings(flat_settings=True))
        except:
            print("Error getting OpenSearch cluster settings.")
            success_flag = False
        
        # Register the distillbert-roberta-v1 model in OpenSearch ML Commons and get model_id
        print("Registering model in OpenSearch...")
        try:
            ml_client = MLCommonClient(opensearch_client)
            model_id = ml_client.register_pretrained_model(model_name = "huggingface/sentence-transformers/all-distilroberta-v1", model_version = "1.0.1", model_format = "TORCH_SCRIPT", deploy_model=True, wait_until_deployed=True)
        except:
            print("Error registering model in OpenSearch.")
            success_flag = False
        else:
            print(model_id)
        
        # Read back model info from OpenSearch cluster to confirm
        try:
            model_info = ml_client.get_model_info(model_id)
        except:
            print("Error reading model info from OpenSearch.")
            success_flag = False

        # Define the OpenSearch neural search ingestion pipeline
        print("Defining OpenSearch neural search ingestion pipeline...")
        try:
            pipeline={
              "description": "Neural search pipeline",
              "processors" : [
                {
                  "text_embedding": {
                    "model_id": model_id,
                    "field_map": {
                       "text": "text_embedding"
                    }
                  }
                }
              ]
            }
            opensearch_client.ingest.put_pipeline(id=pipeline_id,body=pipeline)
        except:
            print("Error defining neural search ingestion pipeline in OpenSearch.")
            success_flag = False
        else:
            print("Success defining neural search ingestion pipeline in OpenSearch.")
        
        # Read back the ingestion pipeline to confirm
        try:
            print(opensearch_client.ingest.get_pipeline(id=pipeline_id))
        except:
            print("Error reading ingestion pipeline from OpenSearch.")
            success_flag = False
        
        # Define the KNN index
        print("Defining the KNN index...")
        knn_index = {
          "settings": {
            "index.knn": True,
            "default_pipeline": pipeline_id
          },
          "mappings": {
            "properties": {
              "document": {
                "type": "text"
              },
              "section": {
                "type": "integer"
              },
              "text_embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                  "engine": "faiss",
                  "space_type": "l2",
                  "name": "hnsw",
                  "parameters": {}
                }
              },
              "text": {
                "type": "text"
              }
            }
          }
        }
        
        # Create the index for the document summaries
        print("Creating the index for the document summaries...")
        try:
            response = opensearch_client.indices.create(index=summary_index_name, body=knn_index, ignore=400)
        except:
            print("Error creating index for document summaries in OpenSearch.")
            success_flag = False
        else:
            print(response)
            print("Success creating index for document summaries in OpenSearch.")
  
        # Create the index for the full text summaries
        print("Creating the index for the full text...")
        try:
            response = opensearch_client.indices.create(index=full_text_index_name, body=knn_index, ignore=400)
        except:
            print("Error creating index for full text in OpenSearch.")
            success_flag = False
        else:
            print(response)
            print("Success creating index for full text in OpenSearch.")
        
        # Read back the lst of indices to confirm
        try:
            for index in opensearch_client.indices.get('*'):
                print(index)
        except:
            print("Error listing indices in OpenSearch.")
            success_flag = False
        
        print("Done.")
        
        # Send the CloudFormation response based on the value of success_flag
        if success_flag == True:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        else:
            cfnresponse.send(event, context, cfnresponse.FAILED, {})
    
        return success_flag