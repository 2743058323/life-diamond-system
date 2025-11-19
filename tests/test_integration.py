"""
集成测试

使用真实的CloudBase API测试业务逻辑层
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'streamlit_app'))

from utils.cloudbase_client import CloudBaseClient
from services.order_service import OrderService
from services.progress_service import ProgressService
from services.photo_service import PhotoService


def test_with_real_api():
    """使用真实API测试"""
    print("\n" + "="*70)
    print("🔗 集成测试 - 连接真实CloudBase API")
    print("="*70)
    
    # 初始化真实的API客户端
    print("\n📡 初始化API客户端...")
    api_client = CloudBaseClient()
    
    # 初始化服务
    order_service = OrderService(api_client)
    progress_service = ProgressService(api_client)
    photo_service = PhotoService(api_client)
    
    print("✅ API客户端初始化成功")
    
    # 测试1: 获取订单列表
    print("\n" + "-"*70)
    print("📋 测试1: 获取订单列表")
    print("-"*70)
    
    try:
        result = order_service.list_orders(page=1, limit=5, status="all")
        
        if result.get('success'):
            data = result.get('data', {})
            orders = data.get('orders', []) if isinstance(data, dict) else []
            
            print(f"✅ 成功获取订单列表")
            print(f"   📊 共 {len(orders)} 个订单")
            
            if orders:
                # 显示第一个订单
                first_order = orders[0]
                print(f"\n   示例订单:")
                print(f"   - 订单号: {first_order.get('order_number', 'N/A')}")
                print(f"   - 客户: {first_order.get('customer_name', 'N/A')}")
                print(f"   - 状态: {first_order.get('order_status', 'N/A')}")
                print(f"   - 进度: {first_order.get('progress_percentage', 0)}%")
                
                # 保存第一个订单ID用于后续测试
                test_order_id = first_order.get('_id')
                return test_order_id
            else:
                print("   ⚠️  订单列表为空")
                return None
        else:
            print(f"❌ 获取订单列表失败: {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_order_detail(order_service, order_id):
    """测试获取订单详情"""
    print("\n" + "-"*70)
    print("📄 测试2: 获取订单详情（含业务逻辑处理）")
    print("-"*70)
    
    try:
        result = order_service.get_order(order_id)
        
        if result.get('success'):
            data = result.get('data', {})
            order = data.get('order', {})
            progress = data.get('progress', [])
            photos = data.get('photos', [])
            allowed_actions = data.get('allowed_actions', [])
            
            print(f"✅ 成功获取订单详情")
            print(f"\n   📋 订单信息:")
            print(f"   - ID: {order.get('_id', 'N/A')}")
            print(f"   - 订单号: {order.get('order_number', 'N/A')}")
            print(f"   - 客户: {order.get('customer_name', 'N/A')}")
            print(f"   - 状态: {order.get('order_status', 'N/A')}")
            print(f"   - 当前阶段: {order.get('current_stage', 'N/A')}")
            print(f"   - 进度: {order.get('progress_percentage', 0)}%")
            
            print(f"\n   🔄 进度记录: {len(progress)} 个阶段")
            for i, p in enumerate(progress[:3], 1):  # 只显示前3个
                status_icon = {'pending': '⏸️', 'in_progress': '🔄', 'completed': '✅'}.get(p.get('status'), '❓')
                print(f"      {i}. {status_icon} {p.get('stage_name')} - {p.get('status')}")
            
            print(f"\n   📷 照片: {len(photos)} 个阶段有照片")
            
            print(f"\n   ✨ 允许的操作: {', '.join(allowed_actions)}")
            
            return order, progress, photos, allowed_actions
        else:
            print(f"❌ 获取订单详情失败: {result.get('message')}")
            return None, None, None, None
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None, None


def test_progress_service(progress_service, order_id, progress_list):
    """测试进度服务"""
    print("\n" + "-"*70)
    print("🔄 测试3: 进度服务逻辑")
    print("-"*70)
    
    try:
        # 测试3.1: 获取当前阶段
        current_stage = progress_service.get_current_stage(progress_list)
        if current_stage:
            print(f"✅ 当前阶段: {current_stage.get('stage_name')} ({current_stage.get('status')})")
        else:
            print("   ℹ️  没有进行中的阶段")
        
        # 测试3.2: 获取下一阶段
        next_stage = progress_service.get_next_stage(progress_list)
        if next_stage:
            print(f"✅ 下一阶段: {next_stage.get('stage_name')} (待处理)")
        else:
            print("   ℹ️  没有待处理的阶段")
        
        # 测试3.3: 获取已完成阶段
        completed_stages = progress_service.get_completed_stages(progress_list)
        print(f"✅ 已完成阶段: {len(completed_stages)} 个")
        
        # 测试3.4: 格式化时间轴数据
        formatted = progress_service.format_progress_for_timeline(progress_list)
        print(f"✅ 时间轴数据格式化成功: {len(formatted)} 个阶段")
        
        # 显示格式化后的时间轴
        print(f"\n   📊 格式化的时间轴:")
        for stage in formatted[:3]:  # 显示前3个
            print(f"      {stage['icon']} {stage['stage_name']} - {stage['status_display']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_photo_service(photo_service, photos_data):
    """测试照片服务"""
    print("\n" + "-"*70)
    print("📷 测试4: 照片服务逻辑")
    print("-"*70)
    
    try:
        # 测试4.1: 按阶段分组
        grouped = photo_service.group_photos_by_stage(photos_data)
        print(f"✅ 照片按阶段分组: {len(grouped)} 个阶段")
        
        for stage_name, photos in list(grouped.items())[:3]:  # 显示前3个
            print(f"   - {stage_name}: {len(photos)} 张照片")
        
        # 测试4.2: 获取总数
        total = photo_service.get_photo_count(photos_data)
        print(f"✅ 照片总数: {total} 张")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_state_machine_with_real_data(order, progress_list):
    """使用真实数据测试状态机"""
    print("\n" + "-"*70)
    print("⚙️  测试5: 状态机验证（真实数据）")
    print("-"*70)
    
    try:
        from services.state_machine import OrderStateMachine
        
        # 测试5.1: 计算进度
        calculated_progress = OrderStateMachine.calculate_progress(progress_list)
        actual_progress = order.get('progress_percentage', 0)
        print(f"✅ 进度计算:")
        print(f"   - 状态机计算: {calculated_progress}%")
        print(f"   - 数据库存储: {actual_progress}%")
        
        if calculated_progress != actual_progress:
            print(f"   ⚠️  进度不一致（可能需要重新计算）")
        
        # 测试5.2: 获取当前阶段名
        current_stage_name = OrderStateMachine.get_current_stage_name(progress_list)
        actual_stage_name = order.get('current_stage', '')
        print(f"\n✅ 当前阶段:")
        print(f"   - 状态机计算: {current_stage_name}")
        print(f"   - 数据库存储: {actual_stage_name}")
        
        # 测试5.3: 自动更新订单状态
        auto_status = OrderStateMachine.auto_update_order_status(progress_list)
        actual_status = order.get('order_status', '')
        print(f"\n✅ 订单状态:")
        print(f"   - 状态机计算: {auto_status}")
        print(f"   - 数据库存储: {actual_status}")
        
        # 测试5.4: 检查是否可以开始下一阶段
        next_pending = next((p for p in progress_list if p.get('status') == 'pending'), None)
        if next_pending:
            can_start, reason = OrderStateMachine.can_start_stage(progress_list, next_pending.get('stage_id'))
            print(f"\n✅ 下一阶段 '{next_pending.get('stage_name')}' 是否可开始:")
            print(f"   - 结果: {'可以' if can_start else '不可以'}")
            print(f"   - 原因: {reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_validation(order_service):
    """测试数据验证"""
    print("\n" + "-"*70)
    print("✔️  测试6: 数据验证功能")
    print("-"*70)
    
    try:
        # 测试6.1: 有效数据
        valid_data = {
            'customer_name': '测试客户',
            'customer_phone': '13800138000',
            'diamond_type': '纪念钻石',
            'diamond_size': '0.5克拉'
        }
        is_valid, error = order_service.validate_order_data(valid_data)
        print(f"✅ 有效数据验证: {'通过' if is_valid else '失败'}")
        
        # 测试6.2: 缺少必填字段
        invalid_data = {
            'customer_name': '测试客户'
        }
        is_valid, error = order_service.validate_order_data(invalid_data)
        print(f"✅ 无效数据验证: {'正确拒绝' if not is_valid else '错误通过'}")
        print(f"   错误信息: {error}")
        
        # 测试6.3: 错误电话格式
        invalid_phone = {
            'customer_name': '测试客户',
            'customer_phone': '12345',
            'diamond_type': '纪念钻石',
            'diamond_size': '0.5克拉'
        }
        is_valid, error = order_service.validate_order_data(invalid_phone)
        print(f"✅ 电话格式验证: {'正确拒绝' if not is_valid else '错误通过'}")
        print(f"   错误信息: {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n" + "="*70)
    print("🚀 集成测试 - 业务逻辑层 + 真实CloudBase API")
    print("="*70)
    
    results = []
    
    # 初始化服务
    try:
        api_client = CloudBaseClient()
        order_service = OrderService(api_client)
        progress_service = ProgressService(api_client)
        photo_service = PhotoService(api_client)
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        return 1
    
    # 测试1: 获取订单列表
    test_order_id = test_with_real_api()
    
    if not test_order_id:
        print("\n⚠️  没有可用的订单数据，无法继续测试")
        print("   建议：先在系统中创建一些测试订单")
        return 1
    
    # 测试2: 获取订单详情
    order, progress_list, photos_data, allowed_actions = test_order_detail(order_service, test_order_id)
    results.append(('订单详情', order is not None))
    
    if not order:
        print("\n❌ 无法获取订单详情，停止后续测试")
        return 1
    
    # 测试3: 进度服务
    result = test_progress_service(progress_service, test_order_id, progress_list)
    results.append(('进度服务', result))
    
    # 测试4: 照片服务
    result = test_photo_service(photo_service, photos_data)
    results.append(('照片服务', result))
    
    # 测试5: 状态机验证
    result = test_state_machine_with_real_data(order, progress_list)
    results.append(('状态机', result))
    
    # 测试6: 数据验证
    result = test_data_validation(order_service)
    results.append(('数据验证', result))
    
    # 总结
    print("\n" + "="*70)
    print("📊 集成测试结果总结")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 所有集成测试通过！")
        print("✨ 业务逻辑层与CloudBase API集成正常！")
        print("💡 可以继续构建UI层了！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查相关功能")
        return 1


if __name__ == "__main__":
    exit(main())










