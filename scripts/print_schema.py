#!/usr/bin/env python3
import argparse

from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph


def plot_schema(fn):
    graph = create_schema_graph(
        metadata=MetaData('sqlite:///'+fn),
        show_datatypes=False,
        show_indexes=False,
        rankdir='LR',
        concentrate=False
    )
    graph.write_pdf('schema.pdf')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Schema plotter')
    parser.add_argument('db', help='DB to plot')
    args = parser.parse_args()
    plot_schema(args.db)
