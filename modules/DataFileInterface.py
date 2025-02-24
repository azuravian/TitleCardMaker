from pathlib import Path
from typing import Any, Iterable
from yaml import safe_load, dump

from modules.Debug import log
from modules.EpisodeInfo import EpisodeInfo
import modules.global_objects as global_objects
from modules.Title import Title

class DataFileInterface:
    """
    This class is used to interface with a show's data file. And can be used for
    reading from and writing to the files for the purpose of adding new or
    reading existing episode data.
    """

    """Default name for a data file of episode information"""
    GENERIC_DATA_FILE_NAME = 'data.yml'


    def __init__(self, series_info: 'SeriesInfo', data_file: Path) -> None:
        """
        Constructs a new instance of the interface for the specified data file.
        This also creates the parent directories for the data file if they do
        not exist.

        Args:
            data_file: Path to the data file to interface with.
        """
        
        # Store the SeriesInfo and data file
        self.series_info = series_info
        self.file = data_file

        # Create parent directories if necessary
        if not self.file.exists():
            data_file.parent.mkdir(parents=True, exist_ok=True)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (f'<DataFileInterface series_info={self.series_info}, '
                f'file={self.file.resolve()}>')


    def __read_data(self) -> dict[str, dict[float, dict]]:
        """
        Read this interface's data from file. Returns an empty dictionary if the
        file does not exist, is misformatted, or if 'data' key is missing.
        
        Returns:
            Contents under 'data' key of this interface's file.
        """

        # If the file DNE, return empty dictionary
        if not self.file.exists():
            return {}

        # Read file 
        with self.file.open('r', encoding='utf-8') as file_handle:
            try:
                yaml = safe_load(file_handle)
            except Exception as e:
                log.error(f'Error reading datafile:\n{e}\n')
                return {}

        # If the top-level key is not 'data', error and return empty dictionary
        if 'data' not in yaml:
            log.error(f'Datafile "{self.file.resolve()}" missing "data" key')
            return {}

        if not isinstance(yaml['data'], dict):
            log.error(f'Data in "{self.file.resolve()}" is invalid')
            return {}

        return yaml['data']


    def __write_data(self, yaml: dict[str, Any]) -> None:
        """
        Write the given YAML data to this interface's file. This puts all data
        under the 'data' key.

        Args:
            yaml: YAML dictionary to write to file.
        """

        # Write updated data with this entry added
        with self.file.open('w', encoding='utf-8') as file_handle:
            dump({'data': yaml}, file_handle, allow_unicode=True, width=100)


    def read(self) -> tuple[dict[str, Any], set[str]]:
        """
        Read the data file for this object, yielding each valid row.
        
        Returns:
            Yields a dictionary for each entry in this datafile. The dictionary
            has a key 'episode_info' with an EpisodeInfo object, and arbitrary
            keys for all other data found within the entry's YAML.
        """

        # Read yaml, returns {} if empty/DNE
        yaml = self.__read_data()

        # Iterate through each season
        for season, season_data in yaml.items():
            season_number = int(season.rsplit(' ', 1)[-1])

            # Iterate through each episode of this season
            for episode_number, episode_data in season_data.items():
                # If title is missing (or no subkeys at all..) error
                if (not isinstance(episode_data, dict)
                    or ('title' not in episode_data and
                        'preferred_title' not in episode_data)):
                    log.error(f'S{season_number:02}E{episode_number:02} of the '
                              f'{self.series_info} datafile is missing a title')
                    continue

                # Get existing keys for this episode
                given_keys = set(episode_data)

                # If translated title is available, prefer that
                original_title = episode_data.pop('title', None)
                title = episode_data.get('preferred_title', original_title)

                # Ensure Title can be created
                try:
                    title_obj = Title(title, original_title=original_title)
                except Exception:
                    log.error(f'Title for S{season_number:02}E'
                              f'{episode_number:02} of the {self.series_info} '
                              f'datafile is invalid')
                    continue
                
                # Construct EpisodeInfo object for this entry
                episode_info = global_objects.info_set.get_episode_info(
                    self.series_info,
                    title_obj,
                    season_number,
                    episode_number,
                    episode_data.pop('abs_number', None),
                    imdb_id=episode_data.pop('imdb_id', None),
                    tmdb_id=episode_data.pop('tmdb_id', None),
                    tvdb_id=episode_data.pop('tvdb_id', None),
                )

                # Add any additional, unexpected keys from the YAML
                data = {'episode_info': episode_info}
                data.update(episode_data)
                
                yield data, given_keys


    def __info_as_entry(self, episode_info: EpisodeInfo) -> dict[str, Any]:
        """
        Get the given EpisodeInfo object as it's equivalent YAML entry.

        Args:
            episode_info: EpisodeInfo to get the entry of.

        Returns:
            Dictionary to write under episode number key of the given info.
            Possible keys are 'title', and 'abs_number'.
        """

        entry = {'title': episode_info.title.title_yaml}

        if episode_info.abs_number is not None:
            entry['abs_number'] = episode_info.abs_number

        return entry


    def add_data_to_entry(self, episode_info: EpisodeInfo,
                          **new_data: dict[str, Any]) -> None:
        """
        Add any generic data to the YAML entry associated with this EpisodeInfo.
        
        Args:
            episode_info: Episode Info to add to YAML.
            new_data: Generic new data to write.
        """

        yaml = self.__read_data()

        # Verify this entry already exists, warn and exit if not
        season_key = f'Season {episode_info.season_number}'
        if (season_key not in yaml
            or episode_info.episode_number not in yaml[season_key]):
            log.error(f'Cannot add data to entry for {episode_info} in '
                      f'"{self.file.resolve()}" - entry does not exist')
            return None

        # Add new data
        yaml[season_key][episode_info.episode_number].update(new_data)

        # Write updated data
        self.__write_data(yaml)


    def add_many_entries(self, new_episodes: Iterable['EpisodeInfo']) -> None:
        """
        Adds many entries at once. This only reads and writes from this
        interface's file once.

        Args:
            new_episodes: Iterable of EpisodeInfo objects to write.
        """

        # If no new episodes are being added, exit
        if len(new_episodes) == 0:
            return None

        # Read yaml
        yaml = self.__read_data()

        # Go through each episode to possibly add to file
        added = {'count': 0, 'info': None}
        for episode_info in new_episodes:
            # Create blank season data if this key doesn't exist
            season_key = f'Season {episode_info.season_number}'
            if season_key not in yaml:
                yaml[season_key] = {}

            # Construct episode data
            data = self.__info_as_entry(episode_info)

            # Add episode data to existing entry or create new entry for episode
            added = {'count': added['count'] + 1, 'info': episode_info}
            if yaml[season_key].get(episode_info.episode_number) is not None:
                yaml[season_key][episode_info.episode_number].update(data)
            else:
                yaml[season_key][episode_info.episode_number] = data

        # If nothing was added, exit - otherwise log to user
        if (count := added['count']) == 0:
            return None
        elif count > 1:
            log.info(f'Added {count} episodes to "{self.file.parent.name}"')
        else:
            log.info(f'Added {added["info"]} to "{self.file.parent.name}"')

        # Write updated yaml
        self.__write_data(yaml)