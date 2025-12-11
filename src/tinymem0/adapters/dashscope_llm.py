#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dashscope（阿里云）LLM适配器
提供与阿里云通义千问API交互的特定功能
"""

import os
from typing import Optional, List, Dict, Any
from dashscope import Generation


def extract_llm_response_content(response) -> Optional[str]:
    """
    从Dashscope LLM响应中提取内容
    
    Args:
        response: Dashscope API响应对象
        
    Returns:
        提取的响应内容，如果失败返回None
    """
    if not response or response.status_code != 200:
        return None
    
    # 检查响应结构，兼容不同的返回格式
    if hasattr(response.output, 'choices') and response.output.choices:
        return response.output.choices[0].message.content
    elif hasattr(response.output, 'text'):
        return response.output.text
    else:
        print("无法获取响应内容")
        return None


def call_llm_with_prompt(model: str, system_prompt: str, user_content: str) -> Optional[str]:
    """
    调用阿里云LLM API并处理响应
    注意：此函数仅处理云端API调用，不处理本地模型
    本地模型的调用应在上层使用 utils.inference.call_local_llm
    
    Args:
        model: 阿里云模型名称
        system_prompt: 系统提示词
        user_content: 用户内容
        
    Returns:
        处理后的响应内容
    """
    try:
        # 构建符合类型的消息列表
        messages: List[Dict[str, Any]] = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
        response = Generation.call(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            result_format='message'
        )
        
        return extract_llm_response_content(response)
    except Exception as e:
        print(f"阿里云LLM调用异常: {e}")
        return None


def handle_llm_error(response, operation_name: str = "操作"):
    """
    处理Dashscope LLM错误
    
    Args:
        response: LLM响应对象
        operation_name: 操作名称
    """
    error_msg = f"{operation_name}失败: {response.status_code if response else 'No response'}"
    print(error_msg)
    if response and hasattr(response, 'message'):
        print(f"错误信息: {response.message}")
