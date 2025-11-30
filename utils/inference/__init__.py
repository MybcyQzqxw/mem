#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推理引擎模块
提供LLM推理运行时和响应解析功能
"""

from .local_backend import LocalLLM, get_local_llm
from .response_parser import parse_json_response, extract_json_from_text, safe_json_loads


def call_local_llm(model_path: str, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
    """便捷函数：调用本地LLM
    
    Args:
        model_path: 模型路径
        system_prompt: 系统提示词
        user_prompt: 用户输入
        max_tokens: 最大token数
        
    Returns:
        LLM生成的文本
    """
    llm = get_local_llm(model_path)
    return llm.generate(system_prompt, user_prompt, max_tokens=max_tokens)


__all__ = [
    'LocalLLM',
    'get_local_llm',
    'call_local_llm',
    'parse_json_response',
    'extract_json_from_text',
    'safe_json_loads',
]
