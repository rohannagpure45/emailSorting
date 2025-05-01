# Email Sorting Application

An AI-powered application that automatically categorizes, analyzes, and organizes emails based on their content.

## Features

- **Email Categorization**: Automatically sorts emails into categories (work, personal, promotional, etc.)
- **Content Analysis**: Extracts key information and summarizes email content
- **Performance Monitoring**: Dashboard to track sorting accuracy and processing metrics
- **Customizable Configuration**: Adaptable to different email categorization needs

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages (install with `pip install -r requirements.txt`)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/rohannagpure45/emailSorting.git
   cd emailSorting
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application:
   - Update `config.yml` with your settings

### Setting Up Credentials

1. Create a Google Cloud project and enable the Gmail API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API
   - Create OAuth 2.0 credentials
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the `config` directory

2. Get a Google Gemini API key for the AI features:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Add it to your `.env` file (see `.env.example`)

### Running the Application

Start the email sorting agent:
```
python main.py
```

Launch the performance dashboard:
```
./run_dashboard.py
```

## Dashboard

The application includes a monitoring dashboard built with Streamlit that provides:

- Real-time email processing statistics
- Category distribution visualization
- Performance metrics tracking
- Processing time analysis

You can generate sample data for testing the dashboard:
```
./dashboard/generate_sample_data.py
```

## Project Structure

- `agents/`: Core agent logic for email processing
- `dashboard/`: Performance monitoring dashboard
- `config/`: Configuration files and handlers

## License

This project is licensed under the MIT License - see the LICENSE file for details. 