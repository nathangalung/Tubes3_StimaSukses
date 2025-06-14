#!/bin/bash

# MySQL Docker Setup Script for ATS CV Search
# This script sets up MySQL in Docker and prepares the environment

echo "=== ATS CV Search MySQL Setup ==="

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "✅ Docker is available"

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "✅ Docker Compose is available"

# Stop existing containers if running
echo "🔄 Stopping existing containers..."
$COMPOSE_CMD down

# Start MySQL container
echo "🚀 Starting MySQL container..."
$COMPOSE_CMD up -d mysql

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to be ready..."
for i in {1..30}; do
    if docker exec ats_mysql mysqladmin ping -h localhost --silent; then
        echo "✅ MySQL is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ MySQL failed to start after 30 seconds"
        echo "Check logs with: $COMPOSE_CMD logs mysql"
        exit 1
    fi
    
    echo "   Attempt $i/30..."
    sleep 1
done

# Check container status
echo "📊 Container status:"
$COMPOSE_CMD ps

# Show connection info
echo ""
echo "🔗 MySQL Connection Info:"
echo "   Host: localhost"
echo "   Port: 3306"
echo "   Database: kaggle_resumes"
echo "   Username: ats_user"
echo "   Password: StimaSukses"
echo ""
echo "🛠️ Useful commands:"
echo "   📊 Status: $COMPOSE_CMD ps"
echo "   📋 Logs: $COMPOSE_CMD logs mysql"
echo "   🗄️  Connect to DB: docker exec -it ats_mysql mysql -u ats_user -p kaggle_resumes"
echo "   🛑 Stop: $COMPOSE_CMD down"
echo "   🔄 Restart: $COMPOSE_CMD restart mysql"