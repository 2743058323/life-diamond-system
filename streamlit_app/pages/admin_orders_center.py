"""
订单详情 - 查看订单的制作进度和照片

功能：
- 显示订单基本信息卡片
- 制作进度管理（开始/完成阶段、上传进度照片）
- 制作照片管理（查看/上传/删除照片）
"""

import streamlit as st
from services.order_service import OrderService
from services.progress_service import ProgressService
from services.photo_service import PhotoService
from components import order_info_card, progress_timeline, photo_gallery
from utils.cloudbase_client import api_client
from utils.auth import auth_manager

# 初始化服务
order_service = OrderService(api_client)
progress_service = ProgressService(api_client)
photo_service = PhotoService(api_client)


def show_page():
    """订单详情页面"""
    # 权限检查
    if not auth_manager.require_permission("orders.read"):
        return
    
    st.title("🔍 订单详情")
    st.caption("查看订单的制作进度和照片")
    
    # 从 session_state 获取订单ID
    if 'selected_order_id' not in st.session_state or not st.session_state.selected_order_id:
        st.info("💡 请从【订单管理】页面选择一个订单查看详情")
        st.markdown("---")
        st.markdown("### 或者手动输入订单编号")
        
        with st.form("search_order_form"):
            input_order_number = st.text_input("订单编号", placeholder="例如：LD1234A1B2C3")
            submitted = st.form_submit_button("🔍 查询")
            
            if submitted and input_order_number:
                # 通过订单编号查找订单
                result = order_service.list_orders(search=input_order_number, limit=1)
                if result.get('success') and result.get('data', {}).get('orders'):
                    found_order = result['data']['orders'][0]
                    st.session_state.selected_order_id = found_order.get('_id')
                    st.rerun()
                else:
                    st.error(f"❌ 未找到订单：{input_order_number}")
        return
    
    # 显示订单详情
    show_order_detail_panel()


def show_order_detail_panel():
    """显示订单详情面板"""
    order_id = st.session_state.get('selected_order_id')
    
    # 加载订单详情
    with st.spinner("加载订单详情..."):
        result = order_service.get_order(order_id)
    
    if not result.get('success'):
        st.error(f"❌ 加载失败：{result.get('message')}")
        return
    
    data = result.get('data', {})
    order = data.get('order', {})
    progress = data.get('progress', [])
    photos = data.get('photos', [])
    allowed_actions = data.get('allowed_actions', [])
    
    # 调试信息已移除
    
    # 顶部：订单信息卡片
    order_info_card.show(order)
    
    # 返回按钮
    if st.button("← 返回订单管理"):
        st.session_state.selected_order_id = None
        st.session_state.admin_page = "订单管理"
        st.rerun()
    
    st.markdown("---")
    
    # Tab选项卡：只保留进度和照片
    tab1, tab2 = st.tabs(["🔄 制作进度", "📷 制作照片"])
    
    with tab1:
        show_progress_tab(order, progress, allowed_actions)
    
    with tab2:
        show_photos_tab(order, photos, progress, allowed_actions)


# show_basic_info_tab 函数已删除 - 基本信息现在通过 order_info_card 显示


def show_progress_tab(order, progress, allowed_actions):
    """进度Tab - 完整版"""
    st.markdown("### 🔄 制作进度")
    
    # 进度概览
    if progress:
        current_stage = progress_service.get_current_stage(progress)
        next_stage = progress_service.get_next_stage(progress)
        completed_stages = progress_service.get_completed_stages(progress)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总进度", f"{order.get('progress_percentage', 0)}%")
        with col2:
            current_name = current_stage.get('stage_name', '未开始') if current_stage else '未开始'
            st.metric("当前阶段", current_name)
        with col3:
            st.metric("已完成阶段", f"{len(completed_stages)}/{len(progress)}")
        
        st.markdown("---")
        
        # 使用进度时间轴组件
        progress_timeline.show(
            progress_service=progress_service,
            order_id=order.get('order_id'),
            progress_data=progress,
            allowed_actions=allowed_actions,
            on_update=lambda: st.rerun()
        )
    else:
        st.info("📭 暂无进度信息")


def show_photos_tab(order, photos, progress, allowed_actions):
    """照片Tab - 完整版"""
    st.markdown("### 📷 制作照片")
    
    # 按阶段分组
    grouped_photos = photo_service.group_photos_by_stage(photos)
    
    # 使用照片画廊组件
    photo_gallery.show(
        photo_service=photo_service,
        order_id=order.get('order_id'),
        photos_data=photos,
        grouped_photos=grouped_photos,
        allowed_actions=allowed_actions,
        on_change=lambda: st.rerun()
    )
    
    # 上传照片模态框
    if st.session_state.get('show_upload_modal', False):
        st.markdown("---")
        photo_gallery.show_upload_modal(
            photo_service=photo_service,
            order_id=order.get('order_id'),
            progress_data=progress,
            on_upload=lambda: st.rerun()
        )

