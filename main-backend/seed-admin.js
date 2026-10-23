/**
 * Seed Admin Script
 * Usage: node seed-admin.js
 * 
 * Creates a single admin user in the database.
 * Uses environment variables or defaults for credentials.
 */
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import pkg from '@prisma/client';
const { PrismaClient } = pkg;
import { PrismaPg } from '@prisma/adapter-pg';
import pg from 'pg';

dotenv.config();

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@bis.gov.in';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';
const ADMIN_NAME = 'BIS Admin';

async function seedAdmin() {
  const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
  const adapter = new PrismaPg(pool);
  const prisma = new PrismaClient({ adapter });

  try {
    // Check if admin already exists
    const existing = await prisma.user.findUnique({ where: { email: ADMIN_EMAIL } });
    if (existing) {
      console.log(`\n⚠️  Admin user already exists: ${ADMIN_EMAIL}`);
      console.log(`   Role: ${existing.role}`);
      await pool.end();
      process.exit(0);
    }

    // Create admin
    const passwordHash = await bcrypt.hash(ADMIN_PASSWORD, 12);
    const admin = await prisma.user.create({
      data: {
        email: ADMIN_EMAIL,
        passwordHash,
        name: ADMIN_NAME,
        role: 'ADMIN'
      }
    });

    console.log('\n✅ Admin user created successfully!');
    console.log(`   Email:    ${admin.email}`);
    console.log(`   Password: ${ADMIN_PASSWORD}`);
    console.log(`   Role:     ${admin.role}`);
    console.log('\n   You can now login with these credentials.\n');

  } catch (error) {
    console.error('❌ Failed to seed admin:', error.message);
  } finally {
    await pool.end();
    process.exit(0);
  }
}

seedAdmin();
