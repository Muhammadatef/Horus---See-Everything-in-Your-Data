#!/bin/bash

echo "🚀 Starting Local AI-BI Platform..."

# Check system requirements
check_requirements() {
    echo "📋 Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker first."
        echo "   Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose (support both v1 and v2)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Check Docker permissions
    if ! docker ps &> /dev/null; then
        echo "❌ Docker permission denied. Please run:"
        echo "   sudo usermod -aG docker $USER"
        echo "   newgrp docker"
        echo "   Then restart this script."
        exit 1
    fi
    
    # Check available memory
    total_mem=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")
    if [ "$total_mem" -lt 8 ] && [ "$total_mem" -gt 0 ]; then
        echo "⚠️  Warning: Less than 8GB RAM available. Performance may be affected."
        echo "   Current RAM: ${total_mem}GB"
    fi
    
    # Check disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        echo "⚠️  Warning: Less than 10GB disk space available."
        echo "   Available space: ${available_space}GB"
    fi
    
    echo "✅ System requirements check passed"
}

# Initialize directories
init_directories() {
    echo "📁 Creating necessary directories..."
    mkdir -p data/uploads
    mkdir -p data/processed
    mkdir -p data/samples
    mkdir -p logs
    echo "✅ Directories created"
}

# Create sample data for demo
setup_sample_data() {
    echo "📊 Setting up sample user data for demo..."
    
    # Create the CSV file you'll use for testing
    cat > data/samples/user_analytics.csv << 'EOF'
user_id,name,email,status,signup_date,last_login,plan_type,monthly_spending,region,age,gender
U001,John Smith,john.smith@email.com,active,2023-01-15,2024-01-20,premium,299.99,North America,32,male
U002,Sarah Johnson,sarah.j@email.com,active,2023-02-20,2024-01-19,basic,49.99,Europe,28,female
U003,Mike Chen,mike.chen@email.com,inactive,2023-03-10,2023-12-01,premium,199.99,Asia,35,male
U004,Emma Davis,emma.davis@email.com,active,2023-04-05,2024-01-18,basic,29.99,North America,24,female
U005,Carlos Rodriguez,carlos.r@email.com,active,2023-05-12,2024-01-17,premium,399.99,South America,41,male
U006,Lisa Wang,lisa.wang@email.com,inactive,2023-06-08,2023-11-15,basic,19.99,Asia,29,female
U007,David Brown,david.brown@email.com,active,2023-07-22,2024-01-16,premium,249.99,Europe,38,male
U008,Anna Martinez,anna.m@email.com,active,2023-08-14,2024-01-20,basic,39.99,North America,26,female
U009,Tom Wilson,tom.wilson@email.com,active,2023-09-03,2024-01-15,premium,329.99,Europe,33,male
U010,Jennifer Lee,jennifer.lee@email.com,inactive,2023-10-11,2023-10-25,basic,9.99,Asia,31,female
U011,Robert Garcia,robert.g@email.com,active,2023-11-07,2024-01-14,premium,459.99,North America,45,male
U012,Maria Gonzalez,maria.g@email.com,active,2023-12-01,2024-01-19,basic,59.99,South America,27,female
U013,Alex Kim,alex.kim@email.com,active,2024-01-02,2024-01-18,premium,199.99,Asia,30,male
U014,Sophie Turner,sophie.t@email.com,active,2024-01-08,2024-01-17,basic,79.99,Europe,25,female
U015,James Anderson,james.a@email.com,inactive,2022-08-15,2023-08-20,premium,99.99,North America,39,male
U016,Rachel Green,rachel.g@email.com,active,2024-01-10,2024-01-16,basic,49.99,North America,22,female
U017,Luis Silva,luis.silva@email.com,active,2023-05-20,2024-01-15,premium,379.99,South America,36,male
U018,Nina Patel,nina.patel@email.com,active,2023-07-18,2024-01-14,basic,69.99,Asia,34,female
U019,Mark Thompson,mark.t@email.com,active,2023-09-25,2024-01-20,premium,289.99,Europe,40,male
U020,Isabella Lopez,isabella.l@email.com,inactive,2023-04-12,2023-09-10,basic,19.99,South America,23,female
EOF
    
    echo "✅ Sample data created: data/samples/user_analytics.csv"
    echo "   📈 Contains 20 users (15 active, 5 inactive) for testing queries like:"
    echo "   💬 'How many active users do we have?'"
    echo "   💬 'Show me user distribution by region'"
    echo "   💬 'What's our average monthly spending?'"
}

# Start services
start_services() {
    echo "🐳 Starting Docker services..."
    
    # Pull latest images
    echo "📥 Pulling Docker images..."
    $COMPOSE_CMD pull
    
    # Start services
    echo "🏗️  Building and starting services..."
    $COMPOSE_CMD up -d --build
    
    echo "⏳ Waiting for services to be ready..."
    
    # Wait for database
    echo "🗄️  Waiting for database..."
    timeout 60s bash -c 'until docker exec aibi-postgres pg_isready -U aibi_user -d aibi; do sleep 2; done'
    
    # Wait for backend
    echo "🔧 Waiting for backend API..."
    timeout 60s bash -c 'until curl -f http://localhost:8000/health &>/dev/null; do sleep 2; done'
    
    # Wait for frontend
    echo "🌐 Waiting for frontend..."
    timeout 60s bash -c 'until curl -f http://localhost:3000 &>/dev/null; do sleep 2; done'
}

# Setup LLM models for natural language queries
setup_llm_models() {
    echo "🤖 Setting up AI models for natural language queries..."
    
    echo "📥 Downloading Llama 2 7B Chat (this may take several minutes)..."
    docker exec aibi-ollama ollama pull llama2:7b-chat
    
    echo "📥 Downloading CodeLlama 7B for SQL generation..."
    docker exec aibi-ollama ollama pull codellama:7b
    
    echo "✅ AI models ready for natural language queries"
}

# Show status and demo instructions
show_status() {
    echo ""
    echo "🎉 Local AI-BI Platform is ready!"
    echo ""
    echo "📊 Access your platform:"
    echo "   • Main Application: http://localhost:3000"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo "   • File Storage Admin: http://localhost:9001"
    echo "   • Database: localhost:5432 (aibi/aibi_user)"
    echo ""
    echo "🧪 Demo Instructions:"
    echo "   1. Open http://localhost:3000 in your browser"
    echo "   2. Upload: data/samples/user_analytics.csv"
    echo "   3. Ask: 'How many active users do we have?'"
    echo "   4. Expected: '15 active users' + visualization"
    echo ""
    echo "📁 Other sample queries to try:"
    echo "   • 'Show me user distribution by region'"
    echo "   • 'What's our average monthly spending?'"
    echo "   • 'Which users haven't logged in recently?'"
    echo ""
    echo "🔧 Useful commands:"
    echo "   • Stop platform: $COMPOSE_CMD down"
    echo "   • View logs: $COMPOSE_CMD logs -f"
    echo "   • Restart service: $COMPOSE_CMD restart [service-name]"
    echo ""
    
    # Open browser (optional)
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v open &> /dev/null; then
        open http://localhost:3000
    fi
}

# Main execution
main() {
    check_requirements
    init_directories
    setup_sample_data
    start_services
    setup_llm_models
    show_status
}

# Run main function
main "$@"