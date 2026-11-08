const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');

let pool = null;
let useFallback = false;

// Fallback JSON DB path for when PostgreSQL server is not currently reachable
const fallbackDbPath = path.join(__dirname, '..', '..', 'data_fallback.json');

const initFallbackDb = () => {
  if (!fs.existsSync(fallbackDbPath)) {
    const defaultData = {
      images: [],
      users: []
    };
    fs.writeFileSync(fallbackDbPath, JSON.stringify(defaultData, null, 2));
  }
};

const getFallbackData = () => {
  initFallbackDb();
  try {
    return JSON.parse(fs.readFileSync(fallbackDbPath, 'utf8'));
  } catch (e) {
    return { images: [], users: [] };
  }
};

const saveFallbackData = (data) => {
  fs.writeFileSync(fallbackDbPath, JSON.stringify(data, null, 2));
};

const connectDB = async () => {
  const connectionString = process.env.DATABASE_URL || 
    `postgresql://${process.env.DB_USER || 'postgres'}:${process.env.DB_PASSWORD || 'postgres'}@${process.env.DB_HOST || 'localhost'}:${process.env.DB_PORT || 5432}/${process.env.DB_NAME || 'image_gallery'}`;

  pool = new Pool({
    connectionString,
    connectionTimeoutMillis: 3000,
  });

  try {
    const client = await pool.connect();
    console.log('✅ Connected to PostgreSQL database successfully.');
    
    // Create tables if not exist
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS images (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        original_name VARCHAR(255) NOT NULL,
        file_url TEXT NOT NULL,
        s3_key VARCHAR(255),
        uploader_name VARCHAR(100) DEFAULT 'Anonymous',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Ensure default admin user exists
    const adminUser = process.env.ADMIN_USERNAME || 'admin';
    const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
    const res = await client.query('SELECT * FROM users WHERE username = $1', [adminUser]);
    if (res.rows.length === 0) {
      const hashed = await bcrypt.hash(adminPass, 10);
      await client.query('INSERT INTO users (username, password, role) VALUES ($1, $2, $3)', [adminUser, hashed, 'admin']);
      console.log(`🔐 Default admin created: Username "${adminUser}", Password "${adminPass}"`);
    }

    client.release();
    useFallback = false;
  } catch (err) {
    console.warn('⚠️  Could not connect to PostgreSQL (Ensure Docker or PostgreSQL is running).');
    console.warn(`⚠️  Database Error: ${err.message}`);
    console.log('🔄 Switching to local fallback storage (data_fallback.json) for smooth local testing...');
    useFallback = true;
    initFallbackDb();

    // Ensure default admin in fallback
    const data = getFallbackData();
    const adminUser = process.env.ADMIN_USERNAME || 'admin';
    const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
    const exists = data.users.find(u => u.username === adminUser);
    if (!exists) {
      const hashed = await bcrypt.hash(adminPass, 10);
      data.users.push({
        id: 1,
        username: adminUser,
        password: hashed,
        role: 'admin',
        created_at: new Date().toISOString()
      });
      saveFallbackData(data);
      console.log(`🔐 Default admin initialized in fallback: "${adminUser}"`);
    }
  }
};

const query = async (text, params) => {
  if (!useFallback && pool) {
    try {
      return await pool.query(text, params);
    } catch (e) {
      console.error('PostgreSQL query error:', e.message);
      throw e;
    }
  }

  // Fallback handler for queries
  const data = getFallbackData();
  const lower = text.toLowerCase().trim();

  // Handle users query
  if (lower.startsWith('select * from users where username = $1')) {
    const user = data.users.find(u => u.username === params[0]);
    return { rows: user ? [user] : [] };
  }

  // Handle images SELECT
  if (lower.startsWith('select * from images order by created_at desc')) {
    const sorted = [...data.images].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    return { rows: sorted };
  }

  // Handle images INSERT
  if (lower.startsWith('insert into images')) {
    const newImage = {
      id: Date.now(),
      title: params[0],
      original_name: params[1],
      file_url: params[2],
      s3_key: params[3],
      uploader_name: params[4],
      created_at: new Date().toISOString()
    };
    data.images.unshift(newImage);
    saveFallbackData(data);
    return { rows: [newImage] };
  }

  // Handle images SELECT by id
  if (lower.startsWith('select * from images where id = $1')) {
    const img = data.images.find(i => String(i.id) === String(params[0]));
    return { rows: img ? [img] : [] };
  }

  // Handle images DELETE
  if (lower.startsWith('delete from images where id = $1')) {
    const idx = data.images.findIndex(i => String(i.id) === String(params[0]));
    if (idx !== -1) {
      const deleted = data.images.splice(idx, 1);
      saveFallbackData(data);
      return { rowCount: 1, rows: deleted };
    }
    return { rowCount: 0, rows: [] };
  }

  return { rows: [] };
};

module.exports = {
  connectDB,
  query,
  isFallback: () => useFallback
};
