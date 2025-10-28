import requests
import streamlit as st
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from config import CLOUDBASE_CONFIG, API_ENDPOINTS

# 注意：这个文件已被 cloudbase_client.py 替代
# 保留此文件是为了向后兼容，但实际使用的是 cloudbase_client.py

class APIClient:
    """CloudBase API 客户端"""
    
    def __init__(self):
        self.base_url = CLOUDBASE_CONFIG["api_base_url"]
        self.timeout = 30
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {
            "Content-Type": "application/json"
        }
        
        if headers:
            request_headers.update(headers)
        
        # 添加认证Token
        if "access_token" in st.session_state:
            request_headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, 
                    params=params, 
                    headers=request_headers, 
                    timeout=self.timeout
                )
            elif method.upper() == "POST":
                if files:
                    # 文件上传请求
                    response = requests.post(
                        url, 
                        data=data, 
                        files=files, 
                        headers={k: v for k, v in request_headers.items() if k != "Content-Type"}, 
                        timeout=self.timeout
                    )
                else:
                    response = requests.post(
                        url, 
                        json=data, 
                        headers=request_headers, 
                        timeout=self.timeout
                    )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, 
                    json=data, 
                    headers=request_headers, 
                    timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, 
                    headers=request_headers, 
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 解析响应
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                return {
                    "success": False,
                    "message": error_msg,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "网络连接失败，请检查网络状态"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "请求超时，请稍后重试"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"系统错误: {str(e)}"
            }
    
    # 客户查询接口
    def search_orders_by_name(self, customer_name: str) -> Dict[str, Any]:
        """根据客户姓名查询订单"""
        return self._make_request(
            "GET", 
            API_ENDPOINTS["customer_search"],
            params={"name": customer_name}
        )
    
    def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情"""
        endpoint = API_ENDPOINTS["customer_detail"].replace("{order_id}", order_id)
        return self._make_request("GET", endpoint)
    
    # 管理员认证接口
    def admin_login(self, username: str, password: str) -> Dict[str, Any]:
        """管理员登录"""
        return self._make_request(
            "POST",
            API_ENDPOINTS["admin_login"],
            data={
                "username": username,
                "password": password
            }
        )
    
    # 订单管理接口
    def get_orders(
        self, 
        page: int = 1, 
        limit: int = 20, 
        status: str = "all", 
        search: str = ""
    ) -> Dict[str, Any]:
        """获取订单列表"""
        return self._make_request(
            "GET",
            API_ENDPOINTS["admin_orders"],
            params={
                "page": page,
                "limit": limit,
                "status": status,
                "search": search
            }
        )
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新订单"""
        return self._make_request(
            "POST",
            API_ENDPOINTS["admin_orders"],
            data=order_data
        )
    
    # 进度管理接口
    def update_order_progress(
        self, 
        order_id: str, 
        stage_id: str, 
        status: str, 
        notes: str = "",
        actual_completion: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新订单进度"""
        endpoint = API_ENDPOINTS["admin_progress"].replace("{order_id}", order_id)
        data = {
            "stage_id": stage_id,
            "status": status,
            "notes": notes
        }
        if actual_completion:
            data["actual_completion"] = actual_completion
        
        return self._make_request("PUT", endpoint, data=data)
    
    # 照片管理接口
    def upload_photos(
        self, 
        order_id: str, 
        stage_id: str, 
        files: List[Any], 
        description: str = ""
    ) -> Dict[str, Any]:
        """上传照片"""
        import base64
        
        # 处理文件上传
        file_data = []
        for file in files:
            try:
                # 读取文件内容并转换为Base64
                file_content = file.getvalue()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                
                file_data.append({
                    "name": file.name,
                    "type": file.type,
                    "size": file.size,
                    "content": file_base64  # 使用Base64格式
                })
            except Exception as e:
                print(f"处理文件 {file.name} 时出错: {str(e)}")
                # 如果处理失败，跳过这个文件
                continue
        
        return self._make_request(
            "POST",
            API_ENDPOINTS["photo_upload"],
            data={
                "order_id": order_id,
                "stage_id": stage_id,
                "files": file_data,
                "description": description
            }
        )
    
    def get_photos(
        self, 
        order_id: Optional[str] = None, 
        stage_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取照片列表"""
        params = {}
        if order_id:
            params["order_id"] = order_id
        if stage_id:
            params["stage_id"] = stage_id
        
        return self._make_request(
            "GET",
            API_ENDPOINTS["photo_upload"],
            params=params
        )
    
    # 仪表板接口
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return self._make_request(
            "GET",
            API_ENDPOINTS["admin_dashboard"]
        )

# 全局API客户端实例
api_client = APIClient()