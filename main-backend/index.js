import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';
import pkg from '@prisma/client';
const { PrismaClient } = pkg;
import { PrismaPg } from '@prisma/adapter-pg';
import pg from 'pg';

import { authMiddleware, adminOnly } from './auth.js';
import { createAuthRouter } from './auth-routes.js';

dotenv.config();

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL
});
const adapter = new PrismaPg(pool);

const app = express();
const prisma = new PrismaClient({ adapter });
const PORT = process.env.PORT || 3000;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use(cookieParser());

// --- Auth Routes (public) ---
app.use('/api/auth', createAuthRouter(prisma));

// --- Chat History API (protected) ---
app.get('/api/conversations', authMiddleware, async (req, res) => {
  const userId = req.user.userId;
  const convos = await prisma.conversation.findMany({
    where: { userId },
    orderBy: { updatedAt: 'desc' }
  });
  res.json(convos);
});

// --- AI Proxy API (protected) ---
app.post('/api/chat', authMiddleware, async (req, res) => {
  const { query, language, conversationId } = req.body;
  const userId = req.user.userId;
  
  if (!query) {
    return res.status(400).json({ error: 'Query is required' });
  }

  try {
    // 1. Save User Message
    let currentConvoId = conversationId;
    if (!currentConvoId) {
      const newConvo = await prisma.conversation.create({
        data: { userId, title: query.substring(0, 30) }
      });
      currentConvoId = newConvo.id;
    }

    await prisma.message.create({
      data: {
        conversationId: currentConvoId,
        role: 'user',
        content: query
      }
    });

    // 2. Call FastAPI AI Service
    const aiResponse = await fetch(`${AI_SERVICE_URL}/api/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, language: language || 'English' })
    });
    
    const data = await aiResponse.json();

    // 3. Save AI Message
    if (data.answer) {
      await prisma.message.create({
        data: {
          conversationId: currentConvoId,
          role: 'assistant',
          content: data.answer,
          sources: data.sources || []
        }
      });
    }

    res.json({
      conversationId: currentConvoId,
      answer: data.answer,
      sources: data.sources
    });

  } catch (error) {
    console.error('Error in AI Proxy:', error);
    res.status(500).json({ error: 'Failed to process chat query' });
  }
});

app.listen(PORT, () => {
  console.log(`Main Backend running on port ${PORT}`);
});
