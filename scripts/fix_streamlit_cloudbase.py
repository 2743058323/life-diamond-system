#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复Streamlit在CloudBase云托管中的WebSocket连接问题
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_streamlit_config():
    """创建Streamlit配置文件"""
    config_content = """[server]
# 云托管环境配置
headless = true
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false

[browser]
# 禁用自动打开浏览器
gatherUsageStats = false
serverAddress = "0.0.0.0"
serverPort = 8080

[theme]
# 主题配置
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
"""
    
    return config_content

def create_fixed_dockerfile():
    """创建修复后的Dockerfile"""
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

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

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

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# 启动命令 - 使用配置文件
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
"""
    
    return dockerfile_content

def create_fixed_package():
    """创建修复后的部署包"""
    print("🔧 创建修复WebSocket问题的部署包...")
    
    # 创建修复目录
    fix_dir = Path("cloudbase_fixed_package")
    if fix_dir.exists():
        shutil.rmtree(fix_dir)
    fix_dir.mkdir()
    
    # 复制Streamlit应用
    streamlit_dir = fix_dir / "streamlit_app"
    shutil.copytree("streamlit_app", streamlit_dir)
    
    # 创建.streamlit配置目录
    streamlit_config_dir = fix_dir / ".streamlit"
    streamlit_config_dir.mkdir()
    
    # 创建Streamlit配置文件
    config_content = create_streamlit_config()
    with open(streamlit_config_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # 创建修复后的Dockerfile
    dockerfile_content = create_fixed_dockerfile()
    with open(fix_dir / "Dockerfile", "w", encoding="utf-8") as f:
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
"""
    
    with open(fix_dir / ".dockerignore", "w", encoding="utf-8") as f:
        f.write(dockerignore_content)
    
    # 创建启动脚本
    start_script = """#!/bin/bash
# 云托管启动脚本 - 修复WebSocket问题

# 设置环境变量
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=8080
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false

# 启动Streamlit应用
streamlit run streamlit_app/main.py \\
    --server.port 8080 \\
    --server.address 0.0.0.0 \\
    --server.headless true \\
    --server.enableCORS false \\
    --server.enableXsrfProtection false \\
    --server.enableWebsocketCompression false
"""
    
    with open(fix_dir / "start.sh", "w", encoding="utf-8") as f:
        f.write(start_script)
    
    # 创建压缩包
    zip_path = "life-diamond-system-fixed.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(fix_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, fix_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 修复包创建完成: {zip_path}")
    print(f"📁 修复目录: {fix_dir}")
    
    return zip_path, fix_dir

def create_fix_guide():
    """创建修复指南"""
    guide = """
# Streamlit CloudBase WebSocket 错误修复指南

## 问题分析

您遇到的WebSocket连接错误是Streamlit在云托管环境中的常见问题，主要原因：

1. **CORS配置问题** - 云托管的代理服务器阻止了WebSocket连接
2. **XSRF保护冲突** - 云托管的安全策略与Streamlit的XSRF保护冲突
3. **WebSocket压缩问题** - 云托管的网络代理不支持WebSocket压缩
4. **服务器配置不匹配** - Streamlit的默认配置不适合云托管环境

## 修复方案

### 1. 使用修复后的代码包

已为您创建了修复包：`life-diamond-system-fixed.zip`

### 2. 主要修复内容

- ✅ 添加了 `.streamlit/config.toml` 配置文件
- ✅ 禁用了CORS检查
- ✅ 禁用了XSRF保护
- ✅ 禁用了WebSocket压缩
- ✅ 优化了环境变量配置
- ✅ 添加了启动脚本

### 3. 重新部署步骤

1. **删除现有服务**（在CloudBase控制台）
2. **上传修复包**：选择 `life-diamond-system-fixed.zip`
3. **配置参数**：
   - 服务名称：`life-diamond-system`
   - 端口：`8080`
   - 目标目录：留空
   - Dockerfile名称：`Dockerfile`
4. **环境变量**：
   - `CLOUDBASE_ENV_ID` = `cloud1-7g7o4xi13c00cb90`
   - `CLOUDBASE_REGION` = `ap-shanghai`
   - `PYTHONUNBUFFERED` = `1`
   - `STREAMLIT_SERVER_HEADLESS` = `true`
   - `STREAMLIT_SERVER_ENABLE_CORS` = `false`
   - `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION` = `false`
   - `STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION` = `false`

### 4. 验证修复

部署完成后，检查：
- ✅ 页面正常加载
- ✅ 无WebSocket连接错误
- ✅ 交互功能正常
- ✅ 控制台无错误信息

## 技术说明

### Streamlit配置优化

```toml
[server]
headless = true
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
```

### 环境变量优化

```bash
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false
```

这些配置专门针对云托管环境进行了优化，解决了WebSocket连接问题。
"""
    
    with open("websocket_fix_guide.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("📖 WebSocket修复指南已创建: websocket_fix_guide.md")

def main():
    """主函数"""
    print("🔧 Streamlit CloudBase WebSocket 错误修复工具")
    print("=" * 60)
    
    # 创建修复包
    zip_path, fix_dir = create_fixed_package()
    
    # 创建修复指南
    create_fix_guide()
    
    print("\n🎉 修复包准备完成！")
    print(f"📦 修复包: {zip_path}")
    print("📖 修复指南: websocket_fix_guide.md")
    print("\n💡 下一步操作：")
    print("1. 在CloudBase控制台删除现有服务")
    print("2. 重新部署，上传 life-diamond-system-fixed.zip")
    print("3. 按照修复指南配置环境变量")
    print("4. 验证WebSocket错误是否解决")

if __name__ == "__main__":
    main()



