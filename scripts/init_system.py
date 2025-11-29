#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TinyMem0 记忆系统初始化脚本
自动化设置完整的记忆系统环境
"""

import sys
import os
from pathlib import Path
import subprocess

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("🚀 TinyMem0 记忆系统初始化向导")
    print("=" * 70)
    print()
    print("本脚本将帮助您完成以下设置:")
    print("  1. 检查并安装必要的依赖")
    print("  2. 下载嵌入模型")
    print("  3. 下载LLM模型")
    print("  4. 配置环境变量")
    print("  5. 运行测试验证")
    print()


def check_dependencies():
    """检查必要的依赖是否已安装"""
    print("=" * 70)
    print("📦 步骤 1: 检查依赖")
    print("=" * 70)
    
    required_packages = {
        'qdrant_client': 'Qdrant向量数据库客户端',
        'dashscope': '阿里云DashScope SDK（可选）',
        'python-dotenv': '环境变量管理',
        'sentence_transformers': '嵌入模型（本地模式需要）',
        'llama_cpp': 'GGUF模型支持（本地模式需要）',
        'transformers': 'SafeTensors模型支持（可选）',
        'huggingface_hub': '模型下载工具'
    }
    
    missing_packages = []
    optional_missing = []
    
    for package, description in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package:20s} - {description}")
        except ImportError:
            if package in ['dashscope', 'transformers', 'llama_cpp']:
                optional_missing.append(package)
                print(f"⚠️  {package:20s} - {description} (可选)")
            else:
                missing_packages.append(package)
                print(f"❌ {package:20s} - {description} (缺失)")
    
    if missing_packages:
        print(f"\n❌ 发现缺失的必需依赖: {', '.join(missing_packages)}")
        print("\n请运行以下命令安装:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    if optional_missing:
        print(f"\n⚠️  可选依赖未安装: {', '.join(optional_missing)}")
        print("根据您选择的LLM模式，可能需要安装这些包")
    
    print("\n✅ 所有必需依赖已安装")
    return True


def check_env_file():
    """检查并创建.env文件"""
    print("\n" + "=" * 70)
    print("📝 步骤 2: 环境配置文件")
    print("=" * 70)
    
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    if env_file.exists():
        print(f"✅ 找到环境配置文件: {env_file}")
        
        # 读取当前配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        has_dashscope = 'DASHSCOPE_API_KEY' in content
        has_local_llm = 'USE_LOCAL_LLM' in content
        
        print(f"  阿里云API配置: {'✅' if has_dashscope else '❌'}")
        print(f"  本地LLM配置: {'✅' if has_local_llm else '❌'}")
        
        return True
    
    elif env_example.exists():
        print(f"⚠️  未找到 .env 文件")
        print(f"📋 发现示例文件: {env_example}")
        
        choice = input("\n是否从示例文件创建 .env? [Y/n]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已创建 .env 文件")
            print("\n⚠️  请编辑 .env 文件，配置必要的参数")
            return True
        else:
            print("❌ 已跳过，请手动创建 .env 文件")
            return False
    
    else:
        print(f"❌ 未找到 .env 或 .env.example 文件")
        return False


def choose_llm_mode():
    """选择LLM模式"""
    print("\n" + "=" * 70)
    print("🤖 步骤 3: 选择LLM模式")
    print("=" * 70)
    print()
    print("请选择LLM模式:")
    print("  [1] 阿里云API (需要API Key，推荐云端使用)")
    print("  [2] 本地模型 (需要下载模型，推荐离线/隐私场景)")
    print()
    
    while True:
        choice = input("请选择 [1/2]: ").strip()
        if choice in ['1', '2']:
            break
        print("❌ 无效输入，请输入 1 或 2")
    
    return 'cloud' if choice == '1' else 'local'


def setup_cloud_mode():
    """配置云端模式"""
    print("\n📡 配置阿里云API模式")
    print("-" * 70)
    
    # 检查是否已有API Key
    env_file = project_root / '.env'
    has_key = False
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'DASHSCOPE_API_KEY=' in content and not content.split('DASHSCOPE_API_KEY=')[1].split('\n')[0].strip().startswith('#'):
                has_key = True
    
    if has_key:
        print("✅ 检测到已配置的 DASHSCOPE_API_KEY")
        choice = input("是否重新配置? [y/N]: ").strip().lower()
        if choice not in ['y', 'yes']:
            print("保持现有配置")
            return True
    
    print("\n请访问 https://dashscope.console.aliyun.com/ 获取API Key")
    api_key = input("请输入您的 DASHSCOPE_API_KEY (或按回车跳过): ").strip()
    
    if api_key:
        # 更新.env文件
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找并更新或添加API Key
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('DASHSCOPE_API_KEY='):
                    lines[i] = f'DASHSCOPE_API_KEY={api_key}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'\nDASHSCOPE_API_KEY={api_key}\n')
            
            # 确保 USE_LOCAL_LLM=false
            use_local_updated = False
            for i, line in enumerate(lines):
                if line.startswith('USE_LOCAL_LLM='):
                    lines[i] = 'USE_LOCAL_LLM=false\n'
                    use_local_updated = True
                    break
            
            if not use_local_updated:
                lines.append('USE_LOCAL_LLM=false\n')
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print("✅ API Key 已保存到 .env 文件")
            return True
        else:
            print("❌ .env 文件不存在，无法保存配置")
            return False
    else:
        print("⚠️  跳过API Key配置，请稍后手动配置")
        return False


def setup_local_mode():
    """配置本地模式"""
    print("\n💻 配置本地模型模式")
    print("-" * 70)
    
    # 1. 下载嵌入模型
    print("\n📥 步骤 3.1: 嵌入模型")
    choice = input("是否下载嵌入模型? [Y/n]: ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        print("\n启动嵌入模型下载...")
        try:
            subprocess.run([
                sys.executable,
                str(project_root / 'scripts' / 'download_embedding.py')
            ], check=False)
        except Exception as e:
            print(f"❌ 下载失败: {e}")
    else:
        print("跳过嵌入模型下载")
    
    # 2. 下载LLM模型
    print("\n📥 步骤 3.2: LLM模型")
    choice = input("是否下载LLM模型? [Y/n]: ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        print("\n启动LLM模型下载...")
        try:
            subprocess.run([
                sys.executable,
                str(project_root / 'scripts' / 'download_llm.py')
            ], check=False)
        except Exception as e:
            print(f"❌ 下载失败: {e}")
    else:
        print("跳过LLM模型下载")
    
    # 3. 配置模型
    print("\n⚙️  步骤 3.3: 配置模型")
    choice = input("是否配置已下载的模型? [Y/n]: ").strip().lower()
    
    if choice in ['', 'y', 'yes']:
        print("\n启动模型配置...")
        try:
            subprocess.run([
                sys.executable,
                str(project_root / 'scripts' / 'setup_llm.py')
            ], check=False)
        except Exception as e:
            print(f"❌ 配置失败: {e}")
    else:
        print("跳过模型配置")
    
    # 4. 更新.env设置本地模式
    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('USE_LOCAL_LLM='):
                lines[i] = 'USE_LOCAL_LLM=true\n'
                updated = True
                break
        
        if not updated:
            lines.append('\nUSE_LOCAL_LLM=true\n')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("\n✅ 已在 .env 中设置 USE_LOCAL_LLM=true")
    
    return True


def run_test():
    """运行测试验证"""
    print("\n" + "=" * 70)
    print("🧪 步骤 4: 运行测试")
    print("=" * 70)
    
    choice = input("\n是否运行测试验证系统配置? [Y/n]: ").strip().lower()
    
    if choice not in ['', 'y', 'yes']:
        print("跳过测试")
        return
    
    print("\n正在测试记忆系统...")
    
    try:
        # 动态导入以避免过早失败
        from dotenv import load_dotenv
        load_dotenv()
        
        sys.path.insert(0, str(project_root / 'src'))
        from tinymem0 import MemorySystem
        
        print("  ✅ 成功导入 MemorySystem")
        
        # 尝试初始化
        memory = MemorySystem()
        print("  ✅ 成功初始化记忆系统")
        
        # 简单测试
        test_conversation = "你好，这是一条测试消息"
        memory.write_memory(test_conversation, user_id="test_user", agent_id="test_agent")
        print("  ✅ 成功写入测试记忆")
        
        results = memory.search_memory("测试", user_id="test_user", limit=1)
        print(f"  ✅ 成功搜索记忆 (找到 {len(results)} 条)")
        
        print("\n✅ 所有测试通过！记忆系统已就绪")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("\n请检查配置并查看错误信息")
        return False
    
    return True


def print_summary():
    """打印完成总结"""
    print("\n" + "=" * 70)
    print("🎉 初始化完成")
    print("=" * 70)
    print()
    print("📋 下一步:")
    print("  1. 查看示例: python examples/basic_usage.py")
    print("  2. 阅读文档: docs/PROJECT_ARCHITECTURE.md")
    print("  3. 开始开发您的应用")
    print()
    print("🛠️  常用命令:")
    print("  - 下载嵌入模型: python scripts/download_embedding.py")
    print("  - 下载LLM模型: python scripts/download_llm.py")
    print("  - 配置LLM: python scripts/setup_llm.py")
    print("  - 运行评测: python scripts/evaluate_system.py")
    print()
    print("📚 获取帮助:")
    print("  - GitHub Issues: https://github.com/MybcyQzqxw/mem/issues")
    print("  - 项目文档: README.md")
    print("=" * 70)


def main():
    """主函数"""
    print_banner()
    
    # 步骤1: 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装缺失的依赖，然后重新运行此脚本")
        sys.exit(1)
    
    # 步骤2: 检查环境文件
    if not check_env_file():
        print("\n❌ 环境配置文件缺失，请先创建 .env 文件")
        sys.exit(1)
    
    # 步骤3: 选择并配置LLM模式
    mode = choose_llm_mode()
    
    if mode == 'cloud':
        setup_cloud_mode()
    else:
        setup_local_mode()
    
    # 步骤4: 运行测试
    run_test()
    
    # 打印总结
    print_summary()


if __name__ == "__main__":
    main()
