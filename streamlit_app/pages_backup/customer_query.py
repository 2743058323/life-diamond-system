import streamlit as st
import streamlit.components.v1 as components
from utils.cloudbase_client import api_client
from utils.helpers import (
    render_progress_timeline, 
    render_photo_gallery, 
    render_order_card,
    show_error_message,
    format_datetime,
    get_status_info,
    get_stage_info,
    download_photo_from_url
)
from typing import Dict, Any, List

def show_page():
    """客户查询页面"""
    st.title("🔍 客户订单查询")
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    ">
        <h3 style="margin: 0; margin-bottom: 0.5rem;">欢迎使用生命钻石服务系统</h3>
        <p style="margin: 0; opacity: 0.9;">请输入您的姓名查询订单信息和制作进度</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 查询表单
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            st.markdown("### 订单查询")
            
            with st.form("search_form", clear_on_submit=False):
                customer_name = st.text_input(
                    "客户姓名",
                    placeholder="请输入您的姓名",
                    help="请输入订单时的姓名（必须完全匹配）"
                )
                
                search_button = st.form_submit_button(
                    "查询订单",
                    type="primary"
                )
                
                if search_button:
                    if customer_name.strip():
                        search_orders(customer_name.strip())
                    else:
                        st.warning("请输入客户姓名")
    
    # 根据状态显示不同内容：要么显示列表，要么显示详情
    if 'selected_order' in st.session_state and st.session_state.selected_order:
        # 如果有选中的订单，只显示详情页
        show_order_details()
    elif 'search_results' in st.session_state and st.session_state.search_results:
        # 否则显示订单列表
        show_search_results()
    
    # 帮助信息
    with st.expander("使用说明"):
        st.markdown("""
        **如何查询订单？**
        
        1. 在上方输入框中输入您的姓名（必须与订单时的姓名完全一致）
        2. 点击“查询订单”按钮
        3. 系统将显示您的所有订单
        4. 点击具体订单可查看详细信息和制作进度
        
        **注意事项：**
        - 姓名必须与订单时填写的完全一致
        - 如果找不到订单，请检查姓名是否正确或联系客服
        - 系统将实时更新订单进度信息
        """)

def search_orders(customer_name: str):
    """查询订单"""
    with st.spinner("正在查询订单..."):
        result = api_client.search_orders_by_name(customer_name)
        
        if result.get("success"):
            data = result.get("data", {})
            
            # 处理嵌套的数据结构
            if isinstance(data, dict) and 'data' in data:
                orders = data['data']
            elif isinstance(data, list):
                orders = data
            else:
                orders = []
            
            if orders:
                st.session_state.search_results = orders
                st.session_state.search_customer_name = customer_name
                st.success(f"找到 {len(orders)} 个订单")
            else:
                st.info(f"未找到客户'{customer_name}'的订单，请检查姓名是否正确")
                if 'search_results' in st.session_state:
                    del st.session_state.search_results
        else:
            show_error_message(
                result.get("message", "查询失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试或联系客服"
            )
            if 'search_results' in st.session_state:
                del st.session_state.search_results

def show_search_results():
    """显示查询结果"""
    st.markdown("---")
    st.markdown(f"### 📝 {st.session_state.search_customer_name} 的订单列表")
    
    orders = st.session_state.search_results
    
    # 确保orders是列表格式
    if isinstance(orders, dict) and 'data' in orders:
        orders = orders['data']
    elif not isinstance(orders, list):
        orders = []
    
    # 按创建时间排序（最新的在前）
    orders_sorted = sorted(orders, key=lambda x: x.get('created_at', '') if isinstance(x, dict) else '', reverse=True)
    
    for i, order in enumerate(orders_sorted):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            render_order_card(order)
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)  # 垂直居中
            if st.button(
                "查看详情",
                key=f"detail_{order.get('order_id', i)}",
                width='stretch',
                type="secondary"
            ):
                load_order_details(order.get('_id'))

def load_order_details(order_id: str):
    """加载订单详情"""
    with st.spinner("正在加载订单详情..."):
        result = api_client.get_order_detail(order_id)
        
        if result.get("success"):
            # 处理嵌套的数据结构
            data = result.get("data", {})
            if data.get("success"):
                st.session_state.selected_order = data.get("data", {})
            else:
                st.session_state.selected_order = data
            
            # 立即刷新页面以显示详情
            st.rerun()
        else:
            show_error_message(
                result.get("message", "订单详情加载失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试或联系客服"
            )

def show_order_details():
    """显示订单详情"""
    order_data = st.session_state.selected_order
    order_info = order_data.get("order_info", {})
    progress_timeline = order_data.get("progress_timeline", [])
    photos = order_data.get("photos", [])
    
    st.markdown("---")
    
    # 返回按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 返回列表", width='stretch'):
            if 'selected_order' in st.session_state:
                del st.session_state.selected_order
            st.rerun()
    
    st.markdown(f"### 📜 订单详情：{order_info.get('order_number', '')}")
    
    # 订单基本信息
    with st.container():
        st.markdown("#### 📝 订单信息")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 👤 客户信息")
            st.markdown(f"**姓名：** {order_info.get('customer_name', '')}")
            st.markdown(f"**电话：** {order_info.get('customer_phone', '')}")
            if order_info.get('customer_email'):
                st.markdown(f"**邮箱：** {order_info.get('customer_email', '')}")
        
        with col2:
            st.markdown("#### 💎 产品信息")
            st.markdown(f"**类型：** {order_info.get('diamond_type', '')}")
            st.markdown(f"**大小：** {order_info.get('diamond_size', '')}")
            st.markdown(f"**状态：** {order_info.get('order_status', '')}")
        
        with col3:
            st.markdown("#### ⏰ 时间信息")
            st.markdown(f"**下单时间：** {format_datetime(order_info.get('created_at', ''), 'date')}")
            estimated = format_datetime(order_info.get('estimated_completion', ''), 'date') if order_info.get('estimated_completion') else '未设定'
            st.markdown(f"**预计完成：** {estimated}")
            st.markdown(f"**进度：** {order_info.get('progress_percentage', 0)}%")
    
    # 特殊要求
    if order_info.get('special_requirements'):
        st.markdown("#### 📝 特殊要求")
        st.info(order_info.get('special_requirements'))
    
    st.markdown("---")
    
    # 制作进度与照片（合并展示）
    if progress_timeline:
        render_progress_with_photos(
            progress_timeline, 
            photos,
            order_info.get('current_stage', '')
        )
    else:
        st.warning("暂无进度信息")
    
    # 底部提示
    st.markdown("---")
    st.markdown("""
    <div style="
        text-align: center;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        color: #666;
    ">
        如有疑问或需要帮助，请联系我们的客服人员<br>
        电话：400-123-4567 | 邮箱：support@lifediamond.com
    </div>
    """, unsafe_allow_html=True)

def render_progress_with_photos(progress_data: List[Dict[str, Any]], photos_data: List[Dict[str, Any]], current_stage: str = ""):
    """渲染进度时间轴与照片（合并展示）"""
    st.markdown("#### 🔄 制作进度与过程照片")
    
    # 将照片按阶段分组
    photos_by_stage = {}
    for stage_photos in photos_data:
        stage_name = stage_photos.get("stage_name", "")
        photos_by_stage[stage_name] = stage_photos.get("photos", [])
    
    # 按阶段顺序排序
    progress_data_sorted = sorted(progress_data, key=lambda x: x.get('stage_order', 0))
    
    for i, progress in enumerate(progress_data_sorted):
        stage_name = progress.get("stage_name", "")
        status = progress.get("status", "pending")
        started_at = progress.get("started_at")
        completed_at = progress.get("completed_at")
        estimated_completion = progress.get("estimated_completion")
        notes = progress.get("notes", "")
        
        status_info = get_status_info(status)
        stage_info = get_stage_info(f"stage_{i+1}")
        
        # 判断是否为当前阶段
        is_current = stage_name == current_stage
        
        # 获取该阶段的照片
        stage_photos = photos_by_stage.get(stage_name, [])
        
        # 阶段卡片容器
        with st.container():
            # 阶段头部：图标 + 标题 + 状态
            col_title, col_status = st.columns([3, 1])
            
            with col_title:
                stage_icon = stage_info.get('icon', '📍')
                if is_current:
                    st.markdown(f"""
                    <div style="font-size: 1.3rem; font-weight: bold; color: #333; margin-bottom: 0.5rem;">
                        {stage_icon} {stage_name} <span style="color: #1f77b4;">● 正在进行中</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="font-size: 1.3rem; font-weight: bold; color: #333; margin-bottom: 0.5rem;">
                        {stage_icon} {stage_name}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_status:
                st.markdown(f"""
                <div style="
                    background: {status_info['color']};
                    color: white;
                    padding: 6px 14px;
                    border-radius: 20px;
                    font-size: 0.9rem;
                    font-weight: bold;
                    text-align: center;
                    margin-top: 0.3rem;
                ">
                    {status_info['icon']} {status_info['name']}
                </div>
                """, unsafe_allow_html=True)
            
            # 阶段简短描述
            st.markdown(f"<p style='color: #666; font-style: italic; margin-bottom: 1rem;'>{stage_info.get('description', '')}</p>", unsafe_allow_html=True)
            
            # 时间信息
            time_info = []
            if started_at:
                time_info.append(f"🕐 开始：{format_datetime(started_at, 'datetime')}")
            if completed_at:
                time_info.append(f"✅ 完成：{format_datetime(completed_at, 'datetime')}")
            elif estimated_completion:
                time_info.append(f"⏰ 预计：{format_datetime(estimated_completion, 'date')}")
            
            if time_info:
                col_time1, col_time2 = st.columns(2)
                for idx, info in enumerate(time_info):
                    with (col_time1 if idx == 0 else col_time2):
                        st.caption(info)
            
            # 详细说明（可折叠）
            detail_desc = stage_info.get('detail_description', '')
            if detail_desc:
                with st.expander("💡 了解这个阶段"):
                    st.info(detail_desc)
                    estimated_days = stage_info.get('estimated_days', 0)
                    if estimated_days > 0:
                        st.caption(f"⏱️ 通常需要约 {estimated_days} 天")
            
            # 工作人员备注
            if notes:
                with st.expander("📝 工作人员备注"):
                    st.write(notes)
            
            # 该阶段的照片
            if stage_photos:
                with st.expander(f"📸 查看本阶段照片 ({len(stage_photos)} 张)", expanded=False):
                    st.caption("💡 长按图片可保存")
                    
                    # 准备图片列表和标签
                    images = []
                    labels = []
                    photo_data_map = {}  # 用于存储照片的完整信息
                    
                    for photo_idx, photo in enumerate(stage_photos):
                        photo_url = photo.get("thumbnail_url", photo.get("photo_url", ""))
                        photo_desc = photo.get("description", "")
                        if not photo_desc:
                            photo_desc = format_datetime(photo.get('upload_time', ''), 'datetime')
                        
                        if photo_url:  # 只添加有效的URL
                            images.append(photo_url)
                            labels.append(photo_desc)
                            
                            # 存储完整照片信息
                            photo_data_map[photo_url] = {
                                'url': photo.get("photo_url", ""),
                                'caption': photo_desc,
                                'filename': photo.get("file_name", f"photo_{photo_idx+1}.jpg")
                            }
                    
                    # 使用HTML可点击图片（无需按钮，直接点击图片在新标签打开）
                    if images:
                        # 每行显示3张图片
                        cols_per_row = 3
                        for row_idx in range(0, len(images), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for col_idx, col in enumerate(cols):
                                img_idx = row_idx + col_idx
                                if img_idx < len(images):
                                    with col:
                                        # 显示图片
                                        st.image(images[img_idx], width='stretch')
                                        st.caption(labels[img_idx])
                    else:
                        st.warning("⚠️ 该阶段照片URL无效或为空")
            else:
                # 如果该阶段还没照片
                if status == 'pending':
                    st.caption("⏳ 该阶段尚未开始，暂无照片")
                elif status == 'in_progress':
                    st.caption("📷 该阶段正在进行中，照片上传中...")
                else:
                    st.caption("📷 该阶段暂无照片记录")
            
            # 阶段分隔线
            if i < len(progress_data_sorted) - 1:
                st.markdown("""
                <div style="
                    height: 2px;
                    background: linear-gradient(to right, #dee2e6 0%, #adb5bd 50%, #dee2e6 100%);
                    margin: 2rem 0;
                "></div>
                """, unsafe_allow_html=True)