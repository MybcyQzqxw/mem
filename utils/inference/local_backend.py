#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地LLM推理引擎模块
支持多种模型格式：
- GGUF: 量化模型，使用 llama-cpp-python
- SafeTensors: 原始精度模型，使用 transformers
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Literal


class LocalLLM:
    """统一的本地LLM推理引擎（支持GGUF和SafeTensors格式）"""
    
    def __init__(
        self, 
        model_path: Optional[str] = None, 
        backend: Literal['auto', 'gguf', 'transformers'] = 'auto',
        n_ctx: int = 4096, 
        n_gpu_layers: int = -1, 
        device: str = 'auto',
        verbose: bool = False
    ):
        """
        初始化本地LLM推理引擎
        
        Args:
            model_path: 模型路径（文件路径或目录路径），如果为None则从环境变量LOCAL_MODEL_PATH读取
            backend: 推理后端 ('auto', 'gguf', 'transformers')
                - 'auto': 自动检测模型格式
                - 'gguf': 使用 llama-cpp-python (用于.gguf文件)
                - 'transformers': 使用 HuggingFace transformers (用于safetensors目录)
            n_ctx: 上下文窗口大小 (仅用于gguf)
            n_gpu_layers: GPU加速层数，-1表示全部 (仅用于gguf)
            device: 设备 ('auto', 'cuda', 'cpu') (仅用于transformers)
            verbose: 是否输出详细日志
        """
        self.model_path = model_path or os.getenv("LOCAL_MODEL_PATH")
        
        if not self.model_path:
            raise ValueError("请设置model_path参数或LOCAL_MODEL_PATH环境变量")
        
        # 标准化路径
        self.model_path = self._resolve_model_path(self.model_path)
        
        # 自动检测后端
        self.backend = self._detect_backend(backend)
        
        print(f"📦 正在加载模型: {self.model_path}")
        print(f"🔧 使用后端: {self.backend}")
        
        # 根据后端加载模型
        if self.backend == 'gguf':
            self._load_gguf_model(n_ctx, n_gpu_layers, verbose)
        elif self.backend == 'transformers':
            self._load_transformers_model(device, verbose)
        
        print("✅ 模型加载完成")
    
    def _resolve_model_path(self, path: str) -> str:
        """解析模型路径，支持相对路径和绝对路径"""
        if os.path.exists(path):
            return path
        
        # 尝试在标准目录下查找
        search_dirs = [
            'models/gguf',
            'models/safetensors', 
            'models',
            '.'
        ]
        
        for base_dir in search_dirs:
            potential_path = os.path.join(base_dir, path)
            if os.path.exists(potential_path):
                return potential_path
        
        raise FileNotFoundError(
            f"找不到模型: {path}\n"
            f"已搜索目录: {', '.join(search_dirs)}"
        )
    
    def _detect_backend(self, backend: str) -> str:
        """自动检测推理后端"""
        if backend != 'auto':
            return backend
        
        path = Path(self.model_path)
        
        # 检测GGUF文件
        if path.is_file() and path.suffix.lower() == '.gguf':
            return 'gguf'
        
        # 检测SafeTensors目录
        if path.is_dir():
            has_safetensors = any(
                f.name.endswith('.safetensors') 
                for f in path.iterdir() 
                if f.is_file()
            )
            has_config = (path / 'config.json').exists()
            
            if has_safetensors and has_config:
                return 'transformers'
        
        raise ValueError(
            f"无法自动检测模型格式: {self.model_path}\n"
            f"请明确指定 backend='gguf' 或 backend='transformers'"
        )
    
    def _load_gguf_model(self, n_ctx: int, n_gpu_layers: int, verbose: bool):
        """加载GGUF格式模型"""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "GGUF后端需要 llama-cpp-python\n"
                "安装: pip install llama-cpp-python>=0.2.0"
            )
        
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose
        )
        self.tokenizer = None
    
    def _load_transformers_model(self, device: str, verbose: bool):
        """加载SafeTensors格式模型"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError:
            raise ImportError(
                "Transformers后端需要 transformers 和 torch\n"
                "安装: pip install transformers>=4.35.0 torch>=2.0.0"
            )
        
        # 设备选择
        if device == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if device == 'cuda' else torch.float32,
            device_map=device,
            trust_remote_code=True
        )
        
        self.device = device
        print(f"🎯 使用设备: {device}")
    
    def generate(self,
                 system_prompt: str,
                 user_content: str,
                 max_tokens: int = 512,
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 stop: Optional[List[str]] = None) -> Optional[str]:
        """
        生成回复（统一接口）
        
        Args:
            system_prompt: 系统提示词
            user_content: 用户输入内容
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: nucleus sampling参数
            stop: 停止词列表
            
        Returns:
            生成的文本
        """
        if self.backend == 'gguf':
            return self._generate_gguf(system_prompt, user_content, max_tokens, temperature, top_p, stop)
        elif self.backend == 'transformers':
            return self._generate_transformers(system_prompt, user_content, max_tokens, temperature, top_p)
    
    def _generate_gguf(self,
                       system_prompt: str,
                       user_content: str,
                       max_tokens: int,
                       temperature: float,
                       top_p: float,
                       stop: Optional[List[str]]) -> Optional[str]:
        """GGUF后端的生成实现"""
        try:
            # JSON约束增强
            enhanced_system = system_prompt
            if 'json' in system_prompt.lower() or 'JSON' in system_prompt:
                enhanced_system = system_prompt + "\n\nIMPORTANT: You MUST respond with valid JSON only. Do not include any explanatory text before or after the JSON object."
            
            # 构建Qwen格式的prompt
            prompt = f"""<|im_start|>system
{enhanced_system}<|im_end|>
<|im_start|>user
{user_content}<|im_end|>
<|im_start|>assistant
"""
            
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or ["<|im_end|>"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['text'].strip()
            return None
            
        except Exception as e:
            print(f"❌ GGUF生成异常: {e}")
            return None
    
    def _generate_transformers(self,
                               system_prompt: str,
                               user_content: str,
                               max_tokens: int,
                               temperature: float,
                               top_p: float) -> Optional[str]:
        """Transformers后端的生成实现"""
        try:
            # 构建对话格式
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content}
            ]
            
            # 使用tokenizer的聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            
            # 解码输出
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            print(f"❌ Transformers生成异常: {e}")
            return None
    
    def chat(self, messages: List[Dict[str, str]],
             max_tokens: int = 512,
             temperature: float = 0.7,
             top_p: float = 0.9) -> Optional[str]:
        """
        聊天接口（统一接口）
        
        Args:
            messages: 消息列表，每个消息包含role和content
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: nucleus sampling参数
            
        Returns:
            生成的文本
        """
        if self.backend == 'gguf':
            return self._chat_gguf(messages, max_tokens, temperature, top_p)
        elif self.backend == 'transformers':
            return self._chat_transformers(messages, max_tokens, temperature, top_p)
    
    def _chat_gguf(self,
                   messages: List[Dict[str, str]],
                   max_tokens: int,
                   temperature: float,
                   top_p: float) -> Optional[str]:
        """GGUF后端的聊天实现"""
        try:
            # JSON约束增强
            enhanced_messages = messages.copy()
            if enhanced_messages and enhanced_messages[0]['role'] == 'system':
                system_content = enhanced_messages[0]['content']
                if 'json' in system_content.lower():
                    enhanced_messages[0]['content'] = (
                        system_content +
                        "\n\nCRITICAL: You MUST respond ONLY with valid JSON. "
                        "Start with { and end with }. Do NOT include any text "
                        "before or after the JSON object."
                    )
            
            response = self.model.create_chat_completion(
                messages=enhanced_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content'].strip()
            return None
            
        except Exception as e:
            print(f"❌ GGUF聊天异常: {e}")
            return None
    
    def _chat_transformers(self,
                           messages: List[Dict[str, str]],
                           max_tokens: int,
                           temperature: float,
                           top_p: float) -> Optional[str]:
        """Transformers后端的聊天实现"""
        try:
            # 使用tokenizer的聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.tokenizer([text], return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            print(f"❌ Transformers聊天异常: {e}")
            return None


# 全局LLM实例（单例模式）
_llm_instance: Optional[LocalLLM] = None


def get_local_llm(model_path: Optional[str] = None,
                  backend: str = 'auto',
                  n_ctx: int = 4096,
                  n_gpu_layers: int = -1,
                  device: str = 'auto') -> LocalLLM:
    """
    获取全局LLM实例（单例模式）
    避免重复加载模型，节省内存
    
    Args:
        model_path: 模型路径
        backend: 推理后端
        n_ctx: 上下文窗口
        n_gpu_layers: GPU层数
        device: 设备选择
        
    Returns:
        LocalLLM实例
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM(
            model_path=model_path,
            backend=backend,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            device=device
        )
    return _llm_instance

