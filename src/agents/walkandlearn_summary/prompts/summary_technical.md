# Technical Learning Summary Prompt

Let's pause here. I'd like you to create a **technical learning summary** of our entire session.

This is a precise documentation of concepts, formulas, and processes we covered - optimized for quick reference and future recall.

---

## Scope & Approach

**Scope:** Summarize **only what we discussed in this session**. Do not expand beyond our conversation or add external context we didn't cover.

**Tone:** Write in **second person** ("You learned...", "You explored...", "You now understand...").

**Priority:** Technical accuracy over everything else. If unsure about a detail, leave it out rather than approximate.

---

## Required Sections

### 1. TL;DR (at the top)
- Ultra-concise bullet summary of the session's core content
- 5-7 bullets maximum
- Answers: "What technical concepts did we cover?"

### 2. Quick-Reference Cheat Sheets
For each major concept/technique discussed:

**Format:**
- **Emoji + Concept Name**
- **Core Mechanism:** (step-by-step in numbered lists, NOT paragraphs)
- **Mathematical Formulation:** (LaTeX when we discussed math rigorously)
- **Concrete Example:** (numerical walkthrough if applicable)
- **When to Use:** ✅ (bullet points with emoji)
- **Limitations/Trade-offs:** ⚠️ (bullet points with emoji)

**Requirements:**
- Consistent notation across all sections
- Include formulas ONLY if we derived or discussed them in detail
- For complex derivations: use collapsible "Math Details" sections
- No "textbook completeness" - only what we actually covered

### 3. Conceptual Relationships
When relevant:
- Show how concepts connect (parent/child, special cases, variations)
- Create visual hierarchies/trees when multiple related concepts exist
- Add "Relation to X" sections showing mathematical/conceptual bridges
- Skip if we didn't explore these relationships

### 4. Mental Models Built
- Core intuitions you developed
- Use YOUR words and terminology where possible
- Include analogies or metaphors you created
- The "why it makes sense NOW" explanations
- Focus on technical understanding, not emotional journey

### 5. Conscious Blind Spots (choices, not gaps)
- Topics you CHOSE not to dive into (e.g., "Möbius inversion—interesting, but not essential")
- Things you acknowledged would require more time than the ROI justifies
- Distinguish between:
  - "I'm comfortable not knowing this deeply" ✅
  - "I want to revisit this later" 🔍

### 6. Technical Next Steps
- Natural technical extensions based on what we covered
- Deeper dives that would build on this session's foundation
- Keep it technical, not motivational

---

## Critical Guidelines

### Mathematical Rigor
- Include full derivations in collapsible sections IF we did them
- Ensure notation consistency across all formulas
- Add at least one concrete numerical example per major concept
- DO NOT add formulas we didn't actually discuss

### Accuracy Over Completeness
- If we mentioned something briefly, document it briefly
- If we went deep, provide the depth
- Match the level of detail to what actually happened
- Leave gaps rather than fill them with "standard knowledge"

### No Emotional Language
- Avoid: "breakthrough," "aha moment," "exciting," "brilliant"
- Use: "understood," "learned," "explored," "derived," "connected"
- This is a reference document, not a narrative

### Formatting
- Emojis for visual hierarchy (📌, ✅, 🔍, ⚠️)
- Notion-ready: headers (##, ###), bullets, collapsible sections
- LaTeX math when rigorous
- Top-level summaries stay concise; details go in expandable sections

---

## Special Cases

**If we did heavy math:**
- Include full derivations in collapsible sections
- Ensure notation consistency
- Add concrete numerical examples

**If we covered actionable strategies:**
- Include practical playbooks/decision frameworks
- Format as tables or step-by-step guides
- Keep language concrete and applicable

**If multiple techniques share relationships:**
- Create comparison tables
- Show decision trees for "when to use X vs Y"

---

## IMPORTANT - Generate Immediately

Do not ask clarifying questions. Begin generating the summary using these guidelines:
- **Scope:** Only this session's content
- **Focus:** Technical accuracy and quick reference
- **Length:** As needed - completeness matters more than brevity
- **Tone:** Second person, factual, precise

---

## Quality Check

Before finalizing, verify:
- [ ] All formulas use consistent notation
- [ ] No concepts explained beyond what we discussed
- [ ] Concrete examples are accurate and complete
- [ ] Mental models reflect YOUR understanding, not textbook definitions
- [ ] Rigor is present ONLY where we actually went deep
- [ ] No emotional/motivational language leaked in
- [ ] Cheat sheets are genuinely quick-reference (not paragraphs)