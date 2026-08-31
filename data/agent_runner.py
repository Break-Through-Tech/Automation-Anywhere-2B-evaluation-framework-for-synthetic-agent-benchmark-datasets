# Import LLM model configuration with fallback
# try:
import asyncio
from pathlib import Path
from langchain_openai import ChatOpenAI
    
import typing
from langchain_core.tools import StructuredTool
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage, AIMessage, AIMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.embeddings import init_embeddings
from langchain_core.language_models import BaseChatModel

from typing import Dict, List, Any, Optional, Union
import inspect
import os
import warnings
import json
import re
import yaml
from pydantic import BaseModel
import copy
import requests

# Use typing_extensions for Python < 3.12 compatibility
from typing_extensions import TypedDict
from pydantic import Field

import logging

# Setup logging
logger = logging.getLogger(__name__)


class AgentResult(BaseModel):
    messages: List[BaseMessage]  # All messages are now BaseMessage objects
    completed: bool
    turns: int
    
    class Config:
        arbitrary_types_allowed = True  # Allow BaseMessage types in Pydantic model

class SimpleAgent:
    def __init__(self, llm, system_prompt, tools: List[StructuredTool], tool_choice: Optional[str] = None, provider: Optional[str] = None,
                enable_reflection: bool = False, reflection_prompt_template: Optional[str] = None, tool_choice_supported: bool = True):
        # Bind tools to LLM
        tools_dict = {tool.name: tool for tool in tools}

        # Store reflection settings
        self.enable_reflection = enable_reflection
        self.reflection_prompt_template = reflection_prompt_template or """Review the tool call you just made:
- Was the tool selection appropriate for achieving your goal?
- Were the input parameters grounded in the context and conversation?
- Did the result move you closer to completing your objective?
- Are there any errors or corrections needed?
- What are the next steps to take?

Provide a brief self-assessment (2-5 sentences)."""

        # Store tool_choice_supported flag for later use
        self.tool_choice_supported = tool_choice_supported

        # Convert tools to OpenAI function format
        tool_schemas = []
        for tool in tools:
            # Use LangChain's converter to get proper OpenAI schema (without Pydantic's title fields)
            openai_func = convert_to_openai_function(tool)
            tool_schemas.append({
                "type": "function",
                "function": openai_func
            })

        # Determine effective tool_choice based on model capabilities
        if not tool_choice_supported:
            # Model doesn't support tool_choice="required", use "auto" or skip entirely
            effective_tool_choice = None  # Will bind tools without tool_choice parameter
        elif tool_choice is None:
            # If caller didn't specify a tool_choice, derive it from provider:
            # - Anthropic/Bedrock-like providers expect "any" to allow tool use
            # - OpenAI/Azure expect "required" to force tool usage
            if provider and ("openai" in provider.lower() or "azure" in provider.lower()):
                effective_tool_choice = "required"
            else:
                effective_tool_choice = "any"
        else:
            effective_tool_choice = tool_choice

        # Bind tools to LLM with appropriate tool_choice
        # if any of ["gpt", "gemini", "claude"] in llm.model_name:
        if any(x in llm.model_name.lower() for x in ["gpt", "gemini", "claude", "glm", "nemotron"]):
            # Some providers may not accept tool_choice; fallback
            if effective_tool_choice is not None:
                llm_with_tools = llm.bind_tools(tool_schemas, tool_choice=effective_tool_choice)
            else:
                llm_with_tools = llm.bind_tools(tool_schemas)
        else:
            llm_with_tools = llm.bind_tools(tool_schemas)

        self.llm = llm_with_tools
        self.system_prompt = system_prompt
        self.tools_dict = tools_dict
        self.tool_schemas = tool_schemas

    def run(self, input_message: str, max_turns: int = 10, verbose: bool = False) -> AgentResult:
        """Run the agent loop until completion or max turns."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_message}
        ]

        termination_tools = ['SUCCESS', 'CANCELLED', 'FAILED']
        workflow_completed = False
        
        # Initialize all_messages with system and user messages as BaseMessage objects
        all_messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=input_message)
        ]
        
        for turn in range(max_turns):
            if workflow_completed:
                break
                
            if verbose:
                print(f"🔄 === Turn {turn + 1} ===")
            
            # Get LLM response
            try:

                for i in range(3):
                    try:
                        response = self.llm.invoke(messages)
                        break
                    except Exception as e:

                        if verbose:
                            print(f"❌ Error invoking LLM (attempt {i+1}/3): {e}")
                        continue


                messages.append(response)
                all_messages.append(response)
                
                if verbose:
                    print(f"🤖 Assistant: {response.content}")
                
                # Handle tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    if verbose:
                        print(f"🛠️  Assistant made {len(response.tool_calls)} tool call(s)")
                    
                    for tool_call in response.tool_calls:
                        # Extract tool info - handle both object and dictionary formats
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get('name', 'unknown')
                            call_args = tool_call.get('args', {})
                            tool_call_id = tool_call.get('id', f"call_{tool_name}")
                        elif hasattr(tool_call, 'name') and hasattr(tool_call, 'args'):
                            tool_name = tool_call.name
                            call_args = tool_call.args
                            tool_call_id = getattr(tool_call, 'id', f"call_{tool_name}")
                        else:
                            tool_name = 'unknown'
                            call_args = {}
                            tool_call_id = 'call_unknown'
                        
                        if isinstance(call_args, str):
                            try:
                                call_args = json.loads(call_args)
                            except json.JSONDecodeError as e:
                                if verbose:
                                    print(f"   ❌ Error decoding tool call args: {e}")
                        
                        if verbose:
                            print(f"  📞 Tool Call: {tool_name}")
                            if call_args:
                                print(f"     Arguments: {json.dumps(call_args, indent=6)}")
                        
                        # Check for termination
                        if tool_name in termination_tools:
                            workflow_completed = True
                            if verbose:
                                print(f"   ✅ Workflow termination: {tool_name}")
                        
                        # Execute tool
                        try:
                            if tool_name in self.tools_dict:
                                tool = self.tools_dict[tool_name]
                                result = tool.func(**call_args)
                                if verbose:
                                    print(f"  📋 Tool Response: {json.dumps(result, indent=6)}")
                            else:
                                result = {"error": f"Tool {tool_name} not found"}
                                if verbose:
                                    print(f"   ❌ Tool not found: {tool_name}")
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {e}"}
                            if verbose:
                                print(f"   ❌ Tool error: {e}")
                        
                        # Add tool response message as ToolMessage object
                        tool_message = ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tool_call_id,
                            name=tool_name
                        )
                        messages.append(tool_message)
                        all_messages.append(tool_message)
                        
                        # Break out of tool loop if terminated
                        if workflow_completed:
                            break
                    
                    # Reflection step AFTER all tool calls in this turn are processed
                    # This ensures OpenAI's requirement that all tool_call_ids have responses before next user message
                    if self.enable_reflection and not workflow_completed:
                        reflection_messages = messages + [
                            {"role": "user", "content": self.reflection_prompt_template}
                        ]
                        
                        try:
                            # Get reflection from base LLM (without tool bindings)
                            reflection_response = self.base_llm.invoke(reflection_messages)
                            
                            if verbose:
                                print(f"  🤔 Reflection: {reflection_response.content}")
                            
                            # Add reflection as an AI message to the conversation
                            # Strip trailing whitespace to avoid Anthropic API errors
                            from langchain_core.messages import AIMessage
                            reflection_content = f"[REFLECTION] {reflection_response.content}".rstrip()
                            reflection_ai_message = AIMessage(content=reflection_content)
                            messages.append(reflection_ai_message)
                            all_messages.append(reflection_ai_message)
                            
                        except Exception as e:
                            if verbose:
                                print(f"  ⚠️  Reflection error: {e}")
                # else:
                #     # No tool calls - conversation may be complete
                #     if verbose:
                #         print(f"   💬 No tool calls in turn {turn + 1}")
                #     break
                    
            except Exception as e:
                if verbose:
                    print(f"❌ Error in turn {turn + 1}: {e}")
                    # print("=======messages=======")
                    # print(messages)
                break
        
        if verbose:
            print(f"✅ Completed in {turn + 1} turns")

        return AgentResult(
            messages=all_messages,
            completed=workflow_completed,
            turns=turn + 1
        )






# ======================== UTILITY FUNCTIONS ========================

def get_tools_from_test_case(test_case_instance) -> List[StructuredTool]:
    """Convert all methods of a test case instance into LangChain tools."""
    tools = []
    
    # Get all methods of the test case instance
    for name, method in inspect.getmembers(test_case_instance, predicate=inspect.ismethod):
        # Skip private methods
        if name.startswith('_'):
            continue
            
        # Create a tool from the bound method
        tool = StructuredTool.from_function(
            func=method,
            name=name,
            description=method.__doc__ or f"Execute {name} operation"
        )
        tools.append(tool)
        
    return tools

def get_tools_dict_from_test_case(test_case_instance) -> Dict[str, StructuredTool]:
    """Get tools as a dictionary mapping tool names to tool objects."""
    tools = get_tools_from_test_case(test_case_instance)
    return {tool.name: tool for tool in tools}


# ======================== AGENT FACTORY ========================

_DEFAULT_AGENT_TYPE = "simple"


def _load_summarizer_llm():
    """Load the summarizer LLM used by memory-capable agents."""
    summarizer_llm, _ = aai_llm_models.get_model("gpt-4o-mini-20240718")
    return summarizer_llm


def _create_agent(
    agent_llm,
    system_prompt: str,
    tools: List[StructuredTool],
    tool_choice: Optional[str],
    provider: Optional[str],
    enable_reflection: bool,
    reflection_prompt_template: Optional[str],
    hitl_llm = None,
    test_case_instance = None,
    tool_choice_supported: bool = True,
):
    """Instantiate the requested agent implementation."""

    agent_tool_choice = tool_choice if tool_choice is not None else "any"

    return SimpleAgent(
        agent_llm,
        system_prompt,
        tools,
        tool_choice=agent_tool_choice,
        provider=provider,
        enable_reflection=enable_reflection,
        reflection_prompt_template=reflection_prompt_template,
        hitl_llm=hitl_llm,
        test_case_instance=test_case_instance,
        tool_choice_supported=tool_choice_supported,
    )

    


 # ======================== AGENT RUNNER ========================

def load_system_prompt_from_yaml(yaml_path: str, substitutions: dict = None) -> str:
    """
    Load a system prompt template from a YAML file and apply substitutions.
    Handles both single and multi-document YAML files.
    Args:
        yaml_path: Path to the YAML file
        substitutions: Dict of substitutions to apply to the template
    Returns:
        The system prompt string with substitutions applied
    """
    if substitutions is None:
        substitutions = {}
    
    with open(yaml_path, 'r') as f:
        # Load all documents in case of multi-document YAML
        documents = list(yaml.safe_load_all(f))
    
    # Merge all documents into one
    merged_data = {}
    for doc in documents:
        if doc:
            merged_data.update(doc)
    
    # Extract the system prompt
    system_prompt = merged_data.get('system', '')
    
    # Ensure system_prompt is a string
    if system_prompt is None:
        system_prompt = ''
    elif not isinstance(system_prompt, str):
        system_prompt = str(system_prompt)
    
    # Apply substitutions
    if substitutions and system_prompt:
        for key, value in substitutions.items():
            system_prompt = system_prompt.replace(f'{{{{{key}}}}}', str(value))
    
    return system_prompt


# Initialize LLM

import os
if os.getenv('OPENAI_API_KEY'):
    try:
        llm = ChatOpenAI(model="gpt-4.1", base_url=os.getenv('BASE_URL'), temperature=0)
    except Exception as e:
        warnings.warn(f"Failed to initialize OpenAI model: {e}")
else:
    warnings.warn("No OPENAI_API_KEY found. LLM will be None - you'll need to pass your own LLM to create_agent()")


# Move SimpleAgent to module level for readability
class AgentResult(BaseModel):
    messages: List[BaseMessage]  # All messages are now BaseMessage objects
    completed: bool
    turns: int
    
    class Config:
        arbitrary_types_allowed = True  # Allow BaseMessage types in Pydantic model

class SimpleAgent:
    def __init__(self, llm, system_prompt, tools: List[StructuredTool], tool_choice: Optional[str] = None, provider: Optional[str] = None, 
                 enable_reflection: bool = False, reflection_prompt_template: Optional[str] = None, 
                 hitl_llm = None, test_case_instance = None, tool_choice_supported: bool = True):
        # Bind tools to LLM
        tools_dict = {tool.name: tool for tool in tools}
        
        # Store reflection settings
        self.enable_reflection = enable_reflection
        self.reflection_prompt_template = reflection_prompt_template or """Review the tool call you just made:
- Was the tool selection appropriate for achieving your goal?
- Were the input parameters grounded in the context and conversation?
- Did the result move you closer to completing your objective?
- Are there any errors or corrections needed?
- What are the next steps to take?

Provide a brief self-assessment (2-5 sentences)."""

        # Store HITL LLM for generating nudges when agent responds without tool calls
        self.hitl_llm = hitl_llm
        self.test_case_instance = test_case_instance
        self.tool_choice_supported = tool_choice_supported

        # Convert tools to OpenAI function format
        tool_schemas = []
        for tool in tools:
            # Use LangChain's converter to get proper OpenAI schema (without Pydantic's title fields)
            openai_func = convert_to_openai_function(tool)
            
            # Inject 'reasoning' parameter into all tools for AC6 validation
            # This allows the LLM to provide rationale without modifying each tool method
            if 'parameters' in openai_func and 'properties' in openai_func['parameters']:
                openai_func['parameters']['properties']['reasoning'] = {
                    'type': 'string',
                    'description': 'Explain your reasoning for calling this tool and how it helps achieve your goal. Include what information you\'re seeking or what action you\'re taking.'
                }
                # Add to required fields to encourage LLM to provide reasoning
                if 'required' not in openai_func['parameters']:
                    openai_func['parameters']['required'] = []
                if 'reasoning' not in openai_func['parameters']['required']:
                    openai_func['parameters']['required'].append('reasoning')
            
            tool_schemas.append({
                "type": "function",
                "function": openai_func
            })

        # If caller didn't specify a tool_choice, derive it from provider:
        # - Anthropic/Bedrock-like providers expect "any" to allow tool use
        # - OpenAI/Azure expect "required" to force tool usage
        # - Models without tool_choice support should skip this parameter
        if not tool_choice_supported:
            effective_tool_choice = None  # Skip tool_choice parameter
        elif tool_choice is None:
            if provider and ("openai" in provider.lower() or "azure" in provider.lower() or "nvidia" in provider.lower()):
                effective_tool_choice = "required"
            else:
                effective_tool_choice = "any"
        else:
            effective_tool_choice = tool_choice

        if effective_tool_choice is not None:
            llm_with_tools = llm.bind_tools(tool_schemas, tool_choice=effective_tool_choice)
        else:
            llm_with_tools = llm.bind_tools(tool_schemas)
        self.llm = llm_with_tools
        self.base_llm = llm  # Store base LLM for reflection (without tool bindings)
        self.system_prompt = system_prompt
        self.tools_dict = tools_dict
    
    def _generate_user_nudge(self, agent_message: str, context: str) -> str:
        """
        Generate an LLM-powered simulated user response to nudge the agent toward tool usage.
        Similar to HITL pattern but specifically for handling non-tool responses.
        """
        if self.hitl_llm is None:
            # Fallback to simple nudge message
            return "Please proceed by calling the appropriate tool to complete this task."
        
        system_prompt = f"""You are role-playing as a human user/customer in a test scenario.
{context}

The AI agent has responded with text instead of using tools: "{agent_message}"

Your task is to gently guide the agent to use the available tools to complete the task.

IMPORTANT GUIDELINES:
- If the agent has already performed the main work (e.g., got a calculation result), prompt them to call SUCCESS or another completion tool
- If the agent hasn't taken action yet, prompt them to use the relevant action tool
- Keep responses brief and natural (1-2 sentences)
- Don't repeat the same request - vary your phrasing
- Be encouraging and helpful

Respond as the human would in this scenario."""

        try:
            response = self.hitl_llm.invoke([{"role": "system", "content": system_prompt}])
            return response.content
        except Exception as e:
            logger.warning(f"Failed to generate LLM-powered nudge: {e}")
            return "Please proceed by calling the appropriate tool to complete this task."
    
    def _build_nudge_context(self) -> str:
        """Build context for nudge generation from test case instance."""
        if self.test_case_instance and hasattr(self.test_case_instance, '_build_hitl_context'):
            # Reuse the HITL context builder if available
            return self.test_case_instance._build_hitl_context()
        
        # Fallback: build minimal context from system prompt
        context_parts = []
        context_parts.append(f"System Instructions:\n{self.system_prompt[:500]}...")  # First 500 chars
        
        # List available tools
        tool_names = list(self.tools_dict.keys())
        context_parts.append(f"\nAvailable Tools: {', '.join(tool_names)}")
        
        return "\n\n".join(context_parts)

    def run(self, input_message: str, max_turns: int = 90, verbose: bool = False) -> AgentResult:
        """Run the agent loop until completion or max turns."""
        # Strip trailing whitespace to avoid Anthropic API errors
        system_prompt = self.system_prompt.rstrip()
        input_message = input_message.rstrip()
        
        # IMPORTANT: When using OpenAI's Responses API (or OpenAI-compatible clones),
        # the SDK expects a *string* `input` (or a different structured schema), not a
        # Chat Completions-style `messages` list. Some providers expose a `use_responses_api`
        # flag (see `aai_llm_models`) that flips this behavior under the hood.
        #
        # LangChain `ChatOpenAI.invoke()` can still accept a list of role/content dicts,
        # but *only* when it routes to the Chat Completions API. If it routes to the
        # Responses API, passing a list can yield 400s like:
        #   "Input should be a valid string".
        #
        # To keep tool-calling and reflection logic stable across providers, we keep the
        # internal conversation in a `messages` list, but when `use_responses_api` is
        # enabled we serialize that list into a single string prompt.
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_message},
        ]

        termination_tools = ['SUCCESS', 'CANCELLED', 'FAILED']
        workflow_completed = False
        
        # Track consecutive non-tool turns for loop detection
        consecutive_non_tool_turns = 0
        max_non_tool_turns = 5  # Max nudges before terminating
        max_nudges = 5  # Maximum number of LLM-generated nudges to try
        nudge_count = 0  # Track how many nudges we've sent
        last_response_content = None  # Track if responses are repeating
        
        # Initialize all_messages with system and user messages as BaseMessage objects
        all_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=input_message)
        ]
        
        for turn in range(max_turns):
            if workflow_completed:
                break
                
            if verbose:
                print(f"🔄 === Turn {turn + 1} ===")
            
            # Get LLM response
            try:
                invoke_payload: Union[str, List[Dict[str, Any]]]

                # Detect Responses API mode (LangChain `ChatOpenAI` passes through this kwarg).
                use_responses_api = bool(getattr(self.llm, "use_responses_api", False))
                if use_responses_api:
                    # Minimal, robust serialization:
                    # - Preserves role labels (system/user/assistant/tool)
                    # - Avoids sending tool schemas via `input` (those are already bound)
                    # - Produces a string, satisfying Responses API validators
                    prompt_lines: List[str] = []
                    for msg in messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if content is None:
                            content = ""
                        if role:
                            prompt_lines.append(f"[{role}]\n{content}")
                        else:
                            prompt_lines.append(str(content))
                    invoke_payload = "\n\n".join(prompt_lines)
                else:
                    invoke_payload = messages

                response = self.llm.invoke(invoke_payload)
                
                # Normalize response for messages array (Responses API compatibility)
                # The messages array is used for subsequent API calls and must have simple format
                # Extract content - handle both simple strings and structured content arrays
                if hasattr(response, 'content'):
                    content = response.content
                    # If content is a list/array (Responses API format), extract text
                    if isinstance(content, list):
                        # Extract text from structured content parts
                        text_parts = []
                        for part in content:
                            if isinstance(part, dict):
                                if part.get('type') == 'output_text':
                                    text_parts.append(part.get('text', ''))
                                elif 'text' in part:
                                    text_parts.append(part['text'])
                            elif hasattr(part, 'text'):
                                text_parts.append(part.text)
                        content = '\n'.join(text_parts) if text_parts else ''
                    # Ensure content is a string
                    if not isinstance(content, str):
                        content = str(content) if content else ''
                else:
                    content = ''
                
                # Create normalized message dict for API compatibility
                normalized_response = {
                    'role': 'assistant',
                    'content': content
                }
                
                # Preserve tool_calls if present (critical for tool calling flow)
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    normalized_response['tool_calls'] = response.tool_calls
                
                # Add normalized dict to messages (for next API call)
                messages.append(normalized_response)
                # Keep raw response in all_messages for tracking
                all_messages.append(response)
                
                if verbose:
                    print(f"🤖 Assistant: {content}")
                
                # Handle tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Reset non-tool counter when we get tool calls
                    consecutive_non_tool_turns = 0
                    last_response_content = None
                    
                    if verbose:
                        print(f"🛠️  Assistant made {len(response.tool_calls)} tool call(s)")
                    
                    for tool_call in response.tool_calls:
                        # Extract tool info - handle both object and dictionary formats
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get('name', 'unknown')
                            call_args = tool_call.get('args', {})
                            tool_call_id = tool_call.get('id', f"call_{tool_name}")
                        elif hasattr(tool_call, 'name') and hasattr(tool_call, 'args'):
                            tool_name = tool_call.name
                            call_args = tool_call.args
                            tool_call_id = getattr(tool_call, 'id', f"call_{tool_name}")
                        else:
                            tool_name = 'unknown'
                            call_args = {}
                            tool_call_id = 'call_unknown'
                        
                        if verbose:
                            print(f"  📞 Tool Call: {tool_name}")
                            if call_args:
                                print(f"     Arguments: {json.dumps(call_args, indent=6)}")
                        
                        # Check for termination
                        if tool_name in termination_tools:
                            workflow_completed = True
                            if verbose:
                                print(f"   ✅ Workflow termination: {tool_name}")
                        
                        # Execute tool
                        try:
                            if tool_name in self.tools_dict:
                                tool = self.tools_dict[tool_name]
                                
                                # Remove 'reasoning' parameter before passing to tool
                                # (it's used for AC6 validation but not needed by tool methods)
                                tool_args = {k: v for k, v in call_args.items() if k != 'reasoning'}
                                
                                result = tool.func(**tool_args)
                                if verbose:
                                    print(f"  📋 Tool Response: {json.dumps(result, indent=6)}")
                            else:
                                result = {"error": f"Tool {tool_name} not found"}
                                if verbose:
                                    print(f"   ❌ Tool not found: {tool_name}")
                        except Exception as e:
                            result = {"error": f"Tool execution failed: {e}"}
                            if verbose:
                                print(f"   ❌ Tool error: {e}")
                        
                        # Ensure result is JSON-serializable and not None/empty
                        if result is None:
                            result = {"status": "completed", "result": None}
                        
                        # Add tool response as simple dict (API compatibility)
                        tool_message_dict = {
                            'role': 'tool',
                            'content': json.dumps(result),
                            'tool_call_id': tool_call_id,
                            'name': tool_name
                        }
                        messages.append(tool_message_dict)
                        # Keep as ToolMessage for tracking
                        all_messages.append(ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tool_call_id,
                            name=tool_name
                        ))
                        
                        # Break out of tool loop if terminated
                        if workflow_completed:
                            break
                    
                    # Reflection step AFTER all tool calls in this turn are processed
                    # This ensures OpenAI's requirement that all tool_call_ids have responses before next user message
                    if self.enable_reflection and not workflow_completed:
                        reflection_messages = messages + [
                            {"role": "user", "content": self.reflection_prompt_template}
                        ]
                        
                        try:
                            # Get reflection from base LLM (without tool bindings)
                            reflection_response = self.base_llm.invoke(reflection_messages)
                            
                            if verbose:
                                print(f"  🤔 Reflection: {reflection_response.content}")
                            
                            # Add reflection as simple dict (API compatibility)
                            # Strip trailing whitespace to avoid Anthropic API errors
                            reflection_content = f"[REFLECTION] {reflection_response.content}".rstrip()
                            reflection_dict = {'role': 'assistant', 'content': reflection_content}
                            messages.append(reflection_dict)
                            # Keep as AIMessage for tracking
                            from langchain_core.messages import AIMessage
                            all_messages.append(AIMessage(content=reflection_content))
                            
                        except Exception as e:
                            if verbose:
                                print(f"  ⚠️  Reflection error: {e}")
                else:
                    # No tool calls - conversation may be complete, but check for loops
                    if verbose:
                        print(f"   💬 No tool calls in turn {turn + 1}")
                    
                    # Detect if agent is stuck asking questions without taking action
                    consecutive_non_tool_turns += 1
                    current_content = response.content if response.content else ""
                    
                    # Check if response is similar to last one (likely repeating question)
                    if current_content == last_response_content:
                        if verbose:
                            print(f"   🔄 Repeating same response - likely stuck in loop")
                            print(f"   ⏹️  Terminating to prevent infinite loop after {turn + 1} turns")
                        # Force workflow completion to exit loop
                        workflow_completed = True
                    elif consecutive_non_tool_turns >= max_non_tool_turns:
                        if verbose:
                            print(f"   🔄 Agent has not made tool calls for {consecutive_non_tool_turns} turns")
                            print(f"   ⏹️  Terminating to prevent infinite loop after {turn + 1} turns")
                        # Force workflow completion to exit loop
                        workflow_completed = True
                    elif nudge_count < max_nudges and not self.tool_choice_supported:
                        # For models without tool_choice support, generate LLM-powered nudge
                        if verbose:
                            print(f"   🤖 Generating user nudge (attempt {nudge_count + 1}/{max_nudges})...")
                        
                        # Build context and generate nudge
                        context = self._build_nudge_context()
                        nudge_message = self._generate_user_nudge(current_content, context)
                        
                        if verbose:
                            print(f"   👤 Simulated user: {nudge_message}")
                        
                        # Inject nudge as simple dict (API compatibility)
                        human_nudge_dict = {'role': 'user', 'content': nudge_message}
                        messages.append(human_nudge_dict)
                        # Keep as BaseMessage for tracking
                        all_messages.append(HumanMessage(content=nudge_message))
                        
                        nudge_count += 1
                        # Don't terminate - let the loop continue with the nudge
                    
                    last_response_content = current_content
                    
            except Exception as e:
                if verbose:
                    print(f"❌ Error in turn {turn + 1}: {e}")
                break
        
        if verbose:
            print(f"✅ Completed in {turn + 1} turns")

        return AgentResult(
            messages=all_messages,
            completed=workflow_completed,
            turns=turn + 1
        )
            

def run_test_case(
        test_case_instance, 
        input_data: Dict[str, Any], 
        max_turns: int = 99, 
        verbose: bool = False, 
        test_agent_llm=None, 
        system_prompt_yaml: Optional[str] = None, 
        enable_reflection: bool = False, 
        reflection_prompt_template: Optional[str] = None,
        tool_choice: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> AgentResult:
    """
    Run a test case using the test case instance's methods as tools.
    
    Args:
        test_case_instance: The test case instance with methods to use as tools
        input_data: Input data for the test case
        max_turns: Maximum number of conversation turns
        verbose: Whether to print verbose output
        test_agent_llm: Optional LLM model to use for the test agent. If None, uses the default global llm.
        system_prompt_yaml: Optional path to a YAML file containing system prompt template
        enable_reflection: Whether to enable reflection after each tool call
        reflection_prompt_template: Optional custom reflection prompt template
        tool_choice: Optional tool choice strategy
    
    Returns:
        AgentResult with execution details
    """
    
    # Initialize Acontext if configured
    acontext_client = None
    acontext_session = None
    
    if acontext_config is None:
        acontext_config = AcontextConfig()
    
    # Validate and initialize Acontext if enabled
    if acontext_config.validate():
        try:
            acontext_client = AcontextClient(
                api_key=acontext_config.api_key,
                base_url=acontext_config.base_url
            )
            logger.info("Initialized Acontext client for memory and self-learning")
        except Exception as e:
            logger.warning(f"Failed to initialize Acontext client: {e}. Continuing without Acontext.")
            acontext_config.enabled = False
    
    # Get domain from test case if available, or from input_data agent_name
    domain = getattr(test_case_instance, 'domain', None)
    if not domain and isinstance(input_data, dict) and 'agent_name' in input_data:
        # Use agent_name as domain (e.g., 'travel_support', 'healthcare_records')
        domain = input_data.get('agent_name', 'general')
    if not domain:
        domain = 'general'
    
    # Get or create space and retrieve prior skills
    prior_skills_text = ""
    if acontext_config.enabled and acontext_client:
        try:
            space_id = get_or_create_space(
                acontext_client,
                domain,
                acontext_config.space_mapping
            )
            
            if space_id and acontext_config.retrieve_skills:
                # Search for prior skills using test case goal
                query = getattr(test_case_instance, 'goal', str(input_data))
                prior_skills_text = search_for_prior_skills(
                    acontext_client,
                    space_id,
                    query,
                    acontext_config
                )
                
                if prior_skills_text and verbose:
                    print(f"📚 Retrieved prior skills from Acontext")
            
            # Initialize Acontext session for this run
            if space_id:
                acontext_session = AcontextSession(
                    acontext_client,
                    space_id,
                    test_case_instance.__class__.__name__,
                    domain
                )
                if not acontext_session.create():
                    acontext_session = None
                    
        except Exception as e:
            logger.error(f"Error setting up Acontext: {e}. Continuing without Acontext.")
            acontext_config.enabled = False
    
    # Create system prompt from YAML template if provided, otherwise use default
    if system_prompt_yaml:
        # Load the YAML template with substitutions
        substitutions = {
            'role': test_case_instance.role,
            'goal': test_case_instance.goal,
            'action_plan': f"""- Assumptions: {test_case_instance.action_plan['assumptions']}
- Guidelines: {test_case_instance.action_plan['guidelines']}
- Workflow Selection: {test_case_instance.action_plan['workflow_selection']}
- Success Criteria: {test_case_instance.action_plan['success_criteria']}"""
        }

    # - Workflow Selection: {test_case_instance.action_plan['workflow_selection']}
        system_prompt = load_system_prompt_from_yaml(system_prompt_yaml, substitutions)
    else:
        # Create system prompt from the test case attributes (original behavior)
        system_prompt = f"""

    {test_case_instance.role}
    
    Goal: {test_case_instance.goal}
    
    Action Plan:
    - Assumptions: {test_case_instance.action_plan['assumptions']}
    - Guidelines: {test_case_instance.action_plan['guidelines']}
    - Success Criteria: {test_case_instance.action_plan['success_criteria']}
    - Workflow Selection: {test_case_instance.action_plan['workflow_selection']}
    - Success Criteria: {test_case_instance.action_plan['success_criteria']}
    
    You have access to the following tools to complete your tasks:
    """
    # - Workflow Selection: {test_case_instance.action_plan['workflow_selection']}
    #     You have access to the following tools to complete your tasks:
    
    # Inject prior skills if retrieved
    if prior_skills_text:
        system_prompt += prior_skills_text
    
    # Get tools from the test case instance using the utility function
    tools = get_tools_from_test_case(test_case_instance)
    
    # Determine which LLM and provider to use.
    # test_agent_llm may be either:
    #   - an LLM instance (agent_provider inferred from module-level 'provider' if present), or
    #   - a tuple (llm, provider)
    agent_provider = globals().get('provider', None)
    if isinstance(test_agent_llm, tuple):
        agent_llm = test_agent_llm[0]
        # allow (llm, provider) tuples; provider may be None
        agent_provider = test_agent_llm[1] if len(test_agent_llm) > 1 else agent_provider
    else:
        agent_llm = test_agent_llm if test_agent_llm is not None else llm

    # Check if LLM is available
    if agent_llm is None:
        raise ValueError("No LLM available. Please set OPENAI_API_KEY environment variable or configure aai_llm_models.")

    # Extract model_info to check tool_choice_supported flag
    tool_choice_supported = True  # Default to True for backward compatibility
    model_name = getattr(agent_llm, 'model_name', None) or getattr(agent_llm, 'model', None)
    if model_name and USE_AAI_MODELS:
        try:
            model_info = aai_llm_models.MODELS.get(model_name, {})
            tool_choice_supported = model_info.get('tool_choice_supported', True)
        except Exception as e:
            logger.warning(f"Could not extract tool_choice_supported flag: {e}")
    
    # Initialize hitl_llm for generating nudges (only for models without tool_choice support)
    hitl_llm = None
    if not tool_choice_supported:
        try:
            hitl_llm, _ = aai_llm_models.get_model("gpt-4.1-2025-04-14")
            logger.info("Initialized HITL LLM for nudge generation")
        except Exception as e:
            logger.warning(f"Failed to initialize HITL LLM: {e}")

    agent = _create_agent(
        agent_llm,
        system_prompt,
        tools,
        tool_choice,
        agent_provider,
        enable_reflection,
        reflection_prompt_template,
        hitl_llm=hitl_llm,
        test_case_instance=test_case_instance,
        tool_choice_supported=tool_choice_supported,
    )

    # Create input message
    input_message = f"{input_data}"
    
    # Run the agent
    result = agent.run(input_message, max_turns=max_turns, verbose=verbose)
    
    # Post-run: Push messages to Acontext if enabled
    if acontext_config.enabled and acontext_session:
        try:
            if verbose:
                print(f"📤 Pushing conversation to Acontext for memory and learning...")
                print(f"   Total messages: {len(result.messages)}")
                print(f"   ℹ️  Note: Skills are learned from multi-turn conversations with tool calls")
                print(f"      Simple conversations may be skipped by Acontext's complexity filter")
            
            # Push all messages from result (system and tool messages filtered out)
            # Note: Acontext auto-extracts tasks from conversations
            # Tasks with 'success' status are learned into skills
            # Only complex multi-step workflows are stored (simple queries are filtered)
            success_count = acontext_session.push_messages(
                result.messages,
                message_format='openai'
            )
            
            # Flush to trigger skill learning
            if success_count > 0:
                acontext_session.flush()
                if verbose:
                    print(f"✅ Acontext learning triggered ({success_count} user/assistant messages pushed and flushed)")
                    print(f"   Complex multi-step tasks will be learned into skills automatically")
            else:
                if verbose:
                    print(f"⚠️  No user/assistant messages to push (system/tool messages filtered)")
            
            # Save space mapping to file if configured
            acontext_config.save_space_mapping()
            
        except Exception as e:
            logger.warning(f"Failed to push messages to Acontext: {e}. Continuing without learning.")
    
    return result

def run_test_case_local(test_case_instance, input_data: Dict[str, Any], 
                  max_turns: int = 99, verbose: bool = False, 
                  test_agent_llm=None, system_prompt=None,
                  enable_reflection: bool = False, reflection_prompt_template: Optional[str] = None,
                  tool_choice: Optional[str] = None,
                  agent_type: Optional[str] = None,) -> AgentResult:
    """
    Run a test case using the test case instance's methods as tools.
    
    Args:
        test_case_instance: The test case instance with methods to use as tools
        input_data: Input data for the test case
        max_turns: Maximum number of conversation turns
        verbose: Whether to print verbose output
        test_agent_llm: Optional LLM model to use for the test agent. If None, uses the default global llm.
    
    Returns:
        AgentResult with execution details
    """
    
    # Create system prompt from the test case attributes
    if system_prompt is None:
        system_prompt = f"""
    {test_case_instance.role}
    
    Goal: {test_case_instance.goal}
    
    Action Plan:
    - Assumptions: {test_case_instance.action_plan['assumptions']}
    - Guidelines: {test_case_instance.action_plan['guidelines']}
    - Success Criteria: {test_case_instance.action_plan['success_criteria']}
    """
    
    # Get tools from the test case instance using the utility function
    tools = get_tools_from_test_case(test_case_instance)
    
    # Determine which LLM to use
    agent_llm = test_agent_llm if test_agent_llm is not None else llm
    
    # Check if LLM is available
    if agent_llm is None:
        raise ValueError("No LLM available. Please set OPENAI_API_KEY environment variable or configure aai_llm_models.")
    
    agent_provider = globals().get('provider', None)

    agent = _create_agent(
        agent_llm,
        system_prompt,
        tools,
        tool_choice,
        agent_provider,
        enable_reflection,
        reflection_prompt_template,
    )

    # Create input message
    input_message = f"{input_data}"
    
    # Run the agent
    result = agent.run(input_message, max_turns=max_turns, verbose=verbose)
    
    return result, tools
