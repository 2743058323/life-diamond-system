import os
from typing import Dict, Any

# CloudBase 配置
CLOUDBASE_CONFIG = {
    "env_id": os.getenv("CLOUDBASE_ENV_ID", "cloud1-7g7o4xi13c00cb90"),
    "region": os.getenv("CLOUDBASE_REGION", "ap-shanghai"),
    "api_base_url": os.getenv("API_BASE_URL", "https://cloud1-7g7o4xi13c00cb90.service.tcloudbase.com")
}

# API 接口配置 - 直接调用云函数
API_ENDPOINTS = {
    # 客户查询
    "customer_search": "customer-search",
    "customer_detail": "customer-detail",
    
    # 管理后台
    "admin_login": "admin-auth",
    "admin_orders": "admin-orders",
    "admin_progress": "admin-progress",
    "admin_users": "admin-users",
    "photo_upload": "photo-upload",
    "admin_dashboard": "admin-dashboard"
}

# 应用配置
APP_CONFIG = {
    "title": "生命钻石服务系统",
    "page_title": "生命钻石服务系统",
    "page_icon": "🔷",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        "Get Help": None,
        "Report a bug": None,
        "About": "生命钻石服务系统 v1.0"
    }
}

# 制作阶段配置 - 根据实际生命钻石制作流程
PRODUCTION_STAGES = [
    {
        "id": "stage_1",
        "name": "进入实验室",
        "description": "原料进入专业实验室，准备制作环境",
        "estimated_days": 1,
        "color": "#E8F4FD"
    },
    {
        "id": "stage_2",
        "name": "碳化提纯",
        "description": "对原料进行碳化处理和提纯工艺",
        "estimated_days": 2,
        "color": "#FFF4E6"
    },
    {
        "id": "stage_3",
        "name": "石墨化",
        "description": "钻石结构转换和石墨化处理",
        "estimated_days": 2,
        "color": "#FFF1F0"
    },
    {
        "id": "stage_4",
        "name": "高温高压培育生长",
        "description": "在高温高压环境下培育钻石生长",
        "estimated_days": 15,
        "color": "#F9F0FF"
    },
    {
        "id": "stage_5",
        "name": "钻胚提取",
        "description": "提取钻石毛胚，进行初步成型",
        "estimated_days": 3,
        "color": "#F6FFED"
    },
    {
        "id": "stage_6",
        "name": "切割",
        "description": "精密切割钻石，塑造最终形状",
        "estimated_days": 5,
        "color": "#E6F7FF"
    },
    {
        "id": "stage_7",
        "name": "认证溯源",
        "description": "钻石质量认证和溯源证书制作",
        "estimated_days": 3,
        "color": "#F0F9FF"
    },
    {
        "id": "stage_8",
        "name": "镶嵌钻石",
        "description": "将钻石镶嵌到指定位置，完成最终产品",
        "estimated_days": 4,
        "color": "#FEF7F0"
    }
]

# 默认管理员账户（仅用于文档说明）
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",  # 密码：admin123
    "role": "admin"
}

DEFAULT_OPERATOR = {
    "username": "operator",
    "password": "operator123",  # 密码：operator123
    "role": "operator"
}

# 状态映射
STATUS_MAPPING = {
    "pending": {
        "name": "待处理",
        "color": "#faad14",
        "icon": "⏳"
    },
    "in_progress": {
        "name": "进行中",
        "color": "#1890ff",
        "icon": "▶️"
    },
    "completed": {
        "name": "已完成",
        "color": "#52c41a",
        "icon": "✅"
    }
}

# 订单状态映射
ORDER_STATUS_MAPPING = {
    "待处理": {
        "color": "#faad14",
        "icon": "🗓️"
    },
    "制作中": {
        "color": "#1890ff",
        "icon": "🔧"
    },
    "已完成": {
        "color": "#52c41a",
        "icon": "✨"
    }
}