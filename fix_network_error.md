# 🔧 Fix NetworkError: Backend Not Running

## **Problem**
You're getting "NetworkError when attempting to fetch resource" because the backend server isn't running.

## **Solution Steps**

### **Step 1: Install Backend Dependencies**
```bash
cd /home/maf/maf/Dask/AIBI/backend

# Install Python dependencies
pip3 install --user -r requirements.txt

# If that fails, try:
python3 -m pip install --user -r requirements.txt
```

### **Step 2: Start the Backend Server**
```bash
cd /home/maf/maf/Dask/AIBI/backend

# Start the FastAPI server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅ Database tables created/verified
✅ Application startup complete
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Step 3: Verify Backend is Running**
Open a new terminal and test:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","service":"Local AI-BI Platform","version":"1.0.0"}
```

### **Step 4: Start Frontend (in separate terminal)**
```bash
cd /home/maf/maf/Dask/AIBI/frontend

# Install frontend dependencies (if needed)
npm install

# Start React development server
npm start
```

### **Step 5: Test the Complete System**
1. Backend running on http://localhost:8000
2. Frontend running on http://localhost:3000
3. Click "Start Chatting" → Should work now!

## **Troubleshooting**

### **If pip install fails:**
```bash
# Try installing with break-system-packages flag
pip3 install --user --break-system-packages -r requirements.txt
```

### **If you get "Redis not available" warnings:**
This is normal! The system falls back to in-memory storage. The conversation memory still works.

### **If you still get NetworkError:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS: Backend allows localhost:3000 ✅
3. Check frontend API URL: Should be `http://localhost:8000/api/v1/conversational/analyze` ✅

## **Expected Flow After Fix**
1. Upload CSV file ✅
2. Ask "What is the average price?" ✅
3. Get specific response: "The average price is $456.99..." ✅
4. Ask follow-up: "What about the highest price?" ✅
5. Get contextual response: "The highest price is $1999.99. Compared to the average of $456.99..." ✅

🎉 **Your sequential ChatGPT-like conversation system will work perfectly!**