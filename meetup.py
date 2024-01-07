import httpx
from typing import List
from pydantic import BaseModel
from bs4 import BeautifulSoup
from cat.log import log
import time


CACHE_LIFETIME = 60 # seconds


class Event(BaseModel):
    name: str
    time: str
    link: str
    location: str = 'N/A'
    details: str = 'N/A' # would be nice to automatically ingest linked pages
    slide_links: List[str] = [] # obtained from https://speakerdeck.com/pythontorino

    def __repr__(self) -> str:
        # I'm not sure this is the best way to format event info
        return f'Event `{self.name}`\n- time: `{self.time}`\n- link: `{self.link}`\n- location: `{self.location}\n'


class Meetup:
    def __init__(self, organization_name):
        self._organization_name = organization_name
        self._past_events_url = f'https://www.meetup.com/{organization_name}/events/?type=past'
        self._upcoming_events_url = f'https://www.meetup.com/{organization_name}/events/?type=upcoming'

        self._past_events_timestamp = -1 # filled with the timestamp of the last update
        self._past_events = []
        self._upcoming_events_timestamp = -1 # filled with the timestamp of the last update
        self._upcoming_events = []
    
    def _request(self, url: str, method='GET') -> list[Event]:
        r = httpx.request(method, url)
        r.raise_for_status()
        return r.text
    
    def _scrape_events(self, text: str):
        soup = BeautifulSoup(text, 'html.parser')
        
        event_divs = soup.select('div[id^="e-"], div[id^="ep-"]')

        events = []
        for event_div in event_divs:
            # Extract time and title from each div
            time = event_div.find('time').text.strip()
            title = event_div.find('span', class_='ds-font-title-3').text.strip()
            link = event_div.find('a')['href']
            location = event_div.find('div', class_='flex items-start space-x-1.5').find('span', class_='text-gray6').text.strip()
            # location = event_div.find_all('span', class_='text-gray6')[-1].text.strip()
            events.append(Event(
                name=title,
                time=time,
                link=link,
                location = location if 'event has passed' not in location else 'N/A'
            ))
        return events
    
    def _scrape_event(self, text: str): # TODO
        print("s")
        print("")

    def _get_past_events(self): # use this to get past_events doing an GET request on meetup.com
        return self._scrape_events(self._request(self._past_events_url))

    def _get_upcoming_events(self): # use this to get upcoming_events doing an GET request on meetup.com
        return self._scrape_events(self._request(self._upcoming_events_url))
    
    def get_event_detail(self, event_url: str): # TODO
        return self._scrape_event(self._request(event_url))
    
    @property    
    def past_events(self): # use this to get past_events using a cached result
        current_timestamp = time.time()
        if current_timestamp - self._past_events_timestamp >= CACHE_LIFETIME:
            self._past_events_timestamp = current_timestamp
            self._past_events = self._get_past_events()
            log.info(f"Community Manager scraped {len(self._past_events)} past events")
        return self._past_events

    @property    
    def upcoming_events(self): # use this to get upcoming_events using a cached result
        current_timestamp = time.time()
        if current_timestamp - self._upcoming_events_timestamp >= CACHE_LIFETIME:
            self._upcoming_events_timestamp = current_timestamp
            self._upcoming_events = self._get_upcoming_events()
            log.info(f"Community Manager scraped {len(self._upcoming_events)} upcoming events")
        return self._upcoming_events
