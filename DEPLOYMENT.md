# VoiceSnap Deployment Guide

## 🚀 Deployment Architecture

VoiceSnap uses a **split deployment strategy**:
- **Backend (Python/FastAPI)**: Deploy on Render
- **Frontend (React/Vite)**: Deploy on Vercel

## 📦 Backend Deployment (Render)

### Step 1: Deploy Backend to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `voicesnap-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free or Starter

### Step 2: Add Environment Variables

Add these environment variables in Render:

```
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
CORS_ORIGINS=["https://your-vercel-app.vercel.app"]
ENVIRONMENT=production
DEBUG=false
PORT=8000
```

### Step 3: Note Your Backend URL

After deployment, Render will give you a URL like:
```
https://voicesnap-backend.onrender.com
```

Save this URL - you'll need it for the frontend deployment.

## 🎨 Frontend Deployment (Vercel)

### Step 1: Deploy Frontend to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### Step 2: Add Environment Variables

Add these environment variables in Vercel:

```
VITE_API_BASE_URL=https://voicesnap-backend.onrender.com
VITE_WS_URL=wss://voicesnap-backend.onrender.com
```

**Important**: Replace `voicesnap-backend.onrender.com` with your actual Render backend URL.

### Step 3: Deploy

Click "Deploy" and wait for the build to complete.

## 🔧 Alternative: Deploy Both on Render

If you prefer to deploy both frontend and backend on Render:

1. Use the included `render.yaml` file
2. Push to GitHub
3. In Render Dashboard, click "New +" → "Blueprint"
4. Connect your repository
5. Render will automatically deploy both services

The `render.yaml` is already configured for this approach.

## 🔐 CORS Configuration

After deploying, update your backend CORS settings:

1. Go to Render Dashboard → Your Backend Service → Environment
2. Update `CORS_ORIGINS` to include your Vercel frontend URL:
   ```
   CORS_ORIGINS=["https://your-app.vercel.app","http://localhost:5173"]
   ```

## ✅ Verify Deployment

### Backend Health Check
Visit: `https://your-backend.onrender.com/health`

Should return:
```json
{
  "status": "healthy",
  "service": "VoiceSnap API"
}
```

### Frontend Check
Visit: `https://your-app.vercel.app`

Should load the VoiceSnap home screen.

## 🐛 Troubleshooting

### 404 Error on Vercel

**Problem**: Getting 404 NOT_FOUND error

**Solution**: 
1. Make sure you're deploying from the `frontend` directory
2. Check that `vercel.json` is in the root directory
3. Verify the build command is correct
4. Check Vercel build logs for errors

### CORS Errors

**Problem**: API requests failing with CORS errors

**Solution**:
1. Update `CORS_ORIGINS` in Render backend environment variables
2. Include your Vercel frontend URL
3. Redeploy the backend

### WebSocket Connection Failed

**Problem**: Voice conversation not working

**Solution**:
1. Check that `VITE_WS_URL` uses `wss://` (not `ws://`)
2. Verify the backend URL is correct
3. Check backend logs for WebSocket errors

### Audio Files Not Playing

**Problem**: Songs and voice responses not playing

**Solution**:
1. Check that audio files are being generated (backend logs)
2. Verify CORS headers are set correctly for audio files
3. Check browser console for audio loading errors

## 📝 Environment Variables Summary

### Backend (Render)
```env
ELEVENLABS_API_KEY=sk_...
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
CORS_ORIGINS=["https://your-app.vercel.app"]
ENVIRONMENT=production
DEBUG=false
PORT=8000
```

### Frontend (Vercel)
```env
VITE_API_BASE_URL=https://voicesnap-backend.onrender.com
VITE_WS_URL=wss://voicesnap-backend.onrender.com
```

## 🎉 Success!

Once deployed, your VoiceSnap app will be live at:
- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://voicesnap-backend.onrender.com`

Share your app and let objects come to life! 🌟
