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
        return f'Event: {{"name":{self.name}, "time",:{self.time}, "link":{self.link}, "location",:{self.location}, "details":{self.details}, "slide_links",:{self.slide_links}}}'



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
        #div_elements = soup.find_all('div', class_='grid gap-2')

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

        



# r = httpx.('https://www.meetup.com/python-torino/events/?type=past')

# if r.status_code == 200:
#     soup = BeautifulSoup(r.text, 'html.parser')
    
#     div_elements = soup.find_all('div', class_='grid gap-2')

#     for div in div_elements:
#         # Extract time and title from each div
#         time_element = div.find('time')  # Assuming time is wrapped in a 'time' tag
#         title_element = div.find('span', class_='ds-font-title-3')  # Assuming title is inside a span tag with the specified class

#         # Extract text content
#         time = time_element.text.strip() if time_element else 'N/A'
#         title = title_element.text.strip() if title_element else 'N/A'

#         # Print or do something with the extracted information
#         print(f'Time: {time}')
#         print(f'Title: {title}')
#         print('-' * 30)

# else:
#     print(f"Failed to retrieve the webpage. Status code: {r.status_code}")
