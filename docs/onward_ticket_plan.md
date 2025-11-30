# Onward Ticket Platform Design

## Product summary
- **Goal:** Sell short-term, cancellable travel itineraries that can be used as proof of onward travel for visa or check-in requirements.
- **Users:** Travelers needing proof of onward travel, visa agencies, and partners who resell tickets via API or white-label flows.
- **Core flows:**
  1. Customer enters travel route and date window.
  2. System reserves a verifiable itinerary through a GDS/OTA partner or synthetic PNR service.
  3. Payment is taken instantly; receipt and itinerary PDF/PNR are delivered by email/SMS.
  4. Ticket auto-expires or can be cancelled/refunded according to policy.

## Experience principles
- **Speed:** Checkout completes in under 2 minutes with minimal form fields.
- **Transparency:** Clear validity window, cancellation policy, and verification instructions.
- **Trust:** Deliver PNR that can be verified via airline or GDS tools; include support contact and SLA.
- **Automation-first:** Minimize manual intervention through webhooks and background jobs.

## Architecture overview
```
+-----------------+      +-------------------+       +---------------------+
| Web / Mobile UI | ---> | API Gateway / BFF | ----> | Ticket Service      |
+-----------------+      +-------------------+       | - PNR management    |
         ^                       |                   | - Inventory sources |
         |                       v                   +---------------------+
         |              +-------------------+       +---------------------+
         |              | Payments Service  | <---- | Payment Providers   |
         |              +-------------------+       +---------------------+
         |                       |                   +---------------------+
         |                       v                   | Notification Svc    |
         |              +-------------------+        | - Email/SMS         |
         |              | Notification Svc  |        | - Templates         |
         |              +-------------------+        +---------------------+
         |                       |                   +---------------------+
         |                       v                   | Identity & Access   |
         |              +-------------------+        +---------------------+
         |              | Order Database    |
         |              +-------------------+
```

### Services
- **API Gateway/BFF:** Auth, request validation, rate limiting, session handling. Exposes REST/GraphQL for web, mobile, and partner API.
- **Ticket Service:** Coordinates PNR creation with providers, issues PDFs, tracks validity windows, and schedules expiration/cancellation jobs.
- **Payments Service:** Handles pricing, fees, currency conversion, provider routing (e.g., Stripe/Adyen), webhook processing, and refund logic.
- **Notification Service:** Email/SMS templates, delivery status tracking, and customer support routing.
- **Identity & Access:** Customer accounts, OAuth for partners, signed URLs for ticket delivery.
- **Admin/Support:** Dashboard for manual issuance, refunds, and compliance audits.

### Data model (high level)
- **User:** id, email/phone, verification status, kyc fields (if needed), partner_id.
- **Order:** id, user_id, status (pending, paid, issued, delivered, expired, refunded), price, currency, coupon_id, expires_at.
- **Itinerary:** id, order_id, origin, destination, departure_at, return_at (optional), passengers, pnr_locator, supplier_reference, status.
- **Payment:** id, order_id, provider, intent_id, status, amount, currency, fee_breakdown, refund_reference.
- **Notification:** id, order_id, channel, template, status, sent_at, provider_message_id.

### External integrations
- **GDS/OTA/Synthetic PNR:** Amadeus, Sabre, Kiwi (Tequila), Duffel, or specialized onward-ticket APIs. Include fallback provider and automated verification check.
- **Payments:** Stripe/Adyen with webhooks for success/failure, 3DS, fraud checks, and refund initiation.
- **Notifications:** SendGrid/Postmark for email, Twilio for SMS; signed download URLs for PDF delivery.
- **Storage:** Object storage for PDFs (S3/GCS), secrets management (Vault/SM), and observability (OpenTelemetry, Prometheus, Sentry).

## API sketch (REST)
- `POST /v1/orders` — create an order with itinerary preferences and passenger details; returns pricing and payment intent.
- `POST /v1/orders/{id}/confirm` — confirm payment and lock itinerary; idempotent.
- `POST /v1/orders/{id}/issue` — issue or reissue ticket; typically triggered by payment success webhook.
- `GET /v1/orders/{id}` — fetch order status, delivery assets (PDF, PNR), and expiration time.
- `POST /v1/orders/{id}/cancel` — request cancellation/refund if policy allows.
- `POST /v1/webhooks/payments` — handle payment provider webhooks.
- `POST /v1/webhooks/tickets` — handle GDS/OTA status webhooks.

## Operational considerations
- **Reliability:** use retries with jitter for provider APIs; circuit breakers and timeouts; background queues for issuance and notifications.
- **Fraud & abuse:** rate limits, velocity checks per identity/device, optional identity verification, and order review queue.
- **Compliance:** PCI scope isolation for payments, GDPR for data retention, and audit logging for admin actions.
- **Metrics:** issuance success rate, time-to-issue, refund rate, chargeback rate, delivery success, support response time.

## Delivery roadmap (MVP -> V1)
1. **MVP (2-3 weeks):** Single provider integration, card payments, email delivery with signed PDF, manual admin ops.
2. **V0.9 (4-6 weeks):** Add SMS delivery, auto-expiry jobs, partner API keys, and webhooks.
3. **V1 (8-10 weeks):** Multi-provider routing, automated verification, support workflows, localization, and analytics dashboard.

## UI/UX outline
- **Landing/Checkout:** origin, destination, travel date, passenger count, upsells (priority delivery, insurance), price breakdown, policy summary.
- **Order status page:** live status (issuing, delivered, expires_in), download links, verification instructions, support chat link.
- **Admin:** search orders by email/PNR, resend notifications, refund/cancel, provider health view.

## Engineering next steps
- Choose stack and scaffold repo (monolith or modular services) with Docker and CI.
- Define configuration/secrets strategy and local dev environment with mock providers.
- Start with contract tests for providers and webhook flows before UI polish.
