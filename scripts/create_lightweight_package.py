#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建轻量级CloudBase部署包
解决构建超时问题
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_lightweight_dockerfile():
    """创建轻量级Dockerfile"""
    dockerfile_content = """FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false

# 只安装必要的系统依赖，避免编译工具
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# 配置pip使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \\
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件
COPY streamlit_app/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY streamlit_app/ ./streamlit_app/

# 创建Streamlit配置目录
RUN mkdir -p /root/.streamlit

# 复制Streamlit配置文件
COPY .streamlit/config.toml /root/.streamlit/config.toml

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /root/.streamlit
USER appuser

# 暴露端口
EXPOSE 8080

# 简化的健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=2 \\
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
"""
    
    return dockerfile_content

def create_minimal_requirements():
    """创建最小化依赖文件"""
    requirements_content = """streamlit>=1.28.0
requests>=2.31.0
pandas>=2.0.0
plotly>=5.15.0
Pillow>=10.0.0
streamlit-option-menu>=0.3.6
streamlit-extras>=0.3.0
jsonschema>=4.17.0
python-dateutil>=2.8.2
"""
    
    return requirements_content

def create_streamlit_config():
    """创建Streamlit配置"""
    config_content = """[server]
headless = true
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
maxUploadSize = 200

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"
serverPort = 8080

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
"""
    
    return config_content

def create_lightweight_package():
    """创建轻量级部署包"""
    print("🚀 创建轻量级CloudBase部署包...")
    
    # 创建部署目录
    deploy_dir = Path("cloudbase_lightweight")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # 复制Streamlit应用（排除不必要的文件）
    streamlit_dir = deploy_dir / "streamlit_app"
    shutil.copytree("streamlit_app", streamlit_dir)
    
    # 删除不必要的文件
    for pattern in ["__pycache__", "*.pyc", "*.pyo"]:
        for file_path in streamlit_dir.rglob(pattern):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
    
    # 创建最小化requirements.txt
    requirements_content = create_minimal_requirements()
    with open(streamlit_dir / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    # 创建.streamlit配置目录
    streamlit_config_dir = deploy_dir / ".streamlit"
    streamlit_config_dir.mkdir()
    
    # 创建Streamlit配置文件
    config_content = create_streamlit_config()
    with open(streamlit_config_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # 创建轻量级Dockerfile
    dockerfile_content = create_lightweight_dockerfile()
    with open(deploy_dir / "Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    # 创建.dockerignore
    dockerignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/
.DS_Store
.vscode/
.idea/
*.swp
*.swo
*~
*.zip
*.tar.gz
"""
    
    with open(deploy_dir / ".dockerignore", "w", encoding="utf-8") as f:
        f.write(dockerignore_content)
    
    # 创建启动脚本
    start_script = """#!/bin/bash
# 轻量级启动脚本

# 设置环境变量
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=8080
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false

# 启动应用
exec streamlit run streamlit_app/main.py \\
    --server.port 8080 \\
    --server.address 0.0.0.0 \\
    --server.headless true
"""
    
    with open(deploy_dir / "start.sh", "w", encoding="utf-8") as f:
        f.write(start_script)
    
    # 创建压缩包
    zip_path = "life-diamond-system-lightweight.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 轻量级部署包创建完成: {zip_path}")
    print(f"📁 部署目录: {deploy_dir}")
    
    return zip_path, deploy_dir

def create_deployment_guide():
    """创建部署指南"""
    guide = """
# CloudBase轻量级部署指南

## 构建失败原因分析

### 1. 系统依赖安装超时
- 原Dockerfile安装了gcc、g++等编译工具
- 这些工具包很大，在云托管环境中构建超时
- 网络连接不稳定导致包下载失败

### 2. 构建配置过于复杂
- 构建层数过多
- 不必要的系统依赖
- 网络配置问题

## 轻量级解决方案

### 1. 优化Dockerfile
- ✅ 移除了gcc、g++等编译工具
- ✅ 只保留必要的curl用于健康检查
- ✅ 简化了构建步骤
- ✅ 优化了网络配置

### 2. 最小化依赖
- ✅ 使用最小化的requirements.txt
- ✅ 移除了不必要的Python包
- ✅ 优化了包安装顺序

### 3. 构建优化
- ✅ 减少了构建层数
- ✅ 优化了缓存策略
- ✅ 简化了健康检查

## 部署步骤

### 1. 上传轻量级包
- 文件：`life-diamond-system-lightweight.zip`
- 类型：压缩包
- 服务名：`life-diamond-system`

### 2. 配置参数
- 端口：8080
- 目标目录：留空
- Dockerfile名称：Dockerfile

### 3. 环境变量
```
CLOUDBASE_ENV_ID=cloud1-7g7o4xi13c00cb90
CLOUDBASE_REGION=ap-shanghai
PYTHONUNBUFFERED=1
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
```

## 预期效果

- ✅ 构建时间大幅缩短（5-10分钟）
- ✅ 构建成功率提高
- ✅ 应用启动更快
- ✅ 资源占用更少
"""
    
    with open("lightweight_deploy_guide.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("📖 轻量级部署指南已创建: lightweight_deploy_guide.md")

def main():
    """主函数"""
    print("🔷 CloudBase轻量级部署包创建工具")
    print("=" * 50)
    
    # 创建轻量级包
    zip_path, deploy_dir = create_lightweight_package()
    
    # 创建部署指南
    create_deployment_guide()
    
    print("\n🎉 轻量级部署包准备完成！")
    print(f"📦 部署包: {zip_path}")
    print("📖 部署指南: lightweight_deploy_guide.md")
    print("\n💡 主要优化：")
    print("✅ 移除了gcc、g++等编译工具")
    print("✅ 简化了构建步骤")
    print("✅ 优化了网络配置")
    print("✅ 减少了构建时间")
    print("\n🚀 现在可以重新部署了！")

if __name__ == "__main__":
    main()



