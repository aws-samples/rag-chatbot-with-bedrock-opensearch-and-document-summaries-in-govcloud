# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Setup script to prepare to run streamlit web user interface in SageMaker Studio

pip install --no-cache-dir -r requirements.txt
sudo yum install -y iproute
sudo yum install -y jq
sudo yum install -y lsof