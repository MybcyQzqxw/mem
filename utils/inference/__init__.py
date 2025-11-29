#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推理引擎模块
提供LLM推理运行时和响应解析功能
"""

from .local_backend import LocalLLM, get_local_llm
from .response_parser import parse_json_response, extract_json_from_text, safe_json_loads

__all__ = [
    'LocalLLM',
    'get_local_llm',
    'parse_json_response',
    'extract_json_from_text',
    'safe_json_loads',
]
