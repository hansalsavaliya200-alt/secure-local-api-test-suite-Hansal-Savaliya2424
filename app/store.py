"""In-memory data with FICTIONAL users and tickets. Replace with a real database for real use."""
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache

from .security import hash_password

# Fictional demo accounts for local use only.
DEMO_ACCOUNTS = {"alice": "user", "bob": "user", "carol": "agent", "dave": "admin"}
DEMO_PASSWORDS = {name: f"{name}-demo-Passw0rd!" for name in DEMO_ACCOUNTS}


@dataclass
class User:
    username: str
    role: str
    password_hash: str
    disabled: bool = False


@lru_cache(maxsize=None)
def _seed_hash(username: str) -> str:
    return hash_password(DEMO_PASSWORDS[username])  # hashed once per process to keep tests fast


class Store:
    def __init__(self):
        self.users = {name: User(name, role, _seed_hash(name)) for name, role in DEMO_ACCOUNTS.items()}
        self.tickets = {}
        self.add_ticket("alice", "Printer on floor 2 is offline", "Shows a paper jam error.", "normal")
        self.add_ticket("bob", "Need a replacement keyboard", "Two keys stopped working.", "low")

    def add_ticket(self, owner, title, description, priority):
        ticket_id = str(uuid.uuid4())
        now = int(time.time())
        self.tickets[ticket_id] = {
            "id": ticket_id, "owner": owner, "title": title, "description": description,
            "priority": priority, "status": "open", "created_at": now, "updated_at": now,
        }
        return self.tickets[ticket_id]
