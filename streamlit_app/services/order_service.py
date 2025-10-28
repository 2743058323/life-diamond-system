"""
订单服务

处理订单相关的业务逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .state_machine import OrderStateMachine, OrderStatus


class OrderService:
    """订单业务逻辑服务"""
    
    def __init__(self, api_client):
        """
        初始化订单服务
        
        Args:
            api_client: CloudBase API客户端实例
        """
        self.api_client = api_client
        self.state_machine = OrderStateMachine
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建订单
        
        自动：
        1. 生成订单号
        2. 创建所有阶段的进度记录
        3. 设置初始状态
        
        Args:
            order_data: 订单基本信息
            
        Returns:
            创建结果 {'success': bool, 'data': {...}, 'message': str}
        """
        # 调用API创建订单
        result = self.api_client.create_order(order_data)
        return result
    
    def get_order(self, order_id: str, include_progress: bool = True, 
                  include_photos: bool = True) -> Dict[str, Any]:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            include_progress: 是否包含进度信息
            include_photos: 是否包含照片信息
            
        Returns:
            订单详情 + 进度 + 照片 + 允许的操作
        """
        # 获取订单基本信息
        result = self.api_client.get_order_detail(order_id, is_admin=True)
        
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        
        # 如果数据中已经包含了所需信息，直接返回
        if isinstance(data, dict):
            order_info = data.get('order_info', {})
            progress_timeline = data.get('progress_timeline', [])
            photos = data.get('photos', [])
            
            # 计算允许的操作
            allowed_actions = self.state_machine.get_allowed_actions(
                order_info, 
                progress_timeline
            )
            
            return {
                'success': True,
                'data': {
                    'order': order_info,
                    'progress': progress_timeline,
                    'photos': photos,
                    'allowed_actions': allowed_actions
                }
            }
        
        return result
    
    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新订单基本信息
        
        Args:
            order_id: 订单ID
            update_data: 要更新的字段
            
        Returns:
            更新结果
        """
        result = self.api_client.update_admin_order(order_id, update_data)
        return result
    
    def delete_order(self, order_id: str, soft_delete: bool = True) -> Dict[str, Any]:
        """
        删除订单（软删除）
        
        Args:
            order_id: 订单ID
            soft_delete: 是否软删除（默认True）
            
        Returns:
            删除结果
        """
        result = self.api_client.delete_admin_order(order_id)
        return result
    
    def list_orders(self, page: int = 1, limit: int = 20, 
                    status: str = "all", search: str = "", 
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取订单列表
        
        Args:
            page: 页码
            limit: 每页数量
            status: 订单状态筛选
            search: 搜索关键词（订单号、客户姓名、电话）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            订单列表 + 分页信息
        """
        result = self.api_client.get_orders(
            page=page,
            limit=limit,
            status=status,
            search=search
        )
        
        return result
    
    def get_order_statistics(self) -> Dict[str, Any]:
        """
        获取订单统计信息
        
        Returns:
            统计数据：总数、各状态数量、完成率等
        """
        result = self.api_client.get_dashboard_data()
        return result
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证订单数据
        
        Args:
            order_data: 订单数据
            
        Returns:
            (is_valid, error_message)
        """
        # 必填字段
        required_fields = ['customer_name', 'customer_phone', 'diamond_type', 'diamond_size']
        
        for field in required_fields:
            if not order_data.get(field):
                return False, f"缺少必填字段：{field}"
        
        # 电话号码格式验证（简单验证）
        phone = order_data.get('customer_phone', '')
        if not phone.isdigit() or len(phone) != 11:
            return False, "电话号码格式不正确（应为11位数字）"
        
        return True, ""
    
    def can_delete_order(self, order: Dict[str, Any]) -> tuple[bool, str]:
        """
        检查是否可以删除订单
        
        Args:
            order: 订单信息
            
        Returns:
            (can_delete, reason)
        """
        order_status = order.get('order_status')
        
        # 已删除的订单不能再删除
        if order.get('is_deleted'):
            return False, "订单已被删除"
        
        # 所有状态都可以软删除
        return True, "可以删除"
    
    def format_order_for_display(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化订单数据用于显示
        
        Args:
            order: 原始订单数据
            
        Returns:
            格式化后的订单数据
        """
        return {
            'order_id': order.get('_id', ''),
            'order_number': order.get('order_number', ''),
            'customer_name': order.get('customer_name', ''),
            'customer_phone': order.get('customer_phone', ''),
            'diamond_info': f"{order.get('diamond_type', '')} {order.get('diamond_size', '')}",
            'status': order.get('order_status', '待处理'),
            'progress': order.get('progress_percentage', 0),
            'current_stage': order.get('current_stage', '未开始'),
            'created_at': order.get('created_at', ''),
            'estimated_completion': order.get('estimated_completion', ''),
        }










