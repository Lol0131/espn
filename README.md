# NFL AI Defense Stats Tracker

A Flask web application that fetches NFL defensive statistics from ESPN, uses AI to generate defensive summaries, and provides a downloadable Excel file.

## Features

- 🏈 Fetches real-time NFL defensive stats from ESPN
- 🤖 AI-powered defensive analysis for all 32 NFL teams
- 📊 Exports data to Excel file (nfl_ai_summary.xlsx)
- 🎨 Modern, user-friendly web interface
- 🔒 Secure API key management with .env file

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-your_actual_api_key_here
```

Replace `sk-your_actual_api_key_here` with your actual OpenAI API key. You can get one from [OpenAI's website](https://platform.openai.com/api-keys).

**Important:** 
- The API key should start with `sk-`
- No spaces around the `=` sign
- No quotes around the key value
- No newlines in the key
- Example: `OPENAI_API_KEY=sk-1234567890abcdef...`

**Check your .env setup:**
```bash
python check_env.py
```
This will verify your .env file is configured correctly.

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Click the "Start Analysis & Download" button
3. Wait for the analysis to complete (this may take a few minutes as it processes all 32 NFL teams)
4. Click the "Download Excel File" button to download the results

## File Structure

- **.env** - Stores your private API keys (OPENAI_API_KEY) - **NOT committed to git**
- **app.py** - Flask web server that handles routes and connects frontend with backend
- **learningESPN.py** - Fetches NFL data from ESPN, uses AI to create defensive summaries, saves to Excel
- **main.html** - Web interface with "Start & Download" button
- **requirements.txt** - Python dependencies
- **nfl_ai_summary.xlsx** - Generated Excel file with team defensive stats and AI summaries

## How It Works

1. **Data Fetching**: The application fetches NFL team defensive statistics from ESPN's public API
2. **AI Analysis**: For each team, OpenAI GPT generates a concise defensive analysis based on their stats
3. **Excel Export**: All team data and AI summaries are compiled into an Excel file
4. **Download**: Users can download the Excel file directly from the web interface

## Troubleshooting

### Error: "The string did not match the expected pattern"

This error typically occurs when the OpenAI API key format is incorrect. To fix:

1. **Check your .env file format:**
   - Make sure there are no spaces around the `=` sign
   - Don't use quotes around the API key
   - Ensure the key starts with `sk-`
   - No newlines or extra characters

2. **Run the diagnostic script:**
   ```bash
   python check_env.py
   ```

3. **Verify your API key:**
   - Your OpenAI API key should be about 51 characters long
   - It should start with `sk-`
   - Get a new key from [OpenAI Platform](https://platform.openai.com/api-keys) if needed

### Other Common Issues

- **Port 5000 already in use**: Change the port in `app.py` by modifying `app.run(debug=True, port=5501)`
- **Module not found**: Run `pip install -r requirements.txt` to install all dependencies
- **Excel file not downloading**: Make sure you click "Start Analysis & Download" first, then wait for it to complete

## Notes

- The application uses ESPN's public API endpoints, which may have rate limits
- AI summaries require a valid OpenAI API key
- The analysis processes all 32 NFL teams, so it may take 2-5 minutes to complete
- Make sure your `.env` file is in the same directory as `app.py`

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for fetching ESPN data

## License

This project is for client use.
