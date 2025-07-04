from django.core.management import call_command
from datetime import datetime
import os

def dump_data():
    os.makedirs("dumps", exist_ok=True)
    filename = f"dumps/dump_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w") as f:
        call_command("dumpdata", stdout=f)
    print(f"Dumped data to {filename}")
