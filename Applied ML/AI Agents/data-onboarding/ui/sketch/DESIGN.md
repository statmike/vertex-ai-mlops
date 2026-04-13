# Design System Specification

## 1. Creative North Star: "The Celestial Curator"
This design system is built to transcend the rigid, box-bound layouts of traditional software. We are moving away from "webpages" and toward "immersive environments." The North Star, **The Celestial Curator**, treats the interface as a dark, infinite expanse where data floats like bioluminescent organisms. 

To achieve this, we reject standard rectangular sidebars. We embrace organic, asymmetrical silhouettes, heavy backdrop blurs, and "quietly powerful" interactions. Every element must feel like it is suspended in a liquid, midnight medium—layered, luminous, and intentional.

---

## 2. Color & Atmosphere
The palette is rooted in the "Deepest Midnight." We use dark foundations to allow our "electric" intelligence accents to pierce through the void.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or layout containment. 
Boundaries must be defined through:
1.  **Background Tonal Shifts:** Use `surface-container-low` against `surface` to imply a region.
2.  **Soft Glows:** Use `primary` or `secondary` at 5-10% opacity as a soft outer glow.
3.  **Negative Space:** Large gutters are the primary separator.

### Surface Hierarchy & Nesting
Treat the UI as stacked sheets of frosted obsidian. 
- **Base Layer:** `surface` (#0a0e16)
- **Deepest Recess:** `surface-container-lowest` (#000000) for "sunken" utility areas.
- **Floating Containers:** `surface-bright` (#262c39) with 60% opacity and a 20px backdrop blur.
- **The "Glass & Gradient" Rule:** Main interactive surfaces should use a linear gradient: `surface-container-high` to `surface-container-highest` at a 135-degree angle to provide a subtle "sheen" of depth.

### Accents of Intelligence
- **Primary (Intelligent Blue):** `#85adff` — Use for core actions and active states.
- **Secondary (Electric Cyan):** `#00e3fd` — Reserved for data visualizations and high-priority "AI" insights.
- **Tertiary (Deep Violet):** `#ac89ff` — Used for secondary intelligence and creative features.

---

## 3. Typography: Sophisticated Air
We use **Manrope** for its geometric yet warm characteristics. The goal is "Airy Editorial"—high tracking for labels and generous line heights for body text.

- **Display (3.5rem - 2.25rem):** Set with -2% letter spacing. Use for evocative hero statements.
- **Headline (2rem - 1.5rem):** The "Workhorse" of the system. Always use `on-surface`.
- **Title (1.375rem - 1rem):** Medium weight. These act as the anchors for your organic containers.
- **Body (1rem - 0.75rem):** Line-height must be 1.6x. Use `on-surface-variant` (#a7abb6) for long-form text to reduce visual "vibration" against the dark background.
- **Labels (0.75rem - 0.6875rem):** Uppercase with +10% letter spacing. Use these for metadata to maintain a futuristic, technical feel.

---

## 4. Elevation & Depth
Depth is not a drop shadow; it is **Tonal Layering**.

- **The Layering Principle:** To create a "lifted" card, do not use a black shadow. Instead, place a `surface-container-high` element on a `surface-container-low` background. The color shift *is* the elevation.
- **Ambient Glows:** When an element must "float" (e.g., a modal), use a shadow with a 60px blur, 0px offset, and 8% opacity using the `primary` color. This creates an "aura" rather than a shadow.
- **Ghost Borders:** If accessibility requires a boundary, use `outline-variant` (#444852) at **15% opacity**. It should be felt, not seen.
- **Organic Curvature:** 
    - **Containers:** `xl` (3rem/48px) or `lg` (2rem/32px).
    - **Buttons/Chips:** `full` (9999px) for a pill-shaped, organic feel.

---

## 5. Components

### Organic Containers (The "Anti-Sidebar")
Instead of a vertical bar, use a "Floating Pod." A large, `xl` rounded container that sits 24px away from the screen edge, using Glassmorphism (60% opacity + `surface-bright`).

### Buttons
- **Primary:** `primary` (#85adff) background with `on-primary` (#002c66) text. No border. High-gloss finish (subtle top-down white gradient at 10% opacity).
- **Secondary:** Transparent background with a `Ghost Border` and `primary` text.
- **Tertiary:** No background. `on-surface-variant` text that shifts to `primary` on hover.

### Input Fields
Inputs should not look like boxes. Use a `surface-container-low` background with a `full` (pill) roundness. The focus state should not be a border change, but a soft `primary` outer glow (4px blur).

### Chips (Data Points)
Small, `full` rounded elements. For intelligence-led data, use the `secondary` (Cyan) color at 10% opacity for the background and 100% opacity for the text.

### Cards & Lists
**Strict Rule:** No dividers. Separate items using 12px of vertical space. For lists, use a subtle hover state that changes the background to `surface-container-highest` with a `md` (1.5rem) corner radius.

---

## 6. Do’s and Don'ts

### Do:
- **Use Asymmetry:** Let containers have different corner radii (e.g., 48px, 48px, 48px, 8px) to create a "custom" feel.
- **Embrace Blur:** Use backdrop-blur (12px to 20px) on every floating element to ensure legibility over the deep background.
- **Layer Z-Indices:** Allow elements to slightly overlap. A chip should partially sit over the edge of a card to imply physical depth.

### Don’t:
- **No Pure White:** Never use #FFFFFF. The brightest text should be `on-surface` (#ebedfa).
- **No Hard Edges:** Avoid `none` or `sm` roundness unless it is for a tiny utility icon.
- **No Default Shadows:** Avoid the "Multiply" black shadow. If it isn't a tinted glow, it doesn't belong in this system.
- **No Dense Grids:** If the layout feels "crowded," remove an element. This system requires "Quiet Power"—the luxury of space.