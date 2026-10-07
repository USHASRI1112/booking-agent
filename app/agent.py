"""Tool-calling appointment scheduling agent."""
import json

from app.llm import chat
from app.prompts import system_prompt
from app.state import Clinic
from app.tools import appointments, patients

MAX_TOOL_STEPS_PER_TURN = 10


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "verify_patient",
            "description": "Verify identity with full name and date of birth (YYYY-MM-DD). Required before any appointment action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "dob": {"type": "string"},
                },
                "required": ["full_name", "dob"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_slots",
            "description": "Find free appointment slots. Both filters optional. date is YYYY-MM-DD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_my_appointments",
            "description": "List the verified patient's upcoming appointments.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a free slot for the verified patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["slot_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel one of the verified patient's appointments.",
            "parameters": {
                "type": "object",
                "properties": {"appointment_id": {"type": "string"}},
                "required": ["appointment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_staff",
            "description": "Hand off to clinic staff. urgency: 'emergency' for a possible medical emergency, else 'routine'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "urgency": {"type": "string", "enum": ["emergency", "routine"]},
                },
                "required": ["reason", "urgency"],
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "verify_patient": patients.verify_patient,
    "escalate_to_staff": patients.escalate_to_staff,
    "search_slots": appointments.search_slots,
    "list_my_appointments": appointments.list_my_appointments,
    "book_appointment": appointments.book_appointment,
    "cancel_appointment": appointments.cancel_appointment,
}


def run_tool(clinic, tool_name, arguments_json):
    """Run one tool and return its result as JSON text."""
    try:
        arguments = json.loads(arguments_json or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON arguments."})

    clinic.tool_log.append({"tool": tool_name, "input": arguments})

    tool_function = TOOL_FUNCTIONS.get(tool_name)
    if tool_function is None:
        return json.dumps({"error": f"Unknown tool {tool_name}."})

    try:
        result = tool_function(clinic, **arguments)
    except Exception as error:
        result = {"error": str(error)}

    return json.dumps(result)


class Agent:
    def __init__(self, learned_rules):
        self.clinic = Clinic()
        self.messages = [{"role": "system", "content": system_prompt(learned_rules)}]

    def reply(self, patient_text):
        """Handle one message from the patient and return the agent's answer."""
        self.messages.append({"role": "user", "content": patient_text})

        for step in range(MAX_TOOL_STEPS_PER_TURN):
            model_message = chat(self.messages, tools=TOOLS)
            self.messages.append(model_message.model_dump(exclude_none=True))

            if not model_message.tool_calls:
                return model_message.content or ""

            for tool_call in model_message.tool_calls:
                result = run_tool(self.clinic, tool_call.function.name, tool_call.function.arguments)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        return "Sorry, I'm having trouble. Let me connect you with clinic staff."
