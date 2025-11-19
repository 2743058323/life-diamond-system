#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色权限系统测试脚本
测试云函数是否正确处理新的数据结构
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamlit_app'))

from utils.cloudbase_client import api_client

def test_role_permissions_system():
    """测试角色权限系统"""
    print("🔐 角色权限系统测试")
    print("=" * 50)
    
    # 1. 测试获取角色列表
    print("\n1️⃣ 测试获取角色列表...")
    try:
        result = api_client.get_roles()
        if result.get('success'):
            roles = result.get('data', {}).get('roles', [])
            print(f"✅ 获取到 {len(roles)} 个角色:")
            for role in roles:
                print(f"   🔹 {role.get('display_name')} ({role.get('role_name')}) - ID: {role.get('_id')}")
        else:
            print(f"❌ 获取角色失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 获取角色异常: {str(e)}")
    
    # 2. 测试获取权限列表
    print("\n2️⃣ 测试获取权限列表...")
    try:
        result = api_client.get_permissions()
        if result.get('success'):
            permissions = result.get('data', {}).get('permissions', [])
            print(f"✅ 获取到 {len(permissions)} 个权限:")
            
            # 按分类显示权限
            categories = {}
            for perm in permissions:
                category = perm.get('category', '未分类')
                if category not in categories:
                    categories[category] = []
                categories[category].append(perm)
            
            for category, perms in categories.items():
                print(f"   📁 {category}: {len(perms)} 个权限")
                for perm in perms[:2]:  # 只显示前2个权限
                    print(f"      🔸 {perm.get('permission_name')} ({perm.get('permission_code')}) - ID: {perm.get('_id')}")
                if len(perms) > 2:
                    print(f"      ... 还有 {len(perms) - 2} 个权限")
        else:
            print(f"❌ 获取权限失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 获取权限异常: {str(e)}")
    
    # 3. 测试角色权限查询
    print("\n3️⃣ 测试角色权限查询...")
    try:
        # 先获取角色
        roles_result = api_client.get_roles()
        if roles_result.get('success'):
            roles = roles_result.get('data', {}).get('roles', [])
            
            # 测试每个角色的权限
            for role in roles:
                print(f"\n   🔍 测试角色: {role.get('display_name')} (ID: {role.get('_id')})")
                
                # 获取角色权限
                perm_result = api_client.get_role_permissions(role.get('_id'))
                if perm_result.get('success'):
                    permissions = perm_result.get('data', {}).get('permissions', [])
                    print(f"      ✅ 拥有 {len(permissions)} 个权限:")
                    for perm in permissions[:3]:  # 只显示前3个权限
                        print(f"         🔸 {perm.get('permission_name')} ({perm.get('permission_code')})")
                    if len(permissions) > 3:
                        print(f"         ... 还有 {len(permissions) - 3} 个权限")
                else:
                    print(f"      ❌ 获取权限失败: {perm_result.get('message')}")
    except Exception as e:
        print(f"❌ 测试角色权限异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 角色权限系统测试完成！")

if __name__ == "__main__":
    test_role_permissions_system()
