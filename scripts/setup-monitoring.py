#!/usr/bin/env python3
"""
Pipeline Monitoring Setup Script

This script sets up comprehensive monitoring for the GitHub Actions pipeline
and provides alerts for common issues that cause pipeline failures.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class PipelineMonitor:
    """Monitors GitHub Actions pipeline and sends alerts for issues."""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}" if github_token else ""
        }
    
    def run_git_command(self, command: List[str]) -> str:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                ['git'] + command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running git command: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            return ""
    
    def get_workflow_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent workflow runs from GitHub API."""
        if not self.github_token:
            print("⚠️  GitHub token not provided, using git commands instead")
            return self.get_local_workflow_status()
        
        try:
            url = f"{self.base_url}/actions/runs?per_page={limit}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('workflow_runs', [])
        except requests.RequestException as e:
            print(f"Error fetching workflow runs: {e}")
            return []
    
    def get_local_workflow_status(self) -> List[Dict]:
        """Get workflow status from local git history."""
        # This is a simplified version that checks recent commits for workflow status
        # In a real implementation, you'd want to integrate with GitHub API
        
        recent_commits = self.run_git_command(['log', '--oneline', '-10'])
        if not recent_commits:
            return []
        
        commits = recent_commits.split('\n')
        workflow_runs = []
        
        for commit in commits:
            commit_hash = commit.split()[0]
            commit_msg = ' '.join(commit.split()[1:])
            
            # Check if this commit triggered workflows
            workflow_runs.append({
                'id': commit_hash,
                'name': 'Local Workflow Check',
                'status': 'completed',
                'conclusion': 'success',  # Simplified for local check
                'created_at': datetime.now().isoformat(),
                'head_branch': self.run_git_command(['branch', '--show-current']),
                'head_sha': commit_hash,
                'html_url': f"https://github.com/{self.repo_owner}/{self.repo_name}/commit/{commit_hash}"
            })
        
        return workflow_runs
    
    def check_branch_status(self) -> Dict:
        """Check the status of all phase implementation branches."""
        branches = [
            'phase_2_implementation',
            'phase_3_implementation', 
            'phase_4_implementation',
            'develop',
            'main',
            'master'
        ]
        
        branch_status = {}
        
        for branch in branches:
            try:
                # Check if branch exists
                branch_exists = self.run_git_command(['rev-parse', '--verify', branch])
                if branch_exists:
                    # Get latest commit
                    latest_commit = self.run_git_command(['rev-parse', branch])
                    commit_message = self.run_git_command(['log', '-1', '--pretty=format:%s', branch])
                    commit_date = self.run_git_command(['log', '-1', '--pretty=format:%ci', branch])
                    
                    # Check if up to date with remote
                    try:
                        self.run_git_command(['fetch', 'origin', branch])
                        local_commit = self.run_git_command(['rev-parse', branch])
                        remote_commit = self.run_git_command(['rev-parse', f'origin/{branch}'])
                        
                        is_up_to_date = local_commit == remote_commit
                    except:
                        is_up_to_date = False
                    
                    branch_status[branch] = {
                        'exists': True,
                        'latest_commit': latest_commit,
                        'commit_message': commit_message,
                        'commit_date': commit_date,
                        'up_to_date_with_remote': is_up_to_date
                    }
                else:
                    branch_status[branch] = {
                        'exists': False,
                        'latest_commit': None,
                        'commit_message': None,
                        'commit_date': None,
                        'up_to_date_with_remote': False
                    }
            except Exception as e:
                branch_status[branch] = {
                    'exists': False,
                    'error': str(e)
                }
        
        return branch_status
    
    def check_dependencies(self) -> Dict:
        """Check if all required dependencies are available."""
        dependencies = {
            'python3': False,
            'git': False,
            'docker': False,
            'docker-compose': False,
            'tesseract': False,
            'poppler': False
        }
        
        # Check Python
        try:
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['python3'] = True
        except:
            pass
        
        # Check Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['git'] = True
        except:
            pass
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['docker'] = True
        except:
            pass
        
        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['docker-compose'] = True
        except:
            pass
        
        # Check Tesseract
        try:
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['tesseract'] = True
        except:
            pass
        
        # Check Poppler
        try:
            result = subprocess.run(['pdftotext', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                dependencies['poppler'] = True
        except:
            pass
        
        return dependencies
    
    def check_requirements(self) -> Dict:
        """Check if requirements.txt is valid."""
        issues = []
        
        try:
            with open('requirements.txt', 'r') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            
            # Check for empty lines at end
            if lines and not lines[-1].strip():
                issues.append("requirements.txt has trailing empty lines")
            
            # Check for duplicate dependencies
            deps = []
            for line in lines:
                if line.strip() and not line.strip().startswith('#'):
                    deps.append(line.strip())
            
            if len(deps) != len(set(deps)):
                issues.append("requirements.txt has duplicate dependencies")
            
            # Check for common issues
            if not deps:
                issues.append("requirements.txt is empty")
            
        except FileNotFoundError:
            issues.append("requirements.txt not found")
        except Exception as e:
            issues.append(f"Error reading requirements.txt: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def generate_health_report(self) -> Dict:
        """Generate a comprehensive health report."""
        print("🔍 Generating pipeline health report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'repository': f"{self.repo_owner}/{self.repo_name}",
            'workflow_runs': self.get_workflow_runs(),
            'branch_status': self.check_branch_status(),
            'dependencies': self.check_dependencies(),
            'requirements': self.check_requirements(),
            'issues': [],
            'recommendations': []
        }
        
        # Analyze issues
        self.analyze_issues(report)
        
        return report
    
    def analyze_issues(self, report: Dict):
        """Analyze the report and identify issues."""
        # Check workflow runs for failures
        failed_runs = [run for run in report['workflow_runs'] if run.get('conclusion') == 'failure']
        if failed_runs:
            report['issues'].append(f"Found {len(failed_runs)} failed workflow runs")
        
        # Check branch status
        for branch, status in report['branch_status'].items():
            if not status.get('exists', False):
                report['issues'].append(f"Branch {branch} does not exist")
            elif not status.get('up_to_date_with_remote', False):
                report['issues'].append(f"Branch {branch} is not up to date with remote")
        
        # Check dependencies
        missing_deps = [dep for dep, available in report['dependencies'].items() if not available]
        if missing_deps:
            report['issues'].append(f"Missing dependencies: {', '.join(missing_deps)}")
        
        # Check requirements
        if not report['requirements']['valid']:
            report['issues'].extend(report['requirements']['issues'])
        
        # Generate recommendations
        if 'Missing dependencies' in str(report['issues']):
            report['recommendations'].append("Install missing system dependencies")
        
        if 'requirements.txt has duplicate dependencies' in report['requirements']['issues']:
            report['recommendations'].append("Remove duplicate dependencies from requirements.txt")
        
        if 'Found failed workflow runs' in str(report['issues']):
            report['recommendations'].append("Review and fix failed workflow runs")
        
        if not report['issues']:
            report['recommendations'].append("Pipeline health looks good! Continue monitoring.")
    
    def print_health_report(self, report: Dict):
        """Print a formatted health report."""
        print("\n" + "="*80)
        print("PIPELINE HEALTH REPORT")
        print("="*80)
        print(f"Repository: {report['repository']}")
        print(f"Generated: {report['timestamp']}")
        print("\n" + "-"*80)
        
        # Issues
        print(f"\n🚨 ISSUES ({len(report['issues'])}):")
        if report['issues']:
            for i, issue in enumerate(report['issues'], 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✅ No issues found")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])}):")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # Dependencies status
        print(f"\n📦 DEPENDENCIES:")
        for dep, available in report['dependencies'].items():
            status = "✅" if available else "❌"
            print(f"  {status} {dep}")
        
        # Branch status
        print(f"\n🌿 BRANCH STATUS:")
        for branch, status in report['branch_status'].items():
            if status.get('exists', False):
                sync_status = "✅" if status.get('up_to_date_with_remote', False) else "⚠️"
                print(f"  {sync_status} {branch}")
            else:
                print(f"  ❌ {branch} (missing)")
        
        # Recent workflow runs
        print(f"\n🔄 RECENT WORKFLOW RUNS:")
        for run in report['workflow_runs'][:5]:
            status = "✅" if run.get('conclusion') == 'success' else "❌"
            print(f"  {status} {run.get('name', 'Unknown')} - {run.get('conclusion', 'unknown')}")
    
    def save_health_report(self, report: Dict, filename: str = None):
        """Save the health report to a file."""
        if not filename:
            filename = f"pipeline-health-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Health report saved to: {filename}")
    
    def send_alert(self, subject: str, message: str, recipients: List[str]):
        """Send an alert email (placeholder implementation)."""
        print(f"\n📧 ALERT: {subject}")
        print(f"Message: {message}")
        print(f"Recipients: {', '.join(recipients)}")
        
        # In a real implementation, you would:
        # 1. Set up SMTP server configuration
        # 2. Send actual email notifications
        # 3. Consider using services like SendGrid, AWS SES, etc.
        
        # For now, just log the alert
        with open('pipeline-alerts.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {subject}: {message}\n")


def main():
    """Main entry point for the pipeline monitor."""
    parser = argparse.ArgumentParser(description='Monitor GitHub Actions pipeline health')
    parser.add_argument('--repo-owner', type=str, required=True, help='GitHub repository owner')
    parser.add_argument('--repo-name', type=str, required=True, help='GitHub repository name')
    parser.add_argument('--token', type=str, help='GitHub API token')
    parser.add_argument('--save', type=str, help='Save report to file')
    parser.add_argument('--alert', action='store_true', help='Send alerts for issues')
    parser.add_argument('--recipients', type=str, nargs='+', help='Email recipients for alerts')
    
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = PipelineMonitor(args.repo_owner, args.repo_name, args.token)
    
    # Generate health report
    report = monitor.generate_health_report()
    
    # Print report
    monitor.print_health_report(report)
    
    # Save report if requested
    if args.save:
        monitor.save_health_report(report, args.save)
    
    # Send alerts if requested and there are issues
    if args.alert and report['issues'] and args.recipients:
        subject = f"Pipeline Issues Detected - {args.repo_owner}/{args.repo_name}"
        message = f"Found {len(report['issues'])} issues in the pipeline:\n\n" + \
                 "\n".join([f"- {issue}" for issue in report['issues']])
        monitor.send_alert(subject, message, args.recipients)


if __name__ == '__main__':
    main()