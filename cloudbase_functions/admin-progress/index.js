// 管理员进度管理云函数 - 完整版本
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

exports.main = async function(event, context) {
    console.log('=== 管理员进度管理云函数 - 完整版本 ===');
    
    try {
        // 解析请求参数
        const requestData = JSON.parse(event.body || '{}');
        const action = requestData.action || '';
        const progressData = requestData.data || {};
        
        console.log('操作类型:', action);
        console.log('进度数据:', JSON.stringify(progressData));
        
        if (action === 'list') {
            // 获取进度列表
            const orderId = progressData.order_id || '';
            
            if (!orderId) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: '缺少订单ID',
                        data: null
                    })
                };
            }
            
            // 查询进度记录前，先检查订单是否已删除
            const orderCheck = await db.collection('orders')
                .where({ _id: orderId, is_deleted: db.command.neq(true) })
                .get();
            
            if (!orderCheck.data || orderCheck.data.length === 0) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: '订单不存在或已删除',
                        data: null
                    })
                };
            }
            
            // 查询进度记录
            const progressResult = await db.collection('order_progress')
                .where({ order_id: orderId })
                .orderBy('stage_order', 'asc')
                .get();
            
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: true,
                    message: '获取进度列表成功',
                    data: progressResult.data || []
                })
            };
        }
        
        if (action === 'update') {
            const orderId = progressData.order_id || '';
            const stageId = progressData.stage_id || '';
            const status = progressData.status || '';
            const notes = progressData.notes || '';
            
            if (!orderId || !stageId) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: '缺少订单ID或阶段ID',
                        data: null
                    })
                };
            }
            
            // 先检查订单是否已删除
            const orderCheck = await db.collection('orders')
                .where({ _id: orderId, is_deleted: db.command.neq(true) })
                .get();
            
            if (!orderCheck.data || orderCheck.data.length === 0) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: '订单不存在或已删除',
                        data: null
                    })
                };
            }
            
            // 获取所有进度记录
            const allProgressResult = await db.collection('order_progress')
                .where({ order_id: orderId })
                .orderBy('stage_order', 'asc')
                .get();
            
            const allProgress = allProgressResult.data || [];
            const currentStage = allProgress.find(p => p.stage_id === stageId);
            
            if (!currentStage) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: '未找到指定的阶段记录',
                        data: null
                    })
                };
            }
            
            // 状态验证逻辑
            let validationError = null;
            
            if (status === 'in_progress') {
                // 1. 检查是否有其他阶段正在进行中
                const inProgressStage = allProgress.find(p => p.status === 'in_progress' && p.stage_id !== stageId);
                if (inProgressStage) {
                    validationError = `无法开始新阶段，请先完成当前进行中的阶段：${inProgressStage.stage_name}`;
                }
                
                // 2. 检查是否可以开始这个阶段（前一个阶段必须已完成）
                if (!validationError) {
                    const currentOrder = currentStage.stage_order;
                    const previousStage = allProgress.find(p => p.stage_order === currentOrder - 1);
                    
                    if (previousStage && previousStage.status !== 'completed') {
                        validationError = `无法开始此阶段，请先完成前一个阶段：${previousStage.stage_name}`;
                    }
                }
                
                // 3. 检查当前阶段状态
                if (!validationError && currentStage.status === 'completed') {
                    validationError = '此阶段已完成，无法重新开始';
                }
            }
            
            if (status === 'completed') {
                // 1. 检查当前阶段是否真的是 in_progress
                if (currentStage.status !== 'in_progress') {
                    validationError = '只能完成正在进行中的阶段';
                }
            }
            
            if (validationError) {
                return {
                    statusCode: 200,
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Access-Control-Allow-Origin': '*'
                    },
                    body: JSON.stringify({
                        success: false,
                        message: validationError,
                        data: null
                    })
                };
            }
            
            // 更新进度记录
            const updateData = {
                status: status,
                notes: notes,
                updated_at: new Date().toISOString()
            };
            
            if (status === 'in_progress') {
                updateData.started_at = new Date().toISOString();
            }
            
            if (status === 'completed') {
                updateData.completed_at = new Date().toISOString();
            }
            
            await db.collection('order_progress')
                .where({ order_id: orderId, stage_id: stageId })
                .update(updateData);
            
            // 自动计算整体进度和更新订单状态
            const updatedProgressResult = await db.collection('order_progress')
                .where({ order_id: orderId })
                .orderBy('stage_order', 'asc')
                .get();
            
            const updatedProgress = updatedProgressResult.data || [];
            const totalStages = updatedProgress.length;
            const completedStages = updatedProgress.filter(p => p.status === 'completed').length;
            const inProgressStages = updatedProgress.filter(p => p.status === 'in_progress');
            
            // 计算进度百分比
            const progressPercentage = Math.round((completedStages / totalStages) * 100);
            
            // 确定当前阶段
            let currentStageName = '未开始';
            if (inProgressStages.length > 0) {
                currentStageName = inProgressStages[0].stage_name;
            } else if (completedStages === totalStages) {
                currentStageName = '已完成';
            } else if (completedStages > 0) {
                // 找到下一个未开始的阶段
                const nextStage = updatedProgress.find(p => p.status === 'pending');
                if (nextStage) {
                    currentStageName = nextStage.stage_name;
                }
            }
            
            // 确定订单状态
            let orderStatus = '待处理';
            if (completedStages === totalStages) {
                orderStatus = '已完成';
            } else if (completedStages > 0 || inProgressStages.length > 0) {
                orderStatus = '制作中';
            }
            
            // 更新订单信息
            await db.collection('orders')
                .where({ _id: orderId })
                .update({
                    progress_percentage: progressPercentage,
                    current_stage: currentStageName,
                    order_status: orderStatus,
                    updated_at: new Date().toISOString()
                });
            
            console.log(`订单 ${orderId} 进度更新: ${progressPercentage}%, 当前阶段: ${currentStageName}, 订单状态: ${orderStatus}`);
            
            // 记录操作日志
            // 获取订单信息
            const orderInfo = await db.collection('orders').where({ _id: orderId }).get();
            const order = orderInfo.data && orderInfo.data[0];
            
            if (order) {
                const logType = status === 'in_progress' ? '阶段开始' : '阶段完成';
                const stageName = currentStage.stage_name || stageId;
                const logDescription = `${logType}：客户 ${order.customer_name} - ${stageName}`;
                
                await logOperation({
                    type: logType,
                    operator: progressData.operator || 'admin',
                    description: logDescription,
                    order_id: orderId,
                    order_number: order.order_number,
                    metadata: {
                        customer_name: order.customer_name,
                        stage_name: stageName,
                        progress_percentage: progressPercentage
                    }
                });
            }
            
            return {
                statusCode: 200,
                headers: {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                },
                body: JSON.stringify({
                    success: true,
                    message: '进度更新成功',
                    data: {
                        order_id: orderId,
                        stage_id: stageId,
                        status: status,
                        notes: notes,
                        progress_percentage: progressPercentage,
                        current_stage: currentStageName,
                        order_status: orderStatus
                    }
                })
            };
        }
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: false,
                message: '不支持的操作类型',
                data: null
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
