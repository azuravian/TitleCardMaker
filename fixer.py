from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from dataclasses import dataclass
from pathlib import Path

try:
    from yaml import dump

    from modules.Debug import log
    from modules.DataFileInterface import DataFileInterface
    from modules.PreferenceParser import PreferenceParser
    from modules.preferences import set_preference_parser
    from modules.ShowSummary import ShowSummary
    from modules.SonarrInterface import SonarrInterface
    from modules.TMDbInterface import TMDbInterface
except ImportError:
    print(f'Required Python packages are missing - execute "pipenv install"')
    exit(1)

# Create ArgumentParser object 
parser = ArgumentParser(description='Manual fixes for the TitleCardMaker')
parser.add_argument('-p', '--preference-file', type=Path, 
                    default='preferences.yml', metavar='PREFERENCE_FILE',
                    help='Preference YAML file for parsing '
                         'ImageMagick/Sonarr/TMDb options')

    type=str,
    nargs=2,
    default=SUPPRESS,
# Argument group for Miscelanneous functions
misc_group = parser.add_argument_group('Miscellaneous')
misc_group.add_argument(
    nargs=2,
    default=SUPPRESS,
misc_group.add_argument(
    '--delete-cards',
    nargs='+',
    default=[],
    metavar='DIRECTORY',
    help='Delete all images with the specified directory(ies)')
misc_group.add_argument(
    '--delete-extension',
    type=str,
    default='.jpg',
    metavar='EXTENSION',
    help='Extension of images to delete with --delete-cards')

# Argument group for Sonarr
sonarr_group = parser.add_argument_group('Sonarr')
sonarr_group.add_argument(
    '--read-all-series',
    type=Path,
    default=SUPPRESS,
    metavar='FILE',
    help='Create a generic series YAML file for all the series in Sonarr')
sonarr_group.add_argument(
    '--sonarr-list-ids',
    action='store_true',
    help="List all the ID's for all shows within Sonarr")

# Argument group for TMDb
tmdb_group = parser.add_argument_group(
    'TheMovieDatabase',
    'Fixes for how the Maker interacts with TheMovieDatabase')
tmdb_group.add_argument(
    '--tmdb-download-images',
    nargs=5,
    default=SUPPRESS,
    action='append',
    metavar=('TITLE', 'YEAR', 'SEASON', 'EPISODES', 'DIRECTORY'),
    help='Download the title card source images for the given season of the '
         'given series')
tmdb_group.add_argument(
    '--delete-blacklist',
    action='store_true',
    help='Delete the existing TMDb blacklist file')
tmdb_group.add_argument(
    '--add-translation',
    nargs=5,
    default=SUPPRESS,
    metavar=('TITLE', 'YEAR', 'DATAFILE', 'LANGUAGE_CODE', 'LABEL'),
    help='Add title translations from TMDb to the given datafile')

# Parse given arguments
args, unknown = parser.parse_known_args()

# Parse preference file for options that might need it
pp = PreferenceParser(args.preference_file)
if not pp.valid:
    exit(1)
set_preference_parser(pp)

# Execute Miscellaneous options
    # Temporary classes
    @dataclass
    class Episode:
        destination: Path
for directory in args.delete_cards:
    # Get all images in this directory
    directory = Path(directory)
    images = tuple(directory.glob(f'**/*{args.delete_extension}'))

    # If no images to delete, skip
    if len(images) == 0:
        log.info(f'No images to delete from "{directory.resolve()}"')
        continue

    # Ask user to confirm deletion
    log.warning(f'Deleting {len(images)} images from "{directory.resolve()}"')
    confirmation = input(f'  Continue [Y/N]?  ')
    if confirmation in ('y', 'Y', 'yes', 'YES'):
        # Delete each image returned by glob
        for image in images:
            image.unlink()
            log.debug(f'Deleted {image.resolve()}')

# Execute Sonarr related options
if hasattr(args, 'read_all_series'):
    # Create SonarrInterface
    si = SonarrInterface(pp.sonarr_url, pp.sonarr_api_key)

    # Create YAML
    yaml = {'libraries': {}, 'series': {}}
    for series_info, media_directory in si.get_all_series():
        # Add library section
        library = {'path': str(media_directory.parent.resolve())}
        yaml['libraries'][media_directory.parent.name] = library

        # Get series key for this series
        if series_info.name in yaml.get('series', {}):
            if series_info.full_name in yaml.get('series', {}):
                key = f'{series_info.name} ({series_info.tvdb_id})'
            else:
                key = series_info.full_name
        else:
            key = series_info.name

        # Create YAML entry for this series
        yaml['series'][key] = {
            'year': series_info.year,
            'library': media_directory.parent.name,
            'media_directory': str(media_directory.resolve()),
        }

    # Write YAML to the specified file
    with args.read_all_series.open('w', encoding='utf-8') as file_handle:
        dump(yaml, file_handle, allow_unicode=True)

    log.info(f'\nWrote {len(yaml["series"])} series to '
             f'{args.read_all_series.resolve()}')

if args.sonarr_list_ids:
    if not pp.use_sonarr:
        log.critical("Cannot list Sonarr ID's if Sonarr is disabled")
    else:
        SonarrInterface(pp.sonarr_url, pp.sonarr_api_key).list_all_series_id()

# Execute TMDB related options
if hasattr(args, 'delete_blacklist'):
    if args.delete_blacklist:
        TMDbInterface.delete_blacklist()

if hasattr(args, 'tmdb_download_images'):
    for arg_set in args.tmdb_download_images:
        TMDbInterface.manually_download_season(
            api_key=pp.tmdb_api_key,
            title=arg_set[0],
            year=int(arg_set[1]),
            season=int(arg_set[2]),
            episode_count=int(arg_set[3]),
            directory=Path(arg_set[4]),
        )

if hasattr(args, 'add_language'):
    dfi = DataFileInterface(Path(args.add_language[2]))
    tmdbi = TMDbInterface(pp.tmdb_api_key)

    for entry in dfi.read():
        if args.add_language[4] in entry:
            continue

        new_title = tmdbi.get_episode_title(
            title=args.add_language[0],
            year=args.add_language[1],
            season=entry['season_number'],
            episode=entry['episode_number'],
            language_code=args.add_language[3],
        )

        if new_title == None:
            continue

        dfi.modify_entry(**entry, **{args.add_language[4]: new_title})

