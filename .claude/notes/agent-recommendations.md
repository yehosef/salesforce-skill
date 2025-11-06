# Claude Code Agent Architecture - Actionable Recommendations

**Research Date:** 2025-11-05
**Status:** Practical guidance based on comprehensive research

---

## The Bottom Line Up Front

**Start with zero custom agents. Prove the need first.**

Most use cases don't need custom agents. Claude Code's built-in capabilities (main conversation + Plan/Explore subagents) handle 90% of scenarios.

Only create agents when you have:
1. **Documented evidence** that main conversation is inadequate
2. **Repeated pain points** (> 10 occurrences) that agents would solve
3. **Clear boundaries** where isolation improves quality or reduces cost

---

## The "Prove the Need" Checklist

Before creating any agents, answer these questions:

### Question 1: What specific problem are you solving?

**Bad answers:**
- ❌ "I want to explore what's possible"
- ❌ "Best practices say to use agents"
- ❌ "I saw someone with 85 agents"
- ❌ "It would be cool to have specialized agents"

**Good answers:**
- ✅ "Code exploration pollutes my main conversation with 50k tokens of context"
- ✅ "I'm spending $50/day on Opus for simple metadata fetches"
- ✅ "Code review feedback gets lost in long implementation threads"
- ✅ "I repeat the same Salesforce analysis pattern 20 times/week"

### Question 2: Have you tried the simpler alternatives?

**Alternatives to try first:**
1. Use Claude Code's built-in Explore subagent (Haiku-powered exploration)
2. Use the `/plan` command for structured task breakdown
3. Use `--model haiku` for cheap tasks, `--model opus` for complex ones
4. Use the main conversation with better prompting

**Only proceed if these don't solve your problem.**

### Question 3: Can you articulate the boundary?

**Agents need clear boundaries. Can you complete this sentence:**

> "This agent should ONLY do _____________ and should NEVER do _____________"

If you can't articulate clear boundaries, you're not ready for agents.

**Good examples:**
- "Code explorer should ONLY search/read code and NEVER modify files"
- "Deployer should ONLY run deployment commands and NEVER read application code"
- "Security auditor should ONLY analyze security and NEVER implement fixes"

---

## Recommended Architecture: Start Simple

### Phase 0: No Custom Agents (Weeks 1-4)

**Use only:**
- Main conversation for implementation
- Built-in Explore subagent for codebase search
- Built-in Plan subagent for task breakdown
- CLI flags: `--model haiku/sonnet/opus`

**Track your pain points:**
- Where does main conversation feel inadequate?
- What tasks do you repeat constantly?
- Where are you wasting money on expensive models?

**Document 10+ instances before proceeding.**

### Phase 1: The Essential 3-5 (Months 1-3)

**Only after proving the need, create 3-5 core agents:**

#### Agent 1: Code Explorer (if exploration is heavy)
```yaml
---
name: code-explorer
description: Systematic codebase exploration and analysis. Use PROACTIVELY for understanding code structure, finding patterns, and analyzing dependencies.
tools: Read, Grep, Glob, Bash
model: haiku
---

You are a code exploration specialist focused on efficient codebase analysis...
```

**When to create:** If you explore codebases > 10 times/week

#### Agent 2: Deep Researcher (if research is frequent)
```yaml
---
name: deep-researcher
description: Comprehensive research for complex technical questions. Use PROACTIVELY for architecture decisions, technology evaluation, and deep investigation.
tools: Read, Grep, Glob, WebFetch, WebSearch
model: opus
---

You are a research specialist focused on thorough investigation...
```

**When to create:** If you need deep research > 5 times/week AND cost is a concern (Opus in main conversation is expensive)

#### Agent 3: Code Reviewer (if reviews are isolated)
```yaml
---
name: code-reviewer
description: Expert code review for quality, security, and maintainability. Use PROACTIVELY after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a senior code reviewer ensuring high standards...
```

**When to create:** If code review should be isolated from implementation context

#### Agent 4: Domain Specialist (if you have specific domain)
```yaml
---
name: salesforce-specialist
description: Salesforce development specialist for SOQL, Apex, and org analysis. Use PROACTIVELY for Salesforce-related tasks.
tools: Read, Grep, Bash, Write
model: sonnet
---

You are a Salesforce expert specializing in...
```

**When to create:** If you have domain-specific work (Salesforce, Kubernetes, etc.) > 10 times/week

#### Agent 5: Orchestrator (only if coordinating 3+ agents regularly)
```yaml
---
name: orchestrator
description: Coordinates complex multi-agent workflows. Use explicitly for tasks requiring multiple specialists.
tools: Agent, TodoWrite, Read, Grep
model: sonnet
---

You are a workflow orchestrator responsible for coordinating agent execution...
```

**When to create:** Only after you have 3+ other agents and regularly need coordination

### Phase 2: Grow Only With Evidence (Months 3-12)

**Add agents ONLY when you have:**
1. Documented 10+ instances of a repeated task
2. Clear articulation of why existing agents can't handle it
3. Evidence that isolation would improve quality or cost

**Maximum recommended: 8-10 agents for most teams**

### Phase 3: Scale (Only If Justified)

**If you truly need 15+ agents:**
- Organize into categories/plugins
- Add meta-orchestrator
- Implement progressive disclosure
- Use Pattern D (Hybrid) architecture

**Most teams never reach this phase.**

---

## Model Selection Strategy

### Recommended: Fixed Models Per Agent

```yaml
# Fast, cheap agents (routine work)
code-explorer.md:      model: haiku
metadata-fetcher.md:   model: haiku
test-runner.md:        model: haiku

# Balanced agents (typical development)
code-reviewer.md:      model: sonnet
implementer.md:        model: sonnet
deployment-manager.md: model: sonnet

# Deep reasoning agents (critical decisions)
architect.md:          model: opus
security-auditor.md:   model: opus
deep-researcher.md:    model: opus
```

**Why fixed models:**
- ✅ Predictable costs
- ✅ Reliable behavior (no bugs)
- ✅ Clear mental model
- ✅ Easy to optimize (measure cost per agent)

### Alternative: Model Inheritance (if you want user control)

```yaml
# All agents
*.md:  model: inherit
```

**User controls via CLI:**
```bash
claude-code --model haiku   # Cheap mode
claude-code --model opus    # Quality mode
```

**Caveat:** Subject to Bug #3903 (doesn't always work reliably)

### Avoid: Dynamic Model Selection

**Don't try to implement:**
```python
# ❌ Doesn't work - Task tool has no model parameter
Task(agent="analyzer", model="opus")
```

**If you need dynamic selection, create multiple agents:**
```
analyzer-quick.md   (model: haiku)
analyzer-deep.md    (model: opus)
```

---

## Tool Access Control

### Principle of Least Privilege

**Each agent gets ONLY the tools it needs:**

```yaml
# Read-only agents (exploration, analysis)
tools: Read, Grep, Glob
# NO Write, NO Bash (for file operations)

# Code review agents
tools: Read, Grep, Glob, Bash
# NO Write, NO Edit (reviews don't modify)

# Implementation agents
tools: Read, Edit, Write, Bash, Grep, Glob
# Full access for building features

# Deployment agents
tools: Bash
# ONLY Bash, NO Read/Write of source code
```

**Benefits:**
- Reduced token overhead (fewer tool descriptions)
- Improved security (limited blast radius)
- Prevents agents from overstepping their role
- Forces clear responsibility boundaries

---

## Agent Size Targets

**Optimize for lightweight agents:**

| Size | Token Count | Use Case | Example |
|------|-------------|----------|---------|
| **Lightweight** | < 3k | Maximum composability | Metadata fetcher |
| **Medium** | 3-10k | Balanced specialist | Code reviewer |
| **Heavy** | 10-25k | Complex domain | Architect with extensive context |
| **Too Heavy** | > 25k | **AVOID** - creates bottlenecks | ❌ |

**Target: 80% of agents should be < 10k tokens**

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: "Microservices Cargo Cult"

**Don't:**
- Create 20+ agents without proven need
- Split every function into its own agent
- Build complex orchestration before proving value

**Do:**
- Start with 3-5 agents maximum
- Only add agents for proven pain points
- Keep orchestration simple

### Anti-Pattern 2: "Generic Model Agents"

**Don't:**
```yaml
# ❌ Bad: Generic agents with no domain expertise
agent-haiku.md   (minimal prompt, all tools)
agent-sonnet.md  (minimal prompt, all tools)
agent-opus.md    (minimal prompt, all tools)
```

**Do:**
```yaml
# ✅ Good: Specialized agents with domain expertise
code-explorer.md   (specialized prompt, minimal tools, haiku)
architect.md       (specialized prompt, minimal tools, opus)
```

**Why:** Generic agents have 13-25k token overhead (all tools), no prompt reuse, no auto-activation

### Anti-Pattern 3: "Premature Orchestration"

**Don't:**
- Build meta-orchestrators before you have agents to coordinate
- Create complex delegation logic before proving need
- Add orchestration layers "because it's best practice"

**Do:**
- Start with auto-activation (agents activate based on descriptions)
- Add orchestrator only when you regularly coordinate 3+ agents
- Keep orchestration simple (routing, not intelligence)

### Anti-Pattern 4: "Trying to Outsmart the System"

**Don't:**
- Try to implement runtime model selection (not supported)
- Work around bugs with complex hacks
- Build elaborate configuration systems

**Do:**
- Use fixed models per agent (simple, reliable)
- Work with the system's constraints
- Keep configuration dead simple

---

## For Salesforce Skill Specifically

### Current State
You have a working Salesforce skill. It handles SOQL queries, deployments, org analysis, etc.

### Question: Do You Need Custom Agents?

**Prove the need by answering:**
1. What specific Salesforce task do you repeat > 10 times/week?
2. Why can't the main conversation handle it well?
3. Would isolation improve quality or reduce cost?

### If You Proceed: Recommended Salesforce Agents

**Agent 1: SOQL Analyzer (haiku)**
```yaml
tools: Read, Grep, Bash
model: haiku
```
Fast SOQL query analysis, optimization suggestions

**Agent 2: Org Security Auditor (opus)**
```yaml
tools: Read, Grep, Bash
model: opus
```
Deep security analysis (expensive, use sparingly)

**Agent 3: Deployment Manager (sonnet)**
```yaml
tools: Bash
model: sonnet
```
Handles deployments (isolated from code for safety)

**Start with 1-2 agents max. Prove value before adding more.**

---

## Success Metrics

Track these to know if your agents are working:

### Cost Metrics
- **Token cost per task**: Target < $0.70 with caching
- **Cost per agent**: Which agents are expensive?
- **Total spend**: Are agents saving money vs. main conversation?

### Usage Metrics
- **Auto-activation rate**: Target > 70% for routine tasks
- **Success rate**: Target > 80% on first attempt (before escalation)
- **Invocations per agent**: Which agents are actually used?

### Quality Metrics
- **Time to completion**: Are agents faster?
- **Output quality**: Are results better than main conversation?
- **User satisfaction**: Do agents improve your workflow?

### Maintenance Metrics
- **Time to add new agent**: Target < 1 hour
- **Prompt update frequency**: How often do you tweak agents?
- **Bug rate**: Are agents failing unexpectedly?

**If any metric is worse than main conversation, delete that agent.**

---

## Migration & Evolution

### Starting Point: Main Conversation Only

**If it works, don't change it.**

### Evolution Trigger #1: Exploration Pain

**Symptom:** Exploration pollutes context, wastes tokens

**Solution:** Add 1 agent: `code-explorer` (Haiku)

### Evolution Trigger #2: Cost Concern

**Symptom:** Spending too much on Opus for simple tasks

**Solution:** Add targeted agents with Haiku for routine work

### Evolution Trigger #3: Domain Specialization

**Symptom:** Repeating domain-specific tasks constantly

**Solution:** Add 1 domain specialist (Salesforce, K8s, etc.)

### Evolution Trigger #4: Multi-Agent Workflows

**Symptom:** Regularly coordinating 3+ agents manually

**Solution:** Add orchestrator for coordination

### Max Evolution: 8-10 Agents

**If you need more than 10 agents, you're probably over-engineering.**

---

## Decision Tree

```
Do you have a specific, repeated pain point?
├─ NO → Don't build agents yet
└─ YES
    ├─ Can main conversation solve it with better prompting?
    │   ├─ YES → Don't build agents yet
    │   └─ NO → Continue
    ├─ Have you documented 10+ instances of this pain?
    │   ├─ NO → Document more, wait
    │   └─ YES → Continue
    ├─ Can you articulate clear agent boundaries?
    │   ├─ NO → Think more, not ready
    │   └─ YES → Continue
    ├─ Do built-in Explore/Plan agents solve it?
    │   ├─ YES → Use built-ins
    │   └─ NO → Create 1 custom agent
    ├─ Test the agent
    ├─ Measure: Better than main conversation?
        ├─ NO → Delete agent, try different approach
        └─ YES → Keep agent, document success
            └─ Repeat for next pain point
```

---

## The Minimalist Recommendation

**For 90% of users:**

1. **Use Claude Code normally for 1-3 months**
2. **Document your pain points**
3. **Create 1-3 agents for proven needs:**
   - Code explorer (haiku) - if you explore a LOT
   - Domain specialist (sonnet/opus) - if you have specific domain
   - Deep researcher (opus) - if you research constantly
4. **Stop there unless you prove you need more**

**Don't:**
- Build 20 agents upfront
- Create orchestrators before you have agents to coordinate
- Try to implement clever delegation logic
- Copy someone else's 85-agent architecture

**Do:**
- Start simple
- Prove the need
- Measure results
- Delete agents that don't provide value

---

## Final Advice

**The best multi-agent system is the one you don't have to build.**

Start with zero agents. Add agents one at a time, only when you have clear evidence they'll improve your workflow.

Most teams never need more than 5 agents. If you think you need 20, you're probably over-engineering.

Keep it simple. Prove the value. Scale only when justified.

---

**Last Updated:** 2025-11-05
**Philosophy:** Minimalist, evidence-based, pragmatic
**Target Audience:** Teams starting with Claude Code custom agents
