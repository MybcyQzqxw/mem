#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM模型下载脚本
提供交互式和命令行两种方式下载LLM模型
支持GGUF和SafeTensors两种格式
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.model_manager import download_llm_model


# 模型映射
MODEL_MAP = {
    'qwen2.5-7b': (
        'bartowski/Qwen2.5-7B-Instruct-GGUF',
        'Qwen/Qwen2.5-7B-Instruct'
    ),
    'mistral-7b': (
        'TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
        'mistralai/Mistral-7B-Instruct-v0.2'
    ),
    'llama3-8b': (
        'TheBloke/Meta-Llama-3-8B-Instruct-GGUF',
        'meta-llama/Meta-Llama-3-8B-Instruct'
    ),
    'yi-6b': (
        'TheBloke/Yi-6B-Chat-GGUF',
        '01-ai/Yi-6B-Chat'
    ),
}


def print_banner():
    """打印横幅"""
    print("=" * 70)
    print("🚀 LLM模型下载工具")
    print("=" * 70)


def print_format_choice():
    """打印格式选择"""
    print("\n[1] GGUF (CPU, 4-8GB)")
    print("[2] SafeTensors (GPU, 14-26GB)\n")


def download_model_with_shortcut(model_shortcut='mistral-7b', model_format='gguf', quantization='Q4_K_M', verbose=True, hf_token=None):
    """使用简称下载模型
    
    Args:
        model_shortcut: 模型简称
        model_format: gguf 或 safetensors
        quantization: GGUF量化级别
        verbose: 是否打印信息
        hf_token: HuggingFace访问令牌（由上层传递）
    
    Returns:
        下载的模型路径
    """
    if model_shortcut not in MODEL_MAP:
        raise ValueError(f"不支持的模型: {model_shortcut}. 可用: {list(MODEL_MAP.keys())}")
    
    # 根据格式选择仓库ID
    gguf_id, safetensors_id = MODEL_MAP[model_shortcut]
    model_id = gguf_id if model_format == 'gguf' else safetensors_id
    
    if verbose:
        print(f"🔍 模型: {model_shortcut}")
        print(f"🔗 仓库: {model_id}")
        print(f"📁 格式: {model_format}")
        if model_format == 'gguf':
            print(f"🔧 量化: {quantization}")
    
    from utils.model_manager.downloader import download_llm_model
    
    return download_llm_model(
        model_id=model_id,
        cache_dir='./models',
        model_format=model_format,
        quantization=quantization if model_format == 'gguf' else None,
        hf_token=hf_token
    )


def command_line_download(args):
    """命令行下载"""
    model_id = args.model_id
    
    # 检查是否是简称
    if model_id in MODEL_MAP:
        gguf_id, safetensors_id = MODEL_MAP[model_id]
        actual_id = gguf_id if args.format == 'gguf' else safetensors_id
        print(f"🔍 模型简称: {model_id}")
        print(f"🔗 仓库: {actual_id}")
        model_id = actual_id
    
    print(f"📁 格式: {args.format}")
    if args.format == 'gguf':
        print(f"🔧 量化: {args.quant}")
    
    try:
        print(f"\n⏳ 开始下载...")
        
        from utils.model_manager.downloader import download_llm_model
        downloaded_path = download_llm_model(
            model_id=model_id,
            cache_dir='./models',
            model_format=args.format,
            quantization=args.quant
        )
        
        print(f"\n✅ 下载完成: {downloaded_path}")
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LLM模型下载工具')
    
    parser.add_argument('--model', '-m', type=str, dest='model_id',
                       help='模型简称或完整ID')
    parser.add_argument('--format', type=str, choices=['gguf', 'safetensors'],
                       default='gguf', help='模型格式')
    parser.add_argument('--quant', type=str, default='Q4_K_M',
                       help='GGUF量化版本')
    
    args = parser.parse_args()
    
    if args.model_id:
        command_line_download(args)
    else:
        print("用法: python scripts/download_llm.py --model MODEL --format FORMAT")
        print(f"可用模型: {list(MODEL_MAP.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()
