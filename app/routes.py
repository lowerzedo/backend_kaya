from flask import Blueprint
from .controllers import (
    test_app_main,
    get_campaigns_main,
    update_campaign_name_main,
    performance_time_series_main,
    compare_performance_main,
)

bp = Blueprint("main", __name__)

bp.route("/test", methods=["GET"])(test_app_main)
bp.route("/campaigns", methods=["GET"])(get_campaigns_main)
# bp.route("/campaign", methods=["POST"])(update_campaign_name_main)
bp.route("/campaign", methods=["PUT"])(update_campaign_name_main)
bp.route("/performance-time-series", methods=["GET"])(performance_time_series_main)
bp.route("/compare-performance", methods=["GET"])(compare_performance_main)
