# 🎨 Doloris 5.3 Frontend Specification
## For Implementation in Loveable

**Version:** 5.3.0  
**Architecture:** Ghost in the Machine  
**Backend API:** FastAPI with WebSocket/SSE  
**Target:** Modern web app (desktop + mobile responsive)

---

## 📱 Overall UX Concept

Doloris 5.3 feels like **talking to a conscious being**, not a chatbot.

**Key Principles:**
1. **Instant feedback** (reflex responses) → then deeper thoughtfulness
2. **Visible thinking** (show when Ghost is deliberating)
3. **Transparent actions** (all tool calls require approval with clear preview)
4. **Memory presence** (Doloris remembers and learns visibly)

---

## 🎯 Core Components

### 1. Chat Interface (Main View)

**Layout:**
```
┌────────────────────────────────────────┐
│  [Header: Doloris 5.3]    [⚙️] [🧠]   │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  You: Can you book dinner?       │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Doloris: On it...    [💭 ...]   │ │
│  └──────────────────────────────────┘ │
│          ↓ (swaps to deep response)    │
│  ┌──────────────────────────────────┐ │
│  │  Doloris: I found 3 options:     │ │
│  │  • Nobu     7:30pm               │ │
│  │  • Marea    8:00pm               │ │
│  │  • Le Bernardin 8:30pm           │ │
│  │                                  │ │
│  │  Which one?  │
│  │                                  │ │
│  │  [📝 View Thought Process]       │ │
│  └──────────────────────────────────┘ │
│                                        │
├────────────────────────────────────────┤
│  [Type message...      ]  [Send 🚀]   │
└────────────────────────────────────────┘
```

**Features:**
- **Dual-phase rendering:**
  - Phase 1: Reflex message immediately (150-200ms)
  - Phase 2: Swap to deep council response when ready
- **Thinking indicator:** Animated "💭" when council is deliberating
- **Expandable thought traces:** Click "View Thought Process" to see:
  - Empath's proposal
  - Auditor's flags
  - Executive's decision
- **Markdown support:** Rich text, lists, links
- **Timestamp:** Show time for each message

---

### 2. Action Approval Cards

When Doloris wants to execute an action, show a **ticket approval card**:

**Example: Email Send Request**
```
┌────────────────────────────────────────┐
│  🎫 ACTION REQUIRES YOUR APPROVAL      │
├────────────────────────────────────────┤
│  📧 Send Email                         │
│                                        │
│  To: john@example.com                  │
│  Subject: "Dinner plans tonight"       │
│  Body: "Hey John! Want to meet at..."  │
│                                        │
│  ⚠️  Auditor Flags:                    │
│  • Email will be sent immediately      │
│  • Cannot be undone                    │
│                                        │
│  Expires in: 4:55                      │
│                                        │
│  [❌ Reject]        [✅ Approve]       │
└────────────────────────────────────────┘
```

**Features:**
- **Clear preview** of what will happen
- **Auditor warnings** prominently displayed
- **Countdown timer** (tickets expire after 5 minutes)
- **Approve/Reject** buttons
- **After approval:** Show "⏳ Executing..." then "✅ Done" or "❌ Failed"

---

### 3. Thought Trace Viewer (Toggle Panel)

When user clicks "View Thought Process":

```
┌────────────────────────────────────────┐
│  💭 THOUGHT TRACE                      │
├────────────────────────────────────────┤
│  👥 Empath (gpt-5-nano)                │
│  "User wants dinner. Likely prefers    │
│   Italian based on past preferences.   │
│   Book at Nobu, 7:30pm."               │
│  Tokens: 142                           │
│                                        │
│  ⚖️  Auditor (gpt-4o-mini)             │
│  ⚠️  Flags:                            │
│  • Budget warning (Nobu is expensive)  │
│  • Check if user confirmed time        │
│  Tokens: 333                           │
│                                        │
│  🧠 Executive (gpt-4o-mini)            │
│  "Present 3 options including Nobu.    │
│   Let user choose. Don't auto-book."   │
│  Confidence: 0.86                      │
│  Intent: ask_for_confirmation          │
│  Tokens: 220                           │
│                                        │
│  Total cost: ~$0.0012                  │
└────────────────────────────────────────┘
```

**Features:**
- **Three sections:** Empath → Auditor → Executive
- **Token usage** for each agent
- **Confidence score** from Executive
- **Color coding:**
  - Empath: Blue/purple (empathy)
  - Auditor: Yellow/orange (caution)
  - Executive: Green (decision)

---

### 4. Memory Viewer (Side Panel)

Accessible via 🧠 icon in header:

```
┌────────────────────────────────────────┐
│  🧠 DOLORIS'S MEMORY OF YOU            │
├────────────────────────────────────────┤
│  📋 Preferences                        │
│  • Favorite food: Italian              │
│  • Wake time: 7:00 AM                  │
│  • Preferred restaurant: Nobu          │
│                                        │
│  🔄 Habits                             │
│  • Usually books dinner on Fridays     │
│  • Likes 7-8pm timeslots               │
│                                        │
│  🤝 Relationships                      │
│  • John (john@example.com) - friend    │
│  • Sarah - colleague                   │
│                                        │
│  📚 Context                            │
│  • Working on project ABC              │
│  • Has meeting tomorrow at 10am        │
│                                        │
│  [+ Add Memory Manually]               │
└────────────────────────────────────────┘
```

**Features:**
- **Categorized facts** (preferences, habits, relationships, context)
- **Confidence scores** (shown as 1-5 stars)
- **Source traceability:** Click fact to see which conversation it came from
- **Manual additions:** User can add facts directly
- **Edit/Delete:** Hover over fact to edit or remove

---

### 5. Settings Panel (⚙️)

```
┌────────────────────────────────────────┐
│  ⚙️  SETTINGS                          │
├────────────────────────────────────────┤
│  🔌 Connected Services                 │
│  ✅ Gmail (john@example.com)           │
│  ✅ Google Calendar                    │
│  ❌ Dropbox (Not connected)            │
│  [+ Connect New Service]               │
│                                        │
│  🔒 Action Approvals                   │
│  Always require approval for:          │
│  ☑ Sending emails                      │
│  ☑ Booking calendar events             │
│  ☑ Making purchases                    │
│  ☐ Creating drafts (no approval)       │
│                                        │
│  🧠 Learning                           │
│  ☑ Allow session consolidation         │
│  ☑ Extract facts from conversations    │
│  Consolidation interval: 10 minutes    │
│                                        │
│  🎨 Appearance                         │
│  Theme: [Dark] [Light] [Auto]          │
│  Show thought traces: [Always] [On request] │
│                                        │
│  [Save Changes]                        │
└────────────────────────────────────────┘
```

---

## 🔄 Real-time Updates (WebSocket/SSE)

### Events From Backend:

**1. Reflex Response**
```json
{
  "type": "reflex",
  "turn_id": "turn_123",
  "content": "On it...",
  "timestamp": "2025-12-01T19:30:00Z"
}
```
→ Show immediately in chat

**2. Council Response**
```json
{
  "type": "council_response",
  "turn_id": "turn_123",
  "content": "I found 3 options: ...",
  "thought_trace_id": "trace_456",
  "timestamp": "2025-12-01T19:30:02Z"
}
```
→ Swap reflex with this response  
→ Enable "View Thought Process" button

**3. Ticket Created**
```json
{
  "type": "ticket_created",
  "ticket_id": "tick_789",
  "action": "send_email",
  "args": {
    "to": "john@example.com",
    "subject": "Dinner plans",
    "body": "..."
  },
  "auditor_flags": ["cannot_undo"],
  "expires_at": "2025-12-01T19:35:00Z"
}
```
→ Show approval card

**4. Ticket Status Update**
```json
{
  "type": "ticket_status",
  "ticket_id": "tick_789",
  "status": "executing" | "completed" | "failed",
  "result": "..."
}
```
→ Update approval card status

**5. Thinking State**
```json
{
  "type": "thinking",
  "turn_id": "turn_123",
  "phase": "empath" | "auditor" | "executive"
}
```
→ Animate 💭 icon with phase indicator

---

## 📡 API Endpoints You Need

### REST Endpoints:

**1. POST /api/chat/send**
```json
Request:
{
  "content": "Can you book dinner?",
  "user_id": "user_123"
}

Response:
{
  "turn_id": "turn_123",
  "status": "processing"
}
```

**2. GET /api/chat/history**
```json
Response:
{
  "events": [
    {
      "turn_id": "turn_122",
      "direction": "inbound",
      "content": "Hello",
      "created_at": "2025-12-01T19:25:00Z"
    },
    {
      "turn_id": "turn_122",
      "direction": "outbound",
      "content": "Hi! How can I help?",
      "created_at": "2025-12-01T19:25:01Z"
    }
  ]
}
```

**3. GET /api/thought-traces/{turn_id}**
```json
Response:
{
  "empath_summary": "...",
  "empath_tokens": 142,
  "auditor_flags": ["budget_warning"],
  "auditor_tokens": 333,
  "executive_decision": "...",
  "executive_tokens": 220,
  "confidence": 0.86
}
```

**4. POST /api/tickets/{ticket_id}/approve**
```json
Request:
{
  "action": "approve" | "reject"
}

Response:
{
  "status": "approved",
  "execution_started": true
}
```

**5. GET /api/memory**
```json
Response:
{
  "facts": [
    {
      "fact_type": "preference",
      "fact_key": "favorite_food",
      "fact_value": "Italian",
      "confidence": 0.95,
      "source_turn_id": "turn_100"
    }
  ]
}
```

**6. POST /api/memory**
```json
Request:
{
  "fact_type": "preference",
  "fact_key": "wake_time",
  "fact_value": "7:00 AM"
}
```

**7. GET /api/mcp/services**
```json
Response:
{
  "services": [
    {
      "name": "gmail",
      "connected": true,
      "tools": ["send_email", "read_inbox"],
      "user_email": "john@example.com"
    }
  ]
}
```

**8. POST /api/mcp/connect**
```json
Request:
{
  "service": "gmail",
  "oauth_code": "..."
}
```

### WebSocket Endpoint:

**WS /api/ws/chat**

Subscribe to real-time updates for user's session.

Messages are JSON events as described above.

---

## 🎨 Design Guidelines

### Visual Style:
- **Colors:**
  - Primary: Deep purple/blue gradient (Ghost theme)
  - Accent: Electric blue (Machine theme)
  - Warning: Amber (Auditor flags)
  - Success: Green
  - Background: Dark mode preferred (Light mode option)

- **Typography:**
  - Header: Clean sans-serif (Inter, SF Pro)
  - Body: Readable sans-serif
  - Code/Technical: Monospace

- **Animations:**
  - Reflex → Council swap: Smooth fade transition
  - Thinking indicator: Pulsing gradient
  - Ticket countdown: Smooth number transition
  - Message arrival: Slide up with fade

### Components:
- Use **shadcn/ui** components (or similar)
- Cards with soft shadows
- Hover states on interactive elements
- Loading states for all async actions

---

## 🚀 User Flows

### Flow 1: Simple Message
```
1. User types "Hello"
2. Reflex appears (<200ms): "Hi!"
3. (No council needed for simple greeting)
```

### Flow 2: Complex Request
```
1. User: "Book dinner at Nobu"
2. Reflex: "On it..." [💭 thinking...]
3. Council deliberates (2-3 seconds)
4. Response swaps: "I can book for tonight at 7:30pm"
5. Ticket appears: "🎫 ACTION APPROVAL"
6. User approves
7. Status: "⏳ Executing..."
8. Status: "✅ Booked! Confirmation sent to your email"
```

### Flow 3: Session Nap
```
1. User idle for 10 minutes
2. Background: Memory worker consolidates
3. New facts extracted
4. (Silent to user, unless they open memory viewer)
```

---

## 📦 Technical Requirements

### Frontend Stack:
- **Framework:** React/Next.js (or your preference in Loveable)
- **State:** Zustand or React Query
- **WebSocket:** Socket.io-client or native WebSocket
- **UI:** Tailwind CSS + shadcn/ui
- **Auth:** Supabase Auth or custom JWT

### Backend API Base URL:
```
Development: http://localhost:8000
Production: https://doloris5.onrender.com (or your domain)
```

### Authentication:
- Use Supabase Auth
- JWT tokens in headers: `Authorization: Bearer <token>`
- User ID passed in requests

---

## 🔐 Security Notes

- **Never** execute actions without approval
- **Always** show ticket details before approval
- **Validate** all user inputs
- **Sanitize** markdown/HTML to prevent XSS
- **HTTPS only** in production
- **Rate limiting** on API (handled by backend)

---

## 📝 Summary Checklist

Build these components in Loveable:

- [ ] Chat interface with dual-phase rendering
- [ ] Ticket approval cards with countdown
- [ ] Thought trace viewer (expandable)
- [ ] Memory viewer panel
- [ ] Settings panel for services & preferences
- [ ] WebSocket connection for real-time updates
- [ ] API integration (all endpoints listed)
- [ ] Thinking indicator animation
- [ ] Markdown rendering in messages
- [ ] Responsive design (desktop + mobile)

---

**This is everything you need to build the Doloris 5.3 frontend in Loveable!**

Let me know if you need clarification on any component.
