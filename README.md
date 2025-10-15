## Service Assistant CLI Chatbot

A simple Python CLI chatbot that books appointments and answers FAQs using `data.json`.

### Requirements
- Python 3.9+

```
pip install -r requirements.txt
```

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
  - Locations: lists zip codes covered from technician coverage:
  - Services Offered: lists unique `business_units` across all technicians.

### Examples

#### Flow 1 (successful booking)
```
❯ python chatbot.py
Agent: Welcome to the Service Assistant CLI chatbot!

- Type 'book' to book an appointment
- Type 'faq' to ask about locations/hours or services offered
- Type 'quit' to exit

Agent: What would you like to do today? (book/faq/quit):

You: book

Agent: Let's book your appointment. I'll ask you a few quick questions.

Agent: What service do you need? (e.g., plumber, electrician, hvac): 

You: plumber

Agent: What is your preferred date & time for the appointment (1h)? (YYYY-MM-DD HH:MM,
24h): 

You: 2025-10-21 14:30

Agent: Service zip code (5 digits): 

You: 94113

Agent: You're all set!

- Confirmation: d8b8d482-9760-485d-99e4-f05930211a4b
- Technician: Gina Garza
- Service: plumbing
- When: 2025-10-21 14:30
- Where (zip): 94113

Agent: What would you like to do today? (book/faq/quit):

You: quit

Agent: Goodbye!
```

#### Flow 2 (no technicians available at time)

```
❯ python chatbot.py
Agent: Welcome to the Service Assistant CLI chatbot!

- Type 'book' to book an appointment
- Type 'faq' to ask about locations/hours or services offered
- Type 'quit' to exit

Agent: What would you like to do today? (book/faq/quit):

You: book

Agent: Let's book your appointment. I'll ask you a few quick questions.

Agent: What service do you need? (e.g., plumber, electrician, hvac): 

You: plumber

Agent: What is your preferred date & time for the appointment (1h)? (YYYY-MM-DD HH:MM,
24h): 

You: 2025-10-21 14:30

Agent: Service zip code (5 digits): 

You: 94113

Agent: 
Thanks! I checked our schedule and service area, but there is no availability matching
plumbing in 94113 at 2025-10-21 14:30. Please try a different time or service zip.

Agent: What would you like to do today? (book/faq/quit):

You: quit

Agent: Goodbye!
```

#### Flow 3 (FAQ)

```
❯ python chatbot.py
Agent: Welcome to the Service Assistant CLI chatbot!

- Type 'book' to book an appointment
- Type 'faq' to ask about locations/hours or services offered
- Type 'quit' to exit

Agent: What would you like to do today? (book/faq/quit):

You: faq

Agent: What question do you have today? (e.g., 'What locations do you serve?', 'What 
services do you offer?')

You: What locations do you serve?

Agent: We currently serve these zip codes:

- 94101
- 94106
- 94107
- 94111
- 94113
- 94115
- 94117
- 94118
- 94119
- 94120
- 94133

Agent: What would you like to do today? (book/faq/quit):

You: faq

Agent: What question do you have today? (e.g., 'What locations do you serve?', 'What 
services do you offer?')

You: What services do you offeR?

Agent: We offer the following services:

- electrical
- hvac
- plumbing

Agent: What would you like to do today? (book/faq/quit):

You: quit

Agent: Goodbye!
```
