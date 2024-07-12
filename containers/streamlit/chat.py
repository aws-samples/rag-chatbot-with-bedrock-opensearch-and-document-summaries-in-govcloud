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

#st.sidebar.success("Select a demo above.")

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

# Set the text gen config and parameters for the LLM
text_gen_config = {
    "maxTokenCount": config_dict['max_token_count'],
    "stopSequences": [], 
    "temperature": config_dict['temperature'],
    "topP": config_dict['top_p']
}
accept = 'application/json' 
content_type = 'application/json'

# Get the Bedrock Guardrails parameters from CloudFormation
stack_name = "chatbot-demo"
cf_client = boto3.client('cloudformation')
response = cf_client.describe_stacks(StackName=stack_name)
outputs = response["Stacks"][0]["Outputs"]
bedrock_guardrail_id = list(filter(lambda outputs: outputs['OutputKey'] == 'BedrockGuardrailId', outputs))[0]["OutputValue"]
bedrock_guardrail_version = list(filter(lambda outputs: outputs['OutputKey'] == 'BedrockGuardrailVersion', outputs))[0]["OutputValue"]
stack_parameters = response["Stacks"][0]["Parameters"]
bedrock_guardrails_block_message = list(filter(lambda stack_parameters: stack_parameters['ParameterKey'] == 'BedrockGuardrailsBlockMessage', stack_parameters))[0]["ParameterValue"]

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about your documents."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Query OpenSearch
            rag_text, reference_text = opensearch_query(prompt, opensearch_model_id, config_dict)

            # Prepare the request to the model
            prompt_template = '''Context - {context}\n\n\n\n
            Based only on the above context, answer this question - {query_text}'''
            prompt_data = prompt_template.replace("{context}", rag_text).replace("{query_text}", prompt)
            body = json.dumps({
                "inputText": prompt_data,
                "textGenerationConfig": text_gen_config
            })

            # Invoke model 
#            st.write(body)
            bedrock_response = bedrock_runtime.invoke_model(
                body=body, 
                modelId=config_dict['bedrock_model_id'], 
                accept=accept, 
                contentType=content_type,
                guardrailIdentifier=bedrock_guardrail_id,
                guardrailVersion=bedrock_guardrail_version
            )
            response_body = json.loads(bedrock_response.get('body').read())
            outputText = response_body.get('results')[0].get('outputText')
            
            st.markdown(outputText)
#            st.write(outputText)
#            st.write(response_body)
            if outputText != bedrock_guardrails_block_message:
                with st.expander("References"):
                    st.write(reference_text)
    st.session_state.messages.append({"role": "assistant", "content": outputText})