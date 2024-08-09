# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import streamlit as st
import json
from opensearch_retrieve_helper import opensearch_query
from get_opensearch_model_id import opensearch_model_id
import logging
from rag_search_config_helper import read_rag_search_config

st.title("Question and Answer Bot")

# Get the OpenSearch model ID
opensearch_model_id = opensearch_model_id()

# Get the current region
session = boto3.session.Session()
region_name = session.region_name

# Get the values from rag_search.cfg
config_dict = read_rag_search_config()

# Create the Bedrock runtime
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=region_name, 
)

# Get the Bedrock Guardrails parameters from CloudFormation
stack_name = "chatbot-demo"
cf_client = boto3.client('cloudformation')
response = cf_client.describe_stacks(StackName=stack_name)
outputs = response["Stacks"][0]["Outputs"]
bedrock_guardrail_id = list(filter(lambda outputs: outputs['OutputKey'] == 'BedrockGuardrailId', outputs))[0]["OutputValue"]
bedrock_guardrail_version = list(filter(lambda outputs: outputs['OutputKey'] == 'BedrockGuardrailVersion', outputs))[0]["OutputValue"]
stack_parameters = response["Stacks"][0]["Parameters"]
bedrock_guardrails_block_message = list(filter(lambda stack_parameters: stack_parameters['ParameterKey'] == 'BedrockGuardrailsBlockMessage', stack_parameters))[0]["ParameterValue"]

# Build the user interface
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about your documents."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query_text := st.chat_input("Enter your question"):
    st.session_state.messages.append({"role": "user", "content": query_text})
    with st.chat_message("user"):
        st.markdown(query_text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Query OpenSearch
            rag_text, reference_text = opensearch_query(query_text, opensearch_model_id, config_dict)

            # Prepare the request to the model
            prompt_template = (
                        "Context information is below.\n"
                        "---------------------\n"
                        "{context}\n"
                        "---------------------\n"
                        "You are an assistant for answering questions. "
                        "You are given the extracted parts long documents as context and a question. "
                        "Provide a conversational answer. "
                        "If you don't know the answer, just say 'I do not know.' Don't make up an answer.\n"
                        "Query: {query_text}\n"
                        "Answer: "
                        )
            prompt_data = prompt_template.replace("{context}", rag_text).replace("{query_text}", query_text)

            # If config file says use Titan Text Express, invoke that model
            if config_dict['bedrock_model_id'] == "amazon.titan-text-express-v1":
                text_gen_config = {
                    "maxTokenCount": config_dict['max_token_count'],
                    "stopSequences": [], 
                    "temperature": config_dict['temperature'],
                    "topP": config_dict['top_p']
                }
                accept = 'application/json' 
                content_type = 'application/json'

                body = json.dumps({
                    "inputText": prompt_data,
                    "textGenerationConfig": text_gen_config
                })

                bedrock_response = bedrock_runtime.invoke_model(
                    modelId = config_dict['bedrock_model_id'], 
                    body = body, 
                    accept = accept, 
                    contentType = content_type,
                    guardrailIdentifier = bedrock_guardrail_id,
                    guardrailVersion = bedrock_guardrail_version
                )
                response_body = json.loads(bedrock_response.get('body').read())
                output_text = response_body.get('results')[0].get('outputText')

            # If config file says use a Llama 3 model, invoke that model
            elif "meta.llama3" in config_dict['bedrock_model_id']:
                native_request = {
                    "prompt": prompt_data,
                    "max_gen_len": config_dict['max_gen_len'],
                    "temperature": config_dict['temperature'],
                }
                request = json.dumps(native_request)
                bedrock_response = bedrock_runtime.invoke_model(
                    modelId = config_dict['bedrock_model_id'],
                    body = request,
                    guardrailIdentifier = bedrock_guardrail_id,
                    guardrailVersion = bedrock_guardrail_version
                )
                response_body = json.loads(bedrock_response["body"].read())
                output_text = response_body["generation"]

            # Invalid model specified in config file
            else:
                output_text = "Invalid model in config file."

            st.markdown(output_text)
#            st.write(output_text)
            if output_text != bedrock_guardrails_block_message:
                with st.expander("References"):
                    st.write(reference_text)
    st.session_state.messages.append({"role": "assistant", "content": output_text})