# 页面模块初始化文件

# 导入所有页面模块
from . import customer_query
from . import admin_dashboard
from . import admin_orders
from . import admin_progress
from . import admin_photos
from . import admin_users
from . import admin_role_permissions

__all__ = [
    'customer_query',
    'admin_dashboard', 
    'admin_orders',
    'admin_progress',
    'admin_photos',
    'admin_users',
    'admin_role_permissions'
]