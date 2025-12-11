# TinyMem0 - 完成重构说明

## ✅ 重构完成总结

项目已从**命令行参数**完全迁移到 **`.env` 配置文件**管理。

## 当前配置状态

### 默认配置（.env）

```bash
USE_LOCAL_LLM=true                    # 使用本地模型（默认）
MODEL_SHORTCUT=mistral-7b              # Mistral-7B模型
MODEL_FORMAT=gguf                      # GGUF格式（CPU友好）
MODEL_QUANTIZATION=Q4_K_M              # 4-bit量化（4GB）
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5  # 中文嵌入模型
EMBEDDING_DIM=512                      # 向量维度
SKIP_DOWNLOAD=false                    # 自动下载（首次运行）
```

### 已下载的模型

```
📂 models/
├── embeddings/ (93MB)
│   └── models--BAAI--bge-small-zh-v1.5/
└── gguf/ (4.1GB)
    └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

## 运行方式

### 简单运行（使用默认配置）

```bash
python examples/complete_demo.py
```

就这么简单！无需任何命令行参数。

### 修改配置

编辑 `.env` 文件，然后直接运行：

```bash
# 编辑配置
vim .env

# 运行
python examples/complete_demo.py
```

## 测试结果

✅ **首次运行测试**（2025-12-12）
- ✅ 嵌入模型自动下载：BAAI/bge-small-zh-v1.5 (93MB)
- ✅ LLM模型自动下载：Mistral-7B Q4_K_M (4.1GB)
- ✅ 模型加载成功
- ✅ 记忆系统正常运行
- ✅ 事实提取正常：提取了4个事实
- ✅ 记忆搜索正常：返回相关结果
- ✅ 记忆更新正常：自动更新职业信息
- ✅ `.env` 自动更新：`LOCAL_MODEL_PATH` 已填充

## 配置说明

### 本地模式 vs 云端模式

**本地模式**（当前默认）：
```bash
USE_LOCAL_LLM=true
# 首次运行会自动下载模型
```

**云端模式**（需要API密钥）：
```bash
USE_LOCAL_LLM=false
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx  # 需要配置
```

### 模型选择

支持的模型（MODEL_SHORTCUT）：
- `qwen2.5-7b` - 通义千问2.5 7B
- `qwen2.5-3b` - 通义千问2.5 3B（更快）
- `qwen2.5-1.5b` - 通义千问2.5 1.5B（最快）
- `mistral-7b` - Mistral 7B（默认，英文更好）
- `llama3-8b` - Llama 3 8B
- `yi-6b` - Yi 6B

### 模型格式

**GGUF**（推荐，CPU友好）：
```bash
MODEL_FORMAT=gguf
MODEL_QUANTIZATION=Q4_K_M  # 4-bit量化，~4GB
```

量化选项：
- `Q3_K_M` - 3-bit，~3GB（最小）
- `Q4_K_M` - 4-bit，~4GB（推荐）
- `Q5_K_M` - 5-bit，~5GB（平衡）
- `Q8_0` - 8-bit，~8GB（高质量）

**SafeTensors**（需要GPU）：
```bash
MODEL_FORMAT=safetensors  # ~14-26GB
```

## 项目架构

### 配置管理

```
.env                     → 唯一配置源
├── USE_LOCAL_LLM       → 模式选择
├── MODEL_SHORTCUT      → 模型选择
├── MODEL_FORMAT        → 格式选择
├── MODEL_QUANTIZATION  → 量化精度
└── LOCAL_MODEL_PATH    → 自动填充
```

### 模型下载

```
utils/model_manager/downloader.py  → 统一下载入口
├── download_embedding_model()     → 嵌入模型
└── download_llm_model()           → LLM模型
    ├── _download_gguf_model()     → GGUF格式
    └── _download_safetensors_model() → SafeTensors格式
```

### 固定路径

```
./models/
├── embeddings/          → 嵌入模型（固定）
├── gguf/                → GGUF模型（固定）
└── safetensors/         → SafeTensors模型（固定）
```

## 下一步

### 再次运行（无需下载）

模型已下载，直接运行即可：

```bash
python examples/complete_demo.py
```

### 跳过下载

如果想确保不下载（使用现有模型）：

```bash
# 编辑 .env
SKIP_DOWNLOAD=true

# 运行
python examples/complete_demo.py
```

### 切换模型

编辑 `.env`：

```bash
MODEL_SHORTCUT=qwen2.5-7b  # 改为千问模型
SKIP_DOWNLOAD=false        # 允许下载新模型
```

然后运行：

```bash
python examples/complete_demo.py
```

## 常见问题

**Q: 如何查看当前配置？**

A: 运行程序时会显示所有配置信息。

**Q: 模型下载到哪里？**

A: 固定路径 `./models/`，不可配置。

**Q: 如何使用云端API？**

A: 在 `.env` 中设置：
```bash
USE_LOCAL_LLM=false
DASHSCOPE_API_KEY=your_key_here
```

**Q: 下载太慢怎么办？**

A: 已配置国内镜像 `HF_ENDPOINT=https://hf-mirror.com`。

**Q: 如何清理模型？**

A: 直接删除 `./models/` 目录即可。

## 文档

- **配置指南**: `CONFIG_GUIDE.md` - 详细配置说明
- **项目架构**: `docs/PROJECT_ARCHITECTURE.md` - 架构文档
- **环境配置**: `.env.example` - 配置模板

## 验证通过

- [x] 嵌入模型自动下载
- [x] LLM模型自动下载
- [x] 模型加载成功
- [x] 记忆系统运行
- [x] 配置自动更新
- [x] 无命令行参数依赖
- [x] 完全通过 `.env` 管理

---

**重构完成日期**: 2025-12-12
**测试状态**: ✅ 通过
**默认模式**: 本地模型（USE_LOCAL_LLM=true）
