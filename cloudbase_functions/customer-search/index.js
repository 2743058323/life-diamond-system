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
        var searchType = '';  // 查询类型：name, phone, email, order_number
        var searchValue = '';
        
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    var body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                    searchType = body.search_type || 'phone';  // 默认按电话查询
                    searchValue = body.search_value || body.customer_name || '';
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                searchType = 'phone';
                searchValue = '';
            }
        } else {
            // GET请求支持多种参数
            searchType = event.search_type || 'phone';
            searchValue = event.search_value || event.customer_name || event.order_number || event.customer_phone || event.customer_email || '';
        }
        
        console.log('查询类型:', searchType);
        console.log('查询值:', searchValue);
        
        if (!searchValue || !searchValue.trim()) {
            console.log('查询值为空，返回错误');
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: false,
                    message: '查询内容不能为空',
                    data: []
                })
            };
        }
        
        // 构建查询条件
        var queryCondition = {
            is_deleted: db.command.neq(true)
        };
        
        // 根据查询类型设置查询字段
        switch(searchType) {
            case 'order_number':
                queryCondition.order_number = searchValue.trim();
                break;
            case 'phone':
                queryCondition.customer_phone = searchValue.trim();
                break;
            case 'email':
                queryCondition.customer_email = searchValue.trim();
                break;
            case 'name':
            default:
                queryCondition.customer_name = searchValue.trim();
                break;
        }
        
        // 查询数据库（排除软删除的订单）
        console.log('开始查询数据库...');
        console.log('查询条件:', JSON.stringify(queryCondition));
        const result = await db.collection('orders')
            .where(queryCondition)
            .get();
        
        console.log('数据库查询成功！');
        console.log('数据库查询结果:', JSON.stringify(result, null, 2));
        
        var responseData = result.data || [];
        var searchTypeName = {
            'name': '姓名',
            'phone': '电话',
            'email': '邮箱',
            'order_number': '订单号'
        }[searchType] || '信息';
        
        var response = {
            success: true,
            data: responseData,
            message: '根据' + searchTypeName + '查询成功，找到 ' + responseData.length + ' 个订单'
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
