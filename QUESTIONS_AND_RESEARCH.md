# ArmadaBench - Questions & Research Items

This document tracks open questions, research needs, and decisions that need to be made before or during implementation.

---

## Critical Questions for User

### Star Forge API

1. **API Access**
   - What is the base URL for the Star Forge API?
   - Does it require authentication? If so, what method (API key, OAuth, etc.)?
   - Is there API documentation or an OpenAPI/Swagger spec available?
   - What are the rate limits (if any)?

2. **API Capabilities**
   - Can we get JSON responses for all card types (ships, squadrons, upgrades, objectives)?
   - Is there a search/filter endpoint, or do we need to fetch all cards and filter locally?
   - Does the API include card legality info (banned, restricted, errata)?
   - Can the API validate complete fleet compositions?

3. **Data Format**
   - Can you provide example JSON responses for:
     - A ship card (e.g., Imperial Star Destroyer II)
     - A squadron card (e.g., TIE Fighter)
     - An upgrade card (e.g., Darth Vader commander)
     - An objective card
   - What field names are used for:
     - Point costs
     - Faction
     - Hull/Shield values
     - Upgrade slots
     - Card abilities/text

4. **Fleet Building Logic**
   - Does Star Forge already have validation logic we can reuse?
   - How does it handle unique cards (only one per fleet)?
   - How does it validate upgrade slot compatibility?
   - Does it enforce timing of building (commander first, etc.)?

### Vassal Module Details

5. **Module Access**
   - Which version of the Star Wars Armada Vassal module should we target?
   - Do you have a specific .vmod file, or should we use the latest public version?
   - Are there any custom modifications to the module we should know about?

6. **Shrimpbot Integration**
   - You mentioned Shrimpbot can import fleets - is this something we should integrate with?
   - Does Shrimpbot have an API or is it Discord-based?
   - Can we use Shrimpbot's fleet export format?

### Benchmarking Goals

7. **Target Models**
   - Which LLMs do you want to benchmark? (e.g., Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro)
   - Do you have API access to these models?
   - Any specific model versions or checkpoints?

8. **Success Metrics**
   - What level of performance would be "good" for an LLM?
   - Are you more interested in:
     - Rules knowledge accuracy?
     - Strategic play quality?
     - List building creativity?
     - All equally?

9. **Dataset Creation**
   - Do you have existing games or scenarios you want to use for testing?
   - Should we create synthetic scenarios or use real games?
   - Do you have expert players who could validate test scenarios?

### Deployment

10. **Environment**
    - Where will this run? (local machines, cloud servers, containers)
    - Do we need headless Vassal support, or can we run with GUI?
    - Any performance requirements (e.g., must run tests in < 1 hour)?

---

## Research Items - Vassal Engine

### Critical Research (Must Answer Before Phase 1)

1. **Programmatic Module Loading**
   - ✓ Confirmed: Vassal has a `GameModule` class
   - ❓ How exactly do we instantiate a GameModule from a .vmod file path?
   - ❓ Can we run Vassal headless, or does it require X11/display?
   - ❓ What's the initialization sequence?

2. **Game State Access**
   - ✓ Confirmed: Use `Map.getPieces()` to get all pieces
   - ❓ How do we identify piece types in Armada module specifically?
   - ❓ Are ships/squadrons different GamePiece types or differentiated by properties?
   - ❓ What properties are exposed on Armada pieces?

3. **Action Execution**
   - ✓ Confirmed: Commands are used for actions
   - ❓ Can we create Commands programmatically, or must we simulate UI?
   - ❓ Is there a Command for moving a piece to specific coordinates?
   - ❓ How do maneuver tools work internally?

### Important Research (Phase 2-3)

4. **Armada Module Structure**
   - ❓ How are ship stats stored? (as piece properties, separate data files?)
   - ❓ How are damage cards tracked?
   - ❓ How are defense tokens represented?
   - ❓ How are upgrade cards attached to ships?
   - ❓ How does the module track shield dials?

5. **Movement Mechanics**
   - ❓ Are maneuver templates GamePieces themselves?
   - ❓ Can we get maneuver template geometry data?
   - ❓ How does the module handle collisions?
   - ❓ Can we validate moves before executing?

6. **Attack Mechanics**
   - ❓ How are attacks executed in the module?
   - ❓ Is there a dice roller we can hook into?
   - ❓ Can we make attacks deterministic for testing?
   - ❓ How are damage and defense tokens handled?

### Useful Research (Phase 4+)

7. **Fleet Loading**
   - ❓ What format does the module use for saved fleets?
   - ❓ Can we programmatically spawn ships with upgrades?
   - ❓ How does Shrimpbot integration work?

8. **Visual Capture**
   - ❓ Can we get the Map component bounds reliably?
   - ❓ Does Vassal support offscreen rendering?
   - ❓ Can we zoom/pan the map programmatically?

9. **Extensions & Customization**
   - ❓ Can we add custom Vassal module components?
   - ❓ Could we add properties to pieces for easier state tracking?
   - ❓ Can we modify the module to expose more data?

### Research Methodology

**Approach 1: Documentation Dive**
- Study Vassal JavaDoc thoroughly
- Read Vassal source code on GitHub
- Search Vassal forums for similar use cases

**Approach 2: Experimentation**
- Create minimal Java test programs
- Load module and explore GameModule API
- Try creating Commands manually
- Log all available piece properties

**Approach 3: Community**
- Post on Vassal forums
- Ask in Armada community Discord
- Contact Armada module maintainers
- Check if anyone has done similar automation

---

## Technical Decisions

### 1. Communication Protocol: Java ↔ Python

**Options:**
- **REST API** (via Javalin, Spring Boot)
  - ✅ Simple, language-agnostic, good debugging tools
  - ❌ HTTP overhead, JSON serialization cost
  - **Recommendation**: Start with this, optimize later if needed

- **gRPC**
  - ✅ Faster, efficient binary protocol, strong typing
  - ❌ More complex setup, code generation required
  - **Recommendation**: Consider for v2.0 if performance issues

- **ZeroMQ**
  - ✅ Very fast, flexible messaging patterns
  - ❌ No built-in service discovery, more low-level
  - **Recommendation**: Overkill for this use case

- **IPC (Named Pipes, Unix Sockets)**
  - ✅ Lowest latency
  - ❌ Platform-specific, complex error handling
  - **Recommendation**: Only if running on same machine

**Decision**: Start with **REST API (Javalin)** for simplicity, profile later

---

### 2. Java Web Framework

**Options:**
- **Javalin**
  - ✅ Lightweight (single JAR), simple API, good docs
  - ✅ Minimal boilerplate
  - ❌ Less "enterprise" features
  - **Recommendation**: Best for our use case

- **Spring Boot**
  - ✅ Comprehensive ecosystem, auto-configuration
  - ❌ Heavy, slower startup, more complexity
  - **Recommendation**: Overkill

- **Vert.x**
  - ✅ Reactive, high performance
  - ❌ Different programming model, steeper learning curve
  - **Recommendation**: Unnecessary complexity

**Decision**: **Javalin** - simple, fast, sufficient

---

### 3. State Management

**How do we track game state between calls?**

**Options:**
- **Stateless** - Query Vassal fresh each time
  - ✅ No sync issues, simple
  - ❌ Slower, can't track history

- **Cached State** - Python maintains state cache
  - ✅ Faster queries
  - ❌ Can get out of sync with Vassal

- **Event-Driven** - Vassal pushes state changes
  - ✅ Always in sync, efficient
  - ❌ More complex, requires WebSocket or polling

**Decision**: **Hybrid approach**
- Start with stateless queries for correctness
- Add caching for frequently accessed data
- Invalidate cache on any mutation
- Consider event-driven for v2.0

---

### 4. Screenshot Format

**What format should screenshots be in?**

**Options:**
- **PNG**
  - ✅ Lossless, good for text/UI
  - ❌ Larger files
  - **Recommendation**: Best for quality

- **JPEG**
  - ✅ Smaller files
  - ❌ Lossy, artifacts on sharp edges
  - **Recommendation**: Not ideal for game boards

- **WebP**
  - ✅ Good compression, good quality
  - ❌ Less universal support
  - **Recommendation**: Consider as option

**Decision**: **PNG** as default, allow format parameter

**Resolution:**
- Full resolution? Or downscale for LLM efficiency?
- Test Claude's vision with different resolutions
- May want both: full for archival, scaled for LLM

---

### 5. Test Scenario Format

**How should we define test scenarios?**

**Options:**
- **JSON files**
  - ✅ Human-readable, easy to version control
  - ✅ Easy to parse in Python
  - ❌ Can get verbose

- **YAML files**
  - ✅ More concise than JSON
  - ✅ Comments supported
  - ❌ Parsing slightly slower

- **Python dataclasses**
  - ✅ Type safety, IDE support
  - ❌ Less accessible to non-programmers

- **SQLite database**
  - ✅ Queryable, good for large datasets
  - ❌ Harder to version control, edit

**Decision**: **JSON files** for scenarios, **SQLite** for results

---

### 6. Determinism in Testing

**Should tests be deterministic?**

**Challenge**: Armada has dice rolls and randomness

**Options:**
- **Seed random number generator**
  - ✅ Reproducible tests
  - ❌ Need to hook into Vassal's RNG

- **Mock dice rolls**
  - ✅ Full control
  - ❌ Need to modify Vassal module or intercept

- **Accept variance**
  - ✅ Tests real gameplay
  - ❌ Harder to debug failures

- **Hybrid**
  - Deterministic for spatial/movement tests
  - Randomized for combat, run multiple times

**Decision**: **Hybrid approach** + ability to set seed for Vassal RNG (if possible)

---

### 7. Error Handling Strategy

**How should errors be handled?**

**Principles:**
- **Fail fast** on invalid states
- **Graceful degradation** for recoverable errors
- **Rich error messages** for LLM to understand

**Error Categories:**
- **Invalid tool calls** → Return error in MCP response with explanation
- **Vassal crashes** → Restart Vassal, restore state if possible
- **Network errors** → Retry with exponential backoff
- **Illegal moves** → Return error but explain why move is illegal

**Logging:**
- Java: SLF4J + Logback
- Python: structlog for structured logging
- All errors logged with full context for debugging

---

## Open Design Questions

### UX for LLMs

1. **How verbose should tool responses be?**
   - Minimal (just data) vs. Explanatory (with context)?
   - Trade-off: token usage vs. LLM understanding

2. **Should we provide "hint" tools?**
   - E.g., `suggest_next_action()` that gives valid options
   - Could help models, but reduces benchmark difficulty

3. **How should we handle rule clarifications?**
   - Include full rules text in responses?
   - Require LLM to call `search_rules()` tool?
   - Provide "rules coach" mode vs. "tournament" mode?

### Benchmark Design

4. **What makes a good benchmark scenario?**
   - Edge cases vs. common situations?
   - Simple scenarios for diagnosis vs. complex for realism?
   - How many scenarios needed for statistical significance?

5. **How do we score strategic play?**
   - Win/loss is ultimate metric, but games are long
   - Intermediate metrics? (damage dealt, objectives scored, board control)
   - How to account for luck (dice rolls)?

6. **Difficulty progression**
   - Should tests get harder?
   - Start with rules, then tactics, then strategy?
   - Or test all levels simultaneously?

### Performance

7. **Latency targets**
   - What's acceptable for tool calls? (< 100ms? < 1s?)
   - How long can a full game take? (minutes? hours?)

8. **Caching strategy**
   - What should be cached?
   - How long to cache?
   - When to invalidate?

9. **Parallelization**
   - Run multiple tests in parallel?
   - Multiple Vassal instances?
   - How to isolate state?

---

## Information Needed from Armada Community

### Game Rules

1. **Rules Clarifications**
   - Are there edge cases in rules that are commonly misunderstood?
   - What are the most complex interactions to test?
   - Which FAQs/errata are most important?

2. **List Building Meta**
   - What makes a "competitive" fleet?
   - What are common beginner mistakes in list building?
   - Are there universally banned/restricted cards?

3. **Tactical Knowledge**
   - What are fundamental tactics every player should know?
   - What are common mistakes in ship movement?
   - How important is dice probability calculation?

### Vassal Module

4. **Module Quirks**
   - Are there known bugs in the Armada Vassal module?
   - Are there features that don't match physical game?
   - What do experienced Vassal players wish was automated?

5. **Fleet Import**
   - What's the best way to get fleets into Vassal?
   - Is Shrimpbot the standard, or are there alternatives?
   - Can we access Shrimpbot programmatically?

---

## Next Steps for Research

### Immediate (Week 1)
- [ ] Clone Vassal source code from GitHub
- [ ] Create minimal Java program to load Armada module
- [ ] Explore GameModule API interactively
- [ ] Document Armada piece types and properties
- [ ] Test basic screenshot capture

### Short-term (Weeks 2-3)
- [ ] Experiment with Command creation
- [ ] Try moving pieces programmatically
- [ ] Research Vassal headless mode
- [ ] Contact Armada Vassal module maintainers
- [ ] Get Star Forge API access and test queries

### Medium-term (Month 1)
- [ ] Prototype movement prediction algorithm
- [ ] Test attack execution in Vassal
- [ ] Build proof-of-concept MCP server
- [ ] Create 10 sample test scenarios
- [ ] Validate approach with Armada community

---

## Success Indicators for Research

We'll know we're ready to proceed when:
- ✅ We can load Armada module and access game state
- ✅ We can move at least one ship programmatically
- ✅ We can capture a screenshot of the board
- ✅ We have Star Forge API access working
- ✅ We've validated approach with Vassal community
- ✅ We have answers to critical research questions

---

## Contact & Resources

### Vassal Engine
- **Docs**: https://vassalengine.org/wiki/Main_Page
- **Forums**: https://forum.vassalengine.org/
- **GitHub**: https://github.com/vassalengine/vassal
- **JavaDoc**: https://vassalengine.org/javadoc/latest/

### Star Wars Armada
- **Armada Module**: https://vassalengine.org/wiki/Module:Star_Wars:_Armada
- **Reddit**: r/StarWarsArmada
- **Discord**: (need invite link)
- **Rules Reference**: https://www.atomicmassgames.com/star-wars-armada-documents

### MCP
- **Docs**: https://modelcontextprotocol.io/
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Examples**: https://github.com/modelcontextprotocol/servers

---

## Decision Log

*This section will track major decisions as they're made*

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| TBD | Communication protocol | | Pending |
| TBD | Web framework choice | | Pending |
| TBD | Screenshot format | | Pending |
| TBD | Test scenario format | | Pending |
