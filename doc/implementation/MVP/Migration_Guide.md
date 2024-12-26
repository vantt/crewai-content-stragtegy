# Migration Guide

## Overview
This guide outlines how to incrementally migrate our current content marketing system to the new framework-aligned version while maintaining system stability.

## Current System State

### Components in Use
1. Agent System:
   - StrategyAnalyst (src/agents/strategy_analyst.py)
   - MarketSkeptic (src/agents/strategy_skeptic.py)
   - StrategyDebate (src/agents/strategy_debate.py)

2. Core Systems:
   - Event System (src/core/events.py)
   - State Management (src/core/state.py)
   - Workflow Management (src/core/workflow.py)

3. UI Components:
   - Chat History (src/ui/chat_history.py)
   - Debate View (src/ui/debate.py)
   - Metrics View (src/ui/metrics.py)

## Technical Dependencies

### Current Dependencies
```json
{
  "required": {
    "streamlit": "^1.24.0",
    "crewai": "latest",
    "python": "^3.9.0"
  },
  "development": {
    "pytest": "^7.0.0",
    "black": "^22.0.0",
    "mypy": "^1.0.0"
  }
}
```

### New Dependencies Needed
```json
{
  "required": {
    "streamlit-chat": "^0.1.0",
    "pydantic": "^2.0.0",
    "asyncio": "^3.4.3"
  },
  "development": {
    "pytest-asyncio": "^0.21.0",
    "pytest-cov": "^4.1.0"
  }
}
```

## Migration Strategy

### 1. Preparation Phase
1. Code Backup:
   ```bash
   # Create backup branch
   git checkout -b backup/pre-mvp
   git push origin backup/pre-mvp
   ```

2. Environment Setup:
   ```bash
   # Create new virtual environment
   python -m venv venv-mvp
   source venv-mvp/bin/activate
   pip install -r requirements.txt
   ```

3. Testing Environment:
   ```bash
   # Set up test database
   python scripts/setup_test_env.py
   pytest tests/
   ```

### 2. Stage 1 Migration: Human Integration

#### Step 1: UI Enhancement
1. Backup current UI:
   ```bash
   cp src/ui/chat_history.py src/ui/chat_history.bak
   cp src/ui/debate.py src/ui/debate.bak
   ```

2. Implement changes:
   - Add framework context
   - Enhance chat interface
   - Add input handling
   - Update tests

3. Validation:
   ```bash
   pytest tests/ui/
   streamlit run src/examples/test_chat.py
   ```

#### Step 2: Event System Update
1. Extend event system:
   - Add human events
   - Add framework events
   - Update handlers
   - Update tests

2. Validation:
   ```bash
   pytest tests/core/test_events.py
   ```

### 3. Stage 2 Migration: Agent Adaptation

#### Step 1: Agent Enhancement
1. Backup current agents:
   ```bash
   cp -r src/agents/strategy_* src/agents/backup/
   ```

2. Implement changes:
   - Add framework awareness
   - Update debate protocol
   - Enhance evidence handling
   - Update tests

3. Validation:
   ```bash
   pytest tests/agents/
   ```

#### Step 2: Integration
1. Update orchestrator:
   - Add framework support
   - Update workflow
   - Enhance coordination
   - Update tests

2. Validation:
   ```bash
   pytest tests/integration/
   ```

### 4. Stage 3 Migration: Framework Implementation

#### Step 1: Core Updates
1. Extend state management:
   - Add framework state
   - Add quality metrics
   - Update recovery
   - Update tests

2. Validation:
   ```bash
   pytest tests/core/
   ```

#### Step 2: Full Integration
1. System integration:
   - Connect all components
   - Add validation
   - Update documentation
   - Full testing

2. Validation:
   ```bash
   pytest
   streamlit run src/examples/test_full_system.py
   ```

## Risk Mitigation

### 1. Technical Risks
- **Data Loss**: Regular backups and version control
- **Performance**: Regular benchmarking and optimization
- **Integration**: Comprehensive testing at each step
- **Dependencies**: Version locking and compatibility checks

### 2. Operational Risks
- **System Downtime**: Staged deployment and rollback plans
- **User Impact**: Clear communication and training
- **Quality**: Regular validation and testing
- **Timeline**: Buffer periods and priority management

### 3. Rollback Procedures
```python
# Rollback script structure
def rollback_stage(stage: str):
    if stage == "ui":
        restore_ui_backup()
    elif stage == "agents":
        restore_agent_backup()
    elif stage == "framework":
        restore_framework_backup()
    
    run_validation_tests()
    notify_team()
```

## Success Validation

### 1. Technical Validation
- All tests passing
- Performance metrics met
- Error rates acceptable
- Code quality maintained

### 2. Functional Validation
- Framework alignment complete
- Human interaction working
- Agent adaptation successful
- Quality metrics met

### 3. User Validation
- Interface usable
- Workflow smooth
- Feedback positive
- Value demonstrated

## Next Steps
1. Review current system
2. Set up test environment
3. Begin Stage 1 migration
4. Monitor and validate
