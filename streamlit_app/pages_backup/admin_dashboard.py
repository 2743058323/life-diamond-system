import streamlit as st
from utils.cloudbase_client import api_client
from utils.auth import auth_manager
from utils.helpers import (
    show_error_message,
    format_datetime,
    convert_to_dataframe
)
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_page():
    """管理仪表板页面"""
    # 权限检查
    if not auth_manager.require_permission("dashboard.view"):
        return
    
    st.title("📊 数据仪表板")
    st.markdown("实时查看系统运营数据和关键指标")
    
    # 加载仪表板数据
    load_dashboard_data()
    
    if 'dashboard_data' in st.session_state:
        render_dashboard()
    else:
        st.info("正在加载数据...") 

def load_dashboard_data():
    """加载仪表板数据"""
    # 在页面加载时或用户点击刷新时加载数据
    if 'dashboard_data' not in st.session_state or st.button("🔄 刷新数据", type="secondary", key="dashboard_refresh_top"):
        with st.spinner("正在加载仪表板数据..."):
            result = api_client.get_dashboard_data()
            
            if result.get("success"):
                # 处理嵌套的数据结构
                data = result.get("data", {})
                if isinstance(data, dict) and data.get("success"):
                    st.session_state.dashboard_data = data.get("data", {})
                else:
                    st.session_state.dashboard_data = data
                st.session_state.dashboard_last_update = datetime.now()
            else:
                show_error_message(
                    result.get("message", "数据加载失败"),
                    error_code=str(result.get("status_code", "")),
                    support_info="请稍后重试"
                )

def render_dashboard():
    """渲染仪表板"""
    data = st.session_state.dashboard_data
    overview = data.get("overview", {})
    stage_stats = data.get("stage_stats", {})
    
    # 显示最后更新时间
    if 'dashboard_last_update' in st.session_state:
        last_update = st.session_state.dashboard_last_update
        # 直接格式化本地时间，不进行时区转换
        formatted_time = last_update.strftime("%Y年%m月%d日 %H:%M:%S")
        st.caption(f"最后更新：{formatted_time}")
    
    # 核心指标卡片
    render_metrics_cards(overview)
    
    st.markdown("---")
    
    # 统计图表区域
    col1, col2 = st.columns(2)
    
    with col1:
        render_order_status_chart(overview)
        render_completion_trend_chart(data)
    
    with col2:
        render_stage_distribution_chart(stage_stats)
    
    st.markdown("---")
    
    # 快捷操作
    st.markdown("### ⚡ 快捷操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ 新建订单"):
            st.session_state.admin_page = "订单管理"
            st.rerun()
    
    with col2:
        if st.button("📋 订单列表"):
            st.session_state.admin_page = "订单管理"
            st.rerun()
    
    with col3:
        if st.button("🔄 刷新数据", key="dashboard_refresh_quick"):
            if 'dashboard_data' in st.session_state:
                del st.session_state.dashboard_data
            st.rerun()

def render_metrics_cards(overview: dict):
    """渲染指标卡片"""
    st.markdown("### 📈 核心指标")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{overview.get('total_orders', 0)}</h2>
            <p style="margin: 0; opacity: 0.9;">总订单数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{overview.get('in_progress_orders', 0)}</h2>
            <p style="margin: 0; opacity: 0.9;">制作中</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{overview.get('completed_orders', 0)}</h2>
            <p style="margin: 0; opacity: 0.9;">已完成</p>
        </div>
        """, unsafe_allow_html=True)
    
    today_completed = overview.get('today_completed', 0)
    with col4:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{today_completed}</h2>
            <p style="margin: 0; opacity: 0.9;">今日完成</p>
        </div>
        """, unsafe_allow_html=True)
    
    this_month_completed = overview.get('this_month_completed', 0)
    with col5:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #faad14 0%, #fadb14 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{this_month_completed}</h2>
            <p style="margin: 0; opacity: 0.9;">本月完成</p>
        </div>
        """, unsafe_allow_html=True)
    
    avg_completion_time = overview.get('avg_completion_time', 0)
    with col6:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; font-size: 2rem;">{avg_completion_time}</h2>
            <p style="margin: 0; opacity: 0.9;">平均耗时(天)</p>
        </div>
        """, unsafe_allow_html=True)

def render_order_status_chart(overview: dict):
    """渲染订单状态分布图"""
    st.markdown("#### 📊 订单状态分布")
    
    status_data = {
        "待处理": overview.get('pending_orders', 0),
        "制作中": overview.get('in_progress_orders', 0),
        "已完成": overview.get('completed_orders', 0)
    }
    
    if sum(status_data.values()) > 0:
        fig = px.pie(
            values=list(status_data.values()),
            names=list(status_data.keys()),
            color_discrete_sequence=['#faad14', '#1890ff', '#52c41a']
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>数量: %{value}<br>比例: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True, key="order_status_chart")
    else:
        st.info("暂无订单数据")

def render_stage_distribution_chart(stage_stats: dict):
    """渲染阶段分布图"""
    st.markdown("#### 🔄 各阶段进度分布")
    
    if stage_stats:
        stages = list(stage_stats.keys())
        pending_counts = [stage_stats[stage].get('pending', 0) for stage in stages]
        in_progress_counts = [stage_stats[stage].get('in_progress', 0) for stage in stages]
        completed_counts = [stage_stats[stage].get('completed', 0) for stage in stages]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='待处理',
            x=stages,
            y=pending_counts,
            marker_color='#faad14'
        ))
        
        fig.add_trace(go.Bar(
            name='进行中',
            x=stages,
            y=in_progress_counts,
            marker_color='#1890ff'
        ))
        
        fig.add_trace(go.Bar(
            name='已完成',
            x=stages,
            y=completed_counts,
            marker_color='#52c41a'
        ))
        
        fig.update_layout(
            barmode='stack',
            height=300,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis_title="制作阶段",
            yaxis_title="订单数量",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key="stage_distribution_chart")
    else:
        st.info("暂无阶段数据")

def render_completion_trend_chart(dashboard_data: dict):
    """渲染完成趋势图（真实数据）"""
    st.markdown("#### 📈 近期完成趋势")
    
    # 从仪表板数据中获取趋势数据
    trend_data = dashboard_data.get('completion_trend', {})
    dates = trend_data.get('dates', [])
    completions = trend_data.get('completions', [])
    
    if not dates or not completions:
        st.info("暂无完成趋势数据")
        return
    
    # 转换日期格式为Plotly可识别的格式
    from datetime import datetime, timedelta
    today = datetime.now()
    dates_list = []
    
    # dates是MM-DD格式，需要转换为完整日期
    for date_str in dates:
        month, day = date_str.split('-')
        # 判断是今年还是去年
        date_obj = datetime(today.year, int(month), int(day))
        # 如果日期在未来，说明是去年的
        if date_obj > today:
            date_obj = datetime(today.year - 1, int(month), int(day))
        dates_list.append(date_obj)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates_list,
        y=completions,
        mode='lines+markers',
        name='完成订单数',
        line=dict(color='#52c41a', width=3),
        marker=dict(size=6, color='#52c41a'),
        fill='tozeroy',  # 填充到x轴，不再使用tonexty
        fillcolor='rgba(82, 196, 26, 0.1)'
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title="日期",
        yaxis_title="完成数量",
        showlegend=False,
        xaxis=dict(
            tickformat='%m-%d',
            nticks=10,  # 显示约10个刻度
            tickangle=-45  # 倾斜45度
        ),
        yaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1  # Y轴每个刻度为1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, key="completion_trend_chart")