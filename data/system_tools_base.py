from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI configuration from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')
model_name = os.getenv('MODEL_NAME')

if not openai_api_key or not base_url or not model_name:
    print("❌ Error: Missing required environment variables")
    print("   Please ensure .env file contains: OPENAI_API_KEY, BASE_URL, MODEL_NAME")

print(f"✓ Loaded configuration from .env")
print(f"  Model: {model_name}")
print(f"  Base URL: {base_url}")

# Initialize OpenAI model
html_llm = ChatOpenAI(
    model=model_name,
    openai_api_key=openai_api_key,
    openai_api_base=base_url,
    temperature=0
)

print(f"✓ Initialized OpenAI model: {model_name}\n")

print(f"Loading test cases for agents: {html_llm}")



class SystemToolsBaseClass:
    """Master base class containing common system tools for all test cases."""
    
    def __init__(self):
        # Optional: store context for LLM-HITL
        self._hitl_context = {}
        self._hitl_llm = html_llm
        
    def SUCCESS(self, message: str, result_data: dict = None) -> dict:
        """Signal successful operation/result"""
        print(f"--- SUCCESS ---")
        print(f"message: {message}, result_data: {result_data}")
        return {
            "exit_status": "success",
            "message": message,
            "data": result_data
        }

    def FAILED(self, message: str, error_details: dict = None) -> dict:
        """Report an operation failure/error"""
        print(f"--- FAILED ---")
        print(f"message: {message}, error_details: {error_details}")
        return {
            "exit_status": "failed",
            "message": message,
            "error": error_details
        }

    def CANCELLED(self, message: str, reason: str = None) -> dict:
        """Indicate process was cancelled/interrupted"""
        print(f"--- CANCELLED ---")
        print(f"message: {message}, reason: {reason}")
        return {
            "exit_status": "cancelled",
            "message": message,
            "reason": reason
        }

    def HUMAN_IN_THE_LOOP(self, ai_message: str) -> dict:
        """Escalate to human review - can be LLM-powered role-play"""
        print(f"--- HUMAN_IN_THE_LOOP ---")
        print(f"ai_message: {ai_message}")
        
        # Option 1: Static response (backward compatible)
        human_response = self._get_human_response(ai_message)
        
        return {
            "exit_status": "escalated",
            "ai_message": ai_message,
            "human_response": human_response
        }
    
    def _get_human_response(self, ai_message: str) -> str:
        """Generate human response - can be overridden for LLM-powered responses"""
        # Check if LLM-powered HITL is enabled
        if hasattr(self, '_hitl_llm') and self._hitl_llm is not None:
            return self._llm_powered_human_response(ai_message)
        else:
            # Default static response (backward compatible)
            return "Request acknowledged and escalated to human supervisor."
    
    def _llm_powered_human_response(self, ai_message: str) -> str:
        """Use LLM to role-play as a human user"""
        # Build context from test case data
        context = self._build_hitl_context()
        
        system_prompt = f"""You are role-playing as a human user/customer in a test scenario.
Context: {context}

The AI agent has asked you: "{ai_message}"

Respond as the human would in this scenario. Be helpful and provide realistic information
that would allow the agent to proceed with the task."""

        # Call LLM to generate response
        response = self._hitl_llm.invoke([{"role": "system", "content": system_prompt}])
        return response.content
    
    def _build_hitl_context(self) -> str:
        """Build context string for HITL LLM from test case data, including full agent_definition.yaml if available."""
        import yaml
        import sys
        from pathlib import Path
        import inspect
        
        context_parts = []
        
        # Fix #1 & #2: Correctly locate the agent_definition.yaml file
        # Use inspect to get the actual file path of the test case class
        try:
            # Get the file path of the class, not the imported module
            test_case_file = inspect.getfile(self.__class__)
            module_path = Path(test_case_file).parent
            yaml_path = module_path / "agent_definition.yaml"
            
            if yaml_path.exists():
                with open(yaml_path, "r") as f:
                    yaml_content = yaml.safe_load(f)
                
                # Fix #3: Parse and format the YAML for better context structure
                if isinstance(yaml_content, dict) and 'agent' in yaml_content:
                    agent_info = yaml_content['agent']
                    
                    # Extract key agent information
                    if 'role' in agent_info:
                        context_parts.append(f"Agent Role:\n{agent_info['role']}")
                    if 'goal' in agent_info:
                        context_parts.append(f"Agent Goal:\n{agent_info['goal']}")
                    
                    # Include available tools
                    if 'action_plan' in agent_info and 'tools_and_resources' in agent_info['action_plan']:
                        tools = agent_info['action_plan']['tools_and_resources']
                        if isinstance(tools, list):
                            tool_names = [t['tool'] if isinstance(t, dict) else t for t in tools]
                            context_parts.append(f"Available Tools: {', '.join(tool_names)}")
                    
                    # Include guidelines for context
                    if 'action_plan' in agent_info and 'guidelines' in agent_info['action_plan']:
                        guidelines = agent_info['action_plan']['guidelines']
                        context_parts.append(f"Agent Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))
                else:
                    # Fallback: include raw YAML if structure is unexpected
                    context_parts.append(f"Agent Definition:\n{yaml.dump(yaml_content)}")
            else:
                context_parts.append(f"[Agent definition file not found at: {yaml_path}]")
        except Exception as e:
            context_parts.append(f"[Could not load agent_definition.yaml: {e}]")
        
        # Fix #3: Include only user-relevant context (not expected_tool_calls or milestones)
        # The human shouldn't know what the agent is "expected" to do
        if hasattr(self, 'title'):
            context_parts.append(f"\nCurrent Task: {self.title}")
        if hasattr(self, 'workflow'):
            context_parts.append(f"Workflow: {self.workflow}")
        if hasattr(self, 'input_data'):
            context_parts.append(f"\nUser Scenario Details:\n{yaml.dump(self.input_data, default_flow_style=False)}")
        
        return "\n\n".join(context_parts)