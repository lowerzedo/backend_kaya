from .services import (
    test_app,
    get_campaigns,
    update_campaign_name,
    performance_time_series,
    compare_performance,
)

# from .helpers.auth import auth_required


# @auth_required
def test_app_main(**kwargs):
    return test_app(**kwargs)


def get_campaigns_main(**kwargs):
    return get_campaigns(**kwargs)


def update_campaign_name_main(**kwargs):
    return update_campaign_name(**kwargs)


def performance_time_series_main(**kwargs):
    return performance_time_series(**kwargs)


def compare_performance_main(**kwargs):
    return compare_performance(**kwargs)
