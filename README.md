# Local AI-BI Platform

**Upload your data, ask questions in plain English, get instant insights**

A complete local Business Intelligence platform that runs entirely on your machine with no cloud dependencies. Upload any data format (CSV, Excel, JSON, Parquet) and query it using natural language powered by local AI models.

## 🚀 Quick Start

### One-Command Setup
```bash
# Clone and start everything
git clone <your-repo-url>
cd local-ai-bi
./start-local.sh
```

**What the startup script does:**
1. ✅ Checks system requirements
2. 📥 Downloads required Docker images
3. 🤖 Downloads LLM models (Llama 2, CodeLlama)
4. 🏗️ Starts all services
5. 📊 Sets up sample data
6. 🌐 Opens browser to http://localhost:3000

### System Requirements
- **Minimum**: 8GB RAM, 4 cores, 50GB free space
- **Recommended**: 16GB+ RAM, 8 cores, 100GB SSD
- **Docker**: Latest version installed

## 🎯 Demo Walkthrough

1. **Start the platform**: `./start-local.sh`
2. **Open**: http://localhost:3000
3. **Upload**: `data/samples/user_analytics.csv`
4. **Ask**: *"How many active users do we have?"*
5. **Get**: *"**15 active users**"* + beautiful pie chart visualization

### Sample Questions to Try
- "How many active users do we have?"
- "Show me user distribution by region" 
- "What's our average monthly spending?"
- "How many premium users are there?"

## 🏗️ Architecture

### Complete Local Stack
```yaml
Services:
  - PostgreSQL: Local analytical database
  - Redis: Caching and session management  
  - MinIO: Local file storage (S3-compatible)
  - Ollama: Local LLM (Llama 2, CodeLlama)
  - FastAPI: Python backend service
  - React: Frontend interface
  - Apache ECharts: Visualization library
```

### Data Flow
1. **Upload** → File stored in MinIO → Auto-processed → PostgreSQL
2. **Query** → Natural language → Ollama LLM → SQL generation → Execute → Visualize

## 🔧 Development

### Daily Commands
```bash
# Start platform
./start-local.sh

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop platform  
./stop-local.sh
```

### API Endpoints
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **File Admin**: http://localhost:9001

## 📁 Project Structure

```
local-ai-bi/
├── docker-compose.yml          # All services definition
├── start-local.sh             # One-click startup
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── services/         # Core business logic
│   │   ├── models/           # Data models
│   │   └── utils/            # Helper functions
│   └── requirements.txt
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── services/         # API clients
│   │   └── hooks/            # React hooks
│   └── package.json
├── data/                      # Local data storage
│   ├── uploads/              # User uploaded files
│   ├── processed/            # Cleaned data
│   └── samples/              # Sample datasets
└── docs/                      # Documentation
```

## ✨ Features

### Universal Data Ingestion
- **Drag & Drop Upload**: CSV, Excel, JSON, Parquet support
- **Auto-Detection**: File format and delimiter detection
- **Smart Cleaning**: Removes duplicates, handles missing values
- **Schema Intelligence**: Generates business-friendly descriptions

### Natural Language Queries
- **Local LLM**: Powered by Ollama (Llama 2, CodeLlama)
- **SQL Generation**: Converts questions to optimized queries
- **Context Aware**: Understands your data schema
- **Safe Execution**: Prevents dangerous operations

### Instant Visualizations
- **Auto-Charts**: Intelligently selects best chart type
- **Interactive**: Built with Apache ECharts
- **Multiple Types**: Pie, bar, line, scatter, metric cards
- **Export Ready**: PNG, PDF, Excel formats

### Complete Privacy
- **Offline First**: Works without internet connection
- **Local Storage**: Data never leaves your machine
- **No Cloud Costs**: Zero ongoing fees
- **Full Control**: Customize and modify as needed

## 🎛️ Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://aibi_user:local_password@postgres:5432/aibi
OLLAMA_URL=http://ollama:11434
MAX_UPLOAD_SIZE=100MB

# Frontend  
REACT_APP_API_URL=http://localhost:8000
```

### Docker Compose Services
- **postgres**: Database (port 5432)
- **redis**: Cache (port 6379)  
- **minio**: File storage (ports 9000, 9001)
- **ollama**: LLM service (port 11434)
- **backend**: API server (port 8000)
- **frontend**: Web interface (port 3000)

## 🚨 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
lsof -i :3000
kill -9 [PID]
```

**Docker out of space:**
```bash
docker system prune -a --volumes
```

**Services not starting:**
```bash
docker-compose logs [service-name]
docker-compose restart [service-name]
```

**LLM not responding:**
```bash
docker exec aibi-ollama ollama list
docker exec aibi-ollama ollama pull llama2:7b-chat
```

## 📊 Success Metrics

### Performance Goals
- ⏱️ **Startup Time**: Platform ready in < 2 minutes
- 🚀 **Query Speed**: < 5 seconds for simple queries
- 📁 **File Support**: Up to 100MB uploads
- 💾 **Resource Usage**: < 4GB total memory

### User Experience
- ⚡ **Time to Insight**: < 3 minutes from upload to visualization
- 🎯 **Query Accuracy**: > 90% natural language success rate
- 📊 **Auto-Visualization**: Appropriate charts generated automatically
- 👥 **Learning Curve**: Non-technical users productive in < 30 minutes

## 🎯 Target Use Cases

- **Small Businesses**: Sensitive data analysis without cloud costs
- **Consultants**: Portable BI for client work  
- **Researchers**: Academic/scientific data analysis
- **Enterprises**: Proof-of-concept before cloud deployment
- **Regulated Industries**: Healthcare, finance with strict data policies

## 🔮 Roadmap

- [ ] **Dashboard Builder**: Save and organize visualizations
- [ ] **Advanced Analytics**: Statistical analysis, forecasting
- [ ] **Data Connections**: Direct database connections
- [ ] **Collaboration**: Share insights and reports
- [ ] **Mobile Support**: Responsive design for tablets
- [ ] **Plugin System**: Custom data sources and visualizations

---

**Built with ❤️ for complete data privacy and local control**