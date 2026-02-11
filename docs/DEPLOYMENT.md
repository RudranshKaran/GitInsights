# 🚀 GitInsight Deployment Guide

This guide walks you through deploying GitInsight to production using **Render** (backend) and **Vercel** (frontend).

## 📋 Prerequisites

- GitHub account
- Render account ([render.com](https://render.com))
- Vercel account ([vercel.com](https://vercel.com))
- Google Gemini API key ([aistudio.google.com](https://aistudio.google.com/app/apikey))
- GitHub Personal Access Token (optional, but recommended)

---

## 🏗 Architecture

```
User Browser
     ↓
Vercel (Frontend - Next.js)
     ↓
Render (Backend - FastAPI)
     ↓
GitHub API + Google Gemini API
```

---

## 🔧 Backend Deployment (Render)

### Step 1: Prepare Backend Files

Ensure your `backend/` folder contains:
- ✅ `app/` directory with all Python code
- ✅ `requirements.txt`
- ✅ `render.yaml` (already created)
- ✅ `.env.example` (already created)

### Step 2: Create Web Service on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository: `GitInsights`
5. Configure the service:

| Setting              | Value                                              |
| -------------------- | -------------------------------------------------- |
| **Name**             | `gitinsight-backend` (or your choice)              |
| **Region**           | Choose closest to your users                       |
| **Branch**           | `main` (or your default branch)                    |
| **Root Directory**   | `backend`                                          |
| **Runtime**          | `Python 3`                                         |
| **Build Command**    | `pip install -r requirements.txt`                  |
| **Start Command**    | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan**             | Free (or Starter for better performance)           |

### Step 3: Add Environment Variables

In the Render dashboard, go to **"Environment"** and add:

| Variable                  | Value                                    | Required |
| ------------------------- | ---------------------------------------- | -------- |
| `GEMINI_API_KEY`          | Your Google Gemini API key               | ✅        |
| `GITHUB_TOKEN`            | Your GitHub Personal Access Token        | ⚠️       |
| `FRONTEND_URL`            | `https://your-app.vercel.app`            | ✅        |
| `PORT`                    | `10000` (auto-set by Render)             | ✅        |
| `RATE_LIMIT`              | `10/minute` (default)                    | ❌        |
| `REQUEST_TIMEOUT_SECONDS` | `90` (default)                           | ❌        |
| `CACHE_TTL_SECONDS`       | `900` (default)                          | ❌        |
| `CACHE_MAX_SIZE`          | `100` (default)                          | ❌        |

**Important Notes:**
- ✅ = Required
- ⚠️ = Highly recommended (increases API rate limits)
- ❌ = Optional (has sensible defaults)
- **FRONTEND_URL**: Set this AFTER deploying frontend (Step 3 below)
- **No trailing slash** in FRONTEND_URL

### Step 4: Deploy Backend

1. Click **"Create Web Service"**
2. Render will automatically build and deploy
3. Wait for deployment to complete (~2-3 minutes)
4. Copy your backend URL: `https://gitinsight-backend.onrender.com`

### Step 5: Test Backend

Visit your health endpoint:
```
https://gitinsight-backend.onrender.com/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T..."
}
```

---

## ⚡ Frontend Deployment (Vercel)

### Step 1: Prepare Frontend Files

Ensure your `frontend/` folder contains:
- ✅ `package.json` with `build` script
- ✅ `app/` directory with Next.js pages
- ✅ `.env.example` (already created)

### Step 2: Deploy to Vercel

1. Go to [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `GitInsights`
4. Configure the project:

| Setting                | Value                        |
| ---------------------- | ---------------------------- |
| **Framework Preset**   | Next.js (auto-detected)      |
| **Root Directory**     | `frontend`                   |
| **Build Command**      | `npm run build` (default)    |
| **Output Directory**   | `.next` (default)            |
| **Install Command**    | `npm install` (default)      |

### Step 3: Add Environment Variables

Before deploying, click **"Environment Variables"** and add:

| Variable                | Value                                       | Environment |
| ----------------------- | ------------------------------------------- | ----------- |
| `NEXT_PUBLIC_API_URL`   | `https://gitinsight-backend.onrender.com`   | Production  |

**Important:**
- Replace with YOUR actual Render backend URL
- **No trailing slash** in the URL
- This must match your `FRONTEND_URL` in Render (but without the scheme if needed)

### Step 4: Deploy Frontend

1. Click **"Deploy"**
2. Vercel will build and deploy (~1-2 minutes)
3. Copy your frontend URL: `https://gitinsight-abc123.vercel.app`

### Step 5: Update Backend CORS

⚠️ **Important:** Go back to Render and update the `FRONTEND_URL` environment variable:

1. Go to Render dashboard → Your web service
2. Navigate to **"Environment"**
3. Update `FRONTEND_URL` to: `https://gitinsight-abc123.vercel.app`
4. Click **"Save Changes"**
5. Render will automatically redeploy

---

## 🧪 Testing Production Deployment

### 1. Test Frontend
Visit your Vercel URL: `https://your-app.vercel.app`

### 2. Test Full Flow
1. Click **"Analyze Your Repository"**
2. Enter a GitHub URL (e.g., `https://github.com/facebook/react`)
3. Wait for analysis (~30-60 seconds)
4. Verify you see the report with scores

### 3. Check Logs

**Backend Logs (Render):**
- Go to Render dashboard → Your service → **"Logs"**
- Check for errors or warnings

**Frontend Logs (Vercel):**
- Go to Vercel dashboard → Your project → **"Deployments"** → **"Functions"**
- Check for runtime errors

---

## 🔧 Local Development

### Backend (FastAPI)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`

### Frontend (Next.js)
```powershell
cd frontend
npm install
cp .env.local.example .env.local
# Optional: Edit .env.local if needed (for local dev, you can leave it empty)
npm run dev
```

Frontend runs at: `http://localhost:3000`

---

## 🔐 Environment Variables Reference

### Backend (Render)

| Variable                  | Description                              | Required | Default         |
| ------------------------- | ---------------------------------------- | -------- | --------------- |
| `GEMINI_API_KEY`          | Google Gemini API key for AI analysis    | ✅        | N/A             |
| `GITHUB_TOKEN`            | GitHub PAT for higher rate limits        | ⚠️       | N/A             |
| `FRONTEND_URL`            | Vercel frontend URL for CORS             | ✅        | N/A             |
| `PORT`                    | Server port (set by Render)              | ✅        | `10000`         |
| `RATE_LIMIT`              | API rate limit per IP                    | ❌        | `10/minute`     |
| `REQUEST_TIMEOUT_SECONDS` | Maximum request duration                 | ❌        | `90`            |
| `CACHE_TTL_SECONDS`       | Cache time-to-live                       | ❌        | `900`           |
| `CACHE_MAX_SIZE`          | Maximum cached responses                 | ❌        | `100`           |

### Frontend (Vercel)

| Variable                | Description                       | Required | Default |
| ----------------------- | --------------------------------- | -------- | ------- |
| `NEXT_PUBLIC_API_URL`   | Backend API URL (Render)          | ✅        | N/A     |

---

## 🚨 Troubleshooting

### ❌ CORS Error: "Access blocked by CORS policy"

**Cause:** Frontend URL doesn't match `FRONTEND_URL` in backend

**Solution:**
1. Check Render environment variable `FRONTEND_URL`
2. Ensure it exactly matches your Vercel URL
3. Remove any trailing slashes
4. Redeploy backend after changes

### ❌ 404: "Cannot POST /api/v1/analyze"

**Cause:** Frontend is using wrong API URL

**Solution:**
1. Check Vercel environment variable `NEXT_PUBLIC_API_URL`
2. Ensure it matches your Render backend URL
3. Remove any trailing slashes
4. Redeploy frontend after changes

### ❌ Timeout: "Analysis taking longer than expected"

**Causes:**
- Render free tier cold starts (~30 seconds)
- Large repository analysis
- API rate limits

**Solutions:**
- Wait 30-60 seconds for cold start
- Try a smaller repository
- Upgrade to Render paid plan
- Add `GITHUB_TOKEN` for higher rate limits

### ❌ 500: "Internal Server Error"

**Cause:** Missing API keys or configuration

**Solution:**
1. Check Render logs for errors
2. Verify `GEMINI_API_KEY` is set correctly
3. Check API key is valid and has credits
4. Restart Render service

### ❌ "Module not found" errors

**Cause:** Missing dependencies

**Solution:**
1. Check `requirements.txt` is in `backend/` folder
2. Verify build command: `pip install -r requirements.txt`
3. Check Render build logs
4. Redeploy service

---

## 💡 Best Practices

### Security
- ✅ Never commit `.env` files to Git
- ✅ Use environment variables for all secrets
- ✅ Rotate API keys regularly
- ✅ Enable Vercel password protection for staging

### Performance
- ✅ Use Render paid tier for production (no cold starts)
- ✅ Add `GITHUB_TOKEN` for higher API rate limits
- ✅ Monitor cache hit rates
- ✅ Set appropriate timeout values

### Monitoring
- ✅ Check Render logs daily
- ✅ Set up Render alerts for downtime
- ✅ Monitor Vercel function execution times
- ✅ Track API error rates

### Cost Optimization
- ✅ Use free tiers for MVP/testing
- ✅ Implement caching to reduce API calls
- ✅ Set rate limits to prevent abuse
- ✅ Monitor API usage and costs

---

## 📝 Production Checklist

Before going live, verify:

### Backend (Render)
- [ ] Service deployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] `GEMINI_API_KEY` is set
- [ ] `GITHUB_TOKEN` is set (optional but recommended)
- [ ] `FRONTEND_URL` matches Vercel URL exactly
- [ ] No trailing slashes in URLs
- [ ] Logs show no errors
- [ ] CORS configured correctly

### Frontend (Vercel)
- [ ] Deployment successful
- [ ] `NEXT_PUBLIC_API_URL` is set
- [ ] Landing page loads correctly
- [ ] Analyze page loads correctly
- [ ] No console errors in browser
- [ ] CSS/styling renders correctly

### Integration
- [ ] Full analysis flow works end-to-end
- [ ] Test with public repository
- [ ] Error messages display correctly
- [ ] Loading states work properly
- [ ] Report displays correctly
- [ ] No CORS errors
- [ ] API calls complete successfully

### Security
- [ ] No secrets in Git repository
- [ ] `.env` files in `.gitignore`
- [ ] API keys are valid and active
- [ ] Rate limiting enabled
- [ ] CORS restricted to frontend URL only

---

## 🆘 Support

**Render Documentation:** https://render.com/docs
**Vercel Documentation:** https://vercel.com/docs
**FastAPI Documentation:** https://fastapi.tiangolo.com
**Next.js Documentation:** https://nextjs.org/docs

---

## 📚 Additional Resources

- **Google Gemini API:** https://ai.google.dev/docs
- **GitHub API:** https://docs.github.com/en/rest
- **Render Free Tier:** https://render.com/docs/free
- **Vercel Hobby Plan:** https://vercel.com/docs/concepts/limits/overview

---

## 🎉 Congratulations!

Your GitInsight application is now deployed and ready to analyze GitHub repositories!

Share your deployment URL and start getting insights! 🚀
