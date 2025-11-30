import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import dashscope
from dashscope import Generation

# 导入prompt模块
from .prompts import FACT_EXTRACTION_PROMPT, MEMORY_PROCESSING_PROMPT
# 导入适配器（TinyMem0特定）
from .adapters import extract_llm_response_content, call_llm_with_prompt, handle_llm_error, extract_embedding_from_response

# 导入推理工具 - 添加父目录到路径
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
from utils.inference import parse_json_response

class MemorySystem:
    def __init__(
        self,
        collection_name: str = "memories",
        llm_model: str = "qwen-turbo",
        embedding_model: str = "text-embedding-v1",
        log_mode: Optional[str] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        qdrant_path: Optional[str] = None,
        use_local_llm: Optional[bool] = None,
        local_model_path: Optional[str] = None,
        local_embedding_model: Optional[str] = None,
        embedding_dim: Optional[int] = None
    ):
        """
        初始化记忆系统
        
        Args:
            collection_name: Qdrant集合名称
            llm_model: LLM模型名称（云端API）
            embedding_model: 向量模型名称（云端API）
            log_mode: 日志模式 (plain | json)
            log_level: 日志级别 (debug | info | warn | error)
            log_file: 日志文件路径
            qdrant_path: Qdrant数据存储路径
            use_local_llm: 是否使用本地LLM
            local_model_path: 本地LLM路径
            local_embedding_model: 本地嵌入模型
            embedding_dim: 嵌入向量维度
        """
        self.collection_name = collection_name
        self.qdrant_path = qdrant_path or "./qdrant_data"
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        
        # 参数优先级：构造参数 > 默认值（不再读取.env）
        self.use_local_llm = use_local_llm if use_local_llm is not None else False
        self.local_model_path = local_model_path or ""
        self.local_embedding_model = local_embedding_model or "BAAI/bge-small-zh-v1.5"
        self.embedding_dim = embedding_dim or (512 if self.use_local_llm else 1536)
        # 日志模式: 优先参数，其次环境变量，默认 plain
        self.log_mode = (log_mode or os.getenv("MEM_LOG_MODE") or "plain").lower()
        if self.log_mode not in {"plain", "json"}:
            self.log_mode = "plain"
        # 日志级别: DEBUG < INFO < WARN < ERROR
        self._level_order = {"debug":10, "info":20, "warn":30, "error":40}
        env_level = (os.getenv("MEM_LOG_LEVEL") or "").lower()
        self.log_level = (log_level or env_level or "info").lower()
        if self.log_level not in self._level_order:
            self.log_level = "info"
        # 日志文件
        self.log_file = log_file or os.getenv("MEM_LOG_FILE")
        if self.log_file:
            # 若包含目录则创建
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception as e:
                    # 创建失败则放弃文件写入
                    self.log_file = None
                    print(f"[MEMORY_SYSTEM] 无法创建日志目录 {log_dir}: {e}")
        
        # 初始化Qdrant客户端，使用本地文件存储
        self.qdrant_client = QdrantClient(path=self.qdrant_path)
        
        # 设置API密钥
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        
        # 初始化集合
        self._init_collection()
    
    def _init_collection(self):
        """初始化Qdrant集合"""
        collections = self.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if self.collection_name not in collection_names:
            # 使用实例的embedding_dim
            vector_size = self.embedding_dim
            
            # 创建新集合
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            self._log_event("init", message=f"创建集合: {self.collection_name}, 向量维度: {vector_size}", level="info")
        else:
            self._log_event("init", message=f"使用现有集合: {self.collection_name}", level="info")

    
    def extract_facts(self, conversation: str) -> List[str]:
        """
        从对话中提取事实信息
        
        Args:
            conversation: 用户对话内容
            
        Returns:
            提取的事实列表
        """
        self._log_event("facts_extract_start", level="debug")
        
        if self.use_local_llm:
            # 使用本地LLM
            from utils.inference import call_local_llm
            result = call_local_llm(
                model_path=self.local_model_path,
                system_prompt=FACT_EXTRACTION_PROMPT,
                user_prompt=conversation
            )
        else:
            # 使用云端API
            result = call_llm_with_prompt(self.llm_model, FACT_EXTRACTION_PROMPT, conversation)
        
        if result:
            parsed = parse_json_response(result, 'facts')
            # 确保返回的是列表
            if isinstance(parsed, list):
                return parsed
        return []
     
    
    def get_embeddings(self, text: str, operation: str = "search") -> List[float]:
        """
        获取文本的向量嵌入
        支持阿里云API和本地嵌入模型
        
        Args:
            text: 输入文本
            operation: 操作类型 ("search" 或 "add")
            
        Returns:
            向量嵌入
        """
        if self.use_local_llm:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用全局嵌入模型实例
                if not hasattr(self, '_embedding_model_instance'):
                    model_name = self.local_embedding_model
                    
                    # 检查是否是本地路径
                    if os.path.exists(model_name):
                        self._log_event("loading_embedding_model", model=model_name, level="info")
                        self._embedding_model_instance = SentenceTransformer(model_name)
                    else:
                        # 从HuggingFace下载到固定目录
                        embedding_cache_dir = "./models/embeddings"
                        self._log_event("loading_embedding_model", model=model_name, level="info")
                        print(f"正在加载嵌入模型: {model_name}")
                        print(f"📁 保存到: {embedding_cache_dir}")
                        os.makedirs(embedding_cache_dir, exist_ok=True)
                        self._embedding_model_instance = SentenceTransformer(
                            model_name, 
                            cache_folder=embedding_cache_dir
                        )
                
                self._log_event("embedding_start", level="debug", op=operation)
                embedding = self._embedding_model_instance.encode(text, normalize_embeddings=True)
                emb = embedding.tolist()
                self._log_event("embedding_ok", level="debug", size=len(emb))
                return emb
            except Exception as e:
                self._log_event("embedding_error", error=str(e), level="error")
                return []
        else:
            # 使用阿里云API
            try:
                self._log_event("embedding_start", level="debug", op=operation)
                response = dashscope.TextEmbedding.call(
                    model=self.embedding_model,
                    input=text
                )
                emb = extract_embedding_from_response(response)
                self._log_event("embedding_ok", level="debug", size=len(emb) if emb else 0)
                return emb
            except Exception as e:
                self._log_event("embedding_error", error=str(e), level="error")
                return []
    
    def search_memories(self, query: str, filters: Optional[Dict] = None, 
                       limit: int = 5, threshold: Optional[float] = None) -> List[Dict]:
        """
        搜索相关记忆
        
        Args:
            query: 搜索查询
            filters: 过滤条件
            limit: 返回结果数量限制
            threshold: 相似度阈值
            
        Returns:
            相关记忆列表
        """
        try:
            self._log_event("search_start", query=query, level="debug")
            embeddings = self.get_embeddings(query, "search")
            if not embeddings:
                return []
            
            # 构建Qdrant过滤器
            query_filter = None
            if filters:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = []
                for key, value in filters.items():
                    if value is None:
                        continue
                    conditions.append(FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value)))
                query_filter = Filter(must=conditions)
            
            # 执行向量搜索
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=embeddings,
                limit=limit,
                query_filter=query_filter,
                score_threshold=threshold
            )
            
            memories = []
            for result in search_result:
                # 类型守卫：确保 payload 不为 None
                if result.payload is not None:
                    memories.append({
                        "id": result.id,
                        "text": result.payload.get("data", ""),
                        "score": result.score,
                        "metadata": result.payload.get("metadata", {})
                    })
            
            self._log_event("search_ok", query=query, result_count=len(memories), level="debug")
            return memories
        except Exception as e:
            self._log_event("search_error", error=str(e), level="error")
            return []
    
    def process_memory(self, new_facts: List[str], existing_memories: List[Dict]) -> List[Dict]:
        """
        处理记忆，决定添加、更新、删除或不做操作
        
        Args:
            new_facts: 新提取的事实
            existing_memories: 现有记忆
            
        Returns:
            处理后的记忆列表
        """
        try:
            # 准备输入数据
            input_data = {
                "new_facts": new_facts,
                "existing_memories": existing_memories
            }
            
            if self.use_local_llm:
                # 使用本地LLM
                from utils.inference import call_local_llm
                result = call_local_llm(
                    model_path=self.local_model_path,
                    system_prompt=MEMORY_PROCESSING_PROMPT,
                    user_prompt=json.dumps(input_data, ensure_ascii=False)
                )
            else:
                # 使用云端API
                result = call_llm_with_prompt(
                    self.llm_model, 
                    MEMORY_PROCESSING_PROMPT, 
                    json.dumps(input_data, ensure_ascii=False)
                )
            
            if result:
                parsed = parse_json_response(result, 'memory')
                # 确保返回的是列表
                if isinstance(parsed, list):
                    return parsed
            return []
        except Exception as e:
            self._log_event("process_error", error=str(e), level="error")
            return []
    
    def add_memory(self, text: str, metadata: Optional[Dict] = None) -> str:
        """
        添加新记忆
        
        Args:
            text: 记忆内容
            metadata: 元数据
            
        Returns:
            记忆ID
        """
        try:
            embeddings = self.get_embeddings(text, "add")
            if not embeddings:
                return ""
            
            memory_id = str(uuid.uuid4())
            point = PointStruct(
                id=memory_id,
                vector=embeddings,
                payload={
                    "data": text,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return memory_id
        except Exception as e:
            self._log_event("add_error", error=str(e), level="error")
            return ""
    
    def update_memory(self, memory_id: str, new_text: str, metadata: Optional[Dict] = None):
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            new_text: 新的记忆内容
            metadata: 新的元数据
        """
        try:
            embeddings = self.get_embeddings(new_text, "add")
            if not embeddings:
                return
            
            point = PointStruct(
                id=memory_id,
                vector=embeddings,
                payload={
                    "data": new_text,
                    "metadata": metadata or {},
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            self._log_event("update_error", error=str(e), level="error")
    
    def delete_memory(self, memory_id: str):
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
        """
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id]
            )
        except Exception as e:
            self._log_event("delete_error", error=str(e), level="error")
    
    def write_memory(self, conversation: str, user_id: Optional[str] = None, agent_id: Optional[str] = None, extra_metadata: Optional[Dict] = None):
        """
        记忆写入主流程
        
        Args:
            conversation: 用户对话
            user_id: 用户ID
            agent_id: 代理ID
            extra_metadata: 额外的metadata信息（如session_id, dialog_id等）
        """
        # 1. 提取事实
        new_facts = self.extract_facts(conversation)
        if not new_facts:
            self._log_event("facts_none", message="未提取到相关事实", level="info")
            return
        self._log_event("facts_extracted", facts=new_facts, level="info")
        
        # 2. 检索相关记忆（去重收集）
        retrieved_old_memory_map: Dict[str, Dict[str, str]] = {}
        for new_fact in new_facts:
            filters = {}
            if user_id:
                filters["user_id"] = user_id
            if agent_id:
                filters["agent_id"] = agent_id
            existing_memories = self.search_memories(query=new_fact, filters=filters, limit=5)
            for mem in existing_memories:
                # 以 id 作为唯一键，避免重复加入
                retrieved_old_memory_map[mem["id"]] = {"id": mem["id"], "text": mem["text"]}
        retrieved_old_memory = list(retrieved_old_memory_map.values())
        self._log_event("memories_retrieved", memories=retrieved_old_memory, level="debug")

        # 3. 处理记忆（LLM 返回后进行事件归一化）
        processed_memories_raw = self.process_memory(new_facts, retrieved_old_memory)
        processed_memories = self._normalize_events(processed_memories_raw)
        if processed_memories_raw and len(processed_memories_raw) != len(processed_memories):
            self._log_event(
                "events_normalized",
                raw_count=len(processed_memories_raw),
                normalized_count=len(processed_memories),
                level="debug"
            )

        # 4. 执行记忆操作（按归一化结果）
        for memory in processed_memories:
            event = memory.get("event", "NONE")
            memory_id = memory.get("id")
            text = memory.get("text")
            
            metadata = {
                "user_id": user_id,
                "agent_id": agent_id,
                "created_at": datetime.now().isoformat()
            }
            # 合并额外metadata
            if extra_metadata:
                metadata.update(extra_metadata)
            
            if event == "ADD":
                # 类型守卫：确保 text 不为 None
                if text:
                    self.add_memory(text, metadata)
                    self._log_event("memory_add", text=text, metadata=metadata, level="info")
            elif event == "UPDATE":
                # 类型守卫：确保 memory_id 和 text 不为 None
                if memory_id and text:
                    self.update_memory(memory_id, text, metadata)
                    self._log_event("memory_update", id=memory_id, text=text, metadata=metadata, level="info")
            elif event == "DELETE":
                # 类型守卫：确保 memory_id 不为 None
                if memory_id:
                    self.delete_memory(memory_id)
                    self._log_event("memory_delete", id=memory_id, text=text, level="info")
            elif event == "NONE":
                self._log_event("memory_none", id=memory_id, text=text, level="debug")
    
    def search_memory(self, query: str, user_id: Optional[str] = None, agent_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        记忆搜索
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            agent_id: 代理ID
            limit: 返回结果数量
            
        Returns:
            相关记忆列表
        """
        # 构建过滤条件
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = agent_id
        
        return self.search_memories(query, filters, limit) 

    # ================= 内部工具方法 =================
    def _normalize_events(self, memories: List[Dict]) -> List[Dict]:
        """对 LLM 返回的 memory 事件结果进行归一化与去重。

        规则：
        1. 同一个 id 只保留优先级最高的事件（DELETE > UPDATE > ADD > NONE）
        2. 多个 ADD 如 text 完全相同，则仅保留一条
        3. NONE 事件如果与其它事件冲突（同 id 已有更高优先级），会被丢弃
        4. 保持输出的事件列表顺序尽量稳定：先保留去重后的 ADD，其余按出现顺序合并
        """
        if not memories:
            return []

        priority = {"DELETE": 4, "UPDATE": 3, "ADD": 2, "NONE": 1}
        by_id: Dict[str, Dict] = {}
        add_seen_text = set()
        result_adds: List[Dict] = []

        ordered_non_add_ids = []  # 记录非 ADD 事件的 id 顺序用于稳定输出

        for m in memories:
            event = m.get("event", "NONE")
            mid = m.get("id")
            text = m.get("text")

            # 处理 ADD：用 text 去重（没有 id 或者 id 是新生成的占位）
            if event == "ADD":
                if text in add_seen_text:
                    continue
                add_seen_text.add(text)
                result_adds.append(m)
                continue

            # 处理有 id 的其它事件
            if mid:
                prev = by_id.get(mid)
                if (not prev) or priority.get(event, 0) > priority.get(prev["__event"], 0):
                    by_id[mid] = {**m, "__event": event}
                    if mid not in ordered_non_add_ids:
                        ordered_non_add_ids.append(mid)
            # 没有 id 且不是 ADD 的 NONE/UPDATE/DELETE（不合法），忽略

        # 汇总：先 ADD，再按 id 顺序输出其它事件
        normalized = list(result_adds)
        for mid in ordered_non_add_ids:
            item = by_id[mid]
            item.pop("__event", None)
            normalized.append(item)

        return normalized

    def _log_event(self, event: str, level: str = "info", **data):
        """统一日志输出。

        plain 输出：简单的人类可读形式。
        json  输出：一行 JSON，包含时间戳与事件名。
        """
        level = (level or "info").lower()
        if level not in self._level_order:
            level = "info"
        # 级别过滤
        if self._level_order[level] < self._level_order.get(self.log_level, 20):
            return
        timestamp = datetime.now().isoformat()
        # 生成消息
        if self.log_mode == "json":
            payload = {"ts": timestamp, "event": event, "level": level.upper(), **data}
            try:
                line = json.dumps(payload, ensure_ascii=False)
            except Exception as e:
                line = f"{{'ts':'{timestamp}','event':'{event}','level':'{level.upper()}','error':'log_json_fail','detail':'{e}'}}"
        else:
            base = f"[{level.upper()}][{event}]"
            if "message" in data:
                base += f" {data['message']}"
            if "text" in data and event not in {"facts_extracted", "memories_retrieved"}:
                base += f" | text={data['text']}"
            if event == "facts_extracted":
                base += f" 提取到的事实: {data.get('facts')}"
            elif event == "memories_retrieved":
                base += f" 相关记忆: {data.get('memories')}"
            elif event == "events_normalized":
                base += f" 事件归一化: {data.get('raw_count')} -> {data.get('normalized_count')}"
            elif event.startswith("memory_"):
                if "id" in data:
                    base += f" | id={data['id']}"
            if "error" in data:
                base += f" | ERROR={data['error']}"
            line = base
        # 控制台输出
        print(line)
        # 文件输出
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
            except Exception:
                pass