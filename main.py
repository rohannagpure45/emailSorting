import asyncio
import os
import sys
from agents.coordinator_agent import CoordinatorAgent
from utils.config_handler import ConfigHandler
from loguru import logger
import argparse
import json
from tabulate import tabulate

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("logs/app.log", rotation="1 day", level="DEBUG")

async def main():
    """Main entry point for the email sorting application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Email Sorting Agent")
    parser.add_argument("--batch", type=int, help="Number of emails to process")
    parser.add_argument("--config", type=str, default="config/config.json", help="Path to config file")
    parser.add_argument("--email", type=str, help="Process a single email by ID")
    parser.add_argument("--save-analysis", action="store_true", help="Save detailed analysis to files")
    parser.add_argument("--no-save-analysis", dest="save_analysis", action="store_false", help="Don't save analysis results")
    parser.add_argument("--detailed-output", action="store_true", help="Show detailed analysis in terminal output")
    parser.add_argument("--output-format", choices=["text", "json"], default="text", help="Output format for results")
    parser.set_defaults(save_analysis=None)
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_handler = ConfigHandler(args.config)
        config = config_handler.get_config()
        
        # Initialize coordinator
        coordinator = CoordinatorAgent()
        
        # Apply config to coordinator
        coordinator.batch_size = args.batch if args.batch else config.batch_size
        coordinator.confidence_threshold = config.confidence_threshold
        coordinator.auto_mark_as_read = config.auto_mark_as_read
        coordinator.save_analysis = args.save_analysis if args.save_analysis is not None else config.save_analysis
        
        # Create analysis results directory if needed
        if coordinator.save_analysis:
            os.makedirs("analysis_results", exist_ok=True)
        
        # Process emails
        if args.email:
            # Process a single email
            logger.info(f"Processing single email with ID: {args.email}")
            result = await coordinator.process_single_email(args.email)
            
            if args.output_format == "json":
                print(json.dumps(result, indent=2))
            else:
                print_email_result(result, args.detailed_output)
                
        else:
            # Process batch of emails
            logger.info(f"Starting email processing with batch size: {coordinator.batch_size}")
            result = await coordinator.process()
            
            # Print summary
            if result.get('error'):
                logger.error(f"Error during processing: {result['error']}")
            else:
                logger.info(f"Processed {result['processed']} emails")
                
                if args.output_format == "json":
                    print(json.dumps(result, indent=2))
                else:
                    print_summary(result, args.detailed_output)
                
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        return 1

def print_email_result(result, detailed=False):
    """Print a single email result in a user-friendly format."""
    print("\n" + "="*80)
    print(f"Email: {result.get('subject', 'No subject')}")
    print(f"Category: {result.get('category', 'Unknown')} (Confidence: {result.get('confidence', 0.0):.2f})")
    print(f"Label: {result.get('label_applied', 'None')}")
    print(f"Priority: {result.get('priority', 'Unknown')}")
    print(f"Sentiment: {result.get('sentiment', 'Unknown')}")
    print(f"Action Required: {'Yes' if result.get('action_required', False) else 'No'}")
    
    if detailed:
        print("\nSummary:")
        print(result.get('summary', 'No summary available'))
        
        if result.get('action_items'):
            print("\nAction Items:")
            for item in result.get('action_items', []):
                print(f"- {item}")
                
        if result.get('deadlines'):
            print("\nDeadlines:")
            for deadline in result.get('deadlines', []):
                print(f"- {deadline}")
                
        if result.get('enhanced_data'):
            print("\nEnhanced Data:")
            for key, value in result.get('enhanced_data', {}).items():
                if isinstance(value, list):
                    print(f"{key}:")
                    for item in value:
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
    
    print("="*80 + "\n")

def print_summary(result, detailed=False):
    """Print a summary of processed emails."""
    if not result.get('results'):
        print("No emails processed.")
        return
    
    # Basic table of results
    table_data = []
    for email in result.get('results', []):
        table_data.append([
            email.get('subject', 'No subject')[:30] + ('...' if len(email.get('subject', '')) > 30 else ''),
            email.get('category', 'Unknown'),
            email.get('priority', 'Unknown'),
            'Yes' if email.get('action_required', False) else 'No',
            email.get('sentiment', 'Unknown'),
            email.get('label_applied', 'None')
        ])
    
    headers = ["Subject", "Category", "Priority", "Action Req", "Sentiment", "Label"]
    print("\nProcessed Emails:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Print action required emails
    action_emails = [e for e in result.get('results', []) if e.get('action_required', False)]
    if action_emails:
        print("\nEmails Requiring Action:")
        for email in action_emails:
            print(f"- {email.get('subject', 'No subject')} ({email.get('category', 'Unknown')})")
            if detailed and email.get('action_items'):
                for item in email.get('action_items', []):
                    print(f"  * {item}")
    
    # Print high priority emails
    high_priority = [e for e in result.get('results', []) if e.get('priority', 'low') == 'high']
    if high_priority:
        print("\nHigh Priority Emails:")
        for email in high_priority:
            print(f"- {email.get('subject', 'No subject')} ({email.get('category', 'Unknown')})")

if __name__ == "__main__":
    # Ensure necessary directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Run the main async function
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 