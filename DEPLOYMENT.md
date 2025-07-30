# Deployment Guide - Secure Environment Variables

## 🔐 **Security First - Environment Variables**

**NEVER commit API keys, tokens, or secrets to git!**

## 🚀 **Vercel Deployment Setup**

### **Step 1: Set Environment Variables in Vercel Dashboard**

Go to your Vercel project settings → Environment Variables and add:

```bash
# Required Variables
OPENAI_API_KEY=your_actual_openai_api_key
ENVIRONMENT=production
DEBUG=false

# Security (Generate strong random string)
SECRET_KEY=your_generated_strong_secret_key

# CORS Origins
ALLOWED_ORIGINS=["https://your-frontend-url.vercel.app","https://lumilens.ai"]

# Database Paths (Vercel compatible)
CHROMA_PATH=/tmp/chroma_db
DATA_PATH=/tmp/data

# OpenAI Configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Document Processing
CHUNK_SIZE=300
CHUNK_OVERLAP=100
MAX_FILE_SIZE=52428800
```

### **Step 2: Deploy Backend**

```bash
# Deploy to Vercel
vercel --prod

# The deployment will automatically use environment variables from dashboard
```

## 🔧 **GitHub Actions Setup (Optional)**

### **Step 1: Add Secrets to GitHub Repository**

Go to Settings → Secrets and variables → Actions:

```bash
# Repository Secrets
OPENAI_API_KEY=your_actual_openai_api_key
VERCEL_TOKEN=your_vercel_deployment_token
VERCEL_ORG_ID=your_vercel_org_id  
VERCEL_PROJECT_ID=your_vercel_project_id
```

### **Step 2: Create Deployment Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [deploy-facts]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## 🏠 **Local Development Setup**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your actual values
# (This file is gitignored and won't be committed)

# 3. Start development server
python run_server.py
```

## ✅ **Security Checklist**

- [ ] `.env` files are in `.gitignore`
- [ ] No secrets in git history
- [ ] Environment variables set in Vercel dashboard
- [ ] GitHub secrets configured (if using CI/CD)
- [ ] Strong secret keys generated
- [ ] CORS origins properly configured

## 🔄 **Integration with Frontend**

The frontend should use environment variables to connect:

```typescript
// Frontend .env.local (gitignored)
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

Remember: **Never commit environment files with actual secrets!**
