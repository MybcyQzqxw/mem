#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
记忆写入脚本 (Memory Ingestion)
将 Locomo 数据集的对话内容写入记忆库

对应提示词：
- src/tinymem0/prompts/fact_extraction.py   → 从对话提取事实
- src/tinymem0/prompts/memory_processing.py → 记忆增删改查

遍历层级：
  conversations[0..9] → sessions[1..N] → dialogs[0..M] → batches (batch_size)

评测模式：
  - EVAL_TEST_MODE=true  → 测试模式：仅第一个 conversation 的第一个 session
  - EVAL_TEST_MODE=false → 完整模式：全部 conversation 的全部 session
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

# 导入共享模块
from evaluation.eval_common import (
    load_config,
    print_header,
    print_config,
    BaseLogger,
    create_memory_system,
    FALLBACK_DATA_PATH
)
from evaluation.locomo_adapter import LocomoAdapter


# =============================================================================
# 日志记录器
# =============================================================================

class IngestionLogger(BaseLogger):
    """记忆写入日志记录器"""
    
    def __init__(self, verbose: bool = True):
        super().__init__(verbose)
        self.stats = {
            "conversations_processed": 0,
            "sessions_processed": 0,
            "batches_processed": 0,
            "total_messages": 0,
            "errors": 0
        }
    
    def log_batch_start(self, batch_idx: int, total_batches: int, batch: List[Dict]):
        """记录批次开始"""
        self.log("BATCH", f"批次 {batch_idx}/{total_batches} 开始处理")
        for msg in batch:
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            print(f"           │ {role_icon} {msg['role']}: {content}")
    
    def log_batch_complete(self, batch_idx: int):
        """记录批次完成"""
        self.stats["batches_processed"] += 1
        print(f"           └─ 批次处理完成")
    
    def log_session_summary(self, conv_idx: int, session_num: int, batches_count: int, speaker: str):
        """记录 session 摘要"""
        self.stats["sessions_processed"] += 1
        self.log("SUCCESS", f"Conv{conv_idx}/Session{session_num} ({speaker}) 完成: {batches_count} 个批次")


# =============================================================================
# 核心函数：记忆写入
# =============================================================================

def run_ingestion(
    config: Optional[Dict] = None,
    logger: Optional[IngestionLogger] = None
) -> bool:
    """
    记忆写入主函数
    
    遍历逻辑：conversations → sessions → dialogs → batches
    
    调用链路：
    1. 加载对话数据
    2. 视角转换（双视角）
    3. 分批处理
    4. write_memory() → fact_extraction.py → memory_processing.py
    
    范围由 config['test_mode'] 控制：
    - test_mode=True  → 仅 conversation[0] 的 session[0]
    - test_mode=False → 全部 conversations 的全部 sessions
    
    Args:
        config: 配置字典
        logger: 日志记录器
        
    Returns:
        bool: 是否成功完成
    """
    # 初始化
    if config is None:
        config = load_config()
    
    if logger is None:
        logger = IngestionLogger(verbose=True)
    
    # 根据 test_mode 决定遍历范围
    test_mode = config.get('test_mode', True)
    
    if test_mode:
        max_conversations = 1
        max_sessions_per_conv = 1
        mode_desc = "测试模式 (EVAL_TEST_MODE=true)"
    else:
        max_conversations = None
        max_sessions_per_conv = None
        mode_desc = "完整模式 (EVAL_TEST_MODE=false)"
    
    print_header(f"记忆写入 - {mode_desc}")
    print_config(config, {
        "max_conversations": max_conversations if max_conversations else "全部",
        "max_sessions_per_conv": max_sessions_per_conv if max_sessions_per_conv else "全部"
    })
    
    # =========================================================================
    # 步骤1: 加载数据集
    # =========================================================================
    print_header("步骤1: 加载数据集", level=3)
    
    try:
        adapter = LocomoAdapter(config['data_path'])
    except FileNotFoundError:
        logger.log("WARN", f"数据集不存在，尝试备选路径: {FALLBACK_DATA_PATH}")
        try:
            adapter = LocomoAdapter(FALLBACK_DATA_PATH)
            config['data_path'] = FALLBACK_DATA_PATH
        except FileNotFoundError:
            logger.log("ERROR", "数据集加载失败")
            return False
    
    total_conversations = adapter.get_total_conversations()
    num_conversations = min(max_conversations, total_conversations) if max_conversations else total_conversations
    
    logger.log("INFO", f"数据集共 {total_conversations} 个 conversation，本次处理 {num_conversations} 个")
    
    batch_size = config['batch_size']
    
    # =========================================================================
    # 步骤2: 遍历 conversations
    # =========================================================================
    for conv_idx in range(num_conversations):
        print_header(f"Conversation {conv_idx + 1}/{num_conversations}", level=2)
        
        # 获取 conversation 数据
        try:
            conversation_data = adapter.get_conversation_pair(idx=conv_idx)
        except IndexError:
            logger.log("ERROR", f"Conversation {conv_idx} 不存在，跳过")
            logger.stats["errors"] += 1
            continue
        
        conversation = conversation_data['conversation']
        speaker_a = conversation['speaker_a']
        speaker_b = conversation['speaker_b']
        
        logger.log("INFO", f"对话双方: {speaker_a} vs {speaker_b}")
        
        # 获取所有 session
        all_sessions = adapter.get_all_sessions(conversation)
        num_sessions = min(max_sessions_per_conv, len(all_sessions)) if max_sessions_per_conv else len(all_sessions)
        
        logger.log("INFO", f"共 {len(all_sessions)} 个 session，本次处理 {num_sessions} 个")
        
        # 创建记忆库（双视角）- 使用工厂函数确保一致性
        try:
            memory_a = create_memory_system(speaker_a, conv_idx, config)
            memory_b = create_memory_system(speaker_b, conv_idx, config)
            logger.log("SUCCESS", f"记忆库初始化完成: {speaker_a} / {speaker_b}")
        except Exception as e:
            logger.log("ERROR", f"记忆库初始化失败: {e}")
            logger.stats["errors"] += 1
            continue
        
        # =====================================================================
        # 步骤3: 遍历 sessions
        # =====================================================================
        for session_i in range(num_sessions):
            session_num = all_sessions[session_i]
            print_header(f"Session {session_num} ({session_i + 1}/{num_sessions})", level=3)
            
            # 提取对话
            speaker_a_name, speaker_b_name, dialogs = adapter.get_session_dialogs(
                conversation, session_num
            )
            
            session_datetime = conversation.get(f'session_{session_num}_date_time', 'Unknown')
            logger.log("INFO", f"对话数: {len(dialogs)}, 时间: {session_datetime}")
            
            # 视角转换
            user_id_a, messages_a, user_id_b, messages_b = adapter.convert_to_dual_perspective(
                speaker_a_name, speaker_b_name, dialogs, conversation_idx=conv_idx
            )
            
            logger.stats["total_messages"] += len(dialogs)
            
            # 分批
            batches_a = adapter.get_batches(messages_a, batch_size=batch_size)
            batches_b = adapter.get_batches(messages_b, batch_size=batch_size)
            
            print(f"   📊 {speaker_a_name}: {len(messages_a)} 条 → {len(batches_a)} 批次")
            print(f"   📊 {speaker_b_name}: {len(messages_b)} 条 → {len(batches_b)} 批次")
            
            # =================================================================
            # 步骤4: 写入 Speaker A 的记忆
            # =================================================================
            _write_batches(
                memory=memory_a,
                batches=batches_a,
                user_id=user_id_a,
                adapter=adapter,
                logger=logger,
                metadata={
                    "conversation_idx": conv_idx,
                    "session_num": session_num,
                    "session_datetime": session_datetime
                }
            )
            logger.log_session_summary(conv_idx, session_num, len(batches_a), speaker_a_name)
            
            # =================================================================
            # 步骤5: 写入 Speaker B 的记忆
            # =================================================================
            _write_batches(
                memory=memory_b,
                batches=batches_b,
                user_id=user_id_b,
                adapter=adapter,
                logger=logger,
                metadata={
                    "conversation_idx": conv_idx,
                    "session_num": session_num,
                    "session_datetime": session_datetime
                }
            )
            logger.log_session_summary(conv_idx, session_num, len(batches_b), speaker_b_name)
        
        logger.stats["conversations_processed"] += 1
    
    # =========================================================================
    # 最终统计
    # =========================================================================
    logger.print_stats("写入统计")
    print_header("记忆写入完成")
    print("\n💡 提示: 运行 memory_qa.py 进行问答评测")
    
    return logger.stats["errors"] == 0


def _write_batches(
    memory,
    batches: List[List[Dict]],
    user_id: str,
    adapter: LocomoAdapter,
    logger: IngestionLogger,
    metadata: Dict
):
    """
    写入多个批次到记忆库（内部函数）
    
    Args:
        memory: MemorySystem 实例
        batches: 批次列表
        user_id: 用户ID
        adapter: Locomo 适配器
        logger: 日志记录器
        metadata: 元数据
    """
    for batch_i, batch in enumerate(batches, 1):
        logger.log_batch_start(batch_i, len(batches), batch)
        
        batch_text = adapter.format_batch_for_memory_system(batch)
        
        try:
            memory.write_memory(
                conversation=batch_text,
                user_id=user_id,
                agent_id="assistant",
                extra_metadata={
                    **metadata,
                    "batch_idx": batch_i
                }
            )
            logger.log_batch_complete(batch_i)
        except Exception as e:
            logger.log("ERROR", f"批次 {batch_i} 写入失败: {e}")
            logger.stats["errors"] += 1


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Locomo 记忆写入 (Memory Ingestion)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能说明:
  将 Locomo 数据集的对话内容写入记忆库
  
  调用链路:
    对话 → fact_extraction.py → memory_processing.py → 记忆库

示例:
  # 默认：根据 EVAL_TEST_MODE 环境变量自动决定范围
  python memory_ingestion.py
  
  # EVAL_TEST_MODE=true  → 测试模式：仅 conversation 0 的 session 1
  # EVAL_TEST_MODE=false → 完整模式：全部 conversation 的全部 session

环境变量配置（.env）:
  EVAL_TEST_MODE=true   # 测试模式
  EVAL_TEST_MODE=false  # 完整模式
  EVAL_BATCH_SIZE=2     # 批次大小
        """
    )
    
    parser.add_argument(
        '-b', '--batch-size',
        type=int,
        default=None,
        help='批次大小（覆盖 .env 中的 EVAL_BATCH_SIZE）'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=True,
        help='详细输出模式 (默认: True)'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 命令行参数覆盖
    if args.batch_size is not None:
        config['batch_size'] = args.batch_size
    
    # 创建日志记录器
    logger = IngestionLogger(verbose=args.verbose)
    
    # 执行记忆写入
    success = run_ingestion(config=config, logger=logger)
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
