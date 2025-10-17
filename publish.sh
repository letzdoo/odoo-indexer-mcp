#!/bin/bash
set -e

echo "🔨 Building package..."
rm -rf dist/ build/ *.egg-info
uv build

echo ""
echo "📦 Package built successfully!"
echo ""
echo "Files in dist/:"
ls -lh dist/

echo ""
echo "📤 Ready to publish!"
echo ""
echo "To publish to TestPyPI (recommended first):"
echo "  ~/.local/bin/twine upload --repository testpypi dist/*"
echo ""
echo "To publish to PyPI:"
echo "  ~/.local/bin/twine upload dist/*"
echo ""
echo "Or add ~/.local/bin to PATH:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  twine upload dist/*"
