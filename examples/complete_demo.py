#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
记忆系统使用示例 - 自动下载模型并运行
"""
import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from tinymem0 import MemorySystem


def download_models(model_shortcut='qwen2.5-7b', model_format='gguf'):
    """自动下载模型
    
    Args:
        model_shortcut: 模型快捷名称 (qwen2.5-7b, mistral-7b等)
        model_format: 模型格式 (gguf或safetensors)
    """
    print("=" * 70)
    print("📦 检查并下载模型")
    print("=" * 70)
    
    # 检查嵌入模型
    print("\n1️⃣ 嵌入模型...")
    embedding_model = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    print(f"   {embedding_model} (首次使用时自动下载)")
    
    # 检查LLM模型
    print("\n2️⃣ LLM模型...")
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    if not use_local:
        print("   ⏭️  云端API模式，无需下载")
        print("\n" + "=" * 70)
        return
    
    # 检查模型是否已存在
    if model_format == 'gguf':
        model_dir = Path('./models/gguf')
        if model_dir.exists():
            gguf_files = list(model_dir.glob('*.gguf'))
            if gguf_files:
                print(f"   ✅ 模型已存在: {gguf_files[0]}")
                print("\n" + "=" * 70)
                return
    else:
        model_dir = Path('./models/safetensors') / model_shortcut
        if model_dir.exists() and list(model_dir.glob('*')):
            print(f"   ✅ 模型已存在: {model_dir}")
            print("\n" + "=" * 70)
            return
    
    # 模型不存在，调用下载工具
    print(f"   ❌ 模型不存在，准备下载...\n")
    
    # 添加scripts到路径并调用下载函数
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
    from download_llm import download_model_with_shortcut
    
    try:
        downloaded_path = download_model_with_shortcut(
            model_shortcut=model_shortcut,
            model_format=model_format,
            quantization='Q4_K_M',
            verbose=True
        )
        
        print(f"\n   ✅ 模型下载完成！")
        print(f"   📂 位置: {downloaded_path}")
        
    except Exception as e:
        print(f"\n   ❌ 下载失败: {e}")
        print(f"   💡 你可以手动运行:")
        print(f"   python scripts/download_llm.py --model {model_shortcut} --format {model_format}")
    
    print("\n" + "=" * 70)


def main():
    """主函数 - 演示记忆系统的使用"""
    import os 
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    if not use_local and not os.getenv("DASHSCOPE_API_KEY"):
        raise RuntimeError("未找到 DASHSCOPE_API_KEY，请在 .env 中配置。")
    
    mode = "本地模型" if use_local else "云端API"
    print(f"初始化记忆系统 ({mode})...")
    memory_system = MemorySystem()
    
    # 示例1: 写入记忆
    print("\n=== 示例1: 写入记忆 ===")
    conversation1 = "你好，我叫张三，是一名软件工程师，我喜欢看电影，特别是科幻片。"
    print(f"用户对话: {conversation1}")
    
    memory_system.write_memory(
        conversation=conversation1,
        user_id="user_001",
        agent_id="agent_001"
    )
    
    # 示例2: 搜索记忆
    print("\n=== 示例2: 搜索记忆 ===")
    query = "张三的职业是什么？"
    print(f"搜索查询: {query}")
    
    results = memory_system.search_memory(
        query=query,
        user_id="user_001",
        agent_id="agent_001",
        limit=3
    )
    
    print("搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['text']} (相似度: {result['score']:.3f})")
    
    # 示例3: 更新记忆
    print("\n=== 示例3: 更新记忆 ===")
    conversation2 = "我最近改变了职业，现在是一名产品经理，不再做软件工程师了。"
    print(f"用户对话: {conversation2}")
    
    memory_system.write_memory(
        conversation=conversation2,
        user_id="user_001",
        agent_id="agent_001"
    )
    
    # 再次搜索验证更新
    print("\n更新后再次搜索:")
    results = memory_system.search_memory(
        query="张三的职业",
        user_id="user_001",
        agent_id="agent_001",
        limit=3
    )
    
    print("搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['text']} (相似度: {result['score']:.3f})")


def example_memory_update():
    """示例2: 记忆更新和冲突处理"""
    print("\n" + "=" * 70)
    print("🔄 示例2: 记忆更新")
    print("=" * 70)
    
    memory = MemorySystem(collection_name="demo_update")
    
    # 初始记忆
    print("\n1️⃣ 写入初始信息...")
    memory.write_memory(
        "我叫李明，今年25岁，在上海做产品经理",
        user_id="user_li",
        agent_id="assistant"
    )
    print("✅ 初始记忆已保存")
    
    # 搜索当前职业
    print("\n2️⃣ 查询当前职业...")
    results = memory.search_memory(
        "李明的职业",
        user_id="user_li",
        limit=1
    )
    if results:
        print(f"  当前职业: {results[0]['text']}")
    
    # 更新信息
    print("\n3️⃣ 更新职业信息...")
    memory.write_memory(
        "我现在换工作了，成为了一名数据科学家",
        user_id="user_li",
        agent_id="assistant"
    )
    print("✅ 记忆已更新")
    
    # 再次搜索
    print("\n4️⃣ 验证更新结果...")
    results = memory.search_memory(
        "李明的职业",
        user_id="user_li",
        limit=2
    )
    
    print("  搜索结果:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. {result['text']}")
    
    print("\n✅ 示例2完成")


def example_multi_user():
    """示例3: 多用户记忆隔离"""
    print("\n" + "=" * 70)
    print("👥 示例3: 多用户场景")
    print("=" * 70)
    
    memory = MemorySystem(collection_name="demo_multiuser")
    
    # 用户A的记忆
    print("\n1️⃣ 用户A的对话...")
    memory.write_memory(
        "我喜欢吃川菜，特别是麻婆豆腐",
        user_id="user_a",
        agent_id="assistant"
    )
    
    # 用户B的记忆
    print("2️⃣ 用户B的对话...")
    memory.write_memory(
        "我喜欢吃粤菜，特别是白切鸡",
        user_id="user_b",
        agent_id="assistant"
    )
    
    # 分别搜索
    print("\n3️⃣ 分别搜索用户偏好...")
    
    print("  用户A的搜索结果:")
    results_a = memory.search_memory(
        "喜欢吃什么菜",
        user_id="user_a",
        limit=1
    )
    for r in results_a:
        print(f"    - {r['text']}")
    
    print("  用户B的搜索结果:")
    results_b = memory.search_memory(
        "喜欢吃什么菜",
        user_id="user_b",
        limit=1
    )
    for r in results_b:
        print(f"    - {r['text']}")
    
    print("\n✅ 示例3完成 - 记忆已正确隔离")


def example_fact_extraction():
    """示例4: 事实提取功能"""
    print("\n" + "=" * 70)
    print("📊 示例4: 事实提取")
    print("=" * 70)
    
    memory = MemorySystem(collection_name="demo_facts")
    
    # 测试不同类型的对话
    test_cases = [
        ("简单问候", "你好"),
        ("个人信息", "我叫王芳，今年30岁，住在深圳"),
        ("兴趣爱好", "我喜欢旅游，去年去了日本和韩国"),
        ("工作信息", "我在一家互联网公司担任UI设计师"),
        ("未来计划", "我计划明年学习摄影")
    ]
    
    print("\n测试事实提取功能:\n")
    for label, conversation in test_cases:
        print(f"  [{label}]")
        print(f"  对话: {conversation}")
        
        facts = memory.extract_facts(conversation)
        
        if facts:
            print(f"  提取事实: {facts}")
        else:
            print("  提取事实: (无实质性信息)")
        print()
    
    print("✅ 示例4完成")


def example_advanced_search():
    """示例5: 高级搜索功能"""
    print("\n" + "=" * 70)
    print("🔎 示例5: 高级搜索")
    print("=" * 70)
    
    memory = MemorySystem(collection_name="demo_search")
    
    # 准备丰富的记忆数据
    print("\n1️⃣ 准备测试数据...")
    knowledge = [
        "我在2020年毕业于清华大学计算机系",
        "我的第一份工作是在字节跳动做后端开发",
        "2022年我跳槽到了阿里巴巴",
        "我现在负责电商推荐系统的开发",
        "我最擅长的技术栈是Python和Go",
        "业余时间我喜欢研究机器学习算法",
        "我的长期目标是成为一名技术专家"
    ]
    
    for k in knowledge:
        memory.write_memory(k, user_id="user_tech", agent_id="assistant")
    
    print(f"✅ 已写入 {len(knowledge)} 条记忆")
    
    # 不同类型的搜索
    print("\n2️⃣ 执行不同类型的搜索...\n")
    
    search_cases = [
        ("教育背景", "毕业院校"),
        ("工作经历", "工作变动历史"),
        ("技术能力", "擅长的编程语言"),
        ("兴趣爱好", "业余爱好"),
        ("职业规划", "未来目标")
    ]
    
    for category, query in search_cases:
        print(f"  [{category}] 查询: {query}")
        results = memory.search_memory(
            query=query,
            user_id="user_tech",
            limit=2
        )
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"    {i}. {r['text']} (分数: {r['score']:.3f})")
        else:
            print("    未找到相关结果")
        print()
    
    print("✅ 示例5完成")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='TinyMem0 记忆系统完整示例 - 自动下载模型并运行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 使用默认模型 (Qwen2.5-7B GGUF格式)
  python examples/complete_demo.py
  
  # 指定其他模型
  python examples/complete_demo.py --model mistral-7b --format gguf
  python examples/complete_demo.py --model qwen2.5-3b --format safetensors
  
  # 跳过模型下载（使用云端API或已有模型）
  python examples/complete_demo.py --skip-download

支持的模型:
  qwen2.5-7b, qwen2.5-3b, qwen2.5-1.5b
  mistral-7b, llama3-8b, yi-6b

支持的格式:
  gguf       - CPU推理，4-8GB (推荐)
  safetensors - GPU推理，14-26GB
        ''')
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='mistral-7b',
        choices=['qwen2.5-7b', 'qwen2.5-3b', 'qwen2.5-1.5b',
                'mistral-7b', 'llama3-8b', 'yi-6b'],
        help='选择模型 (默认: mistral-7b, 使用TheBloke/Mistral-7B-Instruct-v0.2-GGUF)'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        default='gguf',
        choices=['gguf', 'safetensors'],
        help='模型格式 (默认: gguf)'
    )
    
    parser.add_argument(
        '--skip-download', '-s',
        action='store_true',
        help='跳过模型下载，直接运行demo'
    )
    
    args = parser.parse_args()
    
    # 下载模型（除非明确跳过）
    if not args.skip_download:
        download_models(args.model, args.format)
        print("\n")
    else:
        print("⏭️  跳过模型下载\n")
    
    # 运行主示例
    main()
