#!/bin/bash
DOMAIN_ID=`aws sagemaker list-domains --query "Domains[?DomainName=='chatbot-demo-domain'].DomainId" --output text`
CURRENT_REGION=`aws configure list | grep region | awk '{print $2}'`
echo "Deleting SageMaker domain ID $DOMAIN_ID in region $CURRENT_REGION..."
aws --region $CURRENT_REGION sagemaker delete-domain --domain-id $DOMAIN_ID --retention-policy HomeEfsFileSystem=Delete
echo "Confirm the domain is deleted in the SageMaker console, then you can delete the CloudFormation stack."