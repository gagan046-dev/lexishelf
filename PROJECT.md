# LexiShelf — Project Reference

> AI-powered reading companion for understanding difficult English and automatically storing knowledge in Notion.

---

## About the Project

LexiShelf is a mobile-first application that helps users understand unfamiliar **words, phrases, idioms, and sentences** while reading books.

The intended experience is:

```text
Search
   ↓
Understand
   ↓
Ask AI / refine explanation
   ↓
Save
   ↓
Notion
```

Instead of searching Google, copying an explanation, opening Notion, finding the correct book page, and formatting the result manually, the user should be able to say:

```text
"Explain 'stolen into your room' and save it to my current book."
```

The AI agent understands the request, uses the appropriate tools, and performs the Notion operation.

### Product Definition

> **LexiShelf is an AI reading companion that turns difficult language encountered during reading into organized, reusable personal knowledge.**

---

# Project Goals

## Primary Goals

- Provide a beautiful mobile reading/vocabulary experience.
- Explain words and phrases using **simple English**.
- Understand phrases in **context**, not only dictionary definitions.
- Organize vocabulary by **book/collection**.
- Connect each collection to a Notion page.
- Allow an AI agent to **read from and write to Notion**.
- Allow the user to give natural-language Notion commands.
- Use **Groq** as the LLM provider.
- Use **CrewAI** for agentic orchestration.
- Keep deterministic operations outside the LLM whenever possible.

## Non-Goals for MVP

Do not initially build:

- A multi-agent architecture.
- A vector database without a demonstrated requirement.
- Complex event-driven microservices.
- Autonomous deletion of Notion content.
- A full replacement for Notion.
- A fully autonomous AI that can execute arbitrary code.

---

# Keys to Remember

These are the most important architectural rules for Codex.

## 1. AI for reasoning, APIs for execution

The LLM should decide **what needs to happen**.

Typed tools/services should decide **how it actually happens**.

```text
User
 ↓
Groq LLM
 ↓
CrewAI Agent
 ↓
Tool
 ↓
Service
 ↓
External API / Database
```

Do not allow the LLM to directly make arbitrary HTTP requests.

---

## 2. The Agent must be able to take action

The agent is not just a chatbot.

It must be able to perform actions such as:

```text
Explain vocabulary
Search collections
Find Notion pages
Create Notion pages
Append to Notion pages
Update Notion pages
Create collections
Save vocabulary
```

For example:

```text
User:
"Save this to my The Alchemist collection."

Agent:
1. Resolve collection.
2. Resolve Notion page.
3. Prepare vocabulary entry.
4. Call Notion append tool.
5. Verify success.
6. Tell the user what happened.
```

---

## 3. Never claim a successful action without tool confirmation

Bad:

```text
✓ Saved to Notion.
```

when the Notion request failed.

Correct:

```text
I couldn't save this to Notion because the Notion API
returned an authorization error.
```

The final response must be based on actual tool results.

---

## 4. User identity comes from the backend

Never allow the LLM to decide or provide the authenticated `user_id`.

Bad:

```json
{
  "user_id": "user-from-llm"
}
```

Correct:

```text
Authenticated request
        ↓
Backend identifies user
        ↓
Tool receives trusted user context
```

The backend is responsible for authorization.

---

## 5. Never expose secrets to the mobile app

These must remain server-side:

```text
GROQ_API_KEY
NOTION_CLIENT_SECRET
NOTION_ACCESS_TOKEN
DATABASE_CREDENTIALS
JWT_SIGNING_SECRET
```

---

# Methodology

The project follows a **hybrid agentic architecture**.

## Deterministic Layer

Use conventional APIs/services for operations where the required action is known.

Examples:

```text
Authentication
Database CRUD
Collection lookup
Notion API calls
Dictionary API calls
Permission checks
Validation
```

## Agentic Layer

Use CrewAI + Groq when the request requires interpretation, reasoning, context, or tool selection.

Examples:

```text
"Explain this phrase."

"Explain this in simple English."

"Explain this and save it."

"Find my Alchemist notes and add this."

"Create a page for my reading notes."

"Add this to whatever book I'm currently reading."
```

---

# Proposed Solution

## High-Level Architecture

```text
                         MOBILE APP
                             │
                             ▼
                       REST API / HTTPS
                             │
                             ▼
                         FastAPI
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
       Application Services            Agent Layer
              │                             │
              │                       CrewAI Agent
              │                             │
              │                          Groq LLM
              │                             │
              │                    ┌────────┼────────┐
              │                    │        │        │
              │                    ▼        ▼        ▼
              │               Vocabulary Notion Collection
              │                  Tool      Tools     Tools
              │                    │        │        │
              └────────────┬───────┴────────┴────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
          PostgreSQL     Notion       Dictionary
                         API            API
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Mobile | React Native + Expo |
| Backend | Python + FastAPI |
| Agent Framework | CrewAI |
| LLM | Groq |
| Database | PostgreSQL |
| ORM | SQLAlchemy / SQLModel |
| Knowledge Integration | Notion API |
| Vocabulary | Dictionary API + Groq |
| Authentication | JWT/session-based authentication |
| Testing | Pytest |
| Deployment | Docker |
| Cloud-ready | AWS |

The exact libraries may be changed if a better maintained equivalent is required, but the architectural boundaries should remain.

---

# Groq Integration

## Purpose

Groq is the LLM provider.

The model must be configurable.

Environment:

```env
GROQ_API_KEY=
GROQ_MODEL=
GROQ_TEMPERATURE=
```

Never hard-code the API key or model throughout the codebase.

## Recommended flow

```text
Application
    ↓
CrewAI
    ↓
Groq
    ↓
Tool call
    ↓
Backend executes tool
    ↓
Tool result
    ↓
Groq
    ↓
Final response
```

## Important

Groq should be treated as the **reasoning engine**, not the system of record.

The database and Notion remain authoritative for their respective data.

---

# CrewAI Agent

## Primary Agent

### Vocabulary & Knowledge Agent

**Role:**

> Personal AI reading assistant responsible for understanding the user's language-learning and knowledge-management requests and using available tools to complete them.

### Responsibilities

```text
Understand user intent
Understand vocabulary
Understand context
Select tools
Perform Notion actions
Use collection context
Return concise results
```

---

# CrewAI Tool Architecture

Tools should have one clear responsibility.

```text
tools/
├── vocabulary/
│   ├── lookup_word
│   └── explain_term
│
├── notion/
│   ├── search_pages
│   ├── get_page
│   ├── create_page
│   ├── append_content
│   └── update_page
│
└── collections/
    ├── list_collections
    ├── get_collection
    └── create_collection
```

The agent receives these tools explicitly.

The tools perform validation and API calls.

---

# Vocabulary Tools

## `lookup_word`

### Purpose

Retrieve deterministic dictionary information.

### Input

```json
{
  "term": "serendipity"
}
```

### Output

```json
{
  "term": "serendipity",
  "definition": "...",
  "part_of_speech": "noun",
  "pronunciation": "...",
  "synonyms": ["...", "..."]
}
```

---

## `explain_term`

### Purpose

Explain a word or phrase using Groq, especially when contextual understanding is required.

### Input

```json
{
  "term": "stolen into",
  "sentence_context": "He had stolen into the room.",
  "difficulty_level": "simple"
}
```

### Output

```json
{
  "term": "stolen into",
  "meaning": "Entered quietly or secretly.",
  "simple_meaning": "Went into a place quietly without being noticed.",
  "contextual_meaning": "Here, 'stolen' does not mean taking something.",
  "example": "He stole into the room without making a sound.",
  "synonyms": [
    "slipped into",
    "sneaked into"
  ],
  "usage_note": "This is an older/literary use of 'steal'."
}
```

---

# Notion Tools

The agent must be capable of writing to Notion.

## `notion_search_pages`

### Purpose

Find authorized Notion pages.

### Input

```json
{
  "query": "The Alchemist"
}
```

### Output

```json
{
  "pages": [
    {
      "id": "...",
      "title": "The Alchemist",
      "url": "..."
    }
  ]
}
```

---

## `notion_get_page`

### Purpose

Retrieve page metadata/content before an operation when required.

### Input

```json
{
  "page_id": "..."
}
```

---

## `notion_create_page`

### Purpose

Create a new Notion page when the user requests it.

### Input

```json
{
  "parent_page_id": "...",
  "title": "Interesting Words",
  "content": "..."
}
```

### Example User Request

```text
"Create a Notion page called Books I Want To Read."
```

Expected:

```text
Agent
 ↓
notion_create_page
 ↓
Notion
 ↓
Created page
 ↓
Agent confirms result
```

---

## `notion_append_content`

### Purpose

Append content to an existing Notion page.

### Input

```json
{
  "page_id": "...",
  "content": "## Serendipity\n\nA fortunate discovery..."
}
```

This should be the **preferred write operation** for vocabulary collections.

---

## `notion_update_page`

### Purpose

Update page properties or content when explicitly requested.

This operation must be conservative.

Do not replace an entire page unless the user clearly asks for replacement.

---

# Natural Language Agent Commands

The agent should understand commands such as:

```text
"Explain serendipity."

"Explain this phrase in simple English."

"Save this to The Alchemist."

"Explain this and save it."

"Add this to my current book."

"Create a Notion page called Reading Notes."

"Create a collection for Mythos."

"Find my Psychology of Money notes."

"Add another example to the serendipity entry."

"Put this explanation in my reading notes."
```

---

# Collection System

Collections are the application's book-centric organization layer.

Example:

```text
Collections

📖 The Alchemist
   24 words

📖 Mythos
   31 words

📖 The Psychology of Money
   18 words
```

Each collection stores a Notion page reference.

```text
Collection
├── id
├── user_id
├── name
├── notion_page_id
├── notion_page_url
└── theme_id
```

---

# Creating a Collection

Example UI:

```text
Create Collection

Book Name
[ The Alchemist ]

Notion Page
[ Select Notion Page ]

Theme
[ Golden Hour ]

[ Create Collection ]
```

After creation:

```text
The Alchemist
      │
      ▼
Notion Page ID
      │
      ▼
All vocabulary saves go here
```

---

# Deleting a Collection

Deleting a collection is a **destructive operation** and must require explicit user confirmation before execution.

```text
Delete Collection

⚠ This will permanently remove "The Alchemist"
  and all 24 saved words from LexiShelf.

  This does NOT delete anything from Notion.

[ Cancel ]        [ Delete Collection ]
```

Rules:

```text
The backend must never delete a collection without an explicit confirmation flag.
Deleting a collection only removes the app's local record (collection + its vocabulary entries).
The linked Notion page/content is never deleted automatically.
The agent must never trigger this action autonomously without the user directly confirming.
```

### Endpoint contract

```json
{
  "confirm": true
}
```

If `confirm` is not `true`, the backend returns an error instead of deleting.

---

# Deleting a Vocabulary Entry

Each saved word/phrase must have a **delete button** in the collection detail view.

```text
Serendipity                     🗑
"A fortunate discovery..."
```

Tapping delete asks for a lightweight confirmation (inline or modal) before removal:

```text
Delete "Serendipity" from this collection?

[ Cancel ]        [ Delete ]
```

This operation removes the entry from the app's database only; it does not modify Notion content that was already appended.

---

# Notion Storage Strategy

## MVP: Append Mode

The simplest storage model is:

```text
The Alchemist
│
├── Serendipity
├── Omens
├── Stolen into
└── ...
```

The app appends structured content to the linked page.

Example:

```markdown
## Serendipity

**Meaning:** A fortunate discovery made unexpectedly.

**Simple meaning:** Finding something good without looking for it.

**Context:** Used when something valuable is discovered accidentally.

**Example:** Meeting her was pure serendipity.

**Synonyms:** Chance, fortune, luck

---
```

## Future: Child Page Mode

Later, support:

```text
The Alchemist
│
├── Serendipity
├── Omens
└── Stolen into
```

where each item is a separate Notion child page.

---

# AI Explanation Schema

Internal AI responses should be structured.

```json
{
  "term": "serendipity",
  "normalized_term": "serendipity",
  "part_of_speech": "noun",
  "meaning": "...",
  "simple_meaning": "...",
  "contextual_meaning": "...",
  "example": "...",
  "synonyms": [],
  "usage_note": "...",
  "confidence": 0.94
}
```

The frontend should render this structure rather than parsing arbitrary prose.

---

# Context-Aware Understanding

This is one of the core differentiators.

The app should accept:

```text
Word
Phrase
Full sentence
Paragraph
```

Example:

```text
User:
"marching ahead of us"
```

The system should explain the phrase rather than treating every word independently.

Possible response structure:

```text
Easy meaning

Moving forward before us.

Context

The phrase suggests that someone is progressing
or moving ahead before the speaker/group.

Similar expressions

• moving ahead of us
• going before us
• leading the way
```

The AI should distinguish:

```text
Literal meaning
vs.
Contextual meaning
vs.
Idiomatic/literary meaning
```

---

# Mobile Application

The mobile app should feel like a **premium reading companion**, not an enterprise dashboard.

## Home

```text
Good evening 🌙

What are you reading?

┌─────────────────────────────┐
│ 🔍 Search a word or phrase  │
└─────────────────────────────┘

Current Collection

┌─────────────────────────────┐
│ 📖 The Alchemist            │
│ 24 words                    │
└─────────────────────────────┘

Collections
...
```

---

# Search Result

Example:

```text
stolen into

Easy meaning

Entered quietly or secretly.

Context

Here, "stole" does not mean taking something.

Example

He stole into the room without making a sound.

Synonyms

slipped into · sneaked into

[ + Save ]

[ Ask AI ]
```

---

# Agent Chat

The user can interact naturally.

```text
You:
Explain "omen" and save it to my current collection.

Agent:
An omen is a sign that something may happen
in the future.

In the context of the book, it can refer to a
sign that appears to guide or warn someone.

✓ Saved to The Alchemist.
```

---

# Themes

Themes should be data-driven.

Initial themes:

```text
🌙 Midnight
🌅 Golden Hour
🌲 Forest
🌊 Ocean
📜 Vintage
🌸 Dreamy
📚 Library
◻️ Minimal
```

Theme configuration should be separated from business logic.

Example:

```json
{
  "id": "midnight",
  "name": "Midnight",
  "colors": {
    "background": "#0B0F1A",
    "surface": "#151B2B",
    "primary": "#7C9CFF",
    "text": "#F4F6FB",
    "muted": "#8892B0"
  },
  "animation": "stars"
}
```

Animations should be subtle and optional.

## Theme Switching

The user must be able to change the active color theme at any time from a **Theme Selector** screen/sheet.

```text
Choose a Theme

( ● ) 🌙 Midnight
( ) 🌅 Golden Hour
( ) 🌲 Forest
( ) 🌊 Ocean
( ) 📜 Vintage
( ) 🌸 Dreamy
( ) 📚 Library
( ) ◻️ Minimal
```

Rules:

```text
The selected theme is persisted per-user (local storage, synced to backend if authenticated).
Switching themes must animate (crossfade) rather than hard-cut.
All screens re-render using the active theme's color tokens — no hard-coded colors in components.
A collection may optionally override the global theme with its own theme_id.
```

## Animated UI

LexiShelf should feel alive, not static. Motion should be used purposefully:

```text
Screen transitions        → shared-element / fade-slide
Collection cards          → staggered fade-in on list mount
Search result reveal      → fade + slight upward slide
Save confirmation         → checkmark micro-animation
Delete (word/collection)  → shrink-and-fade-out before removal from list
Theme switch              → animated crossfade of background/surface colors
Agent "thinking" state    → subtle pulsing/typing indicator
```

Guidelines:

```text
Animations must be interruptible and never block user input.
Respect the OS "reduce motion" accessibility setting.
Use a single animation library consistently (e.g. react-native-reanimated) rather than mixing approaches.
```

---

# Database Model

## User

```text
id
email
created_at
```

## NotionConnection

```text
id
user_id
access_token_encrypted
workspace_id
workspace_name
created_at
updated_at
```

## Collection

```text
id
user_id
name
description
notion_page_id
notion_page_url
theme_id
created_at
updated_at
```

## VocabularyEntry

```text
id
user_id
collection_id
term
phrase
sentence_context
meaning
simple_explanation
contextual_explanation
example
synonyms
part_of_speech
pronunciation
created_at
updated_at
```

## SearchHistory

```text
id
user_id
query
collection_id
response_summary
created_at
```

---

# Backend API

## `POST /api/v1/chat`

### Request

```json
{
  "message": "Explain 'stolen into your room' and save it to my current collection.",
  "collection_id": "collection-id",
  "conversation_id": "conversation-id"
}
```

### Response

```json
{
  "message": "Here is the explanation...",
  "actions": [
    {
      "type": "notion_append",
      "status": "success"
    }
  ]
}
```

---

## `GET /api/v1/collections`

Returns the authenticated user's collections.

---

## `POST /api/v1/collections`

Creates a collection.

---

## `GET /api/v1/collections/{id}`

Returns a collection.

---

## `DELETE /api/v1/collections/{id}`

Deletes a collection and its vocabulary entries. Requires explicit confirmation.

### Request

```json
{
  "confirm": true
}
```

### Response

```json
{
  "success": true,
  "data": { "deleted_collection_id": "collection-id" }
}
```

If `confirm` is missing or `false`, respond with `400` and `error_code: "CONFIRMATION_REQUIRED"`.

---

## `DELETE /api/v1/vocabulary/{id}`

Deletes a single vocabulary entry (the delete button in collection detail).

### Response

```json
{
  "success": true,
  "data": { "deleted_entry_id": "entry-id" }
}
```

---

## `GET /api/v1/notion/pages/search`

Searches authorized Notion pages.

---

## `POST /api/v1/collections/{id}/sync`

Optional explicit synchronization endpoint.

---

# Suggested Backend Structure

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── collections.py
│   │       └── notion.py
│   │
│   ├── agents/
│   │   ├── vocabulary_agent.py
│   │   └── crew.py
│   │
│   ├── tools/
│   │   ├── vocabulary.py
│   │   ├── notion.py
│   │   └── collections.py
│   │
│   ├── services/
│   │   ├── groq_service.py
│   │   ├── notion_service.py
│   │   └── vocabulary_service.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── db/
│   ├── config/
│   └── security/
│
├── tests/
├── requirements.txt
└── .env.example
```

---

# Agent Execution Flow

## Example

User:

```text
Explain "stolen into your room" and save it to The Alchemist.
```

### Step 1 — Intent

CrewAI/Groq identifies:

```text
Vocabulary explanation
+
Notion save
+
Target collection = The Alchemist
```

### Step 2 — Resolve Collection

```text
get_collection("The Alchemist")
```

### Step 3 — Explain

```text
explain_term(...)
```

### Step 4 — Prepare Content

```text
Structured vocabulary record
```

### Step 5 — Write

```text
notion_append_content(...)
```

### Step 6 — Verify

```text
Notion → success
```

### Step 7 — Response

```text
Explanation...

✓ Saved to The Alchemist.
```

---

# Security

## Required

### Secrets

All secrets remain server-side.

### Notion Tokens

Encrypt stored tokens at rest.

### User Isolation

Every database query must be scoped to the authenticated user.

A user must never access another user's:

```text
Collections
Vocabulary
Notion tokens
Notion page IDs
Conversations
```

### Tool Authorization

The backend supplies trusted user context to tools.

The LLM cannot override authorization.

---

# Agent Safety

The agent must not have unrestricted capabilities.

## Required controls

```text
Maximum agent iterations
Tool timeouts
API retries
Input validation
Output validation
Authorization checks
Structured errors
Request IDs
```

## Destructive Operations

For operations such as:

```text
Delete page
Delete large amount of content
Replace page content
```

the agent should ask for confirmation before executing.

Prefer:

```text
append
create
```

over destructive operations.

---

# Error Handling

Every tool should return structured results.

Success:

```json
{
  "success": true,
  "data": {}
}
```

Failure:

```json
{
  "success": false,
  "error_code": "NOTION_UNAUTHORIZED",
  "message": "Notion authorization has expired."
}
```

The agent must receive the actual tool result.

---

# Observability

Log:

```text
request_id
user_id
agent_id
tool_name
tool_arguments_sanitized
tool_result_status
latency
error_code
```

Never log:

```text
API keys
OAuth tokens
Passwords
Secrets
```

---

# Testing Strategy

## Unit Tests

Each tool must be independently testable.

```text
test_lookup_word()
test_explain_phrase()
test_create_collection()
test_notion_search()
test_notion_create_page()
test_notion_append()
test_user_cannot_access_other_collection()
```

## Agent Tests

Natural-language tests:

```text
"Explain serendipity."

"Save serendipity to The Alchemist."

"Create a collection for Mythos."

"Add this to my current book."

"Create a Notion page called Reading Notes."

"Explain this phrase and save it."
```

## Integration Tests

Use:

```text
Mock Notion API
OR
Dedicated Notion test workspace
```

Do not run destructive integration tests against a user's personal production pages.

---

# MVP

## Mobile

```text
✓ Home
✓ Search
✓ Search result
✓ Collections
✓ Collection detail
✓ Agent chat
✓ Theme selector
```

## Backend

```text
✓ Authentication
✓ Collection CRUD
✓ Vocabulary CRUD
✓ Groq integration
✓ CrewAI agent
✓ Notion integration
✓ Notion search
✓ Notion append
✓ Notion page creation
```

## AI

```text
✓ Word explanation
✓ Phrase explanation
✓ Context explanation
✓ Natural-language Notion actions
```

---

# Future Features

## Phase 2

```text
OCR from book photos
Screenshot → vocabulary extraction
Text-to-speech
Pronunciation
Translation
Daily revision
Spaced repetition
Quizzes
```

## Phase 3

```text
AI reading companion
Paragraph explanations
Chapter summaries
Vocabulary analytics
Personalized difficulty
Cross-book vocabulary search
Personalized English learning plan
```

---

# Future Multi-Agent Architecture

Do not implement this in the MVP.

If the application grows:

```text
                    User
                      │
                      ▼
              Supervisor Agent
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
     Vocabulary    Reading     Knowledge
       Agent        Agent        Agent
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                  Tool Layer
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Notion      Database    External APIs
```

Only introduce additional agents when there is a real separation of responsibilities.

---

# Agent vs Manual API Decision

| Requirement | Implementation |
|---|---|
| Search dictionary | API |
| Retrieve collection | Backend/API |
| Save exact known entry | Backend/API |
| Notion append | Tool/API |
| Notion page creation | Tool/API |
| Explain a word | Groq |
| Explain a phrase | Groq |
| Understand context | Groq |
| Interpret natural language | Groq |
| Decide which tools are required | CrewAI + Groq |
| Multi-step request | CrewAI + tools |

## Principle

> **APIs for certainty. AI for understanding. Agents for orchestration.**

---

# Implementation Order

Codex should implement in this order.

## Step 1 — Repository Foundation

```text
Project structure
Python environment
Dependency management
Configuration
.env.example
Logging
```

## Step 2 — Database

```text
Models
Migrations
Repositories
User isolation
```

## Step 3 — Notion Service

```text
Authentication/connection abstraction
Search
Get page
Create page
Append content
Update page
```

## Step 4 — Vocabulary Service

```text
Dictionary provider abstraction
Groq service
Structured AI response
Validation
```

## Step 5 — CrewAI

```text
Agent
Tools
Tasks
Crew
Agent execution
```

## Step 6 — Backend API

```text
Chat
Collections
Notion
Authentication
```

## Step 7 — Mobile

```text
Navigation
Home
Search
Collections
Agent chat
Themes
Result rendering
```

## Step 8 — Testing

```text
Unit tests
Agent tests
Integration tests
Security tests
```

## Step 9 — Documentation

```text
README
Local setup
Environment variables
Architecture
API documentation
```

---

# Definition of Done

The MVP is complete when:

```text
[ ] User can authenticate.
[ ] User can connect Notion.
[ ] User can create a collection.
[ ] User can link a collection to a Notion page.
[ ] User can search a word.
[ ] User can search a phrase.
[ ] Groq generates a structured explanation.
[ ] CrewAI agent can use tools.
[ ] Agent can save vocabulary to Notion.
[ ] Agent can create a Notion page.
[ ] Agent can append content to Notion.
[ ] Agent can understand natural-language Notion commands.
[ ] Agent never falsely claims a successful write.
[ ] User data is isolated.
[ ] Secrets remain server-side.
[ ] Basic tests pass.
[ ] .env.example exists.
[ ] README contains setup instructions.
```

---

# References

Use the latest official documentation before implementing provider-specific functionality.

## Groq

- Chat/API reference:
  `https://console.groq.com/docs/api-reference`
- Tool use:
  `https://console.groq.com/docs/tool-use/overview`

## CrewAI

- Documentation:
  `https://docs.crewai.com/`

## Notion

- API introduction:
  `https://developers.notion.com/reference/intro`
- Page content:
  `https://developers.notion.com/guides/data-apis/working-with-page-content`
- Page API:
  `https://developers.notion.com/reference/page`

---

# Final Architecture Principle

LexiShelf should not be built as:

```text
Mobile
  ↓
LLM
  ↓
"Hope it works"
```

It should be:

```text
                    USER
                      │
                      ▼
                   MOBILE
                      │
                      ▼
                   FASTAPI
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
   Normal Services          CREWAI AGENT
          │                       │
          │                     GROQ
          │                       │
          │              ┌────────┼────────┐
          │              ▼        ▼        ▼
          │         Vocabulary  Notion  Collection
          │            Tool      Tools     Tools
          │              │        │        │
          └──────────────┴────────┴────────┘
                         │
                 ┌───────┴───────┐
                 ▼               ▼
             DATABASE          NOTION
```

The agent should be **capable of thinking and acting**, but the system must remain deterministic, secure, testable, and observable.

> **The agent decides what to do. Tools do the work. Backend enforces the rules. Notion stores the user's knowledge.**
