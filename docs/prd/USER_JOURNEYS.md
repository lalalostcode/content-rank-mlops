# Analyst and visitor journeys

1. An analyst selects an authorized client. Show the snapshot date, coverage and queue freshness together. If no run exists, show pending scoring.
2. Filter the queue by review status, open an item, inspect units, timestamps and reason codes. Preserve client, filters and run when navigating back.
3. Start review, record a decision and optional note, then close or defer. A conflicting edit refreshes the item and preserves the unsent note. A retry uses the same request key.
4. Revisit history after a new snapshot arrives. Show comparable measures and dates. Missing follow-up produces an explicit empty state. Observed changes do not establish intervention effects.
5. A portfolio visitor repeats the journey using a labeled synthetic fixture. The static adapter holds edits until reload.
