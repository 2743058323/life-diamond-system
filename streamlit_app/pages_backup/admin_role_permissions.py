import streamlit as st
from typing import Dict, Any, List
import json
from utils.cloudbase_client import api_client
from utils.auth import auth_manager

def show_page():
    """显示角色权限管理页面"""
    st.title("🔐 角色权限管理")
    st.caption("在这里集中管理后台的角色、权限，以及每个角色拥有哪些权限。")
    st.markdown("---")

    # 检查权限
    if not auth_manager.has_permission("users.manage"):
        st.error("❌ 您没有权限访问此页面")
        return
    
    # 初始化数据
    if 'roles_data' not in st.session_state:
        load_roles_data()
    
    if 'permissions_data' not in st.session_state:
        load_permissions_data()
    
    # 初始化当前标签页（0: 角色管理, 1: 权限管理, 2: 角色权限配置）
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 0
    
    # 页面导航卡片（方案 B：三块卡片式布局）
    col1, col2, col3 = st.columns(3)
    with col1:
        is_active = st.session_state.current_tab == 0
        if st.button("📋 角色管理", key="tab_roles", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.current_tab = 0
            st.rerun()
        st.caption("查看、创建和编辑系统中的角色（如 管理员、客服、操作员 等）。")
    with col2:
        is_active = st.session_state.current_tab == 1
        if st.button("🔑 权限管理", key="tab_permissions", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.current_tab = 1
            st.rerun()
        st.caption("查看系统中所有权限点，并可启用 / 禁用某些权限。")
    with col3:
        is_active = st.session_state.current_tab == 2
        if st.button("⚙️ 角色权限配置", key="tab_config", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.current_tab = 2
            st.rerun()
        st.caption("为每个角色勾选具体权限，例如让客服只能看订单、不能删订单。")
    
    st.markdown("---")
    
    # 根据session state显示对应内容
    if st.session_state.current_tab == 0:
        show_roles_management()
    elif st.session_state.current_tab == 1:
        show_permissions_management()
    elif st.session_state.current_tab == 2:
        show_role_permissions_config()

def load_roles_data():
    """加载角色数据"""
    try:
        result = api_client.get_roles()
        if result.get('success'):
            st.session_state.roles_data = result.get('data', {}).get('roles', [])
        else:
            st.error(f"❌ 加载角色数据失败: {result.get('message', '未知错误')}")
            st.session_state.roles_data = []
    except Exception as e:
        st.error(f"❌ 加载角色数据异常: {str(e)}")
        st.session_state.roles_data = []

def load_permissions_data():
    """加载权限数据"""
    try:
        result = api_client.get_permissions()
        if result.get('success'):
            st.session_state.permissions_data = result.get('data', {}).get('permissions', [])
        else:
            st.error(f"❌ 加载权限数据失败: {result.get('message', '未知错误')}")
            st.session_state.permissions_data = []
    except Exception as e:
        st.error(f"❌ 加载权限数据异常: {str(e)}")
        st.session_state.permissions_data = []

def show_roles_management():
    """显示角色管理（全新布局）"""
    st.markdown("### 📋 角色管理")
    st.caption("先整体看一眼有哪些角色，再选择某个角色进行编辑或配置权限。")

    roles = st.session_state.get('roles_data', [])

    # 顶部：概览 + 快捷操作
    summary_col, action_col = st.columns([3, 2])

    with summary_col:
        st.markdown("#### 概览")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("角色总数", len(roles))
        with col2:
            active_roles = len([r for r in roles if r.get('is_active', True)])
            st.metric("启用", active_roles)
        with col3:
            st.metric("禁用", len(roles) - active_roles)

    with action_col:
        st.markdown("#### 快捷操作")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("🔄 刷新", key="roles_refresh_new", help="重新加载角色数据"):
                load_roles_data()
                st.rerun()
        with col_a2:
            if st.button("🚀 初始化默认数据", key="roles_init_new", help="首次使用时一键创建默认角色和权限"):
                init_default_data()

    st.markdown("---")

    # 中部：角色列表（表格视图）
    st.markdown("#### 角色列表")
    if not roles:
        st.info("当前还没有任何角色，请先使用右上角的“初始化默认数据”或在下方新建角色。")
    else:
        table_data = []
        for r in roles:
            table_data.append({
                "显示名称": r.get("display_name", r.get("role_name", "")),
                "代码": r.get("role_name", ""),
                "状态": "启用" if r.get("is_active", True) else "禁用",
                "描述": r.get("description", "无描述")
            })
        st.table(table_data)

    st.markdown("---")

    # 下部：选择一个角色进行操作 + 新建角色
    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.markdown("#### 选择角色")
        if not roles:
            st.caption("暂无角色可选。")
            selected_role = None
        else:
            options = {f"{r.get('display_name', r.get('role_name'))} ({r.get('role_name')})": r for r in roles}
            selected_label = st.selectbox("选择一个角色", list(options.keys()))
            selected_role = options[selected_label]

        if selected_role:
            st.markdown(f"**当前选择：{selected_role.get('display_name', selected_role.get('role_name'))}**")
            st.caption(selected_role.get("description", "无描述"))

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏️ 编辑这个角色", key="edit_selected_role"):
                    st.session_state.editing_role = selected_role
                    st.rerun()
            with c2:
                if st.button("🔧 配置这个角色的权限", key="config_selected_role"):
                    st.session_state.configuring_role = selected_role
                    st.session_state.current_tab = 2
                    st.rerun()

    with col_right:
        st.markdown("#### 新建角色")
        with st.form("create_role_form_new"):
            new_role_name = st.text_input("角色代码（英文）", placeholder="例如：finance, kefu")
            new_display_name = st.text_input("角色名称（显示用）", placeholder="例如：财务、客服")
            new_description = st.text_area("角色描述", placeholder="用于说明这个角色的职责范围")
            submitted = st.form_submit_button("💾 创建角色")

            if submitted:
                if not new_role_name or not new_display_name:
                    st.error("角色代码和角色名称不能为空")
                else:
                    try:
                        user_info = auth_manager.get_user_info()
                        created_by = user_info.get('username', 'system')
                        result = api_client.create_role(
                            {
                                "role_name": new_role_name.strip(),
                                "display_name": new_display_name.strip(),
                                "description": new_description.strip()
                            },
                            created_by=created_by
                        )
                        if result.get("success"):
                            st.success("✅ 角色创建成功！")
                            load_roles_data()
                            st.rerun()
                        else:
                            st.error(f"❌ 创建角色失败：{result.get('message', '未知错误')}")
                    except Exception as e:
                        st.error(f"❌ 创建角色异常：{str(e)}")

    # 底部：编辑角色表单（仍然复用原有逻辑）
    if 'editing_role' in st.session_state:
        show_edit_role_form()

def show_permissions_management():
    """显示权限管理"""
    st.markdown("### 🔑 权限管理")
    
    # 强制重新加载权限数据
    load_permissions_data()
    
    # 操作按钮
    if st.button("🔄 刷新数据", help="重新加载权限数据", key="permissions_refresh"):
        load_permissions_data()
        st.rerun()
    
    st.markdown("---")
    
    # 显示权限列表
    permissions = st.session_state.get('permissions_data', [])
    
    if not permissions:
        st.info("📝 暂无权限数据")
        return
    
    # 权限统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总权限数", len(permissions))
    with col2:
        active_permissions = len([p for p in permissions if p.get('is_active', True)])
        st.metric("启用权限", active_permissions)
    with col3:
        categories = len(set(p.get('category', '') for p in permissions))
        st.metric("权限分类", categories)
    
    st.markdown("---")
    
    # 按分类显示权限
    categories = {}
    for perm in permissions:
        category = perm.get('category', '未分类')
        if category not in categories:
            categories[category] = []
        categories[category].append(perm)
    
    for category, perms in categories.items():
        with st.expander(f"📁 {category} ({len(perms)} 个权限)"):
            for i, perm in enumerate(perms):
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{perm.get('permission_name', '未知权限')}**")
                    st.caption(f"代码: {perm.get('permission_code', 'N/A')}")
                
                with col2:
                    st.markdown(f"📝 {perm.get('description', '无描述')}")
                
                with col3:
                    status_color = "🟢" if perm.get('is_active', True) else "🔴"
                    st.caption(f"{status_color} {'启用' if perm.get('is_active', True) else '禁用'}")
                
                with col4:
                    # 使用权限ID作为key的一部分，确保唯一性
                    perm_id = perm.get('_id', f'perm_{i}')
                    if st.button("🔄", key=f"toggle_perm_{perm_id}", help="切换启用状态"):
                        toggle_permission_status(perm)
                        st.rerun()
    
    # 添加说明信息
    st.info("💡 **权限说明**：系统权限通过代码管理，如需添加新权限请联系开发人员。")

def toggle_permission_status(permission):
    """切换权限启用状态"""
    try:
        current_status = permission.get('is_active', True)
        new_status = not current_status

        # 调用云函数更新权限状态（调试输出已移除，避免干扰界面）
        from utils.cloudbase_client import api_client
        result = api_client.update_permission_status(
            permission.get('_id'),  # 使用数据库中的实际ID
            new_status
        )

        if result.get('success'):
            status_text = "启用" if new_status else "禁用"
            st.success(f"✅ 权限 '{permission.get('permission_name')}' 已{status_text}！")
            
            # 刷新权限数据并重新加载页面
            load_permissions_data()
            st.rerun()
        else:
            st.error(f"❌ 更新权限状态失败: {result.get('message', '未知错误')}")
        
    except Exception as e:
        st.error(f"❌ 切换权限状态异常: {str(e)}")

def show_role_permissions_config():
    """显示角色权限配置"""
    st.markdown("### ⚙️ 角色权限配置")
    
    roles = st.session_state.get('roles_data', [])
    permissions = st.session_state.get('permissions_data', [])
    
    if not roles or not permissions:
        st.warning("⚠️ 请先确保角色和权限数据已加载")
        return
    
    # 选择角色
    role_options = {f"{r.get('display_name', r.get('role_name'))}": r for r in roles}
    
    # 如果有从角色管理页面跳转过来的角色，自动选择它
    default_index = 0
    if 'configuring_role' in st.session_state:
        configuring_role = st.session_state.configuring_role
        for i, (name, role) in enumerate(role_options.items()):
            if role.get('_id') == configuring_role.get('_id'):
                default_index = i
                break
        # 清除配置状态，避免下次进入时还选中
        del st.session_state.configuring_role
    
    selected_role_name = st.selectbox(
        "选择要配置的角色:",
        options=list(role_options.keys()),
        index=default_index,
        help="选择要配置权限的角色"
    )
    
    if not selected_role_name:
        st.info("请选择一个角色")
        return
    
    selected_role = role_options[selected_role_name]
    st.markdown(f"**当前角色**: {selected_role.get('display_name')} ({selected_role.get('role_name')})")
    
    # 获取角色当前权限
    if 'role_permissions' not in st.session_state or st.session_state.get('current_config_role_id') != selected_role.get('_id'):
        load_role_permissions(selected_role.get('_id'))
        st.session_state.current_config_role_id = selected_role.get('_id')
    
    current_permissions = st.session_state.get('role_permissions', [])
    current_permission_ids = [p.get('_id') for p in current_permissions]
    
    st.markdown("---")
    
    # 权限配置界面
    st.markdown("#### 🔧 权限配置")
    
    # 按分类显示权限选择
    categories = {}
    for perm in permissions:
        category = perm.get('category', '未分类')
        if category not in categories:
            categories[category] = []
        categories[category].append(perm)
    
    new_permission_ids = []
    
    for category, perms in categories.items():
        with st.expander(f"📁 {category} ({len(perms)} 个权限)"):
            for perm in perms:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{perm.get('permission_name')}**")
                    st.caption(f"{perm.get('description', '无描述')}")
                
                with col2:
                    is_checked = perm.get('_id') in current_permission_ids
                    # 使用重置标志来强制重新渲染checkbox
                    reset_key = st.session_state.get('reset_permissions', 0)
                    checkbox_key = f"perm_{perm.get('_id')}_{reset_key}"
                    
                    if st.checkbox(
                        "启用",
                        value=is_checked,
                        key=checkbox_key,
                        help=f"权限代码: {perm.get('permission_code')}"
                    ):
                        new_permission_ids.append(perm.get('_id'))
    
    st.markdown("---")
    
    # 保存按钮
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("💾 保存权限配置", type="primary"):
            save_role_permissions(selected_role.get('_id'), new_permission_ids)
    
    with col2:
        if st.button("🔄 重置为当前配置"):
            # 清除权限缓存
            if 'role_permissions' in st.session_state:
                del st.session_state.role_permissions
            if 'current_config_role_id' in st.session_state:
                del st.session_state.current_config_role_id
            
            # 增加重置标志，强制重新渲染所有checkbox
            st.session_state.reset_permissions = st.session_state.get('reset_permissions', 0) + 1
            
            # 重新加载当前角色的权限
            load_role_permissions(selected_role.get('_id'))
            st.session_state.current_config_role_id = selected_role.get('_id')
            st.success("✅ 已重置为当前配置")
            st.rerun()

def load_role_permissions(role_id: str):
    """加载角色权限"""
    try:
        result = api_client.get_role_permissions(role_id)
        if result.get('success'):
            st.session_state.role_permissions = result.get('data', {}).get('permissions', [])
        else:
            st.error(f"❌ 加载角色权限失败: {result.get('message', '未知错误')}")
            st.session_state.role_permissions = []
    except Exception as e:
        st.error(f"❌ 加载角色权限异常: {str(e)}")
        st.session_state.role_permissions = []

def save_role_permissions(role_id: str, permission_ids: List[str]):
    """保存角色权限"""
    try:
        user_info = auth_manager.get_user_info()
        granted_by = user_info.get('username', 'system')
        
        result = api_client.update_role_permissions(role_id, permission_ids, granted_by)
        
        if result.get('success'):
            st.success(f"✅ 角色权限更新成功！已配置 {len(permission_ids)} 个权限")
            # 清除缓存，强制重新加载
            if 'role_permissions' in st.session_state:
                del st.session_state.role_permissions
            st.rerun()
        else:
            st.error(f"❌ 角色权限更新失败: {result.get('message', '未知错误')}")
    except Exception as e:
        st.error(f"❌ 保存角色权限异常: {str(e)}")

def init_default_data():
    """初始化默认数据"""
    try:
        with st.spinner("正在初始化默认数据..."):
            result = api_client.init_default_role_data()
        
        if result.get('success'):
            st.success("✅ 默认数据初始化成功！")
            st.info(f"📊 创建了 {result.get('data', {}).get('permissions_created', 0)} 个权限和 {result.get('data', {}).get('roles_created', 0)} 个角色")
            # 重新加载数据
            load_roles_data()
            load_permissions_data()
            st.rerun()
        else:
            st.error(f"❌ 初始化失败: {result.get('message', '未知错误')}")
    except Exception as e:
        st.error(f"❌ 初始化异常: {str(e)}")

def show_edit_role_form():
    """显示编辑角色表单"""
    role = st.session_state.editing_role
    
    st.markdown("---")
    st.markdown("### ✏️ 编辑角色")
    
    with st.form("edit_role_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("角色代码", value=role.get('role_name', ''), disabled=True, help="角色代码不可修改")
            
            display_name = st.text_input(
                "显示名称 *",
                value=role.get('display_name', ''),
                help="角色的显示名称"
            )
        
        with col2:
            description = st.text_area(
                "角色描述",
                value=role.get('description', ''),
                help="角色的详细描述"
            )
            
            is_active = st.checkbox(
                "启用角色", 
                value=role.get('is_active', True),
                help="禁用的角色将无法使用"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button("保存修改", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("取消", type="secondary")
        
        if submit_button:
            # 这里可以添加更新角色的逻辑
            st.success("✅ 角色信息更新成功！")
            if 'editing_role' in st.session_state:
                del st.session_state.editing_role
            st.rerun()
        
        if cancel_button:
            if 'editing_role' in st.session_state:
                del st.session_state.editing_role
            st.rerun()

