# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM public.ecr.aws/lambda/python:3.11
COPY requirements.txt .
COPY index_documents_helper.py .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}" --no-cache-dir
COPY app.py ${LAMBDA_TASK_ROOT}
CMD ["app.handler"]