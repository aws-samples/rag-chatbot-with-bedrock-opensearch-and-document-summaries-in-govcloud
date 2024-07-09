# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import urllib.parse
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, helpers
from index_documents_helper import (
    summarize_documents, 
    index_opensearch_summary_payload, 
    split_and_index_full_text,
    index_date,
    delete_index_recs_by_key_list
)

def handler(event, context):

    s3_notification = json.loads(event["Records"][0]["body"])
    if not "Records" in s3_notification:
        print("No records in notification.  Event dump:")
        print(event)
        #print("s3_notification: ", s3_notification)
        return {"statusCode": 200}

    if (
            not s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put" 
            and not s3_notification["Records"][0]["eventName"] == "ObjectCreated:CompleteMultipartUpload"
            and not s3_notification["Records"][0]["eventName"] == "ObjectRemoved:Delete"
            and not s3_notification["Records"][0]["eventName"] == "ObjectRemoved:DeleteMarkerCreated"
        ):
        print("Event is not s3 object created or object removed.  Event dump:")
        print(event)
        return {"statusCode": 200}

    print("S3 notification:", s3_notification)
    s3_object_data = s3_notification["Records"][0]["s3"]
    print("S3 object data:", s3_object_data)

    stack_name = "chatbot-demo"
    max_file_size = 25000000
    max_summary_length = 5000
    full_text_index_name = "chatbot-full_text"
    summary_index_name = "chatbot-summary"
    date_index_name = "chatbot-date-index"
    pipeline_id = "chatbot-nlp-pipeline"

    # Get the current region
    session = boto3.session.Session()
    region_name = session.region_name
    print("Region is", region_name)
    
    # Get the name of the data bucket and the OpenSearch endpoint created by the stack
    cf_client = boto3.client('cloudformation')
    response = cf_client.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0]["Outputs"]
    bucket_name = list(filter(lambda outputs: outputs['OutputKey'] == 'DataBucket', outputs))[0]["OutputValue"]
    print("The name of the data bucket is:", bucket_name)
    host = list(filter(lambda outputs: outputs['OutputKey'] == 'OpenSearchServiceDomainEndpoint', outputs))[0]["OutputValue"]
    print("The endpoint for the OpenSearch domain is:", host)

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

    # Get the file info and check to make sure it is within the maximum size
    key = urllib.parse.unquote_plus(s3_object_data["object"]["key"])
    print("Processing file", key, "for", s3_notification["Records"][0]["eventName"])
    if "size" in s3_object_data["object"] and s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put":
        file_size = s3_object_data["object"]["size"]
        if  file_size > max_file_size:
            print("File size", file_size, "exceeds maximum file size", max_file_size, " Skipping.")
            return {"statusCode": 200}

    key_list = [key]
    
    # Delete any existing records in the OpenSearch summary index for this document
    summary_delete_result = delete_index_recs_by_key_list(
        region_name = region_name, 
        opensearch_host = host, 
        key_list = key_list, 
        index_name = summary_index_name
    )
    print("Summary text delete result:", summary_delete_result)

    # Summarize the document using the LLM and return an OpenSearch payload
    if s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put":
        opensearch_payload = summarize_documents(
            region_name = region_name,
            bucket_name = bucket_name,
            key_list = key_list,
            max_summary_length = max_summary_length
        )
        print("OpenSearch payload has", len(opensearch_payload), "records")

    # Index the OpenSearch summary payload
    if s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put":
        summary_indexing_result = index_opensearch_summary_payload(
            region_name = region_name,
            opensearch_host = host,
            opensearch_payload = opensearch_payload,
            summary_index_name = summary_index_name
        )
        print("Summary indexing result:", summary_indexing_result)

    # Delete any existing records in the OpenSearch full text index for this document
    full_text_delete_result = delete_index_recs_by_key_list(
        region_name = region_name, 
        opensearch_host = host, 
        key_list = key_list, 
        index_name = full_text_index_name
    )
    print("Full text delete result:", full_text_delete_result)

    # Iterate through list of files, split into sections and add to OpenSearch index
    if s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put":
        full_text_indexing_result = split_and_index_full_text(
            region_name = region_name, 
            opensearch_host = host,
            bucket_name = bucket_name,
            key_list = key_list,
            full_text_index_name = full_text_index_name
        )
        print("Full text indexing result:", full_text_indexing_result)

    # Delete any existing records in the OpenSearch date index for this document
    date_delete_result = delete_index_recs_by_key_list(
        region_name = region_name, 
        opensearch_host = host, 
        key_list = key_list, 
        index_name = date_index_name
    )
    print("Date delete result:", date_delete_result)

    # Iterate through list of files, get date and add to OpenSearch index
    if s3_notification["Records"][0]["eventName"] == "ObjectCreated:Put":
        date_indexing_result = index_date(
            region_name = region_name, 
            opensearch_host = host,
            bucket_name = bucket_name,
            key_list = key_list,
            date_index_name = date_index_name
        )
        print("Date indexing result:", date_indexing_result)

    return {"statusCode": 200}