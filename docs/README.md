# FSGT CX Ranking - Web Interface

This directory contains the web interface for the FSGT CX Ranking system.

## Features

- **Interactive Rankings Table**: View current Elo rankings with filtering options
- **Runner Details**: Select any runner to see detailed statistics
- **Performance History**: Interactive charts showing race performance over time
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Filtering**: Filter by minimum races and display limits

## Local Development

### Prerequisites

1. Make sure you have run the ranking system to generate cache files:
   ```bash
   python rank.py --csv_folder data/csv --output ranking.csv
   ```

2. Verify cache files exist in `docs/cache/`:
   - `ranking.csv`
   - `race_history.json`
   - `processed_races.json`

### Running Locally

1. **Option 1: Using Python's built-in server**
   ```bash
   cd docs
   python -m http.server 8000
   ```
   Then open: http://localhost:8000

2. **Option 2: Using any web server**
   - Serve the `page` directory with any web server
   - Make sure the server can access the `cache` subdirectory

### Troubleshooting Local Issues

- **CORS Errors**: Make sure you're using a web server, not opening the file directly
- **File Not Found**: Check that cache files exist in the `docs/cache/` directory
- **Port Already in Use**: Try a different port: `python -m http.server 8001`

## GitHub Pages Deployment

### Setup Instructions

1. **Commit all files including cache**
   ```bash
   git add .
   git commit -m "Add web interface with cache files"
   git push
   ```

2. **Configure GitHub Pages**
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Under "Source", select "Deploy from a branch"
   - Choose your main branch (usually `main` or `master`)
   - Set the folder to `/docs`
   - Click "Save"

3. **Wait for deployment**
   - GitHub will build and deploy your site
   - You'll see a green checkmark when deployment is complete
   - Your site will be available at: `https://yourusername.github.io/yourrepository/`

### GitHub Pages Benefits

- **No CORS Issues**: HTTPS serving eliminates local CORS problems
- **Automatic Updates**: Site updates when you push changes
- **Free Hosting**: No server setup required
- **Custom Domain**: Can use your own domain if desired

### File Structure for GitHub Pages

```
your-repository/
├── docs/
│   ├── index.html          # Main web page
│   ├── .nojekyll          # Disable Jekyll processing
│   ├── README.md          # This file
│   └── cache/             # Cache files (must be committed)
│       ├── ranking.csv
│       ├── race_history.json
│       └── processed_races.json
├── rank.py                # Ranking system
├── app.py                 # Streamlit app
└── data/                  # Race data
```

### Important Notes for GitHub Pages

1. **Cache Files Must Be Committed**: The `cache/` directory and all its files must be committed to the repository for the web interface to work.

2. **Nojekyll File**: The `.nojekyll` file tells GitHub Pages not to process the site with Jekyll, which can interfere with static file serving.

3. **Branch Protection**: Make sure your main branch is protected and cache files are included in commits.

4. **Deployment Time**: GitHub Pages deployment can take a few minutes after pushing changes.

## Usage

### Viewing Rankings

1. **Display Limit**: Choose how many top runners to show (10, 20, 50, 100, or all)
2. **Minimum Races**: Set the minimum number of races a runner must have participated in
3. **Runner Selection**: Use the dropdown to select a specific runner for detailed view

### Runner Details

When you select a runner, you'll see:
- **Current Rank**: Their position in the overall rankings
- **Elo Rating**: Their current Elo rating
- **Rating Uncertainty**: The uncertainty in their rating (± value)
- **Races Participated**: Total number of races they've run
- **Best Finish**: Their best race result
- **Performance History**: Interactive chart showing their race results over time

## Technical Details

- **Frontend**: Pure HTML/CSS/JavaScript (no framework required)
- **Charts**: Plotly.js for interactive visualizations
- **Data Format**: CSV for rankings, JSON for race history
- **Responsive**: Mobile-friendly design
- **No Backend**: All processing happens client-side

## Updating Rankings

To update the rankings on the web interface:

1. Run the ranking system:
   ```bash
   python rank.py --csv_folder data/csv --output ranking.csv
   ```

2. Commit the updated cache files:
   ```bash
   git add docs/cache/
   git commit -m "Update rankings"
   git push
   ```

3. GitHub Pages will automatically redeploy with the new data

## Troubleshooting

### Common Issues

1. **"Error loading rankings"**
   - Check that `docs/cache/ranking.csv` exists
   - Verify the file is committed to the repository
   - For local development, ensure you're using a web server

2. **"No race history available"**
   - Check that `docs/cache/race_history.json` exists
   - Verify the file contains valid JSON data

3. **Charts not displaying**
   - Check browser console for JavaScript errors
   - Ensure internet connection (Plotly.js is loaded from CDN)

4. **GitHub Pages not updating**
   - Wait a few minutes for deployment
   - Check the Actions tab for deployment status
   - Verify cache files are committed to the repository

### Browser Compatibility

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Mobile**: iOS Safari, Chrome Mobile
- **JavaScript**: Required (for interactivity)
- **Internet**: Required (for loading Plotly.js from CDN) 