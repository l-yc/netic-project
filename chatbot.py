from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from rich.console import Console
import uuid

from intent import Intent, detect_intent

DATA_FILE_PATH = Path(".") / "data.json"
APPOINTMENTS_FILE_PATH = Path(".") / "appointments.jsonl"
console = Console()
AGENT_TAG = "[bold green]Agent[/bold green]"
USER_TAG = "[bold blue]You[/bold blue]"


@dataclass(frozen=True)
class Location:
    location_id: int
    name: str
    address: str


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    contact: str


@dataclass(frozen=True)
class Technician:
    technician_id: int
    name: str
    zones: Set[str]
    business_units: Set[str]


@dataclass(frozen=True)
class Appointment:
    appointment_id: uuid.UUID
    technician_id: int
    start: datetime
    end: datetime
    trade: str


def load_data(data_file_path: Path = DATA_FILE_PATH) -> Dict:
    """Load the JSON data file into a dictionary."""
    with data_file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_locations(raw_data: Dict) -> Dict[str, Location]:
    """Convert raw location profiles into Location objects."""
    locations = {}
    for t in raw_data.get("Location_Profiles", []):
        locations[t["id"]] = Location(
                    location_id=t["id"],
                    name=t["name"],
                    address=t.get("address")
                )
    return locations


def build_customers(raw_data: Dict) -> Dict[str, Customer]:
    """Convert raw customer profiles into Customer objects."""
    customers = {}
    for t in raw_data.get("Customer_Profiles", []):
        customers[t["id"]] = Customer(
                    customer_id=t["id"],
                    name=t["name"],
                    contact=t.get("contact")
                )
    return customers


def build_technicians(raw_data: Dict) -> List[Technician]:
    """Convert raw technician profiles into Technician objects."""
    technicians: List[Technician] = []
    for t in raw_data.get("Technician_Profiles", []):
        technicians.append(
            Technician(
                technician_id=t["id"],
                name=t["name"],
                zones=set(t.get("zones", [])),
                business_units=set(map(str.lower, t.get("business_units", []))),
            )
        )
    return technicians


def normalize_trade(user_input: str) -> Optional[str]:
    """
    Normalize user-provided trade strings to match business_units.

    Examples:
    - "plumber" -> "plumbing"
    - "electrician" -> "electrical"
    - "hvac" -> "hvac"
    """
    text = user_input.strip().lower()
    if not text:
        return None

    synonyms = {
        "plumber": "plumbing",
        "plumbing": "plumbing",
        "electrician": "electrical",
        "electrical": "electrical",
        "hvac": "hvac",
        "air conditioning": "hvac",
        "aircon": "hvac",
        "ac": "hvac",
    }

    return synonyms.get(text)


def parse_datetime(user_input: str) -> Optional[datetime]:
    """
    Parse a date/time from user input. Accepts formats:
    - YYYY-MM-DD HH:MM (24-hour)
    - YYYY-MM-DDTHH:MM (ISO-like)
    """
    text = user_input.strip()
    if not text:
        return None

    tried_formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
    for fmt in tried_formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def load_appointments(appointments_file_path: Path = APPOINTMENTS_FILE_PATH) -> Dict[str, Dict[str, str]]:
    """
    Load appointments file as a mapping of technician_id -> [].
    The file is created on demand if it does not exist.
    """
    if not appointments_file_path.exists():
        return []

    with appointments_file_path.open("r", encoding="utf-8") as f:
        appointments = []
        for line in f:
            data = json.loads(line)
            appointments.append(Appointment(
                appointment_id=uuid.UUID(data["appointment_id"]),
                technician_id=data["technician_id"],
                start=datetime.fromisoformat(data["start"]),
                end=datetime.fromisoformat(data["end"]),
                trade=data["trade"]
            ))
        return appointments


def save_appointments(appointments: List[Appointment], appointments_file_path: Path = APPOINTMENTS_FILE_PATH) -> None:
    """Persist appointments mapping to disk."""
    with appointments_file_path.open("w", encoding="utf-8") as f:
        for appt in appointments:
            appt_dict = asdict(appt)
            appt_dict['appointment_id'] = str(appt.appointment_id)
            appt_dict['start'] = appt.start.isoformat()
            appt_dict['end'] = appt.end.isoformat()
            f.write(json.dumps(appt_dict) + "\n")


def find_matching_technicians(trade: str, zip_code: str, technicians: List[Technician]) -> List[Technician]:
    """Filter technicians by business unit (trade) and coverage zone (zip)."""
    return [t
            for t in technicians
            if trade in t.business_units and zip_code in t.zones]


def is_technician_available(technician: Technician, start: datetime, end: datetime, appointments: List[Appointment]) -> bool:
    for appt in appointments:
        if appt.technician_id != technician.technician_id:
            continue

        if not (end <= appt.start or appt.end <= start):
            return False

    return True


def book_first_available(
    trade: str,
    zip_code: str,
    service_time: datetime,
    technicians: List[Technician],
    appointments: List[Appointment],
) -> Optional[Tuple[Technician, str]]:
    """
    Book the first available technician matching trade and zone. Returns (technician, confirmation_id) if booked.
    """
    matches = find_matching_technicians(trade=trade, zip_code=zip_code, technicians=technicians)
    if not matches:
        return None

    for tech in matches:
        start = service_time
        end = service_time + timedelta(hours=1)

        if is_technician_available(tech, start, end, appointments):
            confirmation_id = uuid.uuid4()
            appointments.append(Appointment(
                appointment_id=confirmation_id,
                technician_id=tech.technician_id,
                start=start,
                end=end,
                trade=trade,
            ))
            return tech, confirmation_id

    return None


def derive_locations(technicians: List[Technician]) -> List[str]:
    set_of_zones = set()
    for tech in technicians:
        set_of_zones |= tech.zones
    return sorted(set_of_zones)


def derive_services_offered(technicians: List[Technician]) -> List[str]:
    """Return a sorted list of unique services derived from technician business_units."""
    services: Set[str] = set()
    for tech in technicians:
        services |= tech.business_units
    return sorted(services)


def say(prompt: str) -> str:
    """Say something to the user."""
    console.print(f"{AGENT_TAG}: {prompt}\n")

def ask(prompt: str) -> str:
    """Prompt the user with a chatbot style and return the stripped input."""
    console.print(f"{AGENT_TAG}: {prompt}\n")
    result = console.input(f"{USER_TAG}: ").strip()
    print()
    return result


def run_booking_flow(locations: List[Location], 
                     customers: List[Customer], 
                     technicians: List[Technician],
                     appointments: List[Appointment]) -> None:
    say("Let's book your appointment. I'll ask you a few quick questions.")

    # Service/trade
    trade: Optional[str] = None
    while trade is None:
        trade_input = ask("What service do you need? (e.g., plumber, electrician, hvac): ")
        normalized = normalize_trade(trade_input)
        if normalized is None:
            say("Sorry, I didn't catch that trade. Try 'plumber', 'electrician', or 'hvac'.")
            continue
        trade = normalized

    # Date & time
    service_time: Optional[datetime] = None
    while service_time is None:
        dt_input = ask("What is the preferred date & time for the appointment (1h)? (YYYY-MM-DD HH:MM, 24h): ")
        parsed = parse_datetime(dt_input)
        if parsed is None:
            say("Please use format YYYY-MM-DD HH:MM, for example 2025-10-21 14:30.")
            continue
        service_time = parsed

    # Zip code
    zip_code: Optional[str] = None
    while zip_code is None:
        zip_input = ask("What is the customer zip code? (5 digits): ")
        digits_only = "".join(ch for ch in zip_input if ch.isdigit())
        if len(digits_only) != 5:
            say("Please enter a valid 5-digit zip code.")
            continue
        zip_code = digits_only

    booking = book_first_available(
        trade=trade,
        zip_code=zip_code,
        service_time=service_time,
        technicians=technicians,
        appointments=appointments,
    )

    if booking is None:
        say(
            "\nThanks! I checked our schedule and service area, but there is no availability matching "
            f"{trade} in {zip_code} at {service_time.strftime('%Y-%m-%d %H:%M')}. "
            "Please try a different time or service zip."
        )
        return

    tech, confirmation_id = booking

    #location_profile = locations[zip_code]
    #customer_profile = customers[zip_code]

    say("You're all set!")
    print(
        f"- Confirmation: {confirmation_id}\n"
        f"- Technician: {tech.name}\n"
        f"- Service: {trade}\n"
        f"- When: {service_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"- Where (zip): {zip_code}\n"
        #f"- Where (zip): {location_profile.name} -> {location_profile.address}\n"
        #f"- Customer: {customer_profile.name} ({customer_profile.contact})\n"
    )


def run_faq_flow(technicians: List[Technician]) -> None:
    q = ask("What question do you have today? (e.g., 'What locations do you serve?', 'What services do you offer?')")
    inferred_intent = detect_intent(q)

    def faq_location_handler():
        locations = derive_locations(technicians)
        if not locations:
            say("We are not currently serving any locations.")
            return

        say("We currently serve these zip codes:")
        for location in locations:
            print(f"- {location}")
        print()

    def faq_services_handler():
        services = derive_services_offered(technicians)
        if not services:
            say("We don't have any services listed at the moment.")
            return

        say("We offer the following services:")
        for s in services:
            print(f"- {s}")
        print()
    
    intent_handlers = {
        Intent.FAQ_LOCATIONS: faq_location_handler,
        Intent.FAQ_SERVICES: faq_services_handler,
    }

    handler = intent_handlers.get(inferred_intent)
    if handler is None:
        say("\nSorry, I can help with locations/hours or services offered. Try asking one of those.")
        return

    handler()


def main() -> None:
    raw = load_data()
    locations = build_locations(raw)
    customers = build_customers(raw)
    technicians = build_technicians(raw)
    appointments = load_appointments()

    say(f"Welcome to the Service Assistant CLI chatbot!")
    print("- Type 'book' to book an appointment")
    print("- Type 'faq' to ask about locations/hours or services offered")
    print("- Type 'quit' to exit")
    print()

    while True:
        choice = ask("What would you like to do today? (book/faq/quit):").lower()
        if choice in ("quit", "exit", "q"):
            say("Goodbye!")
            save_appointments(appointments)
            break
        elif choice == "book":
            run_booking_flow(locations, customers, technicians, appointments)
            continue
        elif choice == "faq":
            run_faq_flow(technicians)
        else:
            say("Please choose 'book', 'faq', or 'quit'.")


if __name__ == "__main__":
    main()


