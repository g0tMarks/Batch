# Mobile Navbar Standardization Across All Templates

## Product Requirements Document (PRD)

### Objective
Apply the hamburger menu mobile navbar pattern from `index.html` to all other template files, ensuring consistent mobile navigation experience across the entire application.

### Current State
- `index.html` has updated mobile navbar with hamburger menu
- Other templates (`login.html`, `signup.html`, `upload.html`, `download.html`, `reports.html`) have different navbar structures
- Inconsistent mobile navigation experience across the application
- Some templates use inline styles, others reference external CSS

### Desired State
- All templates have consistent mobile navbar behavior
- Hamburger menu pattern works identically across all pages
- Full "BATCH" logo visible on mobile for all templates
- Dropdown navigation accessible from any page
- Maintain existing desktop functionality for all templates

### Technical Requirements

1. **Template Analysis:**
   - Identify navbar structure in each template file
   - Map current navigation items per template
   - Determine if templates use inline styles or external CSS
   - Check for template-specific navigation logic

2. **HTML Structure Updates:**
   - Add hamburger menu button to each template
   - Create mobile dropdown menu container for each template
   - Ensure navigation items match template-specific requirements
   - Maintain existing desktop navbar structure

3. **CSS Integration:**
   - Apply mobile navbar styles from `styles.css` to all templates
   - Handle templates with inline styles vs external CSS
   - Ensure consistent styling across all pages
   - Maintain template-specific styling where appropriate

4. **JavaScript Functionality:**
   - Add hamburger menu JavaScript to each template
   - Ensure consistent behavior across all pages
   - Handle template-specific navigation logic

### Acceptance Criteria
- [ ] All templates show full "BATCH" logo on mobile (≤600px width)
- [ ] Hamburger menu appears on right side of all templates
- [ ] Dropdown menu works consistently across all pages
- [ ] Navigation items are appropriate for each template's context
- [ ] Desktop functionality remains unchanged
- [ ] No broken links or missing navigation items
- [ ] Consistent styling and animations across all templates

### Implementation Notes
- Templates may have different navigation items (logged-in vs logged-out states)
- Some templates may need template-specific navigation logic
- Inline styles in templates should be preserved where appropriate
- External CSS should be used for shared mobile navbar styles
- Test each template individually to ensure proper functionality

---

## Task List

### Phase 1: Analysis & Planning
- [ ] **Task 1.1:** Examine `login.html` navbar structure and navigation items
- [ ] **Task 1.2:** Examine `signup.html` navbar structure and navigation items  
- [ ] **Task 1.3:** Examine `upload.html` navbar structure and navigation items
- [ ] **Task 1.4:** Examine `download.html` navbar structure and navigation items
- [ ] **Task 1.5:** Examine `reports.html` navbar structure and navigation items
- [ ] **Task 1.6:** Document which templates use inline styles vs external CSS
- [ ] **Task 1.7:** Map navigation items and user states for each template

### Phase 2: HTML Structure Updates
- [ ] **Task 2.1:** Update `login.html` - Add hamburger menu button structure
- [ ] **Task 2.2:** Update `login.html` - Add mobile dropdown menu container
- [ ] **Task 2.3:** Update `login.html` - Ensure navigation items match template requirements (HOME, SIGN UP)
- [ ] **Task 2.4:** Update `login.html` - Maintain existing desktop navbar

- [ ] **Task 2.5:** Update `signup.html` - Add hamburger menu button structure
- [ ] **Task 2.6:** Update `signup.html` - Add mobile dropdown menu container
- [ ] **Task 2.7:** Update `signup.html` - Ensure navigation items match template requirements (HOME, LOGIN)
- [ ] **Task 2.8:** Update `signup.html` - Maintain existing desktop navbar

- [ ] **Task 2.9:** Update `upload.html` - Add hamburger menu button structure
- [ ] **Task 2.10:** Update `upload.html` - Add mobile dropdown menu container
- [ ] **Task 2.11:** Update `upload.html` - Ensure navigation items match template requirements (DOWNLOAD, UPLOAD, REPORTS, LOGOUT)
- [ ] **Task 2.12:** Update `upload.html` - Maintain existing desktop navbar

- [ ] **Task 2.13:** Update `download.html` - Add hamburger menu button structure
- [ ] **Task 2.14:** Update `download.html` - Add mobile dropdown menu container
- [ ] **Task 2.15:** Update `download.html` - Ensure navigation items match template requirements (DOWNLOAD, UPLOAD, REPORTS, LOGOUT)
- [ ] **Task 2.16:** Update `download.html` - Maintain existing desktop navbar

- [ ] **Task 2.17:** Update `reports.html` - Add hamburger menu button structure
- [ ] **Task 2.18:** Update `reports.html` - Add mobile dropdown menu container
- [ ] **Task 2.19:** Update `reports.html` - Ensure navigation items match template requirements (DOWNLOAD, UPLOAD, REPORTS, LOGOUT)
- [ ] **Task 2.20:** Update `reports.html` - Maintain existing desktop navbar

### Phase 3: CSS Integration
- [ ] **Task 3.1:** Identify templates with inline navbar styles
- [ ] **Task 3.2:** Extract mobile navbar styles to external CSS where appropriate
- [ ] **Task 3.3:** Ensure mobile navbar styles are applied consistently
- [ ] **Task 3.4:** Preserve template-specific styling where needed
- [ ] **Task 3.5:** Verify mobile navbar styles from `styles.css` work across all templates
- [ ] **Task 3.6:** Add any missing mobile-specific styles to external CSS
- [ ] **Task 3.7:** Ensure hamburger menu animations work on all templates
- [ ] **Task 3.8:** Test responsive breakpoints across all templates

### Phase 4: JavaScript Integration
- [ ] **Task 4.1:** Add hamburger menu JavaScript to `login.html`
- [ ] **Task 4.2:** Add hamburger menu JavaScript to `signup.html`
- [ ] **Task 4.3:** Add hamburger menu JavaScript to `upload.html`
- [ ] **Task 4.4:** Add hamburger menu JavaScript to `download.html`
- [ ] **Task 4.5:** Add hamburger menu JavaScript to `reports.html`
- [ ] **Task 4.6:** Ensure consistent behavior across all templates

### Phase 5: Testing & Validation
- [ ] **Task 5.1:** Test `login.html` mobile navbar functionality
- [ ] **Task 5.2:** Test `signup.html` mobile navbar functionality
- [ ] **Task 5.3:** Test `upload.html` mobile navbar functionality
- [ ] **Task 5.4:** Test `download.html` mobile navbar functionality
- [ ] **Task 5.5:** Test `reports.html` mobile navbar functionality
- [ ] **Task 5.6:** Verify navigation items work correctly on each template
- [ ] **Task 5.7:** Verify hamburger menu behavior is identical across all templates
- [ ] **Task 5.8:** Test responsive breakpoints (mobile vs desktop)
- [ ] **Task 5.9:** Ensure no broken links or missing navigation items
- [ ] **Task 5.10:** Validate accessibility features (ARIA labels, keyboard navigation)
- [ ] **Task 5.11:** Test complete user flows across all templates
- [ ] **Task 5.12:** Verify desktop functionality remains unchanged
- [ ] **Task 5.13:** Check for any styling conflicts or inconsistencies
- [ ] **Task 5.14:** Ensure mobile UX is consistent and intuitive

### Phase 6: Documentation
- [ ] **Task 6.1:** Document mobile navbar implementation across all templates
- [ ] **Task 6.2:** Note any template-specific considerations
- [ ] **Task 6.3:** Update any relevant README or style guide documentation

---

## Progress Tracking

**Total Tasks:** 47
**Completed:** 0
**In Progress:** 0
**Remaining:** 47

**Current Phase:** Phase 1 - Analysis & Planning
**Next Task:** Task 1.1 - Examine `login.html` navbar structure and navigation items

---

## Notes
- All mobile navbar changes should only affect screens ≤600px width
- Desktop functionality must remain completely unchanged
- Test each template individually before moving to the next
- Maintain existing user experience while improving mobile navigation 