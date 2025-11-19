// 修复数据库中的阶段名称 - 从旧配置更新到新配置
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

// 旧配置到新配置的映射
const stageMapping = {
    '订单确认': '进入实验室',
    '原料准备': '碳化提纯', 
    '高温高压处理': '石墨化',
    '切割打磨': '高温高压培育生长',
    '质量检测': '毛胚提取',
    '包装完成': '切割'
};

async function fixStageNames() {
    console.log('开始修复阶段名称...');
    console.log('映射关系:', stageMapping);
    
    try {
        // 获取所有照片记录
        const result = await db.collection('photos').get();
        console.log(`找到 ${result.data.length} 条照片记录`);
        
        let updateCount = 0;
        const updateResults = [];
        
        for (const photo of result.data) {
            const oldStageName = photo.stage_name;
            const newStageName = stageMapping[oldStageName];
            
            if (newStageName && oldStageName !== newStageName) {
                console.log(`更新记录 ${photo._id}: ${oldStageName} -> ${newStageName}`);
                
                await db.collection('photos').doc(photo._id).update({
                    stage_name: newStageName
                });
                
                updateCount++;
                updateResults.push({
                    id: photo._id,
                    old_name: oldStageName,
                    new_name: newStageName
                });
            } else if (newStageName) {
                console.log(`记录 ${photo._id} 已经是正确名称: ${oldStageName}`);
            } else {
                console.log(`记录 ${photo._id} 使用未知阶段名称: ${oldStageName}`);
            }
        }
        
        console.log(`修复完成！共更新了 ${updateCount} 条记录`);
        console.log('更新详情:', updateResults);
        
    } catch (error) {
        console.error('修复失败:', error);
    }
}

// 执行修复
fixStageNames();
