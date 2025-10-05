import os
from openai import AzureOpenAI
from config import GeneralConfig

def azure_call(prompt, system_prompt, retries=10, temperature=0.0, max_input_chars=50000):
    """Call Azure OpenAI GPT model with retries and safe input truncation.

    Args:
        prompt (str): User prompt content.
        system_prompt (str): System instruction for the model.
        retries (int, optional): Number of retries on failure. Defaults to 10.
        temperature (float, optional): Sampling temperature. Defaults to 0.0.
        max_input_chars (int, optional): Max allowed characters for input. Defaults to 50000.

    Returns:
        str | None: Model response or None if all retries fail.
    """
    deployment_name = GeneralConfig.AZURE_GPT_4O_MINI_MODEL
    client = AzureOpenAI(
        azure_endpoint=GeneralConfig.AZURE_OPENAI_4O_MINI_URL,
        api_key=GeneralConfig.AZURE_OPENAI_4O_MINI_KEY,
        api_version=GeneralConfig.AZURE_OPENAPI_VERSION
    )

    if len(prompt) > max_input_chars:
        print(f"Truncating prompt from {len(prompt)} to {max_input_chars} chars")
        prompt = prompt[:max_input_chars]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                max_tokens=10000,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Attempt {attempt+1}/{retries} failed: {e}")
    return None
