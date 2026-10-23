import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'bis-assistant-secret-key-change-in-production';
const JWT_EXPIRES_IN = '7d';

/**
 * Generate JWT access token for a user.
 */
export function generateToken(user) {
  return jwt.sign(
    { userId: user.id, email: user.email, role: user.role },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );
}

/**
 * Set JWT as HTTP-only cookie on the response.
 */
const isProduction = process.env.NODE_ENV === 'production';

export function setTokenCookie(res, token) {
  res.cookie('token', token, {
    httpOnly: true,
    secure: isProduction,
    sameSite: isProduction ? 'none' : 'lax',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    path: '/'
  });
}

/**
 * Clear the auth cookie.
 */
export function clearTokenCookie(res) {
  res.clearCookie('token', {
    httpOnly: true,
    secure: isProduction,
    sameSite: isProduction ? 'none' : 'lax',
    path: '/'
  });
}

/**
 * Auth middleware — verifies JWT from Authorization Bearer header or cookie.
 * Attaches req.user = { userId, email, role }
 */
export function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  const bearerToken = authHeader && authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;
  const token = bearerToken || req.cookies?.token;

  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

/**
 * Admin-only middleware — must be used AFTER authMiddleware.
 */
export function adminOnly(req, res, next) {
  if (req.user?.role !== 'ADMIN') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
}
