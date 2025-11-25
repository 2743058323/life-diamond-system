// 客户订单详情查询 - 优化版本（过滤未开始阶段）
const cloudbase = require('@cloudbase/node-sdk');
const COS = require('cos-nodejs-sdk-v5');

const {
    TENCENT_SECRET_ID,
    TENCENT_SECRET_KEY,
    STORAGE_REGION = 'ap-shanghai',
    STORAGE_BUCKET = 'life-diamond-photos-1379657467',
    COS_GET_SIGNED_URL_EXPIRES = '3600'
} = process.env;

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

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

exports.main = async function(event, context) {
    console.log('=== 客户订单详情查询 - 优化版本 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        // 解析请求参数
        var requestData = {};
        var orderId = '';
        
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    requestData = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                requestData = {};
            }
        } else if (event.httpMethod === 'GET') {
            requestData = event.queryStringParameters || {};
        }
        
        // 从不同来源获取 order_id
        orderId = requestData.order_id || 
                 (event.pathParameters && event.pathParameters.order_id) || 
                 event.order_id || '';
        
        console.log('请求参数:', JSON.stringify(requestData));
        console.log('订单ID:', orderId);
      
        if (!orderId) {
            console.log('订单ID为空');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '订单ID不能为空',
                    data: null
                })
            };
        }
      
      // 获取订单基本信息 - 按_id字段查询（排除软删除的订单）
      const orderResult = await db.collection('orders')
        .where({
          _id: orderId,
          is_deleted: db.command.neq(true)
        })
        .get();
      
      let orderInfo = null;
      
      if (orderResult.data && orderResult.data.length > 0) {
        orderInfo = orderResult.data[0];
      }
      
      if (!orderInfo) {
        return {
          statusCode: 200,
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
          },
          body: JSON.stringify({
            success: false,
            message: '订单不存在或已删除'
          })
        };
      }
      
      // 获取进度时间轴
      const progressResult = await db.collection('order_progress')
        .where({
          order_id: orderId
        })
        .orderBy('stage_order', 'asc')
        .get();
      
      // 获取照片信息
      const photosResult = await db.collection('photos')
        .where({
          order_id: orderId,
          is_deleted: false
        })
        .orderBy('stage_id', 'asc')
        .orderBy('sort_order', 'asc')
        .get();
      
      // 阶段ID到名称的映射
      const stageNameMap = {
        'STAGE001': '进入实验室',
        'STAGE002': '碳化提纯',
        'STAGE003': '石墨化',
        'STAGE004': '高温高压培育生长',
        'STAGE005': '钻胚提取',
        'STAGE006': '切割',
        'STAGE007': '认证溯源',
        'STAGE008': '镶嵌钻石'
      };
      
      // 按阶段分组照片
      const photosByStage = {};
      for (const photo of photosResult.data) {
        const stageName = stageNameMap[photo.stage_id] || photo.stage_name || '未知阶段';
        if (!photosByStage[stageName]) {
          photosByStage[stageName] = [];
        }

        const cloudPath = photo.cloud_path || extractKeyFromUrl(photo.photo_url) || extractKeyFromUrl(photo.thumbnail_url);
        const baseUrl = cloudPath ? buildCosUrl(cloudPath) : (photo.photo_url || '');
        const signedUrl = generateSignedGetUrl(cloudPath, baseUrl);

        photosByStage[stageName].push({
          photo_url: signedUrl,
          thumbnail_url: signedUrl,
          description: photo.description,
          upload_time: photo.upload_time,
          media_type: photo.media_type || (photo.file_type && photo.file_type.startsWith('video/') ? 'video' : 'photo'), // 添加媒体类型
          file_type: photo.file_type || 'image/jpeg', // 添加文件类型
          file_name: photo.file_name || '', // 添加文件名
          _id: photo._id || '' // 添加ID用于调试
        });
      }
      
      // 根据调用来源决定显示哪些进度记录
      let filteredProgress;
      
      // 检查是否是管理员端调用（通过请求头判断）
      const isAdminCall = event.headers && (
        event.headers['x-administrator'] === 'true' ||
        event.headers['user-agent'] && event.headers['user-agent'].includes('admin')
      );
      
      if (isAdminCall) {
        // 管理员端：显示所有进度记录
        console.log('管理员端调用：显示所有进度记录');
        filteredProgress = progressResult.data.sort((a, b) => {
          const statusOrder = { 'completed': 3, 'in_progress': 2, 'pending': 1 };
          return statusOrder[b.status] - statusOrder[a.status];
        });
      } else {
        // 客户端：只显示已开始的阶段（completed 和 in_progress）
        console.log('客户端调用：只显示已开始的阶段');
        filteredProgress = progressResult.data.filter(progress => {
          return progress.status === 'completed' || progress.status === 'in_progress';
        }).sort((a, b) => {
          const statusOrder = { 'completed': 2, 'in_progress': 1 };
          return statusOrder[b.status] - statusOrder[a.status];
        });
      }
      
      console.log('数据库查询成功！');
      console.log('原始进度记录数:', progressResult.data.length);
      console.log('过滤后进度记录数:', filteredProgress.length);
      console.log('返回数据:', JSON.stringify({
          order_info: orderInfo,
          progress_timeline: filteredProgress,
          photos: Object.keys(photosByStage).map(stageName => ({
              stage_name: stageName,
              photos: photosByStage[stageName]
          }))
      }, null, 2));
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: true,
                data: {
                    order_info: {
                        order_id: orderInfo._id,
                        order_number: orderInfo.order_number,
                        customer_name: orderInfo.customer_name,
                        customer_phone: orderInfo.customer_phone,
                        diamond_type: orderInfo.diamond_type,
                        diamond_size: orderInfo.diamond_size,
                        special_requirements: orderInfo.special_requirements,
                        order_status: orderInfo.order_status,
                        progress_percentage: orderInfo.progress_percentage,
                        created_at: orderInfo.created_at
                    },
                    progress_timeline: filteredProgress.map(progress => ({
                        stage_id: progress.stage_id,
                        stage_name: progress.stage_name,
                        status: progress.status,
                        started_at: progress.started_at,
                        completed_at: progress.completed_at,
                        notes: progress.notes,
                        stage_order: progress.stage_order
                    })),
                    photos: Object.keys(photosByStage).map(stageName => ({
                        stage_name: stageName,
                        photos: photosByStage[stageName]
                    }))
                },
                message: '查询成功'
            })
        };
        
    } catch (error) {
        console.error('云函数执行错误:', error);
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: false,
                message: '服务器内部错误: ' + error.message,
                data: null
            })
        };
    }
};
