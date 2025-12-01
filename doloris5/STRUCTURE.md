# Doloris 5.3 Project Structure

doloris5/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI gateway
│   ├── config.py                  # Environment config
│   │
│   ├── cognitive/                 # THE GHOST
│   │   ├── __init__.py
│   │   ├── empath.py             # Empath agent
│   │   ├── auditor.py            # Auditor agent
│   │   ├── executive.py          # Executive agent
│   │   ├── council.py            # Tri-Cameral orchestrator
│   │   └── prompts.py            # Agent prompts
│   │
│   ├── workers/                   # THE MACHINE
│   │   ├── __init__.py
│   │   ├── reflex_worker.py      # Instant responses
│   │   ├── council_worker.py     # Deep thinking
│   │   ├── tool_worker.py        # MCP execution
│   │   ├── memory_worker.py      # Session naps
│   │   └── ticket_worker.py      # Action execution
│   │
│   ├── execution/                 # THE HANDS
│   │   ├── __init__.py
│   │   ├── tickets.py            # Signed ticket system
│   │   ├── mcp_broker.py         # MCP integration
│   │   └── connectors/
│   │       ├── gmail.py
│   │       ├── calendar.py
│   │       └── github.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── semantic.py           # Semantic memory
│   │   ├── episodic.py           # Conversation history
│   │   └── consolidation.py      # Session naps
│   │
│   ├── streams/                   # Redis Streams
│   │   ├── __init__.py
│   │   ├── producer.py           # Publish to streams
│   │   ├── consumer.py          # Consume from streams
│   │   └── schemas.py            # Stream message schemas
│   │
│   ├── api/                       # HTTP endpoints
│   │   ├── __init__.py
│   │   ├── chat.py               # Chat endpoints
│   │   ├── tickets.py            # Ticket approval endpoints
│   │   ├── memory.py             # Memory viewer
│   │   └── websocket.py          # WebSocket/SSE
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py           # Supabase models
│   │   └── schemas.py            # Pydantic schemas
│   │
│   └── utils/
│       ├── __init__.py
│       ├── openai_client.py
│       ├── redis_client.py
│       └── supabase_client.py
│
├── tests/
├── migrations/
├── requirements.txt
├── .env.example
└── README.md
