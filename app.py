#%%
import streamlit as st
import pandas as pd
import os
import sys
import subprocess
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import datetime

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
from rank import Ranker

# Page configuration
st.set_page_config(
    page_title="Runner Ranking System",
    page_icon="\U0001f6b4",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .runner-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .runner-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .selected-runner {
        border: 2px solid #1f77b4;
        background-color: #f8f9ff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ranker' not in st.session_state:
    st.session_state.ranker = None
if 'rankings_df' not in st.session_state:
    st.session_state.rankings_df = None
if 'selected_runner' not in st.session_state:
    st.session_state.selected_runner = None

def load_existing_rankings():
    """
    Load existing rankings from data/csv/ranking.csv if it exists
    """
    ranking_file = "data/csv/ranking.csv"
    if os.path.exists(ranking_file):
        try:
            df = pd.read_csv(ranking_file)
            # Also create a ranker object to enable cyclist details
            ranker = Ranker(previous_rank=ranking_file)
            return df, ranker
        except Exception as e:
            st.error(f"Error loading existing rankings: {str(e)}")
            return None, None
    return None, None

# Load existing rankings on app start
if st.session_state.rankings_df is None:
    existing_rankings, existing_ranker = load_existing_rankings()
    if existing_rankings is not None:
        st.session_state.rankings_df = existing_rankings
        st.session_state.ranker = existing_ranker
        # Show success message in sidebar
        st.sidebar.success("✅ Loaded existing rankings from data/csv/ranking.csv")

def run_parse_files_in_conda(pdf_folder, csv_folder):
    """
    Run parse_files.py in the 'ranking' conda environment using subprocess
    """
    try:
        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
     
        # Run the script in the ranking conda environment
        cmd = [
            'conda run -n parser python parse_files.py'
              ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_dir,
            shell=True
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def main():
    # Header
    st.markdown('<h1 class="main-header">FSGT CX Ranking</h1>', unsafe_allow_html=True)
    
    # Sidebar for controls
    with st.sidebar:        
        # File parsing section
        st.subheader("📄 Parse PDF Files")
        
        if st.button("Parse PDF Files", type="primary"):
            with st.spinner("Parsing PDF files..."):
                try:
                    success, message = run_parse_files_in_conda("data/pdf", "data/csv")
                    if success:
                        st.success("✅ PDF files parsed successfully!")
                    else:
                        st.error(f"❌ Error parsing files: {message}")
                except Exception as e:
                    st.error(f"❌ Error parsing files: {str(e)}")
        
        st.divider()
        
        # Ranking section
        st.subheader("🏆 Calculate Rankings")
        previous_rank_file = 'data/csv/ranking.csv' if os.path.exists('data/csv/ranking.csv') else None
        
        if st.button("Calculate Rankings", type="primary"):
            with st.spinner("Calculating rankings..."):
                #try:
                    # Initialize ranker
                    ranker = Ranker(previous_rank=previous_rank_file)
                    
                    # Process all races
                    ranker.rank(folder="data/csv")
                    
                    # Get filtered rankings with minimum races requirement
                    min_races = st.session_state.get('min_races', 3)
                    rankings_data = ranker.get_rankings(min_races=min_races)
                    
                    # Create DataFrame from filtered rankings
                    rankings_df = pd.DataFrame(rankings_data, columns=['name', 'rating', 'sigma', 'races_participated'])
                    rankings_df['rank'] = range(1, len(rankings_df) + 1)                
                    rankings_df = rankings_df[['rank', 'name', 'rating', 'sigma', 'races_participated']]
                    
                    # Save rankings
                    ranker.save_rankings(folder="data/csv", fname="ranking", ext="csv")
                    
                    # Store in session state
                    st.session_state.ranker = ranker
                    st.session_state.rankings_df = rankings_df
                    
                    st.success("✅ Rankings calculated successfully!")
                #except Exception as e:
                #    st.error(f"❌ Error calculating rankings: {str(e)}")
        
        # Add recalculate button for existing rankings
        if st.session_state.ranker is not None:
            if st.button("Update details"):
                with st.spinner("Recalculating rankings with current filter..."):
                    try:
                        # Get filtered rankings with current minimum races requirement
                        min_races = st.session_state.get('min_races', 3)
                        rankings_data = st.session_state.ranker.get_rankings(min_races=min_races)
                        
                        # Create DataFrame from filtered rankings
                        rankings_df = pd.DataFrame(rankings_data, columns=['name', 'rating', 'sigma', 'races_participated'])
                        rankings_df['rank'] = range(1, len(rankings_df) + 1)                        
                        rankings_df = rankings_df[['rank', 'name', 'rating', 'sigma', 'races_participated']]
                        
                        # Update session state
                        st.session_state.rankings_df = rankings_df
                        
                        st.success("✅ Rankings recalculated with current filter!")
                    except Exception as e:
                        st.error(f"❌ Error recalculating rankings: {str(e)}")
        
        st.divider()
        
        # Display options
        st.subheader("📊 Display Options")
        min_races = st.number_input("Minimum Races Required", value=3, min_value=1, max_value=10, help="Only show runners who participated in at least this many races")
        st.session_state['min_races'] = min_races # Store min_races in session state
        
        if st.session_state.rankings_df is not None:
            st.metric("Total Runners", len(st.session_state.rankings_df))
            if st.session_state.ranker:
                st.metric("Total Races", len(st.session_state.ranker.race_history))
        
        # Cache management
        if st.session_state.ranker is not None:
            st.divider()
            st.subheader("🗄️ Cache Management")
            
            # Check if any cache files exist
            cache_files_exist = (
                os.path.exists(os.path.join(st.session_state.ranker.cache_dir, 'name_mappings.json')) or 
                os.path.exists(os.path.join(st.session_state.ranker.cache_dir, 'different_names.json')) or
                os.path.exists(os.path.join(st.session_state.ranker.cache_dir, 'processed_races.json')) or
                os.path.exists(os.path.join(st.session_state.ranker.cache_dir, 'race_history.json'))
            )
            
            if cache_files_exist:
                                
                if st.button("🗑️ Clear All Caches", type="secondary"):
                    st.session_state.ranker.clear_cache()
                    st.success("✅ All caches cleared!")
                    st.rerun()
            else:
                st.info("No caches found")
    
    # Main content area
    st.header("Current Ranking")
    
    if st.session_state.rankings_df is not None:
        # Apply minimum races filter to displayed rankings
        current_min_races = st.session_state.get('min_races', 3)
        filtered_rankings = st.session_state.rankings_df[
            st.session_state.rankings_df['races_participated'] >= current_min_races
        ].copy()
        
        # Display rankings table
        display_rankings = filtered_rankings.copy()
                    
        st.dataframe(
            display_rankings,
            use_container_width=True,
            hide_index=True
        )
        
        # Show filter info
        st.info(f"Showing runners with at least {current_min_races} races. Total filtered runners: {len(filtered_rankings)}")
        

        ######### Rankings chart #########
        # if len(display_rankings) > 0:
        #     fig = px.bar(
        #         display_rankings.head(10),
        #         x='name',
        #         y='rating',
        #         title="Top 10 Runner Ratings",
        #         labels={'name': 'Runner Name', 'rating': 'Elo Rating'},
        #         color='rating',
        #         color_continuous_scale='viridis'
        #     )
        #     fig.update_layout(
        #         xaxis_tickangle=-45,
        #         height=400,
        #         showlegend=False
        #     )
        #     st.plotly_chart(fig, use_container_width=True)
        # else:
        #     st.warning("No runners meet the minimum races requirement.")
        
    else:
        st.info("Use the sidebar controls to parse PDF files and calculate rankings.")
    
    st.divider()
    
    # Runner Details section below rankings
    st.header("📈 Cyclist Details")
    
    if st.session_state.rankings_df is not None:
        # Apply minimum races filter to displayed rankings
        current_min_races = st.session_state.get('min_races', 3)
        filtered_rankings = st.session_state.rankings_df[
            st.session_state.rankings_df['races_participated'] >= current_min_races
        ].copy()
        
        # Runner selection
        runner_names = filtered_rankings['name'].tolist()
        
        # Handle case where selected runner is not in filtered list
        if st.session_state.selected_runner and st.session_state.selected_runner in runner_names:
            default_index = runner_names.index(st.session_state.selected_runner)
        else:
            default_index = 0
            st.session_state.selected_runner = runner_names[0] if runner_names else None
        
        selected_runner = st.selectbox(
            "Select a runner:",
            runner_names,
            index=default_index
        )
        
        if selected_runner and st.session_state.ranker:
            # Get runner statistics
            stats = st.session_state.ranker.get_player_stats(selected_runner)
            
            if stats:
                # Display runner stats
                st.markdown(f"### {stats['name']}")
                
                # Get current rank from filtered rankings
                runner_rank_data = filtered_rankings[filtered_rankings['name'] == selected_runner]
                current_rank = runner_rank_data['rank'].iloc[0] if not runner_rank_data.empty else "N/A"
                
                # Stats cards
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Current Rank", f"#{current_rank}" if current_rank != "N/A" else current_rank)
                    st.metric("Current Rating", f"{stats['current_rating']:.1f}")
                
                with col_b:
                    st.metric("Best Finish", f"{stats['best_finish']}" if stats['best_finish'] else "N/A")
                    st.metric("Rating Uncertainty", f"{stats['rating_uncertainty']:.1f}")
                
                with col_c:
                    st.metric("Races Participated", stats['races_participated'])
                
                # Rating history visualization
                if st.session_state.ranker.race_history:
                    
                    # Create rating history data
                    rating_history = []
                    for i, race in enumerate(st.session_state.ranker.race_history):
                        race_data = race['race_data']
                        if selected_runner in race_data['name'].values:
                            runner_place = race_data[race_data['name'] == selected_runner]['place'].iloc[0]
                            race_name = race.get('race_name', f'Race {i+1}')
                            # Clean up race name for display (remove .csv extension and format date)
                            if race_name.endswith('.csv'):
                                race_name = race_name[:-4]  # Remove .csv extension
                            # Try to format the date part if it exists
                            if race_name[-2] == '_' and race_name[-1].isdigit():
                                race_name = race_name[:-2]

                            idx = 1
                            tmp_race_name = race_name
                            while tmp_race_name in [h['race_name'] for h in rating_history]:
                                tmp_race_name = f"{race_name}_{idx}"
                                idx += 1
                            race_name = tmp_race_name
                            
                            rating_history.append({
                                'race': i + 1,
                                'race_name': race_name,
                                'place': runner_place,
                                'total_runners': len(race_data)
                            })
                    
                    if rating_history:
                        history_df = pd.DataFrame(rating_history)
                        
                        st.markdown(f"### Result History")
    
                        # Create subplot for place history
                        fig = make_subplots(
                            rows=1, cols=1,
                        )
                        
                        # Race performance over time
                        fig.add_trace(
                            go.Scatter(
                                x=history_df['race_name'],
                                y=history_df['place'],
                                mode='lines+markers',
                                name='Place',
                                line=dict(color='#1f77b4', width=2),
                                marker=dict(size=8)
                            ),
                            row=1, col=1
                        )
                        
                        fig.update_layout(
                            height=400,
                            showlegend=False,
                        )
                        
                        fig.update_xaxes(title_text="Race", tickangle=-45)
                        fig.update_yaxes(title_text="Place")
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No race history available for this runner.")
            else:
                st.error("Could not retrieve statistics for this runner.")
        elif selected_runner and not st.session_state.ranker:
            # Show basic info when ranker is not available
            st.markdown(f"### {selected_runner}")
            st.info("📊 Detailed statistics not available (rankings loaded from file). Calculate new rankings to see detailed runner statistics and performance history.")
            
            # Show basic ranking info if available
            runner_data = filtered_rankings[filtered_rankings['name'] == selected_runner]
            if not runner_data.empty:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Current Rating", f"{runner_data['rating'].iloc[0]:.1f}")
                with col_b:
                    st.metric("Races Participated", runner_data['races_participated'].iloc[0])
                with col_c:
                    st.metric("Position", f"#{runner_data['rank'].iloc[0]} of {len(filtered_rankings)}")
    else:
        st.info("Calculate rankings first to view runner details.")
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🏃‍♂️ Runner Ranking System | Built with Streamlit & EloMMR"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()