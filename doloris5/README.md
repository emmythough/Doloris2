# 🌌 Doloris 5.3 - Ghost in the Machine

A consciousness engine with secure, separated cognitive and execution layers.

## Architecture

- **Ghost (Cognitive Layer)**: Tri-Cameral Council (Empath → Auditor → Executive)
- **Machine (Technical Layer)**: Redis Streams + Workers
- **Hands (Execution Layer)**: Signed Tickets + MCP Integration

## Quick Start

### 1. Install Dependencies

```bash
cd doloris5
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Set Up Database

Run the schema in Supabase:
```bash
# In Supabase dashboard SQL editor, run:
doloris5/schema.sql
```

### 4. Start Redis

```bash
docker run -p 6379:6379 redis:latest
```

### 5. Start Workers

```bash
# Terminal 1: Reflex Worker
python -m app.workers.reflex_worker

# Terminal 2: Council Worker
python -m app.workers.council_worker

# Terminal 3: MCP Broker
python -m app.execution.mcp_broker

# Terminal 4: Memory Worker
python -m app.workers.memory_worker
```

### 6. Start API Gateway

```bash
uvicorn app.main:app --reload
```

API will be available at http://localhost:8000

## Frontend

See `FRONTEND_SPEC.md` for complete frontend implementation guide.

### API Endpoints

- `POST /api/chat/send` - Send message
- `GET /api/chat/history` - Get conversation history
- `GET /api/thought-traces/{turn_id}` - Get thought trace
- `POST /api/tickets/{ticket_id}/approve` - Approve/reject ticket
- `GET /api/memory` - Get user memory
- `WS /api/ws/chat` - WebSocket for real-time updates

## Project Structure

```
doloris5/
├── app/
│   ├── cognitive/       # Tri-Cameral Council
│   ├── workers/         # Background workers
│   ├── execution/       # Tickets + MCP
│   ├── streams/         # Redis producers
│   ├── api/             # HTTP + WebSocket
│   └── models/          # Pydantic schemas
├── schema.sql           # Database schema
├── requirements.txt     # Python dependencies
└── FRONTEND_SPEC.md     # Frontend guide
```

## How It Works

1. **User sends message** → FastAPI gateway
2. **Reflex worker** → Instant response (<200ms)
3. **Council worker** → Deep thinking (Empath → Auditor → Executive)
4. **Executive decides** → Text response or action ticket
5. **User approves ticket** → MCP broker executes
6. **Memory worker** → Extracts facts during idle time

## Development

```bash
# Run tests
pytest

# Format code
black app/

# Type check
mypy app/
```

## Documentation

- `STRUCTURE.md` - Project structure
- `FRONTEND_SPEC.md` - Frontend specification
- `schema.sql` - Database schema

## License

MIT
