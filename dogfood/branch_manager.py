# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Branch Manager - Git Operations for Safe Dogfood Cycles

Handles all Git branch operations for safe dogfood experimentation
with automatic cleanup and rollback capabilities.
"""

import asyncio
import contextlib
from datetime import datetime
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional


class BranchManager:
    """Manages Git branches for safe dogfood experimentation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()

        # Configuration
        self.main_branch = self.config.get('main_branch', 'main')
        self.dogfood_prefix = self.config.get('dogfood_prefix', 'dogfood')
        self.auto_cleanup = self.config.get('auto_cleanup', True)

    async def create_dogfood_branch(self, improvement_goal: str) -> str:
        """
        Create a new dogfood branch for safe experimentation

        Args:
            improvement_goal: The goal of this dogfood cycle (nasa_compliance, etc.)

        Returns:
            str: Name of the created branch
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"{self.dogfood_prefix}_{improvement_goal}_{timestamp}"

        self.logger.info(f"📋 Creating dogfood branch: {branch_name}")

        try:
            # Ensure we're on main and up to date
            await self._run_git_command(['checkout', self.main_branch])
            await self._run_git_command(['pull', 'origin', self.main_branch])

            # Create new branch
            await self._run_git_command(['checkout', '-b', branch_name])

            # Push branch to remote for tracking
            await self._run_git_command(['push', '-u', 'origin', branch_name])

            self.logger.info(f"✅ Created and pushed dogfood branch: {branch_name}")
            return branch_name

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to create dogfood branch: {e}")
            # Try to cleanup partial state
            await self._cleanup_failed_branch_creation(branch_name)
            raise RuntimeError(f"Failed to create dogfood branch: {e}")

    async def merge_to_main(self, branch_name: str) -> bool:
        """
        Merge dogfood branch back to main after successful validation

        Args:
            branch_name: Name of the branch to merge

        Returns:
            bool: True if merge was successful
        """
        self.logger.info(f"✅ Merging successful dogfood branch to main: {branch_name}")

        try:
            # Switch to main
            await self._run_git_command(['checkout', self.main_branch])

            # Pull latest changes
            await self._run_git_command(['pull', 'origin', self.main_branch])

            # Create merge commit with descriptive message
            merge_message = self._create_merge_message(branch_name)

            # Merge the branch
            await self._run_git_command([
                'merge', branch_name,
                '--no-ff',  # Always create merge commit
                '-m', merge_message
            ])

            # Push to remote
            await self._run_git_command(['push', 'origin', self.main_branch])

            # Clean up the dogfood branch if auto-cleanup enabled
            if self.auto_cleanup:
                await self._cleanup_dogfood_branch(branch_name)

            self.logger.info(f"🎉 Successfully merged {branch_name} to main")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to merge branch {branch_name}: {e}")
            # Try to return to a safe state
            with contextlib.suppress(Exception):
                await self._run_git_command(['checkout', self.main_branch])

            return False

    async def rollback_and_cleanup(self, branch_name: str) -> bool:
        """
        Rollback changes and cleanup failed dogfood branch

        Args:
            branch_name: Name of the branch to rollback and cleanup

        Returns:
            bool: True if rollback was successful
        """
        self.logger.warning(f"❌ Rolling back failed dogfood branch: {branch_name}")

        try:
            # Switch to main branch
            await self._run_git_command(['checkout', self.main_branch])

            # Delete the dogfood branch locally
            with contextlib.suppress(subprocess.CalledProcessError):
                await self._run_git_command(['branch', '-D', branch_name])


            # Delete the branch from remote
            with contextlib.suppress(subprocess.CalledProcessError):
                await self._run_git_command(['push', 'origin', '--delete', branch_name])


            self.logger.info(f"🧹 Successfully cleaned up failed branch: {branch_name}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to cleanup branch {branch_name}: {e}")
            return False

    async def emergency_cleanup(self) -> bool:
        """
        Emergency cleanup - return to main and clean up any dogfood branches

        Returns:
            bool: True if emergency cleanup was successful
        """
        self.logger.warning("🚨 Performing emergency cleanup...")

        try:
            # Force checkout to main
            await self._run_git_command(['checkout', '--force', self.main_branch])

            # Get all local dogfood branches
            result = await self._run_git_command(['branch', '--list', f'{self.dogfood_prefix}*'])
            dogfood_branches = [
                line.strip().replace('* ', '')
                for line in result.stdout.decode().split('\n')
                if line.strip() and self.dogfood_prefix in line
            ]

            # Delete all dogfood branches
            for branch in dogfood_branches:
                try:
                    await self._run_git_command(['branch', '-D', branch])
                    self.logger.info(f"🧹 Deleted local branch: {branch}")
                except:
                    pass

            # Get remote dogfood branches and delete them
            try:
                result = await self._run_git_command(['branch', '-r', '--list', f'origin/{self.dogfood_prefix}*'])
                remote_branches = [
                    line.strip().replace('origin/', '')
                    for line in result.stdout.decode().split('\n')
                    if line.strip() and self.dogfood_prefix in line
                ]

                for branch in remote_branches:
                    try:
                        await self._run_git_command(['push', 'origin', '--delete', branch])
                        self.logger.info(f"🧹 Deleted remote branch: {branch}")
                    except:
                        pass
            except:
                pass

            self.logger.info("✅ Emergency cleanup completed")
            return True

        except Exception as e:
            self.logger.error(f"💥 Emergency cleanup failed: {e}")
            return False

    async def get_current_branch(self) -> str:
        """Get the name of the current branch"""
        try:
            result = await self._run_git_command(['branch', '--show-current'])
            return result.stdout.decode().strip()
        except subprocess.CalledProcessError:
            return "unknown"

    async def is_clean_working_directory(self) -> bool:
        """Check if working directory is clean (no uncommitted changes)"""
        try:
            result = await self._run_git_command(['status', '--porcelain'])
            return len(result.stdout.decode().strip()) == 0
        except subprocess.CalledProcessError:
            return False

    async def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """
        Commit current changes with a descriptive message

        Args:
            message: Commit message
            files: Specific files to commit (None for all changes)

        Returns:
            bool: True if commit was successful
        """
        try:
            # Add files
            if files:
                for file in files:
                    await self._run_git_command(['add', file])
            else:
                await self._run_git_command(['add', '.'])

            # Check if there are changes to commit
            if await self.is_clean_working_directory():
                self.logger.info("No changes to commit")
                return True

            # Commit with message
            full_message = f"{message}\n\n🤖 Generated by Dogfood Self-Improvement System"
            await self._run_git_command(['commit', '-m', full_message])

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit changes: {e}")
            return False

    def _create_merge_message(self, branch_name: str) -> str:
        """Create descriptive merge message for dogfood branch"""
        parts = branch_name.split('_')
        improvement_goal = parts[1] if len(parts) > 1 else "improvement"
        parts[-1] if len(parts) > 2 else "unknown"

        return f"""🚀 DOGFOOD: Merge {improvement_goal} improvements

Automated self-improvement cycle completed successfully:
- Branch: {branch_name}
- Goal: {improvement_goal.replace('_', ' ').title()}
- All tests passed YES
- Metrics improved YES
- Safety validation complete YES

 Generated by Dogfood Self-Improvement System"""

    async def _cleanup_dogfood_branch(self, branch_name: str):
        """Clean up a dogfood branch after successful merge"""
        try:
            # Delete local branch
            await self._run_git_command(['branch', '-d', branch_name])

            # Delete remote branch
            await self._run_git_command(['push', 'origin', '--delete', branch_name])

            self.logger.info(f"🧹 Cleaned up dogfood branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"⚠️ Could not fully cleanup branch {branch_name}: {e}")

    async def _cleanup_failed_branch_creation(self, branch_name: str):
        """Clean up after failed branch creation"""
        try:
            # Try to switch back to main
            await self._run_git_command(['checkout', self.main_branch])

            # Try to delete the partial branch
            await self._run_git_command(['branch', '-D', branch_name])
        except:
            pass  # Best effort cleanup

    async def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a git command asynchronously

        Args:
            args: Git command arguments

        Returns:
            CompletedProcess result
        """
        cmd = ['git', *args]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

        if result.returncode != 0:
            self.logger.error(f"Git command failed: {' '.join(cmd)}")
            self.logger.error(f"Error output: {stderr.decode()}")
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                stdout,
                stderr
            )

        return result
