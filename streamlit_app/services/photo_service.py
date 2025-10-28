"""
照片服务

处理照片上传和管理的业务逻辑
"""

from typing import Dict, List, Optional, Any


class PhotoService:
    """照片业务逻辑服务"""
    
    def __init__(self, api_client):
        """
        初始化照片服务
        
        Args:
            api_client: CloudBase API客户端实例
        """
        self.api_client = api_client
    
    def upload_photos(self, order_id: str, stage_id: str, stage_name: str,
                     photos: List, description: str = "") -> Dict[str, Any]:
        """
        上传照片
        
        Args:
            order_id: 订单ID
            stage_id: 阶段ID
            stage_name: 阶段名称
            photos: 照片文件列表
            description: 照片描述
            
        Returns:
            上传结果
        """
        if not photos or len(photos) == 0:
            return {
                'success': False,
                'message': '没有选择照片'
            }
        
        # CloudBase 客户端期望的参数为 files（不支持 stage_name 关键字）
        result = self.api_client.upload_photos(
            order_id=order_id,
            stage_id=stage_id,
            files=photos,
            description=description
        )
        
        return result
    
    def get_photos(self, order_id: str, stage_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取照片列表
        
        Args:
            order_id: 订单ID
            stage_id: 阶段ID（可选，不传则获取所有照片）
            
        Returns:
            照片列表
        """
        # 通过订单详情获取照片
        result = self.api_client.get_order_detail(order_id, is_admin=True)
        
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        photos = data.get('photos', [])
        
        # 如果指定了stage_id，过滤照片
        if stage_id:
            filtered_photos = []
            for photo_group in photos:
                if photo_group.get('stage_id') == stage_id:
                    filtered_photos = photo_group.get('photos', [])
                    break
            
            return {
                'success': True,
                'data': filtered_photos
            }
        
        return {
            'success': True,
            'data': photos
        }
    
    def delete_photo(self, photo_id: str) -> Dict[str, Any]:
        """
        删除照片
        
        Args:
            photo_id: 照片ID
            
        Returns:
            删除结果
        """
        # TODO: 实现照片删除API
        return {
            'success': False,
            'message': '照片删除功能待实现'
        }
    
    def group_photos_by_stage(self, photos_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        按阶段分组照片
        
        Args:
            photos_data: 照片数据（包含stage_name和photos列表）
            
        Returns:
            按阶段分组的照片字典 {stage_name: [photo1, photo2, ...]}
        """
        grouped = {}
        
        for photo_group in photos_data:
            stage_name = photo_group.get('stage_name', '未知阶段')
            photos = photo_group.get('photos', [])
            grouped[stage_name] = photos
        
        return grouped
    
    def get_photo_count(self, photos_data: List[Dict]) -> int:
        """
        获取照片总数
        
        Args:
            photos_data: 照片数据
            
        Returns:
            照片总数
        """
        total = 0
        for photo_group in photos_data:
            photos = photo_group.get('photos', [])
            total += len(photos)
        
        return total
    
    def validate_photo_files(self, photos: List) -> tuple[bool, str]:
        """
        验证照片文件
        
        Args:
            photos: 照片文件列表
            
        Returns:
            (is_valid, error_message)
        """
        if not photos or len(photos) == 0:
            return False, "请选择至少一张照片"
        
        # 检查文件大小（最大5MB）
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        
        for i, photo in enumerate(photos):
            if hasattr(photo, 'size') and photo.size > MAX_SIZE:
                return False, f"照片 {i+1} 超过5MB大小限制"
        
        # 检查文件类型
        ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
        
        for i, photo in enumerate(photos):
            if hasattr(photo, 'type') and photo.type not in ALLOWED_TYPES:
                return False, f"照片 {i+1} 格式不支持（仅支持JPG、PNG）"
        
        return True, ""










