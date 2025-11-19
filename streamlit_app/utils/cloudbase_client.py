import streamlit as st
from typing import Dict, Any, Optional, List
import json
import os
import base64
from datetime import datetime
from config import CLOUDBASE_CONFIG, API_ENDPOINTS
from PIL import Image
import io

try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.scf.v20180416 import scf_client, models
    CLOUDBASE_SDK_AVAILABLE = True
except ImportError:
    CLOUDBASE_SDK_AVAILABLE = False

class CloudBaseClient:
    """CloudBase 云函数客户端"""

    def __init__(self):
        self.env_id = CLOUDBASE_CONFIG["env_id"]
        self.region = CLOUDBASE_CONFIG["region"]
    
    def _compress_image(self, file_content: bytes, filename: str, max_size_kb: int = 300, quality: int = 90) -> bytes:
        """压缩图片到指定大小"""
        try:
            # 打开图片
            image = Image.open(io.BytesIO(file_content))
            
            # 转换为RGB（如果是RGBA）
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # 计算压缩比例
            original_size = len(file_content)
            target_size = max_size_kb * 1024
            
            if original_size <= target_size:
                return file_content
            
            # 逐步压缩
            for q in range(quality, 40, -5):
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=q, optimize=True)
                compressed_size = len(buffer.getvalue())
                
                if compressed_size <= target_size:
                    print(f"✅ 图片压缩成功: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB (质量={q})")
                    return buffer.getvalue()
            
            # 如果还是太大，缩小尺寸
            width, height = image.size
            while True:
                width = int(width * 0.8)
                height = int(height * 0.8)
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                resized_image.save(buffer, format='JPEG', quality=80, optimize=True)
                compressed_size = len(buffer.getvalue())
                
                print(f"🔄 缩小尺寸: {width}x{height}, 大小: {compressed_size/1024:.1f}KB")
                
                if compressed_size <= target_size or width < 200:
                    print(f"✅ 图片压缩成功: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB (尺寸={width}x{height})")
                    return buffer.getvalue()
            
        except Exception as e:
            print(f"❌ 图片压缩失败: {str(e)}")
            return file_content

    def _call_function(self, function_name: str, data: Dict[str, Any] = None, is_admin: bool = False) -> Dict[str, Any]:
        """调用云函数"""
        try:
            # 使用HTTP请求调用云函数（支持is_admin参数）
            return self._call_with_http(function_name, data, is_admin)
        except Exception as e:
            print(f"❌ 云函数调用异常: {str(e)}")
            # 发生异常时返回错误信息
            return {"success": False, "message": f"云函数调用异常: {str(e)}"}

    def _call_with_http(self, function_name: str, data: Dict[str, Any] = None, is_admin: bool = False) -> Dict[str, Any]:
        """使用HTTP请求调用CloudBase云函数"""
        try:
            import requests
            
            # 构建CloudBase HTTP触发器URL
            base_url = CLOUDBASE_CONFIG["api_base_url"]
            
            # 使用正确的HTTP触发器路径
            http_paths = {
                "customer-search": "/api/customer/orders/search",
                "customer-detail": "/api/customer/orders/detail",
                "admin-auth": "/api/admin/auth",
                "admin-orders": "/api/admin/orders",
                "admin-progress": "/api/admin/progress",
                "admin-users": "/api/admin/users",
                "role-permissions": "/api/admin/role-permissions",
                "photo-upload": "/api/admin/photos/upload",
                "admin-dashboard": "/api/admin/dashboard",
                "admin-logs": "/api/admin/logs"
            }
            
            http_path = http_paths.get(function_name, f"/{function_name}")
            function_url = f"{base_url}{http_path}"
            
            # 准备请求数据
            request_data = data or {}
            
            # 检查请求数据大小
            import json
            request_json = json.dumps(request_data)
            request_size = len(request_json.encode('utf-8'))
            print(f"🌐 尝试调用云函数: {function_url}")
            print(f"📊 请求数据大小: {request_size} bytes ({request_size/1024:.1f}KB)")
            
            # 检查是否超过限制
            if request_size > 800 * 1024:  # 800KB限制
                print(f"⚠️ 请求数据过大: {request_size} bytes > 800KB")
                return {"success": False, "message": "请求数据过大，请减少文件大小"}
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "life-diamond-system/1.0"
            }
            
            # 如果是管理员调用，添加管理员标识
            if is_admin:
                headers["x-administrator"] = "true"
                headers["User-Agent"] = "life-diamond-system-admin/1.0"
            
            # 发送HTTP请求
            response = requests.post(
                function_url,
                json=request_data,
                headers=headers,
                timeout=10
            )
            
            print(f"📡 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                if response.text:
                    result = response.json()
                    print(f"✅ 云函数调用成功: {function_name}")
                    # 直接返回云函数的响应，保持success字段的原始值
                    return result
                else:
                    print("❌ 响应内容为空")
                    return {"success": False, "message": "响应内容为空"}
            else:
                print(f"❌ HTTP请求失败: {response.status_code} - {response.text}")
                return {"success": False, "message": f"HTTP请求失败: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ HTTP调用异常: {str(e)}")
            return {"success": False, "message": f"HTTP调用失败: {str(e)}"}

    # 客户查询接口
    def search_orders_by_name(self, customer_name: str) -> Dict[str, Any]:
        """根据客户姓名查询订单（兼容旧接口）"""
        return self.search_orders(search_type="name", search_value=customer_name)
    
    def search_orders(self, search_type: str = "name", search_value: str = "") -> Dict[str, Any]:
        """
        查询订单（支持多种查询方式）
        
        Args:
            search_type: 查询类型，可选值：name（姓名）、phone（电话）、email（邮箱）、order_number（订单号）
            search_value: 查询值
        """
        return self._call_function("customer-search", {
            "search_type": search_type,
            "search_value": search_value
        })

    def get_order_detail(self, order_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """获取订单详情"""
        return self._call_function("customer-detail", {"order_id": order_id}, is_admin=is_admin)

    # 管理员认证接口
    def admin_login(self, username: str, password: str) -> Dict[str, Any]:
        """管理员登录"""
        return self._call_function("admin-auth", {
            "username": username,
            "password": password
        })

    # 管理员订单管理接口
    def get_admin_orders(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取管理员订单列表"""
        return self._call_function("admin-orders", data)
    
    def get_orders(self, page: int = 1, limit: int = 20, status: str = "all", search: str = "") -> Dict[str, Any]:
        """获取订单列表（兼容接口）"""
        return self._call_function("admin-orders", {
            "action": "list",
            "page": page,
            "page_size": limit,  # 将limit映射到page_size
            "status": status,
            "search": search
        })

    def create_admin_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建订单"""
        return self._call_function("admin-orders", {
            "action": "create",
            "data": order_data
        })

    def update_admin_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新订单"""
        return self._call_function("admin-orders", {
            "action": "update",
            "data": {
                "order_id": order_id,
                **order_data
            }
        })

    def delete_admin_order(self, order_id: str) -> Dict[str, Any]:
        """删除订单"""
        return self._call_function("admin-orders", {
            "action": "delete",
            "data": {"order_id": order_id}
        })

    # 管理员进度管理接口
    def get_admin_progress(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取管理员进度列表"""
        return self._call_function("admin-progress", data)

    def update_admin_progress(self, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新进度"""
        return self._call_function("admin-progress", {
            "action": "update",
            "data": progress_data
        })

    def create_admin_progress(self, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建进度记录"""
        return self._call_function("admin-progress", {
            "action": "create",
            "data": progress_data
        })
    
    def update_order_progress(self, order_id: str, stage_id: str, status: str, notes: str = "", actual_completion: str = None) -> Dict[str, Any]:
        """更新订单进度（兼容接口）"""
        progress_data = {
            "order_id": order_id,
            "stage_id": stage_id,
            "status": status,
            "notes": notes
        }
        if actual_completion:
            progress_data["actual_completion"] = actual_completion
            
        return self._call_function("admin-progress", {
            "action": "update",
            "data": progress_data
        })

    # 管理员仪表板接口
    def get_admin_dashboard(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取管理员仪表板数据"""
        return self._call_function("admin-dashboard", data)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据（兼容接口）"""
        return self._call_function("admin-dashboard", {})
    
    def get_admin_users(self) -> Dict[str, Any]:
        """获取管理员用户列表（兼容接口）"""
        return self._call_function("admin-users", {})
    
    def create_admin_user(self, user_data: Dict[str, Any], password: str) -> Dict[str, Any]:
        """创建管理员用户（兼容接口）"""
        return self._call_function("admin-users", {
            "action": "create",
            "data": {
                **user_data,
                "password": password
            }
        })

    # 照片上传接口 - 直接上传到云存储
    def upload_photos(self, order_id: str, stage_id: str, files: List[Any], description: str = "") -> Dict[str, Any]:
        """上传照片和视频到云存储"""
        try:
            # 收集文件类型信息
            file_types = []
            for file in files:
                file_type = getattr(file, 'type', None) or 'image/jpeg'
                file_types.append(file_type)
            
            # 直接调用云函数获取上传URL
            result = self._call_function("photo-upload", {
                "action": "get_upload_url",
                "data": {
                    "order_id": order_id,
                    "stage_id": stage_id,
                    "file_count": len(files),
                    "file_types": file_types,  # 传递文件类型数组
                    "description": description
                }
            })
            
            if not result.get("success"):
                print(f"❌ 获取上传URL失败: {result.get('message', '未知错误')}")
                return result
            
            # 获取上传URL和文件信息
            upload_urls = result.get("data", {}).get("upload_urls", [])
            print(f"✅ 获取到 {len(upload_urls)} 个上传URL")
            
            if len(upload_urls) != len(files):
                print(f"❌ 上传URL数量不匹配: {len(upload_urls)} vs {len(files)}")
                return {"success": False, "message": "上传URL数量不匹配"}
            
            # 上传文件到云存储
            uploaded_files = []
            for i, file in enumerate(files):
                try:
                    upload_url = upload_urls[i]
                    file_content = file.getvalue()
                    
                    print(f"📤 开始上传文件 {i+1}/{len(files)}: {file.name}")
                    print(f"📊 原始文件大小: {len(file_content)} bytes ({len(file_content)/1024:.1f}KB)")

                    # 只支持COS预签名直传，不压缩，直接使用原图
                    print("🖼️ 使用COS预签名直传，原图上传，不压缩")
                    print(f"🔗 上传URL: {upload_url['upload_url']}")
                    
                    # 验证是否为预签名URL
                    upload_method = upload_url.get("uploadMethod", "")
                    storage_type = upload_url.get("storage_type", "")
                    upload_url_str = str(upload_url.get("upload_url", ""))
                    
                    is_presigned = (
                        upload_method == "presigned_put" 
                        or storage_type == "cos_presigned_put"
                        or "q-sign-algorithm=" in upload_url_str
                    )
                    
                    if not is_presigned:
                        print(f"❌ 错误：返回的上传方式不是预签名直传")
                        print(f"   uploadMethod: {upload_method}")
                        print(f"   storage_type: {storage_type}")
                        print(f"   upload_url: {upload_url_str[:100]}...")
                        return {"success": False, "message": "上传方式错误：只支持COS预签名直传，请检查云函数配置"}
                    
                    # 使用COS预签名直传方案 (PUT)，原图上传
                    print("☁️ 使用COS预签名直传方案 (PUT)，原图上传，不压缩")
                    # 直接向 COS 预签名 URL 发起 PUT
                    try:
                        import requests
                        from urllib.parse import urlparse
                        url_info = urlparse(upload_url["upload_url"])
                        
                        # 详细日志：检查URL路径
                        print(f"🔍 解析预签名URL:")
                        print(f"   - 完整URL: {upload_url['upload_url'][:150]}...")
                        print(f"   - URL路径: {url_info.path}")
                        print(f"   - URL查询参数: {url_info.query[:100]}...")
                        
                        # 检查预签名URL中是否包含host在签名中
                        # 如果q-header-list包含host，需要发送Host header
                        put_headers = {}
                        
                        # 依据文件类型设置 Content-Type
                        try:
                            content_type = getattr(file, 'type', None) or 'application/octet-stream'
                        except Exception:
                            content_type = 'application/octet-stream'
                        put_headers['Content-Type'] = content_type
                        
                        # Content-Length 必须与实体长度一致
                        try:
                            put_headers['Content-Length'] = str(len(file_content))
                        except Exception:
                            pass
                        
                        # 检查是否需要发送Host header
                        # 优先使用云函数返回的required_host值（签名时使用的host值）
                        # 如果没有，则从URL中解析
                        required_host = upload_url.get("required_host")
                        
                        if required_host:
                            # 使用云函数明确指定的host值，确保完全匹配
                            put_headers['host'] = required_host
                            print(f"   - ✅ 使用云函数指定的host header: {required_host}")
                        elif "q-header-list" in upload_url["upload_url"]:
                            # 解析q-header-list参数
                            import re
                            header_list_match = re.search(r'q-header-list=([^&]+)', upload_url["upload_url"])
                            if header_list_match:
                                header_list = header_list_match.group(1)
                                if 'host' in header_list.lower():
                                    # 需要发送host header（小写）
                                    # 使用URL中的域名，移除端口
                                    host_value = url_info.netloc
                                    if ':' in host_value and url_info.scheme == 'https':
                                        host, port = host_value.rsplit(':', 1)
                                        if port == '443':
                                            host_value = host
                                    
                                    put_headers['host'] = host_value
                                    print(f"   - ✅ q-header-list包含host，发送host header: {host_value}")
                                    print(f"   - ⚠️ 注意：如果签名失败，请检查host值是否与签名时完全一致")
                                else:
                                    print(f"   - q-header-list不包含host，不发送host header")
                            else:
                                print(f"   - 无法解析q-header-list，不发送host header")
                        else:
                            print(f"   - URL中无q-header-list参数，不发送host header")
                        
                        print(f"   - Content-Type: {put_headers.get('Content-Type')}")
                        print(f"   - Content-Length: {put_headers.get('Content-Length')}")
                        
                        # 使用requests直接PUT，使用原始文件字节，保持原图质量
                        print(f"📤 发送PUT请求到: {url_info.scheme}://{url_info.netloc}{url_info.path}")
                        response = requests.put(
                            upload_url["upload_url"],
                            # 使用原始文件字节，保持原图质量
                            data=file_content,
                            headers=put_headers,
                            timeout=60
                        )
                        print(f"📡 预签名PUT响应: {response.status_code}")
                        if response.status_code in [200, 201, 204]:
                            upload_success = True
                        else:
                            try:
                                error_text = response.text[:300] if response.text else "无响应内容"
                                print(f"🧪 预签名PUT响应体: {error_text}")
                            except Exception:
                                pass
                            upload_success = False
                            error_msg = f"上传失败 (HTTP {response.status_code})"
                    except Exception as e:
                        print(f"❌ 预签名PUT上传失败: {str(e)}")
                        upload_success = False
                        error_msg = f"上传异常: {str(e)}"
                    
                    if upload_success:
                        uploaded_files.append({
                            "file_id": upload_url.get("file_id", ""),
                            "file_name": file.name,
                            "file_size": file.size,
                            "file_type": file.type,
                            "photo_url": upload_url.get("photo_url", ""),
                            "thumbnail_url": upload_url.get("thumbnail_url", upload_url.get("photo_url", "")),
                            "storage_type": upload_url.get("storage_type", "cos_presigned_put"),
                            "cloud_path": upload_url.get("cloud_path", ""),
                            "fileID": upload_url.get("fileID", ""),  # CloudBase存储的fileID
                            "media_type": upload_url.get("media_type", "photo"),  # 'photo' 或 'video'
                            "file_extension": upload_url.get("file_extension", "")  # 文件扩展名
                        })
                        print(f"✅ 文件 {file.name} 上传成功")
                    else:
                        error_msg = f"上传失败"
                        if 'response' in locals() and response:
                            error_msg += f" (HTTP {response.status_code})"
                        print(f"❌ 文件 {file.name} {error_msg}")
                        
                except Exception as e:
                    print(f"❌ 上传文件 {file.name} 时出错: {str(e)}")
                    continue
            
            if not uploaded_files:
                return {"success": False, "message": "所有文件上传失败"}
            
            # 确认上传完成
            return self._call_function("photo-upload", {
                "action": "confirm_upload",
                "data": {
                    "order_id": order_id,
                    "stage_id": stage_id,
                    "uploaded_files": uploaded_files,
                    "description": description
                }
            })
            
        except Exception as e:
            print(f"❌ 照片上传异常: {str(e)}")
            return {"success": False, "message": f"照片上传失败: {str(e)}"}
    
    def delete_photo(self, photo_id: str, reason: str = "", delete_from_storage: bool = True) -> Dict[str, Any]:
        """删除照片或视频"""
        if not photo_id:
            return {"success": False, "message": "缺少照片ID"}
        
        operator = "admin"
        try:
            user_info = st.session_state.get("user_info") or {}
            operator = user_info.get("username") or user_info.get("real_name") or operator
        except Exception:
            pass
        
        return self._call_function("photo-upload", {
            "action": "delete",
            "data": {
                "photo_id": photo_id,
                "operator": operator,
                "reason": reason,
                "delete_from_storage": delete_from_storage
            }
        }, is_admin=True)

    # 创建订单（兼容接口）
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新订单"""
        return self._call_function("admin-orders", {
            "action": "create",
            "data": order_data
        })

    # 管理员用户管理接口
    def get_admin_users(self) -> Dict[str, Any]:
        """获取管理员用户列表（兼容接口）"""
        return self._call_function("admin-users", {
            "action": "list"
        })
    
    def create_admin_user(self, user_data: Dict[str, Any], password: str) -> Dict[str, Any]:
        """创建管理员用户（兼容接口）"""
        return self._call_function("admin-users", {
            "action": "create",
            "data": {
                **user_data,
                "password": password
            }
        })
    
    def update_admin_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新管理员用户"""
        return self._call_function("admin-users", {
            "action": "update",
            "data": {
                "user_id": user_id,
                **user_data
            }
        })
    
    def delete_admin_user(self, user_id: str) -> Dict[str, Any]:
        """删除管理员用户"""
        return self._call_function("admin-users", {
            "action": "delete",
            "data": {
                "user_id": user_id
            }
        })

    # 角色权限管理接口
    def get_roles(self) -> Dict[str, Any]:
        """获取角色列表"""
        return self._call_function("role-permissions", {
            "action": "list_roles"
        })
    
    def get_permissions(self) -> Dict[str, Any]:
        """获取权限列表"""
        return self._call_function("role-permissions", {
            "action": "list_permissions"
        })
    
    def get_role_permissions(self, role_id: str) -> Dict[str, Any]:
        """获取角色的权限"""
        return self._call_function("role-permissions", {
            "action": "get_role_permissions",
            "data": {
                "role_id": role_id
            }
        })
    
    def update_role_permissions(self, role_id: str, permission_ids: List[str], granted_by: str = "system") -> Dict[str, Any]:
        """更新角色权限"""
        return self._call_function("role-permissions", {
            "action": "update_role_permissions",
            "data": {
                "role_id": role_id,
                "permission_ids": permission_ids,
                "granted_by": granted_by
            }
        })
    
    def create_role(self, role_data: Dict[str, Any], created_by: str = "system") -> Dict[str, Any]:
        """创建角色"""
        return self._call_function("role-permissions", {
            "action": "create_role",
            "data": {
                **role_data,
                "created_by": created_by
            }
        })
    
    def init_default_role_data(self) -> Dict[str, Any]:
        """初始化默认角色权限数据"""
        return self._call_function("role-permissions", {
            "action": "init_default_data"
        })
    
    def update_permission_status(self, permission_id: str, is_active: bool) -> Dict[str, Any]:
        """更新权限状态"""
        return self._call_function("role-permissions", {
            "action": "update_permission",
            "permission_id": permission_id,
            "is_active": is_active
        })
    
    def get_operation_logs(self) -> Dict[str, Any]:
        """获取操作日志"""
        return self._call_function("admin-logs", {
            "action": "list"
        })

# 创建全局实例
api_client = CloudBaseClient()
