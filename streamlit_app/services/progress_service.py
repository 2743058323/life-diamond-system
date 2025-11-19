"""
进度服务

处理订单进度相关的业务逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .state_machine import OrderStateMachine, StageStatus


class ProgressService:
    """进度业务逻辑服务"""
    
    def __init__(self, api_client):
        """
        初始化进度服务
        
        Args:
            api_client: CloudBase API客户端实例
        """
        self.api_client = api_client
        self.state_machine = OrderStateMachine
    
    def get_progress(self, order_id: str) -> Dict[str, Any]:
        """
        获取订单的所有进度记录
        
        Args:
            order_id: 订单ID
            
        Returns:
            进度记录列表
        """
        # 通过订单详情获取进度
        result = self.api_client.get_order_detail(order_id, is_admin=True)
        
        if result.get('success'):
            data = result.get('data', {})
            progress_timeline = data.get('progress_timeline', [])
            return {
                'success': True,
                'data': progress_timeline
            }
        
        return result
    
    def start_stage(self, order_id: str, stage_id: str) -> Dict[str, Any]:
        """
        开始某个阶段
        
        校验：
        1. 前一阶段必须已完成
        2. 没有其他阶段在进行中
        3. 当前阶段必须是pending状态
        
        Args:
            order_id: 订单ID
            stage_id: 阶段ID
            
        Returns:
            更新结果 + 新的订单状态和进度
        """
        # 先获取当前进度列表进行校验
        progress_result = self.get_progress(order_id)
        if not progress_result.get('success'):
            return progress_result
        
        progress_list = progress_result.get('data', [])
        
        # 使用状态机检查是否可以开始
        can_start, reason = self.state_machine.can_start_stage(progress_list, stage_id)
        if not can_start:
            return {
                'success': False,
                'message': reason
            }
        
        # 调用API更新进度
        result = self.api_client.update_order_progress(
            order_id=order_id,
            stage_id=stage_id,
            status=StageStatus.IN_PROGRESS.value,
            notes="开始此阶段"
        )
        
        return result
    
    def complete_stage(self, order_id: str, stage_id: str, 
                      notes: str = "", photos: Optional[List] = None) -> Dict[str, Any]:
        """
        完成某个阶段
        
        校验：
        1. 该阶段必须是in_progress状态
        
        可选：
        - 上传照片和视频
        
        Args:
            order_id: 订单ID
            stage_id: 阶段ID
            notes: 备注
            photos: 照片/视频文件列表
            
        Returns:
            更新结果 + 照片/视频上传结果
        """
        # 先获取当前进度列表进行校验
        progress_result = self.get_progress(order_id)
        if not progress_result.get('success'):
            return progress_result
        
        progress_list = progress_result.get('data', [])
        
        # 使用状态机检查是否可以完成
        can_complete, reason = self.state_machine.can_complete_stage(progress_list, stage_id)
        if not can_complete:
            return {
                'success': False,
                'message': reason
            }
        
        # 调用API更新进度
        result = self.api_client.update_order_progress(
            order_id=order_id,
            stage_id=stage_id,
            status=StageStatus.COMPLETED.value,
            notes=notes
        )
        
        # 如果有照片，上传照片
        photo_result = None
        if photos and len(photos) > 0 and result.get('success'):
            from .photo_service import PhotoService
            photo_service = PhotoService(self.api_client)
            
            # 获取阶段名称
            stage_name = ""
            for p in progress_list:
                if p.get('stage_id') == stage_id:
                    stage_name = p.get('stage_name', '')
                    break
            
            photo_result = photo_service.upload_photos(
                order_id=order_id,
                stage_id=stage_id,
                stage_name=stage_name,
                photos=photos,
                description=f"{stage_name}完成媒体"
            )
        
        # 合并结果
        if photo_result:
            result['photo_upload'] = photo_result
        
        return result
    
    def get_next_stage(self, progress_list: List[Dict]) -> Optional[Dict]:
        """
        获取下一个待处理的阶段
        
        Args:
            progress_list: 进度记录列表
            
        Returns:
            下一个待处理的阶段，如果没有则返回None
        """
        sorted_progress = sorted(progress_list, key=lambda x: x.get('stage_order', 0))
        
        for progress in sorted_progress:
            if progress.get('status') == StageStatus.PENDING.value:
                return progress
        
        return None
    
    def get_current_stage(self, progress_list: List[Dict]) -> Optional[Dict]:
        """
        获取当前进行中的阶段
        
        Args:
            progress_list: 进度记录列表
            
        Returns:
            当前进行中的阶段，如果没有则返回None
        """
        for progress in progress_list:
            if progress.get('status') == StageStatus.IN_PROGRESS.value:
                return progress
        
        return None
    
    def get_completed_stages(self, progress_list: List[Dict]) -> List[Dict]:
        """
        获取所有已完成的阶段
        
        Args:
            progress_list: 进度记录列表
            
        Returns:
            已完成的阶段列表
        """
        return [p for p in progress_list if p.get('status') == StageStatus.COMPLETED.value]
    
    def format_progress_for_timeline(self, progress_list: List[Dict]) -> List[Dict]:
        """
        格式化进度数据用于时间轴显示
        
        Args:
            progress_list: 原始进度记录
            
        Returns:
            格式化后的进度数据
        """
        sorted_progress = sorted(progress_list, key=lambda x: x.get('stage_order', 0))
        
        formatted = []
        for progress in sorted_progress:
            formatted.append({
                'stage_id': progress.get('stage_id', ''),
                'stage_name': progress.get('stage_name', ''),
                'stage_order': progress.get('stage_order', 0),
                'status': progress.get('status', 'pending'),
                'status_display': {
                    'pending': '待处理',
                    'in_progress': '进行中',
                    'completed': '已完成'
                }.get(progress.get('status', 'pending'), '未知'),
                'started_at': progress.get('started_at'),
                'completed_at': progress.get('completed_at'),
                'notes': progress.get('notes', ''),
                'icon': {
                    'pending': '⏸️',
                    'in_progress': '🔄',
                    'completed': '✅'
                }.get(progress.get('status', 'pending'), '❓')
            })
        
        return formatted










