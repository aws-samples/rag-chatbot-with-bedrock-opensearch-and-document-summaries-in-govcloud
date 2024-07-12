# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

EXPOSE 8501

RUN adduser -u 5678 --disabled-password --gecos "" appuser

WORKDIR /home/appuser/app
COPY chat.py /home/appuser/app
COPY /pages/index_status.py /home/appuser/app/pages/index_status.py
COPY get_opensearch_model_id.py /home/appuser/app
COPY opensearch_retrieve_helper.py /home/appuser/app
COPY rag_search_config_helper.py /home/appuser/app
COPY rag_search.cfg /home/appuser/app

RUN chown -R appuser /home/appuser/app

USER appuser

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "chat.py", "--server.port=8501", "--server.address=0.0.0.0"]