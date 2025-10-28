import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    render_progress_timeline,
    show_error_message,
    show_success_message,
    format_datetime,
    get_stage_info
)
from config import PRODUCTION_STAGES
from datetime import datetime, date

def show_page():
    """进度管理页面"""
    # 权限检查
    if not auth_manager.require_permission("progress.update"):
        return
    
    st.title("🔄 进度管理")
    st.markdown("更新和管理生命钻石制作进度，跟踪各个阶段的完成情况")
    
    # 检查是否有选中的订单需要显示进度更新表单
    if 'selected_order_for_progress' in st.session_state:
        show_progress_update_form()
    else:
        # 页面模式选择
        tab1, tab2 = st.tabs(["📅 单个进度更新", "📊 所有订单管理"])
        
        with tab1:
            show_single_progress_update()
        
        with tab2:
            show_all_orders_dashboard()

def show_single_progress_update():
    """单个进度更新"""
    st.markdown("### 选择订单")
    
    # 订单查询
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "搜索订单",
            placeholder="输入订单编号或客户姓名",
            key="progress_search_query"
        )
    
    with col2:
        if st.button("🔍 查询订单", width='stretch'):
            if search_query:
                search_orders_for_progress(search_query)
            else:
                st.warning("请输入搜索关键词")
    
    # 显示搜索结果
    if 'progress_search_results' in st.session_state:
        show_order_selection()
    
    # 显示选中订单的进度更新表单
    if 'selected_order_for_progress' in st.session_state:
        show_progress_update_form()

def search_orders_for_progress(query: str):
    """搜索订单用于进度更新"""
    with st.spinner("正在搜索订单..."):
        # 首先尝试按客户姓名搜索
        result = api_client.search_orders_by_name(query)
        
        if result.get("success"):
            # 处理嵌套的数据结构
            data = result.get("data", {})
            if isinstance(data, dict) and data.get("success"):
                orders = data.get("data", [])
            else:
                orders = data if isinstance(data, list) else []
                
            if orders:
                st.session_state.progress_search_results = orders
                st.success(f"找到 {len(orders)} 个订单")
            else:
                # 如果按姓名未找到，尝试从所有订单中搜索
                all_orders_result = api_client.get_orders(page=1, limit=100, status="all", search="")
                if all_orders_result.get("success"):
                    # 处理嵌套的数据结构
                    all_data = all_orders_result.get("data", {})
                    if isinstance(all_data, dict) and all_data.get("success"):
                        all_orders_info = all_data.get("data", {})
                        all_orders = all_orders_info.get("orders", [])
                    else:
                        all_orders = []
                    # 按订单编号过滤
                    filtered_orders = [
                        order for order in all_orders 
                        if query.lower() in order.get('order_number', '').lower()
                    ]
                    
                    if filtered_orders:
                        st.session_state.progress_search_results = filtered_orders
                        st.success(f"找到 {len(filtered_orders)} 个订单")
                    else:
                        st.info(f"未找到包含“{query}”的订单")
                        if 'progress_search_results' in st.session_state:
                            del st.session_state.progress_search_results
                else:
                    show_error_message(
                        "搜索失败",
                        error_code=str(all_orders_result.get("status_code", "")),
                        support_info="请稍后重试"
                    )
        else:
            show_error_message(
                result.get("message", "搜索失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def show_order_selection():
    """显示订单选择"""
    st.markdown("---")
    st.markdown("### 选择要更新进度的订单")
    
    orders = st.session_state.progress_search_results
    
    for i, order in enumerate(orders):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div style="
                background: white;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #8B4B8C;
                margin-bottom: 0.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="font-weight: bold; color: #333; margin-bottom: 0.5rem;">
                    {order.get('order_number', '')} - {order.get('customer_name', '')}
                </div>
                <div style="color: #666; font-size: 0.9rem;">
                    钻石类型：{order.get('diamond_type', '')} ({order.get('diamond_size', '')})<br>
                    当前阶段：{order.get('current_stage', '')} (进度: {order.get('progress_percentage', 0)}%)<br>
                    订单状态：{order.get('order_status', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button(
                "选择此订单",
                key=f"select_order_{order.get('_id', i)}",
                width='stretch'
            ):
                select_order_for_progress(order)

def select_order_for_progress(order: dict, show_success_message: bool = True):
    """选择订单进行进度更新"""
    # 获取订单详细信息
    with st.spinner("正在加载订单详情..."):
        result = api_client.get_order_detail(order.get('_id'), is_admin=True)
        
        if result.get("success"):
            # 处理嵌套的数据结构
            data = result.get("data", {})
            if isinstance(data, dict) and data.get("success"):
                st.session_state.selected_order_for_progress = data.get("data", {})
            else:
                st.session_state.selected_order_for_progress = data
            
            if show_success_message:
                st.success("订单信息加载成功")
        else:
            show_error_message(
                result.get("message", "订单详情加载失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def show_progress_update_form():
    """显示进度更新表单"""
    order_data = st.session_state.selected_order_for_progress
    order_info = order_data.get("order_info", {})
    progress_timeline = order_data.get("progress_timeline", [])
    
    st.markdown("---")
    
    # 返回按钮
    if st.button("← 重新选择订单"):
        if 'selected_order_for_progress' in st.session_state:
            del st.session_state.selected_order_for_progress
        st.rerun()
    
    st.markdown(f"### 更新订单进度：{order_info.get('order_number', '')}")
    
    # 显示当前进度
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8B4B8C; margin: 0; margin-bottom: 0.5rem;">当前状态</h4>
            <p style="margin: 0; color: #666;">
                <strong>客户姓名：</strong>{order_info.get('customer_name', '')}<br>
                <strong>当前阶段：</strong>{order_info.get('current_stage', '')}<br>
                <strong>整体进度：</strong>{order_info.get('progress_percentage', 0)}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8B4B8C; margin: 0; margin-bottom: 0.5rem;">订单信息</h4>
            <p style="margin: 0; color: #666;">
                <strong>钻石类型：</strong>{order_info.get('diamond_type', '')}<br>
                <strong>钻石大小：</strong>{order_info.get('diamond_size', '')}<br>
                <strong>订单状态：</strong>{order_info.get('order_status', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 进度更新表单
    st.markdown("#### 选择要更新的阶段")
    
    with st.form("progress_update_form"):
        # 选择阶段
        stage_options = []
        stage_mapping = {}
        
        for progress in progress_timeline:
            stage_name = progress.get("stage_name", "")
            status = progress.get("status", "pending")
            stage_key = f"{stage_name} ({status})"
            stage_options.append(stage_key)
            stage_mapping[stage_key] = progress
        
        if not stage_options:
            st.error("未找到可更新的阶段")
            return
        
        selected_stage_key = st.selectbox(
            "选择阶段",
            options=stage_options,
            help="选择要更新的制作阶段"
        )
        
        # 新状态
        new_status = st.selectbox(
            "新状态",
            options=["pending", "in_progress", "completed"],
            format_func=lambda x: {
                "pending": "待处理",
                "in_progress": "进行中",
                "completed": "已完成"
            }[x],
            help="选择阶段的新状态"
        )
        
        # 完成时间（如果状态为已完成）
        completion_date = None
        completion_time = None
        uploaded_photos = None
        
        if new_status == "completed":
            col3, col4 = st.columns(2)
            with col3:
                completion_date = st.date_input(
                    "完成日期",
                    value=date.today(),
                    help="选择阶段完成日期"
                )
            with col4:
                completion_time = st.time_input(
                    "完成时间",
                    value=datetime.now().time(),
                    help="选择阶段完成时间"
                )
            
            # 照片上传（可选）
            st.markdown("#### 📷 上传完成照片（可选）")
            st.info("💡 建议上传该阶段的完成照片，客户可以在查询页面看到")
            uploaded_photos = st.file_uploader(
                "选择照片文件",
                type=['jpg', 'jpeg', 'png'],
                accept_multiple_files=True,
                help="支持上传多张照片，建议每张不超过5MB",
                key="progress_photo_uploader"
            )
            
            if uploaded_photos:
                st.success(f"✅ 已选择 {len(uploaded_photos)} 张照片")
                # 显示预览
                preview_cols = st.columns(min(len(uploaded_photos), 4))
                for i, photo in enumerate(uploaded_photos[:4]):
                    with preview_cols[i]:
                        st.image(photo, width='stretch', caption=f"照片 {i+1}")
                if len(uploaded_photos) > 4:
                    st.caption(f"还有 {len(uploaded_photos) - 4} 张照片...")
        
        # 备注
        notes = st.text_area(
            "备注信息",
            placeholder="请输入本次更新的备注信息（可选）",
            height=100
        )
        
        # 提交按钮
        col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 2])
        
        with col_submit2:
            submitted = st.form_submit_button(
                "更新进度",
                type="primary"
            )
        
        if submitted:
            selected_progress = stage_mapping[selected_stage_key]
            
            # 构建完成时间
            actual_completion = None
            if new_status == "completed" and completion_date and completion_time:
                completion_datetime = datetime.combine(completion_date, completion_time)
                actual_completion = completion_datetime.isoformat()
            
            # 获取阶段ID，尝试不同的字段名
            stage_id = (selected_progress.get('stage_id') or 
                       selected_progress.get('id') or 
                       selected_progress.get('_id') or 
                       '')
            
            order_id = order_info.get('_id') or order_info.get('order_id')
            
            # 更新进度
            update_progress(
                order_id,
                stage_id,
                new_status,
                notes,
                actual_completion,
                uploaded_photos  # 传递照片文件
            )
    
    # 显示当前进度时间轴（带照片显示）
    st.markdown("---")
    st.markdown("#### 当前进度时间轴")
    
    if progress_timeline:
        render_progress_timeline_with_photos(
            progress_timeline,
            order_info.get('current_stage', ''),
            order_info.get('_id') or order_info.get('order_id'),
            order_data.get("photos", [])
        )
    else:
        st.warning("暂无进度信息")

def render_progress_timeline_with_photos(progress_data: list, current_stage: str, order_id: str, photos_data: list):
    """渲染带照片显示的进度时间轴"""
    from utils.helpers import get_status_info, format_datetime
    
    # 按阶段分组照片
    photos_by_stage = {}
    for photo_group in photos_data:
        stage_name = photo_group.get("stage_name", "")
        photos_list = photo_group.get("photos", [])
        photos_by_stage[stage_name] = photos_list
    
    # 按阶段顺序排序
    progress_data_sorted = sorted(progress_data, key=lambda x: x.get('stage_order', 0))
    
    for i, progress in enumerate(progress_data_sorted):
        stage_name = progress.get("stage_name", "")
        status = progress.get("status", "pending")
        started_at = progress.get("started_at")
        completed_at = progress.get("completed_at")
        notes = progress.get("notes", "")
        
        status_info = get_status_info(status)
        is_current = stage_name == current_stage
        
        with st.container():
            # 阶段标题和状态
            col1, col2 = st.columns([3, 1])
            with col1:
                if is_current:
                    st.markdown(f"### 🔵 {stage_name}")
                else:
                    icon = "✅" if status == "completed" else ("🔄" if status == "in_progress" else "⏸️")
                    st.markdown(f"### {icon} {stage_name}")
            with col2:
                st.markdown(f"""
                <div style="
                    background: {status_info['color']};
                    color: white;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.9rem;
                    font-weight: bold;
                    text-align: center;
                ">
                    {status_info['icon']} {status_info['name']}
                </div>
                """, unsafe_allow_html=True)
            
            # 时间信息
            if started_at:
                st.caption(f"🕐 开始时间：{format_datetime(started_at)}")
            if completed_at:
                st.caption(f"✅ 完成时间：{format_datetime(completed_at)}")
            if notes:
                st.info(f"📝 {notes}")
            
            # 显示该阶段的照片
            stage_photos = photos_by_stage.get(stage_name, [])
            if stage_photos:
                st.caption(f"📷 已上传 {len(stage_photos)} 张照片")
                photo_cols = st.columns(min(len(stage_photos), 4))
                for j, photo in enumerate(stage_photos[:4]):
                    with photo_cols[j]:
                        photo_url = photo.get("photo_url", photo.get("thumbnail_url", ""))
                        if photo_url:
                            try:
                                st.image(photo_url, width='stretch', caption=f"照片 {j+1}")
                            except:
                                st.caption(f"照片 {j+1}")
                if len(stage_photos) > 4:
                    st.caption(f"还有 {len(stage_photos) - 4} 张...")
            else:
                if status == "completed":
                    st.caption("📷 暂无照片")
            
            if i < len(progress_data_sorted) - 1:
                st.markdown("---")

def update_progress(order_id: str, stage_id: str, status: str, notes: str, actual_completion: str = None, photos=None):
    """更新订单进度（支持同时上传照片）"""
    with st.spinner("正在更新进度..."):
        # 1. 先更新进度
        result = api_client.update_order_progress(
            order_id=order_id,
            stage_id=stage_id,
            status=status,
            notes=notes,
            actual_completion=actual_completion
        )
        
        if not result.get("success"):
            show_error_message(
                result.get("message", "进度更新失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请检查输入信息后重试"
            )
            return
        
        # 2. 如果有照片，上传照片
        photo_upload_success = True
        photo_upload_count = 0
        
        if photos and len(photos) > 0:
            with st.spinner(f"正在上传 {len(photos)} 张照片..."):
                for i, photo in enumerate(photos):
                    try:
                        # 获取阶段信息用于照片上传
                        from config import PRODUCTION_STAGES
                        stage_name = ""
                        for s in PRODUCTION_STAGES:
                            if s.get("id") == stage_id:
                                stage_name = s.get("name", "")
                                break
                        
                        # 调用照片上传API
                        photo_result = api_client.upload_photos(
                            order_id=order_id,
                            stage_id=stage_id,
                            stage_name=stage_name,
                            photos=[photo],
                            description=f"{stage_name}完成照片"
                        )
                        
                        if photo_result.get("success"):
                            photo_upload_count += 1
                        else:
                            photo_upload_success = False
                            st.warning(f"照片 {i+1} 上传失败：{photo_result.get('message', '未知错误')}")
                    except Exception as e:
                        photo_upload_success = False
                        st.warning(f"照片 {i+1} 上传异常：{str(e)}")
        
        # 3. 显示最终结果
        data = result.get("data", {})
        success_msg = f"进度更新成功！\n新进度：{data.get('progress_percentage', 0)}%\n当前阶段：{data.get('current_stage', '')}"
        
        if photos and len(photos) > 0:
            if photo_upload_count == len(photos):
                success_msg += f"\n✅ 已成功上传 {photo_upload_count} 张照片"
            elif photo_upload_count > 0:
                success_msg += f"\n⚠️  已上传 {photo_upload_count}/{len(photos)} 张照片"
            else:
                success_msg += "\n❌ 照片上传失败"
        
        show_success_message("操作完成", success_msg)
        
        # 重新加载订单详情并刷新页面
        select_order_for_progress({'_id': order_id}, show_success_message=False)
        
        # 强制刷新页面以显示最新信息
        st.rerun()

def show_all_orders_dashboard():
    """显示所有订单的仪表板"""
    st.markdown("### 所有订单进度管理")
    st.info("点击订单卡片可以直接进入进度更新页面，无需搜索")
    
    # 加载所有订单
    if st.button("🔄 刷新订单列表", width='stretch'):
        load_all_orders()
    
    if 'all_orders' in st.session_state:
        display_orders_grid()
    else:
        # 自动加载订单
        load_all_orders()

def load_all_orders():
    """加载所有订单"""
    with st.spinner("正在加载所有订单..."):
        # 获取所有状态的订单
        all_orders = []
        
        # 获取不同状态的订单
        statuses = ["待处理", "制作中", "已完成"]
        for status in statuses:
            result = api_client.get_orders(page=1, limit=100, status=status, search="")
            if result.get("success"):
                orders = result.get("data", {}).get("orders", [])
                all_orders.extend(orders)
        
        st.session_state.all_orders = all_orders
        
        if all_orders:
            st.success(f"加载了 {len(all_orders)} 个订单")
        else:
            st.info("当前没有订单")

def display_orders_grid():
    """以网格形式显示所有订单"""
    orders = st.session_state.all_orders
    
    if not orders:
        st.info("没有订单数据")
        return
    
    # 按状态分组
    orders_by_status = {
        "待处理": [],
        "制作中": [],
        "已完成": []
    }
    
    for order in orders:
        status = order.get('order_status', '待处理')
        if status in orders_by_status:
            orders_by_status[status].append(order)
    
    # 显示每个状态的订单
    for status, status_orders in orders_by_status.items():
        if status_orders:
            st.markdown(f"#### {status} ({len(status_orders)}个订单)")
            
            # 使用列布局显示订单卡片
            cols = st.columns(2)
            for i, order in enumerate(status_orders):
                col_index = i % 2
                with cols[col_index]:
                    display_order_card(order)

def display_order_card(order):
    """显示单个订单卡片"""
    order_id = order.get('_id', '')
    order_number = order.get('order_number', '')
    customer_name = order.get('customer_name', '')
    current_stage = order.get('current_stage', '未开始')
    progress_percentage = order.get('progress_percentage', 0)
    order_status = order.get('order_status', '待处理')
    diamond_type = order.get('diamond_type', '')
    diamond_size = order.get('diamond_size', '')
    
    # 根据状态设置卡片颜色
    status_colors = {
        "待处理": "#faad14",
        "制作中": "#1890ff", 
        "已完成": "#52c41a"
    }
    card_color = status_colors.get(order_status, "#d9d9d9")
    
    # 使用Streamlit组件创建订单卡片
    with st.container():
        # 卡片边框
        st.markdown(f"""
        <div style="
            border: 2px solid {card_color};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
        """, unsafe_allow_html=True)
        
        # 订单号和状态
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{order_number}**")
        with col2:
            st.markdown(f"""
            <span style="
                background: {card_color};
                color: white;
                padding: 0.2rem 0.5rem;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: bold;
            ">{order_status}</span>
            """, unsafe_allow_html=True)
        
        # 客户和钻石信息
        st.markdown(f"**客户：** {customer_name}")
        st.markdown(f"**钻石：** {diamond_type} {diamond_size}")
        st.markdown(f"**当前阶段：** {current_stage}")
        
        # 进度条
        st.progress(progress_percentage / 100)
        
        # 进度百分比
        st.markdown(f"**进度：** {progress_percentage}%")
        
        # 关闭卡片div
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 更新进度按钮
        if st.button(f"📝 更新进度", key=f"update_{order_id}", width='stretch'):
            select_order_for_progress({'_id': order_id})
            st.rerun()  # 强制刷新页面

def load_orders_for_batch_update():
    """加载可批量更新的订单"""
    with st.spinner("正在加载订单数据..."):
        result = api_client.get_orders(page=1, limit=50, status="制作中", search="")
        
        if result.get("success"):
            orders = result.get("data", {}).get("orders", [])
            st.session_state.batch_update_orders = orders
            if orders:
                st.success(f"加载了 {len(orders)} 个在制作中的订单")
            else:
                st.info("当前没有在制作中的订单")
        else:
            show_error_message(
                result.get("message", "订单数据加载失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def show_batch_update_form():
    """显示批量更新表单"""
    orders = st.session_state.batch_update_orders
    
    if not orders:
        st.info("没有可更新的订单")
        return
    
    st.markdown("#### 选择要更新的订单")
    
    selected_orders = []
    
    for i, order in enumerate(orders):
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.checkbox(
                "选中",
                key=f"batch_select_{order.get('_id', i)}"
            ):
                selected_orders.append(order)
        
        with col2:
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 0.8rem;
                border-radius: 6px;
                margin-bottom: 0.5rem;
            ">
                <div style="font-weight: bold;">{order.get('order_number', '')} - {order.get('customer_name', '')}</div>
                <div style="color: #666; font-size: 0.9rem;">
                    当前阶段：{order.get('current_stage', '')} (进度: {order.get('progress_percentage', 0)}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if selected_orders:
        st.markdown(f"**已选中 {len(selected_orders)} 个订单**")
        
        # 批量操作选项
        col1, col2 = st.columns(2)
        
        with col1:
            batch_stage = st.selectbox(
                "选择要更新的阶段",
                options=[阶段["name"] for 阶段 in PRODUCTION_STAGES],
                help="选择要更新的制作阶段"
            )
        
        with col2:
            batch_status = st.selectbox(
                "新状态",
                options=["pending", "in_progress", "completed"],
                format_func=lambda x: {
                    "pending": "待处理",
                    "in_progress": "进行中",
                    "completed": "已完成"
                }[x],
                help="选择批量更新的状态"
            )
        
        if st.button("🚀 执行批量更新", type="primary", width='stretch'):
            execute_batch_update(selected_orders, batch_stage, batch_status)

def execute_batch_update(orders: list, stage_name: str, status: str):
    """执行批量更新"""
    # 找到对应的stage_id
    stage_id = None
    for i, stage in enumerate(PRODUCTION_STAGES):
        if stage["name"] == stage_name:
            stage_id = stage["id"]
            break
    
    if not stage_id:
        st.error("未找到指定的制作阶段")
        return
    
    # 执行批量更新
    success_count = 0
    error_count = 0
    error_messages = []
    
    with st.spinner(f"正在批量更新 {len(orders)} 个订单..."):
        for order in orders:
            order_id = order.get("_id") or order.get("order_id")
            order_number = order.get("order_number", '')
            
            try:
                # 调用单个进度更新API
                result = api_client.update_order_progress(
                    order_id=order_id,
                    stage_id=stage_id,
                    status=status,
                    notes=f"批量更新 - {stage_name} -> {status}"
                )
                
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"{order_number}: {result.get('message', '更新失败')}")
                    
            except Exception as e:
                error_count += 1
                error_messages.append(f"{order_number}: 系统错误 - {str(e)}")
    
    # 显示批量更新结果
    if success_count > 0:
        show_success_message(
            "批量更新完成！",
            f"成功更新 {success_count} 个订单\n失败 {error_count} 个订单"
        )
    
    if error_count > 0:
        st.error("部分订单更新失败：")
        for error_msg in error_messages:
            st.error(f"• {error_msg}")
    
    # 重新加载订单数据
    if success_count > 0:
        load_orders_for_batch_update()
        #     f"批量更新成功！共更新了 {len(batch_data)} 个订单",
        #     f"阶段：{stage_name}\n状态：{status}"
        # )
        
        # # 重新加载订单列表
        # load_orders_for_batch_update()