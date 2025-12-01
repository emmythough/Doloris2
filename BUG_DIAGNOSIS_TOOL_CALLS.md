# Production Error Diagnosis: OpenAI Tool Calls Format

**Date:** November 28, 2025  
**Environment:** Render/Production  
**Severity:** HIGH - Breaks all tool-using conversations

---

## Error Details

```
ERROR: OpenAI API Error: Error code: 400
Invalid value: 'tool_call'. Supported values are: 'function', 'allowed_tools', and 'custom'.
Param: messages[9].tool_calls[0].type
```

**Translation:** When conversation history includes tool calls, OpenAI rejects the format.

---

## Root Cause

**File:** `app/openai_client.py`  
**Line:** 54  
**Bug:**
```python
tool_calls.append({
    "id": tc.id,
    "name": tc.function.name,
    "arguments": tc.function.arguments,
    "type": "tool_call"  # ❌ WRONG!
})
```

**Should be:**
```python
"type": "function"  # ✅ CORRECT
```

---

## Why This Happens

1. User sends message requiring tools
2. Agent calls tool (e.g., `add_task`)
3. openai_client stores tool call in conversation history
4. Next message includes previous tool call in context
5. OpenAI API rejects format: `type: 'tool_call'` is invalid
6. **Entire conversation breaks**

---

## Impact

**Affected:**
- Any conversation using tools (tasks, notes, traces, etc.)
- Multi-turn conversations where tools were called previously
- **ALL agents** (ChatAgent, TasksAgent, SystemAgent, etc.)

**Not Affected:**
- First tool call in a conversation (no history yet)
- Conversations without tools

---

## The Fix

### Change in `app/openai_client.py` (Line 54):

```diff
if message.tool_calls:
    for tc in message.tool_calls:
        tool_calls.append({
            "id": tc.id,
            "name": tc.function.name,
            "arguments": tc.function.arguments,
-           "type": "tool_call"
+           "type": "function"
        })
```

That's it! One word change.

---

## Why This Bug Exists

**OpenAI API Changed:**
- Old format: `type: "tool_call"` (deprecated)
- New format: `type: "function"` (required)

**Our code used old format**, which worked for initial calls but broke when history was replayed.

---

## Test Case

**Before Fix (BROKEN):**
```
User: "Add task: Buy milk"
Bot: ✅ Task added
[tool_call stored with type="tool_call"]

User: "Add task: Buy bread"
[history includes previous tool_call]
❌ 400 Error: Invalid value 'tool_call'
```

**After Fix (WORKING):**
```
User: "Add task: Buy milk"
Bot: ✅ Task added
[tool_call stored with type="function"]

User: "Add task: Buy bread"
[history includes previous tool_call]  
✅ Task added successfully
```

---

## Verification Steps

1. Deploy fix to Render
2. Test multi-turn tool conversation:
   - Add a task
   - Add another task (should not crash)
3. Check logs - no more 400 errors

---

## How R.D Would Handle This

**R.D's Workflow:**
1. **Diagnose:** Read error from Supabase logs
2. **Reproduce:** Write test that sends tool_call with wrong type
3. **Patch:** Change `"tool_call"` to `"function"`
4. **Validate:** Run test - should pass
5. **PR:** Create PR with fix

**This is a perfect R.D use case!**

---

## Priority

**CRITICAL** - Deploy immediately

This breaks all multi-turn conversations using tools, which is **most conversations**.

---

**Fix:** 1 line change  
**Time to deploy:** 2 minutes  
**Impact:** Fixes all tool-using conversations
