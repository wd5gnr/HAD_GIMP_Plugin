#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import math
import os
import sys

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gimp, Gegl, GimpUi, Gtk, Gdk, GLib


# ----------------------------------------------------------------------
# Plug-in identity
# ----------------------------------------------------------------------

PLUGIN_NAME = "Hackaday Tools"
PLUGIN_VERSION = "1.4.2"
PLUGIN_BINARY = os.path.basename(sys.argv[0])


# ----------------------------------------------------------------------
# Menu paths
# ----------------------------------------------------------------------

MENU_ROOT = \
    "<Image>/Filters/Hackaday Tools"

MENU_DEPRECATED = \
    "<Image>/Filters/Hackaday Tools/Deprecated"


# ----------------------------------------------------------------------
# Procedure IDs
# ----------------------------------------------------------------------

PROC_RESIZE_800 = \
    "plug-in-hackaday-tools-resize-800-width"

PROC_SELECT_600 = \
    "plug-in-hackaday-tools-make-selection-600-square"

PROC_SELECT_1200 = \
    "plug-in-hackaday-tools-make-selection-1200-square"

PROC_SELECT_CUSTOM = \
    "plug-in-hackaday-tools-make-selection-custom-square"

PROC_CROP_16_9 = \
    "plug-in-hackaday-tools-crop-16-9"

PROC_CROP_1_1 = \
    "plug-in-hackaday-tools-crop-1-1"

PROC_LINEART_BLACK_ON_WHITE = \
    "plug-in-hackaday-tools-line-art-black-on-white"

PROC_LINEART_WHITE_ON_BLACK = \
    "plug-in-hackaday-tools-line-art-white-on-black"

PROC_SETTINGS = \
    "plug-in-hackaday-tools-settings"


# ----------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------

DEFAULT_THRESHOLD = 0.50
DEFAULT_BACKGROUND = "#1a1a1a"
DEFAULT_FOREGROUND = "#f3bf10"
DEFAULT_CUSTOM_SQUARE_SIZE = 1000

SETTINGS_SECTION = "Hackaday Tools"


# ----------------------------------------------------------------------
# General helpers
# ----------------------------------------------------------------------

def ok(procedure):
    return procedure.new_return_values(
        Gimp.PDBStatusType.SUCCESS,
        None
    )


def cancelled(procedure):
    return procedure.new_return_values(
        Gimp.PDBStatusType.CANCEL,
        None
    )


def fail(procedure, message):
    return procedure.new_return_values(
        Gimp.PDBStatusType.CALLING_ERROR,
        GLib.Error(message)
    )


def flush():
    try:
        Gimp.displays_flush()
    except Exception:
        pass


def status(message):
    try:
        Gimp.message(
            f"{PLUGIN_NAME}: {message}"
        )
    except Exception:
        pass


# ----------------------------------------------------------------------
# Persistent settings
# ----------------------------------------------------------------------

def settings_filename():
    return os.path.join(
        Gimp.directory(),
        "hackaday-tools.ini"
    )


def default_settings():
    return {
        "threshold":
            DEFAULT_THRESHOLD,

        "background":
            DEFAULT_BACKGROUND,

        "foreground":
            DEFAULT_FOREGROUND,

        "custom_square_size":
            DEFAULT_CUSTOM_SQUARE_SIZE,
    }


def normalize_hex_color(
        value,
        fallback):

    value = str(value).strip()

    if (
        len(value) != 7 or
        not value.startswith("#")
    ):
        return fallback

    try:
        int(
            value[1:],
            16
        )

    except ValueError:
        return fallback

    return value.lower()


def load_settings():
    settings = default_settings()

    parser = configparser.ConfigParser()

    try:
        parser.read(
            settings_filename(),
            encoding="utf-8"
        )

        if parser.has_section(
                SETTINGS_SECTION):

            #
            # Threshold
            #
            try:
                threshold = parser.getfloat(
                    SETTINGS_SECTION,
                    "threshold"
                )

                settings["threshold"] = max(
                    0.0,
                    min(
                        1.0,
                        threshold
                    )
                )

            except Exception:
                pass

            #
            # Background
            #
            try:
                value = parser.get(
                    SETTINGS_SECTION,
                    "background"
                )

                settings["background"] = \
                    normalize_hex_color(
                        value,
                        DEFAULT_BACKGROUND
                    )

            except Exception:
                pass

            #
            # Foreground
            #
            try:
                value = parser.get(
                    SETTINGS_SECTION,
                    "foreground"
                )

                settings["foreground"] = \
                    normalize_hex_color(
                        value,
                        DEFAULT_FOREGROUND
                    )

            except Exception:
                pass

            #
            # Custom square size
            #
            try:
                size = parser.getint(
                    SETTINGS_SECTION,
                    "custom_square_size"
                )

                settings["custom_square_size"] = max(
                    1,
                    size
                )

            except Exception:
                pass

    except Exception:
        pass

    return settings


def save_settings(settings):
    parser = configparser.ConfigParser()

    parser[SETTINGS_SECTION] = {
        "threshold":
            f"{settings['threshold']:.4f}",

        "background":
            settings["background"],

        "foreground":
            settings["foreground"],

        "custom_square_size":
            str(
                settings[
                    "custom_square_size"
                ]
            ),
    }

    try:
        os.makedirs(
            Gimp.directory(),
            exist_ok=True
        )

        with open(
                settings_filename(),
                "w",
                encoding="utf-8") as config_file:

            parser.write(
                config_file
            )

        return True

    except Exception:
        return False


# ----------------------------------------------------------------------
# Color helpers
# ----------------------------------------------------------------------

def hex_to_rgba(hex_color):
    rgba = Gdk.RGBA()

    if not rgba.parse(
            hex_color):

        rgba.parse(
            "#000000"
        )

    return rgba


def rgba_to_hex(rgba):
    r = round(
        rgba.red * 255
    )

    g = round(
        rgba.green * 255
    )

    b = round(
        rgba.blue * 255
    )

    return "#{:02x}{:02x}{:02x}".format(
        r,
        g,
        b
    )


# ----------------------------------------------------------------------
# Drawable helpers
# ----------------------------------------------------------------------

def get_target_drawables(
        image,
        drawables):

    if drawables:
        return list(
            drawables
        )

    try:
        targets = \
            image.get_selected_drawables()

        if targets:
            return list(
                targets
            )

    except Exception:
        pass

    try:
        targets = \
            image.list_selected_drawables()

        if targets:
            return list(
                targets
            )

    except Exception:
        pass

    return []


def refresh_target_drawables(
        image,
        fallback_targets):

    try:
        targets = \
            image.get_selected_drawables()

        if targets:
            return list(
                targets
            )

    except Exception:
        pass

    try:
        targets = \
            image.list_selected_drawables()

        if targets:
            return list(
                targets
            )

    except Exception:
        pass

    return fallback_targets


def ensure_rgb(
        image,
        targets):

    if not targets:
        return targets

    if image.get_base_type() != Gimp.ImageBaseType.RGB:

        image.convert_rgb()

        targets = refresh_target_drawables(
            image,
            targets
        )

    return targets


# ----------------------------------------------------------------------
# Selection helpers
# ----------------------------------------------------------------------

def selection_bounds(image):
    """
    Return None when there is no selection.

    Otherwise return:

        (x1, y1, x2, y2)
    """

    try:
        success, non_empty, \
            x1, y1, x2, y2 = \
            Gimp.Selection.bounds(
                image
            )

        if success and non_empty:

            return (
                int(x1),
                int(y1),
                int(x2),
                int(y2)
            )

    except Exception:
        pass

    return None


def save_selection(image):
    try:
        if not Gimp.Selection.is_empty(
                image):

            return Gimp.Selection.save(
                image
            )

    except Exception:
        pass

    return None


def restore_selection(
        image,
        saved_selection):

    try:
        if saved_selection is not None:

            image.select_item(
                Gimp.ChannelOps.REPLACE,
                saved_selection
            )

            image.remove_channel(
                saved_selection
            )

        else:

            Gimp.Selection.none(
                image
            )

    except Exception:
        pass


# ----------------------------------------------------------------------
# Line-art helpers
# ----------------------------------------------------------------------

def make_monochrome_lineart(
        drawable,
        threshold):

    drawable.desaturate(
        Gimp.DesaturateMode.LIGHTNESS
    )

    drawable.threshold(
        Gimp.HistogramChannel.VALUE,
        threshold,
        1.0
    )


def recolor_bw(
        image,
        drawable,
        black_color_hex,
        white_color_hex):

    black = Gegl.Color.new(
        "black"
    )

    white = Gegl.Color.new(
        "white"
    )

    black_out = Gegl.Color.new(
        black_color_hex
    )

    white_out = Gegl.Color.new(
        white_color_hex
    )

    Gimp.context_push()

    try:
        Gimp.context_set_sample_threshold(
            0.0
        )

        Gimp.context_set_sample_merged(
            False
        )

        Gimp.context_set_feather(
            False
        )

        Gimp.context_set_antialias(
            False
        )

        #
        # Thresholded black pixels
        #
        image.select_color(
            Gimp.ChannelOps.REPLACE,
            drawable,
            black
        )

        Gimp.context_set_foreground(
            black_out
        )

        drawable.edit_fill(
            Gimp.FillType.FOREGROUND
        )

        #
        # Thresholded white pixels
        #
        image.select_color(
            Gimp.ChannelOps.REPLACE,
            drawable,
            white
        )

        Gimp.context_set_foreground(
            white_out
        )

        drawable.edit_fill(
            Gimp.FillType.FOREGROUND
        )

    finally:
        Gimp.context_pop()


# ======================================================================
# DEPRECATED FIXED-SIZE TOOLS
# ======================================================================

# ----------------------------------------------------------------------
# Resize image to 800 pixels wide
# ----------------------------------------------------------------------

def run_resize_800(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    width = image.get_width()
    height = image.get_height()

    if width <= 0 or height <= 0:

        return fail(
            procedure,
            "Image has invalid dimensions."
        )

    new_width = 800

    new_height = max(
        1,
        round(
            height *
            new_width /
            width
        )
    )

    image.undo_group_start()

    try:
        image.scale(
            new_width,
            new_height
        )

    finally:
        image.undo_group_end()

    flush()

    status(
        f"resized image to "
        f"{new_width}×{new_height}"
    )

    return ok(
        procedure
    )


# ----------------------------------------------------------------------
# Generic square selection / crop helper
# ----------------------------------------------------------------------

def run_square_tool(
        procedure,
        image,
        size):

    had_selection = \
        selection_bounds(
            image
        ) is not None

    image.undo_group_start()

    try:
        width = image.get_width()
        height = image.get_height()

        if width <= 0 or height <= 0:

            return fail(
                procedure,
                "Image has invalid dimensions."
            )

        #
        # Old fixed-size behavior:
        # enlarge if the image cannot contain the requested square.
        #
        smallest = min(
            width,
            height
        )

        scaled = False

        if smallest < size:

            scale = \
                size / smallest

            new_width = max(
                size,
                round(
                    width * scale
                )
            )

            new_height = max(
                size,
                round(
                    height * scale
                )
            )

            image.scale(
                new_width,
                new_height
            )

            scaled = True

        width = image.get_width()
        height = image.get_height()

        #
        # Default:
        # centered selection.
        #
        x = (
            width - size
        ) // 2

        y = (
            height - size
        ) // 2

        #
        # Existing rough selection:
        # anchor to its upper-left corner.
        #
        if had_selection:

            bounds = selection_bounds(
                image
            )

            if bounds is not None:

                x1, y1, x2, y2 = \
                    bounds

                x = x1
                y = y1

        #
        # Keep square inside canvas.
        #
        x = min(
            x,
            width - size
        )

        y = min(
            y,
            height - size
        )

        x = max(
            0,
            x
        )

        y = max(
            0,
            y
        )

        image.select_rectangle(
            Gimp.ChannelOps.REPLACE,
            x,
            y,
            size,
            size
        )

        #
        # Existing rough selection means crop.
        #
        if had_selection:

            image.crop(
                size,
                size,
                x,
                y
            )

    finally:
        image.undo_group_end()

    flush()

    if had_selection:

        if scaled:

            status(
                f"scaled and cropped image "
                f"to {size}×{size}"
            )

        else:

            status(
                f"cropped image to "
                f"{size}×{size}"
            )

    else:

        if scaled:

            status(
                f"scaled image and created "
                f"centered {size}×{size} selection"
            )

        else:

            status(
                f"created centered "
                f"{size}×{size} selection"
            )

    return ok(
        procedure
    )


def run_select_600(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return run_square_tool(
        procedure,
        image,
        600
    )


def run_select_1200(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return run_square_tool(
        procedure,
        image,
        1200
    )


def run_select_custom(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    settings = load_settings()

    size = int(
        settings[
            "custom_square_size"
        ]
    )

    return run_square_tool(
        procedure,
        image,
        size
    )


# ======================================================================
# ASPECT-RATIO CROP TOOLS
# ======================================================================

def largest_aspect_rectangle(
        image_width,
        image_height,
        ratio_width,
        ratio_height):

    """
    Return the largest exact integer rectangle of the requested
    aspect ratio that fits inside the image without resampling.

    Example:
        4000x3000 -> 4000x2250 for 16:9
    """

    divisor = math.gcd(
        ratio_width,
        ratio_height
    )

    rw = \
        ratio_width // divisor

    rh = \
        ratio_height // divisor

    scale = min(
        image_width // rw,
        image_height // rh
    )

    if scale < 1:
        return None

    return (
        rw * scale,
        rh * scale
    )


def position_aspect_crop(
        image_width,
        image_height,
        crop_width,
        crop_height,
        bounds):

    """
    Position a fixed-size aspect-ratio crop.

    No selection:
        Center the crop.

    With selection:
        Treat the selection as the important region.

        Start by centering the crop on it, then constrain the
        crop so the entire selection remains visible whenever
        geometrically possible.

    The crop is finally clamped to the image boundaries.
    """

    #
    # No selection:
    # ordinary centered crop.
    #
    if bounds is None:

        x = (
            image_width -
            crop_width
        ) // 2

        y = (
            image_height -
            crop_height
        ) // 2

        return x, y


    x1, y1, x2, y2 = \
        bounds

    selection_width = max(
        1,
        x2 - x1
    )

    selection_height = max(
        1,
        y2 - y1
    )

    center_x = \
        (x1 + x2) / 2.0

    center_y = \
        (y1 + y2) / 2.0


    #
    # Initially center the crop on the selection.
    #
    x = round(
        center_x -
        crop_width / 2.0
    )

    y = round(
        center_y -
        crop_height / 2.0
    )


    #
    # If the selection fits horizontally, constrain X to positions
    # that preserve the entire selection.
    #
    if selection_width <= crop_width:

        min_x = max(
            0,
            x2 - crop_width
        )

        max_x = min(
            x1,
            image_width -
            crop_width
        )

        if min_x <= max_x:

            x = max(
                min_x,
                min(
                    x,
                    max_x
                )
            )


    #
    # Same logic vertically.
    #
    if selection_height <= crop_height:

        min_y = max(
            0,
            y2 - crop_height
        )

        max_y = min(
            y1,
            image_height -
            crop_height
        )

        if min_y <= max_y:

            y = max(
                min_y,
                min(
                    y,
                    max_y
                )
            )


    #
    # Final safety clamp.
    #
    x = max(
        0,
        min(
            x,
            image_width -
            crop_width
        )
    )

    y = max(
        0,
        min(
            y,
            image_height -
            crop_height
        )
    )

    return (
        int(x),
        int(y)
    )


def run_aspect_crop(
        procedure,
        image,
        ratio_width,
        ratio_height):

    width = image.get_width()
    height = image.get_height()

    if width <= 0 or height <= 0:

        return fail(
            procedure,
            "Image has invalid dimensions."
        )

    #
    # The existing selection is the region of interest.
    #
    bounds = selection_bounds(
        image
    )

    dimensions = \
        largest_aspect_rectangle(
            width,
            height,
            ratio_width,
            ratio_height
        )

    if dimensions is None:

        return fail(
            procedure,
            "Image is too small for "
            "that aspect ratio."
        )

    crop_width, crop_height = \
        dimensions

    x, y = \
        position_aspect_crop(
            width,
            height,
            crop_width,
            crop_height,
            bounds
        )

    image.undo_group_start()

    try:

        #
        # Replace any rough selection with the actual crop area.
        #
        image.select_rectangle(
            Gimp.ChannelOps.REPLACE,
            x,
            y,
            crop_width,
            crop_height
        )

        #
        # Aspect-ratio operations never resample.
        #
        image.crop(
            crop_width,
            crop_height,
            x,
            y
        )

    finally:
        image.undo_group_end()

    flush()

    if bounds is None:

        status(
            f"center-cropped to "
            f"{ratio_width}:{ratio_height} "
            f"({crop_width}×{crop_height}); "
            f"no resizing"
        )

    else:

        status(
            f"cropped around selection to "
            f"{ratio_width}:{ratio_height} "
            f"({crop_width}×{crop_height}); "
            f"no resizing"
        )

    return ok(
        procedure
    )


def run_crop_16_9(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return run_aspect_crop(
        procedure,
        image,
        16,
        9
    )


def run_crop_1_1(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return run_aspect_crop(
        procedure,
        image,
        1,
        1
    )


# ======================================================================
# LINE-ART CONVERSION
# ======================================================================

def lineart_convert(
        procedure,
        image,
        drawables,
        source_black_is_foreground):

    settings = load_settings()

    threshold = \
        settings["threshold"]

    background = \
        settings["background"]

    foreground = \
        settings["foreground"]

    targets = get_target_drawables(
        image,
        drawables
    )

    if not targets:

        return fail(
            procedure,
            "This command needs a "
            "selected drawable/layer."
        )

    saved_selection = save_selection(
        image
    )

    image.undo_group_start()

    try:
        targets = ensure_rgb(
            image,
            targets
        )

        for drawable in targets:

            make_monochrome_lineart(
                drawable,
                threshold
            )

            if source_black_is_foreground:

                #
                # BLACK ON WHITE
                #
                # Source dark  -> Hackaday foreground
                # Source light -> Hackaday background
                #
                recolor_bw(
                    image,
                    drawable,
                    foreground,
                    background
                )

            else:

                #
                # WHITE ON BLACK
                #
                # Source dark  -> Hackaday background
                # Source light -> Hackaday foreground
                #
                recolor_bw(
                    image,
                    drawable,
                    background,
                    foreground
                )

            drawable.update(
                0,
                0,
                drawable.get_width(),
                drawable.get_height()
            )

        restore_selection(
            image,
            saved_selection
        )

    finally:
        image.undo_group_end()

    flush()

    status(
        "converted line art "
        f"using threshold {threshold:.2f}"
    )

    return ok(
        procedure
    )


def run_lineart_black_on_white(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return lineart_convert(
        procedure,
        image,
        drawables,
        source_black_is_foreground=True
    )


def run_lineart_white_on_black(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    return lineart_convert(
        procedure,
        image,
        drawables,
        source_black_is_foreground=False
    )


# ======================================================================
# SETTINGS
# ======================================================================

def run_settings(
        procedure,
        run_mode,
        image,
        drawables,
        config,
        data):

    GimpUi.init(
        PLUGIN_BINARY
    )

    settings = load_settings()

    dialog = Gtk.Dialog(
        title=f"{PLUGIN_NAME} Settings"
    )

    RESPONSE_RESET = 1001

    dialog.add_button(
        "_Reset Defaults",
        RESPONSE_RESET
    )

    dialog.add_button(
        "_Cancel",
        Gtk.ResponseType.CANCEL
    )

    dialog.add_button(
        "_OK",
        Gtk.ResponseType.OK
    )

    dialog.set_default_response(
        Gtk.ResponseType.OK
    )

    dialog.set_resizable(
        False
    )

    content = \
        dialog.get_content_area()

    content.set_border_width(
        12
    )

    grid = Gtk.Grid()

    grid.set_row_spacing(
        10
    )

    grid.set_column_spacing(
        12
    )

    content.pack_start(
        grid,
        True,
        True,
        0
    )


    #
    # Threshold
    #
    threshold_label = Gtk.Label(
        label="Threshold:"
    )

    threshold_label.set_xalign(
        0.0
    )

    threshold_spin = \
        Gtk.SpinButton.new_with_range(
            0.0,
            1.0,
            0.01
        )

    threshold_spin.set_digits(
        2
    )

    threshold_spin.set_value(
        settings["threshold"]
    )

    threshold_spin.set_tooltip_text(
        "Brightness threshold used to reduce "
        "the source to black and white before "
        "recoloring."
    )

    grid.attach(
        threshold_label,
        0,
        0,
        1,
        1
    )

    grid.attach(
        threshold_spin,
        1,
        0,
        1,
        1
    )


    #
    # Background color
    #
    background_label = Gtk.Label(
        label="Hackaday background color:"
    )

    background_label.set_xalign(
        0.0
    )

    background_button = \
        Gtk.ColorButton.new_with_rgba(
            hex_to_rgba(
                settings["background"]
            )
        )

    background_button.set_use_alpha(
        False
    )

    grid.attach(
        background_label,
        0,
        1,
        1,
        1
    )

    grid.attach(
        background_button,
        1,
        1,
        1,
        1
    )


    #
    # Foreground color
    #
    foreground_label = Gtk.Label(
        label="Hackaday foreground color:"
    )

    foreground_label.set_xalign(
        0.0
    )

    foreground_button = \
        Gtk.ColorButton.new_with_rgba(
            hex_to_rgba(
                settings["foreground"]
            )
        )

    foreground_button.set_use_alpha(
        False
    )

    grid.attach(
        foreground_label,
        0,
        2,
        1,
        1
    )

    grid.attach(
        foreground_button,
        1,
        2,
        1,
        1
    )


    #
    # Deprecated custom square size
    #
    custom_size_label = Gtk.Label(
        label="Custom square size:"
    )

    custom_size_label.set_xalign(
        0.0
    )

    custom_size_spin = \
        Gtk.SpinButton.new_with_range(
            1,
            10000,
            1
        )

    custom_size_spin.set_digits(
        0
    )

    custom_size_spin.set_value(
        settings[
            "custom_square_size"
        ]
    )

    custom_size_spin.set_tooltip_text(
        "Pixel size used by the deprecated "
        "'Make selection custom' command."
    )

    grid.attach(
        custom_size_label,
        0,
        3,
        1,
        1
    )

    grid.attach(
        custom_size_spin,
        1,
        3,
        1,
        1
    )


    #
    # Separator
    #
    separator = Gtk.Separator(
        orientation=
            Gtk.Orientation.HORIZONTAL
    )

    grid.attach(
        separator,
        0,
        4,
        2,
        1
    )


    #
    # About/version information
    #
    about = Gtk.Label()

    about.set_xalign(
        0.0
    )

    about.set_markup(
        f"<b>{PLUGIN_NAME} "
        f"{PLUGIN_VERSION}</b>\n"
        "Utilities for preparing images "
        "for Hackaday.\n\n"
        "Crop images to common aspect ratios "
        "without resampling, convert "
        "black-and-white line art to Hackaday "
        "colors, and retain the older fixed-size "
        "tools under Deprecated."
    )

    about.set_line_wrap(
        True
    )

    grid.attach(
        about,
        0,
        5,
        2,
        1
    )

    dialog.show_all()


    while True:

        response = dialog.run()


        if response == RESPONSE_RESET:

            threshold_spin.set_value(
                DEFAULT_THRESHOLD
            )

            background_button.set_rgba(
                hex_to_rgba(
                    DEFAULT_BACKGROUND
                )
            )

            foreground_button.set_rgba(
                hex_to_rgba(
                    DEFAULT_FOREGROUND
                )
            )

            custom_size_spin.set_value(
                DEFAULT_CUSTOM_SQUARE_SIZE
            )

            continue


        if response == \
                Gtk.ResponseType.OK:

            new_settings = {
                "threshold":
                    threshold_spin.get_value(),

                "background":
                    rgba_to_hex(
                        background_button.get_rgba()
                    ),

                "foreground":
                    rgba_to_hex(
                        foreground_button.get_rgba()
                    ),

                "custom_square_size":
                    custom_size_spin.get_value_as_int(),
            }

            if not save_settings(
                    new_settings):

                error_dialog = \
                    Gtk.MessageDialog(
                        transient_for=dialog,
                        flags=
                            Gtk.DialogFlags.MODAL,
                        message_type=
                            Gtk.MessageType.ERROR,
                        buttons=
                            Gtk.ButtonsType.OK,
                        text=
                            "Could not save "
                            "Hackaday Tools settings."
                    )

                error_dialog.format_secondary_text(
                    settings_filename()
                )

                error_dialog.run()
                error_dialog.destroy()

                dialog.destroy()

                return fail(
                    procedure,
                    "Could not save "
                    "Hackaday Tools settings."
                )

            dialog.destroy()

            status(
                "settings saved"
            )

            return ok(
                procedure
            )


        dialog.destroy()

        return cancelled(
            procedure
        )


# ======================================================================
# REGISTRATION
# ======================================================================

def make_image_procedure(
        plugin,
        name,
        run_func,
        menu_label,
        blurb,
        image_types="*",
        menu_path=MENU_ROOT):

    procedure = \
        Gimp.ImageProcedure.new(
            plugin,
            name,
            Gimp.PDBProcType.PLUGIN,
            run_func,
            None
        )

    procedure.set_image_types(
        image_types
    )

    procedure.set_sensitivity_mask(
        Gimp.ProcedureSensitivityMask.DRAWABLE |
        Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    )

    procedure.set_menu_label(
        menu_label
    )

    procedure.set_attribution(
        PLUGIN_NAME,
        PLUGIN_NAME,
        "2026"
    )

    procedure.add_menu_path(
        menu_path
    )

    procedure.set_documentation(
        blurb,
        blurb,
        None
    )

    return procedure


class HackadayTools(
        Gimp.PlugIn):

    def do_query_procedures(
            self):

        return [
            PROC_RESIZE_800,
            PROC_SELECT_600,
            PROC_SELECT_1200,
            PROC_SELECT_CUSTOM,
            PROC_CROP_16_9,
            PROC_CROP_1_1,
            PROC_LINEART_BLACK_ON_WHITE,
            PROC_LINEART_WHITE_ON_BLACK,
            PROC_SETTINGS,
        ]


    def do_create_procedure(
            self,
            name):

        #
        # Recommended aspect-ratio crop tools
        #
        if name == PROC_CROP_16_9:

            return make_image_procedure(
                self,
                name,
                run_crop_16_9,
                "Crop to _16:9",
                "Crop to the largest possible "
                "16:9 rectangle without resizing. "
                "With no selection the crop is "
                "centered. With a selection, position "
                "the crop to preserve the selected "
                "region whenever possible."
            )


        if name == PROC_CROP_1_1:

            return make_image_procedure(
                self,
                name,
                run_crop_1_1,
                "Crop to _1:1",
                "Crop to the largest possible square "
                "without resizing. With no selection "
                "the crop is centered. With a selection, "
                "position the crop to preserve the "
                "selected region whenever possible."
            )


        #
        # Line-art tools
        #
        if name == \
                PROC_LINEART_BLACK_ON_WHITE:

            return make_image_procedure(
                self,
                name,
                run_lineart_black_on_white,
                "Line art: _black on white",
                "Convert source art with dark lines "
                "on a light background to the "
                "configured Hackaday foreground and "
                "background colors.",
                "RGB*, GRAY*, INDEXED*"
            )


        if name == \
                PROC_LINEART_WHITE_ON_BLACK:

            return make_image_procedure(
                self,
                name,
                run_lineart_white_on_black,
                "Line art: _white on black",
                "Convert source art with light lines "
                "on a dark background to the "
                "configured Hackaday foreground and "
                "background colors.",
                "RGB*, GRAY*, INDEXED*"
            )


        #
        # Deprecated fixed-dimension tools
        #
        if name == PROC_RESIZE_800:

            return make_image_procedure(
                self,
                name,
                run_resize_800,
                "Resize to _800 px wide",
                "Deprecated fixed-width resize tool.",
                menu_path=
                    MENU_DEPRECATED
            )


        if name == PROC_SELECT_600:

            return make_image_procedure(
                self,
                name,
                run_select_600,
                "Make selection _600x600",
                "Deprecated fixed-size square tool.",
                menu_path=
                    MENU_DEPRECATED
            )


        if name == PROC_SELECT_1200:

            return make_image_procedure(
                self,
                name,
                run_select_1200,
                "Make selection _1200x1200",
                "Deprecated fixed-size square tool.",
                menu_path=
                    MENU_DEPRECATED
            )


        if name == PROC_SELECT_CUSTOM:

            return make_image_procedure(
                self,
                name,
                run_select_custom,
                "Make selection _custom",
                "Deprecated configurable fixed-size "
                "square tool.",
                menu_path=
                    MENU_DEPRECATED
            )


        #
        # Settings
        #
        if name == PROC_SETTINGS:

            procedure = \
                Gimp.ImageProcedure.new(
                    self,
                    name,
                    Gimp.PDBProcType.PLUGIN,
                    run_settings,
                    None
                )

            procedure.set_image_types(
                "*"
            )

            #
            # Settings works without an active image.
            #
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.ALWAYS
            )

            procedure.set_menu_label(
                "_Settings..."
            )

            procedure.set_attribution(
                PLUGIN_NAME,
                PLUGIN_NAME,
                "2026"
            )

            procedure.add_menu_path(
                MENU_ROOT
            )

            procedure.set_documentation(
                f"Configure {PLUGIN_NAME} "
                f"{PLUGIN_VERSION}.",

                "Set the line-art threshold, "
                "Hackaday foreground/background "
                "colors and deprecated custom "
                "square size.",

                None
            )

            return procedure


        return None


Gimp.main(
    HackadayTools.__gtype__,
    sys.argv
)
