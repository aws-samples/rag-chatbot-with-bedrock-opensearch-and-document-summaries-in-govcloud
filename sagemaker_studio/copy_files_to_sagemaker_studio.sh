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