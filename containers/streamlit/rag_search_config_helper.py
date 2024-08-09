# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import configparser

def read_rag_search_config():
    config_dict = {}
    config = configparser.ConfigParser()
    config.read('rag_search.cfg')
    # Read the RAG Common parameters
    config_dict['max_length_rag_text'] = config['RAG Common'].getint('MaxLengthRagText', 15000)
    config_dict['full_text_hit_score_threshold'] = config['RAG Common'].getfloat('FullTextHitScoreThreshold', 0.5)
    # Read the RAG Summary parameters
    config_dict['use_summary'] = config['RAG Summary'].getboolean('UseSummary', True)
    config_dict['summary_weight_over_full_text'] = config['RAG Summary'].getfloat('SummaryWeightOverFullText', 1.5)
    config_dict['summary_hit_score_threshold'] = config['RAG Summary'].getfloat('SummaryHitScoreThreshold', 0.9)
    # Read the RAG Date parameters
    config_dict['use_date'] = config['RAG Date'].getboolean('UseDate', True)
    config_dict['years_until_no_value'] = config['RAG Date'].getfloat('YearsUntilNoValue', 8)
    # Read the S3 Key to Weblink Conversion parameters
    config_dict['use_s3_key_to_weblink_conversion'] = config['S3 Key to Weblink Conversion'].getboolean('UseS3KeyToWeblinkConversion', False)
    config_dict['s3_key_prefix_to_remove'] = config['S3 Key to Weblink Conversion'].get('S3KeyPrefixToRemove')
    config_dict['weblink_prefix'] = config['S3 Key to Weblink Conversion'].get('WeblinkPrefix')
    config_dict['s3_key_suffix_to_remove'] = config['S3 Key to Weblink Conversion'].get('S3KeySuffixToRemove')
    config_dict['weblink_suffix'] = config['S3 Key to Weblink Conversion'].get('WeblinkSuffix')
    # Read the Text Gen parameters
    config_dict['max_token_count'] = config['Text Gen'].getint('MaxTokenCount', 350)
    config_dict['temperature'] = config['Text Gen'].getint('Temperature', 0)
    config_dict['top_p'] = config['Text Gen'].getint('TopP', 1)
    config_dict['max_gen_len'] = config['Text Gen'].getint("MaxGenLen", 512)
    config_dict['bedrock_model_id'] = config['Text Gen'].get('BedrockModelId', 'amazon.titan-text-express-v1')
    # Clamp the values from the config file to within limits
    config_dict = clamp_rag_search_config(config_dict)
    # Set points to deduct per day based on years_until_no_value
    config_dict['points_deduct_per_day_old'] = 1/(365 * config_dict['years_until_no_value'])
    return(config_dict)
    
def clamp_rag_search_config(config_dict):
    clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
    config_dict['max_length_rag_text'] = clamp(config_dict['max_length_rag_text'], 100, 15000)
    config_dict['full_text_hit_score_threshold'] = clamp(config_dict['full_text_hit_score_threshold'], 0, 1)
    config_dict['summary_weight_over_full_text'] = clamp(config_dict['summary_weight_over_full_text'], 1, 5)
    config_dict['summary_hit_score_threshold'] = clamp(config_dict['summary_hit_score_threshold'], 0, 1)
    config_dict['years_until_no_value'] = clamp(config_dict['years_until_no_value'], 0.01, 100)
    config_dict['max_token_count'] = clamp(config_dict['max_token_count'], 1, 8192)
    config_dict['temperature'] = clamp(config_dict['temperature'], 0, 1)
    config_dict['top_p'] = clamp(config_dict['top_p'], 0, 1)
    return(config_dict)