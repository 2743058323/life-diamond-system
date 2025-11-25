import streamlit as st
import sys
import os
from datetime import datetime

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import APP_CONFIG
from utils.helpers import apply_custom_css
from utils.auth import auth_manager
from streamlit_option_menu import option_menu
from components.maintenance_page import check_maintenance_mode, show_maintenance_page, should_bypass_maintenance

# 导入页面组件
from pages_backup import customer_query, admin_dashboard, admin_orders, admin_users, admin_role_permissions, admin_operation_logs

def main():
    """主应用函数"""
    # 页面配置
    st.set_page_config(
        page_title=APP_CONFIG["page_title"],
        page_icon=APP_CONFIG["page_icon"],
        layout=APP_CONFIG["layout"],
        initial_sidebar_state=APP_CONFIG["initial_sidebar_state"],
        menu_items=APP_CONFIG["menu_items"]
    )
    
    # 检查维护模式
    is_maintenance, maintenance_info = check_maintenance_mode()
    if is_maintenance and not should_bypass_maintenance():
        # 显示维护页面并停止执行
        show_maintenance_page(**maintenance_info)
        return
    
    # 应用自定义样式
    apply_custom_css()
    inject_global_footer_css()
    
    # 初始化session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "客户查询"
    
    # 主导航栏
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #8B4B8C; margin: 0;">🔷 生命钻石</h1>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">服务系统</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 导航菜单
        menu_options = ["客户查询", "管理后台"]
        menu_icons = ["search", "gear-fill"]
        
        selected = option_menu(
            menu_title="主导航",
            options=menu_options,
            icons=menu_icons,
            menu_icon="house",
            default_index=0 if st.session_state.current_page == "客户查询" else 1,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#8B4B8C", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#8B4B8C"},
            }
        )
        
        # 更新当前页面
        if selected != st.session_state.current_page:
            st.session_state.current_page = selected
            st.rerun()

    
    # 根据选择的页面显示内容
    if st.session_state.current_page == "客户查询":
        customer_query.show_page()
    elif st.session_state.current_page == "管理后台":
        show_admin_pages()
    
    # 统一底部备案信息
    render_footer()

def show_admin_pages():
    """显示管理后台页面"""
    # 检查登录状态
    if not auth_manager.is_authenticated():
        auth_manager.show_login_form()
        return
    
    # 显示用户信息
    auth_manager.show_user_info()
    
    # 管理后台子菜单
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 管理功能")
        
        admin_options = ["数据仪表板", "订单管理", "订单详情", "操作日志", "用户管理", "角色权限"]
        admin_icons = ["bar-chart-fill", "list-ul", "search", "file-text", "people-fill", "shield-check"]
        
        if 'admin_page' not in st.session_state:
            st.session_state.admin_page = "数据仪表板"
        
        admin_selected = option_menu(
            menu_title=None,
            options=admin_options,
            icons=admin_icons,
            default_index=admin_options.index(st.session_state.admin_page) if st.session_state.admin_page in admin_options else 0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#A569BD", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#A569BD"},
            }
        )
        
        if admin_selected != st.session_state.admin_page:
            st.session_state.admin_page = admin_selected
            st.rerun()
    
    # 显示对应的管理页面
    if st.session_state.admin_page == "数据仪表板":
        admin_dashboard.show_page()
    elif st.session_state.admin_page == "订单管理":
        admin_orders.show_page()
    elif st.session_state.admin_page == "订单详情":
        # 订单详情页面（进度 + 照片）
        from pages import admin_orders_center
        admin_orders_center.show_page()
    elif st.session_state.admin_page == "操作日志":
        admin_operation_logs.show_page()
    elif st.session_state.admin_page == "用户管理":
        admin_users.show_page()
    elif st.session_state.admin_page == "角色权限":
        admin_role_permissions.show_page()

def render_footer():
    """显示备案信息"""
    current_year = datetime.now().year
    footer_style = f"""
    <div class="global-footer">
        © {current_year} 生命钻石服务系统 |
        <a href="https://beian.miit.gov.cn/#/Integrated/index" target="_blank" style="color:#888; text-decoration:none;">
            粤ICP备19152413号
        </a> |
        <a href="https://beian.mps.gov.cn/#/query/webSearch?code=44010402001830" target="_blank" style="color:#888; text-decoration:none;">
            粤公网安备 44010402001830号
        </a>
    </div>
    """
    st.markdown(footer_style, unsafe_allow_html=True)

def inject_global_footer_css():
    """注入主内容底部样式"""
    css = """
    <style>
    .global-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        padding: 8px 0;
        text-align: center;
        font-size: 12px;
        color: #888;
        border-top: 1px solid #eee;
        z-index: 1000;
    }
    .stApp {
        padding-bottom: 60px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

if __name__ == "__main__":
    main()