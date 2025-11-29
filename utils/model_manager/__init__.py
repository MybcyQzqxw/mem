#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型下载和管理模块
提供从各种源下载预训练模型的通用功能
"""

from .downloader import (
    download_embedding_model,
    check_model_exists
)

from .llm_helper import (
    ensure_models_directory,
    find_gguf_models,
    configure_llm_model,
    list_available_models,
    validate_gguf_model,
    update_env_file,
    get_model_info
)

__all__ = [
    # Downloader functions
    'download_embedding_model',
    'check_model_exists',
    # LLM helper functions
    'ensure_models_directory',
    'find_gguf_models',
    'configure_llm_model',
    'list_available_models',
    'validate_gguf_model',
    'update_env_file',
    'get_model_info',
]
