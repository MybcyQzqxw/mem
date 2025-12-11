# TinyMem0 配置指南

## 概述

TinyMem0 现在**完全通过 `.env` 文件进行配置**，无需命令行参数。

## 快速开始

### 1. 配置 `.env` 文件

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env  # 或使用其他编辑器
```

### 2. 配置选项

#### 基础配置

```bash
# 是否使用本地LLM（true=本地, false=云端API）
USE_LOCAL_LLM=false

# 阿里云API密钥（云端模式必须）
DASHSCOPE_API_KEY=your_api_key_here
```

#### 本地模型配置（仅当 USE_LOCAL_LLM=true）

```bash
# 模型选择
MODEL_SHORTCUT=mistral-7b
# 可选: qwen2.5-7b, qwen2.5-3b, qwen2.5-1.5b, mistral-7b, llama3-8b, yi-6b

# 模型格式
MODEL_FORMAT=gguf
# gguf: CPU友好，4-8GB
# safetensors: 需要GPU，14-26GB

# 量化精度（仅GGUF格式）
MODEL_QUANTIZATION=Q4_K_M
# Q3_K_M: 最小 (~3GB)
# Q4_K_M: 推荐 (~4GB)
# Q5_K_M: 平衡 (~5GB)
# Q8_0: 高质量 (~8GB)

# 模型路径（自动下载后填充）
LOCAL_MODEL_PATH=
```

#### 嵌入模型配置

```bash
# 嵌入模型
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# 向量维度（留空自动设置）
EMBEDDING_DIM=

# 跳过模型下载
SKIP_DOWNLOAD=false
```

### 3. 运行示例

```bash
# 直接运行，所有配置来自 .env
python examples/complete_demo.py
```

## 配置示例

### 示例1：使用云端API（默认）

```bash
# .env
USE_LOCAL_LLM=false
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx
```

### 示例2：使用本地模型（自动下载）

```bash
# .env
USE_LOCAL_LLM=true
MODEL_SHORTCUT=mistral-7b
MODEL_FORMAT=gguf
MODEL_QUANTIZATION=Q4_K_M
SKIP_DOWNLOAD=false
```

### 示例3：使用已下载的模型

```bash
# .env
USE_LOCAL_LLM=true
LOCAL_MODEL_PATH=models/gguf/mistral-7b-instruct-v0.2.Q4_K_M.gguf
SKIP_DOWNLOAD=true
```

## 模型下载路径（固定）

所有模型下载到项目根目录下的固定位置：

```
./models/
├── embeddings/          # 嵌入模型
│   └── BAAI/bge-small-zh-v1.5/
├── gguf/                # GGUF格式LLM
│   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
└── safetensors/         # SafeTensors格式LLM
    └── Mistral-7B-Instruct-v0.2/
```

## 常见问题

### Q: 如何切换模型？

A: 修改 `.env` 中的 `MODEL_SHORTCUT`，然后运行程序会自动下载。

### Q: 如何使用已下载的模型？

A: 设置 `SKIP_DOWNLOAD=true` 并填写 `LOCAL_MODEL_PATH`。

### Q: 模型下载失败怎么办？

A: 检查网络连接，确保 `HF_ENDPOINT=https://hf-mirror.com` 已配置。

### Q: 如何查看当前配置？

A: 运行程序时会显示所有配置信息。

## 架构说明

- **配置管理**: `.env` 文件（唯一配置源）
- **模型下载**: `utils/model_manager/downloader.py`（统一入口）
- **模型路径**: 固定位置（不可配置）
- **示例程序**: `examples/complete_demo.py`（无命令行参数）

## 迁移指南

如果之前使用命令行参数，请按以下映射配置 `.env`：

| 旧命令行参数 | 新.env配置 |
|------------|-----------|
| `--use-local` | `USE_LOCAL_LLM=true` |
| `--use-cloud` | `USE_LOCAL_LLM=false` |
| `--model mistral-7b` | `MODEL_SHORTCUT=mistral-7b` |
| `--format gguf` | `MODEL_FORMAT=gguf` |
| `--quant Q4_K_M` | `MODEL_QUANTIZATION=Q4_K_M` |
| `--embedding-model xxx` | `LOCAL_EMBEDDING_MODEL=xxx` |
| `--embedding-dim 512` | `EMBEDDING_DIM=512` |
| `--skip-download` | `SKIP_DOWNLOAD=true` |
