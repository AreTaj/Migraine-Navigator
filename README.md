# Migraine Log

This project is a Tkinter-based GUI application for logging and analyzing migraine occurrences. It allows users to input migraine instance details, view logged entries, and perform analysis on the data with the goal of facilitating forecasting based on machine learning algorithms.

## Features

- **Input Frame**: Allows users to input details about their migraines, including date, time, pain level, medication, dosage, triggers, notes, and location.
- **View Frame**: Displays the logged migraine entries in a tabular format.
- **Analysis Frame**: Provides graphical analysis of the migraine data, including migraine days per month, migraine days per year, and medication usage.

## Requirements

The project requires the following Python packages:

- `pandas`
- `geocoder`
- `matplotlib`
- `pytz`

You can install these dependencies using the following command:

```sh
pip install -r requirements.txt
```

## Usage

1. **Run the Application**: Execute the `main.py` file to start the application.

    ```sh
    python main.py
    ```

2. **Input Data**: Use the "Input" tab to enter migraine instance details. Click the "Save Entry" button to save the data.

3. **View Entries**: Switch to the "View Entries" tab to see the logged entries in a table.

4. **Analyze Data**: Go to the "Analysis" tab to perform graphical analysis on the migraine data. Select the type of graph you want to display and click the "Analyze" button.

## File Structure

- `main.py`: The main entry point of the application; all other frames are integrated here.
- `input_frame.py`: Contains the `InputFrame` class for inputting details.
- `view_frame.py`: Contains the `ViewFrame` class for viewing logged entries.
- `analysis_frame.py`: Contains the `AnalysisFrame` class for analyzing data.
- `migraine_log.csv`: The CSV file where data is stored.
- `requirements.txt`: Lists the required Python packages and allows easy installation.

## Screenshots

### Input Frame
![Input Frame](screenshots/input_frame.png)

### View Frame
Cannot be shown for reasons of data privacy.
![View Frame](screenshots/view_frame.png)

### Analysis Frame
![Analysis Frame](screenshots/analysis_frame.png)

## License

More information coming soon.

## Acknowledgements

- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI framework.
- [Pandas](https://pandas.pydata.org/) for data manipulation.
- [Matplotlib](https://matplotlib.org/) for plotting graphs.
- [Geocoder](https://geocoder.readthedocs.io/) for location services.
- [Pytz](https://pythonhosted.org/pytz/) for timezone handling.

## Author

This project was created by Aresh Tajvar.