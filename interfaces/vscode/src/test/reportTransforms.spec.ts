import * as assert from 'assert';
import { convertUnifiedReportToAnalysisResult, convertUnifiedWorkspaceResult } from '../services/reportTransforms';

function testSingleFileTransform() {
    const sampleReport = {
        connascence_violations: [
            {
                id: 'v1',
                type: 'CoM',
                severity: 'high',
                description: 'Magic literal',
                file_path: '/tmp/example.py',
                line_number: 5
            },
            {
                id: 'v2',
                type: 'CoP',
                severity: 'medium',
                description: 'Parameter explosion',
                file_path: '/tmp/other.py',
                line_number: 12
            }
        ],
        duplication_clusters: [
            {
                id: 'c1',
                blocks: [
                    { file_path: '/tmp/example.py', start_line: 20, end_line: 30 },
                    { file_path: '/tmp/example.py', start_line: 40, end_line: 50 }
                ],
                similarity_score: 0.92,
                description: 'Duplicated logic',
                files_involved: ['/tmp/example.py']
            }
        ],
        nasa_violations: [
            {
                rule: 'PO10',
                message: 'Dynamic memory',
                file_path: '/tmp/example.py',
                line_number: 9,
                severity: 'critical',
                power_of_ten_rule: '4'
            }
        ],
        overall_quality_score: 0.77,
        parallel_processing: true,
        worker_count: 4,
        efficiency: 1.1,
        improvement_actions: ['Refactor duplicated logic'],
        priority_fixes: ['Remove global state']
    };

    const result = convertUnifiedReportToAnalysisResult(sampleReport, '/tmp/example.py', Date.now());
    assert.strictEqual(result.findings.length, 1, 'should filter to file specific violations');
    const clusters = result.duplicationClusters || [];
    const nasa = result.nasaCompliance;
    if (!nasa) {
        throw new Error('Missing NASA compliance data');
    }
    assert.ok(clusters[0].severity === 'critical', 'high similarity cluster severity');
    assert.strictEqual(nasa.violations.length, 1, 'NASA violations should surface');
    assert.strictEqual(result.summary.totalIssues, result.findings.length + clusters.length + nasa.violations.length);
}

function testWorkspaceTransform() {
    const sampleReport = {
        connascence_violations: [
            { id: 'v1', type: 'CoM', severity: 'high', description: 'Magic literal', file_path: '/tmp/a.py', line_number: 1 },
            { id: 'v2', type: 'CoP', severity: 'low', description: 'Parameters', file_path: '/tmp/b.py', line_number: 2 }
        ],
        duplication_clusters: [
            { id: 'c1', blocks: [{ file_path: '/tmp/a.py', start_line: 10, end_line: 15 }], similarity_score: 0.8, description: 'dup block', files_involved: ['/tmp/a.py'] }
        ],
        nasa_violations: [],
        overall_quality_score: 0.9
    };

    const workspace = convertUnifiedWorkspaceResult(sampleReport, Date.now());
    assert.strictEqual(workspace.summary.filesAnalyzed, 2, 'two files processed');
    assert.strictEqual(Object.keys(workspace.fileResults).length, 2, 'should return per-file results');
    const fileA = workspace.fileResults['/tmp/a.py'];
    assert.ok(fileA.summary.totalIssues >= 1, 'file should include issues');
}

function run() {
    testSingleFileTransform();
    testWorkspaceTransform();
    console.log('reportTransforms.spec.ts: all tests passed');
}

run();
