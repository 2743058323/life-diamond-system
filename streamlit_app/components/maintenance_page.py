"""
系统维护页面组件
"""
import streamlit as st
from datetime import datetime, timedelta

def show_maintenance_page(
    title="🔧 系统维护中",
    message="我们正在进行系统升级和维护，以提供更好的服务体验。",
    expected_time="预计维护时间：30分钟",
    show_contact=True
):
    """
    显示系统维护页面
    
    Args:
        title: 维护页面标题
        message: 维护信息
        expected_time: 预计恢复时间
        show_contact: 是否显示联系方式
    """
    # 隐藏侧边栏和顶部菜单
    st.markdown("""
        <style>
        /* 隐藏侧边栏 */
        [data-testid="stSidebar"] {
            display: none;
        }
        /* 隐藏顶部菜单 */
        header[data-testid="stHeader"] {
            display: none;
        }
        /* 维护页面样式 */
        .maintenance-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            text-align: center;
            padding: 2rem;
        }
        .maintenance-icon {
            font-size: 5rem;
            margin-bottom: 2rem;
            animation: rotate 3s linear infinite;
        }
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .maintenance-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .maintenance-message {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 1.5rem;
            max-width: 600px;
            line-height: 1.6;
        }
        .maintenance-time {
            font-size: 1rem;
            color: #ff6b6b;
            font-weight: 500;
            margin-bottom: 2rem;
        }
        .maintenance-tips {
            background-color: #f8f9fa;
            border-left: 4px solid #1f77b4;
            padding: 1.5rem;
            margin-top: 2rem;
            text-align: left;
            max-width: 600px;
            border-radius: 8px;
        }
        .maintenance-tips h4 {
            margin-top: 0;
            color: #1f77b4;
        }
        .maintenance-tips ul {
            margin-bottom: 0;
            padding-left: 1.5rem;
        }
        .maintenance-tips li {
            margin-bottom: 0.5rem;
            color: #666;
        }
        .maintenance-contact {
            margin-top: 2rem;
            padding: 1rem;
            background-color: #e3f2fd;
            border-radius: 8px;
            max-width: 600px;
        }
        .maintenance-footer {
            margin-top: 3rem;
            color: #999;
            font-size: 0.9rem;
        }
        
        /* 移动端优化 */
        @media (max-width: 768px) {
            .maintenance-icon {
                font-size: 3rem;
            }
            .maintenance-title {
                font-size: 1.8rem;
            }
            .maintenance-message {
                font-size: 1rem;
                padding: 0 1rem;
            }
            .maintenance-tips {
                padding: 1rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 维护页面内容
    # 构建预计时间部分（如果有的话）
    time_html = f'<div class="maintenance-time">⏰ {expected_time}</div>' if expected_time else ''
    
    st.markdown(f"""
        <div class="maintenance-container">
            <div class="maintenance-icon">⚙️</div>
            <div class="maintenance-title">{title}</div>
            <div class="maintenance-message">{message}</div>
            {time_html}
        </div>
    """, unsafe_allow_html=True)
    
    # 温馨提示
    st.markdown("""
        <div class="maintenance-tips">
            <h4>💡 温馨提示</h4>
            <ul>
                <li>维护期间系统暂时无法访问</li>
                <li>您的数据安全不会受到影响</li>
                <li>维护完成后系统将自动恢复</li>
                <li>如有紧急需求，请联系客服</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # 联系方式
    if show_contact:
        st.markdown("""
            <div class="maintenance-contact">
                <strong>📞 如有紧急需求，请联系：</strong><br>
                客服电话：400-XXX-XXXX<br>
                客服邮箱：service@example.com
            </div>
        """, unsafe_allow_html=True)
    
    # 页脚
    # 获取北京时间（UTC+8）
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    current_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"""
        <div class="maintenance-footer">
            感谢您的耐心等待！<br>
            当前时间：{current_time}
        </div>
    """, unsafe_allow_html=True)


def check_maintenance_mode():
    """
    检查是否处于维护模式（基于域名判断）
    
    Returns:
        tuple: (是否维护模式, 维护信息字典)
    """
    import os
    
    # 方式1：检查环境变量
    is_maintenance_by_env = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
    
    # 方式2：检查当前访问域名（如果设置了 PUBLIC_DOMAIN）
    public_domain = os.getenv("PUBLIC_DOMAIN", "diamond.genepk.cn")
    
    # 尝试获取当前请求的域名
    is_public_domain = False
    try:
        # Streamlit 从 headers 中获取域名
        # 注意：这需要在实际请求中才能获取
        import streamlit.web.server.server as server
        if hasattr(server, 'Server') and server.Server._singleton is not None:
            # 获取当前会话信息
            ctx = st.runtime.scriptrunner.get_script_run_ctx()
            if ctx and hasattr(ctx, 'session_id'):
                # 通过环境变量或者其他方式判断
                pass
    except:
        pass
    
    # 简化判断：如果环境变量开启，就显示维护页面
    is_maintenance = is_maintenance_by_env
    
    # 维护信息
    maintenance_info = {
        "title": os.getenv("MAINTENANCE_TITLE", "🔧 系统维护中"),
        "message": os.getenv("MAINTENANCE_MESSAGE", "我们正在进行系统升级和维护，以提供更好的服务体验。"),
        "expected_time": os.getenv("MAINTENANCE_TIME", ""),  # 默认为空，不显示预计时间
        "show_contact": os.getenv("MAINTENANCE_SHOW_CONTACT", "true").lower() == "true"
    }
    
    return is_maintenance, maintenance_info


def should_bypass_maintenance():
    """
    检查是否应该绕过维护模式
    通过检查特殊的 URL 参数来判断
    
    Returns:
        bool: 是否绕过维护模式
    """
    import os
    
    # 检查是否有绕过密钥参数
    bypass_key = os.getenv("MAINTENANCE_BYPASS_KEY", "")
    
    if not bypass_key:
        return False
    
    # 检查 URL 参数
    try:
        # Streamlit 的 query params
        query_params = st.query_params
        return query_params.get("bypass") == bypass_key
    except:
        return False

