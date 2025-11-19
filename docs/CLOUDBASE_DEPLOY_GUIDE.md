# 🚀 腾讯云CloudBase云托管部署指南

## 📋 部署前准备

### 1. 推送代码到Git仓库

#### 方式A：使用GitHub/Gitee（推荐）

```bash
# 在GitHub/Gitee上创建新仓库后，执行：
git remote add origin https://github.com/你的用户名/life-diamond-system.git
# 或者使用Gitee
git remote add origin https://gitee.com/你的用户名/life-diamond-system.git

# 推送代码
git push -u origin master
```

#### 方式B：使用CloudBase代码仓库

CloudBase控制台也提供Git代码托管服务，可以直接在控制台创建代码仓库。

---

## 🔧 云托管部署步骤

### 第一步：登录CloudBase控制台

1. 访问 [https://console.cloud.tencent.com/tcb](https://console.cloud.tencent.com/tcb)
2. 选择你的环境（如：`life-diamond-xxx`）

### 第二步：创建云托管服务

1. 在左侧菜单选择 **「云托管」**
2. 如果首次使用，需要开通云托管服务
3. 点击 **「新建服务」**

### 第三步：配置服务基本信息

```yaml
服务名称: life-diamond-web
服务备注: 生命钻石服务系统前端应用
```

### 第四步：选择部署方式

选择 **「代码托管部署」**

#### 配置代码源

1. **代码来源**：选择 `GitHub` / `Gitee` / `CloudBase代码仓库`
2. **授权**：首次使用需要授权CloudBase访问你的Git仓库
3. **选择仓库**：选择刚才推送的 `life-diamond-system` 仓库
4. **分支**：`master` 或 `main`

### 第五步：配置构建参数

```yaml
构建方式: Dockerfile
Dockerfile路径: ./Dockerfile  # 使用根目录的Dockerfile
构建目录: .  # 根目录
```

### 第六步：配置服务规格

```yaml
CPU: 0.5核 或 1核（推荐1核）
内存: 1GB 或 2GB（推荐2GB）
实例数量: 1 ~ 10（按需弹性伸缩）
最小实例数: 1（保持至少1个实例运行，避免冷启动）
```

### 第七步：配置端口和健康检查

```yaml
监听端口: 8501
协议类型: HTTP

健康检查:
  检查路径: /_stcore/health
  检查端口: 8501
  检查协议: HTTP
```

### 第八步：配置环境变量（重要！）

点击「高级设置」，添加以下环境变量：

```yaml
# 如果需要在代码中使用环境变量，可以添加：
ENV: production
TZ: Asia/Shanghai  # 设置时区
```

### 第九步：配置访问路径

```yaml
访问路径配置:
  - 路径: /
    转发到端口: 8501
```

### 第十步：开始部署

1. 点击 **「创建」** 按钮
2. 等待服务创建（约1-2分钟）
3. 自动触发首次构建和部署

---

## 📊 部署进度查看

### 构建日志

在「版本管理」中可以查看：
- 构建进度
- 构建日志
- 部署状态

### 预期构建时间

- 首次构建：3-5分钟（需要下载基础镜像和依赖）
- 后续构建：1-3分钟（有缓存）

---

## 🌐 访问部署的应用

### 获取访问地址

部署成功后，在「服务详情」页面可以看到：

```
默认域名: https://life-diamond-web-xxx.ap-shanghai.app.tcloudbase.com
```

### 绑定自定义域名（可选）

1. 在「域名管理」中添加自定义域名
2. 配置DNS解析（CNAME记录）
3. 等待SSL证书自动签发

---

## 🔄 后续更新部署

### 自动部署（推荐）

配置完成后，每次推送代码到Git仓库：

```bash
git add .
git commit -m "更新说明"
git push origin master
```

CloudBase会自动检测到代码变更并触发构建部署。

### 手动部署

在CloudBase控制台「版本管理」中：
1. 点击「新建版本」
2. 选择最新的commit
3. 触发构建

---

## 🐛 常见问题

### 1. 构建失败

**原因**：
- Dockerfile路径配置错误
- 依赖包安装失败
- 内存不足

**解决**：
- 检查Dockerfile路径是否为 `./Dockerfile`
- 查看构建日志，找到具体错误
- 使用阿里云镜像加速pip安装（已在Dockerfile中配置）

### 2. 服务启动失败

**原因**：
- 端口配置错误
- Streamlit启动参数错误
- 环境变量缺失

**解决**：
- 确保监听端口为 `8501`
- 检查Dockerfile中的CMD命令
- 查看实例日志

### 3. 健康检查失败

**原因**：
- Streamlit未完全启动
- 健康检查路径错误

**解决**：
- 健康检查路径：`/_stcore/health`
- 增加启动等待时间（start-period: 40s）

### 4. 访问速度慢

**原因**：
- 实例数量不足
- 冷启动

**解决**：
- 设置最小实例数为1（避免冷启动）
- 增加实例规格（1核2GB）

### 5. 图片无法显示

**原因**：
- 云存储跨域配置
- 图片URL访问权限

**解决**：
- 检查云存储CORS配置
- 确保图片文件公开访问权限

---

## 📈 性能优化建议

### 1. 资源配置

```yaml
生产环境推荐配置:
  CPU: 1核
  内存: 2GB
  最小实例数: 1
  最大实例数: 5
  扩缩容指标: CPU使用率 > 70%
```

### 2. 冷启动优化

- 设置**最小实例数 ≥ 1**
- 避免实例完全缩容到0

### 3. CDN加速（可选）

- 为静态资源配置CDN
- 加速图片和CSS加载

---

## 📞 技术支持

### CloudBase文档

- [云托管文档](https://cloud.tencent.com/document/product/1243/46126)
- [Dockerfile构建](https://cloud.tencent.com/document/product/1243/49826)

### 监控与告警

在CloudBase控制台配置：
- 实例监控：CPU、内存、网络
- 服务告警：构建失败、服务异常

---

## ✅ 部署检查清单

- [ ] Git仓库创建并推送代码
- [ ] CloudBase云托管服务创建
- [ ] Dockerfile路径配置正确（./Dockerfile）
- [ ] 端口配置为8501
- [ ] 健康检查路径：/_stcore/health
- [ ] 最小实例数设置为1
- [ ] 首次构建成功
- [ ] 可以通过默认域名访问
- [ ] 登录功能正常
- [ ] 云函数API调用正常

---

🎉 **部署完成后，你的应用将7x24小时在线运行！**

