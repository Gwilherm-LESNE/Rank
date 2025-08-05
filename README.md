# Runner Ranking System

A Streamlit-based web application for calculating and visualizing Elo rankings for runners based on race results.

## Features

- **PDF Parsing**: Automatically parse PDF race results using camelot-py
- **Elo Ranking**: Calculate Elo ratings using the EloMMR algorithm
- **Interactive Dashboard**: Visualize rankings and runner statistics
- **Multi-Environment Support**: Run PDF parsing in a separate conda environment
- **Minimum Races Filter**: Filter out runners who participated in fewer than a specified number of races
- **Auto-Load Rankings**: Automatically loads and displays existing rankings from `data/csv/ranking.csv` if available
- **Name Mappings Cache**: Caches name mappings to avoid recomputing them on each update (JSON format with alphabetically ordered keys)
- **Different Names Cache**: Caches confirmed different names to avoid re-asking users about name similarities
- **Web Interface**: Static HTML page for viewing rankings (works with GitHub Pages)

## Setup

### 1. Create the Ranking Conda Environment

The PDF parsing functionality requires specific packages that are installed in a separate conda environment called `ranking`.

```bash
# Create conda environment for parsing PDFs
conda create -n parser python=3.10 && conda activate parser

# Install required packages for PDF parsing
pip install camelot-py opencv-python ghostscript pandas numpy

# Deactivate the environment
conda deactivate

#Create conda environment for ranking
conda create -n ranking python=3.10 && conda activate ranking

# Install required packages
pip install openelo numpy pandas
```

### 2. Install Streamlit App Dependencies

In your ranking environment:

```bash
pip install streamlit plotly
```

## Usage

### Running the Streamlit App

```bash
streamlit run app.py
```

### Running the Web Interface

#### Local Development
```bash
cd docs
python -m http.server 8000
```
Then open: http://localhost:8000

#### GitHub Pages Deployment
1. Commit all files including the `docs/cache/` directory
2. Go to repository Settings → Pages
3. Set source to "Deploy from a branch" and folder to `/docs`
4. Your site will be available at: `https://yourusername.github.io/yourrepository/`

For detailed web interface instructions, see [docs/README.md](docs/README.md).

## Using LocalTunnel

```
lt --port yourPortNumber
```

To get the password
```
curl ipv4.icanhazip.com
```

### Workflow

1. **Auto-Load Rankings**: The app automatically loads existing rankings from `data/csv/ranking.csv` if available, allowing you to view previous results immediately.

2. **Parse PDF Files**: Use the sidebar to specify the PDF folder path and click "Parse PDF Files". This will run the parsing in the `ranking` conda environment.

3. **Calculate Rankings**: Set the minimum number of races required and optionally provide a previous rankings file, then click "Calculate Rankings".

4. **Filter Rankings**: Use the "Minimum Races Required" slider to filter out runners who participated in fewer races. Click "Update details" to apply the filter to existing rankings.

5. **View Results**: The app will display:
   - Current rankings table (filtered by minimum races)
   - Individual cyclist statistics
   - Performance history graphs

6. **Cache Management**: The app automatically caches name mappings to speed up processing. You can view cache statistics and clear the cache if needed.

## Development Workflow

### Updating Rankings and Deploying

When you have new race data to process and want to update the rankings:

1. **Switch to dev branch**
   ```bash
   git checkout dev
   # If dev branch doesn't exist, create it:
   # git checkout -b dev
   ```

2. **Process new race data**
   ```bash
   # Parse new PDF files (if any)
   streamlit run app.py
   # Or run the ranking system directly
   python rank.py --csv_folder data/csv --output ranking.csv
   ```

3. **Verify cache files are updated**
   ```bash
   # Check that docs/cache/ files are updated
   ls -la docs/cache/
   ```

4. **Commit changes to dev branch**
   ```bash
   git add .
   git commit -m "Update rankings with new race data"
   git push origin dev
   ```

5. **Test the changes**
   - Run locally: `cd docs && python -m http.server 8000`
   - Or check the dev branch deployment (if configured)

6. **Merge to main branch**
   ```bash
   git checkout main
   git merge dev
   git push origin main
   ```

7. **GitHub Pages will automatically update**
   - The main branch deployment will update with the new rankings
   - This ensures the live site always has the latest data

### Branch Strategy

- **`main`**: Production branch with stable rankings
- **`dev`**: Development branch for testing new rankings before deployment
- **Feature branches**: For major changes or new features

### Best Practices

- Always test rankings on dev branch before merging to main
- Include descriptive commit messages when updating rankings
- Verify cache files are committed with ranking updates
- Use pull requests for major changes

## File Structure

```
Rank/
├── app.py              # Main Streamlit application
├── rank.py             # Elo ranking calculation logic
├── parse_files.py      # PDF parsing functionality
├── test_conda_parse.py # Environment testing script
├── data/              
│   ├── pdf/            # Folder containing the race results as pdf. File names are expected to fit 'YYYY_MM_DD_race-name.pdf'
│   └── csv/            # Folder containing the race results parsed by camelot (button parse file in the app)
├── cache/              # Cache directory for name mappings
│   ├── name_mappings.json # Cached name mappings (JSON format)
│   ├── different_names.json # Cached confirmed different names (JSON format)
│   ├── processed_races.json # Cached races that are already processed (JSON format)
│   └── race_history.json # Cached result per race (JSON format)
├── docs/               # Web interface (GitHub Pages compatible)
│   ├── index.html      # Main web page
│   ├── .nojekyll       # Disable Jekyll processing for GitHub Pages
│   ├── README.md       # Web interface documentation
│   └── cache/          # Cache files for web interface
│       ├── ranking.csv # Rankings data
│       ├── race_history.json # Race history data
│       └── processed_races.json # Processed races data
└── README.md          # This file
```

## Cache File Formats

The system uses four JSON cache files to improve performance:

### Name Mappings Cache (`name_mappings.json`)
Stores normalized name mappings to handle typos and variations:
```json
{
  "alice smith": "Alice Smith",
  "bob jones": "Bob Jones",
  "charlie brown": "Charlie Brown"
}
```

### Different Names Cache (`different_names.json`)
Stores confirmed different names to avoid re-asking users:
```json
{
  "alice smith": ["alice smithson"],
  "bob jones": ["bob johnson"],
  "charlie brown": ["charles brown"]
}
```

### Processed Races
Stores the list of races that are already processed in order to avoid to compute them twice.

### Race History
Stores the cyclist results for each race. It is used to retrieve the results of each cyclist when plotting the 'cyclist details' in the app.

## Troubleshooting

### Common Issues

1. **Conda Environment Not Found**
   - Ensure the `ranking` environment exists: `conda env list`
   - Create it if missing: `conda create -n ranking python=3.9`

2. **PDF Parsing Fails**
   - Check if camelot-py is installed in the ranking environment
   - Verify Ghostscript is installed on your system
   - Check PDF file format and accessibility

3. **Import Errors**
   - Ensure all required packages are installed in both environments
   - Check Python path and module locations


This will check:
- Conda availability
- Ranking environment existence
- Python execution in the environment
- parse_files.py import capability

## Dependencies

### Ranking Environment (Main App)
- streamlit
- pandas
- plotly
- openelo
- numpy

### Parsing Environment (for PDF parsing)
- camelot-py
- opencv-python
- ghostscript
- pandas
- numpy

## License

This project is personal, released under MIT license