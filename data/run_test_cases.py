#!/usr/bin/env python3
"""
Run test cases for specified agents using OpenAI model from .env

Usage:
    python run_test_cases.py --agent_names insurance_claims retail_banking
"""

import argparse
import asyncio
import json
import importlib
import inspect
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from agent_runner import run_test_case_local


def load_test_case_classes(agent_name: str):
    """
    Dynamically import test case classes for a given agent.
    
    Args:
        agent_name: Name of the agent (e.g., "insurance_claims")
        
    Returns:
        Dictionary mapping test_id to test case class
    """
    module_path = f"{agent_name}.test_cases"
    
    try:
        test_cases_module = importlib.import_module(module_path)
    except ImportError as e:
        print(f"Error: Could not import {module_path}")
        print(f"  {e}")
        return {}
    
    # Collect all test case classes (exclude the base class)
    test_case_classes = [
        obj for name, obj in inspect.getmembers(test_cases_module, inspect.isclass)
        if name.startswith("TestCase") and obj.__module__ == module_path
    ]
    
    # Build a dict keyed by test_id or class name
    test_cases_by_id = {}
    for cls in test_case_classes:
        # Try to get test_id from class attributes
        test_id = getattr(cls, 'test_id', None)
        if not test_id:
            # Fallback to class name
            test_id = cls.__name__
        test_cases_by_id[test_id] = cls
    
    print(f"✓ Loaded {len(test_case_classes)} test case classes from {module_path}")
    return test_cases_by_id


def load_local_test_cases(
    agent_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Load local test cases from the file system for the specified agents.

    Args:
        agent_names: List of agent names (e.g., ["insurance_claims", "retail_banking"])

    Returns:
        List of test case examples
    """
    all_examples = []

    # Collect examples from all agents
    all_examples = []
    
    for agent_name in agent_names:
        print(f"\n📦 Loading test cases for: {agent_name}")
        
        # Load test case classes for this agent
        test_cases_by_id = load_test_case_classes(agent_name)
        
        if not test_cases_by_id:
            print(f"  ⚠️  No test cases found for {agent_name}, skipping")
            continue
        
        # Prepare examples for this agent
        for test_id, test_cls in test_cases_by_id.items():
            # Instantiate test case to get its attributes
            test_instance = test_cls()
            
            # Get expected tool sequence - try multiple attribute names
            expected_sequence = getattr(test_instance, 'expected_tool_sequence', [])
            if not expected_sequence:
                # Try expected_tool_calls and extract just the names
                expected_tool_calls = getattr(test_instance, 'expected_tool_calls', [])
                if expected_tool_calls:
                    # Convert from list of dicts with 'name' to list of strings
                    expected_sequence = [call['name'] if isinstance(call, dict) and 'name' in call else str(call) 
                                       for call in expected_tool_calls]
            
            # Get input data - try multiple attribute names
            sample_input = getattr(test_instance, 'input_data', {})
            if not sample_input:
                sample_input = getattr(test_instance, 'sample_input_data', {})
            
            example = {
                "inputs": {
                    "test_id": test_id,
                    "agent_name": agent_name,  # Store agent_name in inputs for per-example loading
                    "input_data": sample_input
                },
                "outputs": {
                    "expected_tool_sequence": expected_sequence,
                    "expected_workflow_completed": True
                },
                "metadata": {
                    "test_case_class": test_cls.__name__,
                    "agent_name": agent_name  # Also keep in metadata for filtering
                }
            }
            all_examples.append(example)
        
        print(f"  ✓ Added {len(test_cases_by_id)} test cases from {agent_name}")
    
    if not all_examples:
        print("\n❌ No test cases found across any agents")
        return
    
    return all_examples


def run_local_testcases(
    inputs: Dict[str, Any],
    max_turns: int = 99,
    test_agent_llm_model = None,
    verbose: bool = False,
    system_prompt: Optional[str] = None,
    agent_type: Optional[str] = None,
) -> None:

    if test_agent_llm_model:
        print(f"✓ Will use test agent LLM: {test_agent_llm_model} (initialized per worker)")
    
    test_id = inputs.get('test_id')
    agent_name = inputs.get('agent_name')
    input_data = inputs.get('input_data', {})
    
    if not agent_name:
        return {
            "error": "Missing agent_name in inputs",
            "task_success": False,
            "trajectory_accuracy": False,
            "tool_sequence_match": False
        }
    
    # Load test cases for this agent (each worker loads independently)
    print(f"  [Worker] Loading test cases for agent: {agent_name}")
    test_cases_by_id = load_test_case_classes(agent_name)
    
    if not test_cases_by_id:
        return {
            "error": f"No test cases found for agent {agent_name}",
            "task_success": False,
            "trajectory_accuracy": False,
            "tool_sequence_match": False
        }
    
    # Get the test case class
    test_cls = test_cases_by_id.get(test_id)
    if not test_cls:
        return {
            "error": f"Test case {test_id} not found for agent {agent_name}",
            "task_success": False,
            "trajectory_accuracy": False,
            "tool_sequence_match": False
        }
    
    
    # Instantiate and run test case
    test_instance = test_cls()
    
    # try:
    # Run the test case using agent_runner
    agent_result, tools = run_test_case_local(
        test_case_instance=test_instance,
        input_data=input_data,
        max_turns=max_turns,
        test_agent_llm=test_agent_llm_model,
        verbose=verbose,
        system_prompt=system_prompt,
        agent_type=agent_type
    )

# # Return the outputs portion (LangSmith will compare this to expected outputs)
# # Also include metadata for additional tracking
    return agent_result, tools  
        
    # except Exception as e:
    #     return {
    #         "error": str(e),
    #         "agent_name": agent_name
    #     }, None
    
## async version of run_local_testcases
async def run_local_testcases_async(    
        inputs: Dict[str, Any],
        max_turns: int = 99,
        test_agent_llm_model = None,
        verbose: bool = False,
        system_prompt: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> None:
    return await asyncio.to_thread(
        run_local_testcases,
        inputs,
        max_turns,
        test_agent_llm_model,
        verbose,
        system_prompt,
        agent_type
    )



async def main(agent_names: List[str], max_turns: int = 20, verbose: bool = True):
    """
    Main function to run test cases from the data folder.

    This script loads test cases for specified agents and runs them using
    the OpenAI model configuration from .env file.

    Args:
        agent_names: List of agent names to test (e.g., ["banking_customer_onboarding"])
        max_turns: Maximum number of turns for the agent (default: 20)
        verbose: Whether to print verbose output (default: True)
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get OpenAI configuration from environment variables
    openai_api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('BASE_URL')
    model_name = os.getenv('MODEL_NAME')

    if not openai_api_key or not base_url or not model_name:
        print("❌ Error: Missing required environment variables")
        print("   Please ensure .env file contains: OPENAI_API_KEY, BASE_URL, MODEL_NAME")
        return

    print(f"✓ Loaded configuration from .env")
    print(f"  Model: {model_name}")
    print(f"  Base URL: {base_url}")

    # Initialize OpenAI model
    model_agent = ChatOpenAI(
        model=model_name,
        openai_api_key=openai_api_key,
        openai_api_base=base_url,
        temperature=0
    )

    print(f"✓ Initialized OpenAI model: {model_name}\n")

    print(f"Loading test cases for agents: {agent_names}")

    # Load test cases
    testcases = load_local_test_cases(agent_names)

    if not testcases:
        print("❌ No test cases found")
        return

    print(f"\n✓ Loaded {len(testcases)} test case(s)\n")
    print("=" * 60)
    print("Running test case...")
    print("=" * 60)

    # Run the first test case
    result, tools = await run_local_testcases_async(
        testcases[0]["inputs"],
        test_agent_llm_model=model_agent,
        system_prompt=None,
        verbose=verbose,
        max_turns=max_turns,
        agent_type="staticremem"
    )

    print("\n" + "=" * 60)
    print("Test Case Results")
    print("=" * 60)
    print(f"Completed: {result.completed}")
    print(f"Turns: {result.turns}")
    print(f"Total messages: {len(result.messages)}")
    print(f"Tools available: {len(tools)}")

    return result, tools


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run test cases for specified agents using OpenAI model from .env"
    )
    parser.add_argument(
        '--agents',
        '-a',
        nargs='+',
        default=["banking_customer_onboarding"],
        help='List of agent names to test (default: banking_customer_onboarding)'
    )
    parser.add_argument(
        '--max-turns',
        '-m',
        type=int,
        default=20,
        help='Maximum number of turns for the agent (default: 20)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        default=True,
        help='Print verbose output (default: True)'
    )
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Disable verbose output'
    )

    args = parser.parse_args()

    # Handle verbose flag
    verbose = args.verbose and not args.quiet

    # Run the async main function with parsed arguments
    asyncio.run(main(
        agent_names=args.agents,
        max_turns=args.max_turns,
        verbose=verbose
    ))


