"""EventBlockView browser view.

Renders the ``eventMetadata`` block from volto-light-theme: a metadata panel for
an Event content type showing start/end dates, location, website and contact
details plus an ICS download link. Unlike most blocks it carries no own data --
it reflects the *context's* event fields, read through ``IEventAccessor`` (the
same normalised accessor plone.app.event uses), so it renders nothing on
non-event content.

Dates follow the Volto view: whole-day events show the date only, timed events
show date and time, and the end is hidden for open-ended events.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.event.interfaces import IEventAccessor


class EventBlockView(BaseBlockView):
    """Render an event's metadata for the eventMetadata block."""

    @property
    def accessor(self):
        return IEventAccessor(self.context, None)

    @property
    def available(self):
        acc = self.accessor
        return acc is not None and acc.start is not None

    @property
    def whole_day(self):
        return bool(getattr(self.accessor, "whole_day", False))

    @property
    def open_end(self):
        acc = self.accessor
        return acc.end is None or bool(getattr(acc, "open_end", False))

    def _format(self, value):
        if value is None:
            return ""
        plone_view = self.context.restrictedTraverse("@@plone")
        # Whole-day events drop the time component; timed events keep it.
        return plone_view.toLocalizedTime(value, long_format=not self.whole_day)

    @property
    def start(self):
        return self._format(self.accessor.start)

    @property
    def end(self):
        return self._format(self.accessor.end)

    @property
    def show_end(self):
        return not self.open_end

    @property
    def location(self):
        return getattr(self.accessor, "location", None) or ""

    @property
    def event_url(self):
        return getattr(self.accessor, "event_url", None) or ""

    @property
    def contact_name(self):
        return getattr(self.accessor, "contact_name", None) or ""

    @property
    def contact_email(self):
        return getattr(self.accessor, "contact_email", None) or ""

    @property
    def contact_phone(self):
        return getattr(self.accessor, "contact_phone", None) or ""

    @property
    def has_contact(self):
        return bool(self.contact_name or self.contact_email or self.contact_phone)

    @property
    def ics_url(self):
        return f"{self.context.absolute_url()}/ics_view"

    def __call__(self):
        if not self.available:
            return ""
        return self.index()
