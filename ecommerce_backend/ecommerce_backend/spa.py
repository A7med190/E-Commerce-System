import os
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.static import serve

DIST_DIR = os.path.join(
    settings.BASE_DIR.parent, 'frontend', 'dist'
)


def _is_safe(path):
    abs_path = os.path.normpath(os.path.join(DIST_DIR, path))
    return abs_path.startswith(os.path.normpath(DIST_DIR))


def spa_asset(request, path):
    full = os.path.join(DIST_DIR, path)
    if not _is_safe(path) or not os.path.isfile(full):
        raise Http404()
    return serve(request, os.path.basename(full), os.path.dirname(full))


def spa_index(request):
    index = os.path.join(DIST_DIR, 'index.html')
    if not os.path.isfile(index):
        return HttpResponse(
            'Frontend not built. Run `npm run build` in the frontend directory.',
            status=501,
        )
    with open(index, 'rb') as f:
        return HttpResponse(f.read(), content_type='text/html')
