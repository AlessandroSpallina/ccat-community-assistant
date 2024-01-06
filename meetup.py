import httpx
import schedule
import time
from typing import List
from pydantic import BaseModel
from bs4 import BeautifulSoup
from cat.mad_hatter.decorators import hook


class Event(BaseModel):
    name: str
    time: str # or python datetime
    link: str
    location: str = 'N/A'
    details: str = 'N/A' # would be nice to automatically ingest linked pages
    slide_links: List[str] = [] # obtained from https://speakerdeck.com/pythontorino

    def __repr__(self) -> str:
        return f'Event: `{self.name}`, time:{self.time}, link:`{self.link}`, location:`{self.location}, details:`{self.details}`, slide_links:`{self.slide_links}'

class Meetup:
    def __init__(self, organization_name):
        self._organization_name = organization_name
        self._past_events_url = f'https://www.meetup.com/{organization_name}/events/?type=past'
        self._upcoming_events_url = f'https://www.meetup.com/{organization_name}/events/?type=upcoming'
    
    def _request(self, url: str, method='GET') -> list[Event]:
        r = httpx.request(method, url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')
        
        event_divs = soup.select('div[id^="e-"], div[id^="ep-"]')

        events = []
        for event_div in event_divs:
            # Extract time and title from each div
            time = event_div.find('time').text.strip()
            title = event_div.find('span', class_='ds-font-title-3').text.strip()
            link = event_div.find('a')['href']
            events.append(Event(
                name=title,
                time=time,
                link=link
            ))
        return events

    def get_past_events(self):
        return self._request(self._past_events_url)

    def get_upcoming_events(self):
        return self._request(self._upcoming_events_url)
