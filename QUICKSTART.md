# 🚀 GitInsight Quick Reference

## 📦 Environment Variables

### Backend (.env)
```bash
GEMINI_API_KEY=your-key-here
GITHUB_TOKEN=your-token-here  # Optional but recommended
FRONTEND_URL=https://your-app.vercel.app  # Production only
```

### Frontend (.env.local) - Production Only
```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

---

## 🏃 Running Locally

### Option 1: PowerShell Scripts
```powershell
# Backend (Terminal 1)
.\backend\start-dev.ps1

# Frontend (Terminal 2)
.\frontend\start-dev.ps1
```

### Option 2: Manual Commands
```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## 🌐 URLs

| Environment  | Backend              | Frontend             |
| ------------ | -------------------- | -------------------- |
| Local        | http://localhost:8000| http://localhost:3000|
| Production   | your-app.onrender.com| your-app.vercel.app  |

---

## 🔗 API Endpoints

- `GET /health` - Health check
- `POST /api/v1/ingest` - Fetch repository data
- `POST /api/v1/evaluate` - Evaluate repository quality
- `POST /api/v1/analyze` - Full analysis pipeline

---

## 📝 Pre-Deployment Checklist

### Backend (Render)
- [ ] `render.yaml` exists in backend/
- [ ] `requirements.txt` is up to date
- [ ] `.env.example` documents all variables
- [ ] CORS configured with FRONTEND_URL

### Frontend (Vercel)
- [ ] `package.json` has build script
- [ ] `.env.example` documents NEXT_PUBLIC_API_URL
- [ ] API calls use environment variable

### Both
- [ ] No secrets in Git
- [ ] `.env` files in `.gitignore`
- [ ] README updated
- [ ] DEPLOYMENT.md reviewed

---

## 🆘 Common Issues

| Error                  | Fix                                 |
| ---------------------- | ----------------------------------- |
| CORS error             | Update FRONTEND_URL in Render       |
| API 404                | Check NEXT_PUBLIC_API_URL in Vercel |
| Module not found       | Run `pip install -r requirements.txt`|
| Timeout                | Render free tier cold start (~30s)  |

---

## 📚 Documentation
- Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Backend README: [backend/README.md](backend/README.md)
- Main README: [README.md](README.md)
