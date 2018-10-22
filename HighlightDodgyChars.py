#!/usr/bin/python
# -*- coding: utf-8 -*-
import sublime, sublime_plugin

class HighlightDodgyChars(sublime_plugin.EventListener):
    def on_activated(self, view):
        self.get_settings()
        self.view = view
        self.has_been_modified = False
        self.delay_update = False

        self.phantom_set = sublime.PhantomSet(view)
        # highlight dodgy characters when the file is opened
        self.highlight(view)

    def get_settings(self):
        settings = sublime.load_settings('HighlightDodgyChars.sublime-settings')

        self.whitelist = settings.get('whitelist_chars')

        if isinstance(self.whitelist, list):
            self.whitelist = ''.join(self.whitelist)

        if self.whitelist is None:
            self.whitelist = ''

        # for some reason the sublime.IGNORECASE -flag did not work so lets
        # duplicate the chars as lower and upper :(
        self.whitelist += self.whitelist.upper()

    def on_modified_async(self, view):
        # call highlight max 4 times a second
        if self.delay_update:
            # if a modification happens during cooldown, an update is needed afterwards
            self.has_been_modified = True
        else:
            self.highlight(view)
            # 250 ms cooldown
            self.delay_update = True
            sublime.set_timeout(lambda: self.end_cooldown(view), 250)

    def on_load_async(self, view):
        self.highlight(view)

    def on_selection_modified_async(self, view):
        # call highlight max 4 times a second
        if self.delay_update:
            # if a modification happens during cooldown, an update is needed afterwards
            self.has_been_modified = True
        else:
            self.highlight(view)
            # 250 ms cooldown
            self.delay_update = True
            sublime.set_timeout(lambda: self.end_cooldown(view), 250)

    def end_cooldown(self, view):
        self.delay_update = False;
        if self.has_been_modified:
            self.has_been_modified = False;
            self.highlight(view)

    def highlight(self, view):
        highlights = []
        phantoms = []
        # allow newline, forward-tick and tabulator
        default_whitelist = u'\n´\u0009'
        # search for non-ascii characters that are not on the whitelist
        needle = '[^\x00-\x7F' + default_whitelist + self.whitelist + ']'

        # search the view
        for pos in self.find_regions(view, needle):
            highlights.append(pos)
            phantoms.append(sublime.Phantom(pos, '<span style="color: var(--background); background-color: var(--pinkish); border-radius: 3px;">!</span>', sublime.LAYOUT_INLINE))

        if highlights:
            view.add_regions('zero-width-and-bad-chars', highlights, 'invalid', 'dot', sublime.DRAW_EMPTY)
        else:
            view.erase_regions('zero-width-and-bad-chars')

        # if something dodgy was found, highlight the dodgy parts
        self.phantom_set.update(phantoms);


    def find_regions(self, view, search):
        limit_chars = 50000

        regions = []
        if not limit_chars:
            regions += view.find_all(search, Pref.case_sensitive)
        else:
            chars = limit_chars
            visible_region = view.visible_region()
            begin = 0 if visible_region.begin() - chars < 0 else visible_region.begin() - chars
            end = visible_region.end() + chars
            from_point = begin
            while True:
                region = view.find(search, from_point)
                if region:
                    regions.append(region)
                    if region.end() > end:
                        break
                    else:
                        from_point = region.end()
                else:
                    break
        return regions
