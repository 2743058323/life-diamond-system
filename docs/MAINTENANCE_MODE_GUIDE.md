# 系统维护模式使用指南

## 📖 功能说明

系统维护模式允许你在修复bug、升级系统或进行重要维护时，向访问 **https://diamond.genepk.cn/** 的用户展示一个友好的维护页面，而你自己可以通过特殊链接绕过维护模式继续访问系统。

## 🎯 核心特点

- ✅ **用户友好**：用户访问看到专业的维护提示页面
- ✅ **你可访问**：通过绕过密钥，你仍然可以正常访问系统
- ✅ **快速开关**：通过环境变量控制，无需修改代码
- ✅ **自定义信息**：可自定义维护标题、说明、预计时间
- ✅ **响应式设计**：桌面端和移动端都美观展示

## 🚀 使用方法

### 第一步：在CloudBase设置环境变量

1. **登录腾讯云CloudBase控制台**
   ```
   https://console.cloud.tencent.com/tcb
   ```

2. **进入云托管服务配置**
   ```
   环境 → 云托管 → 选择你的服务 → 版本配置 → 环境变量
   ```

3. **添加以下环境变量**

   **必需配置**：
   ```
   MAINTENANCE_MODE=true
   MAINTENANCE_BYPASS_KEY=你的密钥（比如：secret2024）
   ```

   **可选配置**（自定义维护信息）：
   ```
   MAINTENANCE_TITLE=🔧 系统升级维护中
   MAINTENANCE_MESSAGE=我们正在修复订单查询功能，感谢您的耐心等待。
   MAINTENANCE_TIME=预计维护时间：15:00-15:30（约30分钟）
   MAINTENANCE_SHOW_CONTACT=true
   ```

4. **保存并重启服务**
   - 点击"保存"
   - 点击"重启"服务
   - 等待1-2分钟生效

### 第二步：验证维护模式

#### ✅ 普通用户访问（看到维护页面）
```
https://diamond.genepk.cn/
```
**效果**：显示维护页面，无法继续访问

#### ✅ 你自己访问（绕过维护模式）
```
https://diamond.genepk.cn/?bypass=你的密钥
```
**示例**：
```
https://diamond.genepk.cn/?bypass=secret2024
```
**效果**：正常访问系统，可以进行维护和测试

### 第三步：完成维护后关闭

1. **修改环境变量**
   ```
   MAINTENANCE_MODE=false
   ```
   或直接删除 `MAINTENANCE_MODE` 环境变量

2. **重启服务**

3. **验证**：访问 https://diamond.genepk.cn/ 恢复正常

## ⚙️ 环境变量详细说明

| 环境变量 | 必需 | 默认值 | 说明 |
|---------|------|--------|------|
| `MAINTENANCE_MODE` | ✅ | `false` | 是否开启维护模式（true/false） |
| `MAINTENANCE_BYPASS_KEY` | ✅ | 无 | 绕过维护模式的密钥，建议使用复杂字符串 |
| `MAINTENANCE_TITLE` | ❌ | `🔧 系统维护中` | 维护页面标题 |
| `MAINTENANCE_MESSAGE` | ❌ | （默认文案） | 维护说明信息 |
| `MAINTENANCE_TIME` | ❌ | `预计维护时间：30分钟` | 预计恢复时间 |
| `MAINTENANCE_SHOW_CONTACT` | ❌ | `true` | 是否显示联系方式（true/false） |

## 📋 完整使用示例

### 示例1：紧急修复Bug

**场景**：发现订单查询功能有bug，需要紧急修复

```
15:00 - 发现问题

15:02 - CloudBase设置：
        MAINTENANCE_MODE=true
        MAINTENANCE_BYPASS_KEY=fix20241028
        MAINTENANCE_MESSAGE=正在修复订单查询功能，请稍候
        MAINTENANCE_TIME=预计15分钟

15:04 - 重启服务
        → 用户看到维护页面

15:05 - 你访问：https://diamond.genepk.cn/?bypass=fix20241028
        → 可以正常访问系统

15:05-15:20 - 修复代码、测试、部署

15:22 - 确认修复成功

15:23 - CloudBase设置：MAINTENANCE_MODE=false

15:25 - 重启服务
        → 用户恢复正常访问
```

### 示例2：计划性系统升级

**场景**：晚上21:00-22:00进行v2.0版本升级

```
20:55 - CloudBase设置：
        MAINTENANCE_MODE=true
        MAINTENANCE_BYPASS_KEY=upgrade2024
        MAINTENANCE_TITLE=🚀 系统升级中
        MAINTENANCE_MESSAGE=我们正在升级到v2.0版本，增加更多实用功能！
        MAINTENANCE_TIME=维护时间：21:00-22:00

21:00 - 重启服务，开始维护
        → 用户看到维护页面

21:05 - 你访问：https://diamond.genepk.cn/?bypass=upgrade2024
        → 部署新版本

21:30 - 部署完成，测试新功能

21:55 - 确认一切正常

21:56 - CloudBase设置：MAINTENANCE_MODE=false

22:00 - 重启服务
        → 用户看到新版本系统
```

### 示例3：数据库维护

**场景**：需要执行数据库清理和优化

```
CloudBase设置：
MAINTENANCE_MODE=true
MAINTENANCE_BYPASS_KEY=db2024
MAINTENANCE_MESSAGE=正在进行数据库优化，提升系统性能。
MAINTENANCE_TIME=预计10-15分钟

你访问：https://diamond.genepk.cn/?bypass=db2024
执行数据库操作、验证

完成后设置：MAINTENANCE_MODE=false
```

## 🎨 维护页面预览

```
┌─────────────────────────────────────┐
│          ⚙️ (旋转动画)              │
│                                     │
│      🔧 系统维护中                   │
│                                     │
│  我们正在进行系统升级和维护，        │
│  以提供更好的服务体验。              │
│                                     │
│  ⏰ 预计维护时间：30分钟             │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 💡 温馨提示                   │  │
│  │ • 维护期间系统暂时无法访问     │  │
│  │ • 您的数据安全不会受到影响     │  │
│  │ • 维护完成后系统将自动恢复     │  │
│  │ • 如有紧急需求，请联系客服     │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 📞 如有紧急需求，请联系：      │  │
│  │ 客服电话：400-XXX-XXXX        │  │
│  │ 客服邮箱：service@example.com │  │
│  └───────────────────────────────┘  │
│                                     │
│        感谢您的耐心等待！            │
│    当前时间：2025-10-28 16:30:45    │
└─────────────────────────────────────┘
```

## 🔒 安全建议

### 1. **密钥设置**
```
❌ 不好：bypass=123
❌ 不好：bypass=admin
✅ 推荐：bypass=maint_2024_october_28_v2
✅ 推荐：bypass=fix_order_bug_20241028
```

### 2. **密钥管理**
- ⚠️ 不要使用过于简单的密钥
- ⚠️ 维护完成后可以更换新密钥
- ⚠️ 不要将密钥提交到Git
- ✅ 建议每次维护使用不同的密钥

### 3. **联系方式更新**

修改文件 `streamlit_app/components/maintenance_page.py`：
```python
# 第107-110行
st.markdown("""
    <div class="maintenance-contact">
        <strong>📞 如有紧急需求，请联系：</strong><br>
        客服电话：你的真实电话<br>
        客服邮箱：你的真实邮箱
    </div>
""", unsafe_allow_html=True)
```

或者隐藏联系方式：
```
MAINTENANCE_SHOW_CONTACT=false
```

## ⚠️ 注意事项

### 1. **环境变量生效**
- 修改环境变量后必须重启服务
- 重启大约需要1-2分钟
- 可以在CloudBase控制台查看服务状态

### 2. **绕过链接保密**
- 不要将绕过链接分享给他人
- 绕过链接格式：`https://diamond.genepk.cn/?bypass=你的密钥`
- 建议每次维护使用新密钥

### 3. **维护时间**
- 建议在用户访问量低的时间段维护
- 提前通知用户（如果可能）
- 尽量控制维护时间在30分钟以内

### 4. **测试建议**
- 第一次使用前，先在本地测试
- 确认绕过链接可以正常访问
- 确认普通访问显示维护页面

## 🔍 故障排查

### 问题1：设置环境变量后维护页面不显示

**可能原因**：
- 环境变量拼写错误
- 环境变量值不是 `true`（小写）
- 没有重启服务

**解决方案**：
```
1. 检查环境变量名：MAINTENANCE_MODE
2. 检查值：true（必须是小写）
3. 在CloudBase控制台点击"重启"
4. 等待1-2分钟后访问
```

### 问题2：绕过链接不工作

**可能原因**：
- 密钥输入错误
- 没有设置 `MAINTENANCE_BYPASS_KEY`
- URL格式不对

**解决方案**：
```
1. 检查环境变量：MAINTENANCE_BYPASS_KEY=你的密钥
2. 确认URL格式：
   正确：https://diamond.genepk.cn/?bypass=你的密钥
   错误：https://diamond.genepk.cn/?key=你的密钥
3. 注意密钥大小写
```

### 问题3：维护页面样式异常

**解决方案**：
- 清除浏览器缓存
- 硬刷新：`Ctrl + Shift + R` (Windows) 或 `Cmd + Shift + R` (Mac)
- 尝试无痕模式访问

### 问题4：无法关闭维护模式

**解决方案**：
```
1. 确认已设置：MAINTENANCE_MODE=false
2. 或直接删除 MAINTENANCE_MODE 环境变量
3. 重启服务
4. 清除浏览器缓存后访问
```

## 📞 技术支持

如果遇到其他问题，可以：
1. 查看CloudBase服务日志
2. 检查环境变量配置是否正确
3. 本地测试环境变量是否生效
4. 检查代码是否正确部署

## 🎯 快速参考卡

```
┌─────────────────────────────────────────────┐
│ 开启维护模式                                 │
├─────────────────────────────────────────────┤
│ 1. CloudBase环境变量：                       │
│    MAINTENANCE_MODE=true                    │
│    MAINTENANCE_BYPASS_KEY=你的密钥          │
│ 2. 重启服务                                 │
│ 3. 用户访问：https://diamond.genepk.cn/     │
│    → 看到维护页面                           │
│ 4. 你访问：                                 │
│    https://diamond.genepk.cn/?bypass=密钥   │
│    → 正常访问系统                           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 关闭维护模式                                 │
├─────────────────────────────────────────────┤
│ 1. CloudBase环境变量：                       │
│    MAINTENANCE_MODE=false                   │
│ 2. 重启服务                                 │
│ 3. 所有人正常访问                           │
└─────────────────────────────────────────────┘
```

