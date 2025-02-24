from pathlib import Path
from re import match, sub, IGNORECASE
from typing import Any

from modules.CleanPath import CleanPath
from modules.Debug import log
import modules.global_objects as global_objects

# Built-in CardType classes
from modules.AnimeTitleCard import AnimeTitleCard
from modules.CutoutTitleCard import CutoutTitleCard
from modules.FrameTitleCard import FrameTitleCard
from modules.LandscapeTitleCard import LandscapeTitleCard
from modules.LogoTitleCard import LogoTitleCard
from modules.OlivierTitleCard import OlivierTitleCard
from modules.PosterTitleCard import PosterTitleCard
from modules.RomanNumeralTitleCard import RomanNumeralTitleCard
from modules.StandardTitleCard import StandardTitleCard
from modules.StarWarsTitleCard import StarWarsTitleCard
from modules.TextlessTitleCard import TextlessTitleCard

class TitleCard:
    """
    This class describes a title card. This class is responsible for applying a
    given profile to the Episode details and initializing a CardType with those
    attributes.

    It also contains the mapping of card type identifier strings to their
    respective CardType classes.
    """

    """Extension of the input source image"""
    INPUT_CARD_EXTENSION = '.jpg'

    """Default extension of the output title card"""
    DEFAULT_CARD_EXTENSION = '.jpg'

    """Default filename format for all title cards"""
    DEFAULT_FILENAME_FORMAT = '{full_name} - S{season:02}E{episode:02}'

    """Mapping of card type identifiers to CardType classes"""
    DEFAULT_CARD_TYPE = 'standard'
    CARD_TYPES = {
        'anime': AnimeTitleCard,
        'cutout': CutoutTitleCard,
        'frame': FrameTitleCard,
        'generic': StandardTitleCard,
        'gundam': PosterTitleCard,
        'ishalioh': OlivierTitleCard,
        'landscape': LandscapeTitleCard,
        'logo': LogoTitleCard,
        'olivier': OlivierTitleCard,
        'phendrena': CutoutTitleCard,
        'photo': FrameTitleCard,
        'polymath': StandardTitleCard,
        'poster': PosterTitleCard,
        'reality tv': LogoTitleCard,
        'roman': RomanNumeralTitleCard,
        'roman numeral': RomanNumeralTitleCard,
        'standard': StandardTitleCard,
        'star wars': StarWarsTitleCard,
        'textless': TextlessTitleCard,
    }

    __slots__ = ('episode', 'profile', 'converted_title', 'maker', 'file')
    

    def __init__(self, episode: 'Episode', profile: 'Profile',
                 title_characteristics: dict[str, Any],
                 **extra_characteristics: dict[str, Any]) -> None:
        """
        Constructs a new instance of this class.
        
        Args:
            episode: The episode whose TitleCard this corresponds to.
            profile: The profile to apply to the creation of this title card.
            title_characteristics: Dictionary of characteristics from the
                CardType class for this Episode to pass to Title.apply_profile()
            extra_characteristics: Any extra keyword arguments to pass directly
                to the creation of the CardType object.
        """

        # Store this card's associated episode and profile
        self.episode = episode
        self.profile = profile

        # Apply the given profile to the Title
        self.converted_title = episode.episode_info.title.apply_profile(
            profile, **title_characteristics
        )   
        
        # Initialize this episode's CardType instance
        args = {
            'source': episode.source,
            'output_file': episode.destination,
            'title': self.converted_title,
            'season_text': profile.get_season_text(self.episode.episode_info),
            'episode_text': profile.get_episode_text(self.episode),
            'hide_season': profile.hide_season_title,
            'blur': episode.blur,
            'watched': episode.watched,
            'grayscale': episode.grayscale,
        } | profile.font.get_attributes() \
          | self.episode.episode_info.indices \
          | extra_characteristics
        self.maker = self.episode.card_class(**args)
        
        # File associated with this card is the episode's destination
        self.file = episode.destination

        
    @staticmethod
    def get_output_filename(format_string: str, series_info: 'SeriesInfo', 
                            episode_info: 'EpisodeInfo',
                            media_directory: Path) -> Path:
        """
        Get the output filename for a title card described by the given values.
        
        Args:
            format_string: Format string that specifies how to construct the
                filename.
            series_info: SeriesInfo for this entry.
            episode_info: EpisodeInfo to get filename of.
            media_directory: Top-level media directory.
        
        Returns:
            Path for the full title card destination.
        """
        
        # Get the season folder for this entry's season
        season_folder = global_objects.pp.get_season_folder(
            episode_info.season_number
        )
        
        # Get filename from the given format string, with illegals removed
        abs_number = episode_info.abs_number
        filename = CleanPath.sanitize_name(
            format_string.format(
                name=series_info.name,
                full_name=series_info.full_name,
                year=series_info.year,
                title=episode_info.title.full_title,
                season=episode_info.season_number,
                episode=episode_info.episode_number,
                abs_number=abs_number if abs_number is not None else 0,
            )
        )
        
        # Add card extension
        filename += global_objects.pp.card_extension
        
        return media_directory / season_folder / filename


    @staticmethod
    def get_multi_output_filename(format_string: str, series_info: 'SeriesInfo',
                                  multi_episode: 'MultiEpisode',
                                  media_directory: Path) -> Path:
        """
        Get the output filename for a title card described by the given values,
        and that represents a range of Episodes (not just one).
        
        Args:
            format_string: Format string that specifies how to construct the
                filename.
            series_info: Series info for this entry.
            multi_episode: MultiEpisode object to get filename of.
            media_directory: Top-level media directory.

        Returns:
            Path to the full title card destination.
        """

        # If there is an episode key to modify, do so
        if '{episode' in format_string:
            # Replace existing episode number reference with episode start number
            mod_format_string=format_string.replace('{episode','{episode_start')

            # Episode number formatting with prefix
            episode_text = match(
                r'.*?(e?{episode_start.*?})', mod_format_string, IGNORECASE
            ).group(1)

            # Duplicate episode text format for end text format
            end_episode_text=episode_text.replace('episode_start','episode_end')

            # Range of episode numbers
            range_text = f'{episode_text}-{end_episode_text}'

            # Completely modified format string with keys for start/end episodes
            modified_format_string = sub(r'e?{episode_start.*?}', range_text,
                                         mod_format_string, flags=IGNORECASE)
        else:
            # No episode key to modify, format the original string
            modified_format_string = format_string

        # # Get the season folder for these episodes
        season_folder = global_objects.pp.get_season_folder(
            multi_episode.season_number
        )

        # Get filename from the modified format string
        abs_number = multi_episode.episode_info.abs_number
        filename = CleanPath.sanitize_name(
            modified_format_string.format(
                name=series_info.name,
                full_name=series_info.full_name,
                year=series_info.year,
                title=multi_episode.episode_info.title.full_title,
                season=multi_episode.season_number,
                episode_start=multi_episode.episode_start,
                episode_end=multi_episode.episode_end,
                abs_number=abs_number if abs_number is not None else 0,
            )
        )

        # Add card extension
        filename += global_objects.pp.card_extension
        
        return media_directory / season_folder / filename


    @staticmethod
    def validate_card_format_string(format_string: str) -> bool:
        """
        Return whether the given card filename format string is valid or not.
        
        Args:
            format_string:  Format string being validated.
        
        Returns:
            True if the given string can be formatted, False otherwise.
        """
        
        try:
            # Attempt to format using all the standard keys
            format_string.format(
                name='TestName', full_name='TestName (2000)', year=2000,
                season=1, episode=1, title='Episode Title', abs_number=1,
            )
            return True
        except Exception as e:
            # Invalid format string, log
            log.error(f'Card format string is invalid - "{e}"')
            return False


    def create(self) -> bool:
        """
        Create this title card. If the card already exists, a new one is not 
        created. Return whether a card was created.

        Returns:
            True if a title card was created, False otherwise.
        """

        # If the card already exists, exit
        if self.file.exists():
            return False

        # If card is invalid, exit
        if not self.maker.valid:
            return False

        # Create parent folders if necessary for this card
        self.file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create card
        self.maker.create()
        
        # Return whether card creation was successful or not
        if self.file.exists():
            log.debug(f'Created card "{self.file.resolve()}"')
            return True

        # Card doesn't exist, log commands to debug
        log.debug(f'Could not create card "{self.file.resolve()}"')
        self.maker.image_magick.print_command_history()
        
        return False