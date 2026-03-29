# Daily News Analyzer Agent

This is a Python-based background agent that automates fetching daily world technology, financial, and business news via RSS. It then calls the Gemini API (Large Language Model) to extract strategic business implications and predictions. Finally, it generates a clean Markdown report summarizing the findings.

## Setup Instructions

1. **Prerequisites**
   Ensure you have Python 3.8+ installed on your system.

2. **Setup the Virtual Environment & Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Settings (.env)**
   Ensure your API key and notification settings are set in `.env` (you can copy `.env.example` to start).
   ```bash
   cp .env.example .env
   ```
   *Note: If no API key is provided, the agent will gracefully mock the output instead of failing.*
   
   **Optional Notification Setup:**
   * **Slack**: Create an Incoming Webhook in Slack and paste the URL as `SLACK_WEBHOOK_URL="https://hooks.slack.com/..."`.
   * **Email**: Add your Gmail credentials to the `EMAIL_SENDER` and `EMAIL_PASSWORD`. Use an App Password if 2FA is enabled. Add your recipient to `EMAIL_RECEIVER`.

4. **Run the Agent**
   - **Manual/Synchronous Run:** Simply execute the main script to immediately test the pipeline.
     ```bash
     python3 main.py
     ```
   - **Background/Scheduled Run:** Open `main.py`, uncomment the lines around line 38, and set `SCHEDULE_TIME` to your preferred execution time (e.g. `"08:00"`). Leave the terminal window open or deploy the script on a cloud server/Raspberry Pi.

## View the Reports
Each daily run will produce a Markdown file inside the automatically created `reports/` folder (e.g., `reports/Business_Implications_Report_2026-03-29.md`).
