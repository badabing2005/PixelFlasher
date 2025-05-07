#!/usr/bin/env python

# This file is part of PixelFlasher https://github.com/badabing2005/PixelFlasher
#
# Copyright (C) 2025 Badabing2005
# SPDX-FileCopyrightText: 2025 Badabing2005
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Also add information on how to contact you by electronic and paper mail.
#
# If your software can interact with users remotely through a computer network,
# you should also make sure that it provides a way for users to get its source.
# For example, if your program is a web application, its interface could
# display a "Source" link that leads users to an archive of the code. There are
# many ways you could offer source, and different solutions will be better for
# different programs; see section 13 for the specific requirements.
#
# You should also get your employer (if you work as a programmer) or school, if
# any, to sign a "copyright disclaimer" for the program, if necessary. For more
# information on this, and how to apply and follow the GNU AGPL, see
# <https://www.gnu.org/licenses/>.
"""
Internationalization support for PixelFlasher.

This module provides functions for translating text in the application.
It uses a simple catalog-based approach that works with f-strings.
"""

import os
import gettext
import locale
import logging
import builtins
import json
import polib  # For compiling PO files to MO files

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Global variables
translations = {}
current_language = None
fallback_language = 'en'
string_catalog = {}
locale_dir = None  # Store locale directory globally for access by get_locale_path

# ============================================================================
#                               Function translate_text
# ============================================================================
def translate_text(text, lang=None, **kwargs):
    """
    Translate a string using the specified language (or current language) and apply formatting.

    Args:
        text: The string to translate
        lang: Specific language to use (default: None, which uses current_language)
        **kwargs: Format parameters to apply to the translated string

    Returns:
        Translated and formatted string
    """
    global current_language, translations, string_catalog

    # Use specified language if provided, otherwise use current language
    if lang is not None:
        target_lang = lang
    else:
        target_lang = current_language

    # If 'en' is specified as the target language, or if we need English regardless of
    # the current language setting, return the original text
    if target_lang == 'en':
        translated = text
    # Otherwise translate according to requested language
    elif target_lang in translations:
        # Get the translated text
        translated = translations[target_lang].gettext(text)
        # If the translation is empty, fall back to the original text
        # This handles cases where msgstr is empty in the .po file
        if not translated:
            translated = text
    else:
        translated = text

    # Apply formatting if kwargs are provided
    if kwargs:
        try:
            return translated.format(**kwargs)
        except KeyError as e:
            logging.warning(f"Missing key in translation format: {e}")
            return translated
    return translated

# Alias for cleaner code
_ = translate_text

# Always set up a fallback translation function immediately
builtins.__dict__['_'] = translate_text

# ============================================================================
#                               Function get_locale_path
# ============================================================================
def get_locale_path():
    """Return the path to the locale directory."""
    global locale_dir
    if locale_dir is None:
        locale_dir = find_locale_dir()
    return locale_dir

# ============================================================================
#                               Function get_translation_for_language
# ============================================================================
def get_translation_for_language(lang_code):
    """
    Get a gettext translation object for a specific language.

    Args:
        lang_code: Language code to get translation for

    Returns:
        gettext.NullTranslation: Translation object for the language, or NullTranslation if unavailable
    """
    global translations

    # If we already have this translation loaded, return it
    if lang_code in translations:
        return translations[lang_code]

    # Try to load the translation
    try:
        locale_dir = get_locale_path()
        translation = gettext.translation('pixelflasher', localedir=locale_dir, languages=[lang_code], fallback=True)
        translations[lang_code] = translation
        return translation
    except Exception as e:
        logging.warning(f"Failed to load translation for {lang_code}: {e}")
        return gettext.NullTranslations()

# ============================================================================
#                               Function get_text_in_language
# ============================================================================
def get_text_in_language(text, lang_code):
    """
    Get a translated text in a specific language regardless of the current language setting.

    Args:
        text: The text to translate
        lang_code: The language code to translate to

    Returns:
        str: The translated text, or the original text if translation is unavailable
    """
    if lang_code == 'en':
        return text

    translation = get_translation_for_language(lang_code)
    return translation.gettext(text)

# ============================================================================
#                               Function get_system_language
# ============================================================================
def get_system_language():
    """Get the system language code."""
    try:
        # Get the user's preferred language
        lang, _ = locale.getdefaultlocale()
        if lang:
            # Strip encoding if present and convert to lowercase
            return lang.split('.')[0].split('_')[0]
    except Exception as e:
        logging.warning(f"Could not determine system language: {e}")

    # Default to English if we can't determine the system language
    return fallback_language

# ============================================================================
#                               Function find_locale_dir
# ============================================================================
def find_locale_dir():
    """Find the locale directory, checking multiple possible locations."""
    base_dirs = [
        # Standard location relative to the script
        os.path.dirname(os.path.abspath(__file__)),
        # Relative to the current working directory
        os.getcwd(),
        # Check for a dedicated locale directory in parent folders
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locale'),
    ]

    for base_dir in base_dirs:
        locale_dir = os.path.join(base_dir, 'locale')
        if os.path.exists(locale_dir) and os.path.isdir(locale_dir):
            logging.info(f"Found locale directory at: {locale_dir}")
            return locale_dir

    # If no existing directory is found, create and return the default one
    default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')
    os.makedirs(default_dir, exist_ok=True)
    logging.info(f"Created default locale directory at: {default_dir}")
    return default_dir

# ============================================================================
#                               Function setup_i18n
# ============================================================================
def setup_i18n():
    """Set up internationalization for the application."""
    global translations, current_language, fallback_language, locale_dir

    try:
        # Find the locale directory
        locale_dir = find_locale_dir()

        # Get available languages by looking at directories in the locale folder
        available_languages = []
        if os.path.exists(locale_dir):
            for lang_dir in os.listdir(locale_dir):
                if os.path.isdir(os.path.join(locale_dir, lang_dir)):
                    # Check if this directory contains LC_MESSAGES with our domain
                    mo_path = os.path.join(locale_dir, lang_dir, 'LC_MESSAGES', 'pixelflasher.mo')
                    po_path = os.path.join(locale_dir, lang_dir, 'LC_MESSAGES', 'pixelflasher.po')
                    if os.path.exists(mo_path) or os.path.exists(po_path):
                        available_languages.append(lang_dir)

        logging.info(f"Available languages: {available_languages}")

        # If no languages are available, try to compile .po files if they exist
        if not available_languages:
            try:
                compile_translations()
                # Recheck available languages
                for lang_dir in os.listdir(locale_dir):
                    if os.path.isdir(os.path.join(locale_dir, lang_dir)):
                        mo_path = os.path.join(locale_dir, lang_dir, 'LC_MESSAGES', 'pixelflasher.mo')
                        po_path = os.path.join(locale_dir, lang_dir, 'LC_MESSAGES', 'pixelflasher.po')
                        if os.path.exists(mo_path) or os.path.exists(po_path):
                            available_languages.append(lang_dir)
            except Exception as e:
                logging.warning(f"Failed to compile translations: {e}")

        # Set up translations for available languages
        for lang in available_languages:
            try:
                # Use fallback=True to prevent FileNotFoundError
                translations[lang] = gettext.translation('pixelflasher', localedir=locale_dir, languages=[lang], fallback=True)
                logging.info(f"Loaded translation for {lang}")
            except Exception as e:
                logging.warning(f"Error loading translation for {lang}: {e}")

        # Always ensure we have a fallback translation
        if not translations or fallback_language not in translations:
            # Create empty translations directory structure if it doesn't exist
            lc_messages_dir = os.path.join(locale_dir, fallback_language, 'LC_MESSAGES')
            os.makedirs(lc_messages_dir, exist_ok=True)

            # If fallback language is not available, set up a NullTranslations
            translations[fallback_language] = gettext.NullTranslations()
            logging.info(f"Using NullTranslations for {fallback_language}")

        # Try to get the system language, but fall back if necessary
        system_lang = get_system_language()

        # if current language is not already set, Set current language to system language if available, otherwise fallback
        if current_language is None or current_language == '' or current_language not in translations:
            if system_lang in translations:
                current_language = system_lang
            else:
                current_language = fallback_language
                logging.info(f"System language {system_lang} not available, using {fallback_language}")

        # Install the translate function
        builtins.__dict__['_'] = translate_text

        logging.info(f"Translation system initialized to language: {current_language}")

    except Exception as e:
        # Last resort if anything goes wrong during setup
        logging.error(f"Translation setup failed: {e}")
        # Ensure we have a working translation function
        builtins.__dict__['_'] = lambda s: s

# ============================================================================
#                               Function compile_translations
# ============================================================================
def compile_translations(specific_po_file=None):
    """
    Compile PO files to MO files using polib.

    Args:
        specific_po_file: If provided, only compile this specific PO file.
            Otherwise, compile all PO files in the locale directory.

    Returns:
        bool: True if at least one file was compiled successfully, False otherwise
    """
    locale_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')

    if not os.path.exists(locale_dir):
        logging.warning(f"Locale directory not found: {locale_dir}")
        return False

    # If a specific PO file was provided, compile only that file
    if specific_po_file:
        try:
            if not os.path.exists(specific_po_file):
                logging.error(f"PO file not found: {specific_po_file}")
                return False

            mo_file = os.path.splitext(specific_po_file)[0] + '.mo'

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(mo_file), exist_ok=True)

            # Load and compile the PO file
            po = polib.pofile(specific_po_file)
            po.save_as_mofile(mo_file)
            logging.info(f"Compiled: {specific_po_file} → {mo_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to compile {specific_po_file}: {e}")
            return False

    # Otherwise, compile all PO files in the locale directory
    success_count = 0
    fail_count = 0

    # Walk through all language directories
    for lang in os.listdir(locale_dir):
        lang_dir = os.path.join(locale_dir, lang)
        if os.path.isdir(lang_dir):
            # Look for LC_MESSAGES directory
            lc_messages_dir = os.path.join(lang_dir, 'LC_MESSAGES')
            if os.path.isdir(lc_messages_dir):
                # Process all .po files in LC_MESSAGES
                for filename in os.listdir(lc_messages_dir):
                    if filename.endswith('.po'):
                        po_path = os.path.join(lc_messages_dir, filename)
                        mo_path = os.path.join(lc_messages_dir, os.path.splitext(filename)[0] + '.mo')

                        try:
                            # Load the PO file and compile to MO using polib
                            po = polib.pofile(po_path)
                            po.save_as_mofile(mo_path)
                            success_count += 1
                            logging.info(f"Compiled: {po_path} → {mo_path}")
                        except Exception as e:
                            fail_count += 1
                            logging.error(f"Failed to compile {po_path}: {str(e)}")

    logging.info(f"Compilation complete. Success: {success_count}, Failed: {fail_count}")
    return success_count > 0

# ============================================================================
#                               Function get_available_languages
# ============================================================================
def get_available_languages():
    """Get a list of available language codes."""
    global translations
    return list(translations.keys())

# ============================================================================
#                               Function get_language
# ============================================================================
def get_language():
    global current_language
    # if current_language is not set, try to load it from PixelFlasher.json file
    if current_language is None:
        from runtime import get_config_file_path, init_config_path
        init_config_path()
        config_file = get_config_file_path()
        try:
            with open(config_file, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                current_language = data.get('language')
                logging.info(f"Got language {current_language} from PixelFlasher.json")
                set_language(current_language)
        except Exception as e:
            logging.warning(f"Failed to load language from PixelFlasher.json: {e}, defaulting to English.")
            set_language('en')
    return current_language

# ============================================================================
#                               Function set_language
# ============================================================================
def set_language(lang_code):
    """Set the current language for translations.

    Args:
        lang_code: The language code to use (e.g., 'en', 'fr')

    Returns:
        bool: True if language was set successfully, False otherwise
    """
    global current_language, translations

    # No change needed if already using this language
    if lang_code == current_language:
        return True

    # If language is already loaded, just switch to it
    if lang_code in translations:
        current_language = lang_code
        logging.info(f"Changed language to {lang_code}")
        return True

    # Try to load the requested language
    try:
        locale_dir = find_locale_dir()
        translation = None

        # First try loading the exact language code
        try:
            translation = gettext.translation('pixelflasher', localedir=locale_dir, languages=[lang_code])
        except FileNotFoundError:
            # If the language has a region suffix (e.g., 'pt_BR'), try the base language ('pt')
            if '_' in lang_code:
                base_lang = lang_code.split('_')[0]
                try:
                    translation = gettext.translation('pixelflasher', localedir=locale_dir, languages=[base_lang])
                    logging.info(f"Using base language {base_lang} instead of {lang_code}")
                    lang_code = base_lang  # Update lang_code to what was actually loaded
                except FileNotFoundError:
                    pass

        # If still no translation found, try to compile from .po file
        if translation is None:
            # Check for a .po file we could compile
            po_path = os.path.join(locale_dir, lang_code, 'LC_MESSAGES', 'pixelflasher.po')
            if os.path.exists(po_path):
                try:
                    # Compile the .po file to .mo and try loading again
                    if compile_translations(po_path):
                        translation = gettext.translation('pixelflasher', localedir=locale_dir, languages=[lang_code])
                except Exception as e:
                    logging.error(f"Failed to compile and load translation for {lang_code}: {e}")

        # If translation was loaded successfully, store it
        if translation:
            translations[lang_code] = translation
            current_language = lang_code
            logging.info(f"Changed language to {lang_code}")
            return True

        # If we get here, we couldn't load the translation
        logging.warning(f"Language {lang_code} not available, falling back to {fallback_language}")

        # Ensure we have a fallback translation if none was loaded
        if fallback_language not in translations:
            translations[fallback_language] = gettext.NullTranslations()

        current_language = fallback_language
        return False

    except Exception as e:
        logging.error(f"Error setting language to {lang_code}: {e}")

        # Ensure we have a fallback translation if none was loaded
        if fallback_language not in translations:
            translations[fallback_language] = gettext.NullTranslations()

        current_language = fallback_language
        return False

# ============================================================================
#                               Function initialize_translations
# ============================================================================
def initialize_translations():
    """Initialize translations for the application."""
    logging.info("Initializing translation system")
    setup_i18n()
    # Verify that the '_' function is properly installed
    if '_' not in builtins.__dict__:
        logging.warning("Translation function not properly installed, using dummy")
        builtins.__dict__['_'] = lambda s: s
    logging.info("Translation initialization complete")
