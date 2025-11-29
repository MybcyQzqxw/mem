#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具模块
提供跨项目可复用的工具函数和类，不依赖特定API或服务

子模块：
- inference: LLM推理引擎和响应解析
- evaluation: 评测指标计算
- model_manager: 模型下载和管理
"""

# 推理工具
from .inference.local_backend import LocalLLM, get_local_llm
from .inference.response_parser import (
    parse_json_response,
    extract_json_from_text,
    safe_json_loads
)

# 评测工具
from .evaluation.metrics import (
    calculate_f1,
    calculate_precision_recall,
    calculate_mrr,
    calculate_recall_at_k,
    normalize_text
)

# 模型管理工具
from .model_manager.downloader import (
    download_embedding_model,
    check_model_exists
)

__all__ = [
    # 推理工具
    'LocalLLM',
    'get_local_llm',
    'parse_json_response',
    'extract_json_from_text',
    'safe_json_loads',
    # 评测工具
    'calculate_f1',
    'calculate_precision_recall',
    'calculate_mrr',
    'calculate_recall_at_k',
    'normalize_text',
    # 模型工具
    'download_embedding_model',
    'check_model_exists',
]
