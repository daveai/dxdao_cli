from dotenv import load_dotenv
from scripts.proposals import fetch_mainnet


load_dotenv()

if __name__ == "__main__":
    fetch_mainnet()

