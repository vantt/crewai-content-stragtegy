# Content Strategy Debate System

A system that enables AI agents to debate content strategy topics with human interaction and feedback.

## Features

- AI-powered strategy debates
- Real-time event monitoring
- Human feedback integration
- Topic-focused discussions
- Interactive UI with Streamlit

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd content_strategy
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run src/app.py
```

2. Using the System:

   a. Select a Debate Topic:
   - Choose from predefined topics like Market Entry Strategy, Product Development, etc.
   - Provide market context information
   - Add any additional relevant details

   b. Start the Debate:
   - Click "Start Debate" to begin
   - Watch real-time interactions between agents
   - Monitor event stream and state changes

   c. Provide Feedback:
   - Review initial analysis
   - Comment on challenges
   - Evaluate final analysis
   - Rate debate quality

   d. View Results:
   - See debate progression
   - Review agent arguments
   - Track consensus achievement
   - Access feedback history

## System Components

### Core Components
- Event System: Handles real-time updates and communication
- State Management: Tracks debate and workflow states
- Agent Adapters: Integrates strategy agents with the system

### UI Components
- Event Stream: Shows real-time system events
- State View: Displays current system state
- Control Panel: Manages debate flow
- Debate View: Shows debate progress and results

### Agents
- Strategy Analyst: Develops and proposes strategies
- Market Skeptic: Challenges and validates proposals
- Debate Orchestrator: Manages overall debate flow

## Development

### Running Tests
```bash
pytest tests/
```

### Project Structure
```
src/
├── agents/         # Agent implementations
├── core/          # Core system components
├── ui/            # UI components
└── app.py         # Main application

tests/
├── agents/        # Agent tests
├── core/          # Core component tests
└── integration/   # Integration tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

[Your License Here]
