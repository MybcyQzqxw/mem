#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 模型配置助手

该脚本用于帮助用户配置本地 GGUF 格式的 LLM 模型。
注意：此脚本不会下载模型，用户需要手动下载 GGUF 模型文件。

功能：
1. 自动创建 ./models 目录
2. 检测目录中的 .gguf 模型文件
3. 将选定的模型路径写入 .env 文件

使用方法：
    python scripts/setup_llm.py

推荐的 GGUF 模型下载源：
- HuggingFace: https://huggingface.co/models?library=gguf
- ModelScope: https://modelscope.cn/models
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.model_manager import (
    ensure_models_directory,
    find_gguf_models,
    configure_llm_model,
    get_model_info
)


def print_banner():
    """打印欢迎信息"""
    print("=" * 70)
    print("🔧 TinyMem0 LLM 模型配置助手")
    print("=" * 70)
    print()
    print("📝 说明：")
    print("  此工具用于配置本地 GGUF 格式的 LLM 模型")
    print("  不会自动下载模型，请先手动下载模型文件到 ./models 目录")
    print()
    print("🌐 推荐下载源：")
    print("  - HuggingFace: https://huggingface.co/models?library=gguf")
    print("  - ModelScope: https://modelscope.cn/models")
    print()


def print_download_guide():
    """打印下载指南"""
    print("📚 GGUF 模型下载指南：")
    print()
    print("推荐模型：")
    print("  1. Qwen2-7B-Instruct (Q4_K_M) - 中文优化，4GB")
    print("  2. Mistral-7B-Instruct (Q4_K_M) - 通用性好，4GB")
    print("  3. Llama-3-8B-Instruct (Q4_K_M) - Meta 官方，5GB")
    print()
    print("下载步骤：")
    print("  1. 访问 HuggingFace 或 ModelScope")
    print("  2. 搜索模型名称 + 'GGUF'")
    print("  3. 下载 Q4_K_M 或 Q5_K_M 量化版本")
    print("  4. 将 .gguf 文件放入 ./models 目录")
    print("  5. 重新运行此脚本")
    print()


def main():
    """主函数"""
    print_banner()
    
    # 确保模型目录存在
    project_root = Path(__file__).parent.parent
    models_dir = project_root / 'models'
    ensure_models_directory(str(models_dir))
    
    # 查找 GGUF 模型
    models = find_gguf_models(str(models_dir))
    
    if not models:
        print("⚠️  未在 ./models 目录中发现 .gguf 模型文件")
        print()
        print_download_guide()
        print("=" * 70)
        return
    
    # 显示找到的模型
    print(f"✅ 在 ./models 目录中发现 {len(models)} 个 GGUF 模型：")
    print()
    
    for i, model_path in enumerate(models, start=1):
        info = get_model_info(model_path)
        print(f"  [{i}] {info['name']}")
        print(f"      大小: {info['size_str']}")
        print(f"      路径: {info['path']}")
        print()
    
    # 选择模型
    choice = None
    if len(models) == 1:
        # 只有一个模型，自动选择
        choice = 1
        print(f"🎯 自动选择唯一的模型: {models[0].name}")
        print()
    else:
        # 多个模型，让用户选择
        try:
            user_input = input(
                f"请输入要配置的模型序号 [1-{len(models)}] (按回车取消): "
            ).strip()
            
            if not user_input:
                print("❌ 已取消配置")
                return
            
            choice = int(user_input)
            
            if choice < 1 or choice > len(models):
                print(f"❌ 无效的序号，请输入 1-{len(models)}")
                return
                
        except ValueError:
            print("❌ 无效的输入，请输入数字")
            return
    
    # 配置选定的模型
    selected_model = models[choice - 1]
    env_file = project_root / '.env'
    
    print(f"📝 正在配置模型...")
    success = configure_llm_model(
        str(selected_model),
        str(env_file)
    )
    
    if success:
        print()
        print("=" * 70)
        print("✅ 配置完成！")
        print()
        print("📋 下一步：")
        print("  1. 确保 .env 文件中 USE_LOCAL_LLM=true")
        print("  2. 运行你的应用程序")
        print()
        print("💡 提示：")
        print(f"  如需更换模型，重新运行: python scripts/setup_llm.py")
        print("=" * 70)
    else:
        print()
        print("❌ 配置失败，请检查文件权限")


if __name__ == '__main__':
    main()
