"""
测试运行器

运行所有测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'streamlit_app'))

from test_state_machine import run_all_tests as test_state_machine
from test_services import run_all_tests as test_services


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 生命钻石订单系统 - 业务逻辑层测试套件")
    print("="*70)
    
    results = []
    
    # 测试1: 状态机
    print("\n📍 第1部分：状态机测试")
    results.append(('状态机', test_state_machine()))
    
    # 测试2: 服务层
    print("\n📍 第2部分：服务层测试")
    results.append(('服务层', test_services()))
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试结果总结")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 所有测试通过！业务逻辑层工作正常！")
        print("\n✨ 你可以放心地基于这个业务逻辑层构建UI了！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查代码！")
        return 1


if __name__ == "__main__":
    exit(main())










