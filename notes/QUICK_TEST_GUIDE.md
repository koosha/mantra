# Quick Test Guide - Get Mantra Running in 5 Minutes

## Current Status
✅ `.env` file created with OpenAI API key  
🔄 Dependencies installing...

## Next Steps (After Installation Completes)

### Step 1: Extract Test Data (~30 seconds)
```bash
python test_extractor.py
```

**What this does:**
- Fetches 5 Delaware corporate law cases from CourtListener
- Saves to `./data/cases/delaware_cases.json`
- No API token needed (uses free tier)

**Expected output:**
```
Fetched 5 opinions
Processed 5 opinions
Saved to ./data/cases/delaware_cases.json
```

---

### Step 2: Build Test Index (~1-2 minutes)
```bash
python test_indexer.py
```

**What this does:**
- Chunks the 5 cases into smaller pieces
- Generates embeddings using OpenAI (uses your API key)
- Creates FAISS index in `./faiss_index_test/`
- Tests search functionality

**Expected output:**
```
Created X chunks from 5 cases
Generating embeddings...
Created FAISS index with X vectors
Test Complete!
```

**Cost:** ~$0.01 (very cheap for testing)

---

### Step 3: Run Mantra! 🚀
```bash
streamlit run mantra_app.py
```

**What happens:**
- Streamlit starts a local web server
- Browser opens automatically to `http://localhost:8501`
- You'll see the Mantra chat interface

**Note:** The app will look for `./faiss_index/` by default. Since we created `./faiss_index_test/`, you have two options:

**Option A: Rename test index (Quick)**
```bash
mv faiss_index_test faiss_index
```

**Option B: Update the app to use test index**
Edit `.env` and change:
```
FAISS_INDEX_PATH=./faiss_index_test
```

---

## Testing the App

Once Mantra is running in your browser:

### ✅ Test with Relevant Questions:
1. "What is fiduciary duty?"
2. "Explain the business judgment rule"
3. "What is the Revlon doctrine?"

**Expected:** Detailed answers with case citations

### ✅ Test with Irrelevant Questions:
1. "Who is Koosha and where does he work?"
2. "What's the weather today?"

**Expected:** Polite rejection message explaining the bot is for Delaware law only

---

## Troubleshooting

### "Index not loaded" warning
- Make sure you ran `python test_indexer.py`
- Check that `./faiss_index/` or `./faiss_index_test/` exists
- Rename test index: `mv faiss_index_test faiss_index`

### "No cases found" error
- Make sure you ran `python test_extractor.py`
- Check that `./data/cases/delaware_cases.json` exists

### OpenAI API errors
- Verify your API key in `.env` is correct
- Check you have credits in your OpenAI account
- Test with: `echo $OPENAI_API_KEY` (after `source .env`)

### Rate limiting from CourtListener
- Normal for free tier
- Wait 1 minute between requests
- Or add `COURTLISTENER_API_TOKEN` to `.env`

---

## Full Production Setup (Later)

Once you've tested and everything works:

### 1. Extract All Cases
```bash
python data_extractor.py
```
- Takes 10-30 minutes
- Fetches 2,000-5,000 Delaware cases

### 2. Build Full Index
```bash
python indexer.py
```
- Takes 5-15 minutes
- Cost: ~$0.33 for embeddings

### 3. Run Production App
```bash
streamlit run mantra_app.py
```

---

## Quick Commands Summary

```bash
# 1. Install (if not done)
pip install -r requirements.txt

# 2. Get test data
python test_extractor.py

# 3. Build test index
python test_indexer.py

# 4. Rename for app
mv faiss_index_test faiss_index

# 5. Run Mantra
streamlit run mantra_app.py
```

---

## What to Expect

### First Query (~5-10 seconds)
- Loads the index
- Generates query embedding
- Searches FAISS
- Calls GPT-4
- Formats response

### Subsequent Queries (~2-5 seconds)
- Index already loaded
- Faster responses

### Cost Per Query
- Embedding: ~$0.00002
- GPT-4: ~$0.15
- **Total: ~$0.15 per query**

---

## Next Steps After Testing

1. ✅ Verify the app works with test data
2. 📥 Extract full dataset (`python data_extractor.py`)
3. 🔨 Build full index (`python indexer.py`)
4. 🚀 Use Mantra for real Delaware law questions!

---

**Need Help?**
- Check `README.md` for full documentation
- Review `IMPLEMENTATION_COMPLETE.md` for architecture details
- See `FAISS_IMPLEMENTATION.md` for FAISS specifics
