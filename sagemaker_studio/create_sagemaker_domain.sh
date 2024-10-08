# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## Script to create SageMaker Studio domain for the chatbot in dev/test mode

# After creating the CloudFormation stack at the address below in dev/test mode, run this script in CloudShell to create the SageMaker domain
# https://github.com/aws-samples/rag-chatbot-with-bedrock-opensearch-and-document-summaries-in-govcloud/blob/main/cloudformation/chatbot_demo_cfn.yml

#!/bin/bash
STACK_NAME="chatbot-demo"
CURRENT_REGION=`aws configure list | grep region | awk '{print $2}'`
echo "Retrieving output values from CloudFormation stack $STACK_NAME..."
EXECUTION_ROLE_ARN=`aws cloudformation describe-stacks --region $CURRENT_REGION --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='SageMakerExecutionRoleArn'].OutputValue" --output text`
VPC_ID=`aws cloudformation describe-stacks --region $CURRENT_REGION --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='VPC'].OutputValue" --output text`
SUBNET_ID=`aws cloudformation describe-stacks --region $CURRENT_REGION --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='PrivateSubnet1'].OutputValue" --output text`
SECURITY_GROUP_ID=`aws cloudformation describe-stacks --region $CURRENT_REGION --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='SageMakerSecurityGroup'].OutputValue" --output text`
echo "Creating SageMaker chatbot-demo-domain..."
aws --region $CURRENT_REGION sagemaker create-domain --domain-name "chatbot-demo-domain" --vpc-id $VPC_ID --subnet-ids $SUBNET_ID --app-network-access-type VpcOnly --auth-mode IAM --default-user-settings "ExecutionRole= ${EXECUTION_ROLE_ARN},SecurityGroups=${SECURITY_GROUP_ID}"
echo "Open SageMaker Domains in the AWS console and wait for the domain status to change from Pending to InService.  Then you may create a user."