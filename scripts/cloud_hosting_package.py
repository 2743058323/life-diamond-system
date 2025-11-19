#!/usr/bin/env python3
"""
创建云托管部署包
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_cloud_hosting_package():
    """创建云托管部署包"""
    print("🔷 开始创建云托管部署包...")
    
    # 创建部署目录
    deploy_dir = Path("cloud_hosting_deploy")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # 复制 Streamlit 应用文件
    streamlit_dir = deploy_dir / "streamlit_app"
    shutil.copytree("streamlit_app", streamlit_dir)
    
    # 创建启动脚本
    start_script = """#!/bin/bash
# 云托管启动脚本

# 安装依赖
pip install -r requirements.txt

# 启动 Streamlit 应用
streamlit run streamlit_app/main.py --server.port 8080 --server.address 0.0.0.0 --server.headless true
"""
    
    with open(deploy_dir / "start.sh", "w", encoding="utf-8") as f:
        f.write(start_script)
    
    # 创建 Dockerfile
    dockerfile_content = """FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 配置 pip 使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件
COPY streamlit_app/requirements_simple.txt requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY streamlit_app/ ./streamlit_app/

# 暴露端口
EXPOSE 8080

# 直接启动 Streamlit 应用
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
"""
    
    with open(deploy_dir / "Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    # 创建云托管配置文件
    hosting_config = """{
  "version": "2.0",
  "name": "life-diamond-system",
  "description": "生命钻石售后系统",
  "runtime": "python3.9",
  "entrypoint": "streamlit run streamlit_app/main.py --server.port 8080 --server.address 0.0.0.0 --server.headless true",
  "env": {
    "CLOUDBASE_ENV_ID": "cloud1-7g7o4xi13c00cb90",
    "CLOUDBASE_REGION": "ap-shanghai"
  },
  "resources": {
    "cpu": "0.5",
    "memory": "1Gi"
  },
  "scaling": {
    "minInstances": 1,
    "maxInstances": 10
  }
}
"""
    
    with open(deploy_dir / "cloudbase.json", "w", encoding="utf-8") as f:
        f.write(hosting_config)
    
    # 创建压缩包
    zip_path = "life-diamond-cloud-hosting.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print("✅ 云托管部署包创建完成！")
    print(f"📁 部署目录: {deploy_dir.absolute()}")
    print(f"📦 压缩包: {zip_path}")
    print("📄 包含文件:")
    print("   - streamlit_app/ (完整应用代码)")
    print("   - start.sh (启动脚本)")
    print("   - Dockerfile (容器配置)")
    print("   - cloudbase.json (云托管配置)")
    print("   - requirements.txt (Python依赖)")
    
    return deploy_dir, zip_path

if __name__ == "__main__":
    create_cloud_hosting_package()
