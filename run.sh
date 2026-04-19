#!/bin/bash

echo "Starting myWallet setup and run script..."

# 1. Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# 2. Run tests
echo "Running tests..."
python3 -m pytest tests/

if [ $? -eq 0 ]; then
    echo "Tests passed! Starting server..."
    # 3. Open browser in background
    (sleep 2 && echo "Opening browser at http://localhost:5000" && (xdg-open "http://localhost:5000" || open "http://localhost:5000" || echo "Please open manually")) &
    
    # 4. Start server in foreground so Ctrl+C kills it natively
    cd backend
    python3 app.py
else
    echo "Tests failed! Server will not start."
    exit 1
fi
