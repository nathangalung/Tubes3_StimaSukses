#!/bin/bash

# MySQL Docker setup script

echo "=== ATS CV Search MySQL Setup ==="

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running"
    exit 1
fi

echo "✅ Docker available"

# Check docker-compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

echo "✅ Using: $COMPOSE_CMD"

# Start MySQL container
echo "🚀 Starting MySQL container..."
$COMPOSE_CMD up -d mysql

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL..."
sleep 10

# Check if container is running
if docker ps | grep -q "ats_mysql"; then
    echo "✅ MySQL container running"
else
    echo "❌ MySQL container failed"
    exit 1
fi

# Test connection
echo "🔍 Testing connection..."
if docker exec ats_mysql mysqladmin ping -h localhost &> /dev/null; then
    echo "✅ MySQL ready"
else
    echo "⚠️ MySQL not ready yet"
fi

# Run initialization if needed
if [ -f "tubes3_seeding.sql" ]; then
    echo "📊 Initializing database..."
    docker exec -i ats_mysql mysql -u ats_user -p"StimaSukses" kaggle_resumes < tubes3_seeding.sql
    echo "✅ Database initialized"
fi

echo ""
echo "🎯 MySQL Setup Complete!"
echo ""
echo "Connection Info:"
echo "  Host: localhost"
echo "  Port: 3306"
echo "  Database: kaggle_resumes"
echo "  User: ats_user"
echo "  Password: StimaSukses"
echo ""
echo "Useful commands:"
echo "  📊 Status: $COMPOSE_CMD ps"
echo "  📋 Logs: $COMPOSE_CMD logs mysql"
echo "  🗄️ Connect: docker exec -it ats_mysql mysql -u ats_user -p kaggle_resumes"
echo "  🛑 Stop: $COMPOSE_CMD down"
echo "  🔄 Restart: $COMPOSE_CMD restart mysql"