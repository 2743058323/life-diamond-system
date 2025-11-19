"""
订单状态机

定义订单和阶段的状态转换规则
"""

from typing import Dict, List, Optional
from enum import Enum


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "待处理"
    IN_PROGRESS = "制作中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class StageStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class OrderStateMachine:
    """订单状态机"""
    
    # 订单状态转换规则
    ORDER_TRANSITIONS = {
        OrderStatus.PENDING: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
        OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
        OrderStatus.COMPLETED: [],  # 终态
        OrderStatus.CANCELLED: []   # 终态
    }
    
    # 阶段状态转换规则
    STAGE_TRANSITIONS = {
        StageStatus.PENDING: [StageStatus.IN_PROGRESS],
        StageStatus.IN_PROGRESS: [StageStatus.COMPLETED],
        StageStatus.COMPLETED: []  # 终态，不可回退
    }
    
    @classmethod
    def can_transition_order(cls, from_status: str, to_status: str) -> bool:
        """检查订单状态是否可以转换"""
        try:
            from_state = OrderStatus(from_status)
            to_state = OrderStatus(to_status)
            return to_state in cls.ORDER_TRANSITIONS.get(from_state, [])
        except ValueError:
            return False
    
    @classmethod
    def can_transition_stage(cls, from_status: str, to_status: str) -> bool:
        """检查阶段状态是否可以转换"""
        try:
            from_state = StageStatus(from_status)
            to_state = StageStatus(to_status)
            return to_state in cls.STAGE_TRANSITIONS.get(from_state, [])
        except ValueError:
            return False
    
    @classmethod
    def can_start_stage(cls, progress_list: List[Dict], stage_id: str) -> tuple[bool, str]:
        """
        检查是否可以开始某个阶段
        
        Returns:
            (can_start, reason) - (是否可以开始, 原因)
        """
        # 按阶段顺序排序
        sorted_progress = sorted(progress_list, key=lambda x: x.get('stage_order', 0))
        
        # 找到目标阶段
        target_stage = None
        target_index = -1
        for i, progress in enumerate(sorted_progress):
            if progress.get('stage_id') == stage_id:
                target_stage = progress
                target_index = i
                break
        
        if not target_stage:
            return False, "未找到指定阶段"
        
        # 检查当前状态
        current_status = target_stage.get('status')
        if current_status == StageStatus.IN_PROGRESS.value:
            return False, "该阶段已经在进行中"
        elif current_status == StageStatus.COMPLETED.value:
            return False, "该阶段已完成，无法重新开始"
        
        # 检查是否有其他阶段在进行中
        in_progress_stages = [p for p in sorted_progress if p.get('status') == StageStatus.IN_PROGRESS.value]
        if in_progress_stages:
            return False, f"请先完成进行中的阶段：{in_progress_stages[0].get('stage_name')}"
        
        # 检查前一阶段是否已完成
        if target_index > 0:
            previous_stage = sorted_progress[target_index - 1]
            if previous_stage.get('status') != StageStatus.COMPLETED.value:
                return False, f"请先完成前一阶段：{previous_stage.get('stage_name')}"
        
        return True, "可以开始"
    
    @classmethod
    def can_complete_stage(cls, progress_list: List[Dict], stage_id: str) -> tuple[bool, str]:
        """
        检查是否可以完成某个阶段
        
        Returns:
            (can_complete, reason)
        """
        # 找到目标阶段
        target_stage = None
        for progress in progress_list:
            if progress.get('stage_id') == stage_id:
                target_stage = progress
                break
        
        if not target_stage:
            return False, "未找到指定阶段"
        
        current_status = target_stage.get('status')
        if current_status != StageStatus.IN_PROGRESS.value:
            return False, "只能完成进行中的阶段"
        
        return True, "可以完成"
    
    @classmethod
    def calculate_progress(cls, progress_list: List[Dict]) -> int:
        """
        计算订单整体进度百分比
        
        Returns:
            progress_percentage (0-100)
        """
        if not progress_list:
            return 0
        
        total_stages = len(progress_list)
        completed_stages = sum(1 for p in progress_list if p.get('status') == StageStatus.COMPLETED.value)
        
        return int((completed_stages / total_stages) * 100)
    
    @classmethod
    def get_current_stage_name(cls, progress_list: List[Dict]) -> str:
        """获取当前阶段名称"""
        if not progress_list:
            return "未开始"
        
        sorted_progress = sorted(progress_list, key=lambda x: x.get('stage_order', 0))
        
        # 查找进行中的阶段
        for progress in sorted_progress:
            if progress.get('status') == StageStatus.IN_PROGRESS.value:
                return progress.get('stage_name', '未知')
        
        # 查找最后一个已完成的阶段
        completed_stages = [p for p in sorted_progress if p.get('status') == StageStatus.COMPLETED.value]
        if completed_stages:
            last_completed = completed_stages[-1]
            # 如果是最后一个阶段，返回"已完成"
            if last_completed == sorted_progress[-1]:
                return "已完成"
            # 否则返回下一个待处理的阶段
            next_index = sorted_progress.index(last_completed) + 1
            if next_index < len(sorted_progress):
                return sorted_progress[next_index].get('stage_name', '未知')
        
        # 都没有开始，返回第一个阶段
        return sorted_progress[0].get('stage_name', '未开始')
    
    @classmethod
    def auto_update_order_status(cls, progress_list: List[Dict]) -> str:
        """根据进度自动更新订单状态"""
        if not progress_list:
            return OrderStatus.PENDING.value
        
        # 检查是否所有阶段都完成
        all_completed = all(p.get('status') == StageStatus.COMPLETED.value for p in progress_list)
        if all_completed:
            return OrderStatus.COMPLETED.value
        
        # 检查是否有阶段在进行或已完成
        has_progress = any(p.get('status') in [StageStatus.IN_PROGRESS.value, StageStatus.COMPLETED.value] 
                          for p in progress_list)
        if has_progress:
            return OrderStatus.IN_PROGRESS.value
        
        return OrderStatus.PENDING.value
    
    @classmethod
    def get_allowed_actions(cls, order: Dict, progress_list: List[Dict]) -> List[str]:
        """
        获取订单允许的操作
        
        Returns:
            List of action names: ['edit', 'start_stage', 'complete_stage', 'upload_photo', ...]
        """
        actions = []
        order_status = order.get('order_status')
        
        # 基本操作
        if order_status != OrderStatus.COMPLETED.value:
            actions.append('edit_info')  # 编辑基本信息
        
        if order_status == OrderStatus.PENDING.value:
            actions.append('start_stage')  # 开始阶段
            actions.append('cancel_order')  # 取消订单
        
        if order_status == OrderStatus.IN_PROGRESS.value:
            # 查找进行中的阶段
            in_progress_stage = next((p for p in progress_list if p.get('status') == StageStatus.IN_PROGRESS.value), None)
            if in_progress_stage:
                actions.append('complete_stage')  # 完成当前阶段
            # 还有待处理的阶段也可以开始
            if any(p.get('status') == StageStatus.PENDING.value for p in progress_list):
                actions.append('start_stage')  # 开始下一个阶段
            actions.append('cancel_order')  # 取消订单
        
        # 照片/视频管理权限：有进度即可上传/删除
        if progress_list and any(p.get('status') in [StageStatus.IN_PROGRESS.value, StageStatus.COMPLETED.value] for p in progress_list):
            actions.append('upload_photo')  # 上传照片/视频
            actions.append('delete_photo')  # 删除照片/视频
        
        if order_status == OrderStatus.COMPLETED.value:
            actions.append('view_details')  # 查看详情
            actions.append('send_notification')  # 发送通知
            actions.append('print_order')  # 打印订单
        
        # 软删除（适用于所有状态）
        if not order.get('is_deleted'):
            actions.append('delete')
        
        return actions










