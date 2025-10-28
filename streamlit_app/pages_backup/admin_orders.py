import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    render_order_card,
    show_error_message,
    show_success_message,
    format_datetime,
    convert_to_dataframe
)
from datetime import datetime, date
import pandas as pd
from services.order_service import OrderService


# 服务实例
order_service = OrderService(api_client)

class OrderPageState:
    KEY = "order_page_state"
    @classmethod
    def get(cls):
        if cls.KEY not in st.session_state:
            st.session_state[cls.KEY] = {
                "status_filter": "all",
                "search": "",
                "page": 1,
                "page_size": 20,
                "view_mode": "卡片模式",
                "editing_id": None,
                "delete_confirm_id": None,
            }
        return st.session_state[cls.KEY]

def show_page():
    """订单管理页面"""
    # 权限检查
    if not auth_manager.require_permission("orders.read"):
        return
    
    st.title("📝 订单管理")
    st.markdown("管理所有生命钻石订单，包括创建、编辑和查看订单信息")
    
    # 页面模式选择
    tab1, tab2 = st.tabs(["📄 订单列表", "➕ 新建订单"])
    
    with tab1:
        show_orders_list()
    
    with tab2:
        if auth_manager.has_permission("orders.create"):
            show_create_order_form()
        else:
            st.error("您没有创建订单的权限")

def show_orders_list():
    """显示订单列表"""
    # 查询条件
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "订单状态",
            options=["all", "待处理", "制作中", "已完成", "已删除"],
            format_func=lambda x: "全部" if x == "all" else x,
            key="order_status_filter"
        )
    
    with col2:
        search_query = st.text_input(
            "搜索客户姓名",
            placeholder="输入客户姓名",
            key="order_search_query"
        )
    
    with col3:
        page_size = st.selectbox(
            "每页显示",
            options=[10, 20, 50],
            index=1,
            key="order_page_size"
        )
    
    with col4:
        refresh_clicked = st.button("🔄 刷新", width='stretch')
    
    state = OrderPageState.get()
    changed = (
        state.get("status_filter") != status_filter or
        state.get("search") != search_query or
        state.get("page_size") != page_size
    )
    if changed or refresh_clicked:
        state["status_filter"] = status_filter
        state["search"] = search_query
        state["page_size"] = page_size
        state["page"] = 1
        api_status = "deleted" if status_filter == "已删除" else status_filter
        load_orders(1, page_size, api_status, search_query)
    
    # 加载订单数据（首次进入或无数据）
    if 'orders_data' not in st.session_state and not refresh_clicked and not changed:
        api_status = "deleted" if status_filter == "已删除" else status_filter
        load_orders(state.get("page", 1), page_size, api_status, search_query)
    
    # 显示订单列表
    if 'orders_data' in st.session_state:
        render_orders_list()
    else:
        st.info("正在加载订单数据...")

def load_orders(page: int, limit: int, status: str, search: str):
    """加载订单数据"""
    with st.spinner("正在加载订单数据..."):
        result = order_service.list_orders(
            page=page,
            limit=limit,
            status=status,
            search=search
        )
        
        if result.get("success"):
            # 处理嵌套的数据结构
            data = result.get("data", {})
            if isinstance(data, dict) and data.get("success"):
                st.session_state.orders_data = data.get("data", {})
            else:
                st.session_state.orders_data = data
        else:
            show_error_message(
                result.get("message", "订单数据加载失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )

def render_orders_list():
    """渲染订单列表"""
    orders_data = st.session_state.orders_data
    orders = orders_data.get("orders", [])
    pagination = orders_data.get("pagination", {})
    
    if not orders:
        st.info("没有找到符合条件的订单")
        return
    
    # 显示统计信息
    total_count = pagination.get("total_count", 0)
    current_page = pagination.get("current_page", 1)
    total_pages = pagination.get("total_pages", 1)
    
    st.markdown(f"**找到 {total_count} 个订单，当前第 {current_page}/{total_pages} 页**")
    
    # 订单列表显示模式
    state = OrderPageState.get()
    view_mode = st.radio(
        "显示模式",
        options=["卡片模式", "表格模式"],
        horizontal=True,
        key="orders_view_mode"
    )
    state["view_mode"] = view_mode
    
    # 软删除本地过滤：未选择“已删除”时隐藏已删除；选择“已删除”仅显示已删除
    filter_status = state.get("status_filter", "all")
    if filter_status == "已删除":
        orders = [o for o in orders if o.get("is_deleted")]
    else:
        orders = [o for o in orders if not o.get("is_deleted")]

    if view_mode == "卡片模式":
        render_orders_cards(orders)
    else:
        render_orders_table(orders)
    
    # 分页导航
    if total_pages > 1:
        render_pagination(pagination)

def render_orders_cards(orders: list):
    """渲染订单卡片"""
    for i, order in enumerate(orders):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            render_order_card(order)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 查看详情按钮
            if st.button("🔍", key=f"view_{order.get('_id', i)}", width='stretch', help="查看详情", type="primary"):
                st.session_state.selected_order_id = order.get('_id')
                st.session_state.admin_page = "订单详情"
                st.rerun()
            
            # 编辑按钮
            if auth_manager.has_permission("orders.update"):
                if st.button("✏️", key=f"edit_{order.get('_id', i)}", width='stretch', help="编辑订单"):
                    state = OrderPageState.get()
                    state["editing_id"] = order.get('_id')
                    st.rerun()
            
            # 删除按钮
            if auth_manager.has_permission("orders.delete"):
                if st.button("🗑️", key=f"delete_{order.get('_id', i)}", width='stretch', type="secondary", help="删除订单"):
                    state = OrderPageState.get()
                    state["delete_confirm_id"] = order.get('_id')
                    st.rerun()
        
        # 显示编辑表单（如果有待编辑的订单）
        state = OrderPageState.get()
        if state.get("editing_id") == order.get('_id'):
            show_edit_order_form(order)
        
        # 显示删除确认（如果有待删除的订单）
        if state.get("delete_confirm_id") == order.get('_id'):
            show_delete_confirmation(order)
        
        st.markdown("---")

def render_orders_table(orders: list):
    """渲染订单表格（简洁版 st.dataframe）"""
    # 转换为DataFrame
    df = convert_to_dataframe(orders, {
        'customer_name': '客户姓名',
        'customer_phone': '联系电话',
        'customer_email': '邮箱',
        'diamond_type': '钻石类型',
        'diamond_size': '钻石大小',
        'special_requirements': '特殊要求',
        'order_status': '订单状态',
        'current_stage': '当前阶段',
        'progress_percentage': '进度(%)',
        'estimated_completion': '预计完成日期',
        'notes': '备注',
        'created_at': '创建时间',
        'updated_at': '更新时间'
    })

    # 删除不需要的列（如果没有重命名，直接删除）
    columns_to_drop = ['_id', 'order_number']
    for col in columns_to_drop:
        if col in df.columns:
            df = df.drop(columns=[col])

    # 格式化时间列
    if '创建时间' in df.columns:
        df['创建时间'] = df['创建时间'].apply(
            lambda x: format_datetime(x, 'date')
        )
    
    if '更新时间' in df.columns:
        df['更新时间'] = df['更新时间'].apply(
            lambda x: format_datetime(x, 'datetime')
        )
    
    if '预计完成日期' in df.columns:
        df['预计完成日期'] = df['预计完成日期'].apply(
            lambda x: format_datetime(x, 'date') if x and x != 'None' else ''
        )

    st.dataframe(
        df,
        width='stretch',
        hide_index=True
    )

def render_pagination(pagination: dict):
    """渲染分页导航"""
    current_page = pagination.get("current_page", 1)
    total_pages = pagination.get("total_pages", 1)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("上一页", disabled=current_page <= 1):
            new_page = current_page - 1
            state = OrderPageState.get()
            state["page"] = new_page
            api_status = "deleted" if state.get("status_filter", "all") == "已删除" else state.get("status_filter", "all")
            load_orders(
                new_page,
                state.get("page_size", 20),
                api_status,
                state.get("search", "")
            )
    
    with col2:
        if st.button("下一页", disabled=current_page >= total_pages):
            new_page = current_page + 1
            state = OrderPageState.get()
            state["page"] = new_page
            api_status = "deleted" if state.get("status_filter", "all") == "已删除" else state.get("status_filter", "all")
            load_orders(
                new_page,
                state.get("page_size", 20),
                api_status,
                state.get("search", "")
            )
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 0.25rem;'>第 {current_page} / {total_pages} 页</div>", unsafe_allow_html=True)
    
    with col4:
        page_input = st.number_input(
            "跳转到",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            key="page_jump_input"
        )
    
    with col5:
        if st.button("跳转"):
            if page_input != current_page:
                state = OrderPageState.get()
                state["page"] = int(page_input)
                api_status = "deleted" if state.get("status_filter", "all") == "已删除" else state.get("status_filter", "all")
                load_orders(
                    int(page_input),
                    state.get("page_size", 20),
                    api_status,
                    state.get("search", "")
                )

def show_create_order_form():
    """显示创建订单表单"""
    st.markdown("### 新建订单")
    
    with st.form("create_order_form", clear_on_submit=True):
        # 基本信息
        st.markdown("#### 客户信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input(
                "客户姓名 *",
                placeholder="请输入客户姓名",
                help="必填项目"
            )
            
            customer_phone = st.text_input(
                "联系电话 *",
                placeholder="请输入联系电话",
                help="必填项目"
            )
        
        with col2:
            customer_email = st.text_input(
                "邮箱地址",
                placeholder="请输入邮箱地址（可选）"
            )
        
        st.markdown("#### 产品信息")
        
        col3, col4 = st.columns(2)
        
        with col3:
            diamond_type = st.selectbox(
                "钻石类型 *",
                options=["纪念钻石", "定制钻石", "特殊定制"],
                help="选择钻石类型"
            )
            
            diamond_size = st.selectbox(
                "钻石大小 *",
                options=["0.5克拉", "1克拉", "1.5克拉", "2克拉", "2.5克拉", "3克拉"],
                help="选择钻石大小"
            )
        
        with col4:
            estimated_completion = st.date_input(
                "预计完成日期",
                value=None,
                help="选择预计完成日期（可选）"
            )
        
        special_requirements = st.text_area(
            "特殊要求",
            placeholder="请输入特殊要求（如刻字内容等）",
            height=100
        )
        
        notes = st.text_area(
            "备注信息",
            placeholder="请输入备注信息（可选）",
            height=100
        )
        
        # 提交按钮
        col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 2])
        
        with col_submit2:
            submitted = st.form_submit_button(
                "创建订单",
                width='stretch',
                type="primary"
            )
        
        if submitted:
            # 验证必填字段
            if not all([customer_name, customer_phone, diamond_type, diamond_size]):
                st.error("请填写所有必填字段（标有 * 的字段）")
            else:
                create_order({
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "customer_email": customer_email,
                    "diamond_type": diamond_type,
                    "diamond_size": diamond_size,
                    "special_requirements": special_requirements,
                    "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
                    "notes": notes
                })

def create_order(order_data: dict):
    """创建订单"""
    with st.spinner("正在创建订单..."):
        # 新建订单默认软删除标记为 False
        if isinstance(order_data, dict) and "is_deleted" not in order_data:
            order_data["is_deleted"] = False
        result = order_service.create_order(order_data)
        
        if result.get("success"):
            data = result.get("data", {})
            show_success_message(
                f"订单创建成功！订单编号：{data.get('order_number', '')}",
                f"订单ID：{data.get('order_id', '')}"
            )
            
            # 清除缓存的订单数据，强制刷新
            if 'orders_data' in st.session_state:
                del st.session_state.orders_data
            
            # 自动切换到订单列表
            st.info("正在刷新订单列表...")
            
        else:
            show_error_message(
                result.get("message", "订单创建失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请检查输入信息后重试"
            )

def show_edit_order_form(order: dict):
    """显示编辑订单表单"""
    st.markdown("### ✏️ 编辑订单")
    
    with st.form("edit_order_form", clear_on_submit=False):
        # 基本信息
        st.markdown("#### 客户信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input(
                "客户姓名 *",
                value=order.get('customer_name', ''),
                placeholder="请输入客户姓名",
                help="必填项目"
            )
            
            customer_phone = st.text_input(
                "联系电话 *",
                value=order.get('customer_phone', ''),
                placeholder="请输入联系电话",
                help="必填项目"
            )
        
        with col2:
            customer_email = st.text_input(
                "邮箱地址",
                value=order.get('customer_email', ''),
                placeholder="请输入邮箱地址（可选）"
            )
        
        st.markdown("#### 产品信息")
        
        col3, col4 = st.columns(2)
        
        with col3:
            diamond_type = st.selectbox(
                "钻石类型 *",
                options=["纪念钻石", "定制钻石", "特殊定制"],
                index=["纪念钻石", "定制钻石", "特殊定制"].index(order.get('diamond_type', '纪念钻石')),
                help="选择钻石类型"
            )
            
            diamond_size = st.selectbox(
                "钻石大小 *",
                options=["0.5克拉", "1克拉", "1.5克拉", "2克拉", "2.5克拉", "3克拉"],
                index=["0.5克拉", "1克拉", "1.5克拉", "2克拉", "2.5克拉", "3克拉"].index(order.get('diamond_size', '1克拉')),
                help="选择钻石大小"
            )
        
        with col4:
            order_status = st.selectbox(
                "订单状态 *",
                options=["待处理", "制作中", "已完成"],
                index=["待处理", "制作中", "已完成"].index(order.get('order_status', '待处理')),
                help="选择订单状态"
            )
            
            estimated_completion = st.date_input(
                "预计完成日期",
                value=datetime.strptime(order.get('estimated_completion', ''), '%Y-%m-%d').date() if order.get('estimated_completion') and order.get('estimated_completion') != '' else None,
                help="选择预计完成日期（可选）"
            )
        
        special_requirements = st.text_area(
            "特殊要求",
            value=order.get('special_requirements', ''),
            placeholder="请输入特殊要求（如刻字内容等）",
            height=100
        )
        
        notes = st.text_area(
            "备注信息",
            value=order.get('notes', ''),
            placeholder="请输入备注信息（可选）",
            height=100
        )
        
        # 提交按钮（只保留保存按钮在表单内）
        if st.form_submit_button("💾 保存修改", width='stretch', type="primary"):
            # 验证必填字段
            if not all([customer_name, customer_phone, diamond_type, diamond_size]):
                st.error("请填写所有必填字段（标有 * 的字段）")
            else:
                update_order_data = {
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "customer_email": customer_email,
                    "diamond_type": diamond_type,
                    "diamond_size": diamond_size,
                    "order_status": order_status,
                    "special_requirements": special_requirements,
                    "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
                    "notes": notes
                }
                update_order(order.get('_id'), update_order_data)
    
    # 取消按钮放在表单外面
    if st.button("❌ 取消编辑", key=f"cancel_edit_{order.get('_id')}", width='stretch', type="secondary"):
        # 清除编辑状态
        state = OrderPageState.get()
        state["editing_id"] = None
        st.rerun()

def show_delete_confirmation(order: dict):
    """显示删除确认"""
    st.warning(f"⚠️ 确定要删除订单 **{order.get('order_number', '')}** 吗？")
    st.info(f"客户：{order.get('customer_name', '')} | 钻石类型：{order.get('diamond_type', '')} | 大小：{order.get('diamond_size', '')}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ 确认删除", key=f"confirm_delete_{order.get('_id')}", width='stretch', type="primary"):
            delete_order(order.get('_id'))
    
    with col2:
        if st.button("❌ 取消", key=f"cancel_delete_{order.get('_id')}", width='stretch'):
            state = OrderPageState.get()
            state["delete_confirm_id"] = None
            st.rerun()
    
    with col3:
        st.empty()

def update_order(order_id: str, order_data: dict):
    """更新订单"""
    with st.spinner("正在更新订单..."):
        result = order_service.update_order(order_id, order_data)
        
        if result.get("success"):
            show_success_message(
                "订单更新成功！",
                f"订单编号：{order_data.get('order_number', '')}"
            )
            
            state = OrderPageState.get()
            state["editing_id"] = None
            
            # 清除缓存的订单数据，强制刷新
            if 'orders_data' in st.session_state:
                del st.session_state.orders_data
            
            st.rerun()
            
        else:
            show_error_message(
                result.get("message", "订单更新失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请检查输入信息后重试"
            )

def delete_order(order_id: str):
    """删除订单"""
    with st.spinner("正在删除订单..."):
        result = order_service.delete_order(order_id)
        
        if result.get("success"):
            show_success_message(
                "订单删除成功！",
                "订单已被标记为已删除"
            )
            
            state = OrderPageState.get()
            state["delete_confirm_id"] = None
            
            # 清除缓存的订单数据，强制刷新
            if 'orders_data' in st.session_state:
                del st.session_state.orders_data
            
            st.rerun()
            
        else:
            show_error_message(
                result.get("message", "订单删除失败"),
                error_code=str(result.get("status_code", "")),
                support_info="请稍后重试"
            )