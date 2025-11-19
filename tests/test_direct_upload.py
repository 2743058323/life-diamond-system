#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试直接上传功能
"""

import requests
import json
import base64

def test_direct_upload():
    """测试直接上传功能"""
    print("🔷 测试直接上传功能...")
    
    # 创建一个测试图片的Base64数据
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # 测试数据
    test_data = {
        "action": "direct_upload",
        "data": {
            "cloudPath": "test/direct_upload_test.png",
            "fileContent": test_image_data,
            "fileName": "test.png"
        }
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
                print("✅ 直接上传测试成功!")
                data = result.get("data", {})
                print(f"📁 fileID: {data.get('fileID')}")
                print(f"🔗 photo_url: {data.get('photo_url')}")
                print(f"📦 storage_type: {data.get('storage_type')}")
            else:
                print(f"❌ 直接上传测试失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_direct_upload()
