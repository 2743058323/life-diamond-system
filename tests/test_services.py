"""
服务层测试

测试 OrderService、ProgressService、PhotoService
使用模拟的API客户端
"""

import sys
sys.path.insert(0, '../streamlit_app')

from typing import Dict, Any


class MockAPIClient:
    """模拟的API客户端"""
    
    def __init__(self):
        self.mock_data = {
            'orders': {},
            'progress': {},
            'photos': {}
        }
    
    def get_order_detail(self, order_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """模拟获取订单详情"""
        return {
            'success': True,
            'data': {
                'order_info': {
                    '_id': order_id,
                    'order_number': 'LD-2024-001',
                    'customer_name': '张三',
                    'order_status': '制作中',
                    'progress_percentage': 50,
                    'is_deleted': False
                },
                'progress_timeline': [
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
                        'status': 'in_progress'
                    }
                ],
                'photos': []
            }
        }
    
    def update_order_progress(self, order_id: str, stage_id: str, 
                            status: str, notes: str = "") -> Dict[str, Any]:
        """模拟更新进度"""
        return {
            'success': True,
            'data': {
                'progress_percentage': 75,
                'current_stage': '打磨抛光',
                'order_status': '制作中'
            }
        }
    
    def upload_photos(self, order_id: str, stage_id: str, stage_name: str,
                     photos: list, description: str = "") -> Dict[str, Any]:
        """模拟上传照片"""
        return {
            'success': True,
            'data': {
                'uploaded': len(photos),
                'failed': 0
            }
        }


def test_order_service():
    """测试订单服务"""
    print("\n=== 测试订单服务 ===")
    
    from services.order_service import OrderService
    
    mock_client = MockAPIClient()
    order_service = OrderService(mock_client)
    
    # 测试1: 获取订单详情
    result = order_service.get_order('test_order_id')
    assert result['success'] == True, "获取订单应该成功"
    assert 'allowed_actions' in result['data'], "应该包含允许的操作"
    print(f"✅ 测试1通过: 获取订单详情成功")
    print(f"   允许的操作: {result['data']['allowed_actions']}")
    
    # 测试2: 验证订单数据
    valid_data = {
        'customer_name': '李四',
        'customer_phone': '13800138000',
        'diamond_type': '纪念钻石',
        'diamond_size': '0.5克拉'
    }
    is_valid, error = order_service.validate_order_data(valid_data)
    assert is_valid == True, f"有效数据应该通过验证: {error}"
    print("✅ 测试2通过: 订单数据验证成功")
    
    # 测试3: 验证无效数据（缺少必填字段）
    invalid_data = {
        'customer_name': '王五'
        # 缺少其他必填字段
    }
    is_valid, error = order_service.validate_order_data(invalid_data)
    assert is_valid == False, "无效数据应该验证失败"
    print(f"✅ 测试3通过: 无效数据被正确拒绝 ({error})")
    
    # 测试4: 验证电话号码格式
    invalid_phone_data = {
        'customer_name': '赵六',
        'customer_phone': '12345',  # 无效电话
        'diamond_type': '纪念钻石',
        'diamond_size': '0.5克拉'
    }
    is_valid, error = order_service.validate_order_data(invalid_phone_data)
    assert is_valid == False, "无效电话应该验证失败"
    print(f"✅ 测试4通过: 电话格式验证成功 ({error})")
    
    # 测试5: 格式化订单显示
    order = {
        '_id': 'test_id',
        'order_number': 'LD-2024-001',
        'customer_name': '张三',
        'diamond_type': '纪念钻石',
        'diamond_size': '0.5克拉',
        'progress_percentage': 75
    }
    formatted = order_service.format_order_for_display(order)
    assert 'diamond_info' in formatted, "应该包含钻石信息"
    assert formatted['diamond_info'] == "纪念钻石 0.5克拉", "钻石信息格式应该正确"
    print("✅ 测试5通过: 订单格式化成功")


def test_progress_service():
    """测试进度服务"""
    print("\n=== 测试进度服务 ===")
    
    from services.progress_service import ProgressService
    
    mock_client = MockAPIClient()
    progress_service = ProgressService(mock_client)
    
    # 测试1: 获取进度
    result = progress_service.get_progress('test_order_id')
    assert result['success'] == True, "获取进度应该成功"
    print("✅ 测试1通过: 获取进度成功")
    
    # 测试2: 获取下一阶段
    progress_list = [
        {'stage_id': 'stage_1', 'stage_order': 1, 'status': 'completed'},
        {'stage_id': 'stage_2', 'stage_order': 2, 'status': 'pending'},
        {'stage_id': 'stage_3', 'stage_order': 3, 'status': 'pending'}
    ]
    next_stage = progress_service.get_next_stage(progress_list)
    assert next_stage is not None, "应该找到下一阶段"
    assert next_stage['stage_id'] == 'stage_2', "下一阶段应该是stage_2"
    print(f"✅ 测试2通过: 找到下一阶段 ({next_stage['stage_id']})")
    
    # 测试3: 获取当前阶段
    progress_list[1]['status'] = 'in_progress'
    current_stage = progress_service.get_current_stage(progress_list)
    assert current_stage is not None, "应该找到当前阶段"
    assert current_stage['stage_id'] == 'stage_2', "当前阶段应该是stage_2"
    print(f"✅ 测试3通过: 找到当前阶段 ({current_stage['stage_id']})")
    
    # 测试4: 获取已完成阶段
    completed = progress_service.get_completed_stages(progress_list)
    assert len(completed) == 1, "应该有1个已完成阶段"
    print(f"✅ 测试4通过: 找到{len(completed)}个已完成阶段")
    
    # 测试5: 格式化时间轴数据
    formatted = progress_service.format_progress_for_timeline(progress_list)
    assert len(formatted) == 3, "应该格式化3个阶段"
    assert 'icon' in formatted[0], "应该包含图标"
    assert 'status_display' in formatted[0], "应该包含状态显示文本"
    print("✅ 测试5通过: 时间轴数据格式化成功")


def test_photo_service():
    """测试照片服务"""
    print("\n=== 测试照片服务 ===")
    
    from services.photo_service import PhotoService
    
    mock_client = MockAPIClient()
    photo_service = PhotoService(mock_client)
    
    # 测试1: 按阶段分组照片
    photos_data = [
        {
            'stage_name': '材料准备',
            'photos': [
                {'photo_url': 'url1'},
                {'photo_url': 'url2'}
            ]
        },
        {
            'stage_name': '钻石制作',
            'photos': [
                {'photo_url': 'url3'}
            ]
        }
    ]
    grouped = photo_service.group_photos_by_stage(photos_data)
    assert '材料准备' in grouped, "应该包含材料准备阶段"
    assert len(grouped['材料准备']) == 2, "材料准备应该有2张照片"
    print("✅ 测试1通过: 照片按阶段分组成功")
    
    # 测试2: 获取照片总数
    total = photo_service.get_photo_count(photos_data)
    assert total == 3, f"应该有3张照片，实际：{total}"
    print(f"✅ 测试2通过: 照片总数计算正确 ({total}张)")
    
    # 测试3: 验证空照片列表
    is_valid, error = photo_service.validate_photo_files([])
    assert is_valid == False, "空照片列表应该验证失败"
    print(f"✅ 测试3通过: 空照片列表被正确拒绝 ({error})")
    
    # 测试4: 模拟文件验证
    class MockFile:
        def __init__(self, size, file_type):
            self.size = size
            self.type = file_type
    
    # 文件过大
    large_file = MockFile(6 * 1024 * 1024, 'image/jpeg')  # 6MB
    is_valid, error = photo_service.validate_photo_files([large_file])
    assert is_valid == False, "过大文件应该验证失败"
    print(f"✅ 测试4通过: 文件大小验证成功 ({error})")
    
    # 文件类型不支持
    invalid_type_file = MockFile(1024, 'image/gif')
    is_valid, error = photo_service.validate_photo_files([invalid_type_file])
    assert is_valid == False, "不支持的文件类型应该验证失败"
    print(f"✅ 测试5通过: 文件类型验证成功 ({error})")
    
    # 有效文件
    valid_file = MockFile(1024 * 1024, 'image/jpeg')  # 1MB JPG
    is_valid, error = photo_service.validate_photo_files([valid_file])
    assert is_valid == True, f"有效文件应该通过验证: {error}"
    print("✅ 测试6通过: 有效文件验证成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 开始测试服务层")
    print("="*60)
    
    try:
        test_order_service()
        test_progress_service()
        test_photo_service()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！服务层逻辑正确！")
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










