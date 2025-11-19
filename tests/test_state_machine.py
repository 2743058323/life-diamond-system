"""
状态机测试

测试订单和阶段的状态转换逻辑
"""

import sys
sys.path.insert(0, '../streamlit_app')

from services.state_machine import OrderStateMachine, OrderStatus, StageStatus


def test_order_state_transitions():
    """测试订单状态转换"""
    print("\n=== 测试订单状态转换 ===")
    
    # 测试1: 待处理 -> 制作中
    can_transition = OrderStateMachine.can_transition_order("待处理", "制作中")
    assert can_transition == True, "待处理应该可以转换到制作中"
    print("✅ 测试1通过: 待处理 -> 制作中")
    
    # 测试2: 待处理 -> 已完成 (不允许)
    can_transition = OrderStateMachine.can_transition_order("待处理", "已完成")
    assert can_transition == False, "待处理不能直接转换到已完成"
    print("✅ 测试2通过: 待处理 -X-> 已完成")
    
    # 测试3: 制作中 -> 已完成
    can_transition = OrderStateMachine.can_transition_order("制作中", "已完成")
    assert can_transition == True, "制作中应该可以转换到已完成"
    print("✅ 测试3通过: 制作中 -> 已完成")
    
    # 测试4: 已完成 -> 制作中 (不允许，终态)
    can_transition = OrderStateMachine.can_transition_order("已完成", "制作中")
    assert can_transition == False, "已完成是终态，不能转换"
    print("✅ 测试4通过: 已完成是终态")


def test_stage_state_transitions():
    """测试阶段状态转换"""
    print("\n=== 测试阶段状态转换 ===")
    
    # 测试1: pending -> in_progress
    can_transition = OrderStateMachine.can_transition_stage("pending", "in_progress")
    assert can_transition == True, "pending应该可以转换到in_progress"
    print("✅ 测试1通过: pending -> in_progress")
    
    # 测试2: in_progress -> completed
    can_transition = OrderStateMachine.can_transition_stage("in_progress", "completed")
    assert can_transition == True, "in_progress应该可以转换到completed"
    print("✅ 测试2通过: in_progress -> completed")
    
    # 测试3: completed -> pending (不允许，不可回退)
    can_transition = OrderStateMachine.can_transition_stage("completed", "pending")
    assert can_transition == False, "completed不能回退到pending"
    print("✅ 测试3通过: completed不可回退")


def test_can_start_stage():
    """测试开始阶段的规则"""
    print("\n=== 测试开始阶段规则 ===")
    
    # 模拟进度数据
    progress_list = [
        {
            'stage_id': 'stage_1',
            'stage_name': '材料准备',
            'stage_order': 1,
            'status': 'completed'
        },
        {
            'stage_id': 'stage_2',
            'stage_name': '钻石制作',
            'stage_order': 2,
            'status': 'pending'
        },
        {
            'stage_id': 'stage_3',
            'stage_name': '打磨抛光',
            'stage_order': 3,
            'status': 'pending'
        }
    ]
    
    # 测试1: 开始第二阶段（前一阶段已完成）
    can_start, reason = OrderStateMachine.can_start_stage(progress_list, 'stage_2')
    assert can_start == True, f"应该可以开始stage_2，原因：{reason}"
    print(f"✅ 测试1通过: 可以开始stage_2 ({reason})")
    
    # 测试2: 跳跃式开始第三阶段（不允许）
    can_start, reason = OrderStateMachine.can_start_stage(progress_list, 'stage_3')
    assert can_start == False, "不应该跳跃式开始stage_3"
    print(f"✅ 测试2通过: 不能跳跃开始stage_3 ({reason})")
    
    # 测试3: 有阶段正在进行时，不能开始新阶段
    progress_list[1]['status'] = 'in_progress'
    progress_list_with_in_progress = progress_list + [{
        'stage_id': 'stage_4',
        'stage_name': '质检',
        'stage_order': 4,
        'status': 'pending'
    }]
    
    can_start, reason = OrderStateMachine.can_start_stage(progress_list_with_in_progress, 'stage_4')
    assert can_start == False, "有阶段进行中时不能开始新阶段"
    print(f"✅ 测试3通过: 有进行中阶段时不能开始新阶段 ({reason})")


def test_calculate_progress():
    """测试进度百分比计算"""
    print("\n=== 测试进度计算 ===")
    
    # 测试1: 0%
    progress_list = [
        {'status': 'pending'},
        {'status': 'pending'},
        {'status': 'pending'},
        {'status': 'pending'}
    ]
    percentage = OrderStateMachine.calculate_progress(progress_list)
    assert percentage == 0, f"应该是0%，实际：{percentage}%"
    print(f"✅ 测试1通过: 0个完成/4个总数 = {percentage}%")
    
    # 测试2: 50%
    progress_list[0]['status'] = 'completed'
    progress_list[1]['status'] = 'completed'
    percentage = OrderStateMachine.calculate_progress(progress_list)
    assert percentage == 50, f"应该是50%，实际：{percentage}%"
    print(f"✅ 测试2通过: 2个完成/4个总数 = {percentage}%")
    
    # 测试3: 100%
    progress_list[2]['status'] = 'completed'
    progress_list[3]['status'] = 'completed'
    percentage = OrderStateMachine.calculate_progress(progress_list)
    assert percentage == 100, f"应该是100%，实际：{percentage}%"
    print(f"✅ 测试3通过: 4个完成/4个总数 = {percentage}%")


def test_auto_update_order_status():
    """测试自动更新订单状态"""
    print("\n=== 测试自动更新订单状态 ===")
    
    # 测试1: 所有pending -> 待处理
    progress_list = [
        {'status': 'pending'},
        {'status': 'pending'}
    ]
    status = OrderStateMachine.auto_update_order_status(progress_list)
    assert status == "待处理", f"应该是待处理，实际：{status}"
    print(f"✅ 测试1通过: 所有pending -> {status}")
    
    # 测试2: 有in_progress -> 制作中
    progress_list[0]['status'] = 'in_progress'
    status = OrderStateMachine.auto_update_order_status(progress_list)
    assert status == "制作中", f"应该是制作中，实际：{status}"
    print(f"✅ 测试2通过: 有in_progress -> {status}")
    
    # 测试3: 所有completed -> 已完成
    progress_list[0]['status'] = 'completed'
    progress_list[1]['status'] = 'completed'
    status = OrderStateMachine.auto_update_order_status(progress_list)
    assert status == "已完成", f"应该是已完成，实际：{status}"
    print(f"✅ 测试3通过: 所有completed -> {status}")


def test_get_current_stage_name():
    """测试获取当前阶段名称"""
    print("\n=== 测试获取当前阶段名称 ===")
    
    # 测试1: 所有pending -> 返回第一个阶段
    progress_list = [
        {'stage_name': '材料准备', 'stage_order': 1, 'status': 'pending'},
        {'stage_name': '钻石制作', 'stage_order': 2, 'status': 'pending'}
    ]
    stage_name = OrderStateMachine.get_current_stage_name(progress_list)
    assert stage_name == "材料准备", f"应该是材料准备，实际：{stage_name}"
    print(f"✅ 测试1通过: 所有pending -> {stage_name}")
    
    # 测试2: 有in_progress -> 返回进行中阶段
    progress_list[1]['status'] = 'in_progress'
    stage_name = OrderStateMachine.get_current_stage_name(progress_list)
    assert stage_name == "钻石制作", f"应该是钻石制作，实际：{stage_name}"
    print(f"✅ 测试2通过: 有in_progress -> {stage_name}")
    
    # 测试3: 所有completed -> 返回"已完成"
    progress_list[0]['status'] = 'completed'
    progress_list[1]['status'] = 'completed'
    stage_name = OrderStateMachine.get_current_stage_name(progress_list)
    assert stage_name == "已完成", f"应该是已完成，实际：{stage_name}"
    print(f"✅ 测试3通过: 所有completed -> {stage_name}")


def test_get_allowed_actions():
    """测试获取允许的操作"""
    print("\n=== 测试允许的操作 ===")
    
    # 测试1: 待处理状态
    order = {
        'order_status': '待处理',
        'is_deleted': False
    }
    progress_list = []
    actions = OrderStateMachine.get_allowed_actions(order, progress_list)
    assert 'edit_info' in actions, "待处理应该允许编辑信息"
    assert 'start_first_stage' in actions, "待处理应该允许开始第一阶段"
    assert 'delete' in actions, "待处理应该允许删除"
    print(f"✅ 测试1通过: 待处理状态允许的操作: {actions}")
    
    # 测试2: 制作中状态
    order['order_status'] = '制作中'
    progress_list = [{'status': 'in_progress'}]
    actions = OrderStateMachine.get_allowed_actions(order, progress_list)
    assert 'complete_stage' in actions, "制作中应该允许完成阶段"
    assert 'upload_photo' in actions, "制作中应该允许上传照片"
    print(f"✅ 测试2通过: 制作中状态允许的操作: {actions}")
    
    # 测试3: 已完成状态
    order['order_status'] = '已完成'
    progress_list = [{'status': 'completed'}]
    actions = OrderStateMachine.get_allowed_actions(order, progress_list)
    assert 'edit_info' not in actions, "已完成不应该允许编辑基本信息"
    assert 'view_details' in actions, "已完成应该允许查看详情"
    print(f"✅ 测试3通过: 已完成状态允许的操作: {actions}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 开始测试订单状态机")
    print("="*60)
    
    try:
        test_order_state_transitions()
        test_stage_state_transitions()
        test_can_start_stage()
        test_calculate_progress()
        test_auto_update_order_status()
        test_get_current_stage_name()
        test_get_allowed_actions()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！状态机逻辑正确！")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)










