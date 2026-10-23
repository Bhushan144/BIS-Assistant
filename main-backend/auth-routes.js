import express from 'express';
import bcrypt from 'bcryptjs';
import { generateToken, setTokenCookie, clearTokenCookie, authMiddleware } from './auth.js';

export function createAuthRouter(prisma) {
  const router = express.Router();

  /**
   * POST /api/auth/register
   * Public — creates a new USER account.
   */
  router.post('/register', async (req, res) => {
    const { email, password, name } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters' });
    }

    try {
      const existing = await prisma.user.findUnique({ where: { email } });
      if (existing) {
        return res.status(409).json({ error: 'Email already registered' });
      }

      const passwordHash = await bcrypt.hash(password, 12);
      const user = await prisma.user.create({
        data: { email, passwordHash, name: name || null, role: 'USER' }
      });

      const token = generateToken(user);
      setTokenCookie(res, token);

      res.status(201).json({
        user: { id: user.id, email: user.email, name: user.name, role: user.role }
      });
    } catch (error) {
      console.error('Register error:', error);
      res.status(500).json({ error: 'Registration failed' });
    }
  });

  /**
   * POST /api/auth/login
   * Public — authenticates user or admin.
   */
  router.post('/login', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    try {
      const user = await prisma.user.findUnique({ where: { email } });
      if (!user) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }

      const valid = await bcrypt.compare(password, user.passwordHash);
      if (!valid) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }

      const token = generateToken(user);
      setTokenCookie(res, token);

      res.json({
        user: { id: user.id, email: user.email, name: user.name, role: user.role }
      });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  });

  /**
   * POST /api/auth/logout
   * Clears the auth cookie.
   */
  router.post('/logout', (_req, res) => {
    clearTokenCookie(res);
    res.json({ message: 'Logged out successfully' });
  });

  /**
   * GET /api/auth/me
   * Protected — returns the current authenticated user.
   */
  router.get('/me', authMiddleware, async (req, res) => {
    try {
      const user = await prisma.user.findUnique({
        where: { id: req.user.userId },
        select: { id: true, email: true, name: true, role: true, createdAt: true }
      });
      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }
      res.json({ user });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch user' });
    }
  });

  return router;
}
