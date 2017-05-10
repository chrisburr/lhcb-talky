import argparse

from .create_database import build_sample_db, build_production_db


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--sample', action='store_true')

    args = parser.parse_args()
    if args.sample == args.production:
        raise ValueError('Invalid arguments passed')

    if args.production:
        build_production_db()
    elif args.sample:
        build_sample_db()
