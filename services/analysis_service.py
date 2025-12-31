from services.entry_service import EntryService
# Lazy loaded
from datetime import datetime

class AnalysisService:
    @staticmethod
    def get_analysis_data(db_path: str):
        """
        Fetches and processes data for analysis.
        Returns calculated statistics directly, rather than raw data.
        """
        data = EntryService.get_entries_from_db(db_path)
        
        if not data:
            return None

        import pandas as pd
        
        # Convert list of dicts to DataFrame for analysis
        data = pd.DataFrame(data)
        
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
        # Filter for entries with Pain > 0 to identify "Migraine Episodes"
        painful_entries = data[data['Pain Level'] > 0].copy()
        
        # Normalize Medication: strip whitespace, replace empty with "No Medication"
        painful_entries['Medication'] = painful_entries['Medication'].astype(str).str.strip()
        painful_entries.loc[painful_entries['Medication'] == '', 'Medication'] = 'No Medication'
        
        medication_counts = painful_entries['Medication'].value_counts()
        
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

        # 5. General Stats
        avg_pain = migraines_with_pain['Pain Level'].mean() if not migraines_with_pain.empty else 0
        max_pain = migraines_with_pain['Pain Level'].max() if not migraines_with_pain.empty else 0

        return {
            "yearly_counts": yearly_counts.to_dict(),
            "medication_counts": medication_counts.to_dict(),
            "monthly_counts": monthly_counts.to_dict(),
            "past_12_months_counts": past_12_counts.to_dict(),
            "avg_pain": round(avg_pain, 1),
            "max_pain": int(max_pain)
        }

    @staticmethod
    def get_trends_data(db_path: str, range_type: str = '1y'):
        """
        Returns formatted data for Recharts (Frontend).
        range_type: '1m', '1y', 'all'
        """
        data = EntryService.get_entries_from_db(db_path)
        if not data:
            return []

        import pandas as pd
        df = pd.DataFrame(data)
        if df.empty:
            return []

        # Standardize Date
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
        df = df.dropna(subset=['Date'])
        # Pain to numeric
        df['Pain Level'] = pd.to_numeric(df['Pain Level'], errors='coerce').fillna(0)

        now = datetime.now()
        
        # Filter Logic
        if range_type == '1m':
            # Last 30 Days -> Daily View (Pain Level)
            start_date = now - pd.DateOffset(days=30)
            filtered = df[df['Date'] >= start_date].copy()
            
            # Keep max pain per day
            daily = filtered.sort_values('Pain Level', ascending=False).drop_duplicates('Date').sort_values('Date')
            # Filter > 0 pain
            daily = daily[daily['Pain Level'] > 0]
            
            return [{
                "name": d.strftime('%b %-d'), 
                "value": p, 
                "type": "pain"
            } for d, p in zip(daily['Date'], daily['Pain Level'])]
            
        else:
            # Monthly View (Frequency)
            # Filter Date Range
            if range_type == '1y':
                start_date = now - pd.DateOffset(months=12)
                # First day of that month
                start_date = start_date.replace(day=1)
                df = df[df['Date'] >= start_date]
            elif range_type == 'all':
                pass # No filter
            
            # Count Migraine Days (Pain > 0)
            migraine_days = df[df['Pain Level'] > 0].copy()
            # Drop duplicates (if multiple entries per day, count as 1 day)
            migraine_days = migraine_days.drop_duplicates(subset='Date')
            
            # Group by Month
            # Use period 'M' to group (e.g., 2025-01)
            monthly = migraine_days.groupby(migraine_days['Date'].dt.to_period('M')).size()
            
            # Ensure all months in range are present? 
            # Recharts handles missing, but nicer to have 0s.
            # Using simple conversion for now.
            
            result = []
            for period, count in monthly.items():
                # Format: "Jan 2025" or "Jan"
                label = period.strftime('%b %Y') if range_type != 'current_year' else period.strftime('%b')
                result.append({
                    "name": label,
                    "value": int(count),
                    "type": "count",
                    "sortKey": period.start_time.timestamp() # Helper for sorting if needed, but dict order usually ok in recent python
                })
            
            return result

