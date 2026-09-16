# Third-party notices

## Agent Reach

- Source: https://github.com/Panniantong/Agent-Reach
- Included path: `.agents/skills/agent-reach/`
- License: MIT, copyright 2025 Agent Eyes

The repository includes the Skill instructions and references, not the full Agent Reach application. Some channels require separate tools, authentication or cookies.

## 说人话 / shuorenhua

- Source: https://github.com/larashero3-dotcom/lieflat-less-ai-tone
- Source revision used as the base: `27d29232f10124db904ca9c0536d0b67cb3b2833`
- Included path: `.agents/skills/shuorenhua/`
- License: MIT, copyright 2026 shiujan
- Local changes: Skill renamed to `shuorenhua`; added rule 12 (give the full English name of a technical term at its first occurrence) and the matching exception to the no-new-content rule

The vendored directory includes the Skill instructions, bilingual README and research notes, analysis scripts and assets. It replaces the previously vendored copy of https://github.com/MrGeDiao/shuorenhua.

## Design Geist

- Source: user-provided local Skill
- Included path: `.agents/skills/design-geist/`
- Separate license file: not provided

This Skill describes a Vercel/Geist-inspired visual language. It is not presented as official Vercel documentation.

## Academic Figures Drawer

- Source: https://github.com/M1n-n9/academic-figures-drawer
- Source revision used as the original base: `b2661ea9092f833dce93fb84ddbc2a90027eb610`
- Included path: `.agents/skills/academic-figures-drawer/`
- Local changes: component/geometry contracts, Visio and asset discovery, Tabler-default search/vendor tooling, SVG safety checks, paper-width review, reproducibility artifacts, and a density contract
- Upstream root license: no root license file was declared at the recorded revision

Do not assume that this repository's root MIT license relicenses the vendored Skill. Small utility portions retain the MIT notices recorded in `.agents/skills/academic-figures-drawer/references/THIRD_PARTY_NOTICES.md`.

The Skill uses Tabler Icons as its default external pictogram source. The complete Tabler library is not bundled; selected icons are downloaded from the official repository and retain the MIT notice in `.agents/skills/academic-figures-drawer/references/TABLER_ICONS_LICENSE.txt`.

## Nature Skills

- Source: https://github.com/Yuan1z0825/nature-skills
- Source revision: `96e41d3348748796c239cf5cb85bd947e5b02d38`
- Included paths: `.agents/skills/nature-writing/`, `.agents/skills/nature-shared/`
- License: Apache License 2.0; see `.agents/skills/nature-skills-LICENSE`

`nature-shared` is included because `$nature-writing` references it through relative paths. The vendored copy excludes local caches and generated runtime artifacts. The previous `nature-figure` Skill has been removed and replaced by `$academic-figures-drawer`.

The root MIT license applies only to original material in this repository. Vendored components retain their own licenses.
