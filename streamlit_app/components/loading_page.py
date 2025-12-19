"""
加载页面组件

提供美观的加载状态显示
"""

import streamlit as st


def show_loading(message: str = "加载中...", spinner_type: str = "default"):
    """
    显示加载状态
    
    Args:
        message: 加载提示信息
        spinner_type: 加载类型，可选值：
            - "default": 默认spinner
            - "fullscreen": 全屏加载（带遮罩）
            - "inline": 行内加载（不占满屏幕）
    """
    if spinner_type == "fullscreen":
        show_fullscreen_loading(message)
    elif spinner_type == "inline":
        show_inline_loading(message)
    else:
        # 默认使用Streamlit的spinner
        return st.spinner(message)


def show_fullscreen_loading(message: str = "加载中..."):
    """
    显示全屏加载页面（带遮罩层）
    
    Args:
        message: 加载提示信息
    """
    # 使用 f-string 避免 CSS 中的花括号被 format 解析
    st.markdown(f"""
    <style>
    .loading-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        backdrop-filter: blur(2px);
    }}
    
    .loading-spinner {{
        width: 60px;
        height: 60px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #8B4B8C;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .loading-message {{
        font-size: 1.2rem;
        color: #8B4B8C;
        font-weight: 500;
        text-align: center;
    }}
    
    .loading-dots {{
        display: inline-block;
        animation: dots 1.5s steps(4, end) infinite;
    }}
    
    @keyframes dots {{
        0%, 20% {{ content: '.'; }}
        40% {{ content: '..'; }}
        60% {{ content: '...'; }}
        80%, 100% {{ content: ''; }}
    }}
    </style>
    
    <div class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-message">{message}<span class="loading-dots"></span></div>
    </div>
    """, unsafe_allow_html=True)


def show_inline_loading(message: str = "加载中..."):
    """
    显示行内加载状态（不遮挡页面）
    
    Args:
        message: 加载提示信息
    """
    # 使用 f-string 避免 CSS 中的花括号被 format 解析
    st.markdown(f"""
    <style>
    .inline-loading {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        text-align: center;
    }}
    
    .inline-spinner {{
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #8B4B8C;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .inline-message {{
        font-size: 1rem;
        color: #666;
        font-weight: 400;
    }}
    </style>
    
    <div class="inline-loading">
        <div class="inline-spinner"></div>
        <div class="inline-message">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def loading_context(message: str = "加载中...", loading_type: str = "default"):
    """
    加载上下文管理器，用于包装需要显示加载状态的代码块
    
    使用示例:
        with loading_context("正在加载数据..."):
            # 执行耗时操作
            data = load_data()
    
    Args:
        message: 加载提示信息
        loading_type: 加载类型，可选值：default, fullscreen, inline
    """
    if loading_type == "fullscreen":
        # 全屏加载需要特殊处理
        placeholder = st.empty()
        with placeholder.container():
            show_fullscreen_loading(message)
        return placeholder
    elif loading_type == "inline":
        placeholder = st.empty()
        with placeholder.container():
            show_inline_loading(message)
        return placeholder
    else:
        # 默认使用Streamlit的spinner
        return st.spinner(message)


def show_loading_with_progress(message: str = "加载中...", progress: float = 0.0):
    """
    显示带进度条的加载状态
    
    Args:
        message: 加载提示信息
        progress: 进度值（0.0 - 1.0）
    """
    st.markdown(f"""
    <style>
    .progress-loading {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        text-align: center;
    }}
    
    .progress-spinner {{
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #8B4B8C;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .progress-message {{
        font-size: 1rem;
        color: #666;
        font-weight: 400;
        margin-bottom: 10px;
    }}
    </style>
    
    <div class="progress-loading">
        <div class="progress-spinner"></div>
        <div class="progress-message">{message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示进度条
    st.progress(progress)

