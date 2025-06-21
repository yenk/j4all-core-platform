#!/bin/bash

# Generate requirements.txt from current virtual environment
echo "📦 Generating requirements.txt from virtual environment..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Not in a virtual environment. Please activate your venv first."
    echo "   Run: source venv/bin/activate.fish"
    exit 1
fi

# Generate requirements.txt
pip freeze > requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ requirements.txt generated successfully!"
    echo "📄 Generated file contains $(wc -l < requirements.txt) dependencies"
    echo "💡 Note: This includes all installed packages. For production, consider using poetry export."
else
    echo "❌ Failed to generate requirements.txt"
    exit 1
fi 