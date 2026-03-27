#!/bin/bash
set -e

echo "🚀 Gary's Guide DigitalOcean Deployment"
echo "========================================"

# Detect IP if not provided
DROPLET_IP="${1:-142.93.3.242}"
echo "Deploying to: $DROPLET_IP"

# Clone or pull repo
if [ ! -d "/app/PyPack_GarysGuide" ]; then
  echo "📦 Cloning repository..."
  git clone https://github.com/atg25/GarysGuide-Scraper.git /app/PyPack_GarysGuide
  cd /app/PyPack_GarysGuide
  git checkout traceability/slot8-phase2-governance
else
  echo "📦 Pulling latest code..."
  cd /app/PyPack_GarysGuide
  git pull origin traceability/slot8-phase2-governance
fi

# Copy env template
if [ ! -f ".env.do" ]; then
  echo "⚙️  Creating .env.do from template..."
  cp .env.do.template .env.do
  echo "⚠️  Edit .env.do with your API token and run again"
  exit 1
fi

# Load env
export $(grep -v '^#' .env.do | xargs)

# Install Docker if needed
if ! command -v docker &> /dev/null; then
  echo "🐳 Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker root
fi

# Ensure Docker is running
systemctl start docker 2>/dev/null || true

# Deploy with docker-compose
echo "🚀 Starting Docker containers..."
docker-compose -f docker-compose.do.yml down 2>/dev/null || true
docker-compose -f docker-compose.do.yml up -d

# Wait for health check
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
    break
  fi
  echo "  Attempt $i/30..."
  sleep 2
done

# Final validation
echo ""
echo "✅ Deployment complete!"
echo "📍 API available at: http://$DROPLET_IP:8000"
echo "📝 Test with: curl -H 'Authorization: Bearer YOUR_TOKEN' http://$DROPLET_IP:8000/health"
