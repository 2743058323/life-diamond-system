# 生命钻石订单系统 - 架构设计文档

## 1. 核心实体模型

### 1.1 订单 (Order)
```json
{
  "_id": "订单ID",
  "order_number": "LD-2024-001",
  "customer_name": "张三",
  "customer_phone": "13800138000",
  "customer_email": "zhang@example.com",
  "customer_address": "北京市朝阳区...",
  "diamond_type": "纪念钻石",
  "diamond_size": "0.5克拉",
  "special_requirements": "特殊要求",
  "order_status": "待处理|制作中|已完成|已取消",
  "progress_percentage": 0,
  "current_stage": "未开始",
  "estimated_completion": "2024-12-31",
  "is_deleted": false,
  "deleted_at": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 1.2 进度记录 (Progress)
```json
{
  "_id": "进度记录ID",
  "order_id": "订单ID",
  "stage_id": "stage_1",
  "stage_name": "材料准备",
  "stage_order": 1,
  "status": "pending|in_progress|completed",
  "started_at": null,
  "completed_at": null,
  "estimated_completion": "2024-01-15",
  "notes": "备注信息",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 1.3 照片 (Photo)
```json
{
  "_id": "照片ID",
  "order_id": "订单ID",
  "stage_id": "stage_1",
  "stage_name": "材料准备",
  "photo_url": "云存储URL",
  "thumbnail_url": "缩略图URL",
  "description": "照片描述",
  "sort_order": 1,
  "is_deleted": false,
  "upload_time": "2024-01-15T10:00:00Z"
}
```

---

## 2. 订单状态机

### 2.1 订单状态
```
待处理 → 制作中 → 已完成
  ↓                  ↑
  └──────→ 已取消 ←──┘
```

### 2.2 状态转换规则

| 当前状态 | 可转换到 | 触发条件 |
|---------|---------|---------|
| 待处理 | 制作中 | 任一阶段开始 |
| 待处理 | 已取消 | 手动取消 |
| 制作中 | 已完成 | 所有阶段完成 |
| 制作中 | 已取消 | 手动取消 |
| 已完成 | - | 终态 |
| 已取消 | - | 终态 |

### 2.3 阶段状态
```
pending (待处理) → in_progress (进行中) → completed (已完成)
```

### 2.4 阶段推进规则
1. 阶段必须按顺序开始（stage_order）
2. 开始新阶段前，前一阶段必须是 completed
3. 同一时间只能有一个阶段是 in_progress
4. completed 状态不可回退

---

## 3. API接口规范

### 3.1 订单API

#### 创建订单
```python
POST /api/orders
Request: {
  "customer_name": "张三",
  "customer_phone": "13800138000",
  "diamond_type": "纪念钻石",
  ...
}
Response: {
  "success": true,
  "data": {
    "order_id": "xxx",
    "order_number": "LD-2024-001",
    "progress_records": [...],  # 自动创建的进度记录
  }
}
```

#### 获取订单列表
```python
GET /api/orders
Query: {
  "page": 1,
  "limit": 20,
  "status": "制作中",
  "search": "张三",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
Response: {
  "success": true,
  "data": {
    "orders": [...],
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

#### 获取订单详情
```python
GET /api/orders/:id
Response: {
  "success": true,
  "data": {
    "order": {...},
    "progress": [...],
    "photos": [...],
    "allowed_actions": ["start_stage", "edit_info", ...]
  }
}
```

### 3.2 进度API

#### 开始阶段
```python
POST /api/progress/start
Request: {
  "order_id": "xxx",
  "stage_id": "stage_2"
}
Response: {
  "success": true,
  "data": {
    "progress": {...},
    "order_status": "制作中",
    "order_progress": 25
  }
}
```

#### 完成阶段
```python
POST /api/progress/complete
Request: {
  "order_id": "xxx",
  "stage_id": "stage_2",
  "notes": "备注",
  "photos": [file1, file2, ...]  # 可选
}
Response: {
  "success": true,
  "data": {
    "progress": {...},
    "order_status": "制作中",
    "order_progress": 50,
    "uploaded_photos": 3
  }
}
```

### 3.3 照片API

#### 上传照片
```python
POST /api/photos/upload
Request: {
  "order_id": "xxx",
  "stage_id": "stage_2",
  "photos": [file1, file2, ...]
}
Response: {
  "success": true,
  "data": {
    "uploaded": 2,
    "failed": 0,
    "photo_urls": [...]
  }
}
```

---

## 4. 业务规则

### 4.1 创建订单
1. 自动生成订单号（格式：LD-YYYY-XXXX）
2. 自动创建所有阶段的进度记录（状态=pending）
3. 订单状态初始为"待处理"
4. 进度百分比初始为0%

### 4.2 开始阶段
**前置条件**：
- 前一阶段必须是 completed（第一阶段除外）
- 没有其他阶段是 in_progress

**执行**：
1. 标记阶段为 in_progress
2. 记录 started_at
3. 订单状态自动变为"制作中"

### 4.3 完成阶段
**前置条件**：
- 当前阶段必须是 in_progress

**执行**：
1. 标记阶段为 completed
2. 记录 completed_at 和 notes
3. 如果有照片，上传并关联到该阶段
4. 重新计算订单进度百分比
5. 如果所有阶段完成，订单状态变为"已完成"

### 4.3 进度百分比计算
```python
progress_percentage = (completed_stages / total_stages) * 100
```

### 4.4 软删除
- 删除订单时设置 is_deleted=true, deleted_at=当前时间
- 所有查询默认过滤 is_deleted=true 的订单
- 软删除的订单不参与统计

---

## 5. 页面结构

### 5.1 订单中心 (admin_orders_hub.py)

#### 布局
```
┌─────────────────────────────────────────┐
│ 顶部工具栏                              │
│ [搜索] [筛选] [+新建订单] [批量操作]    │
├──────────────┬──────────────────────────┤
│              │                          │
│  订单列表    │  订单详情面板            │
│  (左侧30%)   │  (右侧70%)               │
│              │                          │
│  [卡片1]     │  根据订单状态显示：       │
│  [卡片2]     │  - 待处理：基本信息+开始  │
│  [卡片3]     │  - 制作中：进度跟踪器    │
│  ...         │  - 已完成：照片画廊      │
│              │                          │
└──────────────┴──────────────────────────┘
```

#### 订单卡片显示
```
┌──────────────────────────┐
│ LD-2024-001              │
│ 张三 | 13800138000       │
│ ━━━━━━━━━━━━ 75%        │
│ 🔵 钻石制作 | 📷 5张     │
└──────────────────────────┘
```

#### 详情面板（根据状态自适应）

**待处理状态**：
- 显示基本信息（可编辑）
- [开始制作] 按钮（开始第一个阶段）
- [编辑订单] [删除订单]

**制作中状态**：
- Tabs: [基本信息] [进度跟踪] [照片管理]
- 进度跟踪Tab：
  - 时间轴（显示所有阶段）
  - 当前阶段高亮
  - [完成此阶段] 按钮
  - 照片上传区（完成时）

**已完成状态**：
- 完成信息汇总
- 照片画廊（按阶段分组）
- [发送通知] [打印订单]

---

## 6. 组件架构

### 6.1 业务逻辑层 (services/)
```python
services/
├─ order_service.py       # 订单CRUD
├─ progress_service.py    # 进度管理
├─ photo_service.py       # 照片管理
└─ state_machine.py       # 状态机
```

### 6.2 UI组件层 (components/)
```python
components/
├─ order_card.py          # 订单卡片
├─ order_detail.py        # 订单详情（自适应）
├─ progress_tracker.py    # 进度跟踪器
├─ photo_gallery.py       # 照片画廊
└─ quick_actions.py       # 快捷操作栏
```

### 6.3 主页面
```python
pages_backup/
└─ admin_orders_hub.py    # 订单中心主页面
```

---

## 7. 数据流

```
用户操作 
  ↓
UI组件 
  ↓
业务逻辑层（校验规则）
  ↓
API客户端
  ↓
云函数
  ↓
数据库
  ↓
返回数据
  ↓
更新UI
```

---

## 8. 关键设计决策

### 8.1 为什么合并三个页面？
- 订单、进度、照片是强关联的
- 用户操作是连续的流程，不应跨页面
- 减少数据同步问题
- 提升操作效率

### 8.2 为什么使用状态机？
- 明确状态转换规则
- 防止非法操作
- 便于扩展新状态
- 易于测试和维护

### 8.3 为什么详情面板自适应？
- 不同状态的操作差异大
- 避免显示无用信息
- 突出当前可执行的操作
- 更好的用户体验

---

## 9. 后续扩展

### 可扩展功能
1. 订单批量导入/导出
2. 订单模板
3. 自动通知客户
4. 订单打印
5. 统计报表
6. 操作日志审计
7. 订单评论/沟通记录

---

## 10. 迁移计划

### 旧页面 → 新页面
```
admin_orders.py      ─┐
admin_progress.py    ─┼─> admin_orders_hub.py
admin_photos.py      ─┘
```

### 迁移步骤
1. 创建新页面框架
2. 迁移订单列表逻辑
3. 迁移进度管理逻辑
4. 迁移照片管理逻辑
5. 测试所有功能
6. 更新导航菜单
7. 删除旧页面文件

---

*文档版本：v1.0*
*创建日期：2024-01-16*










