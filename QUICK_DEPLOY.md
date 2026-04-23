# 🚀 Quick Deploy Guide - VoiceSnap

## Option 1: Deploy Everything on Render (EASIEST - 5 minutes)

### Step 1: Sign Up for Render
1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Deploy Using Blueprint
1. Click **"New +"** → **"Blueprint"**
2. Connect your GitHub repository: `talkify`
3. Render will detect your `render.yaml` file
4. Click **"Apply"**

### Step 3: Add Environment Variables
Render will ask for these environment variables:

**Backend Service:**
```
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

**Note**: Replace with your actual API keys from:
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys
- Google Gemini: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/keys

### Step 4: Wait for Deployment
- Backend: ~5 minutes
- Frontend: ~3 minutes

### Step 5: Get Your URLs
After deployment, you'll get:
- **Frontend**: `https://voicesnap-frontend.onrender.com`
- **Backend**: `https://voicesnap-backend.onrender.com`

### ✅ Done!
Your app is live! Visit the frontend URL to use VoiceSnap.

---

## Option 2: Vercel (Frontend) + Render (Backend) - BEST PERFORMANCE

### Part A: Deploy Backend on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `voicesnap-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free

5. Add Environment Variables:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   CORS_ORIGINS=["*"]
   ENVIRONMENT=production
   PORT=8000
   ```

6. Click **"Create Web Service"**
7. **Save your backend URL**: `https://voicesnap-backend.onrender.com`

### Part B: Deploy Frontend on Vercel

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: (leave empty)
   - **Build Command**: `npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `npm install --prefix frontend`

5. Add Environment Variables:
   ```
   VITE_API_BASE_URL=https://voicesnap-backend.onrender.com
   VITE_WS_URL=wss://voicesnap-backend.onrender.com
   ```
   (Replace with your actual Render backend URL)

6. Click **"Deploy"**

### Part C: Update CORS
1. Go back to Render → Backend Service → Environment
2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=["https://your-vercel-app.vercel.app","http://localhost:5173"]
   ```
3. Save and redeploy

### ✅ Done!
Your app is live with best performance!

---

## 🆓 Free Tier Limits

### Render Free Tier:
- ✅ 750 hours/month
- ✅ Automatic SSL
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ Takes ~30s to wake up

### Vercel Free Tier:
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ No sleep
- ✅ Fast CDN

### Railway Free Tier:
- ✅ $5 credit/month (~500 hours)
- ✅ No sleep
- ⚠️ Limited hours

---

## 🎯 Which Should You Choose?

### Choose **Render Only** if:
- ✅ You want the easiest setup
- ✅ You're okay with 30s wake-up time
- ✅ You want everything in one place

### Choose **Vercel + Render** if:
- ✅ You want best performance
- ✅ You want instant frontend loading
- ✅ You don't mind managing two platforms

### Choose **Vercel + Railway** if:
- ✅ You want best performance
- ✅ You need backend to never sleep
- ✅ You have low traffic (within free tier)

---

## 🐛 Troubleshooting

### Backend won't start on Render
- Check environment variables are set
- Check build logs for errors
- Verify `requirements.txt` is correct

### Frontend shows 404 on Vercel
- Verify Root Directory is empty or `.`
- Check Output Directory is `frontend/dist`
- Check Build Command is `npm run build`

### CORS errors
- Update `CORS_ORIGINS` in backend environment variables
- Include your frontend URL
- Redeploy backend

### WebSocket not connecting
- Use `wss://` (not `ws://`) for production
- Verify backend URL is correct
- Check backend logs

---

## 📞 Need Help?

Check the full `DEPLOYMENT.md` for detailed troubleshooting and advanced configuration.
