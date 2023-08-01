from urllib.parse import urlparse


def extract_domain_from_url(url: str) -> str:
    """
    This function return only the domain from the given url
    :param url:
    :return:


    >>> url = 'https://www.theguardian.com/environment/2023/jul/31/art-can-move-us-powerfully-towards-civic-activism-on-climate'
    >>> extract_domain_from_url(url)
    'theguardian'

    >>> url = "http://sample.info/?insect=fireman&porter=attraction#cave"
    >>> extract_domain_from_url(url)
    'sample'

    >>> url = "https://www.google.com"
    >>> extract_domain_from_url(url)
    'google'

    >>> url = "http://www.auer.net/et-dolores-placeat-deserunt-qui-voluptatibus-ratione-officiis"
    >>> extract_domain_from_url(url)
    'auer'

    >>> url = "http://www.larson.com/"
    >>> extract_domain_from_url(url)
    'larson'

    >>> url = "http://www.quigley.org/"
    >>> extract_domain_from_url(url)
    'quigley'

    >>> url = "https://mclennan.libguides.com/issues/popular_issues"
    >>> extract_domain_from_url(url)
    'mclennan'

    """
    # Use urlparse to extract the domain with path
    parsed_url = urlparse(url)
    domain_with_path = parsed_url.netloc

    # Extract the domain from the netloc (and remove www. if present)
    if domain_with_path.startswith('www.'):
        domain_with_path = domain_with_path[4:]

    # Split the domain_with_path to get only the domain
    domain = domain_with_path.split('/')[0]

    # Remove any extra parts after the base domain (e.g., .com, .co.uk, etc.)
    domain = domain.split('.')[0]

    return domain


if __name__ == '__main__':
    import doctest

    (failures, tests) = doctest.testmod(report=True, optionflags=doctest.FAIL_FAST)
    print("{} failures, {} tests".format(failures, tests))
