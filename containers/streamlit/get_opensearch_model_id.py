# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# This module finds and returns the ML model ID in OpenSearch

import os
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from opensearch_py_ml.ml_commons import MLCommonClient

def opensearch_model_id():
    
    # Get the current region
    session = boto3.session.Session()
    region_name = session.region_name
    
    # Get OpenSearch endpoint
    host = os.environ['OPENSEARCH_SERVICE_ENDPOINT']

    # Get OpenSearch client
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region_name)
    
    opensearch_client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    ml_client = MLCommonClient(opensearch_client)
    
    model_query = {
      "query": {
        "match_all": {}
      },
      "size": 1000
    }
    
    model_query_json = json.dumps(model_query)
    
    response = ml_client.search_model(model_query)
    model_id = response['hits']['hits'][0]['_source']['model_id']
    model_id.strip()
    return model_id