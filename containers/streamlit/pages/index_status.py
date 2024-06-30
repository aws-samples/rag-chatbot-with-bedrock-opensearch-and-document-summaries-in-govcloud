# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import streamlit as st
import pandas as pd
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import os

st.title("Document index status")

# Get the current region
session = boto3.session.Session()
region_name = session.region_name

# Get the OpenSearch host name and index names
host = os.environ['OPENSEARCH_SERVICE_ENDPOINT']
summary_index_name = os.environ['OPENSEARCH_SUMMARY_INDEX']
full_text_index_name = os.environ['OPENSEARCH_FULL_TEXT_INDEX']

# Get the bucket name
stack_name = "chatbot-demo"
cf_client = boto3.client('cloudformation')
response = cf_client.describe_stacks(StackName=stack_name)
outputs = response["Stacks"][0]["Outputs"]
bucket_name = list(filter(lambda outputs: outputs['OutputKey'] == 'DataBucket', outputs))[0]["OutputValue"]

def get_s3_key_list(bucket_name, s3_prefix, file_extensions, max_file_size):
    s3_resource = boto3.resource('s3')
    key_list = []
    for key in s3_resource.Bucket(bucket_name).objects.filter(Prefix=s3_prefix):
        if key.key.endswith(file_extensions) and int(key.size) <= max_file_size:
            key_list.append(key.key)
            
    return key_list

# Get a list of documents in S3
s3_prefix = ""
file_extensions = (".md", ".pdf", ".docx")
max_file_size = 30000000
key_list = get_s3_key_list(
    bucket_name = bucket_name,
    s3_prefix = s3_prefix,
    file_extensions = file_extensions,
    max_file_size = max_file_size
)

# Get OpenSearch client
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region_name)

opensearch_client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    requestTimeout = 20,
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

index_list = []

# Get a list of dictionaries with counts of OpenSearch documents per file
for count, key in enumerate(key_list):
    # Query is the same for both summary and full text indices
    query={
        "query": {
            "match_phrase": {
                "document": key
            }
        }
    }
    # Get the summary count
    summary_response = opensearch_client.count(index=summary_index_name, body=query)
    # Get the full text count
    full_text_response = opensearch_client.count(index=full_text_index_name, body=query)
    index_list.append(
        {'#': count + 1, 'Filename': key, 'Summary Index Count': summary_response['count'], 'Full Text Index Count': full_text_response['count']}
    )
    
if len(index_list) > 0:    
    # Convert the list of dictionaries to a dataframe
    df = pd.DataFrame(index_list)
    
    # Display the dataframe
    st.dataframe(df.set_index(df.columns[0]))
else:
    st.write("No objects in S3 bucket")