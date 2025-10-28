"""
订单列表组件

功能：
- 显示订单列表（紧凑卡片样式）
- 支持搜索、筛选
- 支持分页
- 点击选中订单
"""

import streamlit as st


def show(order_service, search="", status_filter="全部", page_size=10):
    """
    显示订单列表
    
    Args:
        order_service: OrderService 实例
        search: 搜索关键词
        status_filter: 状态筛选
        page_size: 每页显示数量
    
    Returns:
        selected_order: 用户点击选中的订单（dict）或 None
    """
    
    # 初始化分页状态
    if 'order_list_page' not in st.session_state:
        st.session_state.order_list_page = 1
    
    # 转换状态筛选
    status_value = "all" if status_filter == "全部" else status_filter
    
    # 加载订单
    with st.spinner("加载订单列表..."):
        result = order_service.list_orders(
            page=st.session_state.order_list_page,
            limit=page_size,
            status=status_value,
            search=search
        )
    
    if not result.get('success'):
        st.error(f"❌ 加载失败：{result.get('message')}")
        return None
    
    data = result.get('data', {})
    
    # 处理嵌套的数据结构
    if isinstance(data, dict) and data.get('success'):
        orders = data.get('data', {}).get('orders', [])
        pagination = data.get('data', {}).get('pagination', {})
    else:
        orders = data.get('orders', [])
        pagination = data.get('pagination', {})
    
    if not orders:
        st.info("📭 暂无订单数据")
        return None
    
    # 显示订单数量
    st.caption(f"共 {pagination.get('total', 0)} 个订单")
    
    # 显示订单卡片
    selected_order = None
    current_selected_id = st.session_state.get('selected_order_id')
    
    for order in orders:
        order_id = order.get('_id') or order.get('order_id')
        is_selected = (order_id == current_selected_id)
        
        # 订单信息
        order_number = order.get('order_number', 'N/A')
        customer_name = order.get('customer_name', 'N/A')
        order_status = order.get('order_status', 'N/A')
        progress = order.get('progress_percentage', 0)
        
        # 状态图标
        status_icons = {
            '待处理': '⏸️',
            '制作中': '🔄',
            '已完成': '✅',
            '已取消': '❌'
        }
        status_icon = status_icons.get(order_status, '📄')
        
        # 订单卡片
        if is_selected:
            # 选中状态 - 高亮显示
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                        padding: 12px; 
                        border-radius: 8px; 
                        border-left: 4px solid #2196F3; 
                        margin-bottom: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-weight: 600; color: #1976D2; margin-bottom: 4px;">
                    {status_icon} {order_number}
                </div>
                <div style="color: #424242; font-size: 0.95em; margin-bottom: 4px;">
                    {customer_name}
                </div>
                <div style="color: #666; font-size: 0.85em;">
                    {order_status} | {progress}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 未选中状态 - 可点击按钮
            button_label = f"{status_icon} {order_number}\n{customer_name}\n{order_status} | {progress}%"
            if st.button(
                button_label,
                key=f"order_btn_{order_id}",
                width='stretch'
            ):
                selected_order = order
                st.session_state.selected_order_id = order_id
    
    # 分页控制
    total_pages = pagination.get('total_pages', 1)
    current_page = pagination.get('page', 1)
    
    if total_pages > 1:
        st.markdown("---")
        cols = st.columns([1, 2, 1])
        
        with cols[0]:
            if st.button("◀", disabled=(current_page == 1)):
                st.session_state.order_list_page = current_page - 1
                st.rerun()
        
        with cols[1]:
            st.markdown(
                f"<center style='padding-top: 8px;'>{current_page} / {total_pages}</center>", 
                unsafe_allow_html=True
            )
        
        with cols[2]:
            if st.button("▶", disabled=(current_page >= total_pages)):
                st.session_state.order_list_page = current_page + 1
                st.rerun()
    
    return selected_order

