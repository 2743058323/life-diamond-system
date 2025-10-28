// 管理员用户管理云函数 - 简化版本
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
    console.log('=== 管理员用户管理云函数 - 简化版本 ===');
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
            // 获取管理员用户列表
            console.log('获取管理员用户列表...');
            
            // 查询所有用户，不限制is_active状态
            const usersResult = await db.collection('admins')
                .orderBy('created_at', 'desc')
                .get();
            
            // 过滤敏感信息
            var users = (usersResult.data || []).map(user => ({
                user_id: user._id,
                username: user.username,
                real_name: user.real_name,
                role: user.role,
                email: user.email,
                last_login: user.last_login,
                created_at: user.created_at,
                is_active: user.is_active
            }));
            
            result = {
                success: true,
                data: {
                    users: users,
                    total_count: users.length
                },
                message: '获取用户列表成功'
            };
            
        } else if (action === 'create') {
            // 创建管理员用户
            console.log('创建管理员用户...');
            
            var newUser = {
                username: requestData.username || '',
                password: requestData.password || '',  // 注意：实际应用中应该加密
                real_name: requestData.real_name || '',
                role: requestData.role || 'operator',
                email: requestData.email || '',
                is_active: requestData.is_active !== undefined ? requestData.is_active : true,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                last_login: null
            };
            
            // 检查用户名是否已存在
            const existingUser = await db.collection('admins')
                .where({ username: newUser.username })
                .get();
            
            if (existingUser.data && existingUser.data.length > 0) {
                result = {
                    success: false,
                    message: '用户名已存在',
                    data: null
                };
            } else {
                const createResult = await db.collection('admins').add(newUser);
                
                // 记录操作日志
                await logOperation({
                    type: '用户创建',
                    operator: requestData.operator || 'admin',
                    description: `创建用户：${newUser.username} - ${newUser.real_name}`,
                    metadata: {
                        user_id: createResult.id,
                        username: newUser.username,
                        real_name: newUser.real_name,
                        role: newUser.role
                    }
                });
                
                result = {
                    success: true,
                    data: {
                        user_id: createResult.id,
                        username: newUser.username,
                        real_name: newUser.real_name,
                        role: newUser.role
                    },
                    message: '用户创建成功'
                };
            }
            
        } else if (action === 'update') {
            // 更新用户
            console.log('更新用户...');
            
            var userId = requestData.user_id || '';
            if (!userId) {
                result = {
                    success: false,
                    message: '用户ID不能为空',
                    data: null
                };
            } else {
                var updateData = {
                    updated_at: new Date().toISOString()
                };
                
                // 添加要更新的字段
                if (requestData.real_name !== undefined) updateData.real_name = requestData.real_name;
                if (requestData.email !== undefined) updateData.email = requestData.email;
                if (requestData.role !== undefined) updateData.role = requestData.role;
                if (requestData.is_active !== undefined) updateData.is_active = requestData.is_active;
                if (requestData.password) updateData.password = requestData.password; // 注意：实际应用中应该加密
                
                // 先查询更新前的用户信息
                const oldUserResult = await db.collection('admins')
                    .where({ _id: userId })
                    .get();
                
                const oldUser = oldUserResult.data && oldUserResult.data.length > 0 ? oldUserResult.data[0] : null;
                
                // 执行更新
                const updateResult = await db.collection('admins').where({ _id: userId }).update(updateData);
                
                // 查询更新后的用户信息
                const newUserResult = await db.collection('admins')
                    .where({ _id: userId })
                    .get();
                
                const newUser = newUserResult.data && newUserResult.data.length > 0 ? newUserResult.data[0] : null;
                
                // 记录操作日志
                if (oldUser && newUser) {
                    // 构建字段中文名映射
                    const fieldNameMap = {
                        'real_name': '真实姓名',
                        'email': '邮箱',
                        'role': '角色',
                        'is_active': '账户状态',
                        'password': '密码',
                        'updated_at': '更新时间'
                    };
                    
                    // 构建详细的字段变更信息（包含新值和旧值的对比）
                    const fieldChanges = {};
                    const changedFieldNames = [];  // 只记录真正有变化的字段名
                    
                    Object.keys(updateData).forEach(key => {
                        if (key !== 'updated_at' && key !== 'password') {
                            const chineseName = fieldNameMap[key] || key;
                            const oldValue = oldUser[key] || '';
                            const newValue = updateData[key];
                            
                            // 如果值有变化，记录旧值和新值
                            if (oldValue !== newValue) {
                                // 特殊处理不同类型的值
                                let oldValueStr = oldValue;
                                let newValueStr = newValue;
                                
                                if (key === 'is_active') {
                                    oldValueStr = oldValue ? '启用' : '禁用';
                                    newValueStr = newValue ? '启用' : '禁用';
                                } else if (key === 'role') {
                                    // 角色翻译
                                    const roleMap = {
                                        'admin': '管理员',
                                        'operator': '操作员',
                                        'viewer': '查看者'
                                    };
                                    oldValueStr = roleMap[oldValue] || oldValue;
                                    newValueStr = roleMap[newValue] || newValue;
                                }
                                
                                fieldChanges[chineseName] = `${newValueStr} (原值: ${oldValueStr})`;
                                changedFieldNames.push(chineseName);  // 添加到变化字段列表
                            }
                        }
                    });
                    
                    // 如果更新了密码，只记录"已修改"
                    if (updateData.password) {
                        fieldChanges['密码'] = '已修改';
                        changedFieldNames.push('密码');
                    }
                    
                    // 生成操作描述（只显示真正有变化的字段）
                    const fieldsDesc = changedFieldNames.length > 0 
                        ? `(更新了${changedFieldNames.join('、')})` 
                        : '';
                    
                    await logOperation({
                        type: '用户更新',
                        operator: requestData.operator || 'admin',
                        description: `更新用户：${newUser.real_name} (${newUser.username}) ${fieldsDesc}`,
                        metadata: {
                            username: newUser.username,
                            ...fieldChanges  // 展开所有字段的新值和旧值对比
                        }
                    });
                }
                
                result = {
                    success: true,
                    data: {
                        user_id: userId,
                        ...updateData
                    },
                    message: '用户更新成功'
                };
            }
            
        } else if (action === 'delete') {
            // 删除用户
            console.log('删除用户...');
            
            var userId = requestData.user_id || '';
            if (!userId) {
                result = {
                    success: false,
                    message: '用户ID不能为空',
                    data: null
                };
            } else {
                // 检查是否是最后一个管理员
                const adminCount = await db.collection('admins')
                    .where({ role: 'admin' })
                    .get();
                
                const userToDelete = await db.collection('admins')
                    .where({ _id: userId })
                    .get();
                
                if (userToDelete.data && userToDelete.data.length > 0) {
                    const user = userToDelete.data[0];
                    
                    // 如果是最后一个管理员，不允许删除
                    if (user.role === 'admin' && adminCount.data.length <= 1) {
                        result = {
                            success: false,
                            message: '不能删除最后一个系统管理员',
                            data: null
                        };
                    } else {
                        // 记录操作日志
                        await logOperation({
                            type: '用户删除',
                            operator: requestData.operator || 'admin',
                            description: `删除用户：${user.username} - ${user.real_name}`,
                            metadata: {
                                user_id: userId,
                                role: user.role
                            }
                        });
                        
                        await db.collection('admins').where({ _id: userId }).remove();
                        
                        result = {
                            success: true,
                            data: { user_id: userId },
                            message: '用户删除成功'
                        };
                    }
                } else {
                    result = {
                        success: false,
                        message: '用户不存在',
                        data: null
                    };
                }
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
