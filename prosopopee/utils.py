import sys
import base64

from subprocess import check_output

from path import Path

from jinja2 import Environment, FileSystemLoader, contextfilter

from builtins import str

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def error(test, error_message):
    if test:
        return

    sys.stderr.write(bcolors.FAIL + "Abort: " + bcolors.ENDC + error_message)
    sys.stderr.write("\n")
    sys.exit(1)


def warning(logging, warning_message):
    sys.stderr.write("%s%s: %s%s" % (bcolors.WARNING, logging, bcolors.ENDC, warning_message))
    sys.stderr.write("\n")


def okgreen(logging, ok_message):
    sys.stderr.write("%s%s: %s%s" % (bcolors.OKGREEN, logging, bcolors.ENDC, ok_message))
    sys.stderr.write("\n")

def makeform(template, settings, gallery_settings):
    from_template = template.get_template("form.html")
    form = base64.b64encode(from_template.render(settings=settings, gallery=gallery_settings).encode("Utf-8"))
    return str(form, 'utf-8')

def encrypt(password, template, gallery_path, settings, gallery_settings):
    encrypted_template = template.get_template("encrypted.html")
    index_plain = Path("build").joinpath(gallery_path, "index.html")
    encrypted = check_output('cat %s | openssl enc -e -base64 -A -aes-256-cbc -md md5 -pass pass:"%s"' % (index_plain, password), shell=True)
    html = encrypted_template.render(
        settings=settings,
        form=makeform(template, settings, gallery_settings),
        ciphertext=str(encrypted, 'utf-8'),
        gallery=gallery_settings,
    ).encode("Utf-8")
    return html


@contextfilter
def render_text(context, value):
    """ Renders text, using the propper renderer

    The render choice is up to the user ; could be defined via the
    `text_renderer` yaml setting, that could be specified at global, gallery,
    or section level.

    Possible settings are `markdown` or `html` (default).
    """
    renderers_map = {
        'markdown': markdown_renderer,
        'html': raw_html_renderer,
    }

    for renderer_name in (
            context['settings'].get('text_renderer', None),
            context['gallery'].get('text_renderer', None),
            context['section'].get('text_renderer', None),
            'html',
    ):
        if renderer_name is not None:
            try:
                renderer_func = renderers_map[renderer_name]
                break
            except KeyError:
                error(
                    'Unknown renderer : "{}" (allowed renderers are {})',format(
                        renderer_name,
                        ', '.join(renderers_map.keys())
                    )
                )
    return renderer_func(value)


def raw_html_renderer(text):
    return text

def markdown_renderer(text):
    try:
        import markdown as md
    except ImportError:
        error("Cannot load the markdown library.")
        raise TemplateError("Cannot load the markdown library")
    marked = md.Markdown()

    return marked.convert(text)
