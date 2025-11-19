"""
照片和视频画廊组件

功能：
- 按阶段分组显示照片和视频
- 支持查看大图和播放视频
- 支持删除照片/视频
- 支持上传新照片和视频
"""

import streamlit as st


def show(photo_service, order_id, photos_data, grouped_photos, allowed_actions, on_change=None):
    """
    显示照片画廊
    
    Args:
        photo_service: PhotoService 实例
        order_id: 订单ID
        photos_data: 照片数据列表
        grouped_photos: 按阶段分组的照片字典
        allowed_actions: 允许的操作列表
        on_change: 照片变化后的回调函数
    """
    
    if not photos_data:
        st.info("📭 还没有上传照片或视频")
        
        # 显示上传按钮
        if 'upload_photo' in allowed_actions:
            st.markdown("---")
            if st.button("📷 上传第一张照片/视频"):
                st.session_state.show_upload_modal = True
        return
    
    # 统计照片和视频数量
    photo_count = 0
    video_count = 0
    for photo_group in photos_data:
        photos = photo_group.get('photos', [])
        for photo in photos:
            media_type = photo.get('media_type', 'photo')
            if media_type == 'video':
                video_count += 1
            else:
                photo_count += 1
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("照片总数", f"{photo_count} 张")
    with col2:
        st.metric("视频总数", f"{video_count} 个")
    
    st.markdown("---")
    
    # 按阶段显示照片和视频
    for stage_name, photos in grouped_photos.items():
        # 统计该阶段的照片和视频数量
        stage_photo_count = sum(1 for p in photos if p.get('media_type', 'photo') != 'video')
        stage_video_count = sum(1 for p in photos if p.get('media_type') == 'video')
        
        stage_title = f"### 📷 {stage_name}"
        if stage_video_count > 0:
            stage_title = f"### 📷🎬 {stage_name}"
        
        st.markdown(stage_title)
        if stage_photo_count > 0 and stage_video_count > 0:
            st.caption(f"{stage_photo_count} 张照片，{stage_video_count} 个视频")
        elif stage_video_count > 0:
            st.caption(f"{stage_video_count} 个视频")
        else:
            st.caption(f"{stage_photo_count} 张照片")
        
        # 媒体网格（每行3个）
        cols = st.columns(3)
        for i, photo in enumerate(photos):
            with cols[i % 3]:
                # 获取媒体信息
                media_url = photo.get('photo_url', photo.get('url', ''))
                thumbnail_url = photo.get('thumbnail_url', media_url)  # 优先使用缩略图
                description = photo.get('description', '')
                upload_time = photo.get('created_at', photo.get('upload_time', ''))
                media_id = photo.get('_id', photo.get('photo_id', ''))
                media_type = photo.get('media_type', 'photo')
                file_type = photo.get('file_type', '')
                
                # 显示媒体 - 根据类型显示图片或视频
                if media_url:
                    if media_type == 'video' or file_type.startswith('video/'):
                        # 使用HTML video标签，设置preload="none"确保不预加载
                        # 只有用户点击播放按钮后才会开始下载视频
                        st.markdown(f"""
                        <video width="100%" controls preload="none" style="border-radius: 8px;">
                            <source src="{media_url}" type="video/mp4">
                            您的浏览器不支持视频播放。
                        </video>
                        """, unsafe_allow_html=True)
                    else:
                        # 照片：优先使用缩略图，点击可查看大图
                        photo_key = f"photo_{media_id}_{i}"
                        if photo_key not in st.session_state:
                            st.session_state[photo_key] = False
                        
                        # 优先显示缩略图（如果存在且与原图不同）
                        display_url = thumbnail_url if (thumbnail_url and thumbnail_url != media_url) else media_url
                        st.image(display_url, use_container_width=True)
                        st.caption("📷 照片")
                        
                        # 如果使用了缩略图，提供查看原图按钮
                        if thumbnail_url and thumbnail_url != media_url:
                            if st.button("🔍 查看原图", key=f"view_full_{photo_key}", use_container_width=True):
                                st.session_state[photo_key] = True
                            
                            if st.session_state.get(photo_key, False):
                                st.image(media_url, use_container_width=True)
                                if st.button("❌ 关闭原图", key=f"close_full_{photo_key}", use_container_width=True):
                                    st.session_state[photo_key] = False
                                    st.rerun()
                else:
                    st.warning("媒体URL缺失")
                
                # 媒体信息
                if description:
                    st.caption(f"📝 {description}")
                if upload_time:
                    # 导入format_datetime并格式化时间
                    from utils.helpers import format_datetime
                    formatted_time = format_datetime(upload_time, "datetime")
                    st.caption(f"🕐 {formatted_time}")
                
                # 删除按钮
                if 'delete_photo' in allowed_actions:
                    media_label = "视频" if media_type == 'video' else "照片"
                    delete_key = f"delete_photo_{media_id}"
                    if st.button(
                        f"🗑️ 删除{media_label}", 
                        key=delete_key,
                        width='stretch'
                    ):
                        st.session_state.deleting_photo_id = media_id
                        st.session_state.deleting_photo_url = media_url
                        st.session_state.deleting_photo_label = media_label
                    
                    if st.session_state.get('deleting_photo_id') == media_id:
                        delete_photo_with_confirm(photo_service, media_id, media_url, on_change)
                        # 渲染确认对话框后停止继续渲染，以免重复显示
                        st.stop()
        
        st.markdown("---")
    
    # 上传更多媒体按钮
    if 'upload_photo' in allowed_actions:
        if st.button("📷🎬 上传更多照片/视频"):
            st.session_state.show_upload_modal = True


def delete_photo_with_confirm(photo_service, photo_id, photo_url, on_change):
    """删除照片（带确认）"""
    # 显示确认对话框
    media_label = st.session_state.get('deleting_photo_label', '照片/视频')
    st.warning(f"⚠️ 确定要删除这{media_label}吗？此操作无法撤销！")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 确认删除", key=f"confirm_delete_{photo_id}"):
            with st.spinner("正在删除照片..."):
                result = photo_service.delete_photo(photo_id)
            
            if result.get('success'):
                st.success("✅ 照片已删除！")
                # 清除状态
                if 'deleting_photo_id' in st.session_state:
                    del st.session_state.deleting_photo_id
                if 'deleting_photo_url' in st.session_state:
                    del st.session_state.deleting_photo_url
                if on_change:
                    on_change()
            else:
                st.error(f"❌ 删除失败：{result.get('message')}")
    
    with col2:
        if st.button("❌ 取消", key=f"cancel_delete_{photo_id}"):
            # 清除状态
            if 'deleting_photo_id' in st.session_state:
                del st.session_state.deleting_photo_id
            if 'deleting_photo_url' in st.session_state:
                del st.session_state.deleting_photo_url
            st.rerun()


def show_upload_modal(photo_service, order_id, progress_data, on_upload):
    """显示上传照片和视频模态框"""
    st.markdown("### 📷🎬 上传照片/视频")
    
    with st.form("upload_photo_form"):
        # 选择阶段
        stage_options = [(p.get('stage_id'), p.get('stage_name')) for p in progress_data if p.get('status') in ['in_progress', 'completed']]
        
        if not stage_options:
            st.warning("⚠️ 没有可上传媒体的阶段（需要阶段至少已开始）")
            st.form_submit_button("关闭")
            return
        
        stage_dict = {name: sid for sid, name in stage_options}
        selected_stage_name = st.selectbox(
            "选择制作阶段",
            options=list(stage_dict.keys()),
            help="选择媒体对应的制作阶段"
        )
        selected_stage_id = stage_dict[selected_stage_name]
        
        # 描述
        description = st.text_area(
            "描述（可选）",
            placeholder="简要描述内容",
            help="选填，方便客户了解内容"
        )
        
        # 文件上传 - 支持照片和视频
        uploaded_files = st.file_uploader(
            "选择照片/视频文件",
            type=['jpg', 'jpeg', 'png', 'mp4', 'mov', 'avi', 'webm'],
            accept_multiple_files=True,
            help="支持上传多张照片（最大10MB）或多个视频（最大100MB）"
        )
        
        # 文件预览
        if uploaded_files:
            # 分类显示
            images = [f for f in uploaded_files if f.type and f.type.startswith('image/')]
            videos = [f for f in uploaded_files if f.type and f.type.startswith('video/')]
            
            if images:
                st.markdown(f"**已选择 {len(images)} 张照片：**")
                cols = st.columns(min(len(images), 3))
                for i, file in enumerate(images[:3]):
                    with cols[i % 3]:
                        st.image(file, caption=file.name)
                if len(images) > 3:
                    st.caption(f"...还有 {len(images) - 3} 张照片")
            
            if videos:
                st.markdown(f"**已选择 {len(videos)} 个视频：**")
                for file in videos:
                    st.caption(f"🎬 {file.name} ({file.size/1024/1024:.1f}MB)")
        
        # 提交按钮
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📤 上传")
        with col2:
            cancelled = st.form_submit_button("❌ 取消")
        
        if cancelled:
            st.session_state.show_upload_modal = False
            st.rerun()
        
        if submitted:
            if not uploaded_files:
                st.error("❌ 请至少选择一个文件")
            else:
                # 验证文件
                is_valid, error_msg = photo_service.validate_photo_files(uploaded_files)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    with st.spinner(f"正在上传 {len(uploaded_files)} 个文件..."):
                        result = photo_service.upload_photos(
                            order_id=order_id,
                            stage_id=selected_stage_id,
                            stage_name=selected_stage_name,
                            photos=uploaded_files,
                            description=description
                        )
                    
                    if result.get('success'):
                        file_count = len(uploaded_files)
                        st.success(f"✅ 成功上传 {file_count} 个文件！")
                        st.session_state.show_upload_modal = False
                        if on_upload:
                            on_upload()
                    else:
                        st.error(f"❌ 上传失败：{result.get('message')}")

