const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'secret-jwt-key-image-gallery-2026';
const ADMIN_SECRET_KEY = process.env.ADMIN_SECRET_KEY || 'admin_super_secret_key';

const verifyAdmin = (req, res, next) => {
  // Option 1: Admin Secret Header
  const directKey = req.headers['x-admin-key'];
  if (directKey && directKey === ADMIN_SECRET_KEY) {
    req.user = { role: 'admin', username: 'admin' };
    return next();
  }

  // Option 2: Bearer JWT Token
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(403).json({
      success: false,
      message: 'Access denied. Admin authentication required to perform this action.'
    });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    if (decoded.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Forbidden. Only administrators can delete images.'
      });
    }
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({
      success: false,
      message: 'Invalid or expired token.'
    });
  }
};

module.exports = {
  verifyAdmin,
  JWT_SECRET,
};
