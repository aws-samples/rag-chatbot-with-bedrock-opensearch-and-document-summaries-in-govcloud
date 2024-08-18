# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## Script to delete SageMaker Studio domain for cleanup of the chatbot in dev/test mode

# After you are finished running the chatbot at the address below in dev/test mode, run this script in CloudShell to delete the SageMaker domain
# https://github.com/aws-samples/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/blob/main/cloudformation/chatbot_demo_cfn.yml

#!/bin/bash
DOMAIN_ID=`aws sagemaker list-domains --query "Domains[?DomainName=='chatbot-demo-domain'].DomainId" --output text`
CURRENT_REGION=`aws configure list | grep region | awk '{print $2}'`
echo "Deleting SageMaker domain ID $DOMAIN_ID in region $CURRENT_REGION..."
aws --region $CURRENT_REGION sagemaker delete-domain --domain-id $DOMAIN_ID --retention-policy HomeEfsFileSystem=Delete
echo "Confirm the domain is deleted in the SageMaker console, then you can delete the CloudFormation stack."