## Service Assistant CLI Chatbot

A simple Python CLI chatbot that books appointments and answers FAQs using `data.json`.

### Requirements
- Python 3.9+

### Data
- The bot reads technicians, customers, and locations from `data.json`.
- Bookings are persisted to `appointments.json` in the project root.

### Run

```bash
python3 chatbot.py
```

### Flows

- **Book Appointment**
  - Prompts for: service (plumber/electrician/hvac), date & time (`YYYY-MM-DD HH:MM`), and 5-digit zip.
  - Matches a technician who: provides the service, serves the zip, and is available at the requested time.
  - On success: confirms with a confirmation ID and saves to `appointments.json`.
  - If none fit: returns a friendly no-availability message.

- **Answer FAQs**
  - Locations/Hours: derives hours per zip code from technician coverage:
    - If 2+ technicians cover a zip: `Mon–Sat 08:00–18:00`
    - Else: `Mon–Fri 09:00–17:00`
  - Services Offered: lists unique `business_units` across all technicians.

### Examples

```text
Welcome to the Service Assistant CLI chatbot!
- Type 'book' to book an appointment
- Type 'faq' to ask about locations/hours or services offered
- Type 'quit' to exit

What would you like to do? (book/faq/quit): book
Let's book your appointment. You'll be asked a few quick questions.
Service needed (e.g., plumber, electrician, hvac): plumber
Preferred date & time (YYYY-MM-DD HH:MM, 24h): 2025-10-21 14:30
Service zip code (5 digits): 94133

You're all set!
- Confirmation: A-4697-2025-10-21T1430
- Technician: Michael Page
- Service: plumbing
- When: 2025-10-21 14:30
- Where (zip): 94133
```

```text
What would you like to do? (book/faq/quit): faq
Ask your question (e.g., 'What locations do you serve?', 'What services do you offer?').
> What locations do you serve?

We currently serve these zip codes with the following hours:
- 94107: Mon–Fri 09:00–17:00
- 94111: Mon–Fri 09:00–17:00
- 94113: Mon–Fri 09:00–17:00
- 94115: Mon–Fri 09:00–17:00
- 94117: Mon–Fri 09:00–17:00
- 94118: Mon–Fri 09:00–17:00
- 94119: Mon–Sat 08:00–18:00
- 94120: Mon–Fri 09:00–17:00
- 94133: Mon–Sat 08:00–18:00
- 94106: Mon–Fri 09:00–17:00
- 94101: Mon–Fri 09:00–17:00
```


