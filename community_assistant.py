from cat.mad_hatter.decorators import hook, plugin, tool
from pydantic import BaseModel, Field
import pickle
from datetime import datetime, timezone, timedelta
from cat.looking_glass.cheshire_cat import CheshireCat
from .meetup import Meetup

settings = CheshireCat().mad_hatter.get_plugin().load_settings()
meetup = Meetup(settings['meetup_organization_name'], settings['meetup_auth_cookie'])

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
    meetup_auth_cookie: str = Field(
        default="",
        title="Meetup Auth Cookie",
        description="Fuck antiscraping systems and fuck paid API D:",
        extra={"type": "textArea"}
    )


@plugin
def settings_model():
    return PluginSettings


@hook
def before_agent_starts(agent_input, cat):
    global meetup
    settings = cat.mad_hatter.get_plugin().load_settings()
    if meetup._auth_cookie != settings['meetup_auth_cookie'] or meetup._organization_name != settings['meetup_organization_name']:
        meetup = Meetup(settings['meetup_organization_name'], settings['meetup_auth_cookie'])

    return agent_input


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = f"{cat.mad_hatter.get_plugin().load_settings()['assistant_scope']} You answer Human using ONLY information in the context. NEVER answer questions not in topic with the context. ALWAYS answer in the same language the human is talking to you!"
    return prefix


@hook
def agent_prompt_suffix(prompt_suffix, cat):
    current_time = datetime.now(timezone(timedelta(hours=1))).strftime("%a, %b %d, %Y, %I:%M %p CET")

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
Keep in mind that now is {current_time}, so evaluate time and timezone and don't be fooled with dates!
```text
{meetup.past_events}
```

## Upcoming events organized by the Community
Keep in mind that now is {current_time} and such events stay for around 2 hours, so evaluate time and timezone to guess if the event is ongoing just now!
```text
{meetup.upcoming_events}
```

{{episodic_memory}}

{{declarative_memory}}

{{tools_output}}

## Conversation until now:{{chat_history}}
    - Human: {{input}}
    - AI: 
    """
    return prompt_suffix


#@hook
#def before_cat_recalls_procedural_memories(default_procedural_recall_config, cat):
#    default_procedural_recall_config["k"] = cat.mad_hatter.get_plugin().load_settings()['procedural_k']
#    default_procedural_recall_config["threshold"] = cat.mad_hatter.get_plugin().load_settings()['procedural_threshold']
#    return default_procedural_recall_config