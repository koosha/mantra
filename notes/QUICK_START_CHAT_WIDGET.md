# Quick Start - Mantra Chat Widget 🚀

## Start in 3 Steps

### 1. Start the Server

```bash
cd "/Users/mb16/My Drive (koosha.g@gmail.com)/code/mantra"
./start_chat_widget.sh
```

### 2. Open Browser

Go to: **http://localhost:8000**

### 3. Chat!

Click the purple chat button in the bottom-right corner and ask questions!

---

## Example Questions

Try these:
- "What is fiduciary duty?"
- "Explain the Revlon doctrine"
- "What is the business judgment rule?"
- "Explain the MFW framework"

---

## Two Interfaces Available

### 💬 Chat Widget (Lightweight)
```bash
./start_chat_widget.sh
# Opens at: http://localhost:8000
```
- Floating chat button
- Embeddable in any website
- REST API backend

### 🖥️ Streamlit App (Full UI)
```bash
./start_mantra.sh
# Opens at: http://localhost:8501
```
- Full dashboard interface
- Advanced filtering
- Conversation history

---

## Architecture

```
Chat Widget:
  HTML/CSS/JS ← → FastAPI ← → RAG Pipeline
                              ├─ Query Classifier
                              ├─ FAISS Search
                              └─ GPT-4 Generator

Streamlit:
  Streamlit UI ← → RAG Pipeline (same components)
```

---

## Files Created

```
mantra/
├── chat_api.py                  # FastAPI backend
├── start_chat_widget.sh         # Start chat widget
├── start_mantra.sh              # Start Streamlit app
├── static/
│   ├── index.html              # Chat widget demo page
│   └── chat-widget.js          # Chat functionality
├── mantra_app.py               # Streamlit app
└── src/mantra/                 # Shared RAG components
    ├── query_classifier.py
    ├── indexer.py
    ├── response_generator.py
    └── data_extractor.py
```

---

## Quick Test

```bash
# Test health
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is fiduciary duty?"}'
```

---

## Troubleshooting

**Port in use?**
```bash
lsof -i :8000
kill -9 <PID>
```

**Index not found?**
```bash
python3 tests/test_indexer.py
```

**Dependencies missing?**
```bash
source .venv/bin/activate
uv sync
```

---

## Next Steps

1. ✅ Test the chat widget
2. 📝 Customize colors/branding (edit `static/index.html`)
3. 🌐 Embed in your website (see `CHAT_WIDGET_GUIDE.md`)
4. 🚀 Deploy to production (see deployment section in guide)

---

## Full Documentation

- **Chat Widget Guide**: `CHAT_WIDGET_GUIDE.md` (detailed instructions)
- **Setup Guide**: `SETUP_COMPLETE.md` (initial setup)
- **Implementation**: `IMPLEMENTATION_COMPLETE.md` (technical details)
- **Quick Test**: `QUICK_TEST_GUIDE.md` (original test guide)

---

## 💡 Tips

- The chat widget is **mobile-responsive**
- Use **Ctrl+C** to stop the server
- The backend uses **same RAG logic** as Streamlit
- Both interfaces can run **simultaneously** on different ports

---

**Ready to chat? Start the server and open http://localhost:8000!** 💬⚖️
