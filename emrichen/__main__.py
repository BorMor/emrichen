import argparse
import os
import sys

from .context import Context
from .input import PARSERS
from .output import RENDERERS
from .template import Template


def get_parser():
    parser = argparse.ArgumentParser(
        description='A YAML to YAML preprocessor.',
        prog='emrichen',
        epilog='Variable precedence: -D > -e > -f > !Defaults',
    )
    parser.add_argument(
        'template_file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='The YAML template to process. If unspecified, the template is read from stdin.',
    )

    parser.add_argument(
        '--print-vars',
        dest='action',
        default='render',
        action='store_const',
        const='print_vars',
        help=(
            'Instead of rendering the template, prints the vars used by the template in YAML or '
            'JSON format you can use as a var file.'
        ),
    )
    parser.add_argument(
        '--template-format',
        choices=PARSERS,
        default=None,
        help=(
            'Template format. If unspecified, attempted to be autodetected from the '
            'input filename (but defaults to YAML).'
        ),
    )
    parser.add_argument(
        '--var-file',
        '-f',
        dest='var_files',
        metavar='VAR_FILE',
        type=argparse.FileType('r'),
        action='append',
        default=[],
        help=(
            'A YAML file containing an object whose top-level keys will be defined as variables. '
            'May be specified multiple times.'
        ),
    )
    parser.add_argument(
        '--define',
        '-D',
        metavar='VAR=VALUE',
        action='append',
        default=[],
        help='Defines a single variable. May be specified multiple times.',
    )
    parser.add_argument(
        '--output-file',
        '-o',
        type=argparse.FileType('w'),
        default=sys.stdout,
        help='Output file. If unspecified, the template output is written into stdout.',
    )
    parser.add_argument(
        '--output-format',
        choices=RENDERERS,
        default=None,
        help=(
            'Output format. If unspecified, attempted to be autodetected from the '
            'output filename (but defaults to YAML).'
        ),
    )
    parser.add_argument(
        '--include-env',
        '-e',
        action='store_true',
        default=False,
        help='Expose process environment variables to the template.',
    )
    return parser


def determine_format(filelike, choices, default):
    if hasattr(filelike, 'name'):
        ext = os.path.splitext(filelike.name)[1].lstrip('.').lower()
        if ext in choices:
            return ext
    return default


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(args)

    override_variables = dict(item.split('=', 1) for item in args.define)

    variable_sources = list(args.var_files)
    if args.include_env:
        variable_sources.append(os.environ)

    args.output_format = args.output_format or determine_format(
        args.output_file, RENDERERS, default='yaml'
    )

    args.template_format = args.template_format or determine_format(
        args.template_file, PARSERS, default='yaml'
    )

    context = Context(*variable_sources, **override_variables)
    template = Template.parse(args.template_file, format=args.template_format)

    if args.action == 'render':
        output = template.render(context, format=args.output_format)
    elif args.action == 'print_vars':
        output = template.print_vars(context, format=args.output_format)
    else:
        raise NotImplementedError(args.action)

    args.output_file.write(output)



if __name__ == '__main__':
    main()
