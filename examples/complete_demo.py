#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
记忆系统使用示例 - 从.env读取配置并运行
所有配置通过.env文件管理，无需命令行参数
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from tinymem0 import MemorySystem


def str_to_bool(value: str) -> bool:
    """将字符串转换为布尔值"""
    if not value:
        return False
    return value.lower() in ('true', '1', 'yes', 'on')


def download_models():
    """从.env读取配置并下载模型"""
    # 读取配置
    use_local_llm = str_to_bool(os.getenv('USE_LOCAL_LLM', 'false'))
    skip_download = str_to_bool(os.getenv('SKIP_DOWNLOAD', 'false'))
    model_shortcut = os.getenv('MODEL_SHORTCUT', 'mistral-7b')
    model_format = os.getenv('MODEL_FORMAT', 'gguf')
    quantization = os.getenv('MODEL_QUANTIZATION', 'Q4_K_M')
    embedding_model = os.getenv('LOCAL_EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')
    hf_token = os.getenv('HF_TOKEN')  # 从.env读取HuggingFace令牌
    
    print("=" * 70)
    print("📦 检查并下载模型")
    print("=" * 70)
    print(f"\n配置信息（来自 .env）:")
    print(f"  USE_LOCAL_LLM: {use_local_llm}")
    print(f"  MODEL_SHORTCUT: {model_shortcut}")
    print(f"  MODEL_FORMAT: {model_format}")
    print(f"  MODEL_QUANTIZATION: {quantization}")
    print(f"  SKIP_DOWNLOAD: {skip_download}")
    
    # 1. 下载嵌入模型（调用底层工具）
    print("\n1️⃣ 嵌入模型...")
    print(f"   模型: {embedding_model}")
    
    sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
    from model_manager.downloader import download_embedding_model
    
    try:
        download_embedding_model(model_id=embedding_model)
    except Exception as e:
        print(f"   ⚠️  嵌入模型预下载失败（首次使用时会自动下载）: {e}")
    
    # 2. 检查LLM模型
    print("\n2️⃣ LLM模型...")
    
    if not use_local_llm:
        print("   ⏭️  云端API模式，无需下载")
        print("\n" + "=" * 70)
        return None
    
    if skip_download:
        print("   ⏭️  已设置 SKIP_DOWNLOAD=true，跳过下载")
        print("\n" + "=" * 70)
        return None
    
    # 调用底层下载工具
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
    from download_llm import download_model_with_shortcut
    
    try:
        downloaded_path = download_model_with_shortcut(
            model_shortcut=model_shortcut,
            model_format=model_format,
            quantization=quantization,
            verbose=True,
            hf_token=hf_token  # 传递HF令牌到下层
        )
        
        print(f"\n   ✅ 模型就绪")
        print(f"   📂 位置: {downloaded_path}")
        print("\n" + "=" * 70)
        return downloaded_path
        
    except Exception as e:
        print(f"\n   ❌ 下载失败: {e}")
        print("   💡 请检查网络连接或手动下载模型")
        print("\n" + "=" * 70)
        return None


def main():
    """主函数 - 演示记忆系统的使用（从.env读取所有配置）"""
    # 从.env读取配置
    use_local_llm = str_to_bool(os.getenv('USE_LOCAL_LLM', 'false'))
    local_model_path = os.getenv('LOCAL_MODEL_PATH', '')
    local_embedding_model = os.getenv('LOCAL_EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')
    embedding_dim_str = os.getenv('EMBEDDING_DIM', '')
    
    # 自动设置embedding_dim
    if embedding_dim_str:
        embedding_dim = int(embedding_dim_str)
    else:
        embedding_dim = 512 if use_local_llm else 1536
    
    # 验证配置
    if not use_local_llm and not os.getenv("DASHSCOPE_API_KEY"):
        raise RuntimeError(
            "使用云端API需要配置 DASHSCOPE_API_KEY\n"
            "请在 .env 文件中设置: DASHSCOPE_API_KEY=your_api_key_here"
        )
    
    mode = "本地模型" if use_local_llm else "云端API"
    if use_local_llm and local_model_path:
        print(f"初始化记忆系统 ({mode}: {local_model_path})...")
    else:
        print(f"初始化记忆系统 ({mode})...")
    
    memory_system = MemorySystem(
        use_local_llm=use_local_llm,
        local_model_path=local_model_path,
        local_embedding_model=local_embedding_model,
        embedding_dim=embedding_dim
    )
    
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
    
    memory = MemorySystem(
        collection_name="demo_update",
        use_local_llm=use_local,
        local_model_path=local_model_path,
        local_embedding_model=local_embedding_model,
        embedding_dim=embedding_dim
    )
    
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
    
    memory = MemorySystem(
        collection_name="demo_multiuser",
        use_local_llm=use_local,
        local_model_path=local_model_path,
        local_embedding_model=local_embedding_model,
        embedding_dim=embedding_dim
    )
    
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
    
    memory = MemorySystem(
        collection_name="demo_facts",
        use_local_llm=use_local,
        local_model_path=local_model_path,
        local_embedding_model=local_embedding_model,
        embedding_dim=embedding_dim
    )
    
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
    
    memory = MemorySystem(
        collection_name="demo_search",
        use_local_llm=use_local,
        local_model_path=local_model_path,
        local_embedding_model=local_embedding_model,
        embedding_dim=embedding_dim
    )
    
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
    print("=" * 70)
    print("TinyMem0 记忆系统完整示例")
    print("配置来源: .env 文件")
    print("=" * 70)
    
    # 下载模型（根据.env配置）
    downloaded_path = download_models()
    
    # 如果下载了模型，更新.env中的LOCAL_MODEL_PATH
    if downloaded_path:
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            lines = []
            updated = False
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('LOCAL_MODEL_PATH='):
                        lines.append(f'LOCAL_MODEL_PATH={downloaded_path}\n')
                        updated = True
                    else:
                        lines.append(line)
            
            if updated:
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"\n✅ 已更新 .env: LOCAL_MODEL_PATH={downloaded_path}\n")
                # 重新加载.env
                load_dotenv(override=True)
    
    # 运行主示例
    main()
