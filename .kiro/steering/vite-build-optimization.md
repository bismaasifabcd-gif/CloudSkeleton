---
inclusion: fileMatch
fileMatchPattern: 'vite.config.*|package.json|.*build.*'
---

# Vite Build Optimization Guidelines

## Performance Optimization

### Bundle Splitting Strategy
- Split vendor dependencies into separate chunks for better caching
- Use dynamic imports for code splitting by route or feature
- Implement proper tree shaking to eliminate dead code
- Configure chunk size limits to optimize loading performance

### Asset Optimization
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
          utils: ['lodash', 'date-fns'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
});
```

### Development Performance
- Use fast refresh for instant feedback during development
- Configure proper source maps for debugging
- Implement efficient hot module replacement (HMR)
- Optimize dependency pre-bundling for faster cold starts

## Production Build Configuration

### Environment Variables
- Use VITE_* prefix for client-side environment variables
- Keep sensitive data server-side only
- Implement proper environment-specific configurations
- Use .env files with appropriate precedence

### Security Headers
```typescript
// Configure CSP and security headers in production
server: {
  headers: {
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'",
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
  },
},
```

### Asset Management
- Enable gzip/brotli compression
- Implement proper caching strategies
- Optimize images and fonts
- Use CDN for static assets when appropriate

## Testing Integration

### Test Configuration
- Configure Vitest for unit and integration testing
- Set up proper test environments and mocking
- Implement coverage reporting and thresholds
- Use proper test file patterns and organization

### CI/CD Integration
```json
{
  "scripts": {
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest --run",
    "test:watch": "vitest",
    "test:coverage": "vitest --coverage",
    "type-check": "tsc --noEmit"
  }
}
```

## Build Analysis and Monitoring

### Bundle Analysis
- Use rollup-plugin-visualizer for bundle analysis
- Monitor bundle sizes and loading performance
- Identify and optimize large dependencies
- Track build performance over time

### Performance Metrics
- Implement Core Web Vitals monitoring
- Track bundle size changes in CI/CD
- Monitor loading performance in production
- Set up alerts for performance regressions

#[[file:frontend/vite.config.ts]]
#[[file:frontend/package.json]]