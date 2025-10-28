// 角色权限管理云函数
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
    console.log('=== 角色权限管理云函数 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        var action = '';
        var requestData = {};
        
        // 解析请求参数
        if (event.httpMethod === 'POST') {
            try {
                if (event.body) {
                    var body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
                    action = body.action || 'list';
                    requestData = body.data || body;
                }
            } catch (e) {
                console.log('解析POST body失败:', e);
                action = 'list';
                requestData = {};
            }
        } else if (event.httpMethod === 'GET') {
            action = 'list';
            requestData = event.queryStringParameters || {};
        } else {
            // 处理非HTTP请求（如控制台测试）
            action = 'list';
            requestData = {};
        }
        
        console.log('操作类型:', action);
        console.log('请求数据:', JSON.stringify(requestData));
        
        var result = {};
        
        if (action === 'list') {
            // 默认操作：获取角色列表
            console.log('获取角色列表...');
            
            try {
                const rolesCollection = db.collection('roles');
                const rolesResult = await rolesCollection.get();
                
                console.log('角色查询结果:', rolesResult);
                
                result = {
                    success: true,
                    message: '获取角色列表成功',
                    data: {
                        roles: rolesResult.data || []
                    }
                };
            } catch (error) {
                console.error('获取角色列表失败:', error);
                result = {
                    success: false,
                    message: '获取角色列表失败: ' + error.message,
                    data: null
                };
            }
        } else if (action === 'list_roles') {
            // 获取角色列表
            console.log('获取角色列表...');
            
            const rolesResult = await db.collection('roles')
                .where({ is_active: true })
                .orderBy('created_at', 'desc')
                .get();
            
            // 转换字段名：id -> _id (适配CloudBase的_id字段)
            const roles = (rolesResult.data || []).map(role => ({
                ...role,
                _id: role.id || role._id
            }));
            
            result = {
                success: true,
                data: {
                    roles: roles,
                    total_count: roles.length
                },
                message: '获取角色列表成功'
            };
            
        } else if (action === 'list_permissions') {
            // 获取权限列表
            console.log('获取权限列表...');
            
            const permissionsResult = await db.collection('permissions')
                .orderBy('category', 'asc')
                .orderBy('permission_name', 'asc')
                .get();
            
            // 转换字段名：id -> _id (适配CloudBase的_id字段)
            const permissions = (permissionsResult.data || []).map(permission => ({
                ...permission,
                _id: permission.id || permission._id
            }));
            
            result = {
                success: true,
                data: {
                    permissions: permissions,
                    total_count: permissions.length
                },
                message: '获取权限列表成功'
            };
            
        } else if (action === 'get_role_permissions') {
            // 获取角色的权限
            console.log('获取角色权限...');
            
            var roleId = requestData.role_id || '';
            if (!roleId) {
                result = {
                    success: false,
                    message: '角色ID不能为空',
                    data: null
                };
            } else {
                // 查询角色权限关联
                const rolePermissionsResult = await db.collection('role_permissions')
                    .where({ role_id: roleId })
                    .get();
                
                // 获取权限详情
                var permissionIds = (rolePermissionsResult.data || []).map(rp => rp.permission_id);
                var permissions = [];
                
                if (permissionIds.length > 0) {
                    const permissionsResult = await db.collection('permissions')
                        .where({ 
                            id: db.command.in(permissionIds),
                            is_active: true 
                        })
                        .get();
                    
                    // 转换字段名：id -> _id
                    permissions = (permissionsResult.data || []).map(permission => ({
                        ...permission,
                        _id: permission.id || permission._id
                    }));
                }
                
                result = {
                    success: true,
                    data: {
                        role_id: roleId,
                        permissions: permissions,
                        permission_count: permissions.length
                    },
                    message: '获取角色权限成功'
                };
            }
            
        } else if (action === 'update_role_permissions') {
            // 更新角色权限
            console.log('更新角色权限...');
            
            var roleId = requestData.role_id || '';
            var permissionIds = requestData.permission_ids || [];
            
            if (!roleId) {
                result = {
                    success: false,
                    message: '角色ID不能为空',
                    data: null
                };
            } else {
                // 删除现有权限关联
                await db.collection('role_permissions')
                    .where({ role_id: roleId })
                    .remove();
                
                // 添加新的权限关联
                var newRolePermissions = permissionIds.map(permId => ({
                    role_id: roleId,
                    permission_id: permId,
                    granted_at: new Date().toISOString(),
                    granted_by: requestData.granted_by || 'system'
                }));
                
                if (newRolePermissions.length > 0) {
                    await db.collection('role_permissions').add(newRolePermissions);
                }
                
                // 查询角色信息
                const roleResult = await db.collection('roles')
                    .where({ role_name: roleId })
                    .get();
                const role = roleResult.data && roleResult.data.length > 0 ? roleResult.data[0] : null;
                
                // 记录操作日志
                await logOperation({
                    type: '权限管理',
                    operator: requestData.operator || 'admin',
                    description: `更新角色权限：${role ? role.display_name : roleId}`,
                    metadata: {
                        role_id: roleId,
                        role_name: role ? role.role_name : '',
                        permission_count: permissionIds.length
                    }
                });
                
                result = {
                    success: true,
                    data: {
                        role_id: roleId,
                        permission_count: permissionIds.length
                    },
                    message: '角色权限更新成功'
                };
            }
            
        } else if (action === 'create_role') {
            // 创建角色
            console.log('创建角色...');
            
            var newRole = {
                role_name: requestData.role_name || '',
                display_name: requestData.display_name || '',
                description: requestData.description || '',
                is_active: true,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                created_by: requestData.created_by || 'system'
            };
            
            // 检查角色名是否已存在
            const existingRole = await db.collection('roles')
                .where({ role_name: newRole.role_name })
                .get();
            
            if (existingRole.data && existingRole.data.length > 0) {
                result = {
                    success: false,
                    message: '角色名称已存在',
                    data: null
                };
            } else {
                const createResult = await db.collection('roles').add(newRole);
                
                // 记录操作日志
                await logOperation({
                    type: '角色创建',
                    operator: requestData.operator || 'admin',
                    description: `创建角色：${newRole.display_name} (${newRole.role_name})`,
                    metadata: {
                        role_id: createResult.id,
                        role_name: newRole.role_name,
                        display_name: newRole.display_name
                    }
                });
                
                result = {
                    success: true,
                    data: {
                        role_id: createResult.id,
                        role_name: newRole.role_name,
                        display_name: newRole.display_name
                    },
                    message: '角色创建成功'
                };
            }
            
        } else if (action === 'update_permission') {
            // 更新权限状态
            console.log('更新权限状态...');
            console.log('请求数据:', requestData);
            try {
                const { permission_id, is_active } = requestData;
                
                console.log('权限ID:', permission_id);
                console.log('新状态:', is_active);
                
                if (!permission_id) {
                    result = {
                        success: false,
                        message: '权限ID不能为空',
                        data: null
                    };
                } else {
                    // 通过查询找到权限文档
                    console.log('查询权限文档...');
                    const queryResult = await db.collection('permissions')
                        .where({
                            $or: [
                                { _id: permission_id },
                                { id: permission_id }
                            ]
                        })
                        .get();
                    
                    console.log('查询结果:', queryResult);
                    
                    if (!queryResult.data || queryResult.data.length === 0) {
                        console.log('权限不存在:', permission_id);
                        result = {
                            success: false,
                            message: '权限不存在',
                            data: null
                        };
                    } else {
                        const permissionDoc = queryResult.data[0];
                        const actualId = permissionDoc._id;
                        console.log('找到权限，实际ID:', actualId);
                        console.log('当前状态:', permissionDoc.is_active);
                        
                        // 更新权限状态
                        console.log('开始更新权限状态...');
                        const updateResult = await db.collection('permissions')
                            .doc(actualId)
                            .update({
                                is_active: is_active,
                                updated_at: new Date()
                            });
                        
                        console.log('更新结果:', updateResult);
                        
                        // 记录操作日志
                        await logOperation({
                            type: '权限管理',
                            operator: requestData.operator || 'admin',
                            description: `${is_active ? '启用' : '禁用'}权限：${permissionDoc.permission_name || permissionDoc.permission_code}`,
                            metadata: {
                                permission_id: actualId,
                                permission_code: permissionDoc.permission_code,
                                permission_name: permissionDoc.permission_name,
                                is_active: is_active
                            }
                        });
                        
                        result = {
                            success: true,
                            message: `权限已${is_active ? '启用' : '禁用'}`,
                            data: {
                                permission_id: actualId,
                                is_active: is_active,
                                updated_at: new Date()
                            }
                        };
                    }
                }
            } catch (error) {
                console.error('更新权限状态失败:', error);
                result = {
                    success: false,
                    message: '更新权限状态失败: ' + error.message,
                    data: null
                };
            }
         } else if (action === 'init_default_data') {
            // 初始化默认数据
            console.log('初始化默认数据...');
            
            // 初始化权限数据
            var defaultPermissions = [
                { permission_code: "dashboard.view", permission_name: "查看仪表板", category: "dashboard", description: "查看系统仪表板数据" },
                { permission_code: "orders.read", permission_name: "查看订单", category: "orders", description: "查看订单列表和详情" },
                { permission_code: "orders.create", permission_name: "创建订单", category: "orders", description: "创建新的订单记录" },
                { permission_code: "orders.update", permission_name: "更新订单", category: "orders", description: "修改订单信息" },
                { permission_code: "orders.delete", permission_name: "删除订单", category: "orders", description: "删除订单记录" },
                { permission_code: "progress.update", permission_name: "更新进度", category: "progress", description: "更新订单制作进度" },
                { permission_code: "photos.upload", permission_name: "上传照片", category: "photos", description: "上传制作过程照片" },
                { permission_code: "photos.manage", permission_name: "管理照片", category: "photos", description: "管理照片文件" },
                { permission_code: "users.manage", permission_name: "管理用户", category: "users", description: "管理系统用户" },
                { permission_code: "users.create", permission_name: "创建用户", category: "users", description: "创建新的系统用户" },
                { permission_code: "system.settings", permission_name: "系统设置", category: "system", description: "管理系统设置" }
            ];
            
            // 检查权限是否已存在
            const existingPermissions = await db.collection('permissions').get();
            if (!existingPermissions.data || existingPermissions.data.length === 0) {
                for (var perm of defaultPermissions) {
                    perm.is_active = true;
                    perm.created_at = new Date().toISOString();
                    await db.collection('permissions').add(perm);
                }
            }
            
            // 初始化角色数据
            var defaultRoles = [
                {
                    role_name: "admin",
                    display_name: "系统管理员",
                    description: "拥有所有系统权限",
                    is_active: true,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    created_by: "system"
                },
                {
                    role_name: "operator",
                    display_name: "操作员",
                    description: "负责订单和进度管理",
                    is_active: true,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    created_by: "system"
                },
                {
                    role_name: "viewer",
                    display_name: "查看者",
                    description: "只能查看和上传照片",
                    is_active: true,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    created_by: "system"
                }
            ];
            
            // 检查角色是否已存在
            const existingRoles = await db.collection('roles').get();
            if (!existingRoles.data || existingRoles.data.length === 0) {
                for (var role of defaultRoles) {
                    await db.collection('roles').add(role);
                }
            }
            
            result = {
                success: true,
                data: {
                    permissions_created: defaultPermissions.length,
                    roles_created: defaultRoles.length
                },
                message: '默认数据初始化成功'
            };
            
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
