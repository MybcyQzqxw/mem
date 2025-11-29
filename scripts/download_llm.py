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


# 推荐的GGUF模型列表
GGUF_MODELS = {
    '1': {
        'id': 'TheBloke/Qwen2-7B-Instruct-GGUF',
        'name': 'Qwen2-7B-Instruct',
        'quant': 'Q4_K_M',
        'size': '~4.4GB',
        'lang': '中文优化',
        'description': '推荐：阿里云通义千问2代，中文效果优秀'
    },
    '2': {
        'id': 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
        'name': 'Mistral-7B-Instruct-v0.2',
        'quant': 'Q4_K_M',
        'size': '~4.1GB',
        'lang': '多语言',
        'description': 'Mistral AI官方，通用性好，指令遵循强'
    },
    '3': {
        'id': 'TheBloke/Meta-Llama-3-8B-Instruct-GGUF',
        'name': 'Llama-3-8B-Instruct',
        'quant': 'Q4_K_M',
        'size': '~4.7GB',
        'lang': '多语言',
        'description': 'Meta官方Llama 3，性能强劲'
    },
    '4': {
        'id': 'TheBloke/Yi-6B-Chat-GGUF',
        'name': 'Yi-6B-Chat',
        'quant': 'Q4_K_M',
        'size': '~3.5GB',
        'lang': '中英双语',
        'description': '零一万物，中英双语能力均衡'
    }
}

# 推荐的SafeTensors模型列表
SAFETENSORS_MODELS = {
    '1': {
        'id': 'Qwen/Qwen2-7B-Instruct',
        'name': 'Qwen2-7B-Instruct',
        'size': '~15GB',
        'lang': '中文优化',
        'description': '推荐：原始精度，最佳中文效果，需12GB+显存'
    },
    '2': {
        'id': 'mistralai/Mistral-7B-Instruct-v0.2',
        'name': 'Mistral-7B-Instruct-v0.2',
        'size': '~14GB',
        'lang': '多语言',
        'description': 'Mistral官方，需12GB+显存'
    },
    '3': {
        'id': 'meta-llama/Meta-Llama-3-8B-Instruct',
        'name': 'Llama-3-8B-Instruct',
        'size': '~16GB',
        'lang': '多语言',
        'description': 'Meta官方，需14GB+显存（需申请访问权限）'
    }
}


def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("🚀 TinyMem0 LLM模型下载工具")
    print("=" * 70)
    print()


def print_format_choice():
    """打印格式选择菜单"""
    print("📋 请选择模型格式：\n")
    print("[1] GGUF 格式（量化，推荐）")
    print("    优点: 内存占用低(4-8GB)，CPU可运行，速度快")
    print("    适合: 低配机器，无GPU或显存不足")
    print()
    print("[2] SafeTensors 格式（原始精度）")
    print("    优点: 精度最高，无损量化")
    print("    适合: 高配GPU(12GB+显存)，追求最佳效果")
    print()


def print_gguf_models():
    """打印GGUF模型列表"""
    print("📋 可用的 GGUF 模型（量化版本: Q4_K_M）：\n")
    for key, model in GGUF_MODELS.items():
        print(f"[{key}] {model['name']}")
        print(f"    模型ID: {model['id']}")
        print(f"    大小: {model['size']} | 语言: {model['lang']}")
        print(f"    量化: {model['quant']}")
        print(f"    说明: {model['description']}")
        print()


def print_safetensors_models():
    """打印SafeTensors模型列表"""
    print("📋 可用的 SafeTensors 模型（FP16原始精度）：\n")
    for key, model in SAFETENSORS_MODELS.items():
        print(f"[{key}] {model['name']}")
        print(f"    模型ID: {model['id']}")
        print(f"    大小: {model['size']} | 语言: {model['lang']}")
        print(f"    说明: {model['description']}")
        print()


def interactive_download():
    """交互式下载模式"""
    print_banner()
    print_format_choice()
    
    # 选择格式
    while True:
        format_choice = input("请选择格式 [1-2] (输入 'q' 退出): ").strip()
        
        if format_choice.lower() == 'q':
            print("👋 退出下载")
            return
        
        if format_choice in ['1', '2']:
            break
        
        print("❌ 无效的选择，请重新输入\n")
    
    model_format = 'gguf' if format_choice == '1' else 'safetensors'
    models_dict = GGUF_MODELS if format_choice == '1' else SAFETENSORS_MODELS
    
    print()
    if model_format == 'gguf':
        print_gguf_models()
    else:
        print_safetensors_models()
    
    # 选择模型
    while True:
        model_choice = input(
            f"请选择要下载的模型 [1-{len(models_dict)}] (输入 'q' 退出): "
        ).strip()
        
        if model_choice.lower() == 'q':
            print("👋 退出下载")
            return
        
        if model_choice in models_dict:
            break
        
        print("❌ 无效的选择，请重新输入\n")
    
    model = models_dict[model_choice]
    
    print(f"\n✅ 你选择了: {model['name']}")
    print(f"📦 模型ID: {model['id']}")
    print(f"💾 大小: {model['size']}")
    
    if model_format == 'gguf':
        print(f"🔧 量化: {model['quant']}")
    
    # 确认下载
    confirm = input(f"\n确认下载? [Y/n]: ").strip().lower()
    if confirm not in ['', 'y', 'yes']:
        print("❌ 取消下载")
        return
    
    try:
        print(f"\n⏳ 开始下载 {model['name']}...")
        print("💡 提示: 大文件下载可能需要较长时间，请耐心等待")
        print()
        
        if model_format == 'gguf':
            downloaded_path = download_llm_model(
                model_id=model['id'],
                cache_dir='./models',
                model_format='gguf',
                quantization=model['quant']
            )
        else:
            downloaded_path = download_llm_model(
                model_id=model['id'],
                cache_dir='./models',
                model_format='safetensors'
            )
        
        print()
        print("=" * 70)
        print(f"✅ 下载成功！")
        print(f"📁 模型路径: {downloaded_path}")
        print()
        print("📋 下一步：")
        print("  1. 运行配置脚本: python scripts/setup_llm.py")
        print("  2. 在 .env 文件中设置 USE_LOCAL_LLM=true")
        print("  3. 启动你的应用程序")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 下载失败: {e}")
        print()
        print("💡 故障排除:")
        print("  1. 检查网络连接")
        print("  2. 检查磁盘空间是否充足")
        print("  3. 如果是认证错误，设置 HF_TOKEN 环境变量")
        print("  4. 尝试使用命令行模式指定自定义模型ID")
        print("=" * 70)


def command_line_download(args):
    """命令行下载模式"""
    print_banner()
    
    model_id = args.model_id
    model_format = args.format
    quantization = args.quant
    
    print(f"📦 模型ID: {model_id}")
    print(f"📁 格式: {model_format}")
    if model_format == 'gguf':
        print(f"🔧 量化: {quantization}")
    
    try:
        print(f"\n⏳ 开始下载...")
        
        downloaded_path = download_llm_model(
            model_id=model_id,
            cache_dir='./models',
            model_format=model_format,
            quantization=quantization
        )
        
        print()
        print("=" * 70)
        print(f"✅ 下载成功！")
        print(f"📁 模型路径: {downloaded_path}")
        print("=" * 70)
        
    except Exception as e:
        print()
        print(f"❌ 下载失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='TinyMem0 LLM模型下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

  # 交互式模式（推荐新手）
  python scripts/download_llm.py

  # 下载GGUF模型
  python scripts/download_llm.py \\
    --model-id TheBloke/Qwen2-7B-Instruct-GGUF \\
    --format gguf \\
    --quant Q4_K_M

  # 下载SafeTensors模型
  python scripts/download_llm.py \\
    --model-id Qwen/Qwen2-7B-Instruct \\
    --format safetensors
        """
    )
    
    parser.add_argument(
        '--model-id',
        type=str,
        help='HuggingFace模型ID'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['gguf', 'safetensors', 'auto'],
        default='auto',
        help='模型格式 (默认: auto自动检测)'
    )
    
    parser.add_argument(
        '--quant',
        type=str,
        default='Q4_K_M',
        help='GGUF量化版本 (默认: Q4_K_M)'
    )
    
    args = parser.parse_args()
    
    # 如果指定了model-id，使用命令行模式
    if args.model_id:
        command_line_download(args)
    else:
        # 否则使用交互式模式
        interactive_download()


if __name__ == "__main__":
    main()
