---
name: tutorial-video-style-analyzer
description: >-
  Analyze any tutorial, course, software demo, screen recording, explainer, or
  reference video project to extract a reusable video style system, then apply
  that style to scripts, voiceover copy, subtitles, keyword captions, edit notes,
  pacing, openings, endings, and shot/timeline structure. Use when the user asks
  to "分析风格", "参考这个视频", "做成通用模板", "优化文案/字幕", "总结剪辑风格",
  "生成参考文案", or create a reusable video-production skill or guide from one
  or more example videos.
---

# Tutorial Video Style Analyzer

## Overview

Use this skill to turn one or more reference videos into a reusable style system. The output should be general enough to guide future videos, not merely describe one specific project.

Load `references/style-framework.md` when the task needs a detailed analysis grid, reusable templates, or a before/after style application.

Load `references/sample-corpus-template.md` when the user provides a folder of related tutorial/demo videos and wants to abstract a cross-video style system.

## Core Rule

Separate the **example** from the **style system**.

- Example: the specific product, URL, account, platform, or topic shown in the video.
- Style system: the repeatable decisions behind it, such as pacing, proof structure, subtitle behavior, tone, visual hierarchy, and edit rhythm.

Do not hard-code a single video's subject matter unless the user explicitly asks for a project-specific guide.

## Workflow

1. Inventory the source material: video, SRT, audio, project folder, rough notes, previous draft, or reference link.
2. Extract observable evidence:
   - duration, format, aspect ratio, resolution
   - opening style
   - timeline beats
   - shot types and transitions
   - subtitle style and density
   - voiceover tone and sentence rhythm
   - visual proof methods such as screen recording, comparison, before/after, tests, charts, or real UI
   - whether the source is one video or a corpus of related examples
3. Abstract the pattern:
   - What claim does the video make?
   - What proof path supports that claim?
   - What does the creator consistently emphasize?
   - What is intentionally avoided?
   - Which details are topic-specific and which choices repeat across examples?
4. Produce the requested artifact:
   - style analysis
   - reusable style guide
   - reference copy
   - subtitle rewrite
   - keyword-caption plan
   - edit checklist
   - template for future videos
5. Keep the final answer practical. Avoid vague labels like "高级感" unless they are tied to concrete visual or writing decisions.

## Analysis Dimensions

Use these dimensions for any reference video:

- **Positioning**: tutorial, proof demo, course clip, review, sales walkthrough, case study, knowledge explainer, product update.
- **Narrative Logic**: problem -> action -> proof -> result; hook -> steps -> comparison -> conclusion; mistake -> correction -> summary.
- **Editing Rhythm**: cut frequency, zoom usage, pauses, screen focus, split-screen, title cards, transitions, cursor behavior.
- **Copy Style**: spoken or scripted, casual or formal, first-person or narrator, direct or story-led, dense or relaxed.
- **Subtitle System**: font size, placement, outline, line length, keyword color, whether captions summarize or transcribe.
- **Visual System**: brand opener, background, UI scale, color accents, crop style, overlays, callouts, icons, lower thirds.
- **Trust Devices**: live operation, data sync, side-by-side comparison, before/after, test prompt, error handling, visible timestamps, real outputs.
- **Conversion Path**: what the viewer should believe or do after watching.

## Output Modes

### Style Analysis

Return:

- Overall style verdict
- 剪辑风格
- 文案风格
- 字幕/视觉风格
- 可复用规律
- 3-5 个改进建议

### Reusable Style Guide

Return:

- Style name
- Suitable video types
- Timeline structure
- Voiceover rules
- Subtitle rules
- Visual/editing rules
- Do / Don't list
- A short template that can be reused on the next project

### Copy Or Subtitle Optimization

Return:

- revised voiceover copy
- subtitle-ready short lines
- keyword highlights
- notes about lines that are too dense, too salesy, or not backed by on-screen proof

Respect the user's scope. If the user says "只处理文本", do not propose rendering, editing, or exporting video.

## Writing Rules

- Write in natural Chinese unless the user asks otherwise.
- Prefer concrete diagnosis over praise.
- Use the user's own vocabulary when it is clear and effective.
- Keep improvements actionable: "split this subtitle", "move this proof earlier", "shorten opener", "turn this into a side-by-side comparison".
- When applying a style to a new topic, preserve the style's structure and tone, but replace all subject-specific details.

## Quality Checklist

- The style guide can be used on a different topic.
- The analysis separates topic, brand, and production choices.
- Subtitle advice includes line length and keyword behavior.
- Copy advice includes tone, rhythm, and proof logic.
- Edit advice names concrete operations, not abstract taste.
