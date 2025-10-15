#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


DATA_FILE_PATH = Path(__file__).resolve().parent / "data.json"
APPOINTMENTS_FILE_PATH = Path(__file__).resolve().parent / "appointments.json"


@dataclass(frozen=True)
class Technician:
    technician_id: int
    name: str
    zones: Set[str]
    business_units: Set[str]


def load_data(data_file_path: Path = DATA_FILE_PATH) -> Dict:
    """Load the JSON data file into a dictionary."""
    with data_file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_technicians(raw_data: Dict) -> List[Technician]:
    """Convert raw technician profiles into Technician objects."""
    technicians: List[Technician] = []
    for t in raw_data.get("Technician_Profiles", []):
        technicians.append(
            Technician(
                technician_id=int(t["id"]),
                name=str(t["name"]),
                zones=set(map(str, t.get("zones", []))),
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
    Load appointments file as a mapping of technician_id -> { iso_datetime: appointment_id }.
    The file is created on demand if it does not exist.
    """
    if not appointments_file_path.exists():
        return {}
    try:
        with appointments_file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure expected structure
            return {str(k): dict(v) for k, v in data.items()}
    except Exception:
        # If unreadable/corrupt, start fresh in-memory
        return {}


def save_appointments(appointments: Dict[str, Dict[str, str]], appointments_file_path: Path = APPOINTMENTS_FILE_PATH) -> None:
    """Persist appointments mapping to disk."""
    with appointments_file_path.open("w", encoding="utf-8") as f:
        json.dump(appointments, f, indent=2, ensure_ascii=False)


def find_matching_technicians(trade: str, zip_code: str, technicians: List[Technician]) -> List[Technician]:
    """Filter technicians by business unit (trade) and coverage zone (zip)."""
    return [t for t in technicians if trade in t.business_units and zip_code in t.zones]


def is_technician_available(technician: Technician, service_time: datetime, appointments: Dict[str, Dict[str, str]]) -> bool:
    """
    Availability model: a technician is considered busy if an appointment exists at the exact requested start time.
    Otherwise available.
    """
    tech_key = str(technician.technician_id)
    time_key = service_time.strftime("%Y-%m-%d %H:%M")
    return time_key not in appointments.get(tech_key, {})


def book_first_available(
    trade: str,
    zip_code: str,
    service_time: datetime,
    technicians: List[Technician],
    appointments: Dict[str, Dict[str, str]],
) -> Optional[Tuple[Technician, str]]:
    """
    Book the first available technician matching trade and zone. Returns (technician, confirmation_id) if booked.
    """
    matches = find_matching_technicians(trade=trade, zip_code=zip_code, technicians=technicians)
    if not matches:
        return None

    time_key = service_time.strftime("%Y-%m-%d %H:%M")
    for tech in matches:
        if is_technician_available(tech, service_time, appointments):
            tech_key = str(tech.technician_id)
            appointments.setdefault(tech_key, {})
            confirmation_id = f"A-{tech.technician_id}-{time_key.replace(' ', 'T').replace(':', '')}"
            appointments[tech_key][time_key] = confirmation_id
            return tech, confirmation_id
    return None


def derive_locations_and_hours(technicians: List[Technician]) -> Dict[str, str]:
    """
    Derive coverage hours per zone from technician zones.

    Assumption: Zones (zip codes) covered by multiple technicians have extended hours due to greater coverage.
      - If 2+ technicians cover a zone: Mon–Sat 08:00–18:00
      - Otherwise: Mon–Fri 09:00–17:00
    """
    zone_counts: Dict[str, int] = {}
    for tech in technicians:
        for z in tech.zones:
            zone_counts[z] = zone_counts.get(z, 0) + 1

    hours_by_zone: Dict[str, str] = {}
    for zone, count in sorted(zone_counts.items(), key=lambda kv: kv[0]):
        if count >= 2:
            hours_by_zone[zone] = "Mon–Sat 08:00–18:00"
        else:
            hours_by_zone[zone] = "Mon–Fri 09:00–17:00"
    return hours_by_zone


def derive_services_offered(technicians: List[Technician]) -> List[str]:
    """Return a sorted list of unique services derived from technician business_units."""
    services: Set[str] = set()
    for tech in technicians:
        services |= tech.business_units
    return sorted(services)


def ask(prompt: str) -> str:
    """Prompt the user and return the stripped input."""
    return input(prompt).strip()


def run_booking_flow(technicians: List[Technician]) -> None:
    print("\nLet's book your appointment. You'll be asked a few quick questions.")

    # Service/trade
    trade: Optional[str] = None
    while trade is None:
        trade_input = ask("Service needed (e.g., plumber, electrician, hvac): ")
        normalized = normalize_trade(trade_input)
        if normalized is None:
            print("Sorry, I didn't catch that trade. Try 'plumber', 'electrician', or 'hvac'.")
            continue
        trade = normalized

    # Date & time
    service_time: Optional[datetime] = None
    while service_time is None:
        dt_input = ask("Preferred date & time (YYYY-MM-DD HH:MM, 24h): ")
        parsed = parse_datetime(dt_input)
        if parsed is None:
            print("Please use format YYYY-MM-DD HH:MM, for example 2025-10-21 14:30.")
            continue
        service_time = parsed

    # Zip code
    zip_code: Optional[str] = None
    while zip_code is None:
        zip_input = ask("Service zip code (5 digits): ")
        digits_only = "".join(ch for ch in zip_input if ch.isdigit())
        if len(digits_only) != 5:
            print("Please enter a valid 5-digit zip code.")
            continue
        zip_code = digits_only

    appointments = load_appointments()
    booking = book_first_available(
        trade=trade,
        zip_code=zip_code,
        service_time=service_time,
        technicians=technicians,
        appointments=appointments,
    )

    if booking is None:
        print(
            "\nThanks! I checked our schedule and service area, but there is no availability matching "
            f"{trade} in {zip_code} at {service_time.strftime('%Y-%m-%d %H:%M')}. "
            "Please try a different time or service zip."
        )
        return

    tech, confirmation_id = booking
    save_appointments(appointments)

    print(
        "\nYou're all set!\n"
        f"- Confirmation: {confirmation_id}\n"
        f"- Technician: {tech.name}\n"
        f"- Service: {trade}\n"
        f"- When: {service_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"- Where (zip): {zip_code}\n"
    )


def run_faq_flow(technicians: List[Technician]) -> None:
    print("\nAsk your question (e.g., 'What locations do you serve?', 'What services do you offer?').")
    q = ask("> ")
    text = q.lower()

    if any(k in text for k in ["location", "locations", "serve", "service area", "zip", "hours", "open"]):
        hours_by_zone = derive_locations_and_hours(technicians)
        if not hours_by_zone:
            print("We are not currently serving any locations.")
            return
        print("\nWe currently serve these zip codes with the following hours:")
        for zone, hours in hours_by_zone.items():
            print(f"- {zone}: {hours}")
        return

    if any(k in text for k in ["service", "services", "offer", "do you handle", "what do you do"]):
        services = derive_services_offered(technicians)
        if not services:
            print("We don't have any services listed at the moment.")
            return
        print("\nWe offer the following services:")
        for s in services:
            print(f"- {s}")
        return

    print("\nSorry, I can help with locations/hours or services offered. Try asking one of those.")


def main() -> None:
    raw = load_data()
    technicians = build_technicians(raw)

    print("Welcome to the Service Assistant CLI chatbot!")
    print("- Type 'book' to book an appointment")
    print("- Type 'faq' to ask about locations/hours or services offered")
    print("- Type 'quit' to exit")

    while True:
        choice = ask("\nWhat would you like to do? (book/faq/quit): ").lower()
        if choice in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if choice == "book":
            run_booking_flow(technicians)
            continue
        if choice == "faq":
            run_faq_flow(technicians)
            continue
        print("Please choose 'book', 'faq', or 'quit'.")


if __name__ == "__main__":
    main()


