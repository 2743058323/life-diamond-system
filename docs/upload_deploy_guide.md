
# CloudBase云托管直接上传部署指南

## 部署步骤

### 1. 准备代码包
已为您创建了代码包：`life-diamond-system-upload.zip`

### 2. 在CloudBase控制台上传

1. **选择部署方式**：通过本地代码部署
2. **代码包类型**：选择"压缩包"
3. **上传代码包**：点击"上传"按钮，选择 `life-diamond-system-upload.zip`
4. **服务配置**：
   - 服务名称：`life-diamond-system`
   - 部署类型：容器型服务
5. **容器配置**：
   - 端口：`8080`
   - 目标目录：留空（根目录）
   - Dockerfile名称：`Dockerfile`
6. **环境变量**：
   - `CLOUDBASE_ENV_ID` = `cloud1-7g7o4xi13c00cb90`
   - `CLOUDBASE_REGION` = `ap-shanghai`
   - `PYTHONUNBUFFERED` = `1`
   - `STREAMLIT_SERVER_HEADLESS` = `true`
7. **ENTRYPOINT**：留空（使用Dockerfile中的CMD）
8. **CMD**：留空（使用Dockerfile中的CMD）

### 3. 部署
点击"部署"按钮开始部署

### 4. 等待部署完成
- 构建时间：约5-10分钟
- 部署完成后会显示访问地址

## 注意事项

1. **健康检查**：应用健康检查路径为 `/_stcore/health`
2. **端口**：确保使用8080端口
3. **环境变量**：必须设置CloudBase相关环境变量
4. **构建日志**：可在控制台查看构建和部署日志

## 访问应用

部署完成后，在CloudBase控制台的"云托管"服务中查看访问地址。
