// 测试COS预签名URL生成的脚本
const COS = require('cos-nodejs-sdk-v5');

// 测试配置（需要替换为实际值）
const cos = new COS({
  SecretId: process.env.TENCENT_SECRET_ID || 'YOUR_SECRET_ID',
  SecretKey: process.env.TENCENT_SECRET_KEY || 'YOUR_SECRET_KEY'
});

const BUCKET = 'life-diamond-photos-1379657467';
const REGION = 'ap-shanghai';
const KEY = 'photos/test/test.jpg';

console.log('测试1: getObjectUrl with PUT method (不指定Headers)');
cos.getObjectUrl({
  Bucket: BUCKET,
  Region: REGION,
  Key: KEY,
  Method: 'PUT',
  Sign: true,
  Expires: 300
}, (err, data) => {
  if (err) {
    console.error('❌ 测试1失败:', err);
  } else {
    console.log('✅ 测试1成功:', data.Url ? data.Url.substring(0, 100) + '...' : data);
  }
  
  // 测试2: 使用putObject的预签名方式
  console.log('\n测试2: 使用putObject方法（如果支持）');
  // 注意：putObject通常需要直接上传，不支持预签名
  // 所以这个测试可能不适用
  
  // 测试3: 检查SDK是否有其他方法
  console.log('\n测试3: 检查COS实例的方法');
  console.log('可用方法:', Object.getOwnPropertyNames(Object.getPrototypeOf(cos)).filter(name => 
    name.includes('Url') || name.includes('Presigned') || name.includes('Auth')
  ));
});

