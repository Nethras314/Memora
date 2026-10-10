# Communication Preferences

- Communicates in terse, lowercase, often typo-laden messages with minimal context (e.g. "expo mobile app showing something went wrong"); expects the agent to investigate and infer details rather than ask many clarifying questions. Confidence: 0.85
- Reports problems by pasting the raw artifact — error text or an actual screenshot of the failure — rather than summarizing it in words. Confidence: 0.8
- When asking for design or feature input, wants it framed from a named role/lens (e.g. "as a product manager suggest", "act as a expert product manager and expert system architect") with role-appropriate rationale and trade-offs, not just code. Confidence: 0.9
- Prioritizes the end-user experience for vulnerable audiences (e.g. dementia patients): expects design suggestions to center on calm, anxiety-free, accessible UX rather than clinical/caregiver metrics. Confidence: 0.7
- For codebase audits, wants every stated requirement covered item-by-item with a candid implemented-vs-stub verdict (REAL / PARTIAL / STUB) grounded in concrete code evidence — and does not want capabilities overstated: asks explicitly whether each feature is "implemented 100% for real-world condition or is it stubs." Confidence: 0.85
