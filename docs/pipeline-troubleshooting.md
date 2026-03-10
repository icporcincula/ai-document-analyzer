# GitHub Actions Pipeline Troubleshooting Guide

This guide helps you understand and fix common issues with the GitHub Actions pipeline when merging phase implementation branches.

## Overview

The pipeline consists of three main workflows:
- **test.yml**: Runs unit tests, linting, and type checking
- **quality.yml**: Enforces code quality standards
- **docker.yml**: Builds and tests Docker images

## Common Issues and Solutions

### 1. Python Environment Issues

**Symptoms:**
- `python: command not found`
- `did not find executable at 'C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe'`
- Import errors in tests

**Solutions:**
```bash
# Run the pipeline fix script
./scripts/fix-pipeline.sh

# Or manually fix Python environment
sudo apt-get install python3 python3-pip
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

### 2. Missing System Dependencies

**Symptoms:**
- Tesseract OCR not found
- Poppler utilities missing
- PDF processing failures

**Solutions:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  poppler-utils \
  libpoppler-cpp-dev \
  python3-dev
```

### 3. Quality Gate Failures

**Symptoms:**
- TODO/FIXME comments causing failures
- Print statements in production code
- Missing license headers
- Duplicate dependencies in requirements.txt

**Solutions:**
- **TODO/FIXME comments**: These are now warnings, not failures
- **Print statements**: Replace with proper logging
- **License headers**: Add to all Python files
- **Duplicate dependencies**: Remove duplicates from requirements.txt

### 4. Docker Build Issues

**Symptoms:**
- Multi-platform build failures
- Container startup timeouts
- Service dependency issues

**Solutions:**
- Simplified to single platform (linux/amd64) builds
- Added retry logic for service startup
- Improved error handling for missing Docker Compose files

### 5. Branch Merge Conflicts

**Symptoms:**
- Merge conflicts when merging phase branches
- Pipeline failures after merges
- Missing dependencies between phases

**Solutions:**
- Use the branch tracker to check merge readiness
- Ensure all phase branches are up to date with develop
- Test merges in feature branches first

## Monitoring and Prevention

### Using the Branch Tracker

```bash
# Check all branch status
./scripts/branch-tracker.py --dashboard

# Check specific branch
./scripts/branch-tracker.py --check-branch phase_4_implementation

# Check merge readiness
./scripts/branch-tracker.py --merge-ready phase_4_implementation

# Save status report
./scripts/branch-tracker.py --save --dashboard
```

### Pipeline Health Monitoring

```bash
# Generate health report
python scripts/setup-monitoring.py \
  --repo-owner your-username \
  --repo-name your-repo \
  --token your-github-token \
  --save health-report.json

# Send alerts for issues
python scripts/setup-monitoring.py \
  --repo-owner your-username \
  --repo-name your-repo \
  --alert \
  --recipients you@example.com
```

### Pre-Merge Checklist

Before merging any phase implementation branch:

1. **Run branch tracker check:**
   ```bash
   ./scripts/branch-tracker.py --merge-ready [branch-name]
   ```

2. **Check pipeline health:**
   ```bash
   python scripts/setup-monitoring.py --repo-owner [owner] --repo-name [repo]
   ```

3. **Fix any identified issues:**
   ```bash
   ./scripts/fix-pipeline.sh
   ```

4. **Test locally:**
   ```bash
   # Test Python environment
   python -c "import app; print('Python environment OK')"
   
   # Test dependencies
   pip install -r requirements.txt
   
   # Run tests
   pytest tests/ -v
   ```

## Emergency Recovery

### If Pipeline is Completely Broken

1. **Stop all current workflows:**
   - Go to GitHub Actions tab
   - Cancel any running workflows
   - Delete failed workflow runs

2. **Fix the pipeline:**
   ```bash
   # Run comprehensive fix
   ./scripts/fix-pipeline.sh
   
   # Check health
   python scripts/setup-monitoring.py --repo-owner [owner] --repo-name [repo]
   ```

3. **Test with a small change:**
   - Create a test branch
   - Make a small, safe change (like updating a comment)
   - Push and verify pipeline passes
   - Merge test branch to develop

4. **Resume normal operations:**
   - Once test passes, proceed with phase branch merges
   - Monitor pipeline closely

### If Specific Phase Branch is Problematic

1. **Isolate the issue:**
   ```bash
   # Check branch status
   ./scripts/branch-tracker.py --check-branch [problematic-branch]
   ```

2. **Create a fix branch:**
   ```bash
   git checkout [problematic-branch]
   git checkout -b [problematic-branch]-fix
   ```

3. **Apply fixes:**
   - Fix any dependency issues
   - Resolve quality gate failures
   - Update requirements.txt if needed

4. **Test the fix:**
   - Push to remote
   - Verify pipeline passes
   - Merge fix branch back to problematic branch

5. **Retry merge:**
   - Once fixed, retry merging to develop
   - Monitor pipeline closely

## Best Practices

### For Phase Implementation Branches

1. **Keep branches up to date:**
   ```bash
   git checkout [branch-name]
   git fetch origin
   git rebase origin/develop
   ```

2. **Test before merging:**
   - Run local tests
   - Check branch tracker status
   - Verify no conflicts with develop

3. **Follow quality standards:**
   - No TODO/FIXME comments in production code
   - No print statements
   - Proper license headers
   - Clean requirements.txt

### For Pipeline Maintenance

1. **Regular monitoring:**
   - Run health checks weekly
   - Monitor for dependency updates
   - Check for new quality gate requirements

2. **Documentation:**
   - Update this guide with new issues and solutions
   - Document any custom pipeline configurations
   - Keep troubleshooting steps current

3. **Team communication:**
   - Share pipeline status updates
   - Coordinate phase branch merges
   - Establish clear escalation procedures

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the logs:**
   - GitHub Actions workflow logs
   - Local test output
   - Branch tracker reports

2. **Use monitoring tools:**
   ```bash
   # Generate detailed health report
   python scripts/setup-monitoring.py --repo-owner [owner] --repo-name [repo] --save detailed-report.json
   ```

3. **Escalate if needed:**
   - Contact the development team
   - Create an issue in the repository
   - Use the alert system for critical issues

## Quick Reference

| Issue | Command | Solution |
|-------|---------|----------|
| Python not found | `./scripts/fix-pipeline.sh` | Installs Python and fixes environment |
| Missing dependencies | `sudo apt-get install [packages]` | Installs system dependencies |
| Quality gate failures | `./scripts/branch-tracker.py --check-branch [branch]` | Identifies specific issues |
| Docker issues | Check docker.yml fixes | Simplified builds and better error handling |
| Branch conflicts | `./scripts/branch-tracker.py --merge-ready [branch]` | Checks merge readiness |

Remember: Always test changes in a safe environment before applying them to the main pipeline!