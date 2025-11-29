#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型下载工具
提供从各种源下载预训练模型的通用功能
"""

import os
import sys
from typing import Optional


def download_embedding_model(model_id: str = 'AI-ModelScope/bge-small-zh-v1.5', 
                             cache_dir: str = './embedding_models',
                             source: str = 'modelscope') -> str:
    """
    下载嵌入模型（通用函数）
    
    支持从多个源下载模型：
    - ModelScope: 中国区友好，适合下载中文模型
    - HuggingFace: 国际主流模型库
    
    Args:
        model_id: 模型ID（格式依赖于source）
        cache_dir: 本地缓存目录
        source: 下载源 ('modelscope' 或 'huggingface')
        
    Returns:
        下载后的模型本地路径
        
    Raises:
        ImportError: 缺少必要的依赖包
        RuntimeError: 下载失败
        
    Examples:
        >>> # 从ModelScope下载
        >>> path = download_embedding_model('AI-ModelScope/bge-small-zh-v1.5')
        
        >>> # 从HuggingFace下载
        >>> path = download_embedding_model(
        ...     'sentence-transformers/all-MiniLM-L6-v2',
        ...     source='huggingface'
        ... )
    """
    # 确保缓存目录存在
    os.makedirs(cache_dir, exist_ok=True)
    
    # 检查模型是否已存在
    model_path = os.path.join(cache_dir, model_id)
    if os.path.exists(model_path):
        print(f"✅ 模型已存在: {model_path}")
        return model_path
    
    print(f"📥 开始下载模型: {model_id}")
    print(f"📁 下载目录: {cache_dir}")
    print(f"🌐 下载源: {source}")
    
    try:
        if source == 'modelscope':
            return _download_from_modelscope(model_id, cache_dir)
        elif source == 'huggingface':
            return _download_from_huggingface(model_id, cache_dir)
        else:
            raise ValueError(f"不支持的下载源: {source}")
            
    except ImportError as e:
        print(f"❌ 错误: 缺少必要的依赖包")
        print(f"详细信息: {e}")
        if source == 'modelscope':
            print("请运行: pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple")
        elif source == 'huggingface':
            print("请运行: pip install huggingface_hub")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        raise RuntimeError(f"模型下载失败: {e}")


def _download_from_modelscope(model_id: str, cache_dir: str) -> str:
    """从ModelScope下载模型（内部函数）"""
    from modelscope import snapshot_download
    
    downloaded_path = snapshot_download(
        model_id=model_id,
        cache_dir=cache_dir,
        revision='master'
    )
    
    print(f"✅ 模型下载完成: {downloaded_path}")
    return downloaded_path


def _download_from_huggingface(model_id: str, cache_dir: str) -> str:
    """从HuggingFace下载模型（内部函数）"""
    from huggingface_hub import snapshot_download
    
    downloaded_path = snapshot_download(
        repo_id=model_id,
        cache_dir=cache_dir,
        local_dir=os.path.join(cache_dir, model_id)
    )
    
    print(f"✅ 模型下载完成: {downloaded_path}")
    return downloaded_path


def download_llm_model(
    model_id: str,
    cache_dir: str = './models',
    model_format: str = 'gguf'
) -> str:
    """
    LLM模型下载（当前为占位函数，需手动下载）
    
    由于LLM模型体积巨大(3-20GB+)且有多种量化版本，
    当前版本需要用户手动下载模型。
    
    Args:
        model_id: 模型ID
        cache_dir: 缓存目录
        model_format: 模型格式 ('gguf' 或 'safetensors')
        
    Returns:
        下载后的模型路径
        
    Raises:
        NotImplementedError: 当前版本暂不支持自动下载
        
    推荐下载源和步骤:
    
    ==== GGUF 格式模型 (量化，内存占用低) ====
    
    1. HuggingFace GGUF模型库:
       https://huggingface.co/models?library=gguf
       
       推荐模型:
       - Qwen2-7B-Instruct-GGUF (中文优化)
       - Mistral-7B-Instruct-GGUF (通用性好)
       - Llama-3-8B-Instruct-GGUF (Meta官方)
       
       量化版本选择:
       - Q4_K_M: 4GB左右，推荐平衡
       - Q5_K_M: 5GB左右，更高精度
       - Q8_0: 8GB左右，接近原始精度
    
    2. ModelScope GGUF模型:
       https://modelscope.cn/models
       搜索关键词 "GGUF" + 模型名
    
    3. 下载步骤:
       a. 访问模型页面
       b. 下载 .gguf 文件
       c. 放置到: ./models/gguf/
       d. 运行: python scripts/setup_llm.py
    
    ==== SafeTensors 格式模型 (原始精度，内存占用高) ====
    
    1. HuggingFace 模型库:
       https://huggingface.co/models?library=transformers
       
       推荐模型:
       - Qwen/Qwen2-7B-Instruct
       - mistralai/Mistral-7B-Instruct-v0.2
       - meta-llama/Meta-Llama-3-8B-Instruct
    
    2. 下载步骤 (使用 huggingface-cli):
       pip install huggingface_hub
       huggingface-cli download Qwen/Qwen2-7B-Instruct --local-dir ./models/safetensors/qwen2-7b
    
    3. 或使用 git-lfs:
       git lfs install
       cd models/safetensors
       git clone https://huggingface.co/Qwen/Qwen2-7B-Instruct
    
    ==== 硬件要求 ====
    
    GGUF (量化):
      - 7B Q4: 最低4GB显存/RAM
      - 7B Q5: 最低6GB显存/RAM
      - 13B Q4: 最低8GB显存/RAM
    
    SafeTensors (FP16):
      - 7B: 最低14GB显存
      - 13B: 最低26GB显存
      - 需要CUDA支持
    
    """
    raise NotImplementedError(
        f"\n"
        f"{'='*70}\n"
        f"LLM模型需要手动下载\n"
        f"{'='*70}\n"
        f"\n"
        f"模型格式: {model_format}\n"
        f"目标目录: {cache_dir}/{model_format}/\n"
        f"\n"
        f"请参考函数文档中的下载指南，或运行:\n"
        f"  python -c \"from utils.model_manager import download_llm_model; help(download_llm_model)\"\n"
        f"\n"
        f"下载完成后运行配置脚本:\n"
        f"  python scripts/setup_llm.py\n"
        f"{'='*70}\n"
    )



def check_model_exists(model_id: str, cache_dir: str) -> bool:
    """
    检查模型是否已下载
    
    Args:
        model_id: 模型ID
        cache_dir: 缓存目录
        
    Returns:
        True if exists, False otherwise
    """
    model_path = os.path.join(cache_dir, model_id)
    return os.path.exists(model_path)
