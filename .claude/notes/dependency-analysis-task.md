# Dependency Analysis System - Task Notes

**Date Created**: 2025-11-05
**Status**: Planning Phase
**Priority**: High

## 🎯 Goal

Add comprehensive Salesforce component dependency analysis to the salesforce-skill toolkit.

## 🔍 Problem Statement

The skill currently lacks **dependency analysis capabilities** - a critical gap for enterprise Salesforce development:

- **Deployment Planning**: No way to understand component dependencies before deployment
- **Impact Assessment**: Can't assess risk of changing/removing components
- **Technical Debt**: No visibility into component coupling
- **Safe Refactoring**: Risk of breaking dependent components

## 📋 Requirements

### Core Scripts to Build

#### 1. `scripts/find_component_usage.py`
**Purpose**: Find where a specific component is used across the org

**Features**:
- Query MetadataComponentDependency via Tooling API
- Support multiple component types (Apex, Custom Objects, Fields, Flows)
- Show both "what uses this" and "what this uses"
- Output in markdown table + JSON formats
- Integration with report-manager.sh

**Usage**:
```bash
./scripts/find_component_usage.py MyApexClass production
./scripts/find_component_usage.py Account.CustomField__c staging --type Field
./scripts/find_component_usage.py --help
```

#### 2. `scripts/analyze_metadata_dependencies.py`
**Purpose**: Comprehensive dependency analysis for deployment planning

**Features**:
- Multi-component analysis
- Dependency graph generation
- Deployment order recommendations
- Risk assessment scoring
- Field usage across validation rules, workflows, page layouts
- Flow and process builder dependencies

**Usage**:
```bash
./scripts/analyze_metadata_dependencies.py "Class1,Class2,Object__c" myorg
./scripts/analyze_metadata_dependencies.py --from-file components.txt staging
```

#### 3. `scripts/deployment_impact_assessment.py`
**Purpose**: Pre-deployment impact analysis and risk scoring

**Features**:
- Analyze proposed changes for deployment impact
- Generate risk scores (Low/Medium/High/Critical)
- Identify breaking change scenarios
- Recommend deployment strategies
- Integration with existing deployment scripts

### Integration Points

#### A. Update SKILL.md
Add new section **"13. Dependency Analysis & Impact Assessment"**

#### B. Update deployment-guide.md
Add pre-deployment dependency checking best practices

#### C. Report Management Integration
- Use existing report-manager.sh framework
- Timestamped dependency reports
- Historical tracking of component relationships

#### D. CI/CD Integration
- Add templates to assets/ for GitHub Actions
- JSON output for automated pipeline decisions

## 🏗️ Technical Architecture

### Data Sources
1. **Tooling API**: MetadataComponentDependency object
2. **Static Analysis**: Regex parsing of Apex/VF/LWC files
3. **Configuration Queries**: Validation rules, workflows, page layouts
4. **Flow Metadata**: Process Builder and Lightning Flow definitions

### Query Patterns
```sql
-- Core dependency query
SELECT MetadataComponentId, MetadataComponentName, MetadataComponentType,
       RefMetadataComponentId, RefMetadataComponentName, RefMetadataComponentType
FROM MetadataComponentDependency
WHERE RefMetadataComponentName = 'ComponentName'

-- Field usage in validation rules
SELECT EntityDefinition.QualifiedApiName, DeveloperName, ValidationFormula
FROM ValidationRule
WHERE ValidationFormula LIKE '%FieldName%'

-- Field usage in workflows
SELECT TableEnumOrId, Name, Formula
FROM WorkflowRule
WHERE Formula LIKE '%FieldName%'
```

### Security Considerations
- **Input Validation**: Sanitize component names and types
- **Query Limits**: Respect SOQL governor limits
- **Timeout Protection**: 60+ second timeouts for large orgs
- **Rate Limiting**: Batch large dependency queries

### Performance Patterns
- **Metadata Caching**: Cache component metadata to reduce API calls
- **Parallel Queries**: Execute independent queries concurrently
- **Incremental Analysis**: Only re-analyze changed components

## 📊 Expected Outputs

### 1. Component Usage Report
```markdown
# Component Usage: MyApexClass

## Used By (3 components)
| Component | Type | Usage Context |
|-----------|------|---------------|
| TestClass | ApexClass | Unit test calls |
| MyController | ApexClass | Service layer call |
| MyFlow | Flow | Apex action call |

## Uses (5 dependencies)
| Component | Type | Relationship |
|-----------|------|-------------|
| Account | CustomObject | SOQL queries |
| Contact | CustomObject | DML operations |
| Utils | ApexClass | Static method calls |

## Risk Assessment: **Medium**
- 3 direct dependents found
- Used in active Flow (high risk)
- No validation rule dependencies (low risk)
```

### 2. Deployment Impact Report
```markdown
# Deployment Impact Assessment

## Components to Deploy: MyClass, MyTrigger, CustomField__c

## Deployment Order Recommendation:
1. CustomField__c (no dependencies)
2. MyClass (depends on CustomField__c)
3. MyTrigger (depends on MyClass)

## Risk Analysis:
- **HIGH RISK**: CustomField__c used in 12 validation rules
- **MEDIUM RISK**: MyClass called by active Process Builder
- **LOW RISK**: MyTrigger has adequate test coverage

## Recommended Actions:
- [ ] Backup validation rules before deployment
- [ ] Test Process Builder after deployment
- [ ] Monitor trigger execution in debug logs
```

## 🔧 Implementation Plan

### Phase 1: Core Foundation (Week 1)
- [ ] `find_component_usage.py` with basic Tooling API queries
- [ ] Integration with report-manager.sh
- [ ] Unit tests for query logic
- [ ] Documentation in SKILL.md

### Phase 2: Advanced Analysis (Week 2)
- [ ] `analyze_metadata_dependencies.py` with multi-component support
- [ ] Field usage analysis (validation rules, workflows)
- [ ] Deployment order recommendations
- [ ] Risk scoring algorithm

### Phase 3: Integration & Polish (Week 3)
- [ ] `deployment_impact_assessment.py`
- [ ] CI/CD templates and GitHub Actions integration
- [ ] Performance optimization and caching
- [ ] Comprehensive test suite

## 🎯 Success Criteria

### Functional
- [ ] Can find component usage across org in < 30 seconds
- [ ] Accurately identifies dependencies for major component types
- [ ] Provides actionable deployment recommendations
- [ ] Integrates seamlessly with existing skill workflows

### Quality
- [ ] Follows established skill patterns (security, error handling, documentation)
- [ ] Comprehensive test coverage (>80%)
- [ ] Clear documentation with usage examples
- [ ] No security vulnerabilities (validated by code-reviewer agent)

### User Experience
- [ ] Clear, actionable output format
- [ ] Integration with existing deployment scripts
- [ ] Helpful error messages and troubleshooting
- [ ] Performance suitable for daily use

## 🚨 Risks & Mitigations

### Risk 1: Tooling API Limitations
**Impact**: Some dependencies may not be captured by MetadataComponentDependency
**Mitigation**: Complement with static code analysis for comprehensive coverage

### Risk 2: Governor Limit Issues
**Impact**: Large orgs may hit SOQL limits during dependency analysis
**Mitigation**: Implement query batching and caching strategies

### Risk 3: Performance in Large Orgs
**Impact**: Dependency analysis may be too slow for large enterprise orgs
**Mitigation**: Incremental analysis, parallel processing, aggressive caching

## 📚 Research References

- [Salesforce Tooling API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/)
- [MetadataComponentDependency Object Reference](https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_metadatacomponentdependency.htm)
- [Deployment Dependencies Best Practices](https://help.salesforce.com/s/articleView?id=sf.deploy_overview.htm)

---

**Next Steps**:
1. Create feature branch `feat/dependency-analysis-system`
2. Start with `find_component_usage.py` implementation
3. Set up report framework integration
4. Add comprehensive tests

**Estimated Effort**: 2-3 weeks for complete implementation
**Business Value**: High - Addresses critical gap in enterprise Salesforce deployment workflows