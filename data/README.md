# Test Cases Runner

This directory contains agent test cases and a script to run them using OpenAI-compatible LLM models.

## Quick Start

### 1. Configure Environment Variables

Create or update the `.env` file in the project root with your OpenAI-compatible API credentials:

```bash
OPENAI_API_KEY=your_api_key_here
BASE_URL=https://your-api-endpoint/api/llm
MODEL_NAME=your-model-name
```


### 2. Run Test Cases

```bash
cd data
python run_test_cases.py --agent_names <agent_name>
```

## Usage Examples

### Run a Single Agent
```bash
python run_test_cases.py --agent_names insurance_claims_intake
```

### Run Multiple Agents
```bash
python run_test_cases.py --agent_names insurance_claims_intake banking_customer_onboarding
```

### Customize Max Turns
```bash
python run_test_cases.py --agent_names insurance_claims_intake --max-turns 30
```

### Run Quietly (Less Verbose)
```bash
python run_test_cases.py --agent_names insurance_claims_intake --quiet
```

### Get Help
```bash
python run_test_cases.py --help
```

## Available Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--agent_names` | `-a` | List of agent names to test | `banking_customer_onboarding` |
| `--max-turns` | `-m` | Maximum number of agent turns | `20` |
| `--verbose` | `-v` | Enable verbose output | `True` |
| `--quiet` | `-q` | Disable verbose output | `False` |

## Available Agents

The following agent test cases are available in this directory:

- `banking_accounts_deposits`
- `banking_customer_onboarding`
- `banking_fraud_monitoring`
- `healthcare_patient_onboarding`
- `healthcare_prior_authorization`
- `insurance_claims_intake`
- `manufacturing_purchase_to_pay`

## Script Output

The script will display:

1. **Configuration Info**: Model name and API endpoint
2. **Test Case Loading**: Number of test cases loaded for each agent
3. **Execution Progress**: Turn-by-turn agent execution with tool calls
4. **Results Summary**: 
   - Completion status
   - Number of turns taken
   - Total messages exchanged
   - Number of tools available

### Example Output

```
Loading test cases for agents: ['insurance_claims_intake']

📦 Loading test cases for: insurance_claims_intake
✓ Loaded 10 test case classes from insurance_claims_intake.test_cases
  ✓ Added 10 test cases from insurance_claims_intake

✓ Loaded 10 test case(s)

============================================================
Running test case...
============================================================
🔄 === Turn 1 ===
🤖 Assistant: 
🛠️  Assistant made 2 tool call(s)
  📞 Tool Call: extract_loss_details
  ...

============================================================
Test Case Results
============================================================
Completed: True
Turns: 5
Total messages: 23
Tools available: 12
```

## Project Structure

```
data/
├── README.md                          # This file
├── run_test_cases.py                  # Main test runner script
├── agent_runner.py                    # Agent execution engine
├── system_tools_base.py               # Base class for test tools
├── banking_accounts_deposits/         # Agent test cases
│   ├── __init__.py
│   ├── test_cases.py
│   ├── agent_definition.yaml
│   └── test_cases.json
├── banking_customer_onboarding/
│   └── ...
├── insurance_claims_intake/
│   └── ...
└── [other agent directories...]
```

## Troubleshooting

### Import Errors

If you see import errors like `No module named 'XXX'`:

1. Make sure the virtual environment is activated:
   ```bash
   source ../venv/bin/activate
   ```

2. Verify required packages are installed:
   ```bash
   pip install -r ../requirements.txt
   ```

### No Test Cases Found

If you see "No test cases found":

1. Check that the agent name is correct (case-sensitive)
2. Verify the agent directory contains a `test_cases.py` file
3. Ensure all directories have `__init__.py` files

### API Connection Issues

If you see connection errors:

1. Verify your `.env` file has the correct credentials
2. Check that `BASE_URL` is accessible
3. Ensure `OPENAI_API_KEY` is valid and not expired

### Model Not Found

If you see model-related errors:

1. Verify `MODEL_NAME` in `.env` matches an available model
2. Check that your API key has access to the specified model

## Development

### Adding New Test Cases

1. Create a new directory under `data/` with your agent name
2. Add `__init__.py` to make it a Python package
3. Create `test_cases.py` with test case classes
4. Test case classes should:
   - Start with `TestCase` prefix
   - Inherit from `SystemToolsBaseClass`
   - Define methods that will be used as agent tools

Example:
```python
from system_tools_base import SystemToolsBaseClass

class TestCaseExample(SystemToolsBaseClass):
    def __init__(self):
        self.role = "You are a helpful assistant"
        self.goal = "Complete the task successfully"
        self.action_plan = {
            'assumptions': "...",
            'guidelines': "...",
            'success_criteria': "..."
        }
        self.input_data = {"query": "Example input"}
    
    def example_tool(self, param1: str) -> dict:
        """Tool description"""
        return {"result": "success"}
```

### Running in CI/CD

The script can be integrated into CI/CD pipelines:

```bash
#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Run test cases
cd data
python run_test_cases.py --agent_names insurance_claims_intake --quiet

# Check exit code
if [ $? -eq 0 ]; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Additional Resources

- **Agent Runner**: See `agent_runner.py` for the core agent execution logic
- **System Tools Base**: See `system_tools_base.py` for base tool functionality
- **Test Case Definitions**: Each agent directory contains `test_cases.json` with structured test data

## Support

For issues or questions, please refer to the main project documentation or contact the development team.
