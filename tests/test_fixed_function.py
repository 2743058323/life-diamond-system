#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的云函数
"""

import requests
import json

def test_fixed_function():
    """测试修复后的云函数"""
    print("🔷 测试修复后的云函数...")
    
    # 测试数据
    test_data = {
        "action": "get_upload_url",
        "data": {
            "order_id": "TEST_ORDER_002",
            "stage_id": "TEST_STAGE_002", 
            "file_count": 1,
            "description": "修复后测试"
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
                    print(f"   - fileID: {url_info.get('fileID')}")
                    print(f"   - storage_type: {url_info.get('storage_type')}")
                    
                    # 检查URL是否是正确的CloudBase格式
                    upload_url = url_info.get('upload_url', '')
                    if 'tcb.qcloud.la' in upload_url or 'tcloudbase.com' in upload_url:
                        print("   ✅ URL格式正确")
                    else:
                        print("   ❌ URL格式可能有问题")
            else:
                print(f"❌ 获取上传URL失败: {result.get('message')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_fixed_function()
