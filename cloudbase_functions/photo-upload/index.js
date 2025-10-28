// 照片上传云函数 - 使用CloudBase SDK
const tcb = require('@cloudbase/node-sdk');

// 初始化CloudBase
const app = tcb.init({
  env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

// 记录操作日志（内联函数，避免文件依赖问题）
async function logOperation(params) {
    try {
        const {
            type,
            operator = 'admin',
            description,
            order_number = '',
            order_id = '',
            ip_address = '',
            metadata = {}
        } = params;
        
        const timestamp = new Date().toISOString();
        
        await db.collection('operation_logs').add({
            type,
            operator,
            description,
            order_number,
            order_id,
            ip_address,
            metadata,
            timestamp,
            created_at: timestamp
        });
        
        console.log(`✅ 操作日志已记录: ${type} - ${description}`);
    } catch (error) {
        console.error('❌ 记录操作日志失败:', error);
        // 不抛出异常，避免影响主流程
    }
}

// 阶段ID到名称的映射（与前端config.py保持一致）
function getStageName(stageId) {
  const stageMap = {
    'stage_1': '进入实验室',
    'stage_2': '碳化提纯',
    'stage_3': '石墨化',
    'stage_4': '高温高压培育生长',
    'stage_5': '钻胚提取',
    'stage_6': '切割',
    'stage_7': '认证溯源',
    'stage_8': '镶嵌钻石',
    // 支持STAGE001-STAGE008格式
    'STAGE001': '进入实验室',
    'STAGE002': '碳化提纯',
    'STAGE003': '石墨化',
    'STAGE004': '高温高压培育生长',
    'STAGE005': '钻胚提取',
    'STAGE006': '切割',
    'STAGE007': '认证溯源',
    'STAGE008': '镶嵌钻石'
  };
  return stageMap[stageId] || stageId;
}

exports.main = async (event, context) => {
  console.log('=== 照片上传云函数 - CloudBase SDK版本 ===');
  console.log('请求参数:', event);
  
  try {
    // 解析请求参数
    let body = {};
    try {
      body = JSON.parse(event.body || '{}');
    } catch (e) {
      body = event;
    }
    
    const { action, data } = body;
    
    if (action === 'test') {
      return {
        statusCode: 200,
        headers: { 
          'Content-Type': 'application/json', 
          'Access-Control-Allow-Origin': '*' 
        },
        body: JSON.stringify({ 
          success: true, 
          message: '无依赖云函数运行正常！',
          timestamp: new Date().toISOString(),
          nodeVersion: process.version
        })
      };
    }
    
    if (action === 'get_upload_url') {
      const { order_id, stage_id, file_count = 1 } = data || {};
      
      if (!order_id || !stage_id) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '缺少必要参数: order_id 或 stage_id' 
          })
        };
      }
      
      console.log(`生成上传URL: 订单${order_id}, 阶段${stage_id}, 文件数量${file_count}`);
      
      const upload_urls = [];
      
      for (let i = 0; i < file_count; i++) {
        // 默认使用jpg扩展名，实际扩展名会在上传时确定
        const file_id = `photo_${order_id}_${stage_id}_${Date.now()}_${i}.jpg`;
        
        upload_urls.push({
          file_id: file_id,
          upload_url: 'cloud_storage', // 标记使用云存储
          cloud_path: `photos/${order_id}/${stage_id}/${file_id}`,
          storage_type: 'cloud_storage',
          uploadMethod: 'direct_upload' // 标记直接上传方式
        });
      }
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: true,
          data: { upload_urls: upload_urls },
          message: `成功生成 ${file_count} 个上传URL`
        })
      };
    }
    
    if (action === 'upload') {
      const { order_id, stage_id, files } = data || {};
      
      if (!order_id || !stage_id || !files || !Array.isArray(files)) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '缺少必要参数' 
          })
        };
      }
      
      console.log(`处理 ${files.length} 个文件上传`);
      
      const results = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 获取文件扩展名
        const fileName = file.name || 'unknown';
        const fileExt = fileName.split('.').pop() || 'jpg';
        
        const fileId = `photo_${order_id}_${stage_id}_${Date.now()}_${i}.${fileExt}`;
        
        // 直接生成Base64 data URL（无数据库存储）
        const dataUrl = `data:image/jpeg;base64,${file.content}`;
        
        results.push({
          file_id: fileId,
          photo_url: dataUrl,
          thumbnail_url: dataUrl,
          storage_type: 'database',
          file_name: file.name || '未命名',
          file_size: file.size || 0,
          upload_time: new Date().toISOString()
        });
      }
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: true,
          data: { uploaded_files: results },
          message: `成功处理 ${results.length} 张照片（无数据库存储）`
        })
      };
    }
    
    if (action === 'cloud_upload') {
      const { order_id, stage_id, files } = data || {};
      
      if (!order_id || !stage_id || !files || !Array.isArray(files)) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '缺少必要参数' 
          })
        };
      }
      
      console.log(`处理 ${files.length} 个文件云存储上传`);
      
      const results = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 获取文件扩展名
        const fileName = file.name || 'unknown';
        const fileExt = fileName.split('.').pop() || 'jpg';
        
        const fileId = `photo_${order_id}_${stage_id}_${Date.now()}_${i}.${fileExt}`;
        const cloudPath = `photos/${order_id}/${stage_id}/${fileId}`;
        
        try {
          console.log(`开始上传文件到云存储: ${cloudPath}`);
          
          // 将Base64转换为Buffer
          const fileBuffer = Buffer.from(file.content, 'base64');
          
          // 使用CloudBase SDK上传文件
          const uploadResult = await app.uploadFile({
            cloudPath: cloudPath,
            fileContent: fileBuffer
          });
          
          console.log(`CloudBase上传结果:`, uploadResult);
          
          if (uploadResult.fileID) {
            // 获取文件访问URL
            const tempUrlResult = await app.getTempFileURL({
              fileList: [uploadResult.fileID]
            });
            
            let photoUrl = `https://636c-cloud1-7g7o4xi13c00cb90-1379657467.tcb.qcloud.la/${cloudPath}`;
            
            if (tempUrlResult.fileList && tempUrlResult.fileList[0] && tempUrlResult.fileList[0].tempFileURL) {
              photoUrl = tempUrlResult.fileList[0].tempFileURL;
            }
            
            // 保存照片信息到数据库
            const photoRecord = {
              order_id: order_id,
              stage_id: stage_id,
              stage_name: getStageName(stage_id),
              file_id: fileId,
              photo_url: photoUrl,
              thumbnail_url: photoUrl,
              storage_type: 'cloud_storage',
              file_name: file.name || '未命名',
              file_size: file.size || 0,
              upload_time: new Date().toISOString(),
              cloud_path: cloudPath,
              fileID: uploadResult.fileID,
              description: '',
              sort_order: i,
              is_deleted: false
            };
            
            try {
              await db.collection('photos').add(photoRecord);
              console.log(`✅ 照片记录已保存到数据库: ${fileId}`);
            } catch (dbError) {
              console.error(`❌ 保存照片记录到数据库失败: ${fileId}`, dbError);
            }
            
            results.push(photoRecord);
            
            console.log(`✅ 云存储上传成功: ${fileId}`);
            console.log(`📁 文件ID: ${uploadResult.fileID}`);
            console.log(`🔗 访问URL: ${photoUrl}`);
            
          } else {
            throw new Error('上传失败：未返回fileID');
          }
          
          // 记录上传操作日志（只在第一个文件上传后记录一次）
          if (i === 0) {
            // 查询订单信息
            try {
              const orderResult = await db.collection('orders').where({ _id: order_id }).get();
              const order = orderResult.data && orderResult.data.length > 0 ? orderResult.data[0] : null;
              
              const customerName = order ? order.customer_name : '未知客户';
              const stageName = getStageName(stage_id);
              
              console.log(`📝 准备记录操作日志: 客户 ${customerName} - ${stageName}`);
              
              await logOperation({
                type: '照片上传',
                operator: data.operator || 'admin',
                description: `上传照片：客户 ${customerName} - ${stageName}`,
                order_id: order_id,
                order_number: order ? order.order_number : '',
                metadata: {
                  customer_name: customerName,
                  stage_name: stageName,
                  file_count: files.length
                }
              });
              
              console.log(`✅ 操作日志记录成功`);
            } catch (logError) {
              console.error('❌ 记录照片上传日志失败:', logError);
            }
          }
          
        } catch (error) {
          console.error(`❌ 云存储上传失败: ${fileId}`, error);
          
          // 降级到Base64存储
          const dataUrl = `data:image/jpeg;base64,${file.content}`;
          results.push({
            file_id: fileId,
            photo_url: dataUrl,
            thumbnail_url: dataUrl,
            storage_type: 'database',
            file_name: file.name || '未命名',
            file_size: file.size || 0,
            upload_time: new Date().toISOString(),
            error: error.message
          });
        }
      }
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: true,
          data: { uploaded_files: results },
          message: `成功处理 ${results.length} 张照片（云存储）`
        })
      };
    }
    
    if (action === 'confirm_upload') {
      const { order_id, stage_id, uploaded_files, description } = data || {};
      
      if (!order_id || !stage_id || !uploaded_files || !Array.isArray(uploaded_files)) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '缺少必要参数: order_id, stage_id 或 uploaded_files' 
          })
        };
      }
      
      console.log(`确认上传完成: 订单${order_id}, 阶段${stage_id}, 文件数量${uploaded_files.length}`);
      
      // 模拟确认上传成功（实际应该保存到数据库）
      const confirmed_files = uploaded_files.map(file => ({
        ...file,
        confirmed: true,
        confirm_time: new Date().toISOString()
      }));
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: true,
          data: { 
            confirmed_files: confirmed_files,
            total_files: confirmed_files.length
          },
          message: `成功确认 ${confirmed_files.length} 个文件上传完成`
        })
      };
    }
    
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ 
        success: false, 
        message: '未知操作' 
      })
    };
    
  } catch (error) {
    console.error('云函数执行失败:', error);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ 
        success: false, 
        message: '服务器内部错误',
        error: error.message
      })
    };
  }
};
