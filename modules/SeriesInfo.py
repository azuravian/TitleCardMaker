from re import match

class SeriesInfo:
    """
    This class encapsulates information that is tied to a single Series.
    """

    """After how many characters to truncate the short name"""
    SHORT_WIDTH = 15

    def __init__(self, name: str, year: int) -> None:
        """
        Constructs a new instance.
        
        :param      name:  The name of the series.
        :param      year:  The air year of the series.
        """

        # Set base attributes
        self.name = str(name)
        self.year = int(year)

        # Set short name
        if len(self.name) > self.SHORT_WIDTH:
            self.short_name = f'{self.name[:self.SHORT_WIDTH]}..'
        else:
            self.short_name = self.name

        # Set full and match name
        self.full_name = f'{name} ({year})'
        self.match_name = self.get_matching_title(self.name)

        # Optional attributes
        self.sonarr_id = None
        self.tvdb_id = None
        self.tmdb_id = None


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return self.full_name


    def __repr__(self) -> str:
        """Returns a unambiguous string representation of the object."""

        return (f'<SeriesInfo name={self.name}, year={self.year}, sonarr_id='
                f'{self.sonarr_id}, tvdb_id={self.tvdb_id}, tmdb_id='
                f'{self.tmdb_id}>')


    def update_name(self, name: str) -> None:
        """
        Update the name for this SeriesInfo.
        
        :param      name:  The new name of the series info.
        """

        self.name = name
        self.full_name = f'{name} ({self.year})'


    def set_sonarr_id(self, sonarr_id: int) -> None:
        """
        Set the Sonarr ID for this series.
        
        :param      sonarr_id:  The Sonarr ID used for this series.
        """
        
        self.sonarr_id = int(sonarr_id)


    def set_tvdb_id(self, tvdb_id: int) -> None:
        """
        Set the TVDb ID for this series.
        
        :param      tvdb_id:  The TVDb ID for this series.
        """

        self.tvdb_id = int(tvdb_id)


    def set_tmdb_id(self, tmdb_id: int) -> None:
        """
        Set the TMDb ID for this series.
        
        :param      tmdb_id:    The TMDb ID for this series.
        """

        self.tmdb_id = int(tmdb_id)


    @staticmethod
    def get_matching_title(text: str) -> str:
        """
        Remove all non A-Z characters from the given title.
        
        :param      text:   The title to strip of special characters.
        
        :returns:   The input `text` with all non A-Z characters removed.
        """

        return ''.join(filter(lambda c: match('[a-zA-Z0-9]', c), text)).lower()


    def matches(self, *names: tuple) -> bool:
        """
        Get whether any of the given names match this Series.
        
        :param      names:  The names to check
        
        :returns:   True if any of the given names match this series, False
                    otherwise.
        """

        matching_names = map(self.get_matching_title, names)

        return any(name == self.match_name for name in matching_names)
        