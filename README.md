# 🏢 生命钻石服务系统

基于 Streamlit + 腾讯云CloudBase 的订单管理和进度跟踪系统。

## 📋 功能特性

### 客户端功能
- 🔍 **订单查询**：通过手机号和密码查询订单
- 📸 **照片预览**：查看订单相关照片（移动端友好）
- 📊 **进度追踪**：实时查看订单进度和各阶段状态

### 管理端功能
- 📊 **数据仪表盘**：实时查看系统运营数据和关键指标
- 👥 **用户管理**：管理管理员账户和权限
- 📦 **订单管理**：创建、编辑、删除订单
- 🔄 **进度管理**：更新订单进度状态
- 📷 **照片管理**：上传和管理订单照片
- 📝 **操作日志**：详细记录系统操作历史

## 🛠 技术栈

- **前端框架**：Streamlit 1.28.0
- **后端服务**：腾讯云 CloudBase 云函数
- **数据存储**：腾讯云 CloudBase 云数据库
- **文件存储**：腾讯云 CloudBase 云存储
- **部署方式**：腾讯云 CloudBase 云托管

## 📦 依赖包

```txt
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.0.0
plotly>=5.15.0
Pillow>=10.0.0
streamlit-option-menu>=0.3.6
streamlit-extras>=0.3.0
jsonschema>=4.17.0
python-dateutil>=2.8.2
streamlit-aggrid>=0.3.4
```

## 🚀 本地开发

```bash
# 安装依赖
pip install -r streamlit_app/requirements.txt

# 启动开发服务器
python dev_server.py

# 访问地址
# 电脑：http://localhost:8501
# 手机：http://你的电脑IP:8501
```

## 🔧 环境配置

在 `streamlit_app/config.py` 中配置CloudBase相关参数：

```python
CLOUDBASE_CONFIG = {
    "env_id": "你的环境ID",
    # ... 其他配置
}
```

## 📱 云托管部署

### 1. 推送代码到Git仓库
### 2. 在CloudBase控制台创建云托管服务
### 3. 选择Git仓库部署
### 4. 配置构建参数（使用根目录的Dockerfile）
### 5. 部署完成

## 📄 许可证

MIT License

## 👤 作者

生命钻石服务系统开发团队

