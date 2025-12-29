NFL AI Defense Stats Tracker

A Flask web app that pulls NFL defensive stats from ESPN, runs AI generated summaries on each team, and lets you download everything in an Excel file.

Features

• Fetches current NFL defensive stats from ESPN
• Uses AI to generate defensive summaries for all 32 teams
• Exports data and summaries to an Excel file named nfl_ai_summary.xlsx
• Simple browser based interface
• Secure API key stored in a dot env file

Setup
1. Install dependencies
pip install -r requirements.txt

2. Create a dot env file

Place this in the main folder:

OPENAI_API_KEY=sk_your_actual_api_key_here


Make sure it follows these rules
• Starts with sk
• No spaces around the equal sign
• No quotes
• No extra line breaks

Check the config with:

python check_env.py

3. Launch the web app
python app.py


Open a browser and go to:

http colon slash slash localhost colon five thousand

How to use it

Go to the web page in your browser

Click the button that starts the process

Wait while it collects and analyzes all teams

Download the Excel file once the button appears

Project files

• dot env file stores your private API key and is not uploaded to git
• app dot py runs the Flask web server
• learningESPN dot py fetches data from ESPN, calls the AI model, and writes the Excel file
• main dot html handles the web interface
• requirements dot txt lists the Python packages
• nfl_ai_summary dot xlsx is the file the tool creates

How the system works

It fetches defensive stats for each NFL team using ESPN public data

It sends those stats to the AI model to create a summary

It writes both the numbers and the summary into the Excel file

The user downloads the final result through the browser

Troubleshooting tips

If you get a message about an invalid string pattern
• Confirm that your API key starts with sk
• Confirm that you did not use quotes
• Confirm that there are no spaces or line breaks

Run this again if needed

python check_env.py


Other common issues
• Port already in use update the port number in app dot py inside app run parentheses
• Missing modules install everything using the requirements file
• Download not working wait until the analysis finishes before clicking the download button

Extra notes

• The app uses public ESPN data that might have rate limits
• Requires a valid OpenAI API key for the summaries
• Processing all 32 teams can take a few minutes
• The dot env file must be in the same folder as app dot py

Requirements

• Python version 3.8 or higher
• OpenAI API key
• Internet connection
