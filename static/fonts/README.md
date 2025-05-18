# Font Files Setup

This directory should contain the following Departure Mono font files:

- `DepartureMono-Regular.woff2`
- `DepartureMono-Regular.woff`
- `DepartureMono-Bold.woff2`
- `DepartureMono-Bold.woff`

## How to Add Font Files

1. Purchase and download the Departure Mono font from the official source
2. Convert the font files to WOFF and WOFF2 formats using a font converter
3. Place the converted files in this directory

## Alternative Font

If you don't have access to Departure Mono, you can use a similar monospace font like JetBrains Mono by modifying the CSS in `templates/index.html`:

```css
/* Replace the @font-face declarations with: */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

/* And update the font-family declarations to use JetBrains Mono */
.navbar-brand, .hero-title {
    font-family: 'JetBrains Mono', monospace;
}
``` 