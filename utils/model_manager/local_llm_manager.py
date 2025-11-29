#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 模型辅助模块
提供本地 GGUF 模型的检测、配置和管理功能
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple


def ensure_models_directory(models_dir: str = './models') -> Path:
    """
    确保模型目录存在
    
    Args:
        models_dir: 模型目录路径
        
    Returns:
        模型目录的 Path 对象
    """
    path = Path(models_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_gguf_models(models_dir: str = './models') -> List[Path]:
    """
    在指定目录中查找所有 GGUF 模型文件
    
    Args:
        models_dir: 模型目录路径
        
    Returns:
        GGUF 模型文件路径列表
    """
    path = Path(models_dir)
    if not path.exists():
        return []
    
    return [
        p for p in path.iterdir() 
        if p.is_file() and p.suffix.lower() == '.gguf'
    ]


def update_env_file(
    key: str, 
    value: str, 
    env_file: str = '.env',
    create_if_missing: bool = True
) -> bool:
    """
    更新或添加环境变量到 .env 文件
    
    Args:
        key: 环境变量名
        value: 环境变量值
        env_file: .env 文件路径
        create_if_missing: 如果文件不存在是否创建
        
    Returns:
        操作是否成功
    """
    env_path = Path(env_file)
    
    try:
        # 读取现有内容
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding='utf-8').splitlines()
        elif not create_if_missing:
            return False
        
        # 查找并更新或添加
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f'{key}='):
                new_lines.append(f'{key}={value}')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f'{key}={value}')
        
        # 写回文件
        env_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"❌ 更新 .env 文件失败: {e}")
        return False


def configure_llm_model(
    model_path: str,
    env_file: str = '.env'
) -> bool:
    """
    配置 LLM 模型路径到环境变量
    
    Args:
        model_path: 模型文件路径
        env_file: .env 文件路径
        
    Returns:
        配置是否成功
    """
    success = update_env_file('LOCAL_MODEL_PATH', model_path, env_file)
    
    if success:
        print(f"✅ 已将 LOCAL_MODEL_PATH 写入 {env_file}")
        print(f"   路径: {model_path}")
    
    return success


def get_model_info(model_path: Path) -> dict:
    """
    获取 GGUF 模型的基本信息
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        包含模型信息的字典
    """
    stat = model_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    
    return {
        'name': model_path.name,
        'path': str(model_path),
        'size_mb': round(size_mb, 2),
        'size_str': f"{size_mb / 1024:.2f} GB" if size_mb > 1024 else f"{size_mb:.2f} MB"
    }


def list_available_models(models_dir: str = './models') -> List[dict]:
    """
    列出所有可用的 GGUF 模型及其信息
    
    Args:
        models_dir: 模型目录路径
        
    Returns:
        模型信息列表
    """
    models = find_gguf_models(models_dir)
    return [get_model_info(model) for model in models]


def validate_gguf_model(model_path: str) -> Tuple[bool, str]:
    """
    验证 GGUF 模型文件是否有效
    
    Args:
        model_path: 模型文件路径
        
    Returns:
        (是否有效, 错误信息)
    """
    path = Path(model_path)
    
    if not path.exists():
        return False, f"文件不存在: {model_path}"
    
    if not path.is_file():
        return False, f"不是文件: {model_path}"
    
    if path.suffix.lower() != '.gguf':
        return False, f"不是 .gguf 文件: {model_path}"
    
    # 检查文件大小（GGUF 模型通常至少几百 MB）
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb < 10:
        return False, f"文件太小 ({size_mb:.2f} MB)，可能不是有效的模型"
    
    return True, ""
