# Quick Start Guide

This guide will help you get started with the Content Strategy Debate System and verify your installation.

## Installation

1. Clone the repository and install dependencies:
```bash
git clone <repository-url>
cd content_strategy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## System Features

### 1. Core Features
- Multi-round debates
- Evidence tracking
- Consensus building
- Performance monitoring
- Error recovery

### 2. Visualization
- Real-time event stream
- Interactive metrics
- System health monitoring
- Recovery status
- Performance dashboards

### 3. Recovery & Monitoring
- Automatic error recovery
- System checkpoints
- Health monitoring
- Performance tracking
- Debug interfaces

## Running the System

### 1. Main Application
Launch the main Streamlit dashboard:
```bash
streamlit run src/app.py
```

The dashboard provides:
- Topic selection and context input
- Real-time debate monitoring
- System health visualization
- Recovery status tracking
- Performance metrics

### 2. System Test
Run the comprehensive test suite:
```bash
streamlit run src/examples/test_full_system.py
```

This demonstrates:
- Complete debate flow
- Recovery mechanisms
- System monitoring
- Performance testing

## Using the System

### 1. Starting a Debate
1. Select a topic from predefined options
2. Provide market context information
3. Click "Start Debate"
4. Monitor progress in real-time

### 2. Monitoring Progress
- Watch debate rounds in Event Stream
- Track system health in System Status
- Monitor recovery in Recovery Status
- View metrics in Analytics

### 3. Recovery Features
1. Automatic Recovery:
   - System automatically handles errors
   - Multiple recovery levels
   - State restoration
   - Performance optimization

2. Checkpoints:
   - Automatic state checkpoints
   - Manual checkpoint creation
   - Checkpoint restoration
   - Recovery verification

3. Health Monitoring:
   - Real-time health metrics
   - System performance tracking
   - Resource utilization
   - Error rate monitoring

### 4. Advanced Features
1. Metrics & Analytics:
   - Consensus tracking
   - Evidence quality metrics
   - Performance analytics
   - System health scores

2. Debug Tools:
   - Event inspection
   - State examination
   - Recovery tracking
   - Performance profiling

## System Components

### 1. Core Components
- Event System: Real-time event processing
- State Management: System state tracking
- Recovery System: Error handling and recovery
- Metrics System: Performance monitoring

### 2. UI Components
- Event Stream: Real-time updates
- Metrics View: Interactive analytics
- Recovery View: System health monitoring
- Debug View: System inspection

### 3. Testing Components
- Full System Test: Complete verification
- Recovery Test: Error handling verification
- Performance Test: System optimization
- Integration Test: Component interaction

## Troubleshooting

### Common Issues

1. Import Errors:
```
ModuleNotFoundError: No module named 'src'
```
Solution: Add project root to PYTHONPATH:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)  # Unix
set PYTHONPATH=%PYTHONPATH%;%CD%      # Windows
```

2. Streamlit Port Issues:
```
Port 8501 is already in use
```
Solution: Stop other Streamlit instances or use:
```bash
streamlit run src/app.py --server.port 8502
```

3. Recovery Issues:
```
Checkpoint directory not found
```
Solution: Create required directories:
```bash
mkdir -p data/checkpoints data/logs
```

### System Health Check

1. Run diagnostics:
```bash
streamlit run src/examples/test_full_system.py
```

2. Check system health:
- Monitor System Health tab
- Review error rates
- Check recovery status
- Verify performance metrics

3. Recovery Testing:
- Use Recovery Test option
- Simulate different errors
- Verify recovery actions
- Check system stability

### Getting Help

1. Check logs:
```bash
tail -f data/logs/system.log
tail -f data/logs/error.log
```

2. Run tests:
```bash
pytest tests/
```

3. Debug mode:
```bash
streamlit run src/app.py --log_level debug
```

## Best Practices

1. Regular Monitoring:
- Check system health frequently
- Monitor error rates
- Review performance metrics
- Track recovery status

2. Recovery Management:
- Allow automatic recovery
- Create manual checkpoints
- Monitor recovery success
- Review error patterns

3. Performance Optimization:
- Monitor resource usage
- Track response times
- Review metrics trends
- Optimize as needed

4. System Maintenance:
- Review logs regularly
- Clean old checkpoints
- Update configurations
- Monitor disk usage

## Next Steps

After basic setup:
1. Explore advanced features
2. Test recovery mechanisms
3. Monitor system health
4. Optimize performance

For more information:
- Implementation Plan
- API Documentation
- Test Documentation
- Recovery Guide
