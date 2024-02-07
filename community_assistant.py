from cat.mad_hatter.decorators import hook, plugin, tool
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from cat.looking_glass.cheshire_cat import CheshireCat
from .meetup import Meetup
import json


settings = CheshireCat().mad_hatter.get_plugin().load_settings()
meetup = Meetup(settings['meetup_organization_name'], settings['meetup_auth_cookie'])


def ingest_events_details(cat):
    events = meetup.past_events + meetup.upcoming_events

    for event in events:
        short_summary = cat.llm(f"Write a summary of the following event description: ```{event}\n{event.details}```")
        docs = cat.rabbit_hole.string_to_docs(
            stray=cat,
            file_bytes=short_summary,
            chunk_size=len(short_summary),
            source=event.link
            )

        short_summary = cat.llm(f"Given the following event description extract event details, speakers and their talks: ```{event}\n{event.details}```")
        docs_2 = cat.rabbit_hole.string_to_docs(
            stray=cat,
            file_bytes=short_summary,
            chunk_size=len(short_summary),
            source=event.link
            )
              
        #details_tmp = f'Follow the details of the event `{event.name}`: {event.details}'
        #docs_2 = cat.rabbit_hole.string_to_docs(
        #    stray=cat,
        #    file_bytes=event.details,
        #    source=event.link
        #    )
        
        #for d in docs_2:
        #    d.page_content = f"This is a chunk from the description of the event {event.name}: ```{d.page_content}```"

        docs = docs + docs_2

        for doc in docs:
            doc.metadata['event_name'] = event.name
            doc.metadata['event_time'] = event.time
            doc.metadata['event_location'] = f'{event.location_building} ({event.location_address})'

        cat.rabbit_hole.store_documents(
            stray=cat,
            docs=docs,
            source=event.link
        )


def set_documents_details_ingestion_option(cat, value: bool):
    file_path = f'{cat.mad_hatter.get_plugin().path}settings.json'

    with open(file_path, 'r') as file:
        data = json.load(file)

    data['ingest_events_details'] = value

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


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
    ingest_events_details: bool = Field(
        default=True,
        title="Ingest Events Details"
    )


@plugin
def settings_model():
    return PluginSettings


@hook
def before_agent_starts(agent_input, cat):
    global meetup
    global documents_details_ingested
    settings = cat.mad_hatter.get_plugin().load_settings()

    if meetup._auth_cookie != settings['meetup_auth_cookie'] or meetup._organization_name != settings['meetup_organization_name']:
        meetup = Meetup(settings['meetup_organization_name'], settings['meetup_auth_cookie'])
        ingest_events_details(cat)
        set_documents_details_ingestion_option(cat, False)

    if settings['ingest_events_details']:
        ingest_events_details(cat)
        set_documents_details_ingestion_option(cat, False)

    return agent_input


@hook
def agent_prompt_prefix(prefix, cat):
    prefix = f"{cat.mad_hatter.get_plugin().load_settings()['assistant_scope']} You answer Human with a focus on the information in the context, if you are unsure ask to provide more context. NEVER answer questions not in topic with the context. ALWAYS answer in the same language the human is talking to you!"
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


@hook
def before_cat_recalls_declarative_memories(declarative_recall_config, cat):
    declarative_recall_config["k"] = 10

    return declarative_recall_config