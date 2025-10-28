import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import re
import requests
import base64
from config import PRODUCTION_STAGES, STATUS_MAPPING, ORDER_STATUS_MAPPING

def translate_role(role: str) -> str:
    """将角色英文名翻译为中文"""
    role_map = {
        "admin": "管理员",
        "operator": "操作员",
        "viewer": "查看者"
    }
    return role_map.get(role, role)

def format_datetime(dt_str: str, format_type: str = "datetime") -> str:
    """格式化日期时间 - 自动转换UTC到北京时间(UTC+8)"""
    try:
        if not dt_str:
            return "-"
        
        # 处理不同的时间格式
        if isinstance(dt_str, datetime):
            # 如果已经是datetime对象，直接使用
            utc_time = dt_str
        else:
            # 字符串格式转换为datetime
            dt_str_clean = str(dt_str).replace('Z', '+00:00')
            utc_time = datetime.fromisoformat(dt_str_clean)
        
        # 如果datetime没有时区信息，假设是UTC
        if utc_time.tzinfo is None:
            from datetime import timezone
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        # 转换到北京时间 (UTC+8)
        from datetime import timedelta, timezone
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = utc_time.astimezone(beijing_tz)
        
        # 移除时区信息用于格式化
        beijing_time_naive = beijing_time.replace(tzinfo=None)
        
        if format_type == "date":
            return beijing_time_naive.strftime("%Y年%m月%d日")
        elif format_type == "time":
            return beijing_time_naive.strftime("%H:%M")
        elif format_type == "datetime":
            return beijing_time_naive.strftime("%Y年%m月%d日 %H:%M")
        elif format_type == "relative":
            now = datetime.now()
            diff = now - beijing_time_naive
            
            if diff.days > 0:
                return f"{diff.days}天前"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}小时前"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        else:
            return beijing_time_naive.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        # 如果转换失败，返回原始字符串
        return str(dt_str) if dt_str else "-"

def get_stage_info(stage_id: str) -> Dict[str, Any]:
    """获取阶段信息"""
    for stage in PRODUCTION_STAGES:
        if stage["id"] == stage_id:
            return stage
    return {
        "id": stage_id,
        "name": "未知阶段",
        "description": "",
        "estimated_days": 0,
        "color": "#f0f0f0"
    }

def get_status_info(status: str) -> Dict[str, Any]:
    """获取状态信息"""
    return STATUS_MAPPING.get(status, {
        "name": status,
        "color": "#666",
        "icon": "❓"
    })

def get_order_status_info(status: str) -> Dict[str, Any]:
    """获取订单状态信息"""
    return ORDER_STATUS_MAPPING.get(status, {
        "color": "#666",
        "icon": "❓"
    })

def render_progress_timeline(progress_data: List[Dict[str, Any]], current_stage: str = ""):
    """渲染进度时间轴"""
    st.markdown("#### 制作进度时间轴")
    
    # 按阶段顺序排序（如果数据中有stage_order）
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
        
        # 使用 Streamlit 原生组件
        with st.container():
            # 阶段标题和状态
            col1, col2 = st.columns([3, 1])
            with col1:
                if is_current:
                    st.markdown(f"### 🔵 {stage_name}")
                else:
                    st.markdown(f"### {stage_name}")
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
            
            # 阶段描述
            st.markdown(f"*{stage_info['description']}*")
            
            # 时间信息
            if started_at:
                st.caption(f"🕐 开始时间：{format_datetime(started_at, 'datetime')}")
            if completed_at:
                st.caption(f"✅ 完成时间：{format_datetime(completed_at, 'datetime')}")
            elif estimated_completion:
                st.caption(f"⏰ 预计完成：{format_datetime(estimated_completion, 'date')}")
            
            # 备注
            if notes:
                with st.expander("📝 备注"):
                    st.write(notes)
            
            # 分隔线（除了最后一个）
            if i < len(progress_data_sorted) - 1:
                st.divider()

def render_photo_gallery(photos_data: List[Dict[str, Any]], title: str = "制作过程照片"):
    """渲染照片廊"""
    if not photos_data:
        st.info("暂无制作过程照片")
        return
    
    st.markdown(f"#### {title}")
    
    for stage_photos in photos_data:
        stage_name = stage_photos.get("stage_name", "")
        photos = stage_photos.get("photos", [])
        
        if photos:
            # 更突出的阶段标题
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
                color: white;
                padding: 0.8rem 1.2rem;
                border-radius: 8px;
                margin: 1rem 0 0.5rem 0;
                font-size: 1.1rem;
                font-weight: bold;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                📸 {stage_name} ({len(photos)} 张照片)
            </div>
            """, unsafe_allow_html=True)
            
            # 使用列布局显示照片（每行最多6张，非常紧凑）
            cols = st.columns(min(len(photos), 6))
            
            for i, photo in enumerate(photos):
                with cols[i % 6]:
                    try:
                        st.image(
                            photo.get("thumbnail_url", photo.get("photo_url", "")),
                            caption=photo.get("description", f"上传时间：{format_datetime(photo.get('upload_time', ''), 'datetime')}"),
                            width=80  # 固定图片宽度
                        )
                        
                        # 照片操作按钮
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button(f"🔍 查看大图", key=f"view_{i}_{stage_name}"):
                                st.image(photo.get("photo_url", ""), caption=photo.get("description", ""))
                        
                        with col_btn2:
                            # 下载按钮
                            photo_url = photo.get("photo_url", "")
                            if photo_url:
                                if photo_url.startswith("data:image"):
                                    # Base64格式的图片
                                    st.download_button(
                                        "📥 下载",
                                        data=photo_url.split(",")[1],
                                        file_name=photo.get("file_name", f"photo_{i}.jpg"),
                                        mime="image/jpeg",
                                        key=f"download_{i}_{stage_name}",
                                        width='stretch'
                                    )
                                else:
                                    # 云存储URL
                                    st.download_button(
                                        "📥 下载",
                                        data=photo_url,
                                        file_name=photo.get("file_name", f"photo_{i}.jpg"),
                                        mime="image/jpeg",
                                        key=f"download_{i}_{stage_name}",
                                        width='stretch'
                                    )
                    except:
                        st.error("照片加载失败")
            
            st.markdown("---")

def render_order_card(order: Dict[str, Any], show_details: bool = True):
    """渲染订单卡片 - 客户查询页面专用"""
    order_status = order.get("order_status", "")
    status_info = get_order_status_info(order_status)
    progress = order.get("progress_percentage", 0)
    
    # 渲染美化的订单卡片
    st.markdown(f"""
<div style="background: linear-gradient(to right, #ffffff, #f8f9fa); border-left: 5px solid {status_info['color']}; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <div style="font-size: 1.2rem; font-weight: bold; color: #333;">📋 {order.get('order_number', '')}</div>
        <div style="background: {status_info['color']}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.9rem; font-weight: bold;">{status_info['icon']} {order_status}</div>
    </div>
    <div style="margin-bottom: 0.8rem;"><span style="color: #666; font-size: 0.9rem;">👤 客户：</span><span style="color: #333; font-weight: bold; font-size: 1.05rem;">{order.get('customer_name', '')}</span></div>
    <div style="margin-bottom: 0.8rem;"><span style="color: #666; font-size: 0.9rem;">💎 钻石：</span><span style="color: #333; font-weight: 500;">{order.get('diamond_type', '')} - {order.get('diamond_size', '')}</span></div>
    <div style="margin-bottom: 0.8rem;"><span style="color: #666; font-size: 0.9rem;">🔧 当前：</span><span style="color: #333; font-weight: 500;">{order.get('current_stage', '未开始')}</span></div>
    <div style="margin-bottom: 1rem;"><span style="color: #666; font-size: 0.9rem;">📅 下单：</span><span style="color: #333;">{format_datetime(order.get('created_at', ''), 'date')}</span></div>
    <div style="margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span style="color: #666; font-size: 0.85rem;">制作进度</span>
            <span style="color: {status_info['color']}; font-weight: bold; font-size: 0.95rem;">{progress}%</span>
        </div>
        <div style="background: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden;">
            <div style="background: {status_info['color']}; height: 100%; width: {progress}%; transition: width 0.3s ease;"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def show_success_message(message: str, details: str = ""):
    """显示成功消息"""
    st.success(message)
    if details:
        with st.expander("查看详情"):
            st.info(details)

def show_error_message(message: str, error_code: str = "", support_info: str = ""):
    """显示错误消息"""
    st.error(message)
    
    if error_code or support_info:
        col1, col2 = st.columns(2)
        with col1:
            if error_code:
                st.caption(f"错误代码：{error_code}")
        with col2:
            if support_info:
                st.caption(support_info)

def convert_to_dataframe(data: List[Dict[str, Any]], columns_mapping: Dict[str, str] = None) -> pd.DataFrame:
    """转换为 DataFrame 用于表格显示"""
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    if columns_mapping:
        df = df.rename(columns=columns_mapping)
    
    return df

def apply_custom_css():
    """应用自定义CSS样式"""
    st.markdown("""
    <style>
    /* 只隐藏顶部工具栏中的部分元素，保留侧边栏按钮 */
    header[data-testid="stHeader"] > div:nth-child(2) {
        display: none !important;
    }
    
    /* 隐藏Deploy、Rerun等按钮 */
    header[data-testid="stHeader"] button[kind="header"] {
        display: none !important;
    }
    
    /* 隐藏更多菜单 */
    header[data-testid="stHeader"] button[aria-label="View app menu"] {
        display: none !important;
    }
    
    /* 隐藏页面导航选择器 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* 隐藏页面链接 */
    section[data-testid="stSidebar"] ul[role="listbox"] {
        display: none !important;
    }
    
    /* 调整主内容区域，避免被遮挡 */
    .main .block-container {
        padding-top: 1rem;
    }
    
    /* 主题色彩 */
    .main {
        background-color: #fafafa;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(135deg, #8B4B8C 0%, #A569BD 100%);
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        min-width: 120px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #7D3C98 0%, #9B59B6 100%);
        box-shadow: 0 4px 12px rgba(139, 75, 140, 0.3);
        transform: translateY(-2px);
    }
    
    /* 让按钮容器居中 */
    .stButton {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0;
    }
    
    /* 表单提交按钮样式 */
    .stForm button[type="submit"] {
        width: auto !important;
        min-width: 150px;
        padding: 0.7rem 2.5rem !important;
        font-size: 1.05rem;
        border-radius: 8px;
    }
    
    /* 强制表单按钮居中 - 针对父容器 */
    .stForm {
        text-align: center !important;
    }
    
    /* 表单内容居中对齐 */
    .stForm > div {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }
    
    /* 输入框保持原宽度，左对齐 */
    .stForm .stTextInput,
    .stForm .stSelectbox,
    .stForm .stTextArea {
        width: 100% !important;
        text-align: left !important;
    }
    
    /* 表单内的columns容器（登录页的按钮组） */
    .stForm div[data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important;
    }
    
    /* 表单内的按钮 - 统一居中 */
    .stForm button[type="submit"] {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* 表单内columns中的按钮 */
    .stForm div[data-testid="column"] button {
        width: 100% !important;
        max-width: 200px !important;
    }
    
    /* 按钮组的布局优化 */
    div[data-testid="column"] .stButton {
        width: 100%;
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
        padding: 0.7rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8B4B8C;
        box-shadow: 0 0 0 4px rgba(139, 75, 140, 0.1);
        outline: none;
    }
    
    /* 输入框容器居中 */
    .stTextInput {
        max-width: 500px;
        margin: 0 auto;
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div > select {
        border-radius: 6px;
        border: 2px solid #e0e0e0;
    }
    
    /* 文件上传样式 */
    .stFileUploader > div {
        border-radius: 6px;
        border: 2px dashed #8B4B8C;
        background-color: #fafafa;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #8B4B8C 0%, #52c41a 100%);
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .main {
            padding: 1rem 0.5rem;
        }
        
        .stButton > button {
            width: 100%;
            margin-bottom: 10px;
        }
        
        .stSelectbox > div > div {
            font-size: 16px; /* 防止iOS的自动缩放 */
        }
    }
    
    /* 数据表样式 */
    .stDataFrame {
        border-radius: 6px;
        overflow: hidden;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* 警告和提示样式 */
    .stAlert {
        border-radius: 6px;
    }
    
    /* 移动端响应式优化 */
    @media (max-width: 768px) {
        /* === 整体布局优化 === */
        .main .block-container {
            padding: 1rem 0.5rem !important;
            max-width: 100% !important;
        }
        
        /* 防止横向滚动 */
        .main, .stApp {
            overflow-x: hidden !important;
            max-width: 100vw !important;
        }
        
        /* === 表单优化 === */
        /* 强制表单内的columns在移动端保持水平排列 */
        .stForm [data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }
        
        /* 强制表单内的行容器保持flex row */
        .stForm div[class*="row"] {
            flex-direction: row !important;
            display: flex !important;
        }
        
        /* 移动端按钮保持水平排列，但优化大小 */
        .stForm div[data-testid="column"] button {
            padding: 0.9rem 0.8rem !important;
            font-size: 0.9rem !important;
            min-width: auto !important;
            white-space: nowrap !important;
        }
        
        /* 移动端表单宽度优化 */
        .stForm {
            padding: 0 0.5rem !important;
        }
        
        /* === 按钮优化 === */
        .stButton > button {
            padding: 0.8rem 1rem !important;
            font-size: 0.95rem !important;
            min-width: auto !important;
            width: auto !important;
        }
        
        /* === 输入框优化 === */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px !important;
            padding: 0.8rem 1rem !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        .stTextInput, .stTextArea, .stSelectbox {
            max-width: 100% !important;
            width: 100% !important;
        }
        
        /* === Columns优化 === */
        div[data-testid="column"] {
            padding: 0 0.25rem !important;
            min-width: 0 !important;
        }
        
        /* === 卡片和容器优化 === */
        div[data-testid="stVerticalBlock"] > div {
            padding: 0.5rem !important;
        }
        
        /* === 图片优化 === */
        img {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* === 表格优化 === */
        .dataframe {
            font-size: 0.85rem !important;
            overflow-x: auto !important;
        }
        
        /* === Markdown内容优化 === */
        .stMarkdown {
            font-size: 0.95rem !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        
        /* === Expander优化 === */
        .streamlit-expanderHeader {
            font-size: 1rem !important;
        }
        
        /* === Metric优化 === */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        /* === 标题优化 === */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.3rem !important; }
        h4 { font-size: 1.1rem !important; }
        
        /* === 订单卡片优化 === */
        .order-card {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        
        /* === 侧边栏优化 === */
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
        
        section[data-testid="stSidebar"] .block-container {
            padding: 1rem 0.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 数据验证函数
def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email:
        return True  # 邮箱可以为空
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    if not phone:
        return False
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    # 检查是否包含字母和数字
    has_letter = re.search(r'[a-zA-Z]', password)
    has_digit = re.search(r'\d', password)
    
    if not has_letter or not has_digit:
        return False, "密码必须包含字母和数字"
    
    return True, "密码格式正确"

def validate_order_data(order_data: Dict[str, Any]) -> tuple[bool, str]:
    """验证订单数据"""
    required_fields = ['customer_name', 'customer_phone', 'diamond_type', 'diamond_size']
    
    for field in required_fields:
        if not order_data.get(field):
            return False, f"缺少必填字段: {field}"
    
    # 验证手机号
    if not validate_phone(order_data.get('customer_phone', '')):
        return False, "手机号格式不正确"
    
    # 验证邮箱
    if order_data.get('customer_email') and not validate_email(order_data.get('customer_email')):
        return False, "邮箱格式不正确"
    
    # 验证钻石大小
    diamond_size = order_data.get('diamond_size', '')
    if not re.match(r'^\d+(\.\d+)?克拉$', diamond_size):
        return False, "钻石大小格式不正确，应为数字+克拉"
    
    return True, "订单数据验证通过"

def validate_user_data(user_data: Dict[str, Any]) -> tuple[bool, str]:
    """验证用户数据"""
    required_fields = ['username', 'real_name', 'role']
    
    for field in required_fields:
        if not user_data.get(field):
            return False, f"缺少必填字段: {field}"
    
    # 验证用户名
    username = user_data.get('username', '')
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度应在3-20位之间"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    # 验证角色
    valid_roles = ['admin', 'operator', 'viewer']
    if user_data.get('role') not in valid_roles:
        return False, f"角色必须是以下之一: {', '.join(valid_roles)}"
    
    # 验证邮箱
    if user_data.get('email') and not validate_email(user_data.get('email')):
        return False, "邮箱格式不正确"
    
    return True, "用户数据验证通过"

def validate_progress_data(progress_data: Dict[str, Any]) -> tuple[bool, str]:
    """验证进度数据"""
    required_fields = ['order_id', 'stage_id', 'status']
    
    for field in required_fields:
        if not progress_data.get(field):
            return False, f"缺少必填字段: {field}"
    
    # 验证状态
    valid_statuses = ['pending', 'in_progress', 'completed']
    if progress_data.get('status') not in valid_statuses:
        return False, f"状态必须是以下之一: {', '.join(valid_statuses)}"
    
    return True, "进度数据验证通过"

def sanitize_input(text: str) -> str:
    """清理用户输入，防止XSS攻击"""
    if not text:
        return ""
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 转义特殊字符
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text.strip()

def validate_file_upload(file) -> tuple[bool, str]:
    """验证文件上传"""
    if not file:
        return False, "请选择文件"
    
    # 检查文件大小 (5MB限制)
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        return False, "文件大小不能超过5MB"
    
    # 检查文件类型
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if file.type not in allowed_types:
        return False, "只支持JPEG、PNG、GIF格式的图片"
    
    return True, "文件验证通过"

@st.cache_data(ttl=3600)
def download_photo_from_url(photo_url: str) -> bytes:
    """从URL下载照片内容（带缓存，1小时）"""
    try:
        if photo_url.startswith("http"):
            response = requests.get(photo_url, timeout=10)
            if response.status_code == 200:
                return response.content
        elif photo_url.startswith("data:image"):
            # 处理base64编码的图片
            return base64.b64decode(photo_url.split(",")[1])
    except Exception as e:
        print(f"下载照片失败: {str(e)}")
    return b""