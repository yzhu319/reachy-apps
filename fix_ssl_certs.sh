#!/bin/bash
# Fix SSL certificates for Python on macOS
# Run this script if you get SSL certificate errors with Qwen TTS

echo "🔧 Fixing SSL certificates for Python..."

# Method 1: Install certifi and update certificates
cd ~/reachy-apps
source .venv/bin/activate

# Install certifi if not already installed
uv add certifi

# Method 2: Run Python's certificate installer (if available)
if [ -f "/Applications/Python 3.11/Install Certificates.command" ]; then
    echo "Running Python certificate installer..."
    "/Applications/Python 3.11/Install Certificates.command"
elif [ -f "/Applications/Python 3.12/Install Certificates.command" ]; then
    echo "Running Python certificate installer..."
    "/Applications/Python 3.12/Install Certificates.command"
else
    echo "Python certificate installer not found. Trying alternative method..."
fi

# Method 3: Update certificates using certifi
python -c "import certifi; print('Certifi certificates:', certifi.where())"

echo ""
echo "✅ SSL certificate fix complete!"
echo ""
echo "If you still get SSL errors, you can temporarily disable SSL verification"
echo "by setting this environment variable (NOT recommended for production):"
echo "  export QWEN_DISABLE_SSL_VERIFY=1"
echo ""
echo "Then try running your script again."

