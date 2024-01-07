from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from .meetup import Meetup


m = Meetup('python-torino')


class PluginSettings(BaseModel):
    assistant_scope: str = Field(
        default="""Act as the Community Assistant of 'Python Torino', an organization focused on python and organizing public events with talks with cool people.
You help people connect with the organization, entice them to attend events, and talk about the topics discussed during event talks.""",
        title="Assistant Scope",
        description="What is this assistant for?",
        extra={"type": "TextArea"}
    )
    community_contacts: str = Field(
        default="""You can find all the community contacts at the page 'https://torino.python.it/': organization link collector from which you find:
- Events schedule and description: 'https://www.meetup.com/it-IT/python-torino/'
- Event ticketing system: 'https://www.eventbrite.com/o/python-torino-73732972003'
- Telegram group: 'https://t.me/pytorino'
- Past events recordings: 'https://video.linux.it/c/pythontorino/videos'
- Slides of talks from past events: 'https://speakerdeck.com/pythontorino'""",
        title="Community Contacts",
        description="List all the info you want",
        extra={"type": "TextArea"}
    )
    joking_personality: str = Field(
        default="""If the human is specifically asking you questions about Turin you:
- Suggest 'Vanchiglia' as better neighborhood for a Spritz
- Do jokes about typical dishes from Piedmont, Italy. Examples of dishes are: Vitel tonné, Agnolotti, Bagna Caoda, Bicerin. Suggest Kebap as alternative.
- Complain about shitty public transportation system, 'GTT' (the company who runs the public transport) made you to buy a car""",
        title="Joking Personality",
        description="It works better with uncensored LLMs ;)",
        extra={"type": "textArea"}
    )
    meetup_organization_name: str = Field(
        default="python-torino",
        title="Meetup Organization Name",
        description="Check the meetup.com link, for example https://www.meetup.com/python-torino -> python-torino"
    )

    procedural_k: int = Field(
        default="1",
        ge=0,
        title="Procedural K",
        description="Number of tools to recall from procedural memory after an user message"
    )

    procedural_threshold: float = Field(
        default="0.83",
        ge=0,
        le=1,
        title="Procedural Threshold",
        description="Threshold for tools to recall from procedural memory after an user message"
    )


@plugin
def settings_model():
    return PluginSettings


# @tool
# def event_details(tool_input, cat):
#     """When user asks for an event of the Community. Input is always None
# Examples of questions you might face:
# - che mi sai dire dell'evento?
# - dettagli evento?
# - dimmi di più"""

#     m.get_event_detail()
#     return "BLABLABLABLA"


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = f"{cat.mad_hatter.get_plugin().load_settings()['assistant_scope']} You answer Human with a focus on the following context. NEVER answer questions not in topic with the context. ALWAYS answer in the same language the human is talking to you!"
    return prefix


@hook
def agent_prompt_suffix(prompt_suffix, cat):
    prompt_suffix = f""" 
# Context

## Joking Personality
{cat.mad_hatter.get_plugin().load_settings()['joking_personality']}

## Community Contacts
DON'T suggest any other contact that isn't present in the following text!
```text
{cat.mad_hatter.get_plugin().load_settings()['community_contacts']}
```

## Past events organized by the Community
Keep in mind that now is {datetime.now().strftime("%A %d %B %Y, %H:%M:%S %Z%z")}, so evaluate time and timezone and don't be fooled with dates!
```text
{m.past_events}
```

## Upcoming events organized by the Community
Keep in mind that now is {datetime.now().strftime("%A %d %B %Y, %H:%M:%S %Z%z")} and such events stay for around 2 hours, so evaluate time and timezone to guess if the event is ongoing just now!
```text
{m.upcoming_events}
```

{{episodic_memory}}

{{declarative_memory}}

{{tools_output}}

## Conversation until now:{{chat_history}}
    - Human: {{input}}
    - AI: 
    """
    return prompt_suffix


@hook
def before_cat_recalls_procedural_memories(default_procedural_recall_config, cat):
    default_procedural_recall_config["k"] = cat.mad_hatter.get_plugin().load_settings()['procedural_k']
    default_procedural_recall_config["threshold"] = cat.mad_hatter.get_plugin().load_settings()['procedural_threshold']

    return default_procedural_recall_config