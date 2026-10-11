# Design & UI Preferences

- Avoids generic "AI-generated dashboard" aesthetics — unnecessary gradients, excessive glassmorphism, decorative clutter, inconsistent spacing, and animation without purpose. Prefers a distinctive, warm, purposeful visual identity with strong typography, clear hierarchy, and consistent components. Confidence: 0.8
- Treats mobile as a first-class experience, not a compressed desktop layout: eliminates horizontal overflow, clipping, and overlapping elements and keeps primary actions reachable on small screens. Confidence: 0.75
- Targets WCAG 2.2 AA accessibility: semantic HTML and accessible labels, visible focus indicators, keyboard navigation and logical focus order, ~44px touch targets, reduced-motion support, and never communicates status by color alone. Confidence: 0.85
- Prioritizes fixing critical usability/functionality issues (P0) before visual polish (P2): explicitly does not want time spent refining shadows/animations/micro-details while significant usability problems remain, and doesn't accept "looks attractive" as done. Confidence: 0.65
