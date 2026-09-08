---
inclusion: auto
---

# React TypeScript Development Conventions

## Component Development Standards

### Component Structure
- Use functional components with TypeScript interfaces for props
- Implement proper prop validation and default values
- Use React.memo for components with expensive renders or frequent re-renders
- Organize components by feature in dedicated directories

### TypeScript Best Practices
- Define explicit interfaces for all component props and state
- Use union types for component variants and states  
- Implement proper type guards for runtime type checking
- Avoid `any` type - use `unknown` or specific types instead
- Use generic types for reusable component patterns

### State Management
- Use useState for local component state
- Use useReducer for complex state logic with multiple sub-values
- Implement custom hooks for shared stateful logic
- Use useCallback and useMemo for performance optimization
- Avoid prop drilling - lift state up or use context when appropriate

## Styling and Design System

### Tailwind CSS Usage
- Use utility-first approach with Tailwind classes
- Create reusable component variants using CSS-in-JS patterns
- Implement consistent spacing scale (4px base unit)
- Use semantic color names (primary, secondary, accent, etc.)
- Implement proper responsive design with mobile-first approach

### Dark Mode Implementation
- Use CSS custom properties for theme-aware colors
- Implement theme switching with proper persistence
- Test all components in both light and dark modes
- Use proper contrast ratios for accessibility compliance

## API Integration Patterns

### HTTP Client Setup
- Use fetch with proper error handling and type safety
- Implement request/response interceptors for common patterns
- Use AbortController for request cancellation
- Implement proper loading states and error boundaries

### Data Fetching
- Use custom hooks for API interactions
- Implement proper loading, error, and success states
- Use optimistic updates for improved user experience
- Cache API responses when appropriate to reduce network requests

## Performance Optimization

### Rendering Optimization
- Use React.memo for components that receive stable props
- Implement useMemo for expensive calculations
- Use useCallback for stable function references
- Avoid creating objects and arrays in render methods

### Bundle Optimization  
- Use dynamic imports for code splitting
- Implement lazy loading for routes and heavy components
- Optimize images and static assets
- Use proper tree shaking for unused code elimination

### Monitoring and Debugging
- Use React DevTools for component inspection and profiling
- Implement error boundaries for graceful error handling
- Use console.warn for development-only debugging
- Implement proper logging for user interactions and errors

## Testing Conventions

### Unit Testing
- Test component behavior, not implementation details
- Use React Testing Library for DOM interaction testing
- Mock external dependencies and API calls
- Test error states and edge cases

### Integration Testing
- Test complete user workflows and interactions
- Use Mock Service Worker for API mocking
- Test responsive design and accessibility features
- Implement visual regression testing for UI consistency

## Accessibility Standards

### ARIA Implementation
- Use semantic HTML elements as the foundation
- Implement proper ARIA labels and roles when needed
- Use ARIA live regions for dynamic content updates
- Test with screen readers and keyboard navigation

### Keyboard Navigation
- Implement proper tab order for interactive elements
- Use focus management for modal dialogs and navigation
- Provide keyboard shortcuts for common actions
- Test all functionality without mouse interaction

### Visual Design
- Maintain proper color contrast ratios (WCAG AA compliance)
- Implement responsive design for various screen sizes
- Use relative units (rem, em) for scalable typography
- Provide alternative text for images and visual elements

## File Organization

### Component Structure
```typescript
// ComponentName.tsx
interface ComponentNameProps {
  // Props interface
}

export const ComponentName: React.FC<ComponentNameProps> = ({ 
  // Destructured props
}) => {
  // Hooks and state
  // Event handlers  
  // Render logic
}

export default ComponentName;
```

### Custom Hook Pattern
```typescript
// hooks/useFeatureName.ts
interface UseFeatureNameResult {
  // Return type interface
}

export const useFeatureName = (params: FeatureParams): UseFeatureNameResult => {
  // Hook implementation
  return {
    // Returned values
  }
}
```

### API Client Pattern
```typescript
// lib/api/featureApi.ts
export const featureApi = {
  async getItems(): Promise<Item[]> {
    // API implementation
  },
  
  async createItem(item: CreateItemRequest): Promise<Item> {
    // API implementation
  }
}
```

#[[file:frontend/src/App.tsx]]
#[[file:frontend/src/components/diagram/ArchitectureDiagram.tsx]]
#[[file:frontend/src/lib/api.ts]]