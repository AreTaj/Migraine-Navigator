from services.entry_service import EntryService
import pandas as pd
from datetime import datetime

class AnalysisService:
    @staticmethod
    def get_analysis_data(db_path: str):
        """
        Fetches and processes data for analysis.
        Returns calculated statistics directly, rather than raw data.
        """
        data = EntryService.get_entries_from_db(db_path)
        
        if data.empty:
            return None

        # Process logic from AnalysisFrame.perform_analysis
        data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')
        data = data.dropna(subset=['Date']) # Drop rows with invalid dates
        
        data['Pain Level'] = pd.to_numeric(data['Pain Level'], errors='coerce')
        
        # Filter: Migraines with Pain > 0
        migraines_with_pain = data[data['Pain Level'] > 0]
        # Keep one per day
        migraines_with_pain = migraines_with_pain.drop_duplicates(subset='Date', keep='first')
        
        # 1. Yearly Counts
        yearly_counts = migraines_with_pain.groupby(migraines_with_pain['Date'].dt.year).size()
        
        # 2. Medication Usage
        medication_data = data[data['Medication'].astype(str).str.strip() != '']
        medication_counts = medication_data['Medication'].value_counts()
        
        # 3. Monthly (Current Year)
        current_year = datetime.now().year
        monthly_counts = migraines_with_pain[migraines_with_pain['Date'].dt.year == current_year]
        monthly_counts = monthly_counts.groupby(monthly_counts['Date'].dt.to_period('M')).size()
        # Convert period index to string
        monthly_counts.index = monthly_counts.index.strftime('%B')
        
        # 4. Past 12 Months
        end_date = data['Date'].max()
        start_date = end_date - pd.DateOffset(months=12)
        past_12_months = migraines_with_pain[(migraines_with_pain['Date'] >= start_date) & (migraines_with_pain['Date'] <= end_date)]
        past_12_counts = past_12_months.groupby(past_12_months['Date'].dt.to_period('M')).size()
        past_12_counts.index = past_12_counts.index.strftime('%B %Y')

        return {
            "yearly_counts": yearly_counts.to_dict(),
            "medication_counts": medication_counts.to_dict(),
            "monthly_counts": monthly_counts.to_dict(),
            "past_12_months_counts": past_12_counts.to_dict()
        }
