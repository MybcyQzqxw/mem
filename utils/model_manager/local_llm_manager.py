#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地LLM模型管理模块
提供本地模型的检测、验证和配置功能
支持GGUF和SafeTensors两种格式，分目录存储
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Literal


# 标准目录结构
MODELS_BASE_DIR = './models'
GGUF_DIR = './models/gguf'
SAFETENSORS_DIR = './models/safetensors'


def ensure_models_directory(
    models_dir: str = MODELS_BASE_DIR,
    create_subdirs: bool = True
) -> Path:
    """
    确保模型目录存在
    
    Args:
        models_dir: 基础模型目录路径
        create_subdirs: 是否创建格式子目录 (gguf/, safetensors/)
        
    Returns:
        模型目录的 Path 对象
    """
    path = Path(models_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    if create_subdirs:
        (path / 'gguf').mkdir(exist_ok=True)
        (path / 'safetensors').mkdir(exist_ok=True)
    
    return path


def find_gguf_models(models_dir: str = GGUF_DIR) -> List[Path]:
    """
    在指定目录中查找所有 GGUF 模型文件
    
    Args:
        models_dir: GGUF模型目录路径（默认: ./models/gguf）
        
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


def find_safetensors_models(models_dir: str = SAFETENSORS_DIR) -> List[Path]:
    """
    在指定目录中查找所有 SafeTensors 模型目录
    
    Args:
        models_dir: SafeTensors模型目录路径（默认: ./models/safetensors）
        
    Returns:
        SafeTensors 模型目录路径列表
    """
    path = Path(models_dir)
    if not path.exists():
        return []
    
    models = []
    for item in path.iterdir():
        if not item.is_dir():
            continue
        
        # 检查是否为有效的模型目录
        has_safetensors = any(
            f.name.endswith('.safetensors')
            for f in item.iterdir()
            if f.is_file()
        )
        has_config = (item / 'config.json').exists()
        
        if has_safetensors and has_config:
            models.append(item)
    
    return models


def detect_model_format(model_path: str) -> Literal['gguf', 'safetensors', 'unknown']:
    """
    检测模型格式
    
    Args:
        model_path: 模型路径（文件或目录）
        
    Returns:
        模型格式 ('gguf', 'safetensors', 'unknown')
    """
    path = Path(model_path)
    
    # 检测GGUF文件
    if path.is_file() and path.suffix.lower() == '.gguf':
        return 'gguf'
    
    # 检测SafeTensors目录
    if path.is_dir():
        has_safetensors = any(
            f.name.endswith('.safetensors')
            for f in path.iterdir()
            if f.is_file()
        )
        has_config = (path / 'config.json').exists()
        
        if has_safetensors and has_config:
            return 'safetensors'
    
    return 'unknown'


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


def get_model_info(model_path: Path, model_format: str = None) -> dict:
    """
    获取模型的基本信息
    
    Args:
        model_path: 模型文件或目录路径
        model_format: 模型格式（可选，自动检测）
        
    Returns:
        包含模型信息的字典
    """
    if model_format is None:
        model_format = detect_model_format(str(model_path))
    
    info = {
        'name': model_path.name,
        'path': str(model_path),
        'format': model_format,
    }
    
    if model_format == 'gguf':
        stat = model_path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        info['size_mb'] = round(size_mb, 2)
        info['size_str'] = (
            f"{size_mb / 1024:.2f} GB" if size_mb > 1024
            else f"{size_mb:.2f} MB"
        )
    
    elif model_format == 'safetensors':
        # 计算目录总大小
        total_size = sum(
            f.stat().st_size
            for f in model_path.rglob('*')
            if f.is_file()
        )
        size_mb = total_size / (1024 * 1024)
        info['size_mb'] = round(size_mb, 2)
        info['size_str'] = (
            f"{size_mb / 1024:.2f} GB" if size_mb > 1024
            else f"{size_mb:.2f} MB"
        )
    
    return info


def list_available_models(
    gguf_dir: str = GGUF_DIR,
    safetensors_dir: str = SAFETENSORS_DIR
) -> dict:
    """
    列出所有可用的模型及其信息
    
    Args:
        gguf_dir: GGUF模型目录
        safetensors_dir: SafeTensors模型目录
        
    Returns:
        包含两种格式模型信息的字典
    """
    gguf_models = find_gguf_models(gguf_dir)
    safetensors_models = find_safetensors_models(safetensors_dir)
    
    return {
        'gguf': [get_model_info(m, 'gguf') for m in gguf_models],
        'safetensors': [get_model_info(m, 'safetensors') for m in safetensors_models]
    }


def validate_model(model_path: str) -> Tuple[bool, str, str]:
    """
    验证模型文件或目录是否有效
    
    Args:
        model_path: 模型路径
        
    Returns:
        (是否有效, 模型格式, 错误信息)
    """
    path = Path(model_path)
    
    if not path.exists():
        return False, 'unknown', f"路径不存在: {model_path}"
    
    model_format = detect_model_format(model_path)
    
    if model_format == 'gguf':
        if not path.is_file():
            return False, 'gguf', f"GGUF模型应该是文件: {model_path}"
        
        # 检查文件大小
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb < 10:
            return False, 'gguf', f"文件太小 ({size_mb:.2f} MB)，可能无效"
        
        return True, 'gguf', ""
    
    elif model_format == 'safetensors':
        if not path.is_dir():
            return False, 'safetensors', f"SafeTensors模型应该是目录: {model_path}"
        
        return True, 'safetensors', ""
    
    else:
        return False, 'unknown', (
            f"无法识别的模型格式: {model_path}\n"
            f"GGUF模型应该是 .gguf 文件\n"
            f"SafeTensors模型目录应包含 .safetensors 文件和 config.json"
        )

