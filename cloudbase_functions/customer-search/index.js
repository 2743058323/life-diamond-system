// 直接返回数据的客户查询云函数
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

exports.main = async function(event, context) {
    console.log('=== 直接返回数据的客户查询云函数 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        // 解析请求参数
        var customerName = '';
        
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    var body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                    customerName = body.customer_name || '';
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                customerName = '';
            }
        } else {
            customerName = event.customer_name || '';
        }
        
        console.log('查询客户姓名:', customerName);
        
        if (!customerName) {
            console.log('客户姓名为空，返回错误');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '客户姓名不能为空',
                    data: []
                })
            };
        }
        
        // 查询数据库（排除软删除的订单）
        console.log('开始查询数据库...');
        const result = await db.collection('orders')
            .where({
                customer_name: customerName,
                is_deleted: db.command.neq(true)
            })
            .get();
        
        console.log('数据库查询成功！');
        console.log('数据库查询结果:', JSON.stringify(result, null, 2));
        
        var responseData = result.data || [];
        var response = {
            success: true,
            data: responseData,
            message: '查询成功，找到 ' + responseData.length + ' 个订单'
        };
        
        console.log('准备返回响应:', JSON.stringify(response, null, 2));
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify(response)
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
                data: []
            })
        };
    }
};
