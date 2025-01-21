from anthropic import Anthropic
from openai import OpenAI
import os

def anthropic_llm_call(prompt: str, system_prompt: str = "", model="claude-3-5-sonnet-20241022") -> str:
    """
    Calls the model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The model to use for the call. Defaults to "claude-3-5-sonnet-20241022".

    Returns:
        str: The response from the language model.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
        temperature=0.7,
    )
    return response.content[0].text

def r1_llm_call(prompt: str, system_prompt: str = "", model: str = "deepseek-reasoner", base_url: str = "https://api.deepseek.com") -> str:
    """
    Calls the model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The model to use for the call.
        base_url (str, optional): The base URL of the API. Defaults to "https://api.deepseek.com".

    Returns:
        str: The response from the language model.
    """
    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=base_url)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return "<think>"+response.choices[0].message.reasoning_content+"</think>"+response.choices[0].message.content
