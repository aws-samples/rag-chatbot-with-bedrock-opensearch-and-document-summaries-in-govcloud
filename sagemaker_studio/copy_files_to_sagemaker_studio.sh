# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## Script to copy cloned repository files in SageMaker Studio folder /chatbot to run in dev/test mode

# Read the full readme at the address below.  Create the stack in dev/test mode.
# In SageMaker Studio, clone the repository at the address below.  Then run this script in a Studio terminal to copy the files needed to run the chatbot.
# https://github.com/aws-samples/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/blob/main/cloudformation/chatbot_demo_cfn.yml

#!/bin/bash
mkdir /home/sagemaker-user/chatbot
cd /home/sagemaker-user/chatbot
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/sagemaker_studio/notebooks/* .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/sagemaker_studio/streamlit/* .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/lambda_index/index_documents_helper.py .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/chat.py .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/get_opensearch_model_id.py .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/opensearch_retrieve_helper.py .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/rag_search_config_helper.py .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/rag_search.cfg .
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/requirements.txt .
mkdir /home/sagemaker-user/chatbot/pages
cd /home/sagemaker-user/chatbot/pages
cp /home/sagemaker-user/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/containers/streamlit/pages/index_status.py .
echo Done