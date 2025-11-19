#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化云函数测试脚本
"""

import requests
import json

def test_simple_function():
    """测试简化版云函数"""
    print("🔷 测试简化版云函数...")
    
    # 测试数据
    test_data = {
        "action": "test",
        "data": {}
    }
    
    # CloudBase云函数URL
    cloudbase_url = "https://cloud1-7g7o4xi13c00cb90-1379657467.ap-shanghai.app.tcloudbase.com/api/admin/photos/upload"
    
    print(f"📡 测试URL: {cloudbase_url}")
    print(f"📊 请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送请求
        response = requests.post(
            cloudbase_url,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "life-diamond-system-test/1.0"
            },
            timeout=30
        )
        
        print(f"📡 响应状态: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 云函数测试成功!")
                print(f"📁 环境ID: {result.get('data', {}).get('env_id')}")
                print(f"⏰ 时间戳: {result.get('data', {}).get('timestamp')}")
            else:
                print(f"❌ 云函数返回失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

def test_get_upload_url():
    """测试获取上传URL功能"""
    print("\n🔷 测试获取上传URL功能...")
    
    test_data = {
        "action": "get_upload_url",
        "data": {
            "order_id": "TEST_ORDER_001",
            "stage_id": "TEST_STAGE_001", 
            "file_count": 2,
            "description": "测试图片"
        }
    }
    
    cloudbase_url = "https://cloud1-7g7o4xi13c00cb90-1379657467.ap-shanghai.app.tcloudbase.com/api/admin/photos/upload"
    
    try:
        response = requests.post(
            cloudbase_url,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "life-diamond-system-test/1.0"
            },
            timeout=30
        )
        
        print(f"📡 响应状态: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 获取上传URL成功!")
                upload_urls = result.get("data", {}).get("upload_urls", [])
                print(f"📁 生成的上传URL数量: {len(upload_urls)}")
                
                for i, url_info in enumerate(upload_urls):
                    print(f"📎 URL {i+1}:")
                    print(f"   - file_id: {url_info.get('file_id')}")
                    print(f"   - upload_url: {url_info.get('upload_url')}")
                    print(f"   - photo_url: {url_info.get('photo_url')}")
            else:
                print(f"❌ 获取上传URL失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_simple_function()
    test_get_upload_url()
