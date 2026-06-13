#!/bin/bash
# 台北市气象平台 启动脚本
cd "$(dirname "$0")"
echo "==============================="
echo "  台北市气象平台"
echo "  数据源: Open-Meteo (模拟回退)"
echo "==============================="
echo ""
echo "依赖安装中..."
pip install flask requests -q 2>/dev/null
echo ""
echo "启动服务: http://localhost:5050"
echo "按 Ctrl+C 停止"
echo ""
python app.py
