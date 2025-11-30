# Onward Ticket Platform Concept

This repository captures the initial design for an onward ticket platform similar to https://onwardticket.com/en. The goal is to issue verifiable temporary travel itineraries that customers can purchase quickly, receive via email, and optionally cancel once their visa or booking process is complete.

## What is here
- A concise product brief outlining target users, value proposition, and key flows.
- A systems overview describing the services, data model, and third-party integrations required to support issuing onward tickets.
- An API sketch for the core workflow of creating orders, paying, and delivering tickets.

## Next steps
- Pick a backend framework (e.g., FastAPI, Django, or Rails) and scaffold services following the architecture in `docs/onward_ticket_plan.md`.
- Set up continuous integration, automated tests, and secrets management for third-party providers (email/SMS, payment, document storage).
- Build a minimal UI (web or mobile) for purchase and order tracking.

See `docs/onward_ticket_plan.md` for details.
