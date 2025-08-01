#!/usr/bin/env python3

from session import Session
from courts import Courts
import json

session = Session('kavunshiva@gmail.com', 'poopytennis').session
print('08/05/2025', 'Clay')
print(json.dumps(Courts('08/05/2025', 'Clay', session).free_court_times, indent=4))
print('08/05/2025', 'Hard')
print(json.dumps(Courts('08/05/2025', 'Hard', session).free_court_times, indent=4))
