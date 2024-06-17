# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# This file contains a helper function to make OpenSearch semantic queries
# Uses searches on document summaries and full text
# Returns RAG text, which is a string of all search results
# Also returns references, which is a list of references to search hits

import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, helpers
import json
from urllib.parse import quote

max_length_rag_text = 15000
summary_hit_score_threshold = 0.9
full_text_hit_score_threshold = 0.8
summary_weight_over_full_text = 1.5
use_summary = True

# Parameters below are used for the optional markdown file s3 key to weblink conversion feature
# If use_s3_key_to_weblink_conversion is set to true, markdown file references will be converted to weblinks based on other parameters here
use_s3_key_to_weblink_conversion = True
s3_key_prefix_to_remove = "website"
weblink_prefix = "https://internal-site.us"
s3_key_suffix_to_remove = ".md"
weblink_suffix = ".html"

def opensearch_query(query_text, model_id):
    # Set the OpenSearch host, index name and model ID from envionment variables
    summary_index_name = os.environ['OPENSEARCH_SUMMARY_INDEX']
    full_text_index_name = os.environ['OPENSEARCH_FULL_TEXT_INDEX']
    host = os.environ['OPENSEARCH_SERVICE_ENDPOINT']

    # Get the current region
    session = boto3.session.Session()
    region_name = session.region_name

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

    # Do a semantic search for the search term on the summary index
    if use_summary:
        query={
            "_source": {
                "excludes": [ "text_embedding" ]
            },
            "size": 30,
            "query": {
                "neural": {
                    "text_embedding": {
                    "query_text": query_text,
                    "model_id": model_id,
                    "k": 30
                    }
                }
            }
        }

        summary_response = opensearch_client.search(index=summary_index_name, 
                               body=query,
                               stored_fields=["text"])

        print("Got",len(summary_response["hits"]["hits"]),"hits.")
    else:
        summary_response = []
        
    # Build a list of keys of documents with the highest summary score for each document
    doc_list = []
    min_summary_hit_score = summary_hit_score_threshold * summary_response['hits']['max_score']

    for i in summary_response['hits']['hits']:
        # Add this document if it's within the hit score threshold
        if i['_score'] >= min_summary_hit_score:
            doc_list.append({i['_source']['document']: i['_score']})

    all_keys = set().union(*doc_list)
    document_summary_high_scores = {key: max(dic.get(key, float('-inf')) for dic in doc_list) for key in all_keys}

    # Do a semantic search for the search term on the full text index
    query={
        "_source": {
            "excludes": [ "text_embedding" ]
        },
        "size": 20,
        "query": {
            "neural": {
                "text_embedding": {
                "query_text": query_text,
                "model_id": model_id,
                "k": 30
                }
            }
        }
    }
    full_text_response = opensearch_client.search(index=full_text_index_name, 
                           body=query,
                           stored_fields=["text"])

    # Make a list of full text hits with associated summary document scores
    hit_sections = []
    min_hit_score = full_text_hit_score_threshold * full_text_response['hits']['max_score']

    if use_summary:
        for hit in full_text_response["hits"]["hits"]:
            for i in range(hit["_source"]["section"] - 1, hit["_source"]["section"] + 2):
                if "page" in hit["_source"]:
                    page = hit["_source"]["page"]
                else:
                    page = None
                if "section_heading" in hit["_source"]:
                    section_heading = hit["_source"]["section_heading"]
                else:
                    section_heading = None
                if i > 0 and hit["_score"] >= min_hit_score:
                    # If summary doc score exists for this full text hit then use that, else do not add this item
                    if hit['_source']['document'] in document_summary_high_scores:
                        document_score = summary_weight_over_full_text * document_summary_high_scores[hit["_source"]["document"]]                       
                        hit_sections.append(
                                {
                                    "document": hit["_source"]["document"],
                                    "page": page,
                                    "section_heading": section_heading,
                                    "section": i,
                                    "document_score": hit["_score"] + document_score
                                }
                            )
    else:
        for hit in full_text_response["hits"]["hits"]:
            for i in range(hit["_source"]["section"] - 2, hit["_source"]["section"] + 3):
                if "page" in hit["_source"]:
                    page = hit["_source"]["page"]
                else:
                    page = None
                if "section_heading" in hit["_source"]:
                    section_heading = hit["_source"]["section_heading"]
                else:
                    section_heading = None
                if i > 0 and hit["_score"] >= min_hit_score:
                    hit_sections.append(
                            {
                                "document": hit["_source"]["document"],
                                "page": page,
                                "section_heading": section_heading,
                                "section": i,
                                "document_score": hit["_score"],
                            }
                        )

    # Sort the hit list by score high to low
    sorted_list = sorted(hit_sections, key=lambda x: (x['document_score'] * -1, x['document'], x['page'], x['section_heading'], x['section']))
    
    # Remove the scores and eliminate duplicates in the sorted hit list
    sorted_list_without_scores = []

    for i in sorted_list:
        sorted_list_without_scores.append(
            {
                "document": i['document'],
                "section": i['section']
            }
        )    
    deduplicated_list = {frozenset(item.items()) : item for item in sorted_list_without_scores}.values()

    # Retrieve the text of the each section in the hit list and concatenate into a single string as RAG context for the LLM
    rag_text = ""
    reference_list = []

    for i in sorted_list:
        query = {
            'size': 1,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "document": i["document"]
                            }
                        },
                        {
                            "match": {
                                "section": i["section"]
                            }
                        }
                    ]
                }
            }
        }
        response2 = opensearch_client.search(
            body = query,
            index = full_text_index_name
        )

        # Check to make sure there is a value and that adding this hit will not make the RAG text exceed the maximum length
        if len(response2["hits"]["hits"]) > 0 and (len(rag_text) + len(response2["hits"]["hits"][0]["_source"]["text"]) < max_length_rag_text):
            # Add the text from this hit to the RAG text
            rag_text += response2["hits"]["hits"][0]["_source"]["text"]
            # Add the reference
            reference = {
                "document": i['document'],
                "page": i['page'],
                "section_heading": i['section_heading']
            }
            reference_list.append(reference)
        
    # Get the references used to create the RAG text
    reference_text = ""

    reference_list_dedupe = {frozenset(item.items()) : item for item in reference_list}.values()
    for item in reference_list_dedupe:
        # Default document reference is the S3 key
        document = item['document']
        # If use_s3_key_to_weblink_conversion is set then convert document to a weblink
        if use_s3_key_to_weblink_conversion:
            if document.startswith(s3_key_prefix_to_remove):
                document = document.replace(s3_key_prefix_to_remove, weblink_prefix, 1)
            if document.endswith(s3_key_suffix_to_remove):
                #document = document.replace(s3_key_suffix_to_remove, weblink_suffix, 1)
                document = document[:-len(s3_key_suffix_to_remove)] + weblink_suffix

        # If there is a page reference, then include it
        if item["page"] is not None:
            reference_text += "\n- " + document + " page: " + str(item['page'])
        # If there is a section heading reference and weblink conversion is selected then add it to URL
        elif item["section_heading"] is not None and use_s3_key_to_weblink_conversion:
            reference_text += "\n- " + document + "#" + quote(str(item['section_heading'])) + " "
        # If there is a section heading reference and weblink conversion is not selected then add it as text
        elif item["section_heading"] is not None and use_s3_key_to_weblink_conversion is False:
            reference_text += "\n- " + document + " heading: " + str(item['section_heading'])
        else:
            reference_text += "\n- " + document

    return(rag_text, reference_text)