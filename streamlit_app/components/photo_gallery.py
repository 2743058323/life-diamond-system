"""
照片画廊组件

功能：
- 按阶段分组显示照片
- 支持查看大图
- 支持删除照片
- 支持上传新照片
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
        st.info("📭 还没有上传照片")
        
        # 显示上传按钮
        if 'upload_photo' in allowed_actions:
            st.markdown("---")
            if st.button("📷 上传第一张照片"):
                st.session_state.show_upload_modal = True
        return
    
    # 照片统计
    photo_count = photo_service.get_photo_count(photos_data)
    st.metric("照片总数", f"{photo_count} 张")
    
    st.markdown("---")
    
    # 按阶段显示照片
    for stage_name, photos in grouped_photos.items():
        st.markdown(f"### 📷 {stage_name}")
        st.caption(f"{len(photos)} 张照片")
        
        # 照片网格（每行3张）
        cols = st.columns(3)
        for i, photo in enumerate(photos):
            with cols[i % 3]:
                # 显示照片
                photo_url = photo.get('photo_url', photo.get('url', ''))
                description = photo.get('description', '')
                upload_time = photo.get('created_at', photo.get('upload_time', ''))
                photo_id = photo.get('_id', photo.get('photo_id', ''))
                
                # 照片卡片 - 只有URL不为空时才显示
                if photo_url:
                    st.image(photo_url)
                else:
                    st.warning("照片URL缺失")
                
                # 照片信息
                if description:
                    st.caption(f"📝 {description}")
                if upload_time:
                    # 导入format_datetime并格式化时间
                    from utils.helpers import format_datetime
                    formatted_time = format_datetime(upload_time, "datetime")
                    st.caption(f"🕐 {formatted_time}")
                
                # 删除按钮
                if 'delete_photo' in allowed_actions:
                    if st.button(
                        "🗑️ 删除", 
                        key=f"delete_photo_{photo_id}",
                        width='stretch'
                    ):
                        delete_photo_with_confirm(photo_service, photo_id, photo_url, on_change)
        
        st.markdown("---")
    
    # 上传更多照片按钮
    if 'upload_photo' in allowed_actions:
        if st.button("📷 上传更多照片"):
            st.session_state.show_upload_modal = True


def delete_photo_with_confirm(photo_service, photo_id, photo_url, on_change):
    """删除照片（带确认）"""
    # 使用 session_state 来存储待删除的照片
    st.session_state.deleting_photo_id = photo_id
    st.session_state.deleting_photo_url = photo_url
    
    # 显示确认对话框
    st.warning("⚠️ 确定要删除这张照片吗？此操作无法撤销！")
    
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
    """显示上传照片模态框"""
    st.markdown("### 📷 上传照片")
    
    with st.form("upload_photo_form"):
        # 选择阶段
        stage_options = [(p.get('stage_id'), p.get('stage_name')) for p in progress_data if p.get('status') in ['in_progress', 'completed']]
        
        if not stage_options:
            st.warning("⚠️ 没有可上传照片的阶段（需要阶段至少已开始）")
            st.form_submit_button("关闭")
            return
        
        stage_dict = {name: sid for sid, name in stage_options}
        selected_stage_name = st.selectbox(
            "选择制作阶段",
            options=list(stage_dict.keys()),
            help="选择照片对应的制作阶段"
        )
        selected_stage_id = stage_dict[selected_stage_name]
        
        # 照片描述
        description = st.text_area(
            "照片描述（可选）",
            placeholder="简要描述照片内容",
            help="选填，方便客户了解照片内容"
        )
        
        # 文件上传
        uploaded_files = st.file_uploader(
            "选择照片文件",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="支持上传多张照片，建议每张不超过5MB"
        )
        
        # 照片预览
        if uploaded_files:
            st.markdown(f"**已选择 {len(uploaded_files)} 张照片：**")
            cols = st.columns(min(len(uploaded_files), 3))
            for i, file in enumerate(uploaded_files[:3]):
                with cols[i % 3]:
                    st.image(file, caption=file.name)
            if len(uploaded_files) > 3:
                st.caption(f"...还有 {len(uploaded_files) - 3} 张照片")
        
        # 提交按钮
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📤 上传照片")
        with col2:
            cancelled = st.form_submit_button("❌ 取消")
        
        if cancelled:
            st.session_state.show_upload_modal = False
            st.rerun()
        
        if submitted:
            if not uploaded_files:
                st.error("❌ 请至少选择一张照片")
            else:
                with st.spinner(f"正在上传 {len(uploaded_files)} 张照片..."):
                    result = photo_service.upload_photos(
                        order_id=order_id,
                        stage_id=selected_stage_id,
                        stage_name=selected_stage_name,
                        photos=uploaded_files,
                        description=description
                    )
                
                if result.get('success'):
                    st.success(f"✅ 成功上传 {len(uploaded_files)} 张照片！")
                    st.session_state.show_upload_modal = False
                    if on_upload:
                        on_upload()
                else:
                    st.error(f"❌ 上传失败：{result.get('message')}")

