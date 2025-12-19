import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    show_error_message,
    show_success_message,
    format_datetime
)
from config import PRODUCTION_STAGES
from typing import List
from PIL import Image
import io
from datetime import datetime
from services.photo_service import PhotoService

# 服务实例
photo_service = PhotoService(api_client)

def compress_image(file, max_size_kb=100, quality=85):
    """压缩图片到指定大小"""
    try:
        # 打开图片
        image = Image.open(file)
        
        # 转换为RGB（如果是RGBA）
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # 计算压缩比例
        original_size = len(file.getvalue())
        target_size = max_size_kb * 1024
        
        if original_size <= target_size:
            return file.getvalue()
        
        # 逐步压缩
        for quality in range(quality, 20, -10):
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_size = len(buffer.getvalue())
            
            if compressed_size <= target_size:
                return buffer.getvalue()
        
        # 如果还是太大，缩小尺寸
        width, height = image.size
        while True:
            width = int(width * 0.8)
            height = int(height * 0.8)
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            resized_image.save(buffer, format='JPEG', quality=70, optimize=True)
            compressed_size = len(buffer.getvalue())
            
            if compressed_size <= target_size or width < 200:
                return buffer.getvalue()
        
    except Exception as e:
        st.error(f"图片压缩失败: {e}")
        return file.getvalue()

def show_page():
    """照片管理页面"""
    # 权限检查
    if not auth_manager.require_permission("photos.upload"):
        return
    
    st.title("📷 照片管理")
    st.markdown("上传和管理生命钻石制作过程中的照片，记录制作的每个精彩瞬间")
    
    # 页面模式选择
    tab1, tab2 = st.tabs(["📸 上传照片", "🖼️ 照片管理"])
    
    with tab1:
        show_photo_upload()
    
    with tab2:
        show_photo_management()

def show_photo_upload():
    """显示照片上传界面"""
    st.markdown("### 上传制作过程照片")
    
    # 订单选择
    st.markdown("#### 选择订单")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "搜索订单",
            placeholder="输入订单编号或客户姓名",
            key="photo_search_query"
        )
    
    with col2:
        if st.button("🔍 查询订单"):
            if search_query:
                search_orders_for_photos(search_query)
            else:
                st.warning("请输入搜索关键词")
    
    # 显示搜索结果
    if 'photo_search_results' in st.session_state:
        show_order_selection_for_photos()
    
    # 显示上传表单
    if 'selected_order_for_photos' in st.session_state:
        show_upload_form()

def search_orders_for_photos(query: str):
    """搜索订单用于照片上传"""
    with st.spinner("正在搜索订单..."):
        # 首先尝试按客户姓名搜索
        result = api_client.search_orders_by_name(query)
        
        if result.get("success"):
            orders = result.get("data", [])
            if orders:
                # 过滤出非待处理状态的订单
                active_orders = [
                    order for order in orders 
                    if order.get('order_status') != '已完成'
                ]
                st.session_state.photo_search_results = active_orders
                if active_orders:
                    st.success(f"找到 {len(active_orders)} 个可上传照片的订单")
                else:
                    st.info(f"客户“{query}”的所有订单已完成，无法上传新照片")
            else:
                # 如果按姓名未找到，尝试从所有订单中搜索
                all_orders_result = api_client.get_orders(page=1, limit=100, status="all", search="")
                if all_orders_result.get("success"):
                    all_orders = all_orders_result.get("data", {}).get("orders", [])
                    # 按订单编号过滤
                    filtered_orders = [
                        order for order in all_orders 
                        if (query.lower() in order.get('order_number', '').lower() and 
                            order.get('order_status') != '已完成')
                    ]
                    
                    if filtered_orders:
                        st.session_state.photo_search_results = filtered_orders
                        st.success(f"找到 {len(filtered_orders)} 个可上传照片的订单")
                    else:
                        st.info(f"未找到包含“{query}”的未完成订单")
                        if 'photo_search_results' in st.session_state:
                            del st.session_state.photo_search_results
        else:
            show_error_message(
                result.get("message", "搜索失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def show_order_selection_for_photos():
    """显示订单选择（用于照片上传）"""
    st.markdown("---")
    st.markdown("### 选择要上传照片的订单")
    
    orders = st.session_state.photo_search_results
    
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
                    {order.get('order_number', '')}
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
                key=f"select_order_photo_{order.get('_id', i)}",
                width='stretch'
            ):
                st.session_state.selected_order_for_photos = order
                st.success(f"已选择订单：{order.get('order_number', '')}")
                st.rerun()

def show_upload_form():
    """显示照片上传表单"""
    order = st.session_state.selected_order_for_photos
    
    st.markdown("---")
    
    # 返回按钮
    if st.button("← 重新选择订单"):
        if 'selected_order_for_photos' in st.session_state:
            del st.session_state.selected_order_for_photos
        st.rerun()
    
    st.markdown(f"### 上传照片：{order.get('order_number', '')}")
    
    # 显示订单信息
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="color: #8B4B8C; margin: 0; margin-bottom: 0.5rem;">订单信息</h4>
        <p style="margin: 0; color: #666;">
            <strong>钻石类型：</strong>{order.get('diamond_type', '')} ({order.get('diamond_size', '')})<br>
            <strong>当前阶段：</strong>{order.get('current_stage', '')} (进度: {order.get('progress_percentage', 0)}%)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 上传表单
    with st.form("photo_upload_form", clear_on_submit=True):
        st.markdown("#### 选择照片信息")
        
        # 选择阶段
        stage_options = [stage["name"] for stage in PRODUCTION_STAGES]
        current_stage = order.get('current_stage', '')
        
        # 设置默认选中当前阶段
        default_index = 0
        if current_stage in stage_options:
            default_index = stage_options.index(current_stage)
        
        selected_stage = st.selectbox(
            "选择制作阶段",
            options=stage_options,
            index=default_index,
            help="选择照片所属的制作阶段"
        )
        
        # 文件上传
        uploaded_files = st.file_uploader(
            "选择照片文件",
            type=['jpg', 'jpeg', 'png', 'webp'],
            accept_multiple_files=True,
            help="支持JPG、PNG、WEBP格式，系统会自动压缩图片到80KB以下，最多同时上传1个文件"
        )
        
        # 照片描述
        description = st.text_area(
            "照片描述",
            placeholder="请描述照片内容（可选）",
            height=100,
            help="例如：原料准备阶段的细节照片、高温高压处理设备照片等"
        )
        
        # 提交按钮
        col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 2])
        
        with col_submit2:
            submitted = st.form_submit_button(
                "上传照片",
                type="primary"
            )
        
        if submitted:
            if uploaded_files:
                # 验证文件数量
                if len(uploaded_files) > 1:
                    st.error("最多同时上传 1 个文件")
                else:
                    # 验证文件大小和总大小
                    valid_files = []
                    total_size = 0
                    max_file_size = 100 * 1024  # 100KB单文件限制
                    max_total_size = 200 * 1024  # 200KB总限制（考虑Base64膨胀）
                    
                    for file in uploaded_files:
                        # 压缩图片
                        compressed_data = compress_image(file, max_size_kb=80)  # 压缩到80KB
                        compressed_size = len(compressed_data)
                        
                        # 检查单个文件大小
                        if compressed_size > max_file_size:
                            st.error(f"文件 {file.name} 压缩后仍超过 {max_file_size/1024:.0f}KB 限制")
                            continue
                        
                        # 创建压缩后的文件对象
                        compressed_file = io.BytesIO(compressed_data)
                        compressed_file.name = file.name
                        compressed_file.type = 'image/jpeg'
                        compressed_file.size = compressed_size
                        
                        # 考虑Base64编码会增加33%大小
                        estimated_size = compressed_size * 1.33
                        if total_size + estimated_size > max_total_size:
                            st.error(f"文件总大小超过 {max_total_size/1024:.0f}KB 限制，请减少文件数量")
                            break
                        
                        valid_files.append(compressed_file)
                        total_size += estimated_size
                        
                        # 显示压缩信息
                        if compressed_size < file.size:
                            compression_ratio = (1 - compressed_size / file.size) * 100
                            st.info(f"📷 {file.name}: {file.size/1024:.1f}KB → {compressed_size/1024:.1f}KB (压缩{compression_ratio:.0f}%)")
                        else:
                            st.info(f"📷 {file.name}: {file.size/1024:.1f}KB (无需压缩)")
                    
                    if valid_files:
                        st.info(f"准备上传 {len(valid_files)} 个文件，总大小约 {total_size/1024:.1f}KB")
                        upload_photos(
                            order.get('_id') or order.get('order_id'),
                            selected_stage,
                            valid_files,
                            description
                        )
            else:
                st.warning("请选择要上传的照片文件")

def upload_photos(order_id: str, stage_name: str, files: List, description: str):
    """上传照片"""
    # 找到对应的stage_id
    stage_id = None
    for stage in PRODUCTION_STAGES:
        if stage["name"] == stage_name:
            stage_id = stage["id"]
            break
    
    if not stage_id:
        st.error("未找到指定的制作阶段")
        return
    
    with st.spinner(f"正在上传 {len(files)} 个文件..."):
        try:
            # 通过服务层上传，内部已适配 CloudBase 客户端参数
            result = photo_service.upload_photos(
                order_id=order_id,
                stage_id=stage_id,
                stage_name=stage_name,
                photos=files,
                description=description
            )
            
            if result.get("success"):
                # 修复数据结构匹配
                uploaded_photos = result.get("data", {}).get("uploaded_files", [])
                
                if uploaded_photos and len(uploaded_photos) > 0:
                    show_success_message(
                        f"照片上传成功！共上传 {len(uploaded_photos)} 个文件",
                        f"阶段：{stage_name}\n描述：{description or '无'}"
                    )
                else:
                    st.warning("上传完成，但没有成功上传任何文件")
                    return
                
                # 显示上传结果
                st.markdown("#### 上传结果")
                for i, photo in enumerate(uploaded_photos):
                    st.markdown(f"""
                    <div style="
                        background: #f0f8ff;
                        padding: 0.8rem;
                        border-radius: 6px;
                        margin-bottom: 0.5rem;
                        border-left: 4px solid #52c41a;
                    ">
                        <div style="font-weight: bold; color: #333;">照片 {i+1}</div>
                        <div style="color: #666; font-size: 0.9rem;">
                            文件大小：{photo.get('file_size', 0) / 1024:.1f} KB<br>
                            上传时间：{format_datetime(photo.get('upload_time', datetime.now().isoformat()))}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
            else:
                error_msg = result.get("message", "照片上传失败")
                st.error(f"❌ 上传失败：{error_msg}")
                
                # 显示详细错误信息
                if result.get("data") and result.get("data").get("errors"):
                    st.markdown("#### 错误详情")
                    for error in result.get("data").get("errors", []):
                        st.error(f"文件 {error.get('file_id', '未知')}: {error.get('error', '未知错误')}")
                
        except Exception as e:
            st.error(f"上传过程中出现错误：{str(e)}")

def show_photo_management():
    """显示照片管理界面"""
    st.markdown("### 照片管理")
    st.info("此功能正在开发中，敬请期待...")
    
    # 照片管理功能预览
    st.markdown("""
    #### 即将推出的功能：
    
    - 🖼️ **照片浏览**：按订单和阶段浏览所有上传的照片
    - 📋 **照片列表**：查看所有照片的列表和详情
    - ✏️ **编辑照片**：修改照片描述和排序
    - 🗑️ **删除照片**：删除不需要的照片
    - 📥 **批量下载**：批量下载某个订单的所有照片
    - 📊 **照片统计**：查看照片上传统计和存储使用情况
    """)
    
    # 简单的照片查询功能
    st.markdown("---")
    st.markdown("#### 简单照片查询")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        photo_search_query = st.text_input(
            "搜索订单的照片",
            placeholder="输入订单编号或客户姓名",
            key="photo_management_search"
        )
    
    with col2:
        if st.button("🔍 查询照片"):
            if photo_search_query:
                st.info(f"正在查询“{photo_search_query}”的照片...")
                st.warning("照片查询功能正在开发中")
            else:
                st.warning("请输入搜索关键词")
    
    # 用户指南
    with st.expander("📝 照片上传指南"):
        st.markdown("""
        **照片上传注意事项：**
        
        1. **支持格式**：JPG、JPEG、PNG、WEBP
        2. **文件大小**：单个文件不超过10MB
        3. **数量限制**：每次最多上传5个文件
        4. **质量要求**：请上传清晰、真实的制作过程照片
        5. **命名建议**：使用有意义的文件名，如“订单001_原料准备_1.jpg”
        
        **各阶段照片建议：**
        
        - **订单确认**：客户签字确认单、订单信息表等
        - **原料准备**：原料照片、准备过程照片
        - **高温高压处理**：设备运行照片、处理过程照片
        - **切割打磨**：切割过程、打磨细节照片
        - **质量检测**：检测设备、检测报告照片
        - **包装完成**：成品照片、包装过程照片
        """)
    
    # 数据统计模拟
    st.markdown("---")
    st.markdown("#### 📊 系统统计（模拟数据）")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总照片数", "1,234", "+12")
    
    with col2:
        st.metric("存储用量", "2.5 GB", "+156 MB")
    
    with col3:
        st.metric("本月上传", "89", "+23")
    
    with col4:
        st.metric("平均文件大小", "2.1 MB", "-0.3 MB")