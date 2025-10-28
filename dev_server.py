#!/usr/bin/env python3
"""
本地开发服务器
支持热重载，修改代码后自动刷新
"""

import subprocess
import sys
import os
from pathlib import Path

def start_dev_server():
    """启动本地开发服务器"""
    print("🔷 启动生命钻石服务系统开发服务器...")
    
    # 切换到 streamlit_app 目录
    app_dir = Path("streamlit_app")
    if not app_dir.exists():
        print("❌ 找不到 streamlit_app 目录")
        return
    
    # 启动 Streamlit 开发服务器
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "main.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",  # 监听所有网络接口，允许手机访问
        "--server.runOnSave", "true",  # 保存时自动重载
        "--server.fileWatcherType", "auto",  # 自动文件监控
        "--browser.gatherUsageStats", "false"  # 禁用使用统计
    ]
    
    try:
        print("🚀 启动开发服务器...")
        print("📱 电脑访问: http://localhost:8501")
        print("📱 手机访问: http://192.168.10.153:8501")
        print("💡 修改代码后会自动重载页面")
        print("⚠️  首次访问可能需要配置Windows防火墙允许Python")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        subprocess.run(cmd, cwd=app_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 开发服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    start_dev_server()
