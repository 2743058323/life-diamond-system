#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云存储测试脚本
测试CloudBase云存储的照片上传功能
"""

import requests
import json
import base64
import io
from PIL import Image
import os

def create_test_image():
    """创建一个测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_data = img_buffer.getvalue()
    
    # 转换为Base64
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    return {
        'name': 'test_image.jpg',
        'type': 'image/jpeg',
        'size': len(img_data),
        'content': img_base64
    }

def test_cloud_storage():
    """测试云存储功能"""
    print("🔷 开始测试CloudBase云存储功能...")
    
    # 测试数据
    test_data = {
        "action": "get_upload_url",
        "data": {
            "order_id": "TEST_ORDER_001",
            "stage_id": "TEST_STAGE_001", 
            "file_count": 1,
            "description": "云存储测试图片"
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
                print("✅ 获取上传URL成功!")
                upload_urls = result.get("data", {}).get("upload_urls", [])
                print(f"📁 生成的上传URL数量: {len(upload_urls)}")
                
                for i, url_info in enumerate(upload_urls):
                    print(f"📎 URL {i+1}:")
                    print(f"   - file_id: {url_info.get('file_id')}")
                    print(f"   - upload_url: {url_info.get('upload_url')}")
                    print(f"   - photo_url: {url_info.get('photo_url')}")
                    print(f"   - storage_type: {url_info.get('storage_type')}")
                
                # 测试实际文件上传
                test_actual_upload(upload_urls[0])
            else:
                print(f"❌ 获取上传URL失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

def test_actual_upload(upload_url_info):
    """测试实际文件上传"""
    print("\n🔷 开始测试实际文件上传...")
    
    # 创建测试图片
    test_image = create_test_image()
    print(f"📷 创建测试图片: {test_image['name']} ({test_image['size']} bytes)")
    
    # 准备上传数据
    upload_data = {
        "action": "upload",
        "data": {
            "order_id": "TEST_ORDER_001",
            "stage_id": "TEST_STAGE_001",
            "files": [test_image]
        }
    }
    
    cloudbase_url = "https://cloud1-7g7o4xi13c00cb90-1379657467.ap-shanghai.app.tcloudbase.com/api/admin/photos/upload"
    
    try:
        response = requests.post(
            cloudbase_url,
            json=upload_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "life-diamond-system-test/1.0"
            },
            timeout=60
        )
        
        print(f"📡 上传响应状态: {response.status_code}")
        print(f"📄 上传响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ 文件上传成功!")
                uploaded_photos = result.get("data", {}).get("uploaded_photos", [])
                print(f"📁 上传成功文件数: {len(uploaded_photos)}")
                
                for photo in uploaded_photos:
                    print(f"📎 上传文件:")
                    print(f"   - photo_id: {photo.get('photo_id')}")
                    print(f"   - file_name: {photo.get('file_name')}")
                    print(f"   - photo_url: {photo.get('photo_url')}")
                    print(f"   - storage_type: {photo.get('storage_type')}")
            else:
                print(f"❌ 文件上传失败: {result.get('message')}")
        else:
            print(f"❌ 上传请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 上传测试异常: {str(e)}")

if __name__ == "__main__":
    test_cloud_storage()
