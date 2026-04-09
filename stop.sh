#!/bin/bash

# RAG Chat Platform 停止脚本

echo "🛑 停止服务..."

# 停止后端
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✅ 后端已停止" || echo "后端未运行"

# 停止前端
pkill -f "vite" 2>/dev/null && echo "✅ 前端已停止" || echo "前端未运行"

echo "完成"