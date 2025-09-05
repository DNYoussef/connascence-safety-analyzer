#!/usr/bin/env python3
"""
Dogfood CLI - Command Line Interface for Self-Improvement

Provides a CLI interface for running dogfood self-improvement cycles
on the Connascence Safety Analyzer codebase.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from dogfood import DogfoodController

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def run_dogfood_cycle(
    improvement_goal: str,
    safety_mode: str,
    verbose: bool
) -> int:
    """Run a complete dogfood improvement cycle"""
    
    print("🚀 Connascence Self-Improvement System (Dogfood Mode)")
    print("=" * 60)
    
    try:
        # Initialize controller
        config = {
            'max_changes_per_cycle': 3 if safety_mode == 'strict' else 5,
            'require_approval_for_risky': safety_mode == 'strict',
            'parallel_execution': True
        }
        
        controller = DogfoodController(config)
        
        print(f"🎯 Goal: {improvement_goal.replace('_', ' ').title()}")
        print(f"🛡️ Safety Mode: {safety_mode.title()}")
        print()
        
        # Run the improvement cycle
        result = await controller.run_improvement_cycle(
            improvement_goal=improvement_goal,
            safety_mode=safety_mode
        )
        
        # Display results
        print("📊 Dogfood Cycle Results")
        print("-" * 30)
        print(f"Success: {'✅' if result.success else '❌'}")
        print(f"Branch: {result.branch_name}")
        print(f"Improvements Applied: {len(result.improvements_applied)}")
        print(f"Tests Status: {'✅ All Passed' if result.test_results.get('all_passed') else '❌ Some Failed'}")
        print(f"Decision: {result.decision_reason}")
        print(f"Rollback Performed: {'Yes' if result.rollback_performed else 'No'}")
        
        if result.metrics_comparison:
            print(f"\n📈 Metrics Changes:")
            for metric, change in result.metrics_comparison.items():
                emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"  {emoji} {metric}: {change:+.3f}")
        
        print(f"\nTime: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return 0 if result.success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Dogfood cycle interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Dogfood cycle failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

async def show_status():
    """Show current dogfood system status"""
    from dogfood import BranchManager, MetricsTracker
    
    print("📊 Dogfood System Status")
    print("=" * 30)
    
    try:
        branch_manager = BranchManager()
        metrics_tracker = MetricsTracker()
        
        # Get current branch
        current_branch = await branch_manager.get_current_branch()
        is_clean = await branch_manager.is_clean_working_directory()
        
        print(f"Current Branch: {current_branch}")
        print(f"Is Dogfood Branch: {'✅' if current_branch.startswith('dogfood') else '❌'}")
        print(f"Working Directory: {'✅ Clean' if is_clean else '⚠️ Has Changes'}")
        
        # Get current metrics
        try:
            metrics = await metrics_tracker.capture_current_state()
            print(f"\n📊 Current Quality Metrics:")
            print(f"  Connascence Score: {metrics.connascence_score:.3f}")
            print(f"  Violations: {metrics.violation_count}")
            print(f"  NASA Compliance: {metrics.nasa_compliance:.3f}")
        except Exception as e:
            print(f"  ⚠️ Could not get metrics: {e}")
        
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
        return 1
    
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="🔗💥 Connascence Dogfood Self-Improvement System"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run dogfood improvement cycle')
    run_parser.add_argument(
        '--goal', 
        choices=['nasa_compliance', 'coupling_reduction', 'code_clarity', 'architectural_health'],
        default='coupling_reduction',
        help='Improvement goal (default: coupling_reduction)'
    )
    run_parser.add_argument(
        '--safety',
        choices=['strict', 'moderate', 'experimental'],
        default='strict',
        help='Safety mode (default: strict)'
    )
    run_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show dogfood system status')
    status_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Emergency command
    emergency_parser = subparsers.add_parser('emergency', help='Emergency cleanup')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(getattr(args, 'verbose', False))
    
    # Run appropriate command
    if args.command == 'run':
        return asyncio.run(run_dogfood_cycle(
            improvement_goal=args.goal,
            safety_mode=args.safety,
            verbose=args.verbose
        ))
    elif args.command == 'status':
        return asyncio.run(show_status())
    elif args.command == 'emergency':
        return asyncio.run(emergency_cleanup())
    else:
        parser.print_help()
        return 1

async def emergency_cleanup():
    """Emergency cleanup of dogfood system"""
    from dogfood import BranchManager
    
    print("🚨 Emergency Cleanup - Dogfood System")
    print("=" * 40)
    
    try:
        branch_manager = BranchManager()
        success = await branch_manager.emergency_cleanup()
        
        if success:
            print("✅ Emergency cleanup completed successfully")
            print("  - Returned to main branch")
            print("  - Cleaned up dogfood branches")
            return 0
        else:
            print("❌ Emergency cleanup failed")
            return 1
            
    except Exception as e:
        print(f"💥 Emergency cleanup error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())