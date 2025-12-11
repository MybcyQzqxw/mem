#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型注册表管理工具
查看、验证和管理本地模型注册表
"""

import json
from pathlib import Path
import sys


def list_models():
    """列出注册表中的所有模型，检查文件存在性"""
    registry_file = Path(__file__).parent / 'model_registry.json'
    
    if not registry_file.exists():
        print("❌ 模型注册表不存在")
        return
    
    with open(registry_file, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    models = registry.get('models', [])
    embedding_models = registry.get('embedding_models', [])
    
    if not models and not embedding_models:
        print("📋 模型注册表为空")
        return
    
    print("=" * 80)
    print("📋 模型注册表检查报告")
    print("=" * 80)
    print()
    
    # ========== LLM模型 ==========
    if models:
        print("🤖 LLM模型")
        print("-" * 80)
        
        available_models = []
        missing_models = []
        
        for model in models:
            if Path(model['local_path']).exists():
                available_models.append(model)
            else:
                missing_models.append(model)
        
        if available_models:
            print(f"✅ 可用: {len(available_models)} 个")
            for i, model in enumerate(available_models, 1):
                print(f"  {i}. {model['shortcut']} ({model['format']}, {model.get('quantization', 'N/A')})")
                print(f"     📂 {model['local_path']}")
            print()
        
        if missing_models:
            print(f"⚠️  缺失: {len(missing_models)} 个")
            for i, model in enumerate(missing_models, 1):
                print(f"  {i}. {model['shortcut']} ({model['format']}, {model.get('quantization', 'N/A')})")
                print(f"     ❌ {model['local_path']}")
                print(f"     提示: 文件不存在，需要重新下载")
            print()
    
    # ========== 嵌入模型 ==========
    if embedding_models:
        print("🔤 嵌入模型")
        print("-" * 80)
        
        available_embeddings = []
        missing_embeddings = []
        
        for model in embedding_models:
            if Path(model['local_path']).exists():
                available_embeddings.append(model)
            else:
                missing_embeddings.append(model)
        
        if available_embeddings:
            print(f"✅ 可用: {len(available_embeddings)} 个")
            for i, model in enumerate(available_embeddings, 1):
                print(f"  {i}. {model['model_id']} (dim={model['embedding_dim']})")
                print(f"     📂 {model['local_path']}")
            print()
        
        if missing_embeddings:
            print(f"⚠️  缺失: {len(missing_embeddings)} 个")
            for i, model in enumerate(missing_embeddings, 1):
                print(f"  {i}. {model['model_id']} (dim={model['embedding_dim']})")
                print(f"     ❌ {model['local_path']}")
                print(f"     提示: 文件不存在，需要重新下载")
            print()
    
    # ========== 总结 ==========
    print("=" * 80)
    total_llm = len(models)
    available_llm = sum(1 for m in models if Path(m['local_path']).exists())
    total_emb = len(embedding_models)
    available_emb = sum(1 for m in embedding_models if Path(m['local_path']).exists())
    
    print(f"总计: {total_llm} 个LLM模型, {total_emb} 个嵌入模型")
    print(f"可用: {available_llm} 个LLM, {available_emb} 个嵌入 | 缺失: {total_llm - available_llm + total_emb - available_emb} 个")


def verify_models():
    """验证注册表中的模型文件是否存在"""
    registry_file = Path(__file__).parent / 'model_registry.json'
    
    if not registry_file.exists():
        print("❌ 模型注册表不存在")
        return
    
    with open(registry_file, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    models = registry.get('models', [])
    
    print("🔍 验证模型文件...")
    print()
    
    updated = False
    for model in models:
        path = Path(model['local_path'])
        exists = path.exists()
        
        print(f"  {model['shortcut']} ({model['format']}, {model.get('quantization', 'N/A')})")
        print(f"    路径: {model['local_path']}")
        print(f"    状态: {'✅ 存在' if exists else '❌ 缺失'}")
        print()
    
    if updated:
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        print("💾 已更新注册表验证状态")


def find_model(shortcut=None, format_type=None, quantization=None):
    """根据配置查找模型"""
    registry_file = Path(__file__).parent / 'model_registry.json'
    
    if not registry_file.exists():
        print("❌ 模型注册表不存在")
        return
    
    with open(registry_file, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    models = registry.get('models', [])
    
    # 过滤
    results = []
    for model in models:
        if shortcut and model['shortcut'] != shortcut:
            continue
        if format_type and model['format'] != format_type:
            continue
        if quantization and model.get('quantization') != quantization:
            continue
        results.append(model)
    
    if not results:
        print("❌ 未找到匹配的模型")
        return
    
    print(f"🔍 找到 {len(results)} 个匹配的模型:")
    print()
    
    for model in results:
        exists = Path(model['local_path']).exists()
        print(f"  • {model['shortcut']} ({model['format']}, {model.get('quantization', 'N/A')})")
        print(f"    路径: {model['local_path']}")
        print(f"    状态: {'✅' if exists else '❌'}")
        print()


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python list_models.py list              # 列出所有模型")
        print("  python list_models.py verify            # 验证模型文件")
        print("  python list_models.py find <shortcut>   # 查找指定模型")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        list_models()
    elif command == 'verify':
        verify_models()
    elif command == 'find':
        if len(sys.argv) < 3:
            print("请提供模型简称")
            return
        find_model(shortcut=sys.argv[2])
    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()
