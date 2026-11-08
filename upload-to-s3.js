const { S3Client, PutObjectCommand } = require('./backend/node_modules/@aws-sdk/client-s3');
const fs = require('fs');
const path = require('path');

async function upload() {
  const client = new S3Client({
    region: 'ap-southeast-2',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || 'YOUR_AWS_ACCESS_KEY_ID',
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || 'YOUR_AWS_SECRET_ACCESS_KEY'
    }
  });

  for (const filename of ['project.tar.gz', 'project.zip']) {
    const filePath = path.join(__dirname, filename);
    const fileContent = fs.readFileSync(filePath);

    const command = new PutObjectCommand({
      Bucket: 'samriddhabaket1718',
      Key: filename,
      Body: fileContent,
      ContentType: filename.endsWith('.zip') ? 'application/zip' : 'application/gzip'
    });
    await client.send(command);
    console.log(`✅ Uploaded ${filename} to S3`);
  }
}

upload().catch(err => {
  console.error('Upload Error:', err.message);
  process.exit(1);
});
