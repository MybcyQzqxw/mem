#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型下载和管理模块
提供从各种源下载预训练模型的通用功能
"""

from .downloader import (
    download_embedding_model,
    check_model_exists,
    download_llm_model
)

from .local_llm_manager import (
    ensure_models_directory,
    find_gguf_models,
    find_safetensors_models,
    detect_model_format,
    configure_llm_model,
    list_available_models,
    validate_model,
    update_env_file,
    get_model_info,
    MODELS_BASE_DIR,
    GGUF_DIR,
    SAFETENSORS_DIR
)

__all__ = [
    # Downloader functions
    'download_embedding_model',
    'check_model_exists',
    'download_llm_model',
    # LLM helper functions
    'ensure_models_directory',
    'find_gguf_models',
    'find_safetensors_models',
    'detect_model_format',
    'configure_llm_model',
    'list_available_models',
    'validate_model',
    'update_env_file',
    'get_model_info',
    # Constants
    'MODELS_BASE_DIR',
    'GGUF_DIR',
    'SAFETENSORS_DIR',
]

