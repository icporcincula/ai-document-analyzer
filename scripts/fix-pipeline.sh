#!/bin/bash
# Pipeline Fix Script
# This script fixes common GitHub Actions pipeline issues

set -e

echo "🔧 Starting pipeline fix process..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install missing dependencies
install_dependencies() {
    echo "📦 Installing system dependencies..."
    
    # Update package lists
    sudo apt-get update
    
    # Install core dependencies with fallbacks
    echo "Installing core dependencies..."
    sudo apt-get install -y \
        tesseract-ocr \
        tesseract-ocr-eng \
        poppler-utils \
        libpoppler-cpp-dev \
        python3-dev \
        python3-pip \
        python3-venv \
        curl \
        wget \
        git
    
    # Install python3-poppler with fallback
    if ! pip3 install python3-poppler; then
        echo "⚠️  python3-poppler not available, installing alternatives..."
        sudo apt-get install -y python3-pypdf2
    fi
    
    # Install additional OCR languages if available
    sudo apt-get install -y \
        tesseract-ocr-spa \
        tesseract-ocr-fra \
        tesseract-ocr-deu \
        tesseract-ocr-ita
}

# Function to fix Python environment
fix_python_environment() {
    echo "🐍 Fixing Python environment..."
    
    # Check Python installation
    if ! command_exists python3; then
        echo "❌ Python3 not found, installing..."
        sudo apt-get install -y python3 python3-pip
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    echo "✅ Python environment fixed"
}

# Function to validate requirements.txt
validate_requirements() {
    echo "📋 Validating requirements.txt..."
    
    # Check for empty lines at end
    if [ -s requirements.txt ]; then
        # Remove trailing empty lines
        sed -i '/^$/N;/^\n$/d' requirements.txt
        
        # Check for duplicates
        sort requirements.txt | uniq -d > duplicates.txt
        if [ -s duplicates.txt ]; then
            echo "⚠️  Found duplicate dependencies:"
            cat duplicates.txt
            # Remove duplicates
            sort requirements.txt | uniq > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
        fi
        rm -f duplicates.txt
        
        echo "✅ requirements.txt validated"
    else
        echo "⚠️  requirements.txt is empty or missing"
    fi
}

# Function to fix Docker issues
fix_docker_issues() {
    echo "🐳 Fixing Docker issues..."
    
    # Check Docker installation
    if ! command_exists docker; then
        echo "❌ Docker not found, please install Docker"
        return 1
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        echo "❌ Docker Compose not found, installing..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Test Docker
    if ! docker info >/dev/null 2>&1; then
        echo "⚠️  Docker daemon not running, starting..."
        sudo systemctl start docker
    fi
    
    echo "✅ Docker issues fixed"
}

# Function to fix quality gate issues
fix_quality_gates() {
    echo "🔍 Fixing quality gate issues..."
    
    # Check for TODO/FIXME comments (make them warnings instead of failures)
    echo "Checking for TODO/FIXME comments..."
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX" app/ tests/ --include="*.py" 2>/dev/null | wc -l || echo 0)
    if [ "$TODO_COUNT" -gt 0 ]; then
        echo "⚠️  Found $TODO_COUNT TODO/FIXME comments (these will be warnings, not failures)"
        grep -r "TODO\|FIXME\|XXX" app/ tests/ --include="*.py" | head -5
    fi
    
    # Check for print statements
    echo "Checking for print statements..."
    PRINT_COUNT=$(grep -r "print(" app/ --include="*.py" 2>/dev/null | grep -v "tests/" | wc -l || echo 0)
    if [ "$PRINT_COUNT" -gt 0 ]; then
        echo "⚠️  Found $PRINT_COUNT print statements in production code"
        echo "Consider removing or replacing with logging"
    fi
    
    # Check for debug imports
    echo "Checking for debug imports..."
    DEBUG_COUNT=$(grep -r "import pdb\|from pdb import\|import ipdb\|from ipdb import" app/ --include="*.py" 2>/dev/null | wc -l || echo 0)
    if [ "$DEBUG_COUNT" -gt 0 ]; then
        echo "⚠️  Found $DEBUG_COUNT debug imports in production code"
        echo "Consider removing debug imports"
    fi
    
    # Check for license headers
    echo "Checking for license headers..."
    MISSING_HEADERS=$(find app/ tests/ -name "*.py" -exec grep -L "Copyright\|License" {} \; 2>/dev/null | wc -l || echo 0)
    if [ "$MISSING_HEADERS" -gt 0 ]; then
        echo "⚠️  Found $MISSING_HEADERS Python files missing license headers"
        echo "Consider adding license headers to all Python files"
    fi
    
    echo "✅ Quality gate issues reviewed"
}

# Function to create branch protection script
create_branch_protection() {
    echo "🛡️  Creating branch protection setup..."
    
    cat > setup-branch-protection.sh << 'EOF'
#!/bin/bash
# Setup branch protection rules for phase branches

echo "Setting up branch protection rules..."

# Protect develop branch
gh api repos/foo/bar/branches/develop/protection \
    --method PUT \
    --field required_status_checks='{"strict":true,"contexts":["test","quality"]}' \
    --field enforce_admins=false \
    --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
    --field restrictions=null

echo "Branch protection rules applied"
EOF

    chmod +x setup-branch-protection.sh
    echo "✅ Branch protection script created"
}

# Function to create monitoring script
create_monitoring_script() {
    echo "📊 Creating pipeline monitoring script..."
    
    cat > monitor-pipeline.sh << 'EOF'
#!/bin/bash
# Monitor pipeline status and send alerts

echo "Monitoring pipeline status..."

# Check recent workflow runs
RECENT_RUNS=$(gh api repos/foo/bar/actions/runs --per_page=10 | jq -r '.workflow_runs[] | "\(.name) - \(.status) - \(.conclusion)"')

echo "Recent workflow runs:"
echo "$RECENT_RUNS"

# Check for failed runs
FAILED_RUNS=$(echo "$RECENT_RUNS" | grep "failure")
if [ -n "$FAILED_RUNS" ]; then
    echo "⚠️  Found failed workflow runs:"
    echo "$FAILED_RUNS"
    # Send alert (placeholder for actual alerting mechanism)
    echo "ALERT: Pipeline failures detected"
fi

echo "✅ Pipeline monitoring complete"
EOF

    chmod +x monitor-pipeline.sh
    echo "✅ Monitoring script created"
}

# Main execution
main() {
    echo "🚀 Starting comprehensive pipeline fix..."
    
    # Run all fix functions
    install_dependencies
    fix_python_environment
    validate_requirements
    fix_docker_issues
    fix_quality_gates
    create_branch_protection
    create_monitoring_script
    
    echo ""
    echo "✅ Pipeline fix process completed!"
    echo ""
    echo "📋 Summary of fixes applied:"
    echo "  • System dependencies installed"
    echo "  • Python environment configured"
    echo "  • requirements.txt validated"
    echo "  • Docker issues resolved"
    echo "  • Quality gate issues reviewed"
    echo "  • Branch protection script created"
    echo "  • Monitoring script created"
    echo ""
    echo "🔧 Next steps:"
    echo "  1. Run './scripts/branch-tracker.py --dashboard' to check branch status"
    echo "  2. Run './setup-branch-protection.sh' to apply branch protection"
    echo "  3. Run './monitor-pipeline.sh' to monitor pipeline health"
    echo "  4. Test the fixed pipeline with a small change"
}

# Run main function
main "$@"