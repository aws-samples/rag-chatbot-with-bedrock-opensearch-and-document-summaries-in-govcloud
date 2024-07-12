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
from datetime import datetime

def opensearch_query(query_text, opensearch_model_id, config_dict):
    # Get the OpenSearch host, index name and model ID from envionment variables
    summary_index_name = os.environ['OPENSEARCH_SUMMARY_INDEX']
    full_text_index_name = os.environ['OPENSEARCH_FULL_TEXT_INDEX']
    date_index_name = os.environ['OPENSEARCH_DATE_INDEX']
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
    if config_dict['use_summary']:
        query={
            "_source": {
                "excludes": [ "text_embedding" ]
            },
            "size": 30,
            "query": {
                "neural": {
                    "text_embedding": {
                    "query_text": query_text,
                    "model_id": opensearch_model_id,
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
    if config_dict['use_summary']:
        doc_list = []
        min_summary_hit_score = config_dict['summary_hit_score_threshold'] * summary_response['hits']['max_score']

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
                "model_id": opensearch_model_id,
                "k": 30
                }
            }
        }
    }

    full_text_response = opensearch_client.search(index=full_text_index_name, 
                           body=query,
                           stored_fields=["text"])

    # If use_date parameter is true, get the date of each document with a search hit and calculate its age in days
    document_age_list = []
    if config_dict['use_date']:
        for full_text_hit in full_text_response["hits"]["hits"]:
            if not any(d['document'] == full_text_hit["_source"]["document"] for d in document_age_list):
                query={
                    "query": {
                        "match_phrase": {
                            "document": full_text_hit["_source"]["document"]
                        }
                    }
                }
                date_response = opensearch_client.search(index=date_index_name, body=query)
                document_date = date_response["hits"]["hits"][0]["_source"]["document_date"][:10]
                days_old = (datetime.now() - datetime.strptime(document_date, "%Y-%m-%d")).days
                document_age_list.append(
                    {
                        "document": full_text_hit["_source"]["document"],
                        "date": document_date,
                        "days_old": days_old
                    }
                )
    
    # If use_date parameter is true, deduct points on scores of each full text hit based on the age of the document and parameter points to deduct per day old 
    if config_dict['use_date']:
        for hit in full_text_response["hits"]["hits"]:
            days_old = list(filter(lambda doc: doc['document'] == hit['_source']['document'], document_age_list))[0]["days_old"]
            points_to_deduct = config_dict['points_deduct_per_day_old'] * days_old
            if hit["_score"] > points_to_deduct:
                hit["_score"] = hit["_score"] - (config_dict['points_deduct_per_day_old'] * days_old)
            else:
                hit["_score"] = 0
    
    # Make a list of full text hits with associated summary document scores
    hit_sections = []
    min_hit_score = config_dict['full_text_hit_score_threshold'] * min(full_text_response["hits"]["hits"], key=lambda x:x['_score'])["_score"]

    if config_dict['use_summary']:
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
                        document_score = config_dict['summary_weight_over_full_text'] * document_summary_high_scores[hit["_source"]["document"]]
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
            for i in range(hit["_source"]["section"] - 3, hit["_source"]["section"] + 4):
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
        if len(response2["hits"]["hits"]) > 0 and (len(rag_text) + len(response2["hits"]["hits"][0]["_source"]["text"]) < config_dict['max_length_rag_text']):
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
        if config_dict['use_s3_key_to_weblink_conversion']:
            if document.startswith(config_dict['s3_key_prefix_to_remove']):
                document = document.replace(config_dict['s3_key_prefix_to_remove'], config_dict['weblink_prefix'], 1)
            if document.endswith(config_dict['s3_key_suffix_to_remove']):
                document = document[:-len(config_dict['s3_key_suffix_to_remove'])] + weblink_suffix

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