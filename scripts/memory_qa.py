#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
记忆问答脚本 (Memory QA)
基于记忆库回答 Locomo 数据集中的问题

对应提示词：
- src/tinymem0/prompts/question_answering.py → 基于记忆回答问题

前置条件：
  先运行 memory_ingestion.py 完成记忆写入

流程：
  1. 加载 Locomo 数据集的 QA 问题
  2. 从记忆库搜索相关记忆
  3. 基于记忆生成答案
  4. 与标准答案对比评分（可选）

评测模式：
  - EVAL_TEST_MODE=true  → 测试模式：仅第一个 conversation 的 QA
  - EVAL_TEST_MODE=false → 完整模式：全部 conversation 的 QA
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
    get_user_id,
    FALLBACK_DATA_PATH
)
from evaluation.locomo_adapter import LocomoAdapter


# =============================================================================
# 日志记录器
# =============================================================================

class QALogger(BaseLogger):
    """问答日志记录器"""
    
    def __init__(self, verbose: bool = True):
        super().__init__(verbose)
        self.stats = {
            "conversations_processed": 0,
            "questions_processed": 0,
            "search_success": 0,
            "search_empty": 0,
            "errors": 0
        }


# =============================================================================
# 核心函数：记忆问答
# =============================================================================

def run_qa(
    config: Optional[Dict] = None,
    logger: Optional[QALogger] = None
) -> bool:
    """
    记忆问答主函数
    
    遍历逻辑：conversations → qa_list → search → answer
    
    调用链路：
    1. 加载 QA 问题
    2. search_memory() 搜索相关记忆
    3. 基于 question_answering.py 提示词生成答案
    4. 与标准答案对比
    
    范围由 config['test_mode'] 控制：
    - test_mode=True  → 仅 conversation[0] 的 QA
    - test_mode=False → 全部 conversations 的 QA
    
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
        logger = QALogger(verbose=True)
    
    # 从配置读取搜索限制
    search_limit = config.get('qa_search_limit', 5)
    
    # 根据 test_mode 决定遍历范围
    test_mode = config.get('test_mode', True)
    
    if test_mode:
        max_conversations = 1
        mode_desc = "测试模式 (EVAL_TEST_MODE=true)"
    else:
        max_conversations = None
        mode_desc = "完整模式 (EVAL_TEST_MODE=false)"
    
    print_header(f"记忆问答 - {mode_desc}")
    print_config(config, {
        "max_conversations": max_conversations if max_conversations else "全部"
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
        
        # 连接记忆库 - 使用工厂函数确保与 memory_ingestion.py 一致
        try:
            memory_a = create_memory_system(speaker_a, conv_idx, config)
            memory_b = create_memory_system(speaker_b, conv_idx, config)
            logger.log("SUCCESS", f"记忆库连接成功: {speaker_a} / {speaker_b}")
        except Exception as e:
            logger.log("ERROR", f"记忆库连接失败: {e}")
            logger.log("WARN", "请先运行 memory_ingestion.py 完成记忆写入")
            logger.stats["errors"] += 1
            continue
        
        # =====================================================================
        # 步骤3: 遍历 QA 问题
        # =====================================================================
        qa_list = conversation_data.get('qa', [])
        
        if not qa_list:
            logger.log("WARN", f"Conversation {conv_idx} 没有 QA 数据，跳过")
            continue
        
        logger.log("INFO", f"共 {len(qa_list)} 个 QA 问题")
        
        for qa_idx, qa in enumerate(qa_list, 1):
            _process_single_qa(
                qa=qa,
                qa_idx=qa_idx,
                total_qa=len(qa_list),
                speaker_a=speaker_a,
                speaker_b=speaker_b,
                conv_idx=conv_idx,
                memory_a=memory_a,
                memory_b=memory_b,
                logger=logger,
                search_limit=search_limit
            )
        
        logger.stats["conversations_processed"] += 1
    
    # =========================================================================
    # 最终统计
    # =========================================================================
    logger.print_stats("问答统计")
    print_header("问答评测完成")
    
    return logger.stats["errors"] == 0


def _process_single_qa(
    qa: Dict,
    qa_idx: int,
    total_qa: int,
    speaker_a: str,
    speaker_b: str,
    conv_idx: int,
    memory_a,
    memory_b,
    logger: QALogger,
    search_limit: int
):
    """
    处理单个 QA 问题（内部函数）
    
    Args:
        qa: QA 数据字典
        qa_idx: 问题索引
        total_qa: 问题总数
        speaker_a: Speaker A 名称
        speaker_b: Speaker B 名称
        conv_idx: Conversation 索引
        memory_a: Speaker A 的记忆系统
        memory_b: Speaker B 的记忆系统
        logger: 日志记录器
        search_limit: 搜索限制
    """
    print_header(f"Question {qa_idx}/{total_qa}", level=3)
    
    question = qa.get('question', '')
    expected_answer = qa.get('answer', '')
    qa_type = qa.get('type', 'unknown')
    
    # 显示问题
    question_display = f"问题: {question[:60]}..." if len(question) > 60 else f"问题: {question}"
    logger.log("QA", question_display)
    logger.log("INFO", f"类型: {qa_type}")
    
    # 选择搜索视角（默认使用 speaker_a）
    # TODO: 可根据问题内容智能选择视角
    user_id = get_user_id(speaker_a, conv_idx)
    memory = memory_a
    
    # =================================================================
    # 步骤4: 搜索相关记忆
    # =================================================================
    try:
        results = memory.search_memory(
            query=question,
            user_id=user_id,
            limit=search_limit
        )
        
        if results:
            logger.stats["search_success"] += 1
            logger.log("SEARCH", f"找到 {len(results)} 条相关记忆")
            
            for j, result in enumerate(results, 1):
                text = result['text'][:70] + "..." if len(result['text']) > 70 else result['text']
                score = result.get('score', 0.0)
                print(f"           {j}. [{score:.3f}] {text}")
        else:
            logger.stats["search_empty"] += 1
            logger.log("WARN", "未找到相关记忆")
            
    except Exception as e:
        logger.log("ERROR", f"搜索失败: {e}")
        logger.stats["errors"] += 1
        return
    
    # =================================================================
    # 步骤5: 显示期望答案（用于对比）
    # TODO: 可扩展为调用 LLM 生成答案并计算 F1
    # =================================================================
    if expected_answer:
        expected_display = expected_answer[:80] + "..." if len(expected_answer) > 80 else expected_answer
        logger.log("ANSWER", f"期望答案: {expected_display}")
    
    logger.stats["questions_processed"] += 1


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Locomo 记忆问答 (Memory QA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能说明:
  基于记忆库回答 Locomo 数据集中的问题
  
  调用链路:
    问题 → search_memory → question_answering.py → 答案

前置条件:
  先运行 memory_ingestion.py 完成记忆写入

示例:
  # 默认：根据 EVAL_TEST_MODE 环境变量自动决定范围
  python memory_qa.py
  
  # EVAL_TEST_MODE=true  → 测试模式：仅 conversation 0 的 QA
  # EVAL_TEST_MODE=false → 完整模式：全部 conversation 的 QA

环境变量配置（.env）:
  EVAL_TEST_MODE=true    # 测试模式
  EVAL_TEST_MODE=false   # 完整模式
  QA_SEARCH_LIMIT=5      # 问答搜索记忆数量限制
        """
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
    
    # 创建日志记录器
    logger = QALogger(verbose=args.verbose)
    
    # 执行问答评测
    success = run_qa(config=config, logger=logger)
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
