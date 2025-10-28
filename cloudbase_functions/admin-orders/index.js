// 管理员订单管理云函数 - 简化版本
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

// 生成订单编号
function generateOrderNumber() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const timestamp = Date.now().toString().slice(-6);
    return 'LD' + year + month + day + timestamp;
}

exports.main = async function(event, context) {
    console.log('=== 管理员订单管理云函数 - 简化版本 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        var action = '';
        var requestData = {};
        
        // 解析请求参数
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    var body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                    action = body.action || 'create';
                    requestData = body.data || body;
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                action = 'create';
                requestData = {};
            }
        } else if (event.httpMethod === 'GET') {
            action = 'list';
            requestData = event.queryStringParameters || {};
        }
        
        console.log('操作类型:', action);
        console.log('请求数据:', JSON.stringify(requestData));
        
        var result = {};
        
        if (action === 'list') {
            // 获取订单列表
            console.log('获取订单列表...');
            
            var page = parseInt(requestData.page || '1');
            var limit = parseInt(requestData.limit || requestData.page_size || '20');
            var status = requestData.status || 'all';
            var search = requestData.search || '';
            
            var query = db.collection('orders');
            
            // 过滤已删除的订单（软删除）
            query = query.where({ is_deleted: { $ne: true } });
            
            // 添加状态过滤
            if (status !== 'all') {
                query = query.where({ order_status: status });
            }
            
            // 添加搜索过滤
            if (search) {
                query = query.where({ customer_name: search });
            }
            
            // 获取总数
            const countResult = await query.count();
            const totalCount = countResult.total;
            
            // 分页查询
            const offset = (page - 1) * limit;
            const ordersResult = await query
                .orderBy('created_at', 'desc')
                .skip(offset)
                .limit(limit)
                .get();
            
            result = {
                success: true,
                data: {
                    orders: ordersResult.data || [],
                    pagination: {
                        current_page: page,
                        page_size: limit,
                        total_count: totalCount,
                        total_pages: Math.ceil(totalCount / limit)
                    }
                },
                message: '获取订单列表成功'
            };
            
        } else if (action === 'create') {
            // 创建订单
            console.log('创建订单...');
            
            var newOrder = {
                order_number: generateOrderNumber(),
                customer_name: requestData.customer_name || '',
                customer_phone: requestData.customer_phone || '',
                customer_email: requestData.customer_email || '',
                diamond_type: requestData.diamond_type || '',
                diamond_size: requestData.diamond_size || '',
                special_requirements: requestData.special_requirements || '',
                order_status: '待处理',
                current_stage: '进入实验室',
                progress_percentage: 0,
                estimated_completion: null,
                notes: '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            
            const createResult = await db.collection('orders').add(newOrder);
            const orderId = createResult.id;
            
            // 自动创建8个阶段的进度记录
            console.log('自动初始化进度记录...');
            console.log('订单ID:', orderId);
            
            const stagesResult = await db.collection('stages').orderBy('stage_order', 'asc').get();
            const stages = stagesResult.data || [];
            
            console.log(`找到 ${stages.length} 个阶段，开始创建进度记录...`);
            console.log('阶段数据:', JSON.stringify(stages, null, 2));
            
            if (stages.length === 0) {
                console.error('❌ 没有找到任何阶段数据！');
                // 使用硬编码的阶段数据作为备用
                const fallbackStages = [
                    { stage_id: 'STAGE001', stage_name: '进入实验室', stage_order: 1 },
                    { stage_id: 'STAGE002', stage_name: '碳化提纯', stage_order: 2 },
                    { stage_id: 'STAGE003', stage_name: '钻胚提取', stage_order: 3 },
                    { stage_id: 'STAGE004', stage_name: '高温高压培育生长', stage_order: 4 },
                    { stage_id: 'STAGE005', stage_name: '石墨化', stage_order: 5 },
                    { stage_id: 'STAGE006', stage_name: '切割', stage_order: 6 },
                    { stage_id: 'STAGE007', stage_name: '认证溯源', stage_order: 7 },
                    { stage_id: 'STAGE008', stage_name: '镶嵌钻石', stage_order: 8 }
                ];
                console.log('使用备用阶段数据...');
                stages.push(...fallbackStages);
            }
            
            for (let stage of stages) {
                try {
                    const progressRecord = {
                        order_id: orderId,
                        stage_id: stage.stage_id,
                        stage_name: stage.stage_name,
                        status: 'pending',
                        stage_order: stage.stage_order,
                        estimated_completion: null,
                        notes: '',
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    };
                    
                    console.log(`创建进度记录: ${JSON.stringify(progressRecord)}`);
                    const progressResult = await db.collection('order_progress').add(progressRecord);
                    console.log(`✅ 进度记录创建成功: ${stage.stage_name}, ID: ${progressResult.id}`);
                } catch (error) {
                    console.error(`❌ 创建进度记录失败: ${stage.stage_name}`, error);
                }
            }
            
            console.log('所有进度记录创建完成');
            
            // 记录操作日志
            await logOperation({
                type: '订单创建',
                operator: requestData.operator || 'admin',
                description: `创建订单：${newOrder.order_number} - ${newOrder.customer_name}`,
                order_id: orderId,
                order_number: newOrder.order_number,
                metadata: {
                    customer_name: newOrder.customer_name,
                    diamond_type: newOrder.diamond_type
                }
            });
            
            result = {
                success: true,
                data: {
                    order_id: orderId,
                    order_number: newOrder.order_number,
                    ...newOrder
                },
                message: '订单创建成功，已自动初始化8个制作阶段'
            };
            
        } else if (action === 'update') {
            // 更新订单
            console.log('更新订单...');
            
            var orderId = requestData.order_id || '';
            if (!orderId) {
                result = {
                    success: false,
                    message: '订单ID不能为空',
                    data: null
                };
            } else {
                var updateData = {
                    updated_at: new Date().toISOString()
                };
                
                // 添加要更新的字段
                if (requestData.customer_name) updateData.customer_name = requestData.customer_name;
                if (requestData.customer_phone) updateData.customer_phone = requestData.customer_phone;
                if (requestData.customer_email) updateData.customer_email = requestData.customer_email;
                if (requestData.diamond_type) updateData.diamond_type = requestData.diamond_type;
                if (requestData.diamond_size) updateData.diamond_size = requestData.diamond_size;
                if (requestData.special_requirements !== undefined) updateData.special_requirements = requestData.special_requirements;
                if (requestData.order_status) updateData.order_status = requestData.order_status;
                if (requestData.notes !== undefined) updateData.notes = requestData.notes;
                
                // 先获取更新前的订单信息
                const oldOrderInfo = await db.collection('orders').where({ _id: orderId }).get();
                const oldOrder = oldOrderInfo.data && oldOrderInfo.data[0];
                
                // 执行更新
                await db.collection('orders').where({ _id: orderId }).update(updateData);
                
                // 获取更新后的订单信息
                const newOrderInfo = await db.collection('orders').where({ _id: orderId }).get();
                const newOrder = newOrderInfo.data && newOrderInfo.data[0];
                
                if (oldOrder && newOrder) {
                    // 构建字段中文名映射
                    const fieldNameMap = {
                        'customer_name': '客户姓名',
                        'customer_phone': '联系电话',
                        'customer_email': '邮箱',
                        'diamond_type': '钻石类型',
                        'diamond_size': '钻石大小',
                        'order_status': '订单状态',
                        'special_requirements': '特殊要求',
                        'notes': '备注',
                        'updated_at': '更新时间'
                    };
                    
                    // 构建详细的字段变更信息（包含新值和旧值的对比）
                    const fieldChanges = {};
                    const changedFieldNames = [];  // 只记录真正有变化的字段名
                    
                    Object.keys(updateData).forEach(key => {
                        if (key !== 'updated_at') {
                            const chineseName = fieldNameMap[key] || key;
                            const oldValue = oldOrder[key] || '';
                            const newValue = updateData[key] || '';
                            
                            // 如果值有变化，记录旧值和新值
                            if (oldValue !== newValue) {
                                fieldChanges[chineseName] = `${newValue} (原值: ${oldValue})`;
                                changedFieldNames.push(chineseName);  // 添加到变化字段列表
                            }
                        }
                    });
                    
                    // 生成操作描述（只显示真正有变化的字段）
                    const fieldsDesc = changedFieldNames.length > 0 
                        ? `(更新了${changedFieldNames.join('、')})` 
                        : '';
                    
                    // 记录操作日志
                    await logOperation({
                        type: '订单更新',
                        operator: requestData.operator || 'admin',
                        description: `更新订单：客户 ${newOrder.customer_name} ${fieldsDesc}`,
                        order_id: orderId,
                        order_number: newOrder.order_number,
                        metadata: {
                            customer_name: newOrder.customer_name,
                            ...fieldChanges  // 展开所有字段的新值和旧值对比
                        }
                    });
                }
                
                result = {
                    success: true,
                    data: updateData,
                    message: '订单更新成功'
                };
            }
            
        } else if (action === 'delete') {
            // 删除订单
            console.log('删除订单...');
            
            var orderId = requestData.order_id || '';
            if (!orderId) {
                result = {
                    success: false,
                    message: '订单ID不能为空',
                    data: null
                };
            } else {
                // 软删除：标记为已删除
                // 先获取订单信息
                const orderInfo = await db.collection('orders').where({ _id: orderId }).get();
                const order = orderInfo.data && orderInfo.data[0];
                
                await db.collection('orders').where({ _id: orderId }).update({
                    is_deleted: true,
                    deleted_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                });
                
                // 记录操作日志
                if (order) {
                    await logOperation({
                        type: '订单删除',
                        operator: requestData.operator || 'admin',
                        description: `删除订单：客户 ${order.customer_name}`,
                        order_id: orderId,
                        order_number: order.order_number,
                        metadata: {
                            customer_name: order.customer_name
                        }
                    });
                }
                
                result = {
                    success: true,
                    data: { order_id: orderId },
                    message: '订单删除成功'
                };
            }
            
        } else {
            result = {
                success: false,
                message: '不支持的操作类型: ' + action,
                data: null
            };
        }
        
        console.log('操作结果:', JSON.stringify(result));
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify(result)
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
