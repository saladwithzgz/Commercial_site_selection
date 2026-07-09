"""
后端启动脚本
启动Flask API服务
"""
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.api_server import app, run_server


if __name__ == '__main__':
    print("=" * 60)
    print("🍵 奶茶店智能选址分析系统 - 后端服务")
    print("=" * 60)
    print()
    print("📌 启动信息:")
    print(f"   - 服务地址: http://localhost:5000")
    print(f"   - 前端页面: http://localhost:5000/")
    print(f"   - API文档: http://localhost:5000/api/health")
    print()
    print("🚀 启动中...")
    print()
    
    run_server(host='0.0.0.0', port=5000, debug=True)
