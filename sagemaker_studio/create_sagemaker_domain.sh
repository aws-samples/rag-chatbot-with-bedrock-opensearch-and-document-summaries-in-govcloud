#!/bin/bash
echo "Retrieving output values from CloudFormation stack chatbot-demo..."
REGION=`aws cloudformation describe-stacks --region us-gov-west-1 --query "Stacks[?StackName=='chatbot-demo'][].Outputs[?OutputKey=='Region'].OutputValue" --output text`
EXECUTION_ROLE_ARN=`aws cloudformation describe-stacks --region us-gov-west-1 --query "Stacks[?StackName=='chatbot-demo'][].Outputs[?OutputKey=='SageMakerExecutionRoleArn'].OutputValue" --output text`
VPC_ID=`aws cloudformation describe-stacks --region us-gov-west-1 --query "Stacks[?StackName=='chatbot-demo'][].Outputs[?OutputKey=='VPC'].OutputValue" --output text`
SUBNET_ID=`aws cloudformation describe-stacks --region us-gov-west-1 --query "Stacks[?StackName=='chatbot-demo'][].Outputs[?OutputKey=='PrivateSubnet1'].OutputValue" --output text`
SECURITY_GROUP_ID=`aws cloudformation describe-stacks --region us-gov-west-1 --query "Stacks[?StackName=='chatbot-demo'][].Outputs[?OutputKey=='SageMakerSecurityGroup'].OutputValue" --output text`
echo "Creating SageMaker chatbot-demo-domain..."
aws --region $REGION sagemaker create-domain --domain-name "chatbot-demo-domain" --vpc-id $VPC_ID --subnet-ids $SUBNET_ID --app-network-access-type VpcOnly --auth-mode IAM --default-user-settings "ExecutionRole= ${EXECUTION_ROLE_ARN},SecurityGroups=${SECURITY_GROUP_ID}"
echo "Open SageMaker Domains in the AWS console and wait for the domain status to change from Pending to InService.  Then you may create a user."