# Frontend Coding Agent Prompt

You are a frontend developer building a modern Next.js (React) interface for the EREX pipeline APIs. Deliver a clean, elegant, and modern UI (light theme, ample whitespace, clear hierarchy). Avoid purple bias; use a restrained palette with accent color and good typography.

## Requirements
- Framework: Next.js (App Router preferred), React, TypeScript.
- Data sources: EREX backend APIs.
  - `GET /pipeline/config` — show pipeline steps and config summary.
  - `POST /pipeline/upload` — upload pst/eml/msg to `data/` (multipart).
  - `DELETE /pipeline/files` — delete selected files in `data/`.
  - `POST /pipeline/run` — trigger pipeline, display results and summary.
  - `POST /pipeline/tech-insight` — given `{keyword, count, ratio, category?}`, return short OpenAI-generated description.
- State: handle loading, error, empty states; show toasts/snackbars for success/errors.
- Performance: debounce expensive actions; paginate/virtualize large lists if needed.

## UI Structure
1) **Header**: App name, quick actions (Upload, Run, Refresh Config), theme toggle (optional).
2) **Config Panel**: Show pipeline steps and config summary returned by `/pipeline/config` (render key/value grid). Allow manual refresh.
3) **File Manager**: Upload area (drag & drop), list of current files (names from `data/` directory via a new “list files” call or infer from run results). Actions: delete selected files (calls `DELETE /pipeline/files`).
4) **Run & Results**:
   - Button to trigger `/pipeline/run`; show spinner and status logs.
   - Display **summary** from the response: `message_count`, `block_count`, keyword_summary, class_summary.
   - Display **per-mail** cards: `source_path`, `subject`, `semantic` (text/score/lines if matched), and per-mail aggregation stats.
5) **Charts**: Based on `/pipeline/run` summary.
   - Keyword summary: bar/treemap for top categories and keywords (count/ratio).
   - Class summary: pie/donut (ok/ng or other classes).
   - Message vs block count: simple stats tiles.
   Use a lightweight chart lib (e.g., Recharts or Chart.js) with responsive layout.
6) **Tech Insight Modal/Drawer**:
   - Keywords in charts or lists are clickable; clicking calls `/pipeline/tech-insight` with that keyword’s `count/ratio`/category and shows the returned insight text.
   - Show loading state while waiting for the insight.

## Interaction Notes
- `/pipeline/run` response shape:
  ```json
  {
    "results": [
      {
        "source_path": "...",
        "subject": "...",
        "semantic": {"text":"...","score":0.72,"start_line":3,"end_line":8,"matched":true,"line_scores":[...]},
        "aggregation": {
          "block_count": 2,
          "keyword_summary": {"programming_languages": [{"keyword":"Python","count":1,"ratio":0.5}]},
          "class_summary": {"ok": {"count":1,"ratio":0.5}, "ng": {"count":1,"ratio":0.5}}
        }
      }
    ],
    "summary": {
      "message_count": 10,
      "block_count": 15,
      "keyword_summary": { ...category -> [{keyword,count,ratio}]... },
      "class_summary": { ...class -> {count, ratio}... }
    }
  }
  ```
- `/pipeline/tech-insight` request: `{keyword, count, ratio, category?}`; response: `{keyword, insight}`.
- Upload: `POST /pipeline/upload` multipart with `files[]`.
- Delete: `DELETE /pipeline/files` with JSON array of filenames.

## Visual/UX Guidelines
- Modern, minimal layout with clear sections; prefer cards and grids over tables when possible.
- Typography: pick a clean sans-serif (e.g., Inter/Manrope), use weight/size hierarchy.
- Colors: neutral background, strong contrast for text, single accent color for CTAs/highlights.
- Feedback: snackbars/toasts for async actions, inline error texts near components.
- Accessibility: keyboard focus states, aria labels for inputs/buttons.
- Responsive: adapt charts and grids for mobile/tablet.

## Deliverables
- Next.js project structure with pages/components/services/hooks separated.
- API client utilities for the endpoints above (fetch/axios), with typed responses.
- Reusable UI components: Upload dropzone, Stats tiles, Charts, Keyword list with click-to-insight, Modal/Drawer for insights.
- Minimal but clear styling (CSS modules, Tailwind, or styled-components acceptable). Ensure consistent spacing system and theme tokens.

Follow this prompt to implement the frontend in a focused, production-friendly manner.
