from abc import abstractmethod
from typing import Any

from titlecase import titlecase

from modules.Debug import log
from modules.ImageMaker import ImageMaker

class BaseCardType(ImageMaker):
    """
    This class describes an abstract card type. A BaseCardType is a subclass of
    ImageMaker, because all CardTypes are designed to create title cards. This
    class outlines the requirements for creating a custom type of title card.

    All implementations of BaseCardType must implement this class's abstract
    properties and methods in order to work with the TitleCardMaker. However,
    not all CardTypes need to use every argument of these methods. For example,
    the StandardTitleCard utilizes most all customizations for a title card,
    while a StarWarsTitleCard hardly uses anything.
    """

    """Default case string for all title text"""
    DEFAULT_FONT_CASE = 'upper'

    """Mapping of 'case' strings to format functions"""
    CASE_FUNCTIONS = {
        'blank': lambda _: '',
        'lower': str.lower,
        'source': str,
        'title': titlecase,
        'upper': str.upper,
    }

    """Default episode text format string, can be overwritten by each class"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'

    """Whether this class uses unique source images for card creation"""
    USES_UNIQUE_SOURCES = True

    """Standard size for all title cards"""
    TITLE_CARD_SIZE = '3200x1800'

    """Standard blur effect to apply to spoiler-free images"""
    BLUR_PROFILE = '0x60'

    @property
    @abstractmethod
    def TITLE_CHARACTERISTICS(self) -> dict:
        """
        Characteristics of title splitting for this card type. Must have keys
        for max_line_width, max_line_count, and top_heavy. See `Title` class
        for details.
        """
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def ARCHIVE_NAME(self) -> str:
        """How to name archive directories for this type of card"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def TITLE_FONT(self) -> str:
        """
        Standard font (full path or ImageMagick recognized font name) to use for
        the episode title text
        """
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def TITLE_COLOR(self) -> str:
        """Standard color to use for the episode title text"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def FONT_REPLACEMENTS(self) -> dict:
        """Standard font replacements for the episode title font"""
        raise NotImplementedError(f'All CardType objects must implement this')

    @property
    @abstractmethod
    def USES_SEASON_TITLE(self) -> bool:
        """Whether this class uses season titles for the purpose of archives"""
        raise NotImplementedError(f'All CardType objects must implement this')


    """Slots for standard style attributes"""
    __slots__ = ('valid', 'blur', 'grayscale')


    @abstractmethod
    def __init__(self, blur: bool=False, grayscale: bool=False) -> None:
        """
        Construct a new CardType. Must call super().__init__() to initialize the
        parent ImageMaker class (for PreferenceParser and ImageMagickInterface
        objects).

        Args:
            blur: Whether to blur the source image. Defaults to False.
            grayscale: Whether to convert the source image to grayscale.
                Defaults to False.
        """
        
        # Initialize parent ImageMaker
        super().__init__()

        # Object starts as valid
        self.valid = True

        # Store style attributes
        self.blur = blur
        self.grayscale = grayscale

    
    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)!r}'
                               for attr in self.__slots__
                               if not attr.startswith('__'))

        return (f'<{self.__class__.__name__} {attributes}>')


    @staticmethod
    def modify_extras(extras: dict[str, Any], custom_font: bool,
                      custom_season_titles: bool) -> None:
        """
        Modify the given extras base on whether font or season titles are
        custom. The default behavior is to not modify the extras at all.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        pass
        

    @staticmethod
    @abstractmethod
    def is_custom_font() -> bool:
        """
        Abstract method to determine whether the given font characteristics
        indicate the use of a custom font or not.
        
        Returns:
            True if a custom font is indicated, False otherwise.
        """
        raise NotImplementedError(f'All CardType objects must implement this')


    @staticmethod
    @abstractmethod
    def is_custom_season_titles() -> bool:
        """
        Abstract method to determine whether the given season characteristics
        indicate the use of a custom season title or not.
        
        Returns:
            True if a custom season title is indicated, False otherwise.
        """
        raise NotImplementedError(f'All CardType objects must implement this')

    
    @property
    def resize_and_style(self) -> list[str]:
        """
        ImageMagick commands to resize and apply any style modifiers to an image
        
        Returns:
            List of ImageMagick commands.
        """

        return [
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Background resize shouldn't fill with any color
            f'-background transparent',
            f'-gravity center',
            # Fit to title card size
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB',
        ]


    @property
    def style(self) -> list[str]:
        """
        ImageMagick commands to apply any style modifiers to an image.

        Returns:
            List of ImageMagick commands.
        """

        return [
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB' if self.grayscale else '',
        ]


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method to create the title card outlined by the CardType. All
        implementations of this method should delete any intermediate files.
        """
        raise NotImplementedError(f'All CardType objects must implement this')