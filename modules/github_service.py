"""
GitHub Service Module
Handles GitHub API interactions for retrieving commits, PRs, issues, and mentions
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from github import Github, GithubException
from github.Repository import Repository
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Issue import Issue

logger = logging.getLogger('morning-briefing.github')


class GitHubService:
    """GitHub API service for retrieving repository activity"""

    def __init__(self, access_token: str, username: str, timezone: str = 'America/Santo_Domingo'):
        """
        Initialize GitHub service

        Args:
            access_token: GitHub Personal Access Token
            username: GitHub username
            timezone: User's timezone
        """
        self.access_token = access_token
        self.username = username
        self.timezone = pytz.timezone(timezone)
        self.github = Github(access_token)
        self.user = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with GitHub and verify access"""
        try:
            self.user = self.github.get_user()
            logger.info(f"Authenticated as GitHub user: {self.user.login}")
        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise

    def get_recent_commits(
        self,
        days_back: int = 1,
        organizations: Optional[List[str]] = None,
        include_private: bool = True,
        max_per_repo: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent commits by the user

        Args:
            days_back: How many days back to search
            organizations: List of organization names to include
            include_private: Include private repositories
            max_per_repo: Maximum commits per repository

        Returns:
            List of commit dictionaries
        """
        try:
            since = datetime.now(self.timezone) - timedelta(days=days_back)
            all_commits = []

            # Get user's repositories
            repos = self.user.get_repos()

            for repo in repos:
                try:
                    # Skip if private and not including private
                    if repo.private and not include_private:
                        continue

                    # Skip if organizations specified and repo not in them
                    if organizations and repo.owner.login not in organizations:
                        if repo.owner.login != self.username:
                            continue

                    # Get commits by user since date
                    commits = repo.get_commits(author=self.user, since=since)

                    commit_count = 0
                    for commit in commits:
                        if commit_count >= max_per_repo:
                            break

                        commit_data = {
                            'repo_name': repo.full_name,
                            'repo_url': repo.html_url,
                            'message': commit.commit.message.split('\n')[0],  # First line only
                            'sha': commit.sha[:7],  # Short SHA
                            'url': commit.html_url,
                            'date': commit.commit.author.date,
                            'additions': commit.stats.additions,
                            'deletions': commit.stats.deletions,
                            'files_changed': len(commit.files)
                        }
                        all_commits.append(commit_data)
                        commit_count += 1

                except GithubException as e:
                    logger.warning(f"Failed to get commits from {repo.full_name}: {e}")
                    continue

            # Sort by date (newest first)
            all_commits.sort(key=lambda x: x['date'], reverse=True)

            logger.info(f"Retrieved {len(all_commits)} recent commits")
            return all_commits

        except GithubException as e:
            logger.error(f"Failed to retrieve commits: {e}")
            return []

    def get_pull_requests(
        self,
        states: List[str] = ['open'],
        organizations: Optional[List[str]] = None,
        include_private: bool = True,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's pull requests

        Args:
            states: PR states to include ('open', 'closed', 'merged', 'all')
            organizations: List of organization names to include
            include_private: Include private repositories
            days_back: Only include PRs updated in last N days (None for all)

        Returns:
            List of PR dictionaries
        """
        try:
            all_prs = []
            since = None

            if days_back:
                since = datetime.now(self.timezone) - timedelta(days=days_back)

            # Get user's repositories
            repos = self.user.get_repos()

            for repo in repos:
                try:
                    # Skip filters
                    if repo.private and not include_private:
                        continue

                    if organizations and repo.owner.login not in organizations:
                        if repo.owner.login != self.username:
                            continue

                    # Get PRs for each requested state
                    for state in states:
                        if state == 'merged':
                            # Merged PRs are closed with merged=true
                            prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
                        else:
                            prs = repo.get_pulls(state=state, sort='updated', direction='desc')

                        for pr in prs:
                            # Check if it's the user's PR
                            if pr.user.login != self.username:
                                continue

                            # Filter merged if requested
                            if state == 'merged' and not pr.merged:
                                continue

                            # Filter by date if specified
                            if since and pr.updated_at < since:
                                continue

                            pr_data = {
                                'repo_name': repo.full_name,
                                'repo_url': repo.html_url,
                                'number': pr.number,
                                'title': pr.title,
                                'url': pr.html_url,
                                'state': 'merged' if pr.merged else pr.state,
                                'created_at': pr.created_at,
                                'updated_at': pr.updated_at,
                                'merged_at': pr.merged_at,
                                'comments': pr.comments,
                                'review_comments': pr.review_comments,
                                'additions': pr.additions,
                                'deletions': pr.deletions,
                                'changed_files': pr.changed_files
                            }
                            all_prs.append(pr_data)

                except GithubException as e:
                    logger.warning(f"Failed to get PRs from {repo.full_name}: {e}")
                    continue

            # Sort by updated date (newest first)
            all_prs.sort(key=lambda x: x['updated_at'], reverse=True)

            logger.info(f"Retrieved {len(all_prs)} pull requests")
            return all_prs

        except GithubException as e:
            logger.error(f"Failed to retrieve pull requests: {e}")
            return []

    def get_issues(
        self,
        states: List[str] = ['open'],
        organizations: Optional[List[str]] = None,
        include_private: bool = True,
        assigned_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get issues assigned to or created by the user

        Args:
            states: Issue states to include ('open', 'closed', 'all')
            organizations: List of organization names to include
            include_private: Include private repositories
            assigned_only: Only show issues assigned to user

        Returns:
            List of issue dictionaries
        """
        try:
            all_issues = []

            # Use GitHub search for assigned issues
            if assigned_only:
                for state in states:
                    query = f"assignee:{self.username} type:issue state:{state}"

                    if organizations:
                        org_query = ' '.join([f"org:{org}" for org in organizations])
                        query += f" {org_query}"

                    issues = self.github.search_issues(query, sort='updated', order='desc')

                    for issue in issues:
                        # Skip if private and not including private
                        if issue.repository.private and not include_private:
                            continue

                        issue_data = {
                            'repo_name': issue.repository.full_name,
                            'repo_url': issue.repository.html_url,
                            'number': issue.number,
                            'title': issue.title,
                            'url': issue.html_url,
                            'state': issue.state,
                            'created_at': issue.created_at,
                            'updated_at': issue.updated_at,
                            'comments': issue.comments,
                            'labels': [label.name for label in issue.labels]
                        }
                        all_issues.append(issue_data)

            # Sort by updated date (newest first)
            all_issues.sort(key=lambda x: x['updated_at'], reverse=True)

            logger.info(f"Retrieved {len(all_issues)} issues")
            return all_issues

        except GithubException as e:
            logger.error(f"Failed to retrieve issues: {e}")
            return []

    def get_mentions(
        self,
        days_back: int = 1,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent mentions of the user in issues and PRs

        Args:
            days_back: How many days back to search
            max_results: Maximum number of results

        Returns:
            List of mention dictionaries
        """
        try:
            since = datetime.now(self.timezone) - timedelta(days=days_back)
            mentions = []

            # Search for mentions in issues and PRs
            query = f"mentions:{self.username} updated:>={since.strftime('%Y-%m-%d')}"
            results = self.github.search_issues(query, sort='updated', order='desc')

            count = 0
            for item in results:
                if count >= max_results:
                    break

                mention_data = {
                    'repo_name': item.repository.full_name,
                    'repo_url': item.repository.html_url,
                    'type': 'pull_request' if item.pull_request else 'issue',
                    'number': item.number,
                    'title': item.title,
                    'url': item.html_url,
                    'state': item.state,
                    'updated_at': item.updated_at,
                    'author': item.user.login
                }
                mentions.append(mention_data)
                count += 1

            logger.info(f"Retrieved {len(mentions)} mentions")
            return mentions

        except GithubException as e:
            logger.error(f"Failed to retrieve mentions: {e}")
            return []

    def detect_blockers(
        self,
        blocker_keywords: List[str],
        organizations: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect blocked or waiting items

        Args:
            blocker_keywords: Keywords that indicate blockers
            organizations: List of organization names to include

        Returns:
            List of potential blocker items
        """
        try:
            blockers = []

            # Search for issues with blocker keywords
            for keyword in blocker_keywords:
                query = f'"{keyword}" author:{self.username} type:issue state:open'

                if organizations:
                    org_query = ' '.join([f"org:{org}" for org in organizations])
                    query += f" {org_query}"

                results = self.github.search_issues(query, sort='updated', order='desc')

                for item in results:
                    blocker_data = {
                        'repo_name': item.repository.full_name,
                        'type': 'issue',
                        'number': item.number,
                        'title': item.title,
                        'url': item.html_url,
                        'updated_at': item.updated_at,
                        'reason': f"Contains '{keyword}'"
                    }

                    # Avoid duplicates
                    if not any(b['url'] == blocker_data['url'] for b in blockers):
                        blockers.append(blocker_data)

            logger.info(f"Detected {len(blockers)} potential blockers")
            return blockers

        except GithubException as e:
            logger.error(f"Failed to detect blockers: {e}")
            return []


def create_github_service(
    access_token: str,
    username: str,
    timezone: str = 'America/Santo_Domingo'
) -> GitHubService:
    """
    Create and return a GitHub service instance

    Args:
        access_token: GitHub Personal Access Token
        username: GitHub username
        timezone: User's timezone

    Returns:
        GitHubService instance
    """
    return GitHubService(access_token, username, timezone)
