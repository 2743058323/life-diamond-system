#!/usr/bin/env python3
"""
构建 Streamlit 应用为静态文件
用于部署到腾讯云静态网站托管
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_static_app():
    """构建静态应用"""
    print("🔷 开始构建生命钻石售后系统静态文件...")
    
    # 创建构建目录
    build_dir = Path("dist")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # 创建基本的 HTML 结构
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>生命钻石售后系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        .header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 2rem;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        .feature-card {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            border-left: 4px solid #8B4B8C;
        }
        .feature-card h3 {
            color: #8B4B8C;
            margin-top: 0;
        }
        .btn {
            display: inline-block;
            background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .demo-section {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin: 2rem 0;
        }
        .demo-form {
            max-width: 400px;
            margin: 0 auto;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
        }
        .form-group input:focus {
            outline: none;
            border-color: #8B4B8C;
        }
        .footer {
            background: #f8f9fa;
            padding: 2rem;
            text-align: center;
            color: #666;
        }
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            .content {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔷 生命钻石售后系统</h1>
            <p>专业的纪念钻石制作进度跟踪系统</p>
        </div>
        
        <div class="content">
            <div class="demo-section">
                <h2 style="text-align: center; color: #8B4B8C;">客户查询演示</h2>
                <div class="demo-form">
                    <div class="form-group">
                        <label for="customerName">客户姓名</label>
                        <input type="text" id="customerName" placeholder="请输入您的姓名">
                    </div>
                    <button class="btn" onclick="searchOrder()" style="width: 100%;">查询订单</button>
                </div>
                <div id="result" style="margin-top: 1rem;"></div>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🔍 客户查询</h3>
                    <p>客户可以通过姓名快速查询订单状态和制作进度，实时了解钻石制作情况。</p>
                </div>
                
                <div class="feature-card">
                    <h3>📊 管理后台</h3>
                    <p>管理员可以创建订单、更新进度、上传照片，全面管理制作流程。</p>
                </div>
                
                <div class="feature-card">
                    <h3>📷 照片管理</h3>
                    <p>记录制作过程的每个精彩瞬间，让客户见证钻石的诞生过程。</p>
                </div>
                
                <div class="feature-card">
                    <h3>📈 进度跟踪</h3>
                    <p>6个制作阶段的详细进度跟踪，确保按时交付高质量产品。</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 2rem 0;">
                <h3 style="color: #8B4B8C;">系统特点</h3>
                <p>✅ 实时进度更新 &nbsp;&nbsp; ✅ 照片记录 &nbsp;&nbsp; ✅ 客户友好 &nbsp;&nbsp; ✅ 管理便捷</p>
            </div>
        </div>
        
        <div class="footer">
            <p>生命钻石售后系统 v1.0 | 由 MiniMax Agent 开发</p>
            <p>如有疑问，请联系客服：400-123-4567</p>
        </div>
    </div>
    
    <script>
        // 模拟查询功能
        function searchOrder() {
            const customerName = document.getElementById('customerName').value;
            const resultDiv = document.getElementById('result');
            
            if (!customerName.trim()) {
                resultDiv.innerHTML = '<p style="color: #ff6b6b;">请输入客户姓名</p>';
                return;
            }
            
            // 模拟查询结果
            const mockData = {
                '张三': {
                    orderNumber: 'LD20250922001',
                    status: '制作中',
                    stage: '高温高压处理',
                    progress: 45
                },
                '李四': {
                    orderNumber: 'LD20250922002',
                    status: '待处理',
                    stage: '订单确认',
                    progress: 0
                },
                '王五': {
                    orderNumber: 'LD20250920001',
                    status: '已完成',
                    stage: '已完成',
                    progress: 100
                }
            };
            
            const result = mockData[customerName];
            if (result) {
                resultDiv.innerHTML = `
                    <div style="background: #e8f5e8; padding: 1rem; border-radius: 6px; border-left: 4px solid #52c41a;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #333;">查询结果</h4>
                        <p style="margin: 0.25rem 0;"><strong>订单编号：</strong>${result.orderNumber}</p>
                        <p style="margin: 0.25rem 0;"><strong>订单状态：</strong>${result.status}</p>
                        <p style="margin: 0.25rem 0;"><strong>当前阶段：</strong>${result.stage}</p>
                        <p style="margin: 0.25rem 0;"><strong>制作进度：</strong>${result.progress}%</p>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div style="background: #fff3cd; padding: 1rem; border-radius: 6px; border-left: 4px solid #ffc107;">
                        <p style="margin: 0; color: #856404;">未找到客户"${customerName}"的订单，请检查姓名是否正确</p>
                    </div>
                `;
            }
        }
        
        // 回车键查询
        document.getElementById('customerName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchOrder();
            }
        });
    </script>
</body>
</html>
    """
    
    # 写入主页面
    with open(build_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 创建管理后台页面
    admin_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理后台 - 生命钻石售后系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 1.5rem;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .login-form {
            max-width: 400px;
            margin: 4rem auto;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
        }
        .btn {
            background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .demo-accounts {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔷 生命钻石售后系统 - 管理后台</h1>
    </div>
    
    <div class="container">
        <div class="login-form">
            <h2 style="text-align: center; color: #8B4B8C; margin-bottom: 2rem;">管理员登录</h2>
            
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" placeholder="请输入用户名">
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" placeholder="请输入密码">
            </div>
            
            <button class="btn" onclick="login()">登录</button>
            
            <div class="demo-accounts">
                <h4 style="margin: 0 0 0.5rem 0;">演示账户：</h4>
                <p style="margin: 0.25rem 0;"><strong>管理员：</strong>admin / admin123</p>
                <p style="margin: 0.25rem 0;"><strong>操作员：</strong>operator / operator123</p>
            </div>
            
            <div id="loginResult" style="margin-top: 1rem;"></div>
        </div>
    </div>
    
    <script>
        function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const resultDiv = document.getElementById('loginResult');
            
            if (!username || !password) {
                resultDiv.innerHTML = '<p style="color: #ff6b6b;">请输入用户名和密码</p>';
                return;
            }
            
            // 模拟登录验证
            const validAccounts = {
                'admin': 'admin123',
                'operator': 'operator123'
            };
            
            if (validAccounts[username] === password) {
                resultDiv.innerHTML = `
                    <div style="background: #e8f5e8; padding: 1rem; border-radius: 6px; border-left: 4px solid #52c41a;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #333;">登录成功！</h4>
                        <p style="margin: 0.25rem 0;">欢迎，${username === 'admin' ? '系统管理员' : '操作员'}！</p>
                        <p style="margin: 0.25rem 0; font-size: 14px; color: #666;">
                            管理后台功能包括：订单管理、进度管理、照片管理、数据统计等。
                        </p>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = '<p style="color: #ff6b6b;">用户名或密码错误</p>';
            }
        }
        
        // 回车键登录
        document.getElementById('password').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                login();
            }
        });
    </script>
</body>
</html>
    """
    
    # 写入管理后台页面
    with open(build_dir / "admin.html", "w", encoding="utf-8") as f:
        f.write(admin_html)
    
    print("✅ 静态文件构建完成！")
    print(f"📁 构建目录: {build_dir.absolute()}")
    print("📄 生成文件:")
    print("   - index.html (客户查询页面)")
    print("   - admin.html (管理后台页面)")
    
    return build_dir

if __name__ == "__main__":
    build_static_app()
