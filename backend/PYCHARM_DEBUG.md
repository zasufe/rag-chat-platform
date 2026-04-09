# PyCharm 远程调试配置指南

## 1. 项目结构

```
backend/
├── main.py              # ← 新增：入口文件
├── app/
│   ├── main.py          # FastAPI 应用
│   ├── core/
│   ├── routers/
│   └── services/
├── .vscode/
│   └── launch.json      # VSCode 调试配置
└── .env                 # 环境配置
```

## 2. PyCharm 配置步骤

### 2.1 打开项目

```
File → Open → 选择 backend 目录
```

### 2.2 配置 Python 解释器

```
File → Settings → Project → Python Interpreter
→ 添加远程解释器 (SSH/Docker/WSL)
```

### 2.3 配置运行/调试

```
Run → Edit Configurations → + → Python

配置 1: 使用入口文件
- Script path: /path/to/backend/main.py
- Parameters: --host 0.0.0.0 --port 8000
- Working directory: /path/to/backend

配置 2: 使用 uvicorn 模块
- Module name: uvicorn
- Parameters: app.main:app --host 0.0.0.0 --port 8000 --reload
- Working directory: /path/to/backend
```

### 2.4 远程调试配置

```
Run → Edit Configurations → + → Python Remote Debug

- Host: localhost
- Port: 5678
- Path mappings:
  /remote/path/backend → /local/path/backend
```

## 3. 启动方式

### 3.1 使用入口文件（推荐）

```bash
cd backend
python main.py --host 0.0.0.0 --port 8000
```

### 3.2 使用 uvicorn 模块

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 PyCharm 运行

```
右键 main.py → Run 'main'
或
Shift+F10 → 选择配置 → Run
```

## 4. 调试配置

### 4.1 断点调试

1. 在代码中设置断点（点击行号左侧）
2. Run → Debug 'main'
3. 访问 API 触发断点

### 4.2 远程调试

```python
# 在代码中添加远程调试
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
```

## 5. 环境变量

创建 `.env` 文件：

```bash
# LLM 配置
LLM_API_KEY=sk-xxx
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.5-flash

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 6. 常见问题

### Q1: 找不到模块
```
解决方案：确保 PYTHONPATH 包含 backend 目录
```

### Q2: 导入错误
```
解决方案：右键 app 目录 → Mark Directory as → Sources Root
```

### Q3: 远程调试连接失败
```
解决方案：
1. 检查防火墙
2. 确认端口 5678 开放
3. 检查路径映射配置
```

## 7. 推荐插件

- PyCharm Professional (支持远程调试)
- Python Remote Debug
- Docker (如果使用 Docker)

---

**创建日期**: 2026-04-10  
**版本**: v1.0