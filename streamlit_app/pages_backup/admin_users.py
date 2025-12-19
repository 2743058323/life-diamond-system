import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    show_error_message,
    show_success_message,
    format_datetime,
    translate_role
)
from datetime import datetime
from typing import Dict, Any
import hashlib

def _get_available_roles():
    """从角色管理模块获取可用角色列表，用于用户角色选择"""
    # 优先使用缓存，避免每次打开表单都请求一次
    if "available_roles_cache" in st.session_state:
        return st.session_state["available_roles_cache"]

    try:
        result = api_client.get_roles()
        if result.get("success"):
            roles = result.get("data", {}).get("roles", [])
            # 只取启用的角色，并且有 role_name 字段
            role_names = [
                r.get("role_name")
                for r in roles
                if r.get("is_active", True) and r.get("role_name")
            ]
            if role_names:
                st.session_state["available_roles_cache"] = role_names
                return role_names
    except Exception as e:
        # 如果加载失败，给一个兜底选项，并给出轻量提示
        st.warning(f"加载角色列表失败，将使用默认角色集：{e}")

    fallback = ["admin", "operator", "viewer"]
    st.session_state["available_roles_cache"] = fallback
    return fallback


def show_page():
    """用户管理页面"""
    # 权限检查
    if not auth_manager.require_permission("users.manage"):
        return
    
    st.title("👥 用户管理")
    st.markdown("管理系统管理员账户，包括创建和编辑")
    
    # 页面模式选择
    tab1, tab2 = st.tabs(["👤 用户列表", "➕ 新建用户"])
    
    with tab1:
        show_users_list()
        
        # 显示编辑用户表单
        if 'editing_user' in st.session_state:
            show_edit_user_form()
        
        # 如果有待确认的删除操作，显示取消按钮
        if any(key.startswith('delete_confirm_') for key in st.session_state.keys()):
            st.markdown("---")
            if st.button("🔄 取消所有删除操作", type="secondary"):
                # 清除所有删除确认状态
                for key in list(st.session_state.keys()):
                    if key.startswith('delete_confirm_'):
                        del st.session_state[key]
                st.rerun()
    
    with tab2:
        if auth_manager.has_permission("users.create"):
            show_create_user_form()
        else:
            st.error("您没有创建用户的权限")

def show_users_list():
    """显示用户列表"""
    st.markdown("### 管理员账户列表")
    
    # 加载用户数据
    if 'users_data' not in st.session_state or st.button("🔄 刷新", type="secondary"):
        load_users_data()
    
    if 'users_data' in st.session_state:
        users = st.session_state.users_data
        
        if users:
            # 创建用户数据表
            for i, user in enumerate(users):
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{user.get('real_name', 'N/A')}**")
                        st.caption(f"用户名: {user.get('username', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"**{translate_role(user.get('role', 'N/A'))}**")
                        st.caption(f"状态: {'🟢 活跃' if user.get('is_active', True) else '🔴 禁用'}")
                    
                    with col3:
                        st.caption(f"创建时间: {format_datetime(user.get('created_at', ''), 'date')}")
                        st.caption(f"最后登录: {format_datetime(user.get('last_login', ''), 'datetime')}")
                    
                    with col4:
                        col4_1, col4_2, col4_3 = st.columns(3)
                        
                        with col4_1:
                            if st.button("✏️", key=f"edit_user_{i}", help="编辑用户"):
                                st.session_state.editing_user = user
                                st.rerun()
                        
                        with col4_2:
                            # 状态切换按钮
                            if user.get('is_active', True):
                                if st.button("🔴", key=f"disable_user_{i}", help="禁用用户"):
                                    toggle_user_status(user['user_id'], False)
                            else:
                                if st.button("🟢", key=f"enable_user_{i}", help="启用用户"):
                                    toggle_user_status(user['user_id'], True)
                        
                        with col4_3:
                            # 删除按钮（只有非管理员或非最后一个管理员可以删除）
                            if user.get('role') != 'admin' or len([u for u in users if u.get('role') == 'admin']) > 1:
                                if st.button("🗑️", key=f"delete_user_{i}", help="删除用户"):
                                    st.session_state[f"delete_confirm_{user['user_id']}"] = True
                                    st.rerun()
                            else:
                                st.button("🔒", key=f"locked_user_{i}", help="不能删除最后一个管理员", disabled=True)
                    
                    # 显示删除确认区域（如果有待确认的删除）
                    if st.session_state.get(f"delete_confirm_{user['user_id']}", False):
                        st.warning(f"⚠️ 确定要删除用户 '{user.get('real_name', user.get('username'))}' 吗？")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✅ 确认删除", key=f"confirm_{user['user_id']}", type="primary"):
                                delete_user(user['user_id'])
                        with col_cancel:
                            if st.button("❌ 取消", key=f"cancel_{user['user_id']}", type="secondary"):
                                st.session_state[f"delete_confirm_{user['user_id']}"] = False
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("暂无用户数据")
    else:
        st.info("正在加载用户数据...")

def show_create_user_form():
    """显示创建用户表单"""
    st.markdown("### 创建新管理员账户")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "用户名 *",
                placeholder="输入用户名",
                help="用户名必须唯一，用于登录系统"
            )
            
            real_name = st.text_input(
                "真实姓名 *",
                placeholder="输入真实姓名",
                help="管理员的真实姓名"
            )
            
            email = st.text_input(
                "邮箱地址",
                placeholder="输入邮箱地址",
                help="用于接收系统通知"
            )
        
        with col2:
            password = st.text_input(
                "密码 *",
                type="password",
                placeholder="输入密码",
                help="密码长度至少6位"
            )
            
            confirm_password = st.text_input(
                "确认密码 *",
                type="password",
                placeholder="再次输入密码"
            )
            
            # 角色从角色管理模块动态加载，而不是写死三种
            role_options = _get_available_roles()
            default_role = "operator" if "operator" in role_options else (role_options[0] if role_options else None)
            default_index = role_options.index(default_role) if default_role else 0
            role = st.selectbox(
                "角色 *",
                options=role_options,
                index=default_index,
                format_func=translate_role,
                help="不同角色拥有不同的系统权限"
            )
        
        is_active = st.checkbox("启用账户", value=True, help="禁用的账户无法登录系统")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button("创建用户", type="primary")
        
        with col2:
            reset_button = st.form_submit_button("重置表单", type="secondary")
        
        if submit_button:
            create_user(username, real_name, email, password, confirm_password, role, is_active)
        
        if reset_button:
            st.rerun()

def load_users_data():
    """加载用户数据"""
    with st.spinner("正在加载用户数据..."):
        result = api_client.get_admin_users()
        
        if result.get("success"):
            # 处理嵌套的数据结构
            data = result.get("data", {})
            
            # 直接获取users数组
            if isinstance(data, dict) and "users" in data:
                st.session_state.users_data = data.get("users", [])
            elif isinstance(data, list):
                st.session_state.users_data = data
            else:
                st.session_state.users_data = []
        else:
            show_error_message(
                result.get("message", "用户数据加载失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def create_user(username, real_name, email, password, confirm_password, role, is_active):
    """创建用户"""
    # 验证输入
    if not username or not real_name or not password:
        st.error("请填写所有必填字段")
        return
    
    if len(password) < 6:
        st.error("密码长度至少6位")
        return
    
    if password != confirm_password:
        st.error("两次输入的密码不一致")
        return
    
    # 创建用户数据
    user_data = {
        "username": username,
        "real_name": real_name,
        "email": email,
        "role": role,
        "is_active": is_active,
        "created_at": datetime.now().isoformat(),
        "created_by": st.session_state.get("user_info", {}).get("username", "system")
    }
    
    with st.spinner("正在创建用户..."):
        result = api_client.create_admin_user(user_data, password)
        
        if result.get("success"):
            show_success_message("用户创建成功")
            # 清除缓存，重新加载用户列表
            if 'users_data' in st.session_state:
                del st.session_state.users_data
            st.rerun()
        else:
            show_error_message(
                result.get("message", "用户创建失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请检查输入信息是否正确"
            )

def show_edit_user_form():
    """显示编辑用户表单"""
    user = st.session_state.editing_user
    
    st.markdown("---")
    st.markdown("### ✏️ 编辑用户")
    
    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("用户名", value=user.get('username', ''), disabled=True, help="用户名不可修改")
            
            real_name = st.text_input(
                "真实姓名 *",
                value=user.get('real_name', ''),
                help="管理员的真实姓名"
            )
            
            email = st.text_input(
                "邮箱地址",
                value=user.get('email', ''),
                help="用于接收系统通知"
            )
        
        with col2:
            # 编辑时的角色列表同样从角色管理模块动态获取
            role_options = _get_available_roles()
            current_role = user.get('role', 'operator')
            if current_role not in role_options and current_role:
                # 确保当前用户原有角色也能被选到
                role_options = [current_role] + [r for r in role_options if r != current_role]
            default_index = role_options.index(current_role) if current_role in role_options else 0
            role = st.selectbox(
                "角色 *",
                options=role_options,
                index=default_index,
                format_func=translate_role,
                help="不同角色拥有不同的系统权限"
            )
            
            is_active = st.checkbox(
                "启用账户", 
                value=user.get('is_active', True),
                help="禁用的账户无法登录系统"
            )
            
            new_password = st.text_input(
                "新密码",
                type="password",
                placeholder="留空表示不修改密码",
                help="输入新密码以修改密码"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button("保存修改", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("取消", type="secondary")
        
        if submit_button:
            update_user_data = {
                "real_name": real_name,
                "email": email,
                "role": role,
                "is_active": is_active
            }
            
            if new_password:
                update_user_data["password"] = new_password
            
            update_user(user['user_id'], update_user_data)
        
        if cancel_button:
            if 'editing_user' in st.session_state:
                del st.session_state.editing_user
            st.rerun()

def update_user(user_id: str, user_data: Dict[str, Any]):
    """更新用户"""
    with st.spinner("正在更新用户..."):
        result = api_client.update_admin_user(user_id, user_data)
        
        if result.get("success"):
            show_success_message("用户更新成功")
            # 清除缓存和编辑状态
            if 'users_data' in st.session_state:
                del st.session_state.users_data
            if 'editing_user' in st.session_state:
                del st.session_state.editing_user
            st.rerun()
        else:
            show_error_message(
                result.get("message", "用户更新失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请检查输入信息是否正确"
            )

def toggle_user_status(user_id: str, is_active: bool):
    """切换用户状态"""
    status_text = "启用" if is_active else "禁用"
    
    with st.spinner(f"正在{status_text}用户..."):
        result = api_client.update_admin_user(user_id, {"is_active": is_active})
        
        if result.get("success"):
            show_success_message(f"用户{status_text}成功")
            # 清除缓存
            if 'users_data' in st.session_state:
                del st.session_state.users_data
            st.rerun()
        else:
            show_error_message(
                result.get("message", f"用户{status_text}失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def delete_user(user_id: str):
    """删除用户"""
    with st.spinner("正在删除用户..."):
        result = api_client.delete_admin_user(user_id)
        
        if result.get("success"):
            show_success_message("用户删除成功")
            # 清除缓存和确认状态
            if 'users_data' in st.session_state:
                del st.session_state.users_data
            # 清除所有确认删除状态
            for key in list(st.session_state.keys()):
                if key.startswith('delete_confirm_'):
                    del st.session_state[key]
            st.rerun()
        else:
            show_error_message(
                result.get("message", "用户删除失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )
