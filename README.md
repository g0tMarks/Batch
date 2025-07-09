# Batch_Report
Batch report writing tool

## Overview
Batch is a Flask-based web application that simplifies student report writing by using AI to generate personalized reports from spreadsheet data and sample reports. The application features a responsive design with a unified mobile navigation experience across all pages.

## Features

### Core Functionality
- **Template Download**: Excel template for student data input
- **File Upload**: Drag-and-drop file upload with progress tracking
- **AI Report Generation**: Automated report creation using AI
- **Report Management**: View, download, and delete generated reports
- **User Authentication**: Secure login and signup system

### Responsive Design
- **Mobile-First Approach**: Optimized for mobile devices (≤600px width)
- **Unified Navigation**: Consistent hamburger menu across all templates
- **Desktop Compatibility**: Full desktop functionality maintained
- **Cross-Browser Support**: Chrome, Firefox, Safari, Edge

## Mobile Navigation

### Implementation
The application features a standardized mobile navbar across all templates:

- **Hamburger Menu**: Three-line menu button on mobile devices
- **Context-Aware Navigation**: Shows appropriate links based on user authentication status
- **Active State Highlighting**: Current page highlighted in navigation
- **Accessibility**: ARIA labels and keyboard navigation support

### Navigation States

#### Logged-in Users
- DOWNLOAD (template download)
- UPLOAD (file upload page)
- REPORTS (view generated reports)
- LOGOUT (user logout)

#### Logged-out Users
- LOGIN (user authentication)
- SIGN UP (user registration)

### Technical Details

#### HTML Structure
All templates use a unified `.header-bar` structure with:
- Full "BATCH" logo (visible on mobile)
- Desktop navigation buttons
- Mobile hamburger menu
- Dropdown navigation menu

#### CSS Implementation
- Mobile navbar styles centralized in `static/styles.css`
- Responsive breakpoints: Mobile (≤600px), Desktop (≥600px)
- Smooth animations and transitions
- Consistent styling across all templates

#### JavaScript Functionality
- Hamburger menu toggle functionality
- Click-outside-to-close behavior
- Navigation item click handling
- Consistent behavior across all pages

## File Structure

```
Batch_Report/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── index.html        # Landing page
│   ├── login.html        # User login
│   ├── signup.html       # User registration
│   ├── upload.html       # File upload interface
│   ├── download.html     # Template download
│   └── reports.html      # Report management
├── static/               # Static assets
│   ├── styles.css        # Main stylesheet (includes mobile navbar)
│   ├── icons/           # Navigation and UI icons
│   └── fonts/           # Custom fonts
└── utils/               # Utility modules
```

## Templates

### Mobile Navigation Implementation
All templates feature consistent mobile navigation:

1. **index.html** - Landing page with dynamic navigation based on user state
2. **login.html** - Authentication page with HOME and SIGN UP navigation
3. **signup.html** - Registration page with HOME and LOGIN navigation
4. **upload.html** - File upload with full logged-in navigation
5. **download.html** - Template download with full logged-in navigation
6. **reports.html** - Report management with full logged-in navigation

### Template-Specific Features
- **Context-Aware Navigation**: Each template shows appropriate navigation items
- **Active State Management**: Current page highlighted in both desktop and mobile navigation
- **Form Integration**: All forms work seamlessly with mobile layout
- **JavaScript Compatibility**: Template-specific functionality preserved

## Responsive Design

### Breakpoints
- **Mobile**: ≤600px width
- **Desktop**: ≥600px width

### Mobile Features
- Hamburger menu navigation
- Full "BATCH" logo display
- Touch-friendly interface
- Optimized form layouts
- Responsive typography

### Desktop Features
- Traditional horizontal navigation
- Full feature access
- Hover effects and interactions
- Optimal spacing and layout

## Accessibility

### ARIA Implementation
- Hamburger menu includes `aria-label="Toggle navigation menu"`
- Semantic HTML structure with `<nav>` elements
- Proper heading hierarchy

### Keyboard Navigation
- Menu can be opened/closed with keyboard
- Dropdown items are keyboard accessible
- Focus management handled appropriately
- Tab order follows logical flow

### Screen Reader Support
- Proper navigation announcements
- Descriptive link text
- Form labels and descriptions
- Error message accessibility

## Browser Compatibility

### Tested Browsers
- **Chrome**: Desktop and Mobile
- **Firefox**: Desktop and Mobile
- **Safari**: Desktop and Mobile
- **Edge**: Desktop

### Responsive Behavior
- Consistent hamburger menu functionality
- Proper CSS rendering across browsers
- JavaScript compatibility maintained
- Touch and mouse interaction support

## Performance

### CSS Optimization
- Mobile styles only load on mobile devices
- Minimal CSS footprint for mobile navbar
- Efficient animations using CSS transforms
- External stylesheet for caching

### JavaScript Performance
- Event delegation for dropdown items
- Minimal DOM queries
- Efficient event handling
- No external dependencies

## Maintenance

### Code Organization
- Mobile navbar styles centralized in external CSS
- Consistent HTML structure across all templates
- Identical JavaScript functionality
- Template-specific styling preserved

### Future Updates
- Mobile navbar changes made in `static/styles.css`
- Template-specific navigation logic preserved
- Test on both mobile and desktop after changes
- Maintain accessibility features


### Setup
1. Install Python dependencies: `pip install -r requirements.txt`
2. Configure database settings
3. Run the application: `python app.py`

### Testing
- Test mobile navigation on all templates
- Verify responsive breakpoints
- Check accessibility features
- Validate cross-browser compatibility

## License
[Add your license information here]
