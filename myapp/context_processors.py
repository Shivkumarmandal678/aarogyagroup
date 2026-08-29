from django.conf import settings


def public_site(request):
    public_url = getattr(settings, 'PUBLIC_SITE_URL', 'https://aarogyagroup.com.np').rstrip('/')
    return {
        'PUBLIC_SITE_URL': public_url,
        'PUBLIC_SITE_URL_WITH_PATH': f"{public_url}{request.path}",
    }
