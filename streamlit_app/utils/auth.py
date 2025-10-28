import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from utils.cloudbase_client import api_client
from utils.helpers import translate_role

class AuthManager:
    """身份验证管理器"""
    
    def __init__(self):
        self.session_timeout = 24  # 24小时
    
    def show_login_form(self):
        """显示登录表单"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #8B4B8C; margin-bottom: 0.5rem;">🔷 生命钻石服务系统</h1>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">管理后台登录</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 创建居中的登录表单
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form", clear_on_submit=False):
                st.markdown("#### 请输入登录信息")
                
                username = st.text_input(
                    "用户名",
                    placeholder="请输入用户名",
                    help="默认管理员账户：admin"
                )
                
                password = st.text_input(
                    "密码",
                    type="password",
                    placeholder="请输入密码",
                    help="默认密码：admin123"
                )
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    login_button = st.form_submit_button(
                        "登录", 
                        type="primary"
                    )
                
                with col_b:
                    if st.form_submit_button("忘记密码？"):
                        st.info("请联系系统管理员重置密码")
                
                if login_button:
                    if username and password:
                        with st.spinner("登录中..."):
                            success, result = self.login(username, password)
                            if success:
                                st.success("登录成功")
                                st.rerun()
                            else:
                                # 根据错误类型显示不同的样式
                                if "账户已被禁用" in result:
                                    st.error(f"🚫 {result}")
                                elif "用户名或密码错误" in result:
                                    st.error(f"❌ {result}")
                                else:
                                    st.error(f"登录失败：{result}")
                    else:
                        st.warning("请填写用户名和密码")
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        """执行登录"""
        try:
            result = api_client.admin_login(username, password)
            
            # 检查result是否为None
            if result is None:
                return False, "服务器无响应"
            
            # 检查result是否为字典
            if not isinstance(result, dict):
                return False, f"服务器返回格式错误: {type(result)}"
            
            if result.get("success"):
                data = result.get("data")
                
                # 检查data是否为None
                if data is None:
                    return False, "服务器返回数据为空"
                
                # 处理嵌套的数据结构 - 检查内层success
                if isinstance(data, dict) and 'success' in data:
                    # 如果内层success为False，返回内层的错误信息
                    if not data.get('success'):
                        return False, data.get('message', '登录失败')
                    actual_data = data.get('data')
                else:
                    actual_data = data
                
                # 检查actual_data是否为None
                if actual_data is None:
                    return False, "登录数据为空"
                
                # 保存登录信息到session_state
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = actual_data.get("user", {})
                st.session_state["access_token"] = actual_data.get("token", "")
                st.session_state["login_time"] = datetime.now()
                st.session_state["expires_in"] = 86400  # 24小时
                return True, "登录成功"
            else:
                # 检查是否是账户被禁用的错误
                error_code = result.get("error_code")
                if error_code == "ACCOUNT_DISABLED":
                    return False, "账户已被禁用，请联系管理员"
                else:
                    return False, result.get("message", "登录失败")
                
        except Exception as e:
            return False, f"网络错误：{str(e)}"
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        if not st.session_state.get("authenticated", False):
            return False
        
        # 检查Token是否过期
        login_time = st.session_state.get("login_time")
        expires_in = st.session_state.get("expires_in", 0)
        
        if login_time and expires_in:
            if datetime.now() > login_time + timedelta(seconds=expires_in):
                self.logout()
                return False
        
        return True
    
    def logout(self):
        """退出登录"""
        keys_to_remove = [
            "authenticated", "user_info", "access_token", 
            "login_time", "expires_in"
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return st.session_state.get("user_info", {})
    
    def get_token(self) -> str:
        """获取当前Token"""
        return st.session_state.get("access_token", "")
    
    def has_permission(self, permission: str) -> bool:
        """检查用户权限"""
        user_info = self.get_user_info()
        user_role = user_info.get("role", "")
        
        # 尝试从数据库获取权限，如果失败则使用硬编码权限作为后备
        try:
            from utils.cloudbase_client import api_client
            
            # 获取角色权限
            roles_result = api_client.get_roles()
            if roles_result.get('success'):
                roles = roles_result.get('data', {}).get('roles', [])
                
                # 找到当前用户的角色
                current_role = None
                for role in roles:
                    if role.get('role_name') == user_role:
                        current_role = role
                        break
                
                if current_role:
                    # 获取角色的权限
                    role_permissions_result = api_client.get_role_permissions(current_role.get('_id'))
                    if role_permissions_result.get('success'):
                        permissions = role_permissions_result.get('data', {}).get('permissions', [])
                        permission_codes = [p.get('permission_code') for p in permissions]
                        return permission in permission_codes
        except Exception as e:
            print(f"从数据库获取权限失败，使用硬编码权限: {str(e)}")
        
        # 硬编码权限作为后备方案
        role_permissions = {
            "admin": [
                "dashboard.view", "orders.read", "orders.create", "orders.update", "orders.delete", 
                "progress.update", "photos.upload", "photos.manage", "users.manage", "users.create", "system.settings"
            ],
            "operator": [
                "dashboard.view", "orders.read", "orders.create", "orders.update", 
                "progress.update", "photos.upload", "photos.manage"
            ],
            "viewer": [
                "dashboard.view", "orders.read", "photos.upload"
            ]
        }
        
        if user_role in role_permissions:
            return permission in role_permissions[user_role]
        
        return False
    
    def show_user_info(self):
        """显示用户信息栏"""
        if self.is_authenticated():
            user_info = self.get_user_info()
            
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👤 当前用户")
            
            # 用户信息卡片
            st.sidebar.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
                color: white;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            ">
                <div style="font-weight: bold; font-size: 1.1rem;">{user_info.get('real_name', '')}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">角色：{translate_role(user_info.get('role', ''))}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">用户名：{user_info.get('username', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 退出按钮
            if st.sidebar.button("退出登录", width='stretch', type="secondary"):
                self.logout()
                st.rerun()
    
    def require_permission(self, permission: str) -> bool:
        """权限检查装饰器"""
        if not self.is_authenticated():
            self.show_login_form()
            return False
        
        if not self.has_permission(permission):
            st.error("权限不足，无法访问此功能")
            return False
        
        return True

# 全局认证管理器实例
auth_manager = AuthManager()