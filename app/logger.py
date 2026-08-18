import logging
import os

# create logs folder if it doesn't exist
os.makedirs("logs", exist_ok=True)

# configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/frontdesk.log"),  
        logging.StreamHandler(),                    
    ]
)

logger = logging.getLogger("frontdesk")