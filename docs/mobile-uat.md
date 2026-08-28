# Mobile UAT

Task 22 validates the shared responsive shell at 320, 375, 390, 430, and 768 CSS pixels.

## Covered journeys

- Login and signup use a fluid authentication card and 16px form controls.
- Today, Aria, Actions, Insights, Team, and Settings collapse multi-column content to one column.
- Backlog filters and list rows stack at narrow widths.
- The Sprint board remains a contained, touch-scrollable horizontal board; it does not widen the page.
- Daily Scrum forms and summaries use the same fluid form and grid rules.
- Tables scroll inside `.table-wrap`; mobile alternatives remain available where supplied.
- Modals stay inside the viewport and scroll their own content.

## Acceptance notes

The document viewport prevents page-level horizontal overflow, long user content wraps, controls remain within their containers, and form controls use a 16px minimum font size to prevent unexpected iOS input zoom. Device-specific install prompts and browser chrome remain controlled by Chrome/Android and Safari/iOS.
