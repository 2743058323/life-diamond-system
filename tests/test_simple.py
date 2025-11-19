#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试脚本 - 测试云函数连通性
"""

import requests
import json

def test_cloud_function():
    """测试云函数连通性"""
    print("🔷 测试CloudBase云函数连通性...")
    
    # 测试不同的云函数
    test_functions = [
        {
            "name": "admin-dashboard",
            "url": "https://cloud1-7g7o4xi13c00cb90-1379657467.ap-shanghai.app.tcloudbase.com/api/admin/dashboard",
            "data": {}
        },
        {
            "name": "admin-orders", 
            "url": "https://cloud1-7g7o4xi13c00cb90-1379657467.ap-shanghai.app.tcloudbase.com/api/admin/orders",
            "data": {"action": "list", "page": 1, "page_size": 10}
        }
    ]
    
    for func in test_functions:
        print(f"\n📡 测试云函数: {func['name']}")
        print(f"🔗 URL: {func['url']}")
        
        try:
            response = requests.post(
                func['url'],
                json=func['data'],
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "life-diamond-system-test/1.0"
                },
                timeout=10
            )
            
            print(f"📊 状态码: {response.status_code}")
            print(f"📄 响应: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("✅ 云函数调用成功")
            else:
                print("❌ 云函数调用失败")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_cloud_function()
