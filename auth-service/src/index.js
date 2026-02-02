const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'your-256-bit-secret-for-jwt-signing-change-in-production';
const DATA_DIR = process.env.AUTH_DATA_DIR || path.join(__dirname, '..', 'data');
const USERS_FILE = path.join(DATA_DIR, 'users.json');

// User store: in-memory Map, persisted to JSON file so accounts survive restarts
const users = new Map();

function ensureDataDir() {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    return true;
  } catch (err) {
    console.error('Auth: could not create data directory:', DATA_DIR, err.message);
    return false;
  }
}

function loadUsers() {
  try {
    if (fs.existsSync(USERS_FILE)) {
      const raw = fs.readFileSync(USERS_FILE, 'utf8');
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) {
        arr.forEach((u) => {
          if (u && u.userId && u.email) {
            users.set(u.userId, {
              userId: u.userId,
              email: u.email,
              password: u.password,
              createdAt: u.createdAt,
              firstName: u.firstName ?? '',
              lastName: u.lastName ?? '',
            });
          }
        });
      }
    }
  } catch (err) {
    console.warn('Auth: could not load users file:', err.message);
  }
}

function saveUsers() {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    const arr = [...users.values()];
    fs.writeFileSync(USERS_FILE, JSON.stringify(arr, null, 2), 'utf8');
    return true;
  } catch (err) {
    console.error('Auth: could not save users file:', err.message);
    return false;
  }
}

if (!ensureDataDir()) {
  console.error('Auth: starting without persistent storage. Signup may fail.');
}
loadUsers();

// CORS: allow frontend origins so login/signup work from browser
const CORS_ORIGINS = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173',
  ...(process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',').map(s => s.trim()).filter(Boolean) : []),
];
app.use(cors({
  origin: CORS_ORIGINS,
  credentials: true,
  methods: ['GET', 'POST', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));
app.use(express.json());

function generateToken(userId) {
  return jwt.sign(
    { sub: userId },
    JWT_SECRET,
    { expiresIn: '7d' }
  );
}

app.post('/api/v1/auth/signup', (req, res) => {
  const raw = req.body || {};
  const email = typeof raw.email === 'string' ? raw.email.trim() : '';
  const password = typeof raw.password === 'string' ? raw.password : '';
  const firstName = typeof raw.firstName === 'string' ? raw.firstName.trim() : '';
  const lastName = typeof raw.lastName === 'string' ? raw.lastName.trim() : '';
  if (!email || !password) {
    return res.status(400).json({ error: 'email and password required' });
  }
  const existing = [...users.values()].find(u => u.email === email);
  if (existing) {
    return res.status(409).json({ error: 'Email already registered' });
  }
  const userId = uuidv4();
  users.set(userId, {
    userId,
    email,
    password,
    firstName,
    lastName,
    createdAt: new Date().toISOString(),
  });
  if (!saveUsers()) {
    users.delete(userId);
    return res.status(500).json({ error: 'Could not save account. Check that auth-service/data is writable.' });
  }
  const token = generateToken(userId);
  return res.status(201).json({ token, userId, email, firstName, lastName });
});

app.post('/api/v1/auth/login', (req, res) => {
  const raw = req.body || {};
  const email = typeof raw.email === 'string' ? raw.email.trim() : '';
  const password = typeof raw.password === 'string' ? raw.password : '';
  if (!email || !password) {
    return res.status(400).json({ error: 'email and password required' });
  }
  const user = [...users.values()].find(u => u.email === email && u.password === password);
  if (!user) {
    return res.status(401).json({ error: 'Invalid email or password' });
  }
  const token = generateToken(user.userId);
  return res.json({
    token,
    userId: user.userId,
    email: user.email,
    firstName: user.firstName ?? '',
    lastName: user.lastName ?? '',
  });
});

function authMiddleware(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authorization required' });
  }
  const token = auth.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.sub;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

app.patch('/api/v1/auth/profile', authMiddleware, (req, res) => {
  const user = users.get(req.userId);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  const raw = req.body || {};
  const firstName = typeof raw.firstName === 'string' ? raw.firstName.trim() : user.firstName ?? '';
  const lastName = typeof raw.lastName === 'string' ? raw.lastName.trim() : user.lastName ?? '';
  user.firstName = firstName;
  user.lastName = lastName;
  if (!saveUsers()) {
    return res.status(500).json({ error: 'Could not save profile.' });
  }
  return res.json({ firstName: user.firstName, lastName: user.lastName });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Auth Service listening on port ${PORT}`);
  console.log(`Auth: user data file: ${USERS_FILE}`);
});
