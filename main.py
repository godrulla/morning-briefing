#!/usr/bin/env python3
"""
Morning Briefing Automation
Main orchestration script that coordinates all services and generates the daily briefing

Author: Armando Diaz Silverio
Company: Exxede Investments
"""

import os
import sys
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Add modules directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from modules.config_loader import ConfigLoader
from modules.gmail_service import create_gmail_service
from modules.calendar_service import create_calendar_service
from modules.github_service import create_github_service
from modules.email_formatter import create_email_formatter


def setup_logging(log_file: str, level: str = 'INFO', console_output: bool = False):
    """
    Set up logging configuration

    Args:
        log_file: Path to log file
        level: Logging level
        console_output: Whether to also output to console
    """
    # Create log directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def safe_api_call(func, service_name: str, logger):
    """
    Wrapper for API calls with error handling

    Args:
        func: Function to call
        service_name: Name of the service for logging
        logger: Logger instance

    Returns:
        Function result or None on error
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"{service_name} API error: {str(e)}")
        logger.debug(traceback.format_exc())
        return None


def generate_briefing(config_loader: ConfigLoader, logger, dry_run: bool = False):
    """
    Generate and send the morning briefing

    Args:
        config_loader: Configuration loader instance
        logger: Logger instance
        dry_run: If True, don't send email, just log what would be sent

    Returns:
        True if successful, False otherwise
    """
    try:
        config = config_loader.config
        secrets = config_loader.secrets

        logger.info("=" * 60)
        logger.info("Starting morning briefing generation")
        logger.info("=" * 60)

        # Initialize services
        logger.info("Initializing services...")

        # Gmail service
        gmail_service = safe_api_call(
            lambda: create_gmail_service(
                config_loader.get_google_credentials_path(),
                config_loader.get_google_token_path()
            ),
            "Gmail",
            logger
        )

        if not gmail_service:
            raise Exception("Failed to initialize Gmail service")

        # Calendar service
        calendar_service = safe_api_call(
            lambda: create_calendar_service(
                config_loader.get_google_credentials_path(),
                config_loader.get_google_token_path(),
                config.get('user', {}).get('timezone', 'America/Santo_Domingo')
            ),
            "Calendar",
            logger
        )

        if not calendar_service:
            raise Exception("Failed to initialize Calendar service")

        # GitHub service
        github_service = safe_api_call(
            lambda: create_github_service(
                config_loader.get_github_token(),
                config.get('github', {}).get('username'),
                config.get('user', {}).get('timezone', 'America/Santo_Domingo')
            ),
            "GitHub",
            logger
        )

        if not github_service:
            raise Exception("Failed to initialize GitHub service")

        # Email formatter
        template_dir = SCRIPT_DIR / 'templates'
        formatter = create_email_formatter(str(template_dir))

        # Gather data
        logger.info("Gathering briefing data...")

        # Get calendar events
        logger.info("Fetching calendar events...")
        calendar_events = safe_api_call(
            lambda: calendar_service.get_todays_events(
                calendar_ids=config.get('calendar', {}).get('calendars', ['primary']),
                include_all_day=config.get('calendar', {}).get('show_all_day_events', True),
                include_declined=config.get('calendar', {}).get('include_declined', False)
            ),
            "Calendar",
            logger
        ) or []

        # Detect priorities for calendar events
        priority_keywords = config.get('priority_keywords', {})
        for event in calendar_events:
            event['priority'] = calendar_service.detect_priority(event, priority_keywords)

        logger.info(f"Found {len(calendar_events)} calendar events")

        # Get GitHub commits
        logger.info("Fetching GitHub commits...")
        commits = safe_api_call(
            lambda: github_service.get_recent_commits(
                days_back=config.get('github', {}).get('days_lookback', 1),
                organizations=config.get('github', {}).get('organizations', []),
                include_private=config.get('github', {}).get('include_private', True),
                max_per_repo=config.get('github_filters', {}).get('commits', {}).get('max_results', 10)
            ),
            "GitHub Commits",
            logger
        ) or []

        logger.info(f"Found {len(commits)} commits")

        # Get pull requests
        logger.info("Fetching pull requests...")
        pull_requests = safe_api_call(
            lambda: github_service.get_pull_requests(
                states=config.get('github_filters', {}).get('pull_requests', {}).get('states', ['open', 'merged']),
                organizations=config.get('github', {}).get('organizations', []),
                include_private=config.get('github', {}).get('include_private', True),
                days_back=config.get('github', {}).get('days_lookback', 1)
            ),
            "GitHub Pull Requests",
            logger
        ) or []

        logger.info(f"Found {len(pull_requests)} pull requests")

        # Get issues
        logger.info("Fetching issues...")
        issues = safe_api_call(
            lambda: github_service.get_issues(
                states=config.get('github_filters', {}).get('issues', {}).get('states', ['open']),
                organizations=config.get('github', {}).get('organizations', []),
                include_private=config.get('github', {}).get('include_private', True)
            ),
            "GitHub Issues",
            logger
        ) or []

        logger.info(f"Found {len(issues)} issues")

        # Get GitHub mentions
        logger.info("Fetching GitHub mentions...")
        mentions = safe_api_call(
            lambda: github_service.get_mentions(
                days_back=config.get('github', {}).get('days_lookback', 1),
                max_results=config.get('github_filters', {}).get('mentions', {}).get('max_results', 10)
            ),
            "GitHub Mentions",
            logger
        ) or []

        logger.info(f"Found {len(mentions)} mentions")

        # Get important emails
        logger.info("Fetching important emails...")
        important_emails = []
        if config.get('email_filters', {}).get('enabled', True):
            keywords = config.get('email_filters', {}).get('keywords', [])
            if keywords:
                important_emails = safe_api_call(
                    lambda: gmail_service.get_emails_with_keywords(
                        keywords=keywords,
                        days_back=config.get('email_filters', {}).get('days_lookback', 1),
                        max_results=config.get('email_filters', {}).get('max_results', 10)
                    ),
                    "Gmail Important Emails",
                    logger
                ) or []

        logger.info(f"Found {len(important_emails)} important emails")

        # Detect blockers
        logger.info("Detecting blockers...")
        blockers = safe_api_call(
            lambda: github_service.detect_blockers(
                blocker_keywords=config.get('blocker_keywords', []),
                organizations=config.get('github', {}).get('organizations', [])
            ),
            "GitHub Blockers",
            logger
        ) or []

        logger.info(f"Detected {len(blockers)} blockers")

        # Generate email
        logger.info("Generating email content...")
        html_content = formatter.format_briefing(
            user_name=config.get('user', {}).get('name', 'User'),
            calendar_events=calendar_events,
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
            mentions=mentions,
            important_emails=important_emails,
            blockers=blockers,
            priority_keywords=priority_keywords
        )

        # Generate plain text fallback
        plain_content = formatter.generate_plain_text(
            user_name=config.get('user', {}).get('name', 'User'),
            calendar_events=calendar_events,
            commits=commits,
            pull_requests=pull_requests,
            issues=issues
        )

        # Send email
        if dry_run:
            logger.info("DRY RUN MODE - Email would be sent to: " + config_loader.get_send_to_email())
            logger.info("Subject: " + config.get('email', {}).get('subject_prefix', 'Morning Briefing') +
                       f" - {datetime.now().strftime('%B %d, %Y')}")
            logger.info("Email content generated successfully")
            print("\n" + "=" * 60)
            print("DRY RUN SUCCESSFUL")
            print("=" * 60)
            print(f"Would send briefing to: {config_loader.get_send_to_email()}")
            print(f"Calendar events: {len(calendar_events)}")
            print(f"Commits: {len(commits)}")
            print(f"Pull requests: {len(pull_requests)}")
            print(f"Issues: {len(issues)}")
            print(f"Mentions: {len(mentions)}")
            print(f"Blockers: {len(blockers)}")
            print("=" * 60)
            return True

        logger.info("Sending email...")
        success = gmail_service.send_email(
            to=config_loader.get_send_to_email(),
            subject=config.get('email', {}).get('subject_prefix', 'Morning Briefing') +
                   f" - {datetime.now().strftime('%B %d, %Y')}",
            body_html=html_content,
            body_plain=plain_content
        )

        if success:
            logger.info("=" * 60)
            logger.info("Morning briefing sent successfully!")
            logger.info("=" * 60)
            return True
        else:
            logger.error("Failed to send morning briefing email")
            return False

    except Exception as e:
        logger.error(f"Fatal error generating briefing: {str(e)}")
        logger.error(traceback.format_exc())

        # Try to send error notification
        try:
            if gmail_service and not dry_run:
                error_html = formatter.format_error_notification(
                    error_message=str(e),
                    traceback_info=traceback.format_exc()
                )
                gmail_service.send_email(
                    to=config_loader.get_send_to_email(),
                    subject="Morning Briefing Error",
                    body_html=error_html
                )
                logger.info("Error notification sent")
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")

        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Morning Briefing Automation - Generate and send daily briefing email'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without sending email (for testing)'
    )
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Directory containing config files (default: script directory)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose console output'
    )

    args = parser.parse_args()

    # Determine config directory
    config_dir = args.config_dir if args.config_dir else str(SCRIPT_DIR)

    # Load configuration
    try:
        config_loader = ConfigLoader(config_dir)
        config_loader.load()
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    # Set up logging
    log_file = config_loader.get('logging.file', str(Path.home() / '.local/logs/morning-briefing.log'))
    log_level = config_loader.get('logging.level', 'INFO')
    console_output = args.verbose or config_loader.get('logging.console_output', False)

    logger = setup_logging(log_file, log_level, console_output)

    # Run briefing generation
    success = generate_briefing(config_loader, logger, args.dry_run)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
