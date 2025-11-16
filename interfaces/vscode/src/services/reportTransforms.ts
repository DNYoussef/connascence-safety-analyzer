import * as path from 'path';
import { AnalysisResult, Finding, PerformanceMetrics, DuplicationCluster, NASAComplianceResult, SmartIntegrationResult } from './connascenceService';

export function mapSeverity(severity: string): 'critical' | 'major' | 'minor' | 'info' {
    const severityMap: { [key: string]: 'critical' | 'major' | 'minor' | 'info' } = {
        'critical': 'critical',
        'high': 'major',
        'medium': 'minor',
        'low': 'info',
        'error': 'critical',
        'warning': 'major',
        'info': 'info'
    };

    return severityMap[severity.toLowerCase()] || 'info';
}

export function calculateSeverityBreakdown(findings: Finding[]): {
    critical: number;
    major: number;
    minor: number;
    info: number;
} {
    return findings.reduce((acc, finding) => {
        acc[finding.severity]++;
        return acc;
    }, { critical: 0, major: 0, minor: 0, info: 0 });
}

export function calculateQualityScore(findings: Finding[]): number {
    if (findings.length === 0) return 100;

    const weights = { critical: 10, major: 5, minor: 2, info: 1 };
    const totalWeight = findings.reduce((sum, f) => sum + weights[f.severity], 0);

    return Math.max(0, 100 - totalWeight);
}

export function calculateOverallQualityScore(fileResults: { [filePath: string]: AnalysisResult }): number {
    const scores = Object.values(fileResults).map(r => r.qualityScore);
    return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 100;
}

export function calculateEnhancedQualityScore(
    findings: Finding[],
    duplicationClusters: DuplicationCluster[],
    nasaCompliance: NASAComplianceResult
): number {
    let baseScore = calculateQualityScore(findings);

    const duplicationPenalty = duplicationClusters.length * 5;
    baseScore = Math.max(0, baseScore - duplicationPenalty);

    const compliancePenalty = (1.0 - nasaCompliance.score) * 20;
    baseScore = Math.max(0, baseScore - compliancePenalty);

    return Math.round(baseScore);
}

export function calculateClusterSeverity(similarity: number): 'critical' | 'major' | 'minor' | 'info' {
    if (similarity >= 0.9) return 'critical';
    if (similarity >= 0.8) return 'major';
    if (similarity >= 0.7) return 'minor';
    return 'info';
}

export function calculateOverallRisk(report: any): 'low' | 'medium' | 'high' | 'critical' {
    const criticalViolations = (report.connascence_violations || []).filter((v: any) =>
        v.severity === 'critical'
    ).length;

    const highSimilarityClusters = (report.duplication_clusters || []).filter((c: any) =>
        c.similarity_score >= 0.9
    ).length;

    const nasaViolations = (report.nasa_violations || []).length;

    if (criticalViolations > 10 || highSimilarityClusters > 5 || nasaViolations > 20) {
        return 'critical';
    } else if (criticalViolations > 5 || highSimilarityClusters > 2 || nasaViolations > 10) {
        return 'high';
    } else if (criticalViolations > 0 || highSimilarityClusters > 0 || nasaViolations > 0) {
        return 'medium';
    }

    return 'low';
}

export function convertUnifiedReportToAnalysisResult(report: any, filePath: string, startTime: number): AnalysisResult {
    const findings: Finding[] = [];

    if (report.connascence_violations) {
        for (const violation of report.connascence_violations) {
            if (!violation.file_path || path.resolve(violation.file_path) !== path.resolve(filePath)) {
                continue;
            }

            findings.push({
                id: violation.id || `${violation.type}_${violation.line_number}`,
                type: violation.type || violation.rule_id,
                severity: mapSeverity(violation.severity),
                message: violation.description,
                file: violation.file_path,
                line: violation.line_number,
                column: violation.column_number,
                suggestion: violation.suggestion
            });
        }
    }

    const performanceMetrics: PerformanceMetrics = {
        analysisTime: Date.now() - startTime,
        parallelProcessing: report.parallel_processing || false,
        speedupFactor: report.speedup_factor || 1.0,
        workerCount: report.worker_count || 1,
        memoryUsage: report.peak_memory_mb || 0,
        efficiency: report.efficiency || 1.0
    };

    const duplicationClusters: DuplicationCluster[] = (report.duplication_clusters || []).map((cluster: any) => ({
        id: cluster.id,
        blocks: cluster.blocks.map((block: any) => ({
            file: block.file_path,
            startLine: block.start_line,
            endLine: block.end_line,
            content: block.content || '',
            hash: block.hash_signature || ''
        })),
        similarity: cluster.similarity_score,
        severity: calculateClusterSeverity(cluster.similarity_score),
        description: cluster.description,
        files: cluster.files_involved || []
    }));

    const nasaCompliance: NASAComplianceResult = {
        compliant: (report.nasa_compliance_score || 1.0) >= 0.8,
        score: report.nasa_compliance_score || 1.0,
        violations: (report.nasa_violations || []).map((v: any) => ({
            rule: v.rule,
            message: v.message,
            file: v.file_path || filePath,
            line: v.line_number || 0,
            severity: mapSeverity(v.severity),
            powerOfTenRule: v.power_of_ten_rule
        })),
        powerOfTenRules: report.power_of_ten_rules || []
    };

    const smartIntegrationResults: SmartIntegrationResult = {
        crossAnalyzerCorrelation: report.correlations || [],
        intelligentRecommendations: (report.improvement_actions || []).map((action: string, index: number) => ({
            priority: index < 2 ? 'high' as const : 'medium' as const,
            category: 'quality_improvement',
            description: action,
            impact: 'Improves code quality and maintainability',
            effort: 'medium' as const,
            suggestedActions: [action]
        })),
        qualityTrends: [{
            metric: 'overall_quality',
            current: report.overall_quality_score || 0.8,
            trend: 'stable' as const,
            projection: report.overall_quality_score || 0.8
        }],
        riskAssessment: {
            overallRisk: calculateOverallRisk(report),
            riskFactors: [],
            mitigation: report.priority_fixes || []
        }
    };

    return {
        findings,
        qualityScore: Math.round((report.overall_quality_score || 0.8) * 100),
        summary: {
            totalIssues: findings.length + duplicationClusters.length + nasaCompliance.violations.length,
            issuesBySeverity: calculateSeverityBreakdown(findings)
        },
        performanceMetrics,
        duplicationClusters,
        nasaCompliance,
        smartIntegrationResults
    };
}

export function convertUnifiedWorkspaceResult(report: any, startTime: number): {
    fileResults: { [filePath: string]: AnalysisResult },
    summary: { filesAnalyzed: number, totalIssues: number, qualityScore: number }
} {
    const fileResults: { [filePath: string]: AnalysisResult } = {};
    let totalIssues = 0;

    const violationsByFile = new Map<string, any[]>();
    if (report.connascence_violations) {
        for (const violation of report.connascence_violations) {
            const file = violation.file_path || 'unknown';
            if (!violationsByFile.has(file)) {
                violationsByFile.set(file, []);
            }
            violationsByFile.get(file)!.push(violation);
        }
    }

    for (const [file, violations] of violationsByFile) {
        const findings: Finding[] = violations.map(v => ({
            id: v.id || `${v.type}_${v.line_number}`,
            type: v.type || v.rule_id,
            severity: mapSeverity(v.severity),
            message: v.description,
            file: v.file_path,
            line: v.line_number,
            column: v.column_number,
            suggestion: v.suggestion
        }));

        const fileDuplicationClusters = (report.duplication_clusters || []).filter((cluster: any) =>
            cluster.files_involved && cluster.files_involved.includes(file)
        ).map((cluster: any) => ({
            id: cluster.id,
            blocks: cluster.blocks.filter((block: any) => block.file_path === file),
            similarity: cluster.similarity_score,
            severity: calculateClusterSeverity(cluster.similarity_score),
            description: cluster.description,
            files: [file]
        }));

        const fileNasaViolations = (report.nasa_violations || []).filter((v: any) =>
            v.file_path === file
        ).map((v: any) => ({
            rule: v.rule,
            message: v.message,
            file: v.file_path,
            line: v.line_number,
            severity: mapSeverity(v.severity),
            powerOfTenRule: v.power_of_ten_rule
        }));

        const performanceMetrics: PerformanceMetrics = {
            analysisTime: Date.now() - startTime,
            parallelProcessing: report.parallel_processing || false,
            speedupFactor: report.speedup_factor || 1.0,
            workerCount: report.worker_count || 1,
            memoryUsage: report.peak_memory_mb || 0,
            efficiency: report.efficiency || 1.0
        };

        const nasaCompliance: NASAComplianceResult = {
            compliant: fileNasaViolations.length === 0,
            score: Math.max(0, 1.0 - (fileNasaViolations.length * 0.1)),
            violations: fileNasaViolations,
            powerOfTenRules: []
        };

        const smartIntegrationResults: SmartIntegrationResult = {
            crossAnalyzerCorrelation: [],
            intelligentRecommendations: [],
            qualityTrends: [],
            riskAssessment: {
                overallRisk: findings.filter(f => f.severity === 'critical').length > 0 ? 'high' : 'low',
                riskFactors: [],
                mitigation: []
            }
        };

        const totalFileIssues = findings.length + fileDuplicationClusters.length + fileNasaViolations.length;

        fileResults[file] = {
            findings,
            qualityScore: calculateEnhancedQualityScore(findings, fileDuplicationClusters, nasaCompliance),
            summary: {
                totalIssues: totalFileIssues,
                issuesBySeverity: calculateSeverityBreakdown(findings)
            },
            performanceMetrics,
            duplicationClusters: fileDuplicationClusters,
            nasaCompliance,
            smartIntegrationResults
        };

        totalIssues += totalFileIssues;
    }

    return {
        fileResults,
        summary: {
            filesAnalyzed: Object.keys(fileResults).length,
            totalIssues,
            qualityScore: Math.round((report.overall_quality_score || 0.8) * 100)
        }
    };
}
