#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locomo 数据集评测适配器
实现双视角记忆机制，将两人对话转换为两个独立的用户记忆库
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path


class LocomoAdapter:
    """
    Locomo 数据集适配器
    
    核心功能：
    1. 读取 locomo 数据集的双人对话
    2. 实现视角转换：为每个 speaker 创建独立的消息列表
    3. Speaker A 说的话 → Speaker A 视角下是 user，Speaker B 视角下是 assistant
    4. Speaker B 说的话 → Speaker B 视角下是 user，Speaker A 视角下是 assistant
    """
    
    def __init__(self, data_path: str):
        """
        初始化适配器
        
        Args:
            data_path: locomo 数据集 JSON 文件路径
        """
        self.data_path = Path(data_path)
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """加载 locomo 数据集"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 加载 {len(data)} 个对话场景")
        return data
    
    def get_total_conversations(self) -> int:
        """
        获取数据集中 conversation 的总数
        
        Returns:
            conversation 数量
        """
        return len(self.data)
    
    def get_conversation_pair(self, idx: int = 0) -> Dict:
        """
        获取指定索引的对话场景
        
        Args:
            idx: 对话场景索引
            
        Returns:
            对话数据字典，包含 conversation 和 qa 等字段
        """
        if idx >= len(self.data):
            raise IndexError(f"索引 {idx} 超出范围，数据集共有 {len(self.data)} 个场景")
        
        return self.data[idx]
    
    def get_session_dialogs(
        self, 
        conversation: Dict, 
        session_num: int = 1
    ) -> Tuple[str, str, List[Dict]]:
        """
        提取指定 session 的对话内容
        
        Args:
            conversation: 对话数据（包含 speaker_a, speaker_b, session_1 等）
            session_num: session 编号（1-35）
            
        Returns:
            (speaker_a_name, speaker_b_name, dialogs)
            - speaker_a_name: Speaker A 的名字
            - speaker_b_name: Speaker B 的名字
            - dialogs: 对话列表 [{"speaker": "Caroline", "dia_id": "D1:1", "text": "..."}]
        """
        speaker_a = conversation['speaker_a']
        speaker_b = conversation['speaker_b']
        session_key = f'session_{session_num}'
        
        if session_key not in conversation:
            raise ValueError(f"Session {session_num} 不存在于此对话中")
        
        dialogs = conversation[session_key]
        return speaker_a, speaker_b, dialogs
    
    def convert_to_dual_perspective(
        self,
        speaker_a: str,
        speaker_b: str,
        dialogs: List[Dict],
        conversation_idx: int = 0
    ) -> Tuple[str, List[Dict], str, List[Dict]]:
        """
        将对话转换为双视角格式（核心功能）
        
        视角转换规则：
        - Speaker A 视角：A 说的话是 "user"，B 说的话是 "assistant"
        - Speaker B 视角：B 说的话是 "user"，A 说的话是 "assistant"
        
        Args:
            speaker_a: Speaker A 的名字
            speaker_b: Speaker B 的名字
            dialogs: 对话列表
            conversation_idx: 对话场景索引（用于生成唯一 user_id）
            
        Returns:
            (
                speaker_a_user_id,     # 如 "Caroline_0"
                messages_a,            # Speaker A 的消息列表（dict格式）
                speaker_b_user_id,     # 如 "Melanie_0"
                messages_b             # Speaker B 的消息列表（dict格式）
            )
            
        消息格式示例：
            messages_a = [
                {"role": "user", "content": "Caroline: Hey Mel! Good to see you!"},
                {"role": "assistant", "content": "Melanie: Hey Caroline! I'm swamped with the kids."},
                {"role": "user", "content": "Caroline: I went to a LGBTQ support group yesterday."}
            ]
        """
        # 生成唯一的 user_id
        speaker_a_user_id = f"{speaker_a}_{conversation_idx}"
        speaker_b_user_id = f"{speaker_b}_{conversation_idx}"
        
        # 初始化两个视角的消息列表
        messages_a = []  # Speaker A 的视角
        messages_b = []  # Speaker B 的视角
        
        for dialog in dialogs:
            speaker = dialog['speaker']
            text = dialog['text']
            
            # 构建消息内容（保留说话者名字）
            content = f"{speaker}: {text}"
            
            if speaker == speaker_a:
                # Speaker A 说话
                # - 在 A 的视角下是 "user"
                # - 在 B 的视角下是 "assistant"
                messages_a.append({"role": "user", "content": content})
                messages_b.append({"role": "assistant", "content": content})
            
            elif speaker == speaker_b:
                # Speaker B 说话
                # - 在 B 的视角下是 "user"
                # - 在 A 的视角下是 "assistant"
                messages_a.append({"role": "assistant", "content": content})
                messages_b.append({"role": "user", "content": content})
        
        return speaker_a_user_id, messages_a, speaker_b_user_id, messages_b
    
    def get_batches(
        self,
        messages: List[Dict],
        batch_size: int = 2
    ) -> List[List[Dict]]:
        """
        将消息列表分批（与 mem0 评测项目保持一致）
        
        Args:
            messages: 消息列表
            batch_size: 每批消息数量，默认 2（1轮对话：1句user + 1句assistant）
            
        Returns:
            分批后的消息列表
            
        示例：
            Input: [msg1, msg2, msg3, msg4, msg5, msg6], batch_size=2
            Output: [[msg1, msg2], [msg3, msg4], [msg5, msg6]]
        """
        batches = []
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def format_batch_for_memory_system(
        self,
        batch: List[Dict]
    ) -> str:
        """
        将一批消息格式化为记忆系统的输入
        
        Args:
            batch: 一批消息，如 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Returns:
            合并后的对话字符串，用于 write_memory
            
        示例：
            Input: [{"role": "user", "content": "Caroline: Hey!"}, 
                    {"role": "assistant", "content": "Melanie: Hi!"}]
            Output: "Caroline: Hey!\nMelanie: Hi!"
        """
        contents = [msg["content"] for msg in batch]
        return '\n'.join(contents)
    
    def format_for_memory_system(
        self,
        messages: List[Dict]
    ) -> str:
        """
        将完整消息列表格式化为记忆系统的输入（兼容旧接口）
        
        Args:
            messages: 消息列表（dict格式）
            
        Returns:
            合并后的对话字符串
        """
        contents = [msg["content"] for msg in messages]
        return '\n'.join(contents)
    
    def get_all_sessions(self, conversation: Dict) -> List[int]:
        """
        获取对话中所有有效的 session 编号
        
        Args:
            conversation: 对话数据
            
        Returns:
            session 编号列表，如 [1, 2, 3, ..., 15]
        """
        sessions = []
        for i in range(1, 36):  # locomo 最多 35 个 session
            if f'session_{i}' in conversation and conversation[f'session_{i}']:
                sessions.append(i)
        return sessions


def demo_usage():
    """演示如何使用 LocomoAdapter"""
    print("=" * 70)
    print("Locomo 适配器演示")
    print("=" * 70)
    
    # 1. 初始化适配器
    adapter = LocomoAdapter('locomo/data/locomo1.json')
    
    # 2. 获取第一个对话场景
    conversation_data = adapter.get_conversation_pair(idx=0)
    conversation = conversation_data['conversation']
    
    print(f"\n📖 对话场景 0:")
    print(f"   Speaker A: {conversation['speaker_a']}")
    print(f"   Speaker B: {conversation['speaker_b']}")
    
    # 3. 获取 Session 1 的对话
    speaker_a, speaker_b, dialogs = adapter.get_session_dialogs(conversation, session_num=1)
    print(f"\n💬 Session 1 ({conversation['session_1_date_time']}):")
    print(f"   共 {len(dialogs)} 条消息")
    
    # 4. 视角转换
    user_id_a, messages_a, user_id_b, messages_b = adapter.convert_to_dual_perspective(
        speaker_a, speaker_b, dialogs, conversation_idx=0
    )
    
    print(f"\n🔄 视角转换结果:")
    print(f"\n   【{speaker_a} 的视角】 (user_id: {user_id_a})")
    print(f"   消息数量: {len(messages_a)}")
    print(f"   前3条消息:")
    for i, msg in enumerate(messages_a[:3], 1):
        print(f"      {i}. role={msg['role']}, content={msg['content'][:50]}...")
    
    print(f"\n   【{speaker_b} 的视角】 (user_id: {user_id_b})")
    print(f"   消息数量: {len(messages_b)}")
    print(f"   前3条消息:")
    for i, msg in enumerate(messages_b[:3], 1):
        print(f"      {i}. role={msg['role']}, content={msg['content'][:50]}...")
    
    # 5. 分批处理（batch_size=2，与 mem0 评测项目一致）
    batches_a = adapter.get_batches(messages_a, batch_size=2)
    
    print(f"\n📦 分批处理（batch_size=2）:")
    print(f"   总消息数: {len(messages_a)}")
    print(f"   分批数量: {len(batches_a)}")
    
    print(f"\n   前3个批次:")
    for i, batch in enumerate(batches_a[:3], 1):
        print(f"\n   【批次 {i}】")
        for msg in batch:
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            print(f"      {role_emoji} {msg['role']}: {msg['content'][:50]}...")
        
        # 格式化为记忆系统输入
        batch_text = adapter.format_batch_for_memory_system(batch)
        print(f"      → 输入文本: {batch_text[:80]}...")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo_usage()
