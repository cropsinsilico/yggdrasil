from yggdrasil.communication.filters.FilterBase import FilterBase


class DirectFilter(FilterBase):
    r"""Class that always passes messages."""

    _filtertype = 'direct'

    def evaluate_filter(self, x):
        r"""Call filter on the provided message.

        Args:
            x (object): Message object to filter.

        Returns:
            bool: True if the message will pass through the filter, False otherwise.

        """
        return True

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the filter class.

        Returns:
            list: Mutiple dictionaries of keywords and messages that will
                pass/fail for those keywords.
        
        """
        return [{'pass': [1, 0]}]
