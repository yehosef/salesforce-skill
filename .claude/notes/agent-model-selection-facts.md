# Claude Code Agent Model Selection - Technical Facts

**Research Date:** 2025-11-05
**Status:** Verified technical documentation on how model selection works

---

## Critical Finding: Model Selection is Configuration-Based, NOT Invocation-Based

### What DOESN'T Work (Common Misconception)

```python
# ❌ INCORRECT - This parameter does NOT exist
Task(
    description="Analyze SOQL patterns",
    prompt="Analyze these Salesforce queries...",
    model="opus"  # ← NO SUCH PARAMETER
)

# ❌ INCORRECT - No runtime model selection
agent.run(model="sonnet")  # Not possible

# ❌ INCORRECT - Can't dynamically choose model per invocation
orchestrator chooses "use opus this time" → NOT SUPPORTED
```

### What DOES Work

```yaml
# ✅ CORRECT - Model specified in agent configuration file
---
name: salesforce-analyzer
description: Analyzes Salesforce org structure
tools: Read, Grep, Bash
model: opus  # ← Fixed in configuration
---

Your specialized agent prompt here...
```

**Key fact:** The model is determined by the agent's configuration file, NOT by the caller.

---

## Task/Agent Tool Schema

### Actual Tool Definition

```typescript
interface TaskTool {
  description: string;  // 3-5 word task description
  prompt: string;       // Detailed autonomous task
  subagent_type: string; // Agent type/name
  model?: string;       // ← DOES NOT EXIST
  resume?: string;      // Optional resume ID
}
```

**Confirmed:** The Task/Agent tool has **NO `model` parameter**.

**Source:** System prompt tool definitions, verified against official documentation

---

## Valid Model Field Values

### In Agent Configuration Frontmatter

```yaml
---
name: agent-name
model: sonnet    # Use Claude Sonnet 4.5
---

---
name: agent-name
model: opus      # Use Claude Opus 4
---

---
name: agent-name
model: haiku     # Use Claude Haiku 4.5
---

---
name: agent-name
model: inherit   # Use same model as main conversation
---

---
name: agent-name
# [model omitted]  # Defaults to sonnet
---
```

### What Each Value Does

**`model: sonnet`**
- Agent ALWAYS uses Claude Sonnet 4.5
- Fixed, cannot be overridden at invocation time
- Default if model field is omitted

**`model: opus`**
- Agent ALWAYS uses Claude Opus 4
- Fixed, cannot be overridden at invocation time
- Use for critical/complex reasoning

**`model: haiku`**
- Agent ALWAYS uses Claude Haiku 4.5
- Fixed, cannot be overridden at invocation time
- 3x cheaper, 2x faster, 90% of Sonnet quality

**`model: inherit`**
- Agent uses whatever model the main conversation is using
- If user runs `--model opus`, agent uses Opus
- If user runs `--model haiku`, agent uses Haiku
- Useful for consistency across workflows

**`[model omitted]`**
- Defaults to Sonnet 4.5
- Equivalent to `model: sonnet`

---

## Model Selection Precedence

### Configuration File Precedence

1. **Project-level agents** (`.claude/agents/`) - highest priority
2. **User-level agents** (`~/.claude/agents/`) - lower priority
3. **Plugin-provided agents** - lowest priority

If the same agent name exists in multiple locations, project-level takes precedence.

### Model Selection Hierarchy

1. **Agent's explicit `model:` field** - highest priority
2. **If `model: inherit`** - uses parent conversation's model
3. **If `model:` omitted** - defaults to Sonnet
4. **CLI `--model` flag** - only affects main conversation, NOT sub-agents (see bugs)

---

## Known Bugs & Limitations

### Bug #3903 / #5456: Sub-agents Ignore CLI `--model` Parameter

**Problem:**
```bash
claude-code --model opus "analyze this codebase"
```
- Main task uses Opus
- Sub-agents revert to their config default (usually Sonnet)
- CLI flag doesn't propagate to sub-agents

**Status:** Marked as duplicate, remains unresolved

**Workaround:** Set model in `~/.claude/settings.json` instead of using CLI flag

### Bug #5206: `/agents` Command Shows Wrong Model

**Problem:** Display bug showing incorrect model in agent list

**Status:** UI issue, doesn't affect actual agent behavior

---

## Dynamic Model Selection: What's Actually Possible

### Approach 1: Multiple Agent Files (Most Common)

```
agents/
  soql-analyzer-deep.md      (model: opus)
  soql-analyzer-standard.md  (model: sonnet)
  soql-analyzer-quick.md     (model: haiku)
```

**Orchestrator logic:**
```
if task_complexity == "high":
    invoke("soql-analyzer-deep")      # Uses Opus
elif task_complexity == "medium":
    invoke("soql-analyzer-standard")  # Uses Sonnet
else:
    invoke("soql-analyzer-quick")     # Uses Haiku
```

**Pros:**
- Explicit model per complexity level
- Clear naming convention
- Independent prompts (can optimize per model)

**Cons:**
- More files to maintain
- Potential prompt duplication
- More agents in the namespace

### Approach 2: Model Inheritance

```yaml
---
name: salesforce-analyzer
model: inherit  # Uses parent's model
tools: Read, Grep, Bash
---

Analyzes Salesforce orgs...
```

**User controls:**
```bash
# For simple tasks
claude-code --model haiku "analyze metadata"

# For complex tasks
claude-code --model opus "analyze security model"
```

**Pros:**
- Single agent file
- User controls cost/quality tradeoff
- Simple maintenance

**Cons:**
- All agents in workflow use same model
- Can't mix models (e.g., Haiku explorer + Opus architect)
- Requires user to understand model tradeoffs
- Doesn't work reliably (see Bug #3903)

### Approach 3: Fixed Assignments by Purpose

```yaml
# deployment-manager.md
model: opus    # Critical, high-stakes

# soql-analyzer.md
model: sonnet  # Balanced

# metadata-fetcher.md
model: haiku   # Simple, fast
```

**Pros:**
- Model matches agent complexity
- Set-and-forget configuration
- Predictable costs

**Cons:**
- Can't adjust per invocation
- May over-provision (using Opus when Sonnet would suffice)
- Fixed tradeoff

---

## Real-World Production Examples

### wshobson/agents Distribution

**77 agents with fixed model assignments:**
- **11 Haiku agents**: context-manager, reference-builder, sales-automator
- **45 Sonnet agents**: Most development agents
- **21 Opus agents**: architect-reviewer, security-auditor, ml-engineer

**Pattern:** Fixed models based on agent complexity

### lst97/claude-code-sub-agents

```yaml
---
name: agent-organizer
description: "Master orchestrator for complex, multi-agent tasks"
tools: [Read, Write, Edit, Grep, Glob, Bash, TodoWrite]
model: haiku  # ← Even orchestrator uses Haiku
---
```

**Pattern:** Haiku-first, even for coordination

### jbeck018/agents-opencode

**Strategic model distribution:**
- Frontend agents: Sonnet
- Backend agents: Sonnet
- Infrastructure: Opus
- Testing: Haiku
- Security: Opus

**Pattern:** Domain-specific model selection

---

## The "Orchestrator Specifies Model" Pattern - Why It Doesn't Work

### What Was Assumed

```python
# Hypothetical (doesn't exist):
def orchestrator():
    if is_complex(task):
        Task(agent="analyzer", model="opus")  # ❌ Not possible
    else:
        Task(agent="analyzer", model="haiku")  # ❌ Not possible
```

### Why It Fails

1. **No `model` parameter** in Task/Agent tool
2. **Agent model is fixed** in configuration file
3. **No runtime override mechanism** exists

### What You Must Do Instead

```python
# What actually works:
def orchestrator():
    if is_complex(task):
        Task(subagent_type="analyzer-deep")   # Uses opus (in its config)
    else:
        Task(subagent_type="analyzer-quick")  # Uses haiku (in its config)
```

**You route to DIFFERENT AGENTS, not different models of the same agent.**

---

## Best Practices

### For Most Use Cases

**Use fixed models per agent:**
```yaml
# Fast, cheap agents
code-explorer.md:     model: haiku
test-runner.md:       model: haiku

# Balanced agents
code-reviewer.md:     model: sonnet
implementer.md:       model: sonnet

# Deep reasoning agents
architect.md:         model: opus
security-auditor.md:  model: opus
```

**Benefits:**
- Clear cost model
- Predictable behavior
- No configuration surprises
- Works reliably (no bugs)

### For User-Controlled Workflows

**Use model inheritance:**
```yaml
# All workflow agents
analyzer.md:    model: inherit
reviewer.md:    model: inherit
builder.md:     model: inherit
```

**User controls via session:**
```bash
# Cheap exploration
claude-code --model haiku

# Critical review
claude-code --model opus
```

**Caveat:** Subject to Bug #3903 (CLI flag doesn't always propagate)

### For Escalation Patterns

**Create tiered agents:**
```
analyzer-L1.md  (model: haiku)   → First pass
analyzer-L2.md  (model: sonnet)  → If validation fails
analyzer-L3.md  (model: opus)    → If still unclear
```

**Orchestrator implements retry logic with escalation.**

---

## Summary Table

| Feature | Supported? | How It Works |
|---------|-----------|--------------|
| Specify model in agent config | ✅ Yes | `model: opus` in frontmatter |
| Specify model in Task tool | ❌ No | No such parameter exists |
| Dynamic per-invocation model | ❌ No | Must use multiple agent files |
| Model inheritance | ✅ Yes | `model: inherit` in config |
| CLI `--model` propagation | ⚠️ Buggy | Known issue #3903 |
| Different models per agent | ✅ Yes | Each agent has own config |
| Runtime model override | ❌ No | Configuration-based only |

---

## Migration Guide

### If You Assumed Dynamic Model Selection

**Before (incorrect assumption):**
```python
Task(agent="analyzer", model="opus")  # Doesn't work
```

**After (correct approach):**

**Option 1: Multiple agents**
```python
if complex:
    Task(subagent_type="analyzer-deep")  # analyzer-deep.md has model: opus
else:
    Task(subagent_type="analyzer-quick") # analyzer-quick.md has model: haiku
```

**Option 2: Inheritance**
```python
# analyzer.md has model: inherit
# Set main conversation model before invoking
set_model("opus")
Task(subagent_type="analyzer")
```

---

## Documentation References

**Official Sources:**
- Claude Code Subagents: https://docs.claude.com/en/docs/claude-code/sub-agents
- Model selection docs: "The model field accepts model aliases (sonnet, opus, haiku) or 'inherit'"

**Bug Reports:**
- Issue #3903: Subagents ignore CLI `--model` parameter
- Issue #5456: Duplicate of #3903
- Issue #5206: `/agents` command shows wrong model

**Real-World Examples:**
- wshobson/agents: github.com/wshobson/agents
- lst97: github.com/lst97/claude-code-sub-agents
- jbeck018: github.com/jbeck018/agents-opencode

---

## Key Takeaways

1. **Model selection is configuration-based** - set in agent's frontmatter, not at invocation
2. **Task/Agent tool has NO model parameter** - confirmed via system prompt and docs
3. **For dynamic selection, create multiple agents** - route to different agents per complexity
4. **`model: inherit` exists but is buggy** - CLI propagation doesn't work reliably (Bug #3903)
5. **Production systems use fixed models** - wshobson (77 agents), lst97 (30+ agents)
6. **The "orchestrator specifies model" pattern doesn't work** - fundamental limitation

**Bottom line:** If you need dynamic model selection, create multiple agent files and route intelligently. There is no runtime model override mechanism.

---

**Last Updated:** 2025-11-05
**Verification Status:** Cross-referenced against system prompt, official docs, and bug reports
**Confidence Level:** Very High (confirmed via multiple sources)
