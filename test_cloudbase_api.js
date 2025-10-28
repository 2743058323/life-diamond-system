const cloudbase = require('@cloudbase/node-sdk');

// 初始化CloudBase
const app = cloudbase.init({
  env: 'cloud1-7g7o4xi13c00cb90',
  secretId: process.env.TENCENT_SECRET_ID,
  secretKey: process.env.TENCENT_SECRET_KEY
});

console.log('=== CloudBase SDK API 检查 ===');
console.log('CloudBase SDK 版本:', require('@cloudbase/node-sdk/package.json').version);

console.log('\n=== app 对象的方法 ===');
console.log('app 对象类型:', typeof app);
console.log('app 对象的所有属性:');
Object.getOwnPropertyNames(app).forEach(prop => {
  console.log(`  - ${prop}: ${typeof app[prop]}`);
});

console.log('\n=== 检查云存储相关方法 ===');
const storageMethods = [
  'getUploadUrl',
  'uploadFile', 
  'getTempFileURL',
  'downloadFile',
  'deleteFile',
  'storage',
  'getStorage'
];

storageMethods.forEach(method => {
  if (typeof app[method] === 'function') {
    console.log(`✅ app.${method} 存在`);
  } else {
    console.log(`❌ app.${method} 不存在`);
  }
});

console.log('\n=== 检查 app.storage 对象 ===');
if (typeof app.storage === 'function') {
  try {
    const storage = app.storage();
    console.log('✅ app.storage() 可调用');
    console.log('storage 对象类型:', typeof storage);
    console.log('storage 对象的所有属性:');
    Object.getOwnPropertyNames(storage).forEach(prop => {
      console.log(`  - ${prop}: ${typeof storage[prop]}`);
    });
  } catch (error) {
    console.log('❌ app.storage() 调用失败:', error.message);
  }
} else {
  console.log('❌ app.storage 不是函数');
}

console.log('\n=== 检查数据库相关方法 ===');
const dbMethods = ['database', 'db'];
dbMethods.forEach(method => {
  if (typeof app[method] === 'function') {
    console.log(`✅ app.${method} 存在`);
  } else {
    console.log(`❌ app.${method} 不存在`);
  }
});

console.log('\n=== 检查环境配置 ===');
console.log('环境ID:', app.config?.env);
console.log('配置对象:', app.config);
