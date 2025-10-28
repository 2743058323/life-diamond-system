// 操作日志查询云函数
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

exports.main = async function(event, context) {
    console.log('=== 操作日志查询云函数 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        // 解析请求参数
        let body = {};
        let action = '';
        
        if (event.httpMethod === 'POST' || event.path === '/api/admin/logs') {
            try {
                if (event.body) {
                    body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                    action = body.action || 'list';
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                action = 'list'; // 默认操作
            }
        } else if (event.body) {
            // 兼容直接调用的格式
            body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
            action = body.action || 'list';
        } else {
            action = 'list';
        }
        
        console.log('Action:', action);
        console.log('Body:', body);
        
        if (action === 'list') {
            console.log('开始获取操作日志列表...');
            
            try {
                // 获取所有操作日志（按时间倒序）
                const logsResult = await db.collection('operation_logs')
                    .orderBy('timestamp', 'desc')
                    .limit(1000)
                    .get();
                
                const logs = logsResult.data || [];
                
                console.log(`找到 ${logs.length} 条操作日志`);
                
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: true,
                        data: {
                            logs: logs
                        },
                        message: '获取操作日志成功'
                    })
                };
            } catch (dbError) {
                console.error('数据库查询失败:', dbError);
                // 如果集合不存在，返回空列表
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: true,
                        data: {
                            logs: []
                        },
                        message: '集合不存在，返回空列表'
                    })
                };
            }
        } else {
            return {
                statusCode: 400,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '不支持的操作'
                })
            };
        }
    } catch (error) {
        console.error('操作日志查询失败:', error);
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: false,
                message: `操作日志查询失败: ${error.message}`,
                error: error.toString()
            })
        };
    }
};

