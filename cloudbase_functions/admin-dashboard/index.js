 // 管理员仪表板云函数 - 简化版本
const cloudbase = require('@cloudbase/node-sdk');

// 初始化 CloudBase
const app = cloudbase.init({
    env: 'cloud1-7g7o4xi13c00cb90'
});

// 获取数据库引用
const db = app.database();

exports.main = async function(event, context) {
    console.log('=== 管理员仪表板云函数 - 简化版本 ===');
    console.log('Event:', JSON.stringify(event));
    
    try {
        console.log('开始获取仪表板数据...');
        
        // 1. 获取订单统计（排除软删除的订单）
        const ordersResult = await db.collection('orders')
            .where({ is_deleted: db.command.neq(true) })
            .get();
        const orders = ordersResult.data || [];
        
        // 统计订单状态
        var statusStats = {
            '待处理': 0,
            '制作中': 0,
            '已完成': 0
        };
        
        orders.forEach(order => {
            var status = order.order_status || '待处理';
            if (statusStats.hasOwnProperty(status)) {
                statusStats[status]++;
            }
        });
        
        // 2. 获取进度统计
        const progressResult = await db.collection('order_progress').get();
        const allProgress = progressResult.data || [];
        
        // 统计各阶段进度
        var stageStats = {};
        allProgress.forEach(progress => {
            var stageName = progress.stage_name || '未知阶段';
            if (!stageStats[stageName]) {
                stageStats[stageName] = {
                    completed: 0,
                    in_progress: 0,
                    pending: 0,
                    total: 0
                };
            }
            
            var status = progress.status || 'pending';
            if (stageStats[stageName].hasOwnProperty(status)) {
                stageStats[stageName][status]++;
            }
            stageStats[stageName].total++;
        });
        
        // 3. 生成操作日志
        var recentActivities = [];
        
        // 从订单收集活动
        const sortedOrders = orders
            .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        
        sortedOrders.forEach(order => {
            recentActivities.push({
                type: '订单创建',
                message: order.customer_name + ' - ' + order.order_number,
                timestamp: order.created_at,
                order_id: order._id
            });
        });
        
        // 从进度更新收集活动（最近完成的阶段）
        const sortedProgress = allProgress
            .filter(p => p.status === 'completed' && p.completed_at)
            .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at));
        
        sortedProgress.forEach(progress => {
            // 查找对应的订单信息
            const order = orders.find(o => o._id === progress.order_id);
            if (order) {
                recentActivities.push({
                    type: '阶段完成',
                    message: `${order.customer_name} - ${progress.stage_name || progress.stage_id}`,
                    timestamp: progress.completed_at,
                    order_id: progress.order_id
                });
            }
        });
        
        // 按时间排序
        recentActivities.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
        
        // 4. 计算完成趋势数据（最近30天）
        const trendData = calculateCompletionTrend(orders, allProgress);
        
        // 5. 计算真实的性能指标（使用进度数据）
        const performanceMetrics = calculatePerformanceMetrics(orders, allProgress);
        
        // 6. 计算总体指标
        var totalOrders = orders.length;
        var completedOrders = statusStats['已完成'];
        var inProgressOrders = statusStats['制作中'];
        var pendingOrders = statusStats['待处理'];
        var recentOrdersCount = getRecentOrdersCount(orders);
        
        // 计算今日完成数 - 统计今天完成最后一个阶段的订单数
        var todayCompleted = getTodayCompletedOrders(orders, allProgress);
        
        // 计算本月完成数 - 统计本月完成最后一个阶段的订单数
        var thisMonthCompleted = getThisMonthCompletedOrders(orders, allProgress);
        
        var completionRate = totalOrders > 0 ? Math.round((completedOrders / totalOrders) * 100) : 0;
        var avgCompletionDays = performanceMetrics.avg_completion_days || 0;
        var onTimeRate = performanceMetrics.on_time_rate || 0;
        
        var dashboardData = {
            overview: {
                total_orders: totalOrders,
                completed_orders: completedOrders,
                in_progress_orders: inProgressOrders,
                pending_orders: pendingOrders,
                today_completed: todayCompleted,
                this_month_completed: thisMonthCompleted,
                completion_rate: completionRate,
                recent_orders: recentOrdersCount,
                avg_completion_time: Math.round(avgCompletionDays),
                on_time_rate: Math.round(onTimeRate * 100)
            },
            order_status_stats: statusStats,
            stage_stats: stageStats,
            recent_activities: recentActivities,
            completion_trend: trendData,
            performance_metrics: performanceMetrics
        };
        
        // 添加详细调试信息
        console.log('=== 调试信息 ===');
        console.log('订单总数:', orders.length);
        console.log('已完成订单数:', statusStats['已完成']);
        console.log('进度总记录数:', allProgress.length);
        if (allProgress.length > 0) {
            console.log('第一个进度记录:', JSON.stringify(allProgress[0], null, 2));
        }
        console.log('今日完成:', todayCompleted);
        console.log('本月完成:', thisMonthCompleted);
        console.log('平均耗时:', avgCompletionDays);
        console.log('===============');
        
        console.log('仪表板数据生成成功:', JSON.stringify(dashboardData, null, 2));
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: true,
                data: dashboardData,
                message: '获取仪表板数据成功'
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

// 计算完成趋势数据（最近30天）
function calculateCompletionTrend(orders, allProgress) {
    const dates = [];
    const completions = [];
    
    // 生成最近30天的日期数组
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0]; // 格式：YYYY-MM-DD
        dates.push(dateStr);
        completions.push(0); // 初始化为0
    }
    
    // 统计每天的完成订单数（通过进度表）
    console.log('=== 趋势图调试 ===');
    console.log('已完成订单数:', orders.filter(o => o.order_status === '已完成').length);
    
    let debugCount = 0;
    orders.forEach(order => {
        if (order.order_status === '已完成') {
            // 找到这个订单的所有进度
            const orderProgresses = allProgress.filter(p => p.order_id === order._id);
            console.log(`订单 ${order.order_number} 的进度数:`, orderProgresses.length);
            
            // 调试：打印所有进度的状态
            if (orderProgresses.length > 0) {
                console.log(`订单 ${order.order_number} 的进度详情:`, 
                    orderProgresses.map(p => ({
                        stage_name: p.stage_name, 
                        status: p.status, 
                        completed_at: p.completed_at
                    }))
                );
            }
            
            // 找到最后一个完成的阶段
            const lastCompletedProgress = orderProgresses
                .filter(p => p.status === 'completed' && p.completed_at)
                .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0];
            
            if (lastCompletedProgress && lastCompletedProgress.completed_at) {
                const completedDate = lastCompletedProgress.completed_at.split('T')[0];
                const index = dates.indexOf(completedDate);
                console.log(`订单 ${order.order_number} 完成日期: ${completedDate}, 索引: ${index}`);
                if (index !== -1) {
                    completions[index]++;
                    debugCount++;
                }
            }
        }
    });
    console.log('统计到的完成订单数:', debugCount);
    console.log('==================');
    
    return {
        dates: dates.map(d => d.split('-').slice(1).join('-')), // 格式：MM-DD
        completions: completions
    };
}

// 计算性能指标
function calculatePerformanceMetrics(orders, allProgress) {
    const completedOrders = orders.filter(o => o.order_status === '已完成');
    
    // 计算平均完成天数 - 从订单开始到最后一个阶段完成的时间
    let totalDays = 0;
    let validOrders = 0;
    
    completedOrders.forEach(order => {
        if (order.created_at) {
            // 找到这个订单的所有进度
            const orderProgresses = allProgress.filter(p => p.order_id === order._id);
            
            // 找到最后一个完成的阶段
            const lastCompletedProgress = orderProgresses
                .filter(p => p.status === 'completed' && p.completed_at)
                .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0];
            
            if (lastCompletedProgress) {
                const created = new Date(order.created_at);
                const completed = new Date(lastCompletedProgress.completed_at);
                const days = Math.ceil((completed - created) / (1000 * 60 * 60 * 24));
                if (days > 0) {
                    totalDays += days;
                    validOrders++;
                }
            }
        }
    });
    
    const avgCompletionDays = validOrders > 0 ? Math.round(totalDays / validOrders) : 0;
    
    // 由于系统中不再维护预计完成时间，这里暂不计算准时交付率
    const onTimeRate = 0;
    
    return {
        avg_completion_days: avgCompletionDays,
        on_time_rate: onTimeRate
    };
}

// 获取近30天新订单数
function getRecentOrdersCount(orders) {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    return orders.filter(order => {
        if (order.created_at) {
            return new Date(order.created_at) >= thirtyDaysAgo;
        }
        return false;
    }).length;
}

// 获取今日完成数
function getTodayCompletedCount(orders) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // 调试：打印一些订单数据
    console.log('调试：第一个订单的状态和完成时间', orders[0] ? {
        order_status: orders[0].order_status,
        completed_at: orders[0].completed_at,
        order_number: orders[0].order_number
    } : '无订单');
    
    return orders.filter(order => {
        // 检查是否有完成时间和状态
        const hasCompletedAt = order.completed_at;
        const statusIsCompleted = order.order_status === '已完成';
        
        // 调试信息
        if (hasCompletedAt && !statusIsCompleted) {
            console.log('有完成时间但状态不是已完成:', {
                order_number: order.order_number,
                order_status: order.order_status,
                completed_at: order.completed_at
            });
        }
        
        if (statusIsCompleted && hasCompletedAt) {
            const completed = new Date(order.completed_at);
            completed.setHours(0, 0, 0, 0);
            return completed.getTime() === today.getTime();
        }
        return false;
    }).length;
}

// 获取本月完成数
function getThisMonthCompletedCount(orders) {
    const now = new Date();
    const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    const completedInMonth = orders.filter(order => {
        if (order.order_status === '已完成' && order.completed_at) {
            const completed = new Date(order.completed_at);
            return completed >= firstDayOfMonth;
        }
        return false;
    });
    
    console.log('本月完成的订单数:', completedInMonth.length);
    
    return completedInMonth.length;
}

// 统计今天完成最后一个阶段的订单数
function getTodayCompletedOrders(orders, allProgress) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    let count = 0;
    
    orders.forEach(order => {
        if (order.order_status === '已完成') {
            // 找到这个订单的所有进度
            const orderProgresses = allProgress.filter(p => p.order_id === order._id);
            
            // 找到最后一个完成的阶段
            const lastCompletedProgress = orderProgresses
                .filter(p => p.status === 'completed' && p.completed_at)
                .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0];
            
            if (lastCompletedProgress) {
                const completed = new Date(lastCompletedProgress.completed_at);
                completed.setHours(0, 0, 0, 0);
                if (completed.getTime() === today.getTime()) {
                    count++;
                }
            }
        }
    });
    
    return count;
}

// 统计本月完成最后一个阶段的订单数
function getThisMonthCompletedOrders(orders, allProgress) {
    const now = new Date();
    const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    let count = 0;
    
    orders.forEach(order => {
        if (order.order_status === '已完成') {
            // 找到这个订单的所有进度
            const orderProgresses = allProgress.filter(p => p.order_id === order._id);
            
            // 找到最后一个完成的阶段
            const lastCompletedProgress = orderProgresses
                .filter(p => p.status === 'completed' && p.completed_at)
                .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0];
            
            if (lastCompletedProgress) {
                const completed = new Date(lastCompletedProgress.completed_at);
                if (completed >= firstDayOfMonth) {
                    count++;
                }
            }
        }
    });
    
    return count;
}
