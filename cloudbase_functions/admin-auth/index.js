// 管理员登录认证 - 修复版本
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

// 记录操作日志（内联函数，避免文件依赖问题）
async function logOperation(params) {
    try {
        const {
            type,
            operator = 'system',
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

exports.main = async function(event, context) {
    console.log('=== 管理员登录认证 - 修复版本 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        // 解析请求参数
        var requestData = {};
        
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    requestData = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                requestData = {};
            }
        } else {
            requestData = event.queryStringParameters || {};
        }
        
        console.log('请求参数:', JSON.stringify(requestData));
        
        // 提取用户名和密码
        var username = requestData.username || '';
        var password = requestData.password || '';
        
        console.log('用户名:', username);
        console.log('密码:', password);
        
        if (!username || !password) {
            console.log('用户名或密码为空');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '用户名和密码不能为空',
                    data: null
                })
            };
        }
        
        // 执行数据库操作
        console.log('开始查询管理员账户...');
        
        // 先查询用户名是否存在
        const userResult = await db.collection('admins')
            .where({ username: username })
            .get();
        
        console.log('用户名查询结果:', JSON.stringify(userResult, null, 2));
        
        if (userResult.data.length === 0) {
            console.log('用户名不存在');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '用户名或密码错误',
                    data: null
                })
            };
        }
        
        var user = userResult.data[0];
        
        // 检查账户是否被禁用
        if (!user.is_active) {
            console.log('账户已被禁用');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '账户已被禁用，请联系管理员',
                    data: null,
                    error_code: 'ACCOUNT_DISABLED'
                })
            };
        }
        
        // 检查密码是否正确
        if (user.password !== password) {
            console.log('密码错误');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '用户名或密码错误',
                    data: null
                })
            };
        }
        
        console.log('找到管理员账户:', JSON.stringify(user, null, 2));
        
        // 更新最后登录时间
        const currentTime = new Date().toISOString();
        try {
            await db.collection('admins')
                .where({ _id: user._id })
                .update({
                    last_login: currentTime
                });
            console.log('✅ 已更新最后登录时间');
        } catch (updateError) {
            console.error('❌ 更新最后登录时间失败:', updateError);
            // 不影响登录流程
        }
        
        var responseData = {
            token: 'admin_token_' + Date.now(),
            user: {
                user_id: user._id,
                username: user.username,
                real_name: user.real_name,
                role: user.role
            },
            expires_in: 86400
        };
        
        // 记录登录操作日志
        await logOperation({
            type: '用户登录',
            operator: user.username,
            description: `管理员登录：${user.real_name} (${user.username})`,
            metadata: {
                user_id: user._id,
                role: user.role,
                real_name: user.real_name
            }
        });
        
        console.log('准备返回响应:', JSON.stringify(responseData, null, 2));
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: true,
                data: responseData,
                message: '登录成功'
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
