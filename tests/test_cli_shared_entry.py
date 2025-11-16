from pathlib import Path

from analyzer.cli_entry import CLIAnalysisRequest, run_cli_analysis


def test_cli_analyze_json_output():
    target = Path('tests') / 'sample_for_cli.py'
    assert target.exists(), 'sample file should exist'

    request = CLIAnalysisRequest(input_path=str(target), mode='file')
    response = run_cli_analysis(request)

    assert response.schema_version == '2024-08-01'
    assert response.success is True
    assert response.metadata['policy'] == request.policy
    assert response.summary['total_violations'] >= 0
    assert 'generated_at' in response.metadata
