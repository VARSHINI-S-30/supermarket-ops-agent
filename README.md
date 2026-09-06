# 🛒 Nebula Supermarket Ops Agent

> An AI-powered supermarket operations agent that enables supermarket owners to manage inventory, billing, customer credit, sales analytics, invoices, and business reports through a Telegram-based conversational interface.

---

## 📌 Overview

The **Nebula Supermarket Ops Agent** is an AI-driven supermarket operations system designed to simplify day-to-day store management through natural-language conversations.

Instead of using traditional dashboards or multiple administrative forms, the system allows the supermarket owner to interact with an **AI agent through Telegram**.

The agent can understand requests such as:

```text
"How much Maggi is in stock?"

"Create a bill for 2 packets of Maggi."

"Add 3 packets of Tata Salt."

"Which products are low in stock?"

"How much sales did we make today?"

"Generate the invoice."

"Show me products that need to be reordered."
````

The AI agent interprets the request, selects the appropriate business tool, executes the operation against the database, and returns the result through Telegram.

The system is designed with **tool-based business rules**, ensuring that critical operations such as stock deduction, billing, GST calculation, and credit handling are not performed purely by the language model.

---

## 🎯 Objectives

* Provide a conversational supermarket management system.
* Allow supermarket owners to operate the system through Telegram.
* Manage products and inventory using AI-assisted commands.
* Create and manage multi-turn customer bills.
* Prevent inventory overselling at the tool layer.
* Calculate GST and billing totals correctly.
* Support multiple payment modes.
* Manage customer credit / khata accounts.
* Generate PDF invoices automatically.
* Generate business analysis reports in PowerPoint format.
* Maintain persistent owner preferences across conversations.
* Provide sales, inventory, and business-health analytics.
* Support reliable and idempotent billing operations.

---

# 🤖 AI Agent Architecture

The system follows an **Agent-First Architecture** where the language model acts as the reasoning and orchestration layer.

```text
                    ┌───────────────────────┐
                    │      Store Owner      │
                    │                       │
                    │ Natural Language      │
                    │ Telegram Messages      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Telegram Bot       │
                    │                       │
                    │ Message Handling      │
                    │ Conversation Memory   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      AI Agent         │
                    │                       │
                    │ Intent Understanding  │
                    │ Reasoning             │
                    │ Tool Selection        │
                    │ Clarification         │
                    └───────────┬───────────┘
                                │
                         Tool Invocation
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
     │  Inventory   │   │   Billing    │   │  Analytics   │
     │    Tools     │   │    Tools     │   │    Tools     │
     └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │       SQLite DB       │
                    │                       │
                    │ Products              │
                    │ Customers             │
                    │ Bills                 │
                    │ Bill Items            │
                    │ Preferences           │
                    │ Telegram Sessions     │
                    └───────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
        ┌───────────────┐             ┌───────────────┐
        │ PDF Invoice   │             │ PPTX Report   │
        │ Generation    │             │ Generation    │
        └───────────────┘             └───────────────┘
```

---

# 🧠 Agent Control Loop

The AI agent follows a controlled execution loop.

```text
User Request
     ↓
Understand Intent
     ↓
Determine Required Information
     ↓
Select Appropriate Tool
     ↓
Execute Business Operation
     ↓
Validate Result
     ↓
If More Information Is Required
     ↓
Ask Clarifying Question
     ↓
Otherwise
     ↓
Generate Natural-Language Response
     ↓
Return Result to Telegram
```

This approach separates:

```text
AI Reasoning
      +
Business Logic
      +
Database Operations
```

This prevents the language model from directly modifying important business data.

---

# 🛠️ Core Capabilities

## 📦 Inventory Management

The agent can manage supermarket inventory through natural-language commands.

Supported operations include:

* Add new products
* Receive stock
* Check product stock
* Search products
* Identify low-stock products
* Generate reorder recommendations
* Update product pricing
* Manage GST information
* Track SKU and units

Example:

```text
Owner:
How much Maggi is available?

Agent:
Maggi currently has 39 packets in stock.
```

---

# 🧾 Billing System

The system supports **multi-turn conversational billing**.

A bill can be created and modified over multiple messages.

Example:

```text
Owner:
Create a bill.

Agent:
Bill #12 created. What would you like to add?

Owner:
Add 2 packets of Maggi.

Agent:
Added 2 packets of Maggi.

Owner:
Add 1 packet of Tata Salt.

Agent:
Added 1 packet of Tata Salt.

Owner:
Show the bill.

Agent:
Bill #12
Maggi: 2 × ₹...
Tata Salt: 1 × ₹...
GST: ₹...
Total: ₹...
```

The owner can then modify the bill before finalization.

Supported operations:

* Create bill
* Add item
* Update item quantity
* View bill
* Finalize bill
* Generate invoice
* Support multiple payment modes

---

# 🛡️ Overselling Protection

Inventory safety is implemented at the **tool/database layer** rather than relying only on the AI model.

For example:

```text
Available Stock = 6

Requested Quantity = 10
```

The billing tool rejects the transaction.

```text
❌ Insufficient stock.

Only 6 units are available.
Cannot add 10 units to the bill.
```

This prevents the AI agent from accidentally creating a bill that exceeds available inventory.

---

# 🔒 Idempotent Billing

The billing system supports **idempotent bill finalization**.

If the same finalized bill is finalized again, the system does not:

* Deduct stock again
* Create another payment
* Increase customer credit again

Example:

```text
First Finalization
        ↓
Bill Finalized
        ↓
Stock Deducted
        ↓
Payment Recorded

Retry Finalization
        ↓
Already Finalized
        ↓
No Additional Stock Deduction
```

This protects the system from duplicate operations caused by retries or repeated requests.

---

# 💰 Payment Modes

The system supports:

```text
Cash
UPI
Card
Credit
```

Payment mode validation is performed before finalizing a bill.

For credit transactions:

```text
Customer
     ↓
Bill
     ↓
Credit Payment
     ↓
Customer Khata Balance
```

Credit cannot be created for an unknown customer.

---

# 📒 Customer Credit / Khata

The system supports customer credit management.

Available operations include:

* Check customer credit
* Record credit payment
* Associate customers with bills
* Track outstanding balances

Example:

```text
Owner:
How much does Ravi owe?

Agent:
Ravi currently has ₹500 outstanding credit.
```

The system ensures credit-related operations are connected to known customer records.

---

# 🧮 GST & Billing Calculation

The billing system calculates:

```text
Subtotal
+
GST
=
Total Amount
```

For GST reporting, the system can also provide:

```text
Taxable Amount
CGST
SGST
Total GST
Grand Total
```

GST rates are validated before product and billing operations.

Supported GST values are validated within the range:

```text
0% – 100%
```

Money calculations use decimal-based arithmetic to reduce floating-point rounding problems.

---

# 💵 Pricing Validation

Product pricing follows business rules.

The system prevents:

```text
Selling Price < Cost Price
```

and:

```text
Selling Price > MRP
```

Valid pricing follows:

```text
Cost Price
     ↓
Selling Price
     ↓
MRP
```

This provides a basic business-rule guard against invalid product pricing.

---

# 🔄 Concurrent Stock Protection

Inventory write operations use database-level write locking.

The system uses SQLite transaction control with:

```text
BEGIN IMMEDIATE
```

This helps protect critical operations such as:

* Stock updates
* Bill item additions
* Bill item quantity updates
* Bill finalization

The finalization process also rechecks stock before deducting inventory.

---

# 🧠 Persistent Owner Preferences

The system supports persistent supermarket-owner preferences.

Preferences are stored independently of conversational memory.

Supported preferences include:

```text
default_payment
preferred_brand
shop_name
gstin
```

Example:

```text
Owner:
Always use UPI as my default payment method.

Agent:
Saved your default payment preference as UPI.
```

The preference remains available even after:

```text
/reset
```

and application restarts.

This demonstrates persistent business memory outside the active conversation context.

---

# 🔍 Product Search

The agent provides product search functionality for resolving product names and SKUs.

Example:

```text
Owner:
Find Aashirvaad Atta.

Agent:
Aashirvaad Atta
SKU: ...
Unit: packet
Selling Price: ₹...
MRP: ₹...
GST: ...%
Stock: ...
```

Product search helps the agent select the correct inventory item before performing billing operations.

---

# 📉 Low Stock Detection

The system identifies products whose inventory reaches or falls below their configured reorder level.

Example:

```text
Product              Stock    Reorder Level
------------------------------------------------
Tata Salt             4          10
Maggi                 6          15
```

The owner can ask:

```text
Which products are low in stock?
```

The agent retrieves the information using the inventory tools.

---

# 📦 Reorder Recommendations

The system can generate reorder recommendations based on inventory levels.

Example:

```text
Product       Current Stock      Reorder Level
------------------------------------------------
Maggi              6                  15
Tata Salt          4                  10
```

This helps the supermarket owner identify products that may require replenishment.

---

# 📊 Sales Analytics

The agent can provide sales information using database-backed analytics.

Supported analytics include:

* Daily sales
* Total sales
* Number of bills
* Average bill value
* GST collected
* Payment-mode breakdown
* Top-selling products
* Inventory health

Example:

```text
Owner:
How much did we sell today?

Agent:
Today's sales summary:
Total Sales: ₹...
Bills: ...
GST: ₹...
Average Bill: ₹...
```

---

# 📅 Daily Business Summary

The system provides a daily business summary containing information such as:

```text
Total Sales
Number of Bills
Subtotal
GST
Average Bill Value
Payment Mode Distribution
```

This allows the owner to quickly understand daily store performance.

---

# 🏪 Daily Close

The system provides a daily-close operation for summarizing business activity.

A daily close can be used to review:

```text
Daily Sales
Bills
GST
Payments
Credit Transactions
```

This provides a convenient end-of-day operational summary.

---

# 📄 PDF Invoice Generation

The system can generate PDF invoices for finalized bills.

Invoice generation includes:

* Store name
* GSTIN
* Invoice number
* Bill date/time
* Product details
* Quantity
* Unit price
* GST
* CGST
* SGST
* Grand total
* Payment mode
* Credit information where applicable

Generated invoices are stored in:

```text
generated/invoice_<bill_id>.pdf
```

Example:

```text
generated/
└── invoice_9.pdf
```

---

# 📊 PowerPoint Business Analysis

The system can generate a PowerPoint analysis deck containing business insights.

The generated deck can include:

* Sales summary
* Daily sales chart
* Payment-mode analysis
* Top products
* Inventory health
* Business insights

Generated reports are stored as:

```text
generated/analysis_deck_<timestamp>.pptx
```

The PowerPoint deck uses charts to provide a visual representation of supermarket performance.

---

# 🩺 System Health Monitoring

A system-health tool is available for operational diagnostics.

It checks information such as:

```text
Database connection
Product count
Customer count
Bill count
Bill item count
Owner preferences
Telegram sessions
Negative stock items
Draft bills
Finalized bills
```

Example:

```text
Owner:
Is everything working?

Agent:
System health check completed.
Database: Connected
Status: Healthy
```

The agent does not claim that the system is healthy without checking the health tool.

---

# 🧰 Agent Tools

The AI agent uses a tool registry to access supermarket business operations.

### Inventory Tools

```text
add_product
receive_stock
check_stock
low_stock
search_products
```

### Billing Tools

```text
create_bill
add_item_to_bill
update_bill_item
get_bill
finalize_bill
```

### Customer Credit Tools

```text
get_customer_credit
record_credit_payment
```

### Analytics Tools

```text
get_reorder_recommendations
get_sales_summary
get_daily_sales
get_daily_close
get_business_health
```

### Document Generation Tools

```text
generate_invoice
generate_analysis_deck
```

### Persistent Memory Tools

```text
set_preference
get_preference
get_preferences
clear_preference
```

### Diagnostics

```text
get_system_health
```

---

# 🏗️ Project Architecture

The project is organized into separate layers.

```text
Telegram Interface
        │
        ▼
Agent Layer
        │
        ▼
Tool Registry
        │
        ├── Inventory
        ├── Billing
        ├── Credit
        ├── Analytics
        ├── Preferences
        ├── Health
        └── Document Generation
        │
        ▼
Service Layer
        │
        ├── Invoice Service
        ├── Analysis Deck Service
        └── Validation
        │
        ▼
Database Layer
        │
        └── SQLite
```

This separation makes the project easier to maintain, test, and extend.

---

# 💻 Technology Stack

| Category              | Technologies                     |
| --------------------- | -------------------------------- |
| Programming Language  | Python                           |
| AI Agent              | OpenAI-compatible API            |
| Model Provider        | OpenRouter                       |
| Agent Framework       | Custom Tool-Calling Agent        |
| Telegram              | python-telegram-bot              |
| Backend               | Python                           |
| Database              | SQLite                           |
| ORM                   | SQLAlchemy                       |
| Data Validation       | Custom validation layer          |
| PDF Generation        | ReportLab                        |
| PowerPoint Generation | python-pptx                      |
| Configuration         | python-dotenv                    |
| Testing               | Python / pytest-compatible tests |
| Interface             | Telegram Bot                     |

---

# 📁 Project Structure

```text
supermarket-ops-agent/
│
├── README.md
├── .gitignore
├── .env
├── requirements.txt
├── main.py
│
├── app/
│   ├── __init__.py
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── tools.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── seed.py
│   │   └── seed_customers.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── invoice.py
│   │   ├── analysis_deck.py
│   │   ├── validation.py
│   │   └── memory.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── inventory.py
│   │   ├── billing.py
│   │   ├── preferences.py
│   │   └── health.py
│   │
│   └── telegram/
│       ├── __init__.py
│       └── bot.py
│
├── data/
│   └── supermarket.db
│
├── generated/
│   ├── invoice_*.pdf
│   └── analysis_deck_*.pptx
│
└── tests/
    └── test_step20_final.py
```

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/VARSHINI-S-30/supermarket-ops-agent.git
```

```bash
cd supermarket-ops-agent
```

---

## 2. Create a Python Virtual Environment

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=YOUR_OPENROUTER_API_KEY
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

The project uses OpenRouter through an OpenAI-compatible API.

---

## ⚠️ Security

Never commit the actual `.env` file to GitHub.

Do not expose:

```text
OpenRouter API keys
Telegram Bot tokens
Database credentials
Private credentials
Secrets
```

Use placeholders when sharing configuration examples.

Example:

```env
OPENAI_API_KEY=YOUR_OPENROUTER_API_KEY
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

The `.env` file should be included in `.gitignore`.

---

# 🗄️ Database Setup

The project uses SQLite as the local database.

Database URL:

```text
sqlite:///./data/supermarket.db
```

Create the database tables using:

```bash
python main.py
```

Expected output:

```text
Database tables created successfully!
```

---

# 🌱 Seed the Database

Run the product seed script:

```bash
python -m app.database.seed
```

If customer data is required:

```bash
python -m app.database.seed_customers
```

The seed scripts populate the database with sample supermarket products and customer records for testing.

---

# 🤖 Running the Telegram Bot

Start the Telegram bot using:

```bash
python -m app.telegram.bot
```

The bot uses Telegram polling to receive incoming messages.

Once the bot is running, open the configured Telegram bot and send:

```text
/start
```

---

# 💬 Telegram Commands

The bot supports:

```text
/start
/help
/reset
```

### `/start`

Starts the supermarket operations assistant.

### `/help`

Displays available capabilities.

### `/reset`

Resets the current conversational context.

Persistent owner preferences are stored separately and are not removed by conversation reset.

---

# 🧪 Example Conversations

## Check Stock

```text
Owner:
How much Maggi is in stock?
```

```text
Agent:
Maggi currently has 39 packets in stock.
```

---

## Low Stock

```text
Owner:
Which products are low in stock?
```

```text
Agent:
Here are the products that need attention...
```

---

## Create a Bill

```text
Owner:
Create a bill.
```

```text
Agent:
Bill created. What would you like to add?
```

---

## Add Items

```text
Owner:
Add 2 packets of Maggi.
```

```text
Owner:
Add 1 packet of Tata Salt.
```

---

## Edit Bill

```text
Owner:
Change Maggi quantity to 3.
```

The agent updates the existing bill item instead of creating a duplicate line.

---

## Show Bill

```text
Owner:
Show my bill.
```

The agent retrieves the current bill and displays the calculated totals.

---

## Finalize Bill

```text
Owner:
Finalize the bill using UPI.
```

The system validates the payment mode, rechecks stock, calculates the final amount, deducts inventory, and finalizes the bill.

---

# 🔁 Idempotency Demo

After successfully finalizing a bill:

```text
Owner:
Finalize the bill again.
```

The system recognizes that the bill has already been finalized.

Expected behavior:

```text
Bill already finalized.
No additional stock was deducted.
```

This demonstrates safe retry handling.

---

# 📦 Oversell Demo

Suppose:

```text
Available Stock = 6
```

Then ask:

```text
Create a bill for 10 units.
```

The inventory tool rejects the request.

Expected behavior:

```text
Insufficient stock.

Only 6 units are available.
```

No negative stock should be created.

---

# 🧠 Persistent Preference Demo

Save a default payment preference:

```text
Always use UPI as my default payment method.
```

Save a shop name:

```text
Set my shop name to Sri Lakshmi Supermarket.
```

Save GSTIN:

```text
Set my GSTIN to 33ABCDE1234F1Z5.
```

Then use:

```text
/reset
```

The conversational context is reset, but the saved preferences remain available.

---

# 📄 Invoice Demo

After finalizing a bill:

```text
Generate the invoice.
```

The system generates:

```text
generated/invoice_<bill_id>.pdf
```

The invoice contains the saved business information and finalized billing details.

---

# 📊 Business Analysis Demo

Ask:

```text
Generate the business analysis deck.
```

The system generates a PowerPoint presentation containing:

```text
Sales Summary
Daily Sales
Payment Analysis
Top Products
Inventory Health
Business Insights
```

Output:

```text
generated/analysis_deck_<timestamp>.pptx
```

---

# 📈 Sales Analytics Demo

Example:

```text
How much did we sell today?
```

The agent retrieves database-backed sales information.

Other supported requests include:

```text
Show today's sales.

What is the average bill value?

How much GST did we collect?

Show payment mode distribution.

Which products are selling the most?

What products should I reorder?
```

---

# 🩺 Health Check Demo

Ask:

```text
Is the system healthy?
```

The agent uses the system-health tool to inspect the database and operational state before responding.

---

# 🧪 Testing

The project includes validation and integration tests for the implemented functionality.

Run the final test suite using:

```bash
python tests/test_step20_final.py
```

The tests cover important functionality such as:

```text
Product management
Inventory operations
Billing
GST calculation
Payment handling
Persistent preferences
Invoice generation
Business analysis deck
```

---

# 🔒 Business Safety Rules

The system enforces important business rules at the tool layer.

### Inventory Safety

```text
Stock cannot become negative.
```

### Pricing Safety

```text
Selling Price >= Cost Price
Selling Price <= MRP
```

### GST Safety

```text
GST Rate must be between 0% and 100%.
```

### Quantity Safety

```text
Quantity must be greater than zero.
```

### Payment Safety

Allowed modes:

```text
cash
upi
card
credit
```

### Credit Safety

```text
Credit transactions require a known customer.
```

### Finalization Safety

```text
A finalized bill cannot be finalized again
as a new transaction.
```

---

# 🧩 Design Principles

The project follows several important engineering principles.

## Tool Grounding

Business-critical information such as:

```text
Price
Stock
GST
Customer Credit
Bill Status
```

is retrieved from tools and the database rather than being invented by the language model.

---

## Separation of Responsibilities

```text
AI Agent
   ↓
Reasoning & Tool Selection

Tools
   ↓
Business Rules

Database
   ↓
Persistent State

Services
   ↓
Document Generation & Validation
```

---

## Persistent State

Important supermarket data is stored in the database rather than only inside the conversation.

This includes:

```text
Products
Customers
Bills
Bill Items
Owner Preferences
Telegram Sessions
```

---

# 🌟 Key Features

```text
✓ Telegram-based supermarket assistant
✓ AI-powered natural-language interaction
✓ Agent-first tool orchestration
✓ Product management
✓ Inventory management
✓ Stock validation
✓ Product search
✓ Multi-turn billing
✓ Bill editing
✓ GST calculation
✓ Cash / UPI / Card / Credit payments
✓ Khata management
✓ Oversell protection
✓ Idempotent bill finalization
✓ Concurrent stock protection
✓ Low-stock detection
✓ Reorder recommendations
✓ Sales analytics
✓ Daily business summary
✓ Daily close
✓ Persistent owner preferences
✓ PDF invoice generation
✓ PowerPoint business analysis
✓ System health monitoring
✓ Database-backed business state
```

---

# 📌 Future Enhancements

* [ ] Branded invoice customization
* [ ] Scheduled business analysis reports
* [ ] Automated reorder suggestions
* [ ] FEFO inventory management
* [ ] Voice-note order processing
* [ ] Multi-language supermarket assistant
* [ ] Barcode scanning
* [ ] Product image recognition
* [ ] Automated khata reminders
* [ ] Advanced sales forecasting
* [ ] Demand prediction
* [ ] Supplier management
* [ ] Multi-store support
* [ ] Cloud database deployment
* [ ] Role-based access control
* [ ] Advanced business intelligence dashboards

---

# 📜 License

This project was developed as part of the **Nebula Supermarket Ops Agent hiring task**.

---

# 👩‍💻 Project Information

**Project:** Nebula Supermarket Ops Agent

**Domain:** Artificial Intelligence | Agentic AI | Retail Automation

**Interface:** Telegram

**Backend:** Python

**Database:** SQLite

**AI Model Provider:** OpenRouter

**Developed By:** Sri Varshini S

---

## ⭐ Project Highlights

This project demonstrates the integration of:

**Agentic AI + Tool Calling + Database Engineering + Business Rules + Inventory Management + Conversational Billing + Persistent Memory + Analytics + Document Generation**

to create an intelligent supermarket operations assistant that can perform real business operations safely through a conversational Telegram interface.

```
