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
    model_format: str = 'auto',
    quantization: Optional[str] = None,
    source: str = 'huggingface'
) -> str:
    """
    从 HuggingFace 下载 LLM 模型（支持 GGUF 和 SafeTensors）
    
    Args:
        model_id: 模型ID
            - GGUF: 如 "TheBloke/Qwen2-7B-Instruct-GGUF"
            - SafeTensors: 如 "Qwen/Qwen2-7B-Instruct"
        cache_dir: 缓存目录基础路径
        model_format: 模型格式 ('auto', 'gguf', 'safetensors')
            - 'auto': 自动检测（通过model_id判断）
        quantization: GGUF量化版本（仅GGUF格式需要）
            - 'Q4_K_M': 4-bit, 推荐
            - 'Q5_K_M': 5-bit, 更高精度
            - 'Q8_0': 8-bit, 接近原始
        source: 下载源 ('huggingface' 或 'modelscope')
        
    Returns:
        下载后的模型路径
        
    Examples:
        >>> # 下载GGUF模型
        >>> path = download_llm_model(
        ...     "TheBloke/Qwen2-7B-Instruct-GGUF",
        ...     quantization="Q4_K_M"
        ... )
        
        >>> # 下载SafeTensors模型
        >>> path = download_llm_model(
        ...     "Qwen/Qwen2-7B-Instruct",
        ...     model_format="safetensors"
        ... )
    """
    # 自动检测格式
    if model_format == 'auto':
        if 'GGUF' in model_id or 'gguf' in model_id:
            model_format = 'gguf'
        else:
            model_format = 'safetensors'
    
    print(f"📦 开始下载 {model_format.upper()} 格式模型: {model_id}")
    
    if model_format == 'gguf':
        return _download_gguf_model(model_id, cache_dir, quantization, source)
    elif model_format == 'safetensors':
        return _download_safetensors_model(model_id, cache_dir, source)
    else:
        raise ValueError(f"不支持的模型格式: {model_format}")


def _download_gguf_model(
    model_id: str,
    cache_dir: str,
    quantization: Optional[str],
    source: str
) -> str:
    """下载GGUF格式模型（内部函数）"""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError(
            "需要安装 huggingface_hub\n"
            "运行: pip install huggingface_hub>=0.19.0"
        )
    
    # 设置目标目录
    target_dir = os.path.join(cache_dir, 'gguf')
    os.makedirs(target_dir, exist_ok=True)
    
    # 如果未指定量化版本，尝试推荐
    if not quantization:
        print("⚠️  未指定量化版本，推荐使用 Q4_K_M")
        quantization = "Q4_K_M"
    
    # 构建GGUF文件名（通常格式：模型名-量化版本.gguf）
    # 需要列出仓库文件来找到精确文件名
    print(f"🔍 正在查找 {quantization} 量化版本...")
    
    try:
        from huggingface_hub import list_repo_files
        
        print("   连接到 HuggingFace...")
        # 列出仓库中所有文件
        files = list_repo_files(model_id)
        gguf_files = [f for f in files if f.endswith('.gguf')]
        
        print(f"   找到 {len(gguf_files)} 个GGUF文件")
        
        # 查找匹配的量化文件
        target_file = None
        
        # 优先匹配完整的量化名称（如 Q4_K_M）
        for f in gguf_files:
            if quantization.upper() in f.upper():
                target_file = f
                break
        
        # 如果没找到，尝试匹配类似的（如 Q4_K_M -> q4_k_m）
        if not target_file:
            quant_normalized = quantization.replace('_', '-').lower()
            for f in gguf_files:
                f_normalized = f.replace('_', '-').lower()
                if quant_normalized in f_normalized:
                    target_file = f
                    break
        
        if not target_file:
            print(f"\n❌ 未找到 {quantization} 量化版本")
            print(f"\n可用的GGUF文件:")
            for f in gguf_files[:10]:  # 只显示前10个
                print(f"  - {f}")
            raise ValueError(
                f"未找到 {quantization} 量化版本\n"
                f"请从上面的列表中选择一个文件"
            )
        
        print(f"✅ 找到文件: {target_file}")
        
        # 获取文件大小
        from huggingface_hub import HfApi
        api = HfApi()
        file_info = api.repo_info(model_id, files_metadata=True)
        file_size = None
        for sibling in file_info.siblings:
            if sibling.rfilename == target_file:
                file_size = sibling.size
                break
        
        if file_size:
            size_gb = file_size / (1024**3)
            print(f"📦 文件大小: {size_gb:.2f} GB")
        
        print(f"📥 开始下载...")
        print(f"💾 保存到: {target_dir}")
        
        # 下载文件（带进度条）
        downloaded_path = hf_hub_download(
            repo_id=model_id,
            filename=target_file,
            local_dir=target_dir
        )
        
        print(f"\n✅ 下载完成: {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        raise


def _download_safetensors_model(
    model_id: str,
    cache_dir: str,
    source: str
) -> str:
    """下载SafeTensors格式模型（内部函数）"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError(
            "需要安装 huggingface_hub\n"
            "运行: pip install huggingface_hub>=0.19.0"
        )
    
    # 设置目标目录
    model_name = model_id.split('/')[-1]
    target_dir = os.path.join(cache_dir, 'safetensors', model_name)
    os.makedirs(os.path.dirname(target_dir), exist_ok=True)
    
    # 检查是否已存在
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        config_file = os.path.join(target_dir, 'config.json')
        if os.path.exists(config_file):
            print(f"✅ 模型已存在: {target_dir}")
            return target_dir
    
    print(f"📥 开始下载到: {target_dir}")
    print("⚠️  SafeTensors模型体积较大(10GB+)，请耐心等待...")
    
    try:
        # 获取 HF Token（用于受限模型）
        hf_token = os.getenv('HF_TOKEN', None)
        
        # 下载整个模型仓库
        downloaded_path = snapshot_download(
            repo_id=model_id,
            local_dir=target_dir,
            token=hf_token,
            ignore_patterns=[
                "*.bin",  # 忽略旧的PyTorch格式
                "*.msgpack",
                "*.h5",
                "*.ot",
                "*.onnx"
            ]
        )
        
        print(f"✅ 下载完成: {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        
        # 检查是否为认证问题
        if "401" in str(e) or "403" in str(e) or "authentication" in str(e).lower():
            print("\n💡 提示: 此模型可能需要认证")
            print("请设置 HF_TOKEN 环境变量:")
            print("  1. 访问 https://huggingface.co/settings/tokens")
            print("  2. 创建访问令牌")
            print("  3. 添加到 .env 文件: HF_TOKEN=hf_your_token")
        
        raise



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
