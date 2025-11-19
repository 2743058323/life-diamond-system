// 照片上传云函数 - 使用CloudBase SDK + COS 预签名直传
const tcb = require('@cloudbase/node-sdk');
const COS = require('cos-nodejs-sdk-v5');

// 初始化CloudBase
const app = tcb.init({
  env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

// 读取环境变量
const {
  TENCENT_SECRET_ID,
  TENCENT_SECRET_KEY,
  STORAGE_REGION = 'ap-shanghai',
  STORAGE_BUCKET = 'life-diamond-photos-1379657467',
  STORAGE_DOMAIN = '',
  COS_GET_SIGNED_URL_EXPIRES = '3600'
} = process.env;

// 初始化 COS（用于生成预签名 URL）
let cos = null;
if (TENCENT_SECRET_ID && TENCENT_SECRET_KEY) {
  cos = new COS({
    SecretId: TENCENT_SECRET_ID,
    SecretKey: TENCENT_SECRET_KEY
  });
}

const SIGNED_GET_URL_EXPIRES = parseInt(COS_GET_SIGNED_URL_EXPIRES || '3600', 10);
const COS_DEFAULT_DOMAIN = `${STORAGE_BUCKET}.cos.${STORAGE_REGION}.myqcloud.com`;

function buildCosUrl(key) {
  if (!key) {
    return '';
  }
  return `https://${COS_DEFAULT_DOMAIN}/${key}`;
}

function extractKeyFromUrl(url) {
  if (!url) {
    return '';
  }
  try {
    const parsed = new URL(url);
    return parsed.pathname.replace(/^\/+/, '');
  } catch (err) {
    // 如果本身就是相对路径（如 photos/...），直接返回
    if (url.startsWith('photos/')) {
      return url;
    }
    return '';
  }
}

function generateSignedGetUrl(key, fallbackUrl = '') {
  const baseUrl = key ? buildCosUrl(key) : (fallbackUrl || '');
  if (!key || !cos) {
    return baseUrl;
  }
  try {
    if (typeof cos.getAuth === 'function') {
      const auth = cos.getAuth({
        Method: 'GET',
        Key: key,
        Expires: SIGNED_GET_URL_EXPIRES,
        SignHost: false
      });
      return `${baseUrl}?${auth}`;
    }
  } catch (error) {
    console.error('❌ 生成GET预签名URL失败:', error);
  }
  return baseUrl;
}

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
      const { order_id, stage_id, file_count = 1, file_types = [] } = data || {};
      
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
      
      // 检查COS配置，必须配置才能上传
      if (!cos) {
        return {
          statusCode: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: 'COS未配置：请配置TENCENT_SECRET_ID和TENCENT_SECRET_KEY环境变量',
            error: 'COS_NOT_CONFIGURED'
          })
        };
      }
      
      // 辅助函数：根据MIME类型判断媒体类型和扩展名
      function getMediaInfo(mimeType) {
        if (!mimeType) {
          return { mediaType: 'photo', ext: 'jpg', folder: 'photos' };
        }
        
        const mime = mimeType.toLowerCase();
        if (mime.startsWith('video/')) {
          // 视频类型
          if (mime.includes('mp4')) {
            return { mediaType: 'video', ext: 'mp4', folder: 'videos' };
          } else if (mime.includes('mov')) {
            return { mediaType: 'video', ext: 'mov', folder: 'videos' };
          } else if (mime.includes('avi')) {
            return { mediaType: 'video', ext: 'avi', folder: 'videos' };
          } else if (mime.includes('webm')) {
            return { mediaType: 'video', ext: 'webm', folder: 'videos' };
          } else {
            return { mediaType: 'video', ext: 'mp4', folder: 'videos' };
          }
        } else {
          // 图片类型（默认）
          if (mime.includes('png')) {
            return { mediaType: 'photo', ext: 'png', folder: 'photos' };
          } else {
            return { mediaType: 'photo', ext: 'jpg', folder: 'photos' };
          }
        }
      }
      
      const upload_urls = [];
      
      // 生成预签名 PUT URL（支持照片和视频）
      for (let i = 0; i < file_count; i++) {
          const timestamp = Date.now();
          
          // 获取当前文件的类型信息
          const fileType = file_types[i] || 'image/jpeg'; // 默认图片
          const mediaInfo = getMediaInfo(fileType);
          const { mediaType, ext, folder } = mediaInfo;
          
          // 缩短Key路径：使用order_id的hash（前16字符）和简化的stage_id
          // 照片格式：photos/${order_id_hash}/${stage_id_num}/${timestamp}_${i}.jpg
          // 视频格式：videos/${order_id_hash}/${stage_id_num}/${timestamp}_${i}.mp4
          const crypto = require('crypto');
          const orderIdHash = crypto.createHash('md5').update(order_id).digest('hex').substring(0, 16);
          // STAGE001 -> 1, STAGE002 -> 2, 等等
          const stageIdNum = stage_id.replace('STAGE', '').replace(/^0+/, '') || '0';
          const file_id = `${timestamp}_${i}.${ext}`;
          const key = `${folder}/${orderIdHash}/${stageIdNum}/${file_id}`;
          
          // 保存原始信息到metadata，用于后续查询
          const filePrefix = mediaType === 'video' ? 'video' : 'photo';
          const originalPath = `${folder}/${order_id}/${stage_id}/${filePrefix}_${order_id}_${stage_id}_${timestamp}_${i}.${ext}`;
          
          // 优先使用 getAuth 生成签名，并明确不对 host 签名（SignHost: false）
          const presignUrl = await new Promise((resolve, reject) => {
            try {
              if (cos && typeof cos.getAuth === 'function') {
                console.log('🔧 优先使用cos.getAuth生成PUT预签名URL (SignHost: false)');
                const auth = cos.getAuth({
                  Method: 'PUT',
                  Key: key,
                  Expires: 300,
                  SignHost: false
                });
                const base = `https://${STORAGE_BUCKET}.cos.${STORAGE_REGION}.myqcloud.com/${key}`;
                const url = `${base}?${auth}`;
                try {
                  const u = new URL(url);
                  const qhl = u.searchParams.get('q-header-list') || '';
                  console.log(`📋 getAuth 结果 q-header-list: ${qhl || '空'}`);
                } catch (e) {}
                resolve(url);
              } else {
                console.log('⚠️ cos.getAuth 不可用，回退到 getObjectUrl');
                cos.getObjectUrl(
                  {
                    Bucket: STORAGE_BUCKET,
                    Region: STORAGE_REGION,
                    Key: key,
                    Method: 'PUT',
                    Sign: true,
                    Expires: 300,
                    SignHost: false
                  },
                  (err, data) => {
                    if (err) return reject(err);
                    const url = data && data.Url ? data.Url : (typeof data === 'string' ? data : null);
                    resolve(url);
                  }
                );
              }
            } catch (e) {
              reject(e);
            }
          });
          
          // 构建可访问的公共URL
          const defaultDomain = `${STORAGE_BUCKET}.cos.${STORAGE_REGION}.myqcloud.com`;
          const envDomain = (STORAGE_DOMAIN || "").trim();
          const isLegacyTcbDomain = envDomain && envDomain.endsWith('tcb.qcloud.la');
          const finalDomain = envDomain && !isLegacyTcbDomain ? envDomain : defaultDomain;
          const publicUrl = `https://${finalDomain}/${key}`;
          
          upload_urls.push({
            file_id: `${filePrefix}_${order_id}_${stage_id}_${timestamp}_${i}.${ext}`, // 保留原始file_id用于数据库
            upload_url: presignUrl,
            cloud_path: key, // 使用缩短的Key路径
            original_path: originalPath, // 保存原始路径用于查询
            storage_type: 'cos_presigned_put',
            uploadMethod: 'presigned_put',
            photo_url: publicUrl,
            thumbnail_url: publicUrl,
            media_type: mediaType, // 'photo' 或 'video'
            file_extension: ext,
            metadata: {
              order_id: order_id,
              stage_id: stage_id,
              order_id_hash: orderIdHash,
              stage_id_num: stageIdNum,
              media_type: mediaType
            }
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
      // 已废弃：只支持预签名直传
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: false, 
          message: '此上传方式已废弃，请使用预签名直传方式（get_upload_url + confirm_upload）',
          error: 'DEPRECATED_UPLOAD_METHOD'
        })
      };
    }
    
    if (action === 'cloud_upload') {
      // 已废弃：只支持预签名直传
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: false, 
          message: '此上传方式已废弃，请使用预签名直传方式（get_upload_url + confirm_upload）',
          error: 'DEPRECATED_UPLOAD_METHOD'
        })
      };
    }
    
    if (action === 'confirm_upload') {
      const { order_id, stage_id, uploaded_files, description = '' } = data || {};
      
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
      
      const saved_photos = [];
      const errors = [];
      
      // 获取订单信息（用于日志）
      let order = null;
      try {
        const orderResult = await db.collection('orders').where({ _id: order_id }).get();
        order = orderResult.data && orderResult.data.length > 0 ? orderResult.data[0] : null;
      } catch (err) {
        console.warn('获取订单信息失败:', err);
      }
      
      // 获取当前阶段已有的照片数量（用于sort_order）
      let existingPhotoCount = 0;
      try {
        const existingPhotos = await db.collection('photos')
          .where({
            order_id: order_id,
            stage_id: stage_id,
            is_deleted: false
          })
          .get();
        existingPhotoCount = existingPhotos.data ? existingPhotos.data.length : 0;
      } catch (err) {
        console.warn('获取已有照片数量失败:', err);
      }
      
      // 保存每张照片到数据库
      for (let i = 0; i < uploaded_files.length; i++) {
        const file = uploaded_files[i];
        
        try {
          const cloudPath = file.cloud_path || file.cloudPath || extractKeyFromUrl(file.cloud_path) || extractKeyFromUrl(file.photo_url) || extractKeyFromUrl(file.thumbnail_url);
          const baseUrl = cloudPath ? buildCosUrl(cloudPath) : (file.photo_url || file.thumbnail_url || '');
          
          // 构建媒体记录（支持照片和视频）
          const mediaType = file.media_type || (file.file_type && file.file_type.startsWith('video/') ? 'video' : 'photo');
          const photoRecord = {
            order_id: order_id,
            stage_id: stage_id,
            stage_name: getStageName(stage_id),
            file_id: file.file_id || file.fileID || `${mediaType === 'video' ? 'video' : 'photo'}_${order_id}_${stage_id}_${Date.now()}_${i}.${file.file_extension || (mediaType === 'video' ? 'mp4' : 'jpg')}`,
            photo_url: baseUrl,
            thumbnail_url: baseUrl,
            storage_type: file.storage_type || 'cos_presigned_put',
            file_name: file.file_name || '未命名',
            file_size: file.file_size || 0,
            file_type: file.file_type || (mediaType === 'video' ? 'video/mp4' : 'image/jpeg'),
            media_type: mediaType, // 'photo' 或 'video'
            upload_time: new Date().toISOString(),
            created_at: new Date().toISOString(),
            description: description || '',
            sort_order: existingPhotoCount + i,
            is_deleted: false,
            cloud_path: cloudPath
          };
          
          // 保存到数据库
          const addResult = await db.collection('photos').add(photoRecord);
          
          console.log(`✅ 照片记录已保存到数据库: ${photoRecord.file_id}`);
          
          const savedEntry = {
            _id: addResult.id,
            ...photoRecord
          };
          
          const signedUrl = generateSignedGetUrl(cloudPath, baseUrl);
          if (signedUrl) {
            savedEntry.photo_url = signedUrl;
            savedEntry.thumbnail_url = signedUrl;
            savedEntry.signed_url_expires_in = SIGNED_GET_URL_EXPIRES;
            savedEntry.is_signed_url = true;
          }
          
          saved_photos.push(savedEntry);
          
        } catch (error) {
          console.error(`❌ 保存照片记录失败 (${i+1}/${uploaded_files.length}):`, error);
          errors.push({
            index: i,
            file_name: file.file_name || '未知文件',
            error: error.message
          });
        }
      }
      
      // 记录操作日志（只在有成功保存的照片时记录）
      if (saved_photos.length > 0) {
        try {
          const customerName = order ? order.customer_name : '未知客户';
          const stageName = getStageName(stage_id);
          
          // 统计照片和视频数量
          const photoCount = saved_photos.filter(p => p.media_type === 'photo' || !p.media_type).length;
          const videoCount = saved_photos.filter(p => p.media_type === 'video').length;
          const mediaTypeText = photoCount > 0 && videoCount > 0 
            ? `照片${photoCount}张、视频${videoCount}个`
            : (videoCount > 0 ? `视频${videoCount}个` : `照片${photoCount}张`);
          
          await logOperation({
            type: '媒体上传',
            operator: data.operator || 'admin',
            description: `上传媒体：客户 ${customerName} - ${stageName} (${mediaTypeText})`,
            order_id: order_id,
            order_number: order ? order.order_number : '',
            metadata: {
              customer_name: customerName,
              stage_name: stageName,
              file_count: saved_photos.length,
              photo_count: photoCount,
              video_count: videoCount,
              description: description
            }
          });
          
          console.log(`✅ 操作日志记录成功`);
        } catch (logError) {
          console.error('❌ 记录照片上传日志失败:', logError);
        }
      }
      
      // 返回结果
      if (saved_photos.length === 0) {
        return {
          statusCode: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false,
            message: '所有照片保存失败',
            errors: errors
          })
        };
      }
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ 
          success: true,
          data: { 
            saved_photos: saved_photos,
            total_saved: saved_photos.length,
            total_uploaded: uploaded_files.length,
            errors: errors.length > 0 ? errors : undefined
          },
          message: errors.length > 0 
            ? `成功保存 ${saved_photos.length} 张照片，${errors.length} 张失败`
            : `成功保存 ${saved_photos.length} 张照片`
        })
      };
    }
    
    if (action === 'delete') {
      const { photo_id, operator = 'admin', reason = '', delete_from_storage = true } = data || {};
      
      if (!photo_id) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '缺少必要参数: photo_id' 
          })
        };
      }
      
      console.log(`🗑️ 请求删除媒体: ${photo_id}`);
      
      try {
        // 查询照片记录
        const photoResult = await db.collection('photos')
          .where({ _id: photo_id, is_deleted: false })
          .get();
        
        if (!photoResult.data || photoResult.data.length === 0) {
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ 
              success: false, 
              message: '媒体不存在或已删除' 
            })
          };
        }
        
        const photo = photoResult.data[0];
        const now = new Date().toISOString();
        
        // 软删除数据库记录
        await db.collection('photos')
          .where({ _id: photo_id })
          .update({
            is_deleted: true,
            deleted_at: now,
            updated_at: now,
            delete_reason: reason
          });
        
        let cos_deleted = false;
        let cos_error = null;
        
        // 可选：删除COS文件
        if (delete_from_storage) {
          const cosKey = photo.cloud_path || extractKeyFromUrl(photo.photo_url) || extractKeyFromUrl(photo.thumbnail_url);
          if (cos && cosKey) {
            console.log(`🧹 尝试从COS删除文件: ${cosKey}`);
            try {
              await new Promise((resolve, reject) => {
                cos.deleteObject(
                  {
                    Bucket: STORAGE_BUCKET,
                    Region: STORAGE_REGION,
                    Key: cosKey
                  },
                  (err, data) => {
                    if (err) {
                      return reject(err);
                    }
                    resolve(data);
                  }
                );
              });
              cos_deleted = true;
              console.log('✅ COS文件已删除');
            } catch (err) {
              cos_error = err.message || String(err);
              console.error('❌ 删除COS文件失败:', err);
            }
          } else {
            console.log('ℹ️ 无可删除的COS文件或COS未配置');
          }
        }
        
        // 记录操作日志
        try {
          await logOperation({
            type: '媒体删除',
            operator,
            description: `删除媒体：${photo.stage_name || photo.stage_id} - ${photo.file_name || photo.media_type}`,
            order_id: photo.order_id || '',
            metadata: {
              photo_id,
              stage_id: photo.stage_id,
              media_type: photo.media_type,
              cos_deleted: cos_deleted,
              delete_reason: reason
            }
          });
        } catch (logErr) {
          console.error('❌ 记录媒体删除日志失败:', logErr);
        }
        
        return {
          statusCode: 200,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: true,
            data: { 
              photo_id,
              cos_deleted,
              cos_error
            },
            message: cos_error 
              ? '媒体已删除，但删除COS文件时出现问题'
              : '媒体删除成功'
          })
        };
      } catch (error) {
        console.error('❌ 删除媒体失败:', error);
        return {
          statusCode: 500,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify({ 
            success: false, 
            message: '删除媒体失败',
            error: error.message
          })
        };
      }
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
