"""
Email Formatter Module
Generates HTML email content from briefing data using Jinja2 templates
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger('morning-briefing.formatter')


class EmailFormatter:
    """Formats briefing data into HTML email"""

    def __init__(self, template_dir: str):
        """
        Initialize email formatter

        Args:
            template_dir: Directory containing email templates
        """
        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        logger.info(f"Email formatter initialized with template dir: {template_dir}")

    def format_briefing(
        self,
        user_name: str,
        calendar_events: List[Dict[str, Any]],
        commits: List[Dict[str, Any]],
        pull_requests: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        mentions: List[Dict[str, Any]],
        important_emails: List[Dict[str, Any]],
        blockers: List[Dict[str, Any]],
        priority_keywords: Dict[str, List[str]]
    ) -> str:
        """
        Format briefing data into HTML email

        Args:
            user_name: User's name
            calendar_events: List of calendar events
            commits: List of commits
            pull_requests: List of pull requests
            issues: List of issues
            mentions: List of GitHub mentions
            important_emails: List of important emails
            blockers: List of blocker items
            priority_keywords: Priority keyword configuration

        Returns:
            HTML email content
        """
        try:
            # Load template
            template = self.env.get_template('briefing_template.html')

            # Prepare data
            date_str = datetime.now().strftime('%A, %B %d, %Y')

            # Categorize pull requests
            open_prs = [pr for pr in pull_requests if pr['state'] == 'open']
            merged_prs = [pr for pr in pull_requests if pr['state'] == 'merged']

            # Filter open issues
            open_issues = [issue for issue in issues if issue['state'] == 'open']

            # Detect high priority events
            high_priority_events = [
                event for event in calendar_events
                if event.get('priority') == 'high'
            ]

            # Calculate stats
            total_additions = sum(commit.get('additions', 0) for commit in commits)
            total_deletions = sum(commit.get('deletions', 0) for commit in commits)

            # Render template
            html = template.render(
                user_name=user_name,
                date=date_str,
                calendar_events=calendar_events,
                commits=commits,
                open_prs=open_prs,
                merged_prs=merged_prs,
                open_issues=open_issues,
                mentions=mentions,
                important_emails=important_emails,
                blockers=blockers,
                high_priority_events=high_priority_events,
                total_additions=total_additions,
                total_deletions=total_deletions
            )

            logger.info("Successfully formatted briefing email")
            return html

        except Exception as e:
            logger.error(f"Failed to format briefing email: {e}")
            raise

    def format_error_notification(
        self,
        error_message: str,
        traceback_info: str = None
    ) -> str:
        """
        Format an error notification email

        Args:
            error_message: Error message
            traceback_info: Optional traceback information

        Returns:
            HTML email content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .error-box {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .error-title {{
                    color: #721c24;
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .error-message {{
                    color: #721c24;
                    margin-bottom: 15px;
                }}
                .traceback {{
                    background-color: #f1f1f1;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 15px;
                    font-family: monospace;
                    font-size: 12px;
                    white-space: pre-wrap;
                    overflow-x: auto;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    font-size: 14px;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <h1>Morning Briefing Error</h1>

            <div class="error-box">
                <div class="error-title">Error Occurred</div>
                <div class="error-message">
                    The morning briefing automation failed to run:
                </div>
                <p><strong>{error_message}</strong></p>
            </div>

            {f'<div class="traceback"><strong>Traceback:</strong><br>{traceback_info}</div>' if traceback_info else ''}

            <div class="footer">
                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Check logs at: <code>/Users/mando/.local/logs/morning-briefing.log</code></p>
            </div>
        </body>
        </html>
        """

        logger.info("Formatted error notification email")
        return html

    def generate_plain_text(
        self,
        user_name: str,
        calendar_events: List[Dict[str, Any]],
        commits: List[Dict[str, Any]],
        pull_requests: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ) -> str:
        """
        Generate plain text version of briefing (for email fallback)

        Args:
            user_name: User's name
            calendar_events: List of calendar events
            commits: List of commits
            pull_requests: List of pull requests
            issues: List of issues

        Returns:
            Plain text email content
        """
        lines = []
        lines.append(f"MORNING BRIEFING - {datetime.now().strftime('%A, %B %d, %Y')}")
        lines.append("=" * 60)
        lines.append(f"\nGood morning, {user_name}!\n")

        # Today's Schedule
        lines.append("\n📅 TODAY'S SCHEDULE")
        lines.append("-" * 60)
        if calendar_events:
            for event in calendar_events:
                lines.append(f"{event['time_str']}: {event['summary']}")
                if event.get('location'):
                    lines.append(f"  Location: {event['location']}")
        else:
            lines.append("No events scheduled for today.")

        # Yesterday's Work
        lines.append("\n\n✅ YESTERDAY'S ACCOMPLISHMENTS")
        lines.append("-" * 60)
        if commits:
            lines.append(f"\nCommits: {len(commits)}")
            for commit in commits[:10]:
                lines.append(f"  • {commit['repo_name']}: {commit['message']}")
        else:
            lines.append("No commits from yesterday.")

        # Pull Requests
        if pull_requests:
            lines.append(f"\nPull Requests:")
            for pr in pull_requests[:5]:
                state_emoji = "✅" if pr['state'] == 'merged' else "🔄"
                lines.append(f"  {state_emoji} {pr['repo_name']} #{pr['number']}: {pr['title']}")

        # Issues
        if issues:
            lines.append(f"\nOpen Issues: {len(issues)}")
            for issue in issues[:5]:
                lines.append(f"  • {issue['repo_name']} #{issue['number']}: {issue['title']}")

        lines.append("\n" + "=" * 60)
        lines.append("Generated by Morning Briefing Automation")

        return "\n".join(lines)


def create_email_formatter(template_dir: str) -> EmailFormatter:
    """
    Create and return an email formatter instance

    Args:
        template_dir: Directory containing email templates

    Returns:
        EmailFormatter instance
    """
    return EmailFormatter(template_dir)
