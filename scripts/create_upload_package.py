#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建CloudBase云托管直接上传代码包
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_upload_package():
    """创建可直接上传的代码包"""
    print("📦 创建CloudBase云托管上传代码包...")
    
    # 创建上传目录
    upload_dir = Path("cloudbase_upload_package")
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir()
    
    # 复制Streamlit应用
    streamlit_dir = upload_dir / "streamlit_app"
    shutil.copytree("streamlit_app", streamlit_dir)
    
    # 创建优化的Dockerfile
    dockerfile_content = """FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

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

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
"""
    
    with open(upload_dir / "Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    # 创建.dockerignore文件
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
    
    with open(upload_dir / ".dockerignore", "w", encoding="utf-8") as f:
        f.write(dockerignore_content)
    
    # 创建压缩包
    zip_path = "life-diamond-system-upload.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, upload_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 上传代码包创建完成: {zip_path}")
    print(f"📁 代码目录: {upload_dir}")
    print("\n📋 包含文件:")
    print("   - streamlit_app/ (完整应用代码)")
    print("   - Dockerfile (容器配置)")
    print("   - .dockerignore (忽略文件)")
    
    return zip_path, upload_dir

def create_upload_guide():
    """创建上传指南"""
    guide = """
# CloudBase云托管直接上传部署指南

## 部署步骤

### 1. 准备代码包
已为您创建了代码包：`life-diamond-system-upload.zip`

### 2. 在CloudBase控制台上传

1. **选择部署方式**：通过本地代码部署
2. **代码包类型**：选择"压缩包"
3. **上传代码包**：点击"上传"按钮，选择 `life-diamond-system-upload.zip`
4. **服务配置**：
   - 服务名称：`life-diamond-system`
   - 部署类型：容器型服务
5. **容器配置**：
   - 端口：`8080`
   - 目标目录：留空（根目录）
   - Dockerfile名称：`Dockerfile`
6. **环境变量**：
   - `CLOUDBASE_ENV_ID` = `cloud1-7g7o4xi13c00cb90`
   - `CLOUDBASE_REGION` = `ap-shanghai`
   - `PYTHONUNBUFFERED` = `1`
   - `STREAMLIT_SERVER_HEADLESS` = `true`
7. **ENTRYPOINT**：留空（使用Dockerfile中的CMD）
8. **CMD**：留空（使用Dockerfile中的CMD）

### 3. 部署
点击"部署"按钮开始部署

### 4. 等待部署完成
- 构建时间：约5-10分钟
- 部署完成后会显示访问地址

## 注意事项

1. **健康检查**：应用健康检查路径为 `/_stcore/health`
2. **端口**：确保使用8080端口
3. **环境变量**：必须设置CloudBase相关环境变量
4. **构建日志**：可在控制台查看构建和部署日志

## 访问应用

部署完成后，在CloudBase控制台的"云托管"服务中查看访问地址。
"""
    
    with open("upload_deploy_guide.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("📖 上传部署指南已创建: upload_deploy_guide.md")

def main():
    """主函数"""
    print("🔷 创建CloudBase云托管上传代码包")
    print("=" * 50)
    
    # 创建代码包
    zip_path, upload_dir = create_upload_package()
    
    # 创建指南
    create_upload_guide()
    
    print("\n🎉 代码包准备完成！")
    print(f"📦 上传文件: {zip_path}")
    print("📖 部署指南: upload_deploy_guide.md")
    print("\n💡 现在您可以：")
    print("1. 在CloudBase控制台选择'通过本地代码部署'")
    print("2. 选择'压缩包'类型")
    print("3. 上传 life-diamond-system-upload.zip")
    print("4. 按照指南配置参数并部署")

if __name__ == "__main__":
    main()



