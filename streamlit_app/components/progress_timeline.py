"""
进度时间轴组件

功能：
- 显示制作进度时间轴
- 支持开始阶段
- 支持完成阶段（含备注和照片/视频上传）
- 集成照片和视频上传到进度更新
"""

import streamlit as st
from datetime import datetime, date


def show(progress_service, order_id, progress_data, allowed_actions, on_update=None):
    """
    显示进度时间轴
    
    Args:
        progress_service: ProgressService 实例
        order_id: 订单ID
        progress_data: 进度数据列表
        allowed_actions: 允许的操作列表
        on_update: 更新后的回调函数
    """
    
    if not progress_data:
        st.info("📭 还没有进度信息")
        return
    
    # 格式化进度数据
    timeline = progress_service.format_progress_for_timeline(progress_data)
    
    # 显示每个阶段
    for stage in timeline:
        status = stage['status']
        stage_id = stage['stage_id']
        stage_name = stage['stage_name']
        
        # 状态图标和颜色
        status_config = {
            'pending': {'icon': '⏸️', 'color': '#9E9E9E', 'text': '待处理'},
            'in_progress': {'icon': '🔄', 'color': '#2196F3', 'text': '进行中'},
            'completed': {'icon': '✅', 'color': '#4CAF50', 'text': '已完成'}
        }
        config = status_config.get(status, {'icon': '❓', 'color': '#999', 'text': status})
        
        # 展开容器
        with st.expander(
            f"{config['icon']} {stage_name} - {config['text']}", 
            expanded=(status == 'in_progress')
        ):
            # 时间信息
            col1, col2 = st.columns(2)
            with col1:
                if stage.get('start_time'):
                    st.markdown(f"**⏰ 开始时间：** {stage['start_time']}")
            with col2:
                if stage.get('completion_time'):
                    st.markdown(f"**🎯 完成时间：** {stage['completion_time']}")
            
            # 备注
            if stage.get('notes'):
                st.markdown(f"**📝 备注：** {stage['notes']}")
            
            # 照片和视频数量（如果有）
            photo_count = stage.get('photo_count', 0)
            video_count = stage.get('video_count', 0)
            if photo_count > 0 or video_count > 0:
                if photo_count > 0 and video_count > 0:
                    st.markdown(f"**📷🎬 媒体：** {photo_count} 张照片，{video_count} 个视频")
                elif video_count > 0:
                    st.markdown(f"**🎬 视频：** {video_count} 个")
                else:
                    st.markdown(f"**📷 照片：** {photo_count} 张")
            
            st.markdown("---")
            
            # 操作按钮
            if status == 'pending':
                show_start_stage_button(progress_service, order_id, stage_id, stage_name, allowed_actions, on_update)
            elif status == 'in_progress':
                show_complete_stage_form(progress_service, order_id, stage_id, stage_name, allowed_actions, on_update)


def show_start_stage_button(progress_service, order_id, stage_id, stage_name, allowed_actions, on_update):
    """显示开始阶段按钮"""
    if 'start_stage' not in allowed_actions:
        st.caption("⚠️ 需要有进度更新权限才能开始阶段")
        return
    
    if st.button(f"▶️ 开始此阶段", key=f"start_{stage_id}"):
        with st.spinner(f"正在开始 {stage_name}..."):
            result = progress_service.start_stage(order_id, stage_id)
        
        if result.get('success'):
            st.success(f"✅ 阶段 '{stage_name}' 已开始！")
            if on_update:
                on_update()
        else:
            st.error(f"❌ 开始阶段失败：{result.get('message')}")


def show_complete_stage_form(progress_service, order_id, stage_id, stage_name, allowed_actions, on_update):
    """显示完成阶段表单"""
    if 'complete_stage' not in allowed_actions:
        st.caption("⚠️ 需要有进度更新权限才能完成阶段")
        return
    
    with st.form(f"complete_form_{stage_id}"):
        st.markdown("#### ✅ 完成此阶段")
        
        # 备注
        notes = st.text_area(
            "备注说明",
            placeholder="输入本阶段的完成说明、遇到的问题、注意事项等",
            help="选填，建议填写关键信息",
            key=f"notes_{stage_id}"
        )
        
        # 照片和视频上传
        st.markdown("#### 📷🎬 上传完成照片/视频（可选）")
        st.info("💡 建议上传该阶段的完成照片或视频，客户可以在查询页面看到")
        
        photos = st.file_uploader(
            "选择照片/视频文件",
            type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi', 'webm'],
            accept_multiple_files=True,
            help="支持上传多张照片（最大10MB）或多个视频（最大100MB）",
            key=f"photos_{stage_id}"
        )
        
        # 文件预览
        if photos:
            # 分类显示
            images = [f for f in photos if f.type and f.type.startswith('image/')]
            videos = [f for f in photos if f.type and f.type.startswith('video/')]
            
            if images:
                st.markdown(f"**已选择 {len(images)} 张照片：**")
                cols = st.columns(min(len(images), 3))
                for i, photo in enumerate(images[:3]):  # 最多预览3张
                    with cols[i % 3]:
                        st.image(photo, caption=photo.name)
                if len(images) > 3:
                    st.caption(f"...还有 {len(images) - 3} 张照片")
            
            if videos:
                st.markdown(f"**已选择 {len(videos)} 个视频：**")
                for video in videos:
                    st.caption(f"🎬 {video.name} ({video.size/1024/1024:.1f}MB)")
        
        # 提交按钮
        submitted = st.form_submit_button("✅ 确认完成此阶段")
        
        if submitted:
            # 验证文件
            if photos:
                # 导入 photo_service 进行验证
                from services.photo_service import PhotoService
                from utils.cloudbase_client import api_client
                photo_service = PhotoService(api_client)
                
                is_valid, error_msg = photo_service.validate_photo_files(photos)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                    return
            
            with st.spinner(f"正在完成 {stage_name}..."):
                result = progress_service.complete_stage(
                    order_id,
                    stage_id,
                    notes,
                    photos
                )
            
            if result.get('success'):
                st.success(f"✅ 阶段 '{stage_name}' 已完成！")
                if photos:
                    # 统计照片和视频数量
                    image_count = sum(1 for f in photos if f.type and f.type.startswith('image/'))
                    video_count = sum(1 for f in photos if f.type and f.type.startswith('video/'))
                    if image_count > 0 and video_count > 0:
                        st.success(f"📷🎬 已上传 {image_count} 张照片，{video_count} 个视频")
                    elif video_count > 0:
                        st.success(f"🎬 已上传 {video_count} 个视频")
                    else:
                        st.success(f"📷 已上传 {image_count} 张照片")
                if on_update:
                    on_update()
            else:
                st.error(f"❌ 完成阶段失败：{result.get('message')}")
