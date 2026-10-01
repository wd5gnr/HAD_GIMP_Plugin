# Hackaday Tools for GIMP

A small GIMP 3.x plug-in for common Hackaday image-preparation tasks.

Current version: **1.4.2**

## Features

### Recommended tools

- **Crop to 16:9**
  - Crops to the largest possible exact 16:9 rectangle.
  - Does **not** resample or reduce image resolution.
  - With no selection, the crop is centered.
  - With a selection, the selection is treated as the important region and the crop is positioned to preserve it whenever possible.

- **Crop to 1:1**
  - Crops to the largest possible square.
  - Does **not** resample or reduce image resolution.
  - With no selection, the crop is centered.
  - With a selection, the selection is treated as the important region and the crop is positioned to preserve it whenever possible.

- **Line art: black on white**
  - Intended for dark line art on a light background.
  - Source dark pixels become the configured Hackaday foreground color.
  - Source light pixels become the configured Hackaday background color.

- **Line art: white on black**
  - Intended for light line art on a dark background.
  - Source dark pixels become the configured Hackaday background color.
  - Source light pixels become the configured Hackaday foreground color.

- **Settings...**
  - Configure the line-art threshold.
  - Configure Hackaday foreground/background colors.
  - Configure the custom square size used by the deprecated fixed-size tool.
  - Reset settings to defaults.
  - Displays the installed plug-in version.

### Deprecated fixed-size tools

Older fixed-dimension tools are retained under:

```text
Filters → Hackaday Tools → Deprecated
```

- Resize to 800 px wide
- Make selection 600x600
- Make selection 1200x1200
- Make selection custom

The fixed-size square tools may enlarge an image if necessary so that the requested square fits.

## Default settings

```text
Threshold:                  0.50
Hackaday background color:  #1a1a1a
Hackaday foreground color:  #f3bf10
Custom square size:          1000
```

Settings are persistent between GIMP sessions.

## Installation

Create a plug-in directory under your GIMP 3.x user plug-in directory.

For GIMP 3.2 on Linux, for example:

```sh
mkdir -p ~/.config/GIMP/3.2/plug-ins/hackaday-tools
```

Copy the plug-in into that directory so that the directory and Python file have matching base names:

```text
~/.config/GIMP/3.2/plug-ins/hackaday-tools/
    hackaday-tools.py
```

Make the Python file executable:

```sh
chmod +x ~/.config/GIMP/3.2/plug-ins/hackaday-tools/hackaday-tools.py
```

Then restart GIMP when necessary.

The plug-in appears under:

```text
Filters → Hackaday Tools
```

### Emacs users

Be careful with executable Emacs backup files such as:

```text
hackaday-tools.py~
```

GIMP may also try to load an executable backup file as a plug-in. This can result in stale code being registered or run.

Either remove the backup file from the plug-in directory or make sure it is not executable.

## How the aspect-ratio crops work

The aspect-ratio tools preserve as much source resolution as possible by cropping only. They do not resize the image.

For example:

```text
4000x3000 → Crop to 16:9 → 4000x2250
6000x4000 → Crop to 16:9 → 6000x3375
4032x3024 → Crop to 1:1  → 3024x3024
```

If there is no active selection, the crop is centered.

If there is an active selection, the plug-in treats that selection as the region of interest. It positions the largest possible crop of the requested aspect ratio around that region and tries to retain the complete selection whenever geometrically possible.

This is useful when the important subject is not centered: make a rough selection around the subject, then invoke the desired crop command.

## Keyboard shortcuts

The commands are especially convenient when assigned keyboard shortcuts.

Open GIMP's keyboard-shortcut editor by going to **Preferences → Interface** and clicking **Configure Keyboard Shortcuts**.

In the shortcut editor, search for the Hackaday Tools commands and assign whatever key combinations are convenient for your workflow.

For more information, see the GIMP documentation for Interface preferences:

https://docs.gimp.org/2.6/en/gimp-pimping.html#gimp-prefs-interface

## Notes

The line-art commands share one set of persistent settings.

### Black on white

```text
source dark  → Hackaday foreground
source light → Hackaday background
```

### White on black

```text
source dark  → Hackaday background
source light → Hackaday foreground
```

The aspect-ratio crop tools are the preferred workflow for preserving full source resolution. The fixed-size resize and square tools remain available under **Deprecated** for compatibility with older workflows.
