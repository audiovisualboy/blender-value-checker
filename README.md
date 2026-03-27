# 🎨 Blender Value Checker

I'm a artist who works both digitally and traditionally and I use Blender to create my own reference images to paint from for some of my pieces.

Values are important in how an image reads. In my workflow no matter what the context, whether it's my reference image or the painting itself, I want to reduce it to grayscale and check the values and see how the image reads. Typically I've done this in Photoshop with some custom layer groups triggered by an action, or in Rebelle it's somewhat built in, at least partly as a quick grayscale toggle.

Blender didn't have this. So I built it.

Built by [Toto](https://github.com/audiovisualboy) — free forever. 🤘

---

## ✨ Features

- **Instant grayscale value check** via hotkey (default: F13)
- **Gaussian blur toggle** — squint effect to simplify values (default: F14)
- **Posterize / notan toggle** — reduce to flat value bands (default: F15)
- **Levels control** — Black, Mid, and White point sliders (like Photoshop Levels)
- **Compositor mode buttons** — Off / Camera / Always, right in the panel
- **Preset buttons** for blur size and posterize steps
- **Zero performance cost** when off — all nodes start muted
- **N-Panel UI** in the 3D Viewport sidebar (View3D › Sidebar › Value Check tab)

---

## 📋 Requirements

- **Blender 5.0 or newer** (fully tested on Blender 5.0.1 and 5.1.0)
- Works with any render engine (EEVEE, Cycles, Workbench)

---

## 🔧 Installation

1. Download `value_checker.py` from this repo *(click the file → click the download icon top right)*
2. In Blender, go to **Edit › Preferences › Add-ons**
3. Click **Install from Disk** and select the downloaded `.py` file
4. Enable the addon by checking the box next to **"Value Checker"**

---

## 🚀 First-Time Setup (Required Once Per Scene)

Because this addon uses the Viewport Compositor, you need to initialise it once per scene:

1. Open the **Compositor workspace** (top of Blender, or add it via the + tab)
2. Click **"New"** to create a compositor node tree
3. Switch back to your **3D Viewport**
4. In the **Value Check N-panel** (sidebar › Value Check tab), click **"Re-run Node Setup"**

✅ That's it — you're ready to go. You only need to do this once per scene.

---

## 🎮 How to Use

### Hotkeys (customisable in Preferences)
| Action | Default Key |
|---|---|
| Toggle Value Check ON/OFF | F13 |
| Toggle Blur ON/OFF | F14 |
| Toggle Posterize ON/OFF | F15 |

> 💡 **Note:** F13–F15 are available on extended Mac keyboards. If you don't have them, these are easy to reassign — go to **Edit › Preferences › Add-ons › Value Checker › Preferences** and pick whatever keys work for you. Restart Blender after changing them.

### N-Panel Controls
Open the sidebar in the 3D Viewport (`N` key) and look for the **Value Check** tab.

- **Value Check / Blur / Posterize toggles** — same as the hotkeys, but clickable
- **Off / Camera / Always** — controls when the compositor is active in the viewport
- **Blur Size slider + presets** — controls the Gaussian blur strength
- **Levels sliders** — White, Mid, Black point (like the triangles in Photoshop Levels)
- **Reset Levels** — snaps all three points back to defaults
- **Posterize Steps slider + presets** — controls how many flat value bands to show (2–8)
- **Re-run Node Setup** — use this if you start a new scene

---

## 🖼️ Screenshots

*Coming soon — screenshots and GIFs of the addon in action.*

---

## 💡 How I Use It (Recommended Workflow)

1. Paint or block in your scene in Blender
2. Tap **F13** — instant grayscale. Check your values.
3. If things feel too noisy, tap **F14** for the blur — it simulates the "squinting" trick artists use
4. Want to crunch things down and see how your values are grouping? Tap **F15** for posterize — 3 steps is usually my sweet spot
5. Tap **F13** again to flip back to color and keep painting

---

## ⚙️ Customising Hotkeys

Go to **Edit › Preferences › Add-ons › Value Checker › Preferences** to change any of the three hotkeys. Restart Blender after changing them.

---

## 📜 License

This addon is free and open source under the **GNU General Public License v3.0**.
See [LICENSE](LICENSE) for full details.

---

## 🙏 Credits

Created, directed, and tested by **Toto**. Python wrangling and API spelunking by **Claude** (Anthropic). Inspired by value-checking workflows I'd slowly built up over the years in Photoshop and Rebelle.
