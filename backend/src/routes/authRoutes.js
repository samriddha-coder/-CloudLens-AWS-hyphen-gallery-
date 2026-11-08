const express = require('express');
const router = express.Router();
const { login, getMe } = require('../controllers/authController');
const { verifyAdmin } = require('../middlewares/authMiddleware');

router.post('/login', login);
router.get('/me', verifyAdmin, getMe);

module.exports = router;
