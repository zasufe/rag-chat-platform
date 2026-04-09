#!/usr/bin/env python3
"""
RAG Chat Platform 后端入口文件

用于 PyCharm 远程调试和项目启动

使用方法:
    1. PyCharm 远程调试:
       - 配置远程解释器指向此文件
       - 添加参数：--host 0.0.0.0 --port 8000
    
    2. 命令行启动:
       python main.py --host 0.0.0.0 --port 8000
    
    3. 开发模式 (自动重载):
       python main.py --reload
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from app.main import app


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RAG Chat Platform Backend')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--reload', action='store_true', help='开发模式 (自动重载)')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')
    
    args = parser.parse_args()
    
    # 导入 uvicorn
    import uvicorn
    
    print(f"🚀 启动 RAG Chat Platform v2.0.0")
    print(f"📍 地址：http://{args.host}:{args.port}")
    print(f"📚 API 文档：http://{args.host}:{args.port}/docs")
    print(f"💚 健康检查：http://{args.host}:{args.port}/health")
    print("")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    main()