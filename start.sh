#!/bin/bash
cd "$(dirname "$0")"
echo "=== Starting REXI MVP ==="
docker compose up -d neo4j minio
echo "Waiting for services..."
sleep 8
echo "Starting backend and frontend..."
docker compose up -d backend frontend
echo ""
echo "=== REXI MVP is running ==="
echo "Frontend: http://localhost:5173"
echo "API:      http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Neo4j:    http://localhost:7474"
echo ""
docker compose logs -f
