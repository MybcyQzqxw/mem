#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
评测共享模块 (Evaluation Common)
提供 memory_ingestion.py 和 memory_qa.py 共用的配置、工具函数和常量

确保两个脚本使用完全一致的：
- 配置加载逻辑
- 记忆库路径/命名规则
- 日志格式
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'utils'))


# =============================================================================
# 常量定义（确保两个脚本使用一致的命名规则）
# =============================================================================

# Qdrant 路径模板：./qdrant_data_{speaker_name}
QDRANT_PATH_TEMPLATE = "./qdrant_data_{speaker}"

# Collection 名称模板：locomo_{speaker}_{conv_idx}
COLLECTION_NAME_TEMPLATE = "locomo_{speaker}_{conv_idx}"

# 默认数据集路径
DEFAULT_DATA_PATH = "locomo/data/locomo10.json"
FALLBACK_DATA_PATH = "locomo/data/locomo1.json"


# =============================================================================
# 工具函数
# =============================================================================

def str_to_bool(value: str) -> bool:
    """将字符串转换为布尔值"""
    return value.lower() in ('true', '1', 'yes', 'on')


def print_separator(char: str = "=", length: int = 80):
    """打印分隔线"""
    print(char * length)


def print_header(title: str, level: int = 1):
    """
    打印标题
    
    Args:
        title: 标题文本
        level: 标题级别 (1=主标题, 2=次标题, 3=小标题)
    """
    if level == 1:
        print_separator("=")
        print(f"  {title}")
        print_separator("=")
    elif level == 2:
        print_separator("-")
        print(f"  {title}")
        print_separator("-")
    else:
        print(f"\n▶ {title}")


def format_timestamp() -> str:
    """格式化当前时间戳（毫秒精度）"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def get_qdrant_path(speaker: str) -> str:
    """
    获取指定 speaker 的 Qdrant 存储路径
    
    Args:
        speaker: speaker 名称（如 Caroline）
        
    Returns:
        Qdrant 路径（如 ./qdrant_data_Caroline）
    """
    return QDRANT_PATH_TEMPLATE.format(speaker=speaker)


def get_collection_name(speaker: str, conv_idx: int) -> str:
    """
    获取指定 speaker 和 conversation 的 collection 名称
    
    Args:
        speaker: speaker 名称（如 Caroline）
        conv_idx: conversation 索引（0-9）
        
    Returns:
        Collection 名称（如 locomo_Caroline_0）
    """
    return COLLECTION_NAME_TEMPLATE.format(speaker=speaker, conv_idx=conv_idx)


def get_user_id(speaker: str, conv_idx: int) -> str:
    """
    获取指定 speaker 的 user_id
    
    Args:
        speaker: speaker 名称
        conv_idx: conversation 索引
        
    Returns:
        user_id（如 Caroline_0）
    """
    return f"{speaker}_{conv_idx}"


# =============================================================================
# 配置加载
# =============================================================================

def load_config() -> Dict[str, Any]:
    """
    从 .env 加载评测配置
    
    Returns:
        配置字典，包含：
        - use_local_llm: 是否使用本地 LLM
        - local_model_path: 本地模型路径
        - local_embedding_model: 嵌入模型名称
        - embedding_dim: 嵌入维度
        - batch_size: 批次大小
        - test_mode: 是否测试模式
        - data_path: 数据集路径
    """
    load_dotenv()
    
    config = {
        "use_local_llm": str_to_bool(os.getenv('USE_LOCAL_LLM', 'false')),
        "local_model_path": None,
        "local_embedding_model": os.getenv('LOCAL_EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5'),
        "embedding_dim": int(os.getenv('EMBEDDING_DIM', '512')),
        "memory_search_limit": int(os.getenv('MEMORY_SEARCH_LIMIT', '5')),
        "qa_search_limit": int(os.getenv('QA_SEARCH_LIMIT', '5')),
        "batch_size": int(os.getenv('EVAL_BATCH_SIZE', '2')),
        "test_mode": str_to_bool(os.getenv('EVAL_TEST_MODE', 'true')),
        "data_path": DEFAULT_DATA_PATH
    }
    
    # 如果使用本地 LLM，构建模型路径
    if config["use_local_llm"]:
        model_shortcut = os.getenv('MODEL_SHORTCUT', 'mistral-7b')
        model_format = os.getenv('MODEL_FORMAT', 'gguf')
        quantization = os.getenv('MODEL_QUANTIZATION', 'Q4_K_M')
        
        try:
            from model_manager import _load_model_shortcuts
            shortcuts = _load_model_shortcuts()
            if model_shortcut in shortcuts:
                model_info = shortcuts[model_shortcut]
                model_id = model_info.get(model_format, model_shortcut)
                
                if model_format == 'gguf':
                    model_name = model_id.split('/')[-1].replace('-GGUF', '').lower()
                    filename = f"{model_name}.{quantization}.gguf"
                    config["local_model_path"] = f"models/gguf/{filename}"
                else:
                    config["local_model_path"] = f"models/safetensors/{model_id}"
        except ImportError:
            pass
    
    return config


def print_config(config: Dict[str, Any], extra_info: Optional[Dict[str, Any]] = None):
    """
    打印配置信息
    
    Args:
        config: 配置字典
        extra_info: 额外信息（如 max_conversations）
    """
    print(f"\n📋 配置信息:")
    print(f"   • 数据集: {config['data_path']}")
    print(f"   • batch_size: {config.get('batch_size', 'N/A')}")
    print(f"   • memory_search_limit: {config.get('memory_search_limit', 5)}")
    print(f"   • qa_search_limit: {config.get('qa_search_limit', 5)}")
    print(f"   • 本地LLM: {config['use_local_llm']}")
    if config['use_local_llm'] and config['local_model_path']:
        print(f"   • 模型路径: {config['local_model_path']}")
    print(f"   • 嵌入模型: {config['local_embedding_model']}")
    
    if extra_info:
        for key, value in extra_info.items():
            print(f"   • {key}: {value}")


# =============================================================================
# 基础日志记录器
# =============================================================================

class BaseLogger:
    """基础日志记录器"""
    
    # 日志级别前缀映射
    LEVEL_PREFIXES = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARN": "⚠️ ",
        "ERROR": "❌",
        "BATCH": "📦",
        "MEMORY": "🧠",
        "SEARCH": "🔍",
        "QA": "❓",
        "ANSWER": "💬"
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.stats = {}
    
    def log(self, level: str, message: str, **kwargs):
        """
        记录日志
        
        Args:
            level: 日志级别（INFO, SUCCESS, WARN, ERROR, BATCH, MEMORY, SEARCH, QA, ANSWER）
            message: 日志消息
            **kwargs: 额外信息（会在消息下方显示）
        """
        timestamp = format_timestamp()
        prefix = self.LEVEL_PREFIXES.get(level, "  ")
        
        print(f"[{timestamp}] {prefix} {message}")
        
        if kwargs and self.verbose:
            for key, value in kwargs.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"           └─ {key}: {value}")
    
    def print_stats(self, title: str = "统计"):
        """打印统计信息"""
        print_header(title, level=2)
        for key, value in self.stats.items():
            # 将 snake_case 转换为更友好的显示
            display_key = key.replace("_", " ").title()
            print(f"  📊 {display_key}: {value}")


# =============================================================================
# 记忆系统工厂函数
# =============================================================================

def create_memory_system(
    speaker: str,
    conv_idx: int,
    config: Dict[str, Any]
):
    """
    创建记忆系统实例
    
    确保 memory_ingestion.py 和 memory_qa.py 使用完全一致的参数创建记忆库
    
    Args:
        speaker: speaker 名称
        conv_idx: conversation 索引
        config: 配置字典
        
    Returns:
        MemorySystem 实例
    """
    from tinymem0.memory_system import MemorySystem
    
    return MemorySystem(
        collection_name=get_collection_name(speaker, conv_idx),
        qdrant_path=get_qdrant_path(speaker),
        use_local_llm=config['use_local_llm'],
        local_model_path=config['local_model_path'],
        local_embedding_model=config['local_embedding_model'],
        embedding_dim=config['embedding_dim'],
        memory_search_limit=config.get('memory_search_limit', 5)
    )
