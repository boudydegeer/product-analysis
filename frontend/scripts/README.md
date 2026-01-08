# Screenshot Utility

A simple Playwright-based tool for capturing manual UI screenshots of the application. Perfect for documentation, debugging, bug reports, or visual testing.

## Prerequisites

The tool is already set up and ready to use. Playwright and Chromium browser are installed as dev dependencies.

If you need to reinstall:
```bash
pnpm add -D @playwright/test playwright
npx playwright install chromium
```

## Quick Start

### Basic Usage

```bash
# Capture homepage
npm run screenshot

# Or using pnpm
pnpm screenshot
```

This will:
- Launch Chromium in headless mode
- Navigate to http://localhost:5173
- Capture a screenshot
- Save to `frontend/screenshots/screenshot-<timestamp>.png`

### Common Use Cases

#### Capture a specific page
```bash
npm run screenshot -- --path=/dashboard --name=dashboard-view
```

#### Capture full page (including scrollable content)
```bash
npm run screenshot -- --path=/features --name=features-list --fullPage
```

#### Capture with custom dimensions
```bash
npm run screenshot -- --width=1920 --height=1080 --name=desktop-view
```

#### Capture from different URL (e.g., staging)
```bash
npm run screenshot -- --url=https://staging.example.com --name=staging-homepage
```

#### Capture API documentation
```bash
npm run screenshot -- --url=http://localhost:8000/docs --name=api-docs
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url=<url>` | Full URL to capture | `http://localhost:5173` |
| `--path=<path>` | Path to append to base URL | (empty) |
| `--name=<name>` | Base name for screenshot file | `screenshot-<timestamp>` |
| `--fullPage` | Capture full scrollable page | `false` (viewport only) |
| `--width=<pixels>` | Browser viewport width | `1280` |
| `--height=<pixels>` | Browser viewport height | `720` |
| `--help, -h` | Show help message | - |

## Examples

### Documentation Screenshots

```bash
# Dashboard page
npm run screenshot -- --path=/dashboard --name=dashboard --fullPage

# Feature list
npm run screenshot -- --path=/features --name=features

# Feature detail
npm run screenshot -- --path=/features/FEAT-001 --name=feature-detail
```

### Responsive Testing

```bash
# Mobile view
npm run screenshot -- --width=375 --height=667 --name=mobile-home

# Tablet view
npm run screenshot -- --width=768 --height=1024 --name=tablet-home

# Desktop view
npm run screenshot -- --width=1920 --height=1080 --name=desktop-home
```

### Bug Reporting

```bash
# Capture the problematic state
npm run screenshot -- --path=/buggy-page --name=bug-login-error
```

## Output

Screenshots are saved to: `frontend/screenshots/`

File naming format: `<name>-<timestamp>.png`

Example: `dashboard-view-2026-01-08T15-30-45.png`

**Note:** The `screenshots/` directory is gitignored and will not be committed to version control. This is intentional as screenshots are typically temporary artifacts.

## Troubleshooting

### "Connection refused" error

Make sure your development server is running:
```bash
cd frontend
npm run dev
```

The server should be accessible at http://localhost:5173 (or the URL you specified).

### Page not loading correctly

The script waits for `networkidle` (no network activity for 500ms) and then waits an additional 1 second for animations. If your page needs more time:

1. Modify the timeout in `scripts/screenshot.js`:
   ```javascript
   await page.waitForTimeout(3000); // Wait 3 seconds instead of 1
   ```

2. Or add specific element waiting:
   ```javascript
   await page.waitForSelector('#main-content');
   ```

### Screenshots directory not found

The script automatically creates the `screenshots/` directory on first run. If you encounter issues:

```bash
mkdir -p frontend/screenshots
```

## Advanced Usage

### Direct Script Execution

You can also run the script directly (without npm):

```bash
node scripts/screenshot.js --path=/dashboard --name=dashboard
```

### Multiple Screenshots

Create a bash script to capture multiple pages:

```bash
#!/bin/bash
# capture-all.sh

pages=("/" "/dashboard" "/features" "/settings")
names=("homepage" "dashboard" "features" "settings")

for i in "${!pages[@]}"; do
  npm run screenshot -- --path="${pages[$i]}" --name="${names[$i]}"
done
```

### CI/CD Integration

Add to your CI pipeline for visual regression testing or documentation:

```yaml
# .github/workflows/screenshots.yml
- name: Start dev server
  run: npm run dev &

- name: Wait for server
  run: npx wait-on http://localhost:5173

- name: Capture screenshots
  run: |
    npm run screenshot -- --path=/ --name=homepage
    npm run screenshot -- --path=/dashboard --name=dashboard

- name: Upload screenshots
  uses: actions/upload-artifact@v3
  with:
    name: screenshots
    path: frontend/screenshots/
```

## Technical Details

- **Browser**: Chromium (headless)
- **Engine**: Playwright
- **Image Format**: PNG
- **Default Viewport**: 1280x720
- **Wait Strategy**: networkidle + 1s delay
- **Device Scale**: 1x (can be modified in script)

## Maintenance

### Update Playwright

```bash
pnpm update @playwright/test playwright
npx playwright install chromium
```

### Clean up old screenshots

```bash
# Remove all screenshots
rm -rf frontend/screenshots/*.png

# Remove screenshots older than 7 days
find frontend/screenshots -name "*.png" -mtime +7 -delete
```

## Support

For issues or feature requests, please refer to the main project documentation or create an issue in the repository.
