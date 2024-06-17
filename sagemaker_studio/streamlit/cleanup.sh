# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Script to to kill resources after running streamlit web user interface in SageMaker Studio

#!/bin/bash

# List all processes running from streamlit
echo "Processes running from streamlit:"
ps -Al | grep streamlit

# Kill all processes running from streamlit
echo "Killing all processes running from streamlit"
pkill -9 streamlit

# Delete the file temp.txt
rm temp.txt