# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Setup script to prepare to run streamlit web user interface in SageMaker Studio

# Create and activate Conda environment with Python 3.11
conda create -y --name my_python_311 python=3.11 pip
conda activate my_python_311

# Install dependencies
pip install --no-cache-dir -r requirements.txt
sudo yum install -y iproute
sudo yum install -y jq
sudo yum install -y lsof

# Make the run and cleanup scripts executable
chmod +x ./run.sh
chmod +x ./cleanup.sh