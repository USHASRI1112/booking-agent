"""
llm.py - the ONLY file that talks to the AI model.

Every other file calls one of these two functions:
    chat(messages, tools)          -> the model's next message (text and/or tool calls)
    structured(prompt, name, schema) -> a Python dict that matches `schema`

We use the OpenAI Python library. It also works with any "OpenAI-compatible" provider
(like Groq) - you just set OPENAI_BASE_URL in the .env file.
"""
import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, omit

# Read settings from the .env file (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL).
load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
client = OpenAI(max_retries=3)


def call_model(messages, tools=None, response_format=None):
    """Send one request to the model. If we hit a per-minute rate limit, wait and try again."""
    for attempt in range(30):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                # `omit` means "don't send this field at all" (sending None would send null).
                tools=tools if tools else omit,
                response_format=response_format if response_format else omit,
            )
        except RateLimitError as error:
            message = str(error)

            # Out of daily quota or credits: waiting a few seconds won't help, so stop.
            if "per day" in message or "credit" in message:
                raise

            # The error usually says "Please try again in 2.5s" - wait that long.
            match = re.search(r"try again in ([\d.]+)s", message)
            if match:
                wait_seconds = float(match.group(1)) + 1
            else:
                wait_seconds = 15
            print(f"    (rate limited, waiting {wait_seconds:.0f}s)")
            time.sleep(wait_seconds)

    raise RuntimeError("Still rate limited after 30 attempts")


def chat(messages, tools=None):
    """Ask the model for its next message. It may contain text, tool calls, or both."""
    response = call_model(messages, tools=tools)
    return response.choices[0].message


def structured(prompt, name, schema):
    """Ask the model a question and force the answer to be JSON matching `schema`."""
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": schema, "strict": True},
    }
    messages = [{"role": "user", "content": prompt}]
    response = call_model(messages, response_format=response_format)
    answer_text = response.choices[0].message.content
    return json.loads(answer_text)
