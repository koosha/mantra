# Mantra Interface Comparison

## Two Ways to Use Mantra

---

## 💬 Chat Widget (NEW!)

### What It Looks Like

```
┌─────────────────────────────────────────┐
│  Your Website Content                   │
│                                          │
│  Lorem ipsum dolor sit amet...          │
│                                          │
│                                          │
│                                    ┌───┐│
│                                    │ 💬 ││  ← Floating button
│                                    └───┘│
└─────────────────────────────────────────┘

When clicked:

┌─────────────────────────────────────────┐
│  Your Website Content                   │
│                                          │
│  Lorem ipsum...              ┌─────────┐│
│                              │ Mantra  ││
│                              │─────────││
│                              │ Bot: Hi!││
│                              │ You: ?  ││  ← Chat window
│                              │─────────││
│                              │ [Type...││
│                              └─────────┘│
│                                    ┌───┐│
│                                    │ × ││  ← Close button
│                                    └───┘│
└─────────────────────────────────────────┘
```

### Features

✅ **Floating chat button** (bottom-right corner)
✅ **Expandable chat window** (clicks to open/close)
✅ **Embeddable** in any website
✅ **Lightweight** (pure HTML/CSS/JS)
✅ **Mobile-responsive**
✅ **Beautiful animations**
✅ **REST API backend**

### Best For

- Embedding in your website
- Modern chat experience
- Minimal interface
- Quick questions
- Mobile users

### How to Start

```bash
./start_chat_widget.sh
```

Opens at: **http://localhost:8000**

---

## 🖥️ Streamlit App (Original)

### What It Looks Like

```
┌─────────────────────────────────────────┐
│ ⚖️  Mantra - Delaware Corporate Law    │
│─────────────────────────────────────────│
│                                          │
│ Sidebar:                    Main Area:  │
│ ┌──────────┐              ┌────────────┐│
│ │ Filters  │              │ Chat       ││
│ │ Court: ▼ │              │ History    ││
│ │ Date: ▼  │              │            ││
│ │ Examples │              │ [Messages] ││
│ └──────────┘              │            ││
│                            │ [Input]    ││
│                            └────────────┘│
└─────────────────────────────────────────┘
```

### Features

✅ **Full dashboard** interface
✅ **Advanced filters** (court, date, topics)
✅ **Conversation history**
✅ **Source display** with expandable sections
✅ **Example queries**
✅ **Index status** monitoring
✅ **Rich formatting**

### Best For

- Research sessions
- Detailed analysis
- Multiple queries
- Advanced filtering
- Power users

### How to Start

```bash
./start_mantra.sh
```

Opens at: **http://localhost:8501**

---

## Side-by-Side Comparison

| Feature | Chat Widget 💬 | Streamlit App 🖥️ |
|---------|---------------|------------------|
| **Interface** | Floating button + chat | Full dashboard |
| **Port** | 8000 | 8501 |
| **Backend** | FastAPI | Streamlit |
| **Embeddable** | ✅ Yes | ❌ No |
| **Mobile-friendly** | ✅ Excellent | ⚠️ OK |
| **Filters** | Basic | Advanced |
| **History** | Current session | Full history |
| **API** | ✅ REST API | ❌ No API |
| **Customizable** | ✅ Highly | ⚠️ Limited |
| **Load time** | < 1s | ~2s |
| **Use case** | Quick chat | Research |

---

## Backend Architecture

Both interfaces use the **same RAG pipeline**:

```
┌──────────────┐
│ Chat Widget  │──┐
└──────────────┘  │
                  ├──→ ┌─────────────────┐
┌──────────────┐  │    │   RAG Pipeline  │
│ Streamlit    │──┘    ├─────────────────┤
└──────────────┘       │ Query Classifier│
                       │ FAISS Indexer   │
                       │ Response Gen.   │
                       └─────────────────┘
```

Components shared:
- `src/mantra/query_classifier.py`
- `src/mantra/indexer.py`
- `src/mantra/response_generator.py`
- `src/mantra/data_extractor.py`

---

## Running Both Simultaneously

You can run both at the same time!

**Terminal 1:**
```bash
./start_chat_widget.sh
# Running on http://localhost:8000
```

**Terminal 2:**
```bash
./start_mantra.sh
# Running on http://localhost:8501
```

Both will share the same:
- FAISS index
- OpenAI API key
- Delaware case data

---

## Choosing Which to Use

### Use Chat Widget When:
- 🌐 Embedding in a website
- 📱 Mobile-first design
- ⚡ Quick questions
- 🎨 Need custom branding
- 🔌 Want REST API access

### Use Streamlit App When:
- 🔍 Detailed research
- 📊 Need advanced filters
- 📝 Long conversation sessions
- 🎓 Teaching/demonstrations
- 💼 Internal tool for legal team

---

## Development

### Chat Widget Development
- **Edit UI**: `static/index.html`
- **Edit logic**: `static/chat-widget.js`
- **Edit API**: `chat_api.py`
- **Hot reload**: Changes require server restart

### Streamlit Development
- **Edit app**: `mantra_app.py`
- **Hot reload**: Automatic (Streamlit watches files)
- **Components**: Shared with chat widget

---

## Deployment

### Chat Widget Deployment
- Deploy FastAPI backend to any cloud service
- Serve static files via CDN
- Embed widget code in your website

### Streamlit Deployment
- Deploy to Streamlit Cloud (easiest)
- Or use Docker on any platform
- Access control with authentication

---

## Cost Comparison

Both interfaces have the **same operating costs** because they use the same backend:

**Per 1,000 queries:**
- Embeddings: ~$0.02
- GPT-4: ~$150
- **Total: ~$150/month**

**To reduce costs:**
- Use GPT-4o-mini: ~$15/month (10x cheaper)
- Cache common queries
- Batch similar questions

---

## Summary

| Aspect | Chat Widget | Streamlit |
|--------|------------|-----------|
| 🎯 **Purpose** | Embeddable chat | Research tool |
| 👥 **Audience** | Website visitors | Power users |
| 💻 **Tech** | FastAPI + Vanilla JS | Streamlit |
| 🚀 **Deployment** | Any web host | Streamlit Cloud |
| 🎨 **Customization** | High | Medium |
| 📊 **Features** | Essential | Comprehensive |

---

**Choose based on your use case - or use both!** 🎉

- **For websites**: Use the chat widget
- **For research**: Use the Streamlit app
- **For everything**: Run both and switch as needed

---

*Both interfaces are fully functional and production-ready!* ✅
