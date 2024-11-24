# NBA Game Predictor

A web application that predicts NBA game outcomes based on team standings, recent news, and head-to-head matchups.

## Features

- Select any two NBA teams to predict game outcome
- View current NBA standings
- See head-to-head matchup history
- Get recent news about selected teams
- Receive win probability predictions
- Get estimated final scores

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Select two teams and click "Predict Game" to see the prediction

## Technical Details

- Built with Flask (Python web framework)
- Frontend uses Bootstrap 5 for responsive design
- Uses placeholder data for standings, news, and head-to-head records
- Prediction algorithm based on head-to-head records (placeholder implementation)

## Future Improvements

- Integrate with real NBA data API
- Add machine learning models for more accurate predictions
- Include player statistics and injury reports
- Add historical trends analysis
- Implement real-time score updates
