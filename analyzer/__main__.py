"""
Main entry point for the analyzer module.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.core import ConnascenceAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Connascence Safety Analyzer')
    parser.add_argument('path', help='Path to analyze')
    parser.add_argument('--format', choices=['json', 'text'], default='text')
    parser.add_argument('--policy', help='Policy preset to use')
    
    args = parser.parse_args()
    
    analyzer = ConnascenceAnalyzer()
    violations = analyzer.analyze_directory(args.path)
    
    if args.format == 'json':
        import json
        print(json.dumps([{
            'type': v.violation_type,
            'file': str(v.file_path),
            'line': v.line_number,
            'message': v.description
        } for v in violations], indent=2))
    else:
        print(f"Found {len(violations)} violations:")
        for v in violations:
            print(f"  {v.violation_type} in {v.file_path}:{v.line_number} - {v.description}")

if __name__ == '__main__':
    main()