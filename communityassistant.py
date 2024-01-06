from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List
from .meetup import Meetup


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


@plugin
def settings_model():
    return PluginSettings


# @tool
# def get_the_day(tool_input, cat):
#     """Get the day of the week. Input is always None."""

#     dt = datetime.now()

#     return dt.strftime('%A')


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = f"{cat.mad_hatter.get_plugin().load_settings()['assistant_scope']} You answer Human with a focus on the following context. ALWAYS answer in the same language the human is talking to you!"
    return prefix



@hook
def agent_prompt_suffix(prompt_suffix, cat):
    m = Meetup('python-torino')
    past_events = m.get_past_events()
    upcoming_events = m.get_upcoming_events()

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
```text
{m.get_past_events()}
```

## Upcoming events organized by the Community
Keep in mind that now is {datetime.now().strftime("%d%B %Y, %H:%M:%S %Z%z")} and such events stay for around 2 hours, so evaluate time and timezone to guess if the event is ongoing just now!
```text
{m.get_upcoming_events()}
```

{{episodic_memory}}

{{declarative_memory}}

{{tools_output}}

## Conversation until now:{{chat_history}}
    - Human: {{input}}
    - AI: 
    """
    return prompt_suffix

