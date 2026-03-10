#!/usr/bin/env python3
"""
Branch Tracking System for Phase Implementation Branches

This script tracks the status of phase implementation branches and their CI/CD status.
It provides a dashboard view of branch readiness for merge and helps identify issues
before they cause pipeline failures.
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import argparse


@dataclass
class BranchStatus:
    """Status of a phase implementation branch."""
    name: str
    latest_commit: str
    commit_message: str
    commit_date: str
    is_merged: bool
    merge_commit: Optional[str]
    ci_status: str  # pending, success, failure, cancelled
    ci_details: Dict
    last_test_run: Optional[str]
    issues: List[str]


class BranchTracker:
    """Tracks and manages phase implementation branches."""
    
    def __init__(self):
        self.phase_branches = [
            'phase_2_implementation',
            'phase_3_implementation', 
            'phase_4_implementation',
            'phase_5_implementation',
            'phase_6_implementation',
            'phase_7_implementation',
            'phase_8_implementation',
            'phase_9_implementation',
            'phase_10_implementation'
        ]
        self.status_file = '.branch-status.json'
    
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
    
    def get_branch_status(self, branch_name: str) -> BranchStatus:
        """Get the status of a specific branch."""
        print(f"Analyzing branch: {branch_name}")
        
        # Check if branch exists
        branch_exists = self.run_git_command(['rev-parse', '--verify', branch_name])
        if not branch_exists:
            return BranchStatus(
                name=branch_name,
                latest_commit="",
                commit_message="Branch does not exist",
                commit_date="",
                is_merged=False,
                merge_commit=None,
                ci_status="unknown",
                ci_details={},
                last_test_run=None,
                issues=["Branch does not exist"]
            )
        
        # Get latest commit info
        latest_commit = self.run_git_command(['rev-parse', branch_name])
        commit_message = self.run_git_command(['log', '-1', '--pretty=format:%s', branch_name])
        commit_date = self.run_git_command(['log', '-1', '--pretty=format:%ci', branch_name])
        
        # Check if branch is merged into develop
        is_merged = self.check_if_merged(branch_name, 'develop')
        merge_commit = None
        if is_merged:
            merge_commit = self.get_merge_commit(branch_name, 'develop')
        
        # Check CI status (simplified - would integrate with GitHub API in production)
        ci_status, ci_details = self.check_ci_status(branch_name)
        
        # Get last test run info
        last_test_run = self.get_last_test_run(branch_name)
        
        # Identify issues
        issues = self.identify_issues(branch_name, is_merged, ci_status)
        
        return BranchStatus(
            name=branch_name,
            latest_commit=latest_commit,
            commit_message=commit_message,
            commit_date=commit_date,
            is_merged=is_merged,
            merge_commit=merge_commit,
            ci_status=ci_status,
            ci_details=ci_details,
            last_test_run=last_test_run,
            issues=issues
        )
    
    def check_if_merged(self, branch: str, target_branch: str) -> bool:
        """Check if a branch has been merged into the target branch."""
        try:
            result = self.run_git_command(['merge-base', '--is-ancestor', branch, target_branch])
            return True
        except:
            return False
    
    def get_merge_commit(self, branch: str, target_branch: str) -> Optional[str]:
        """Get the merge commit that merged the branch into target."""
        # Find merge commits
        merge_commits = self.run_git_command([
            'log', '--merges', '--oneline', f'{target_branch}', 
            '--grep', f'Merge branch \'{branch}\''
        ])
        if merge_commits:
            return merge_commits.split('\n')[0].split()[0]
        return None
    
    def check_ci_status(self, branch: str) -> tuple[str, Dict]:
        """Check CI status for the branch (placeholder for GitHub API integration)."""
        # This would integrate with GitHub API in a real implementation
        # For now, we'll check local git status and basic validation
        
        # Check if branch is up to date with remote
        try:
            self.run_git_command(['fetch', 'origin', branch])
            local_commit = self.run_git_command(['rev-parse', branch])
            remote_commit = self.run_git_command(['rev-parse', f'origin/{branch}'])
            
            if local_commit != remote_commit:
                return "outdated", {"local_commit": local_commit, "remote_commit": remote_commit}
            
            return "pending", {"message": "Branch is up to date with remote"}
        except:
            return "unknown", {"message": "Could not check remote status"}
    
    def get_last_test_run(self, branch: str) -> Optional[str]:
        """Get the timestamp of the last test run for this branch."""
        # Check for recent commits that might indicate test runs
        try:
            # Look for commits in the last 24 hours
            recent_commits = self.run_git_command([
                'log', '--since="24 hours ago"', '--oneline', branch
            ])
            if recent_commits:
                return datetime.now().isoformat()
        except:
            pass
        return None
    
    def identify_issues(self, branch: str, is_merged: bool, ci_status: str) -> List[str]:
        """Identify potential issues with the branch."""
        issues = []
        
        if not is_merged and ci_status in ['failure', 'cancelled']:
            issues.append(f"CI status is {ci_status} - should be fixed before merge")
        
        if not is_merged:
            # Check for untracked files that might cause issues
            untracked = self.run_git_command(['status', '--porcelain', '--ignored=no'])
            if untracked:
                issues.append("Branch has untracked files that should be committed")
        
        # Check for merge conflicts potential
        try:
            self.run_git_command(['merge-base', '--is-ancestor', branch, 'develop'])
        except:
            issues.append("Branch may have merge conflicts with develop")
        
        return issues
    
    def generate_status_report(self) -> Dict:
        """Generate a comprehensive status report for all phase branches."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "repository": self.run_git_command(['remote', 'get-url', 'origin']),
            "current_branch": self.run_git_command(['branch', '--show-current']),
            "branches": {}
        }
        
        for branch in self.phase_branches:
            status = self.get_branch_status(branch)
            report["branches"][branch] = asdict(status)
        
        return report
    
    def print_dashboard(self, report: Dict):
        """Print a formatted dashboard of branch status."""
        print("\n" + "="*80)
        print("BRANCH STATUS DASHBOARD")
        print("="*80)
        print(f"Repository: {report['repository']}")
        print(f"Current Branch: {report['current_branch']}")
        print(f"Generated: {report['generated_at']}")
        print("\n" + "-"*80)
        
        for branch, status in report['branches'].items():
            print(f"\nBranch: {branch}")
            print(f"  Status: {status['ci_status']}")
            print(f"  Merged: {'Yes' if status['is_merged'] else 'No'}")
            print(f"  Latest Commit: {status['latest_commit'][:8]}")
            print(f"  Message: {status['commit_message'][:50]}{'...' if len(status['commit_message']) > 50 else ''}")
            print(f"  Issues: {len(status['issues'])}")
            
            if status['issues']:
                for issue in status['issues']:
                    print(f"    - {issue}")
            
            if status['is_merged'] and status['merge_commit']:
                print(f"  Merge Commit: {status['merge_commit'][:8]}")
    
    def save_status(self, report: Dict):
        """Save the status report to a file."""
        with open(self.status_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nStatus saved to {self.status_file}")
    
    def check_merge_readiness(self, branch: str) -> bool:
        """Check if a branch is ready for merge."""
        status = self.get_branch_status(branch)
        
        if status.is_merged:
            print(f"Branch {branch} is already merged into develop")
            return False
        
        if status.ci_status in ['failure', 'cancelled']:
            print(f"Branch {branch} has failing CI - fix issues before merge")
            return False
        
        if status.issues:
            print(f"Branch {branch} has {len(status.issues)} issues that should be resolved:")
            for issue in status.issues:
                print(f"  - {issue}")
            return False
        
        print(f"Branch {branch} appears ready for merge!")
        return True


def main():
    """Main entry point for the branch tracker."""
    parser = argparse.ArgumentParser(description='Track phase implementation branches')
    parser.add_argument('--check-branch', type=str, help='Check specific branch status')
    parser.add_argument('--merge-ready', type=str, help='Check if branch is ready for merge')
    parser.add_argument('--save', action='store_true', help='Save status to file')
    parser.add_argument('--dashboard', action='store_true', help='Show dashboard view')
    
    args = parser.parse_args()
    
    tracker = BranchTracker()
    
    if args.check_branch:
        status = tracker.get_branch_status(args.check_branch)
        print(f"\nStatus for {args.check_branch}:")
        print(f"  CI Status: {status.ci_status}")
        print(f"  Merged: {status.is_merged}")
        print(f"  Issues: {len(status.issues)}")
        for issue in status.issues:
            print(f"    - {issue}")
    
    elif args.merge_ready:
        tracker.check_merge_readiness(args.merge_ready)
    
    elif args.dashboard or not any([args.check_branch, args.merge_ready]):
        report = tracker.generate_status_report()
        tracker.print_dashboard(report)
        
        if args.save:
            tracker.save_status(report)


if __name__ == '__main__':
    main()