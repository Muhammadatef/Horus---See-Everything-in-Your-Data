# 🔺 Horus - The All-Seeing Eye of Business Intelligence

*Divine insights from your data, running entirely on your local machine*

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Local](https://img.shields.io/badge/deployment-local--only-orange.svg)

## 📖 Overview

**Horus** is an intelligent, plug-and-play data platform that runs entirely on your local PC. Upload any data format, ask questions in plain English, and get instant insights with beautiful visualizations - all without sending your data to the cloud.

### 🎯 Core Value Proposition

**"Upload your data, ask questions in plain English, get divine insights"**

- ✅ **100% Local & Offline** - Your data never leaves your machine
- ✅ **Zero Cloud Dependencies** - No API costs or internet required
- ✅ **Universal Data Support** - CSV, Excel, JSON, Parquet, XML, and more
- ✅ **Natural Language Queries** - Ask questions like "What are our top customers?"
- ✅ **Instant Visualizations** - Auto-generated charts and dashboards
- ✅ **Real-time Processing** - Live updates as your data is analyzed
- ✅ **Domain Intelligence** - Adapts to any business domain (telecom, healthcare, finance, etc.)

## 🏗️ Architecture

### The All-Seeing Eye Stack
```
┌─────────────────────────────────────────────────────────────┐
│                    🔺 HORUS PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│  React Frontend  │  Real-time UI with Material Design      │
│  FastAPI Backend │  Python async API with WebSocket        │
│  PostgreSQL      │  Analytical database for insights       │
│  Redis           │  Caching and session management          │
│  MinIO           │  Local S3-compatible file storage        │
│  Ollama + LLMs   │  Local AI: Llama2, CodeLlama, Mistral  │
│  Apache ECharts  │  Beautiful, interactive visualizations  │
└─────────────────────────────────────────────────────────────┘
```

### 🛠️ Complete Tech Stack

**Backend Services:**
- **FastAPI** - Modern Python async web framework
- **PostgreSQL** - Robust analytical database
- **Redis** - High-performance caching
- **MinIO** - S3-compatible local object storage
- **Ollama** - Local LLM inference engine

**AI & Analytics:**
- **Llama2 7B** - Natural language understanding
- **CodeLlama 7B** - SQL generation from plain English
- **Pandas** - Data manipulation and analysis
- **SQLAlchemy** - Database ORM with async support
- **Great Expectations** - Data quality validation

**Frontend:**
- **React 18** - Modern UI framework
- **TypeScript** - Type-safe development
- **Material-UI** - Professional component library
- **Apache ECharts** - Interactive visualizations
- **WebSocket** - Real-time updates

**Infrastructure:**
- **Docker Compose** - One-command deployment
- **Apache Airflow** - Workflow orchestration
- **NGINX** - Production web server (optional)

## 🚀 Quick Start

### Prerequisites
```bash
# System Requirements
- RAM: 8GB minimum (16GB recommended)
- Storage: 50GB free space (100GB for optimal performance)
- CPU: 4 cores minimum (8+ cores recommended)
- Docker: Latest version installed
```

### One-Command Installation

```bash
# Clone the repository
git clone https://github.com/your-org/horus-ai-bi.git
cd horus-ai-bi

# Start the complete platform
./start-horus.sh

# That's it! 🎉
# Open http://localhost:3000 in your browser
```

### Manual Installation

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services to initialize (2-3 minutes)
docker-compose logs -f

# 3. Initialize sample data (optional)
docker-compose exec backend python scripts/init_sample_data.py

# 4. Access the platform
open http://localhost:3000
```

## 📊 How to Use Horus

### 1. Upload Your Data
- **Drag & Drop**: Simply drag any supported file into the upload area
- **Supported Formats**: CSV, Excel (.xls/.xlsx), JSON, Parquet, XML, TSV
- **Real-time Processing**: Watch as Horus analyzes your data structure
- **Intelligent Cleaning**: Automatic data type detection and cleaning

### 2. Ask Questions in Plain English
```
Examples:
• "What are our top 10 customers by revenue?"
• "Show me sales trends over the last 6 months"
• "Which products have the highest profit margins?"
• "Compare performance between different regions"
• "What's the average customer lifetime value?"
```

### 3. Get Instant Insights
- **Smart Visualizations**: Auto-selected charts based on your question
- **Business Answers**: Natural language explanations of results
- **Interactive Dashboards**: Drill down into your data
- **Export Options**: Save charts and reports

### 4. Domain Intelligence
Horus automatically adapts to your business domain:

**Telecom Data**: Recognizes customer usage, network metrics, billing patterns
**Healthcare**: Understands patient records, treatments, outcomes
**Retail**: Identifies sales patterns, inventory, customer behavior
**Finance**: Analyzes transactions, risk metrics, performance indicators

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://aibi_user:local_password@postgres:5432/aibi

# AI Models
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL_CHAT=llama2:7b-chat
OLLAMA_MODEL_CODE=codellama:7b

# Storage
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# File Limits
MAX_UPLOAD_SIZE=100MB
ALLOWED_FILE_TYPES=csv,xlsx,json,parquet,xml,tsv
```

### Resource Optimization
```yaml
# For 8GB RAM systems
ollama:
  environment:
    - OLLAMA_NUM_PARALLEL=1
    - OLLAMA_MAX_LOADED_MODELS=1

# For 16GB+ RAM systems  
ollama:
  environment:
    - OLLAMA_NUM_PARALLEL=2
    - OLLAMA_MAX_LOADED_MODELS=2
```

## 📁 Project Structure

```
horus-ai-bi/
├── 🐳 docker-compose.yml              # Complete service orchestration
├── 🚀 start-horus.sh                  # One-click startup script
├── 📚 README.md                       # This file
├── 📄 CLAUDE.md                       # Project instructions
│
├── 🔧 backend/                        # FastAPI Backend
│   ├── app/
│   │   ├── 🌐 api/v1/endpoints/       # REST API endpoints
│   │   ├── ⚙️ services/               # Core business logic
│   │   │   ├── enhanced_data_ingestion.py    # Smart data processing
│   │   │   ├── enhanced_llm_service.py       # AI query understanding
│   │   │   ├── enhanced_query_processor.py   # Natural language queries
│   │   │   ├── visualization_engine.py       # Auto-chart generation
│   │   │   └── websocket_manager.py          # Real-time updates
│   │   ├── 📊 models/                 # Database models
│   │   ├── 🔧 utils/                  # Helper functions
│   │   └── ⚡ config.py               # Configuration settings
│   ├── 🐳 Dockerfile
│   └── 📋 requirements.txt
│
├── 🎨 frontend/                       # React Frontend
│   ├── src/
│   │   ├── 🧩 components/             # UI components
│   │   │   ├── upload/                # Data upload interface
│   │   │   ├── query/                 # Query interface
│   │   │   ├── visualization/         # Chart components
│   │   │   └── common/                # Shared components
│   │   ├── 🔧 services/               # API clients
│   │   ├── 🎣 hooks/                  # React hooks
│   │   └── 🛠️ utils/                  # Helper functions
│   ├── 🐳 Dockerfile
│   └── 📦 package.json
│
├── 🌊 airflow/                        # Workflow Orchestration
│   ├── dags/                          # Data processing workflows
│   └── config/
│
├── 💾 data/                           # Local Data Storage
│   ├── uploads/                       # User uploaded files
│   ├── processed/                     # Cleaned data
│   └── samples/                       # Sample datasets
│
└── 📖 docs/                           # Documentation
    ├── user-guide.md
    ├── api-docs.md
    └── troubleshooting.md
```

## 🌟 Key Features

### 🧠 Intelligent Data Understanding
- **Auto-Detection**: Recognizes file formats and data types
- **Smart Cleaning**: Handles missing values and inconsistencies  
- **Schema Generation**: Creates business-friendly descriptions
- **Sample Questions**: Suggests relevant queries for your data

### 💬 Natural Language Processing
- **Business Intent**: Understands what you really want to know
- **Context Awareness**: Learns your domain vocabulary
- **SQL Generation**: Converts questions to optimized queries
- **Multi-Language**: Support for business terminology

### 📊 Advanced Visualizations
- **Auto-Selection**: Chooses the best chart for your data
- **Interactive Charts**: Zoom, filter, and drill-down capabilities
- **Multiple Types**: Bar, line, pie, scatter, histogram, and more
- **Export Ready**: High-quality exports for presentations

### ⚡ Real-Time Experience
- **Live Updates**: See processing status in real-time
- **WebSocket**: Instant feedback during data analysis
- **Progress Tracking**: Know exactly what's happening
- **Error Handling**: Clear messages if something goes wrong

## 🎯 Use Cases

### 📈 Small Business Analytics
```
Scenario: Local retail store with sales data
Questions: "Which products sell best on weekends?"
Result: Instant insights without hiring a data analyst
```

### 🏥 Healthcare Research
```
Scenario: Medical research with patient data
Questions: "What factors correlate with treatment success?"
Result: Statistical analysis with publication-ready charts
```

### 📱 Telecom Operations
```
Scenario: Network performance and customer usage data
Questions: "Which cell towers have the highest data usage?"
Result: Network optimization insights and usage patterns
```

### 💼 Consulting Projects
```
Scenario: Client data analysis for recommendations
Questions: "What's driving customer churn in region X?"
Result: Professional client reports in minutes
```

## 🔒 Privacy & Security

### Data Protection
- **Local Processing**: Data never leaves your machine
- **No Cloud APIs**: Zero external dependencies
- **Encrypted Storage**: Local data encryption at rest
- **Access Control**: User session management

### Compliance Ready
- **GDPR Compliant**: Data sovereignty maintained
- **HIPAA Compatible**: Healthcare data stays local
- **SOX Friendly**: Financial data never exposed
- **Custom Policies**: Implement your own security rules

## 🆘 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker status
docker ps
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

**LLM models not loading:**
```bash
# Check Ollama status
docker-compose exec ollama ollama list

# Pull required models
docker-compose exec ollama ollama pull llama2:7b-chat
docker-compose exec ollama ollama pull codellama:7b
```

**Frontend connection issues:**
```bash
# Check backend API
curl http://localhost:8000/api/v1/health

# Check CORS settings in backend/app/config.py
```

### Performance Optimization

**For Low Memory Systems (8GB):**
- Use smaller models: `llama2:7b-q4_0` instead of `llama2:7b-chat`
- Limit concurrent connections in docker-compose.yml
- Increase swap space on your system

**For High Performance (32GB+):**
- Use larger models: `llama2:13b-chat`
- Enable GPU acceleration if available
- Increase worker processes

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/CONTRIBUTING.md) for details.

### Development Setup
```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development  
cd frontend
npm install
npm start
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **API Reference**: [localhost:8000/docs](http://localhost:8000/docs) (when running)
- **Issue Tracker**: [GitHub Issues](https://github.com/your-org/horus-ai-bi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/horus-ai-bi/discussions)

## 🙏 Acknowledgments

- **Ollama Team** - Local LLM inference
- **FastAPI** - Modern Python web framework
- **Apache ECharts** - Beautiful visualizations
- **Material-UI** - Professional React components
- **PostgreSQL** - Robust database engine

---

<div align="center">

**🔺 Horus - The All-Seeing Eye of Business Intelligence**

*Built with ❤️ for data privacy and local intelligence*

[⭐ Star us on GitHub](https://github.com/your-org/horus-ai-bi) | [📖 Read the Docs](docs/) | [💬 Join Discussions](https://github.com/your-org/horus-ai-bi/discussions)

</div>