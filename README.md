# Hackaday Tools for GIMP

A small GIMP 3.x plug-in for common Hackaday image-preparation tasks.

Current version: **1.5.0**

## Features

### Recommended tools

- **Crop to 16:9**
  - Crops to the largest possible exact 16:9 rectangle.
  - Can optionally scale the cropped result to a configured width.
  - Optional scaling is disabled by default; its default width is 800 px.
  - With no selection, the crop is centered.
  - With a selection, the selection is treated as the important region and the crop is positioned to preserve it whenever possible.

- **Crop to 1:1**
  - Crops to the largest possible square.
  - Can optionally scale the cropped result to a configured square size.
  - Optional scaling is disabled by default; its default size is 600x600 px.
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
  - Configure optional output scaling for the 1:1 and 16:9 crop tools.
  - Choose the scaling interpolation method; NoHalo is the default.
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
Scale 1:1 result:            disabled
1:1 output size:             600 px
Scale 16:9 result:           disabled
16:9 output width:           800 px
Scaling interpolation:       NoHalo
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

The aspect-ratio tools first preserve as much source resolution as possible by cropping. If optional output scaling is enabled in **Settings...**, they then scale the cropped image to the configured dimensions.

For example:

```text
4000x3000 → Crop to 16:9 → 4000x2250
6000x4000 → Crop to 16:9 → 6000x3375
4032x3024 → Crop to 1:1  → 3024x3024
```

With the default scaling dimensions enabled, examples include:

```text
4000x3000 → Crop to 16:9 → 4000x2250 → Scale to 800x450
4032x3024 → Crop to 1:1  → 3024x3024 → Scale to 600x600
```

For 16:9 output, the configured number is the width and the height is calculated automatically. If the width does not produce a whole-pixel 16:9 height, the height is rounded to the nearest pixel. Scaling can enlarge or reduce the cropped image.

The scaling interpolation can be set to None, Linear, Cubic, NoHalo, or LoHalo. NoHalo is the default and is a strong general-purpose choice for reducing photographic images.

If there is no active selection, the crop is centered.

If there is an active selection, the plug-in treats that selection as the region of interest. It positions the largest possible crop of the requested aspect ratio around that region and tries to retain the complete selection whenever geometrically possible.

This is useful when the important subject is not centered: make a rough selection around the subject, then invoke the desired crop command.

## Keyboard shortcuts

The commands are especially convenient when assigned keyboard shortcuts.

Open GIMP's keyboard-shortcut editor by going to **Preferences → Interface** and clicking **Configure Keyboard Shortcuts**.

In the shortcut editor, search for the Hackaday Tools commands and assign whatever key combinations are convenient for your workflow.

For more information, see the GIMP documentation for Interface preferences:

https://docs.gimp.org/3.0/en/gimp-prefs-interface.html

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

The aspect-ratio crop tools are the preferred workflow. Leave their scaling options disabled to preserve full source resolution, or enable scaling to produce consistent output dimensions. The fixed-size resize and square tools remain available under **Deprecated** for compatibility with older workflows.
