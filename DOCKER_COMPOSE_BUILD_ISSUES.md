# Docker Compose Build Issues - Fix Documentation

## Overview
The `podman-compose up -d --build` command is failing due to frontend build issues in the React/TypeScript application.

## Current Status
- **Backend (Python/FastAPI)**: ✅ Building successfully
- **Frontend (React/TypeScript)**: ❌ Failing during build process

## Root Cause Analysis

### 1. TypeScript/React JSX Runtime Issues
**Problem**: TypeScript compiler cannot find React JSX runtime
**Error Messages**:
```
This JSX tag requires the module path 'react/jsx-runtime' to exist, but none could be found
```

**Affected Files**:
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`

### 2. Missing TypeScript Configuration
**Problem**: `tsconfig.json` lacks proper React/JSX configuration
**Current Issues**:
- Missing JSX runtime configuration
- Improper module resolution settings
- React-specific compiler options not configured

### 3. Import Resolution Problems
**Problem**: Vite/Rollup cannot resolve React component imports
**Error Messages**:
```
Could not resolve "./components/MetricsDashboard" from "src/App.tsx"
```

**Status**: ✅ Already fixed by removing MetricsDashboard import

### 4. Build Process Failures
**Problem**: Frontend TypeScript compilation fails before Vite build
**Impact**: Prevents container from building successfully

## Files That Need Fixes

### 1. `frontend/tsconfig.json` (CRITICAL)
**Current State**: Missing proper React configuration
**Required Changes**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",  // CRITICAL: Add this
    "jsxImportSource": "react"  // CRITICAL: Add this
  },
  "include": ["src"]
}
```

### 2. `frontend/src/main.tsx` (NEEDS VERIFICATION)
**Current State**: JSX import issues
**Status**: May be resolved with tsconfig fix

### 3. `frontend/src/App.tsx` (NEEDS VERIFICATION)
**Current State**: JSX import issues
**Status**: May be resolved with tsconfig fix

### 4. `frontend/package.json` (NEEDS VERIFICATION)
**Current State**: Build script configuration
**Status**: Should be working correctly

## Step-by-Step Fix Plan

### Phase 1: Fix TypeScript Configuration
1. **Update `frontend/tsconfig.json`**:
   - Add proper JSX configuration
   - Ensure React-specific settings are correct
   - Fix module resolution settings

2. **Verify React Dependencies**:
   - Check that all React packages are properly installed
   - Ensure TypeScript types are available

### Phase 2: Test Frontend Build
1. **Build Frontend Only**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Check for Errors**:
   - Verify TypeScript compilation succeeds
   - Ensure Vite build completes without errors

### Phase 3: Test Full Docker Compose Build
1. **Run Full Build**:
   ```bash
   podman-compose up -d --build
   ```

2. **Verify Container Status**:
   ```bash
   podman-compose ps
   ```

3. **Check Container Logs**:
   ```bash
   podman-compose logs
   ```

## Expected Build Flow

1. **Backend Container**:
   - ✅ Python dependencies install
   - ✅ Application code copies
   - ✅ Container builds successfully

2. **Frontend Container**:
   - ❌ Currently failing at TypeScript compilation
   - ✅ Should succeed after tsconfig fix
   - ✅ Vite build should complete
   - ✅ Nginx container should start

## Troubleshooting Commands

### Check Frontend Build Issues
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run TypeScript check
npx tsc --noEmit

# Run build
npm run build
```

### Check Docker Build Issues
```bash
# Build frontend container only
podman build -f frontend/Dockerfile -t frontend-test .

# Check container logs
podman-compose logs frontend
```

### Verify Dependencies
```bash
# Check React version
npm list react

# Check TypeScript version
npm list typescript

# Check @types/react version
npm list @types/react
```

## Dependencies Status

### Required Frontend Dependencies (Should be Present)
- ✅ `react: ^18.2.0`
- ✅ `react-dom: ^18.2.0`
- ✅ `typescript: ^5.2.2`
- ✅ `@types/react: ^18.2.37`
- ✅ `@types/react-dom: ^18.2.15`
- ✅ `vite: ^4.5.0`
- ✅ `@vitejs/plugin-react: ^4.1.1`

### Build Tools (Should be Present)
- ✅ `npm` (Node.js package manager)
- ✅ `podman-compose` (Container orchestration)

## Success Criteria

After fixes are applied:
1. ✅ `podman-compose up -d --build` completes successfully
2. ✅ All containers start without errors
3. ✅ Frontend web UI is accessible at `http://localhost:3001`
4. ✅ Backend API is accessible at `http://localhost:8000`
5. ✅ No TypeScript compilation errors
6. ✅ No Vite build errors

## Notes

- The backend FastAPI application is building correctly
- The issue is isolated to the frontend React/TypeScript build process
- The main culprit is the missing JSX runtime configuration in `tsconfig.json`
- Once the TypeScript configuration is fixed, the build should complete successfully
- All previously fixed issues (npm install, missing files, import paths) should remain resolved

## Next Steps

1. Apply the `tsconfig.json` fix
2. Test the frontend build process
3. Run the full docker-compose build
4. Verify all containers are running
5. Test application functionality

---

**Last Updated**: March 10, 2026
**Status**: Issues Identified, Fixes Documented
**Next Action**: Apply TypeScript configuration fixes