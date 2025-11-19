#!/usr/bin/env python3
"""
测试不同登录场景的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'streamlit_app'))

from streamlit_app.utils.cloudbase_client import api_client

def test_login_scenarios():
    """测试不同的登录场景"""
    print("🔍 测试登录场景...")
    
    # 测试场景
    test_cases = [
        {
            "name": "正确登录",
            "username": "admin",
            "password": "admin123",
            "expected": "成功"
        },
        {
            "name": "用户名不存在",
            "username": "nonexistent",
            "password": "password",
            "expected": "用户名或密码错误"
        },
        {
            "name": "密码错误",
            "username": "admin",
            "password": "wrongpassword",
            "expected": "用户名或密码错误"
        },
        {
            "name": "账户被禁用",
            "username": "123",
            "password": "123456",  # 这个密码需要根据实际情况调整
            "expected": "账户已被禁用"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试场景: {test_case['name']}")
        print(f"   用户名: {test_case['username']}")
        print(f"   密码: {test_case['password']}")
        print(f"   期望结果: {test_case['expected']}")
        
        result = api_client.admin_login(test_case['username'], test_case['password'])
        
        if result.get("success"):
            print(f"   ✅ 实际结果: 登录成功")
        else:
            message = result.get("message", "未知错误")
            error_code = result.get("error_code", "")
            print(f"   ❌ 实际结果: {message}")
            if error_code:
                print(f"   错误代码: {error_code}")
        
        # 检查是否符合期望
        if test_case['expected'] == "成功":
            if result.get("success"):
                print("   ✅ 测试通过")
            else:
                print("   ❌ 测试失败")
        else:
            if not result.get("success") and test_case['expected'] in result.get("message", ""):
                print("   ✅ 测试通过")
            else:
                print("   ❌ 测试失败")

if __name__ == "__main__":
    test_login_scenarios()
