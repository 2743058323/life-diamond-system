import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    show_error_message,
    format_datetime,
    convert_to_dataframe,
    translate_role
)
from datetime import datetime, timedelta
import pandas as pd

def show_page():
    """操作日志页面"""
    # 权限检查（使用仪表板权限，因为数据来源是仪表板）
    if not auth_manager.require_permission("dashboard.view"):
        return
    
    # 标题和刷新按钮
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title("📋 操作日志")
    with col_refresh:
        if st.button("🔄 刷新数据", type="primary"):
            st.session_state.refresh_logs = True
            st.rerun()
    
    st.markdown("查看系统所有操作记录")
    
    # 加载日志数据
    logs_data = load_operation_logs()
    
    if logs_data:
        # 渲染筛选器
        render_filters(logs_data)
        
        # 渲染日志列表
        render_logs_list()
    else:
        st.info("暂无操作日志记录")

def load_operation_logs():
    """加载操作日志数据"""
    if 'operation_logs' not in st.session_state or st.session_state.get('refresh_logs', False):
        with st.spinner("正在加载操作日志..."):
            # 只从云函数获取日志数据
            result = api_client.get_operation_logs()
            
            if result.get("success"):
                data = result.get("data", {})
                logs = data.get("logs", [])
                st.session_state.operation_logs = logs
            else:
                # 如果云函数失败，不显示任何数据
                st.session_state.operation_logs = []
                # 静默处理 404 错误（HTTP 触发器未配置）
                status_code = result.get("status_code", 0)
                if status_code != 404:
                    show_error_message(
                        result.get("message", "日志加载失败"),
                        error_code=str(status_code),
                        support_info="请检查云函数配置"
                    )
            st.session_state.refresh_logs = False
    
    return st.session_state.get("operation_logs", [])

def render_filters(logs_data):
    """渲染筛选器"""
    st.markdown("### 🔍 筛选条件")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 操作类型筛选
        operation_types = [
            "全部", 
            "用户登录",
            "订单创建", 
            "订单更新", 
            "订单删除", 
            "阶段开始", 
            "阶段完成",
            "用户创建",
            "用户更新",
            "用户删除",
            "照片上传",
            "权限管理",
            "角色创建"
        ]
        selected_type = st.selectbox("操作类型", operation_types)
    
    with col2:
        # 订单编号搜索
        order_number = st.text_input("订单编号", placeholder="如: LD20251026107650")
    
    with col3:
        # 客户姓名搜索
        customer_name = st.text_input("客户姓名")
    
    with col4:
        # 操作人搜索
        operator = st.text_input("操作人")
    
    col5, col6 = st.columns(2)
    
    with col5:
        # 日期范围筛选
        date_range = st.selectbox("时间范围", 
            ["全部", "今天", "昨天", "最近7天", "最近30天", "自定义"])
    
    with col6:
        # 自定义日期范围
        if date_range == "自定义":
            date_from = st.date_input("开始日期", value=datetime.now() - timedelta(days=30), key="date_from")
            date_to = st.date_input("结束日期", value=datetime.now(), key="date_to")
        else:
            date_from = None
            date_to = None
    
    # 搜索按钮
    col_button, col_info = st.columns([1, 5])
    with col_button:
        if st.button("🔍 搜索", type="primary"):
            st.session_state['search_applied'] = True
    
    # 应用筛选
    if st.session_state.get('search_applied', False):
        filtered_logs = apply_filters(
            logs_data,
            selected_type,
            date_range,
            order_number,
            customer_name,
            operator,
            date_from,
            date_to
        )
        
        st.session_state.filtered_logs = filtered_logs
        
        # 显示筛选结果统计
        st.caption(f"📊 找到 {len(filtered_logs)} 条记录")
    else:
        # 首次加载显示所有记录
        st.session_state.filtered_logs = logs_data
        st.caption(f"📊 共 {len(logs_data)} 条记录")

def apply_filters(logs, type_filter, date_range, order_number, customer_name, operator, date_from, date_to):
    """应用筛选条件"""
    filtered = logs
    
    # 操作类型筛选
    if type_filter != "全部":
        filtered = [log for log in filtered if log.get('type') == type_filter]
    
    # 时间范围筛选
    now = datetime.now()
    if date_range == "今天":
        filtered = [log for log in filtered if is_same_day(log.get('timestamp'), now)]
    elif date_range == "昨天":
        yesterday = now - timedelta(days=1)
        filtered = [log for log in filtered if is_same_day(log.get('timestamp'), yesterday)]
    elif date_range == "最近7天":
        week_ago = now - timedelta(days=7)
        filtered = [log for log in filtered if is_after_date(log.get('timestamp'), week_ago)]
    elif date_range == "最近30天":
        month_ago = now - timedelta(days=30)
        filtered = [log for log in filtered if is_after_date(log.get('timestamp'), month_ago)]
    elif date_range == "自定义" and date_from and date_to:
        filtered = [log for log in filtered if is_in_date_range(log.get('timestamp'), date_from, date_to)]
    
    # 订单编号筛选
    if order_number and order_number.strip():
        filtered = [log for log in filtered if order_number.lower() in log.get('order_number', '').lower()]
    
    # 客户姓名筛选（从详细信息的metadata中查找）
    if customer_name and customer_name.strip():
        filtered = [log for log in filtered 
                   if customer_name.lower() in log.get('description', '').lower() or 
                      customer_name.lower() in str(log.get('metadata', {})).lower()]
    
    # 操作人筛选
    if operator and operator.strip():
        filtered = [log for log in filtered if operator.lower() in log.get('operator', '').lower()]
    
    return filtered

def is_same_day(timestamp_str, date):
    """判断是否同一天"""
    if not timestamp_str:
        return False
    try:
        log_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return log_date.date() == date.date()
    except:
        return False

def is_after_date(timestamp_str, date):
    """判断是否在日期之后"""
    if not timestamp_str:
        return False
    try:
        log_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return log_date.date() >= date.date()
    except:
        return False

def is_in_date_range(timestamp_str, date_from, date_to):
    """判断是否在日期范围内"""
    if not timestamp_str:
        return False
    try:
        log_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).date()
        return date_from <= log_date <= date_to
    except:
        return False

def render_logs_list():
    """渲染日志列表"""
    st.markdown("### 📝 操作记录")
    
    filtered_logs = st.session_state.get("filtered_logs", [])
    
    if filtered_logs:
        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", len(filtered_logs))
        with col2:
            st.metric("今日操作", count_today_operations(filtered_logs))
        with col3:
            # 导出Excel按钮
            export_excel_button(filtered_logs)
        
        # 准备表格数据
        table_data = []
        for log in filtered_logs:
            row = {
                '操作时间': format_datetime(log.get('timestamp'), 'datetime') if log.get('timestamp') else '',
                '操作类型': log.get('type', ''),
                '操作人': log.get('operator', ''),
                '操作描述': log.get('description', ''),
                '订单编号': log.get('order_number', ''),
                '详细信息': format_metadata_readable(log.get('metadata', {}))
            }
            table_data.append(row)
        
        # 转换为DataFrame并显示
        df = pd.DataFrame(table_data)
        
        st.dataframe(
            df,
            hide_index=True,
            height=600,
            column_config={
                '详细信息': st.column_config.TextColumn(
                    '详细信息',
                    width='large',
                    help='点击单元格可查看完整内容'
                )
            }
        )
    else:
        st.info("没有符合条件的操作记录")

def format_metadata_readable(metadata):
    """格式化元数据为表格中易读的格式（使用换行）"""
    if not metadata or not isinstance(metadata, dict):
        return ''
    
    # 需要排除的技术性字段（对用户没有实际意义）
    exclude_fields = {'_id', 'user_id', 'stage_id', 'role_id', 'permission_id', 'order_id'}
    
    parts = []
    for key, value in metadata.items():
        # 跳过技术性字段
        if key in exclude_fields:
            continue
            
        # 翻译常见的英文键
        key_map = {
            'customer_name': '客户姓名',
            'customer_phone': '联系电话',
            'customer_email': '邮箱',
            'diamond_type': '钻石类型',
            'diamond_size': '钻石大小',
            'order_status': '订单状态',
            'special_requirements': '特殊要求',
            'notes': '备注',
            'stage_name': '制作阶段',
            'status': '状态',
            'progress_percentage': '完成进度',
            'username': '用户名',
            'real_name': '真实姓名',
            'role': '角色',
            'email': '邮箱',
            'password': '密码',
            'file_count': '照片数量',
            'role_name': '角色名称',
            'display_name': '显示名称',
            'permission_count': '权限数量',
            'permission_code': '权限代码',
            'permission_name': '权限名称',
            'updated_at': '更新时间',
            'is_active': '账户状态'
        }
        display_key = key_map.get(key, key)
        
        # 特殊值翻译（但不翻译已经包含"原值"对比的字符串）
        if isinstance(value, str) and '(原值:' in value:
            # 已经是对比格式，直接使用
            pass
        elif key == 'role' or display_key == '角色':
            value = translate_role(value)
        elif key == 'is_active' or display_key == '账户状态':
            if isinstance(value, bool):
                value = '启用' if value else '禁用'
        elif isinstance(value, list):
            # 如果值是列表，转换为字符串
            value = ', '.join(str(v) for v in value)
        
        parts.append(f"{display_key}: {value}")
    
    # 使用换行符分隔，让表格中显示更清晰
    return "\n".join(parts) if parts else ''

def count_today_operations(logs):
    """统计今日操作数"""
    today = datetime.now().date()
    count = 0
    for log in logs:
        if log.get('timestamp'):
            try:
                log_date = datetime.fromisoformat(log.get('timestamp').replace('Z', '+00:00')).date()
                if log_date == today:
                    count += 1
            except:
                pass
    return count

def export_excel_button(logs):
    """导出Excel按钮"""
    try:
        # 准备显示数据
        export_data = []
        for log in logs:
            export_data.append({
                '操作时间': format_datetime(log.get('timestamp'), 'datetime') if log.get('timestamp') else '',
                '操作类型': log.get('type', ''),
                '操作人': log.get('operator', ''),
                '操作描述': log.get('description', ''),
                '订单编号': log.get('order_number', ''),
                '详细信息': format_metadata_readable(log.get('metadata', {}))
            })
        
        df = pd.DataFrame(export_data)
        
        # 导出到内存
        from io import BytesIO
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        # 生成文件名
        filename = f"操作日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 提供下载按钮
        st.download_button(
            label="📥 导出Excel",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch'
        )
    except ImportError:
        st.error("❌ 缺少 openpyxl 包，请安装：pip install openpyxl")
    except Exception as e:
        st.error(f"❌ 导出失败: {str(e)}")

