#!/bin/bash

# RAG Chat Platform 智能启动脚本
# 自动检测空闲端口，避免端口冲突

set -e

cd "$(dirname "$0")"

echo "🚀 RAG Chat Platform 启动脚本"
echo "=============================="

# 检测空闲端口
find_available_port() {
    local port=$1
    if ! netstat -ntlp 2>/dev/null | grep -q ":${port} "; then
        echo $port
        return 0
    fi
    return 1
}

# 后端端口检测
BACKEND_PORT=8000
if ! find_available_port $BACKEND_PORT > /dev/null; then
    echo "⚠️  端口 $BACKEND_PORT 被占用，尝试其他端口..."
    for p in 8001 8002 8003 8004 8005; do
        if find_available_port $p > /dev/null; then
            BACKEND_PORT=$p
            echo "✅ 使用后端端口：$BACKEND_PORT"
            break
        fi
    done
fi

# 前端端口检测
FRONTEND_PORT=3000
if ! find_available_port $FRONTEND_PORT > /dev/null; then
    echo "⚠️  端口 $FRONTEND_PORT 被占用，尝试其他端口..."
    for p in 3001 3002 3003 3004 3005; do
        if find_available_port $p > /dev/null; then
            FRONTEND_PORT=$p
            echo "✅ 使用前端端口：$FRONTEND_PORT"
            break
        fi
    done
fi

# 停止旧服务
echo ""
echo "🛑 停止旧服务..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# 启动后端
echo ""
echo "📦 启动后端服务 (端口：$BACKEND_PORT)..."
cd backend

# 更新配置
sed -i "s/PORT=.*/PORT=$BACKEND_PORT/" .env 2>/dev/null || true

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

cd ..
sleep 3

# 检查后端状态
if curl -s http://127.0.0.1:$BACKEND_PORT/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    cat logs/backend.log
    exit 1
fi

# 启动前端
echo ""
echo "🎨 启动前端服务 (端口：$FRONTEND_PORT)..."
cd frontend

# 更新配置
sed -i "s/port: .*/port: $FRONTEND_PORT/" vite.config.ts 2>/dev/null || true

nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"

cd ..
sleep 5

# 获取实际端口 (可能被占用后自动切换)
ACTUAL_FRONTEND_PORT=$(grep "Network:" logs/frontend.log 2>/dev/null | grep "172.16.25.187" | head -1 | sed 's/.*:300/300/' | sed 's/[^0-9].*//')
if [ -z "$ACTUAL_FRONTEND_PORT" ]; then
    ACTUAL_FRONTEND_PORT=$FRONTEND_PORT
fi

echo ""
echo "=============================="
echo "✅ 服务启动成功!"
echo ""
echo "📌 访问地址:"
echo "   前端界面：http://172.16.25.187:$ACTUAL_FRONTEND_PORT"
echo "   API 文档：http://172.16.25.187:$BACKEND_PORT/docs"
echo "   健康检查：http://172.16.25.187:$BACKEND_PORT/health"
echo ""
echo "📋 常用命令:"
echo "   查看后端日志：tail -f logs/backend.log"
echo "   查看前端日志：tail -f logs/frontend.log"
echo "   停止服务：./stop.sh"
echo ""
echo "🔍 端口占用检查:"
echo "   netstat -ntlp | grep ':$BACKEND_PORT\|:$ACTUAL_FRONTEND_PORT'"