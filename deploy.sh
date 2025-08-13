#!/bin/bash

# AlaeAutomates 2.0 Backend API - Quick Deployment Script
# This script helps you quickly deploy to Railway

echo "🚀 AlaeAutomates 2.0 Backend API Deployment"
echo "=========================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - AlaeAutomates 2.0 Backend API"
    echo "✅ Git repository initialized"
else
    echo "📁 Git repository already exists"
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created - please update with your values"
else
    echo "⚙️  .env file already exists"
fi

echo ""
echo "🌐 Next Steps for Railway Deployment:"
echo ""
echo "1. 📤 Push to GitHub:"
echo "   git remote add origin https://github.com/yourusername/alaeautomates-backend.git"
echo "   git push -u origin main"
echo ""
echo "2. 🚂 Deploy on Railway:"
echo "   - Go to https://railway.app"
echo "   - Click 'New Project'"
echo "   - Select 'Deploy from GitHub repo'"
echo "   - Choose your repository"
echo "   - Railway will auto-deploy!"
echo ""
echo "3. ⚙️  Set Environment Variables in Railway:"
echo "   - Go to your project settings"
echo "   - Add SECRET_KEY variable (generate a secure key)"
echo "   - Add any other custom variables from .env"
echo ""
echo "4. 🎉 Your API will be available at:"
echo "   https://your-project-name.railway.app"
echo ""
echo "💡 Pro Tips:"
echo "   - Railway free tier: 500 hours/month"
echo "   - Automatic HTTPS and custom domains"
echo "   - Real-time logs and monitoring"
echo "   - Zero config deployment"
echo ""
echo "🔗 Useful Links:"
echo "   - Railway: https://railway.app"
echo "   - Docs: https://docs.railway.app"
echo "   - Examples in README.md"

echo ""
echo "✅ Deployment setup complete!"
echo "📖 Check README.md for frontend integration examples"