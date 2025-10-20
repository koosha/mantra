# How to Run the Chat Widget

## ✅ Simple 2-Step Process

### Step 1: Open Terminal

Navigate to the project folder:
```bash
cd "/Users/mb16/My Drive (koosha.g@gmail.com)/code/mantra"
```

### Step 2: Run This Command

```bash
source .venv/bin/activate && python3 chat_api.py
```

**That's it!** The server will start and show you:
```
INFO:     Initializing Mantra components...
INFO:     ✅ Loaded FAISS index with 10 vectors
INFO:     ✅ Initialized query classifier
INFO:     ✅ Initialized response generator
INFO:     🎉 Mantra is ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Open Browser

While the server is running, open your browser to:
```
http://localhost:8000
```

---

## ✋ If You Get "Address in Use" Error

Run this first to kill any existing servers:
```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null
```

Then run the start command again.

---

## 🛑 To Stop the Server

Press **Ctrl+C** in the terminal where the server is running.

---

## 🧪 Quick Test

To test if the API is working:

```bash
# In a NEW terminal window (keep server running in first terminal)
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "index_loaded": true,
  "vectors": 10
}
```

---

## 🎯 What You'll See in Browser

1. **Demo page** with Mantra branding
2. **Purple chat button** (💬) in bottom-right corner
3. **Click button** → Chat window opens
4. **Type question** → Get AI response with case citations!

---

## ⚡ Example Questions to Try

- "What is fiduciary duty?"
- "Explain the Revlon doctrine"
- "What is the business judgment rule?"
- "Explain the MFW framework"

---

## 📱 Works On

- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Mobile browsers (responsive design)
- ✅ Tablets

---

## 🔧 Troubleshooting

**Problem: Nothing appears when I open localhost:8000**

Solution:
- Check that the server is actually running (look for "Uvicorn running" message)
- Try refreshing the page (Cmd+R or F5)
- Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)

**Problem: Chat doesn't respond**

Solution:
- Check server terminal for errors
- Verify FAISS index exists: `ls -la faiss_index/`
- Check browser console for errors (F12 → Console tab)

---

**Ready? Run the command above and open http://localhost:8000!** 🚀
