# Building container images
## RAG Chatbot with Amazon Bedrock, OpenSearch and document summaries in AWS GovCloud

## Container build overview

Running the chatbot in production-like mode requires three container images to be built and stored in Amazon Elastic Container Registry (ECR) in the account where the chatbot will be deployed.

The three containers required are:

- **Lambda OpenSearch setup** - Used by a Lambda function that runs once when the chatbot demo CloudFormation stack is complete to perform initial setup of the OpenSearch domain.  The initial setup consists of registering the embedding model and creating the indices in OpenSearch.
- **Lambda index** - Used by a Lambda function that handles events in the S3 document repository bucket to index new documents and remove deleted documents from the OpenSearch indices.
- **Streamlit web front end** - Used in Elastic Container Service (ECS) to run the Streamlit-based web user interface.

To enable container build, a CloudFormation template is provided at ```/containers/chatbot_demo_container_build_cfn.yml```.  This will deploy AWS CodeBuild projects and ECR repositories to build and store each of the three container images required.  The CodeBuild projects are configured to download the source from this project's GitHub repository, build the container image, and store it in ECR.

Alternatively, the user may choose to build the container images using another method as long as the container images are stored in ECR repositories with names that match the corresponding repository name parameters in the stack built by the main template at ```/containers/chatbot_demo_cfn.yml```.
