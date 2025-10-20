# Mantra Chat Widget Guide 💬

## Overview

The Mantra Chat Widget provides a **lightweight, embeddable chatbot interface** similar to chat widgets on Facebook, Amazon, and other modern websites. It features:

- 🎯 **Floating chat button** in the bottom-right corner
- 💬 **Expandable chat window** that appears on click
- 🤖 **RAG-powered responses** using FAISS + GPT-4
- 📚 **Source citations** for every answer
- 🎨 **Beautiful, modern UI** with smooth animations

---

## Architecture

### Components

1. **FastAPI Backend** (`chat_api.py`)
   - REST API that exposes the RAG functionality
   - Endpoints: `/chat`, `/health`, `/examples`
   - Handles query classification, search, and response generation

2. **Chat Widget Frontend** (`static/`)
   - `index.html` - Main demo page with embedded widget
   - `chat-widget.js` - JavaScript for chat interactions
   - Pure HTML/CSS/JS - no frameworks required

### How It Works

```
User clicks chat button
    ↓
Chat window opens
    ↓
User types query
    ↓
JavaScript sends POST to /chat endpoint
    ↓
FastAPI processes:
    1. Query classification (relevant?)
    2. FAISS search (find cases)
    3. GPT-4 response generation
    4. Format sources
    ↓
Response appears in chat window
```

---

## 🚀 Quick Start

### Step 1: Start the Server

```bash
cd "/Users/mb16/My Drive (koosha.g@gmail.com)/code/mantra"
./start_chat_widget.sh
```

This will:
- Activate the virtual environment
- Check if FAISS index exists
- Start the FastAPI server on port 8000
- Display the URL to access

### Step 2: Open in Browser

Open your browser and go to:
```
http://localhost:8000
```

You'll see:
- A demo page explaining the widget
- A **purple chat button** in the bottom-right corner

### Step 3: Test the Chat

1. **Click the chat button** - the chat window will slide up
2. **Type a question** like "What is fiduciary duty?"
3. **Press Enter** or click the send button
4. **Wait for response** - you'll see a typing indicator
5. **View the answer** with case citations

---

## 💻 Manual Server Start

If you prefer to start manually:

```bash
cd "/Users/mb16/My Drive (koosha.g@gmail.com)/code/mantra"
source .venv/bin/activate
python3 chat_api.py
```

The server will start on `http://localhost:8000`

To stop: Press `Ctrl+C`

---

## 🎯 API Endpoints

### POST /chat

Send a message to the chatbot.

**Request:**
```json
{
  "message": "What is fiduciary duty?"
}
```

**Response:**
```json
{
  "message": "Fiduciary duty is a fundamental legal obligation...",
  "relevant": true,
  "sources": [
    {
      "case_name": "Smith v. Van Gorkom",
      "date": "1985-01-29",
      "court": "delaware-supreme",
      "citation": "Smith v. Van Gorkom, 488 A.2d 858 (Del. 1985)",
      "url": "https://www.courtlistener.com/opinion/..."
    }
  ],
  "confidence": "high"
}
```

### GET /health

Check if the server is healthy and the index is loaded.

**Response:**
```json
{
  "status": "healthy",
  "index_loaded": true,
  "vectors": 10
}
```

### GET /examples

Get example queries (relevant and irrelevant).

**Response:**
```json
{
  "relevant": [
    "What is fiduciary duty?",
    "Explain the Revlon doctrine",
    ...
  ],
  "irrelevant": [
    "Who is Koosha?",
    "What's the weather today?",
    ...
  ]
}
```

---

## 🎨 Customization

### Change Colors

Edit `static/index.html` and modify the CSS:

```css
/* Change chat button gradient */
#mantra-chat-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Change to your colors */
}

/* Change chat header gradient */
.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Match your brand */
}
```

### Change Position

Move the chat button to a different corner:

```css
#mantra-chat-widget {
    /* bottom-right (default) */
    bottom: 20px;
    right: 20px;

    /* bottom-left */
    /* bottom: 20px; */
    /* left: 20px; */
}
```

### Change Size

Adjust the chat window dimensions:

```css
#mantra-chat-window {
    width: 380px;      /* Change width */
    height: 550px;     /* Change height */
}
```

---

## 📦 Embedding in Your Website

To embed the chat widget in your own website:

### Option 1: Include as Script

1. Copy `static/chat-widget.js` to your website
2. Add the chat widget HTML to your page
3. Include the script:

```html
<!-- Add near the end of your <body> tag -->
<div id="mantra-chat-widget">
    <!-- Chat button -->
    <button id="mantra-chat-button">💬</button>

    <!-- Chat window -->
    <div id="mantra-chat-window">
        <!-- Chat interface HTML -->
    </div>
</div>

<script src="/path/to/chat-widget.js"></script>
```

### Option 2: Use as Widget (Recommended)

1. Host the FastAPI backend on your server
2. Create a simple widget loader:

```html
<!-- Add to your website -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://your-domain.com/widget/mantra-widget.js';
    document.body.appendChild(script);
  })();
</script>
```

3. Update the API URL in `chat-widget.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com';
```

---

## 🔒 Production Deployment

### Security Considerations

1. **CORS Configuration**
   Edit `chat_api.py` to restrict origins:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specify your domain
       allow_credentials=True,
       allow_methods=["POST", "GET"],
       allow_headers=["*"],
   )
   ```

2. **Rate Limiting**
   Add rate limiting to prevent abuse:
   ```bash
   pip install slowapi
   ```

   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter

   @app.post("/chat")
   @limiter.limit("10/minute")
   async def chat(request: Request, message: ChatMessage):
       ...
   ```

3. **HTTPS**
   Always use HTTPS in production:
   ```bash
   uvicorn chat_api:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
   ```

### Hosting Options

**Option A: Traditional Server (VPS/EC2)**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn chat_api:app --host 0.0.0.0 --port 8000 --workers 4

# Or use gunicorn + uvicorn workers
gunicorn chat_api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**Option B: Docker**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "chat_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option C: Cloud Platforms**
- **AWS**: Deploy with Elastic Beanstalk or ECS
- **Google Cloud**: Use App Engine or Cloud Run
- **Heroku**: Simple `git push` deployment
- **Railway**: One-click deployment

---

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is fiduciary duty?"}'

# Get examples
curl http://localhost:8000/examples
```

### Test in Different Browsers

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

---

## 🐛 Troubleshooting

### Server won't start

**Problem**: `Address already in use` error

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn chat_api:app --port 8001
```

### Chat not responding

**Problem**: Messages sent but no response

**Solution**:
1. Check server logs for errors
2. Verify FAISS index is loaded: `curl http://localhost:8000/health`
3. Check browser console for JavaScript errors
4. Verify OpenAI API key in `.env`

### CORS errors

**Problem**: `CORS policy` error in browser console

**Solution**:
- Make sure CORS is enabled in `chat_api.py`
- Check `allow_origins` includes your domain
- For local testing, `allow_origins=["*"]` is fine

### Slow responses

**Problem**: Chat takes too long to respond

**Solution**:
- Use GPT-4o-mini instead of GPT-4 (10x faster)
- Reduce search results: `indexer.search(query, k=2)`
- Enable caching for common queries
- Use IndexIVFFlat for faster FAISS search

---

## 📊 Performance

### Current Setup (5 cases)
- **Index load time**: < 1 second
- **Search time**: < 50ms
- **Response time**: 2-5 seconds (mostly GPT-4)

### Production Setup (2,500 cases)
- **Index load time**: ~2-3 seconds
- **Search time**: < 100ms
- **Response time**: 2-5 seconds
- **Memory usage**: ~500MB

### Optimization Tips

1. **Reduce LLM latency**:
   - Use streaming responses
   - Cache common queries
   - Use GPT-4o-mini for simple questions

2. **Scale the backend**:
   - Run multiple uvicorn workers
   - Use a load balancer (nginx)
   - Cache embeddings with Redis

3. **Optimize frontend**:
   - Minify JavaScript/CSS
   - Use CDN for static files
   - Implement lazy loading

---

## 💰 Cost Analysis

### Per 1,000 Queries

| Component | Cost |
|-----------|------|
| Embeddings (query) | $0.02 |
| GPT-4 responses | $150 |
| **Total** | **~$150** |

### Cost Optimization

- **Use GPT-4o-mini**: ~$15/1000 queries (10x cheaper)
- **Cache responses**: Save on repeat questions
- **Smart batching**: Combine similar queries

---

## 🎉 Success!

Your Mantra Chat Widget is now ready!

**To start using:**

1. Run: `./start_chat_widget.sh`
2. Open: `http://localhost:8000`
3. Click the chat button
4. Ask about Delaware law!

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **FAISS Guide**: See `FAISS_IMPLEMENTATION.md`
- **Tech Stack**: See `TECH_STACK_FINAL.md`
- **Original Implementation**: See `IMPLEMENTATION_COMPLETE.md`

---

## 🆘 Support

If you encounter issues:
1. Check the server logs
2. Verify FAISS index exists
3. Test API endpoints with curl
4. Check browser console for errors

For questions about Delaware law, just ask Mantra! 💬⚖️
