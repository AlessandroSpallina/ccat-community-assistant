import httpx
from typing import List
from pydantic import BaseModel
from bs4 import BeautifulSoup
from cat.log import log
import time
import json


CACHE_LIFETIME = 86400 # seconds


class Event(BaseModel):
    name: str
    time: str
    link: str
    location_address: str = 'N/A'
    location_building: str = 'N/A'
    # location_google_maps: str = 'N/A'
    details: str = 'N/A' # would be nice to automatically ingest linked pages
    # slide_links: List[str] = [] # obtained from https://speakerdeck.com/pythontorino

    def __repr__(self) -> str:
        # I'm not sure this is the best way to format event info
        return f'\nEvent `{self.name}`\n- time: `{self.time}`\n- link: `{self.link}`\n- location_address: `{self.location_address}`,\n- location_building: `{self.location_building}`'


class Meetup:
    def __init__(self, organization_name, auth_cookie=""):
        self._organization_name = organization_name
        self._auth_cookie = auth_cookie
        self._past_events_url = f'https://www.meetup.com/{organization_name}/events/?type=past'
        self._upcoming_events_url = f'https://www.meetup.com/{organization_name}/events/?type=upcoming'

        self._past_events_timestamp = -1 # filled with the timestamp of the last update
        self._past_events = []
        self._upcoming_events_timestamp = -1 # filled with the timestamp of the last update
        self._upcoming_events = []
    
    def _request(self, url: str, method='GET') -> list[Event]:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }
        if self._auth_cookie != "":
            headers['Cookie'] = self._auth_cookie

        r = httpx.request(method, url, headers=headers)
        r.raise_for_status()
        time.sleep(5) # let's hope meetup.com doesn't ban our IP
        return r.text
    
    def _scrape_events(self, url: str):
        text = self._request(url)
        soup = BeautifulSoup(text, 'html.parser')
        
        event_divs = soup.select('div[id^="e-"], div[id^="ep-"]')

        events = []
        for event_div in event_divs:
            # Extract time and title from each div
            time = event_div.find('time').text.strip()
            title = event_div.find('span', class_='ds-font-title-3').text.strip()
            link = event_div.find('a')['href']
            event = Event(
                name=title,
                time=time,
                link=link,
            )
            events.append(self._scrape_event(event))

        return events
    
    def _scrape_event(self, event: Event):
        text = self._request(event.link)
        soup = BeautifulSoup(text, 'html.parser')
        
        divs = soup.find_all('script', {'type': 'application/ld+json'})
        for div in divs:
            if json.loads(div.string).get('location') != None:
                data = json.loads(div.string)
                location = data.get('location', {})
                event.location_address = location.get('address', {}).get('streetAddress', 'N/A')
                event.location_building = location.get('name', 'N/A')
                break

        event.details = soup.find('div', id='event-details').find('div', class_='break-words').text.strip()

        return event

    def _get_past_events(self): # use this to get past_events doing an GET request on meetup.com
        return self._scrape_events(self._past_events_url)

    def _get_upcoming_events(self): # use this to get upcoming_events doing an GET request on meetup.com
        return self._scrape_events(self._upcoming_events_url)
    
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
