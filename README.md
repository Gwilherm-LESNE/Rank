# Runner Ranking System

A Streamlit-based web application for calculating and visualizing Elo rankings for runners based on race results.

## Features

- **PDF Parsing**: Automatically parse PDF race results using camelot-py
- **Elo Ranking**: Calculate Elo ratings using the EloMMR algorithm
- **Interactive Dashboard**: Visualize rankings and runner statistics
- **Multi-Environment Support**: Run PDF parsing in a separate conda environment
- **Minimum Races Filter**: Filter out runners who participated in fewer than a specified number of races
- **Auto-Load Rankings**: Automatically loads and displays existing rankings from `data/csv/ranking.csv` if available
- **Name Mappings Cache**: Caches name mappings to avoid recomputing them on each update

## Setup

### 1. Create the Ranking Conda Environment

The PDF parsing functionality requires specific packages that are installed in a separate conda environment called `ranking`.

```bash
# Create the ranking environment
conda create -n ranking python=3.9

# Activate the environment
conda activate ranking

# Install required packages for PDF parsing
pip install camelot-py opencv-python ghostscript pandas numpy

# Deactivate the environment
conda deactivate
```

### 2. Install Streamlit App Dependencies

In your main environment (or create a new one):

```bash
pip install streamlit pandas plotly openelo numpy
```

## Usage

### Running the App

```bash
streamlit run app.py
```

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

4. **Filter Rankings**: Use the "Minimum Races Required" slider to filter out runners who participated in fewer races. Click "Recalculate with Current Filter" to apply the filter to existing rankings.

5. **View Results**: The app will display:
   - Current rankings table (filtered by minimum races)
   - Top 10 runners chart
   - Individual runner statistics
   - Performance history graphs

6. **Cache Management**: The app automatically caches name mappings to speed up processing. You can view cache statistics and clear the cache if needed.

## File Structure

```
Rank/
├── app.py              # Main Streamlit application
├── rank.py             # Elo ranking calculation logic
├── parse_files.py      # PDF parsing functionality
├── test_conda_parse.py # Environment testing script
├── cache/              # Cache directory for name mappings
│   └── name_mappings.pkl # Cached name mappings
└── README.md          # This file
```

## Key Modifications

### App.py Changes

- **Subprocess Integration**: Added `run_parse_files_in_conda()` function to run PDF parsing in the `ranking` conda environment
- **Updated Imports**: Changed from `RunnerEloRanker` to `Ranker` class
- **Method Updates**: Updated method calls to match the corrected `rank.py` implementation
- **Error Handling**: Enhanced error handling for subprocess operations

### Rank.py Fixes

- **Attribute Correction**: Fixed `self.runner_players` to `self.players` in `get_rankings()` method
- **Consistent Naming**: Ensured all references use the correct attribute names
- **Cache Implementation**: Added name mappings cache to avoid recomputing mappings on each update

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

### Main App Environment
- streamlit
- pandas
- plotly
- openelo
- numpy

### Ranking Environment (for PDF parsing)
- camelot-py
- opencv-python
- ghostscript
- pandas
- numpy

## License

This project is part of the ECM (École Centrale de Marseille) runner ranking system. 