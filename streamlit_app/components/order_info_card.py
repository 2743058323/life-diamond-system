"""
订单信息卡片组件

显示订单的核心信息（顶部概览）
"""

import streamlit as st


def show(order):
    """
    显示订单信息卡片
    
    Args:
        order: 订单字典，包含订单的所有信息
    """
    # 获取订单信息
    order_number = order.get('order_number', 'N/A')
    customer_name = order.get('customer_name', 'N/A')
    customer_phone = order.get('customer_phone', 'N/A')
    diamond_type = order.get('diamond_type', 'N/A')
    diamond_size = order.get('diamond_size', 'N/A')
    order_status = order.get('order_status', 'N/A')
    progress = order.get('progress_percentage', 0)
    
    # 状态颜色映射
    status_colors = {
        '待处理': '#FFA726',
        '制作中': '#42A5F5',
        '已完成': '#66BB6A',
        '已取消': '#EF5350'
    }
    status_color = status_colors.get(order_status, '#78909C')
    
    # 渲染卡片
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {status_color} 0%, {status_color}dd 100%); 
                padding: 24px; 
                border-radius: 12px; 
                color: white; 
                margin-bottom: 24px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h2 style="margin: 0; color: white;">📋 订单 {order_number}</h2>
            <div style="background: rgba(255,255,255,0.2); 
                        padding: 8px 16px; 
                        border-radius: 20px;
                        font-size: 0.9em;">
                {order_status}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
            <div>
                <div style="opacity: 0.9; font-size: 0.85em; margin-bottom: 4px;">👤 客户姓名</div>
                <div style="font-size: 1.1em; font-weight: 600;">{customer_name}</div>
            </div>
            <div>
                <div style="opacity: 0.9; font-size: 0.85em; margin-bottom: 4px;">📞 联系方式</div>
                <div style="font-size: 1.1em; font-weight: 600;">{customer_phone}</div>
            </div>
            <div>
                <div style="opacity: 0.9; font-size: 0.85em; margin-bottom: 4px;">💎 钻石类型</div>
                <div style="font-size: 1.1em; font-weight: 600;">{diamond_type}</div>
            </div>
            <div>
                <div style="opacity: 0.9; font-size: 0.85em; margin-bottom: 4px;">📏 钻石规格</div>
                <div style="font-size: 1.1em; font-weight: 600;">{diamond_size}</div>
            </div>
            <div>
                <div style="opacity: 0.9; font-size: 0.85em; margin-bottom: 4px;">📊 制作进度</div>
                <div style="font-size: 1.1em; font-weight: 600;">{progress}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 进度条
    st.progress(progress / 100)

