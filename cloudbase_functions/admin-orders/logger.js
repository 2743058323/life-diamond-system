// 通用日志记录工具
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

const db = app.database();

/**
 * 记录操作日志
 * @param {Object} params 日志参数
 * @param {string} params.type - 操作类型
 * @param {string} params.operator - 操作人
 * @param {string} params.description - 操作描述
 * @param {string} params.order_number - 订单编号（可选）
 * @param {string} params.order_id - 订单ID（可选）
 * @param {string} params.ip_address - IP地址（可选）
 * @param {Object} params.metadata - 附加元数据（可选）
 */
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

module.exports = {
    logOperation
};

