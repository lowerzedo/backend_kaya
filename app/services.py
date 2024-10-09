from app.models.ad_group import AdGroup
from app.models.ad_group_stats import AdGroupStats
from app.models.campaign import Campaign
from app import db
import os
import logging
from flask import jsonify, request
from logging.handlers import RotatingFileHandler
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from datetime import timedelta, datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)


if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure RotatingFileHandler
handler = RotatingFileHandler("logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5)
handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def test_app():
    ad_groups = db.session.execute(select(AdGroup)).scalars().all()

    return [ad_group.serialize() for ad_group in ad_groups]


def get_campaigns(**kwargs):
    """
    Retrieve all campaigns along with their related ad groups and statistics.
    """
    try:
        logger.info("Fetching all Campaigns.")
        campaigns = Campaign.query.all()

        if not campaigns:
            logger.warning("No campaigns found.")
            return jsonify({"message": "No campaigns found."}), 404

        result = []

        for campaign in campaigns:
            logger.info(f"Processing Campaign ID: {campaign.campaign_id}")
            ad_groups = (
                db.session.execute(
                    select(AdGroup).where(AdGroup.campaign_id == campaign.campaign_id)
                )
                .scalars()
                .all()
            )

            ad_group_count = len(ad_groups)
            ad_group_names = [ag.ad_group_name for ag in ad_groups]

            total_cost = 0
            total_conversions = 0
            months = set()

            for ad_group in ad_groups:
                ad_group_stats = (
                    db.session.execute(
                        select(AdGroupStats).where(
                            AdGroupStats.ad_group_id == ad_group.ad_group_id
                        )
                    )
                    .scalars()
                    .all()
                )

                for stat in ad_group_stats:
                    total_cost += stat.cost
                    total_conversions += stat.conversions
                    months.add(stat.date.strftime("%Y-%m"))

            avg_monthly_cost = total_cost / len(months) if months else 0
            avg_cost_per_conversion = (
                total_cost / total_conversions if total_conversions > 0 else 0
            )

            campaign_data = {
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.campaign_name,
                "campaign_type": campaign.campaign_type,
                "ad_group_count": ad_group_count,
                "ad_group_names": ad_group_names,
                "average_monthly_cost": round(avg_monthly_cost, 2),
                "average_cost_per_conversion": round(avg_cost_per_conversion, 2),
            }

            logger.debug(f"Campaign Data: {campaign_data}")
            result.append(campaign_data)

        logger.info(f"Successfully fetched data for {len(result)} campaigns.")
        return jsonify(result), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching campaigns: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error in get_campaigns: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


def update_campaign_name(**kwargs):
    """
    Update the name of a specific campaign.
    """
    try:
        data = request.get_json()
        logger.info("Received request to update campaign name.")

        if not data:
            logger.warning("No JSON payload provided.")
            return jsonify({"message": "No input data provided."}), 400

        campaign_id = data.get("campaign_id")
        new_name = data.get("new_name")

        if not campaign_id or not new_name:
            logger.warning("Missing required fields: campaign_id or new_name.")
            return (
                jsonify(
                    {"message": "Missing required fields: campaign_id and new_name."}
                ),
                400,
            )

        # Check for duplicate campaign names if duplicates are not allowed
        # name_exists = (
        #     db.session.execute(
        #         select(Campaign).where(Campaign.campaign_name == new_name)
        #     )
        #     .scalars()
        #     .first()
        # )
        # if name_exists:
        #     logger.warning(f"Duplicate campaign name attempted: {new_name}")
        #     return (
        #         jsonify(
        #             {
        #                 "message": "Campaign name already exists. Please choose a different name."
        #             }
        #         ),
        #         400,
        #     )

        # Fetch the campaign
        campaign = (
            db.session.execute(
                select(Campaign).where(Campaign.campaign_id == campaign_id)
            )
            .scalars()
            .first()
        )

        if not campaign:
            logger.warning(f"Campaign not found: ID {campaign_id}")
            return jsonify({"message": "Campaign not found."}), 404

        # Update the campaing name
        campaign.campaign_name = new_name
        db.session.commit()
        logger.info(f"Campaign ID {campaign_id} name updated to {new_name}.")
        return jsonify({"message": "Campaign name updated successfully."}), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating campaign name: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error in update_campaign_name: {e}")
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred."}), 500


def performance_time_series(**kwargs):
    """
    Retrieve performance metrics aggregated by day, week, or month.
    """
    try:
        logger.info("Fetching performance time series data.")

        # Get query parameters
        aggregate_by = request.args.get("aggregate_by")
        campaigns_param = request.args.get("campaigns")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Input Validation
        if not aggregate_by:
            logger.warning("Missing 'aggregate_by' parameter.")
            return jsonify({"error": "aggregate_by parameter is required."}), 400

        if aggregate_by not in ["day", "week", "month"]:
            logger.warning(f"Invalid 'aggregate_by' parameter: {aggregate_by}")
            return (
                jsonify({"error": "aggregate_by must be one of: day, week, month."}),
                400,
            )

        # Prepare base query for AdGroupStats. Furtjer on the query is added based on the input parameters
        query = AdGroupStats.query

        # Handle campaign filtering (comma-separated values)
        campaigns = []
        if campaigns_param:
            try:
                campaigns = [
                    int(c.strip())
                    for c in campaigns_param.split(",")
                    if c.strip().isdigit()
                ]
                logger.info(f"Filtering by Campaign IDs: {campaigns}")
            except ValueError:
                logger.warning("Invalid format for 'campaigns' parameter.")
                return (
                    jsonify(
                        {
                            "error": "Invalid format for campaigns parameter. Must be comma-separated integers."
                        }
                    ),
                    400,
                )

        if campaigns:
            query = query.join(AdGroup).filter(AdGroup.campaign_id.in_(campaigns))

        # Validate and parse dates
        date_format = "%Y-%m-%d"
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, date_format)
                query = query.filter(AdGroupStats.date >= start_date_obj)
                logger.info(f"Filtering from start_date: {start_date}")
            except ValueError:
                logger.warning("Invalid 'start_date' format.")
                return (
                    jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}),
                    400,
                )

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, date_format)
                query = query.filter(AdGroupStats.date <= end_date_obj)
                logger.info(f"Filtering up to end_date: {end_date}")
            except ValueError:
                logger.warning("Invalid 'end_date' format.")
                return (
                    jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}),
                    400,
                )

        # Define group_by based on aggregate_by
        if aggregate_by == "day":
            group_by = func.date(AdGroupStats.date)
        elif aggregate_by == "week":
            group_by = func.date_trunc("week", AdGroupStats.date)
        elif aggregate_by == "month":
            group_by = func.date_trunc("month", AdGroupStats.date)

        # Aggregate metrics
        performance_data = (
            query.with_entities(
                group_by.label("period"),
                func.sum(AdGroupStats.cost).label("total_cost"),
                func.sum(AdGroupStats.clicks).label("total_clicks"),
                func.sum(AdGroupStats.conversions).label("total_conversions"),
                func.sum(AdGroupStats.impressions).label("total_impressions"),
                func.avg(AdGroupStats.cost / func.nullif(AdGroupStats.clicks, 0)).label(
                    "avg_cost_per_click"
                ),
                func.avg(
                    AdGroupStats.cost / func.nullif(AdGroupStats.conversions, 0)
                ).label("avg_cost_per_conversion"),
                (
                    func.sum(AdGroupStats.clicks)
                    / func.nullif(func.sum(AdGroupStats.impressions), 0)
                ).label("avg_click_through_rate"),
                (
                    func.sum(AdGroupStats.conversions)
                    / func.nullif(func.sum(AdGroupStats.clicks), 0)
                ).label("avg_conversion_rate"),
            )
            .group_by(group_by)
            .order_by(group_by)
            .all()
        )

        # Format the results
        result = []
        for row in performance_data:
            period = row.period
            if isinstance(period, datetime):
                if aggregate_by == "day":
                    formatted_period = period.strftime("%Y-%m-%d")
                elif aggregate_by == "week":
                    formatted_period = period.strftime("%Y-%U")
                elif aggregate_by == "month":
                    formatted_period = period.strftime("%Y-%m")
            else:
                formatted_period = str(period)

            record = {
                "period": formatted_period,
                "total_cost": (
                    round(row.total_cost, 2) if row.total_cost is not None else None
                ),
                "total_clicks": row.total_clicks,
                "total_conversions": (
                    round(row.total_conversions, 2)
                    if row.total_conversions is not None
                    else None
                ),
                "avg_cost_per_click": (
                    round(row.avg_cost_per_click, 2)
                    if row.avg_cost_per_click is not None
                    else None
                ),
                "avg_cost_per_conversion": (
                    round(row.avg_cost_per_conversion, 2)
                    if row.avg_cost_per_conversion is not None
                    else None
                ),
                "avg_click_through_rate": (
                    float(round(row.avg_click_through_rate * 100, 2))
                    if row.avg_click_through_rate is not None
                    else None
                ),
                "avg_conversion_rate": (
                    round(row.avg_conversion_rate, 2)
                    if row.avg_conversion_rate is not None
                    else None
                ),
            }
            logger.debug(f"Performance Record: {record}")
            result.append(record)

        logger.info(
            f"Successfully fetched performance data with {len(result)} records."
        )
        return jsonify(result), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error in performance_time_series: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error in performance_time_series: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


def compare_performance(**kwargs):
    """
    Compare performance metrics between two periods.
    """
    try:
        logger.info("Comparing performance between periods.")

        # Get query parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        compare_mode = request.args.get("compare_mode")

        # Input Validation
        if not start_date or not end_date:
            logger.warning("Missing 'start_date' or 'end_date' parameters.")
            return (
                jsonify({"error": "start_date and end_date parameters are required."}),
                400,
            )

        if compare_mode not in ["preceding", "previous_month"]:
            logger.warning(f"Invalid 'compare_mode' parameter: {compare_mode}")
            return (
                jsonify(
                    {
                        "error": 'Invalid compare_mode. Must be "preceding" or "previous_month".'
                    }
                ),
                400,
            )

        # Convert dates
        date_format = "%Y-%m-%d"
        try:
            start_date_obj = datetime.strptime(start_date, date_format)
            end_date_obj = datetime.strptime(end_date, date_format)
            if start_date_obj > end_date_obj:
                logger.warning("'start_date' is after 'end_date'.")
                return (
                    jsonify(
                        {"error": "start_date must be before or equal to end_date."}
                    ),
                    400,
                )
            logger.info(f"Date range: {start_date} to {end_date}")
        except ValueError:
            logger.warning("Invalid date format provided.")
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Calculate 'before' period based on compare_mode
        days_diff = (end_date_obj - start_date_obj).days + 1
        if compare_mode == "preceding":
            before_start_date = start_date_obj - timedelta(days=days_diff)
            before_end_date = end_date_obj - timedelta(days=days_diff)
            logger.info(
                f"Comparing with preceding period: {before_start_date} to {before_end_date}"
            )
        elif compare_mode == "previous_month":
            try:
                before_start_date = (start_date_obj - timedelta(days=30)).replace(
                    day=start_date_obj.day
                )
                before_end_date = (end_date_obj - timedelta(days=30)).replace(
                    day=end_date_obj.day
                )
                logger.info(
                    f"Comparing with previous month period: {before_start_date} to {before_end_date}"
                )
            except ValueError as e:
                logger.error(f"Error calculating previous month dates: {e}")
                return (
                    jsonify({"error": "Error calculating previous month dates."}),
                    400,
                )

        # Helper function to get aggregated performance data
        def get_performance_data(start, end):
            logger.debug(f"Fetching performance data from {start} to {end}.")
            return (
                AdGroupStats.query.with_entities(
                    func.sum(AdGroupStats.cost).label("total_cost"),
                    func.sum(AdGroupStats.clicks).label("total_clicks"),
                    func.sum(AdGroupStats.conversions).label("total_conversions"),
                    func.sum(AdGroupStats.impressions).label("total_impressions"),
                    func.avg(
                        AdGroupStats.cost / func.nullif(AdGroupStats.clicks, 0)
                    ).label("avg_cost_per_click"),
                    func.avg(
                        AdGroupStats.cost / func.nullif(AdGroupStats.conversions, 0)
                    ).label("avg_cost_per_conversion"),
                    (
                        func.sum(AdGroupStats.clicks)
                        / func.nullif(func.sum(AdGroupStats.impressions), 0)
                    ).label("avg_click_through_rate"),
                    (
                        func.sum(AdGroupStats.conversions)
                        / func.nullif(func.sum(AdGroupStats.clicks), 0)
                    ).label("avg_conversion_rate"),
                )
                .filter(AdGroupStats.date >= start, AdGroupStats.date <= end)
                .first()
            )

        # Round and format metrics
        def round_metrics(data):
            if not data:
                return {
                    "total_cost": None,
                    "total_clicks": None,
                    "total_conversions": None,
                    "avg_cost_per_click": None,
                    "avg_cost_per_conversion": None,
                    "avg_click_through_rate": None,
                    "avg_conversion_rate": None,
                }
            return {
                "total_cost": (
                    round(data.total_cost, 2) if data.total_cost is not None else None
                ),
                "total_clicks": (
                    int(data.total_clicks) if data.total_clicks is not None else None
                ),
                "total_conversions": (
                    round(data.total_conversions, 2)
                    if data.total_conversions is not None
                    else None
                ),
                "avg_cost_per_click": (
                    round(data.avg_cost_per_click, 2)
                    if data.avg_cost_per_click is not None
                    else None
                ),
                "avg_cost_per_conversion": (
                    round(data.avg_cost_per_conversion, 2)
                    if data.avg_cost_per_conversion is not None
                    else None
                ),
                "avg_click_through_rate": (
                    round(data.avg_click_through_rate * 100, 2)
                    if data.avg_click_through_rate is not None
                    else None
                ),
                "avg_conversion_rate": (
                    round(data.avg_conversion_rate * 100, 2)
                    if data.avg_conversion_rate is not None
                    else None
                ),
            }

        # Calculate percentage change
        def calculate_percentage_change(current, before):
            if before in [0, None]:
                return None
            return (
                round(((current - before) / before) * 100, 2)
                if current is not None
                else None
            )

        # Fetch performance data
        current_data = round_metrics(get_performance_data(start_date_obj, end_date_obj))
        before_data = round_metrics(
            get_performance_data(before_start_date, before_end_date)
        )

        # Safely convert to float
        def safe_float(value):
            return float(value) if value is not None else None

        # Construct the response
        response = {
            "date_range": {
                "from_start_date": start_date_obj.strftime(date_format),
                "from_end_date": end_date_obj.strftime(date_format),
                "before_start_date": before_start_date.strftime(date_format),
                "before_end_date": before_end_date.strftime(date_format),
            },
            "metrics": {
                "total_cost": {
                    "current": current_data["total_cost"],
                    "before": before_data["total_cost"],
                    "percentage_change": calculate_percentage_change(
                        current_data["total_cost"], before_data["total_cost"]
                    ),
                },
                "total_clicks": {
                    "current": current_data["total_clicks"],
                    "before": before_data["total_clicks"],
                    "percentage_change": calculate_percentage_change(
                        current_data["total_clicks"], before_data["total_clicks"]
                    ),
                },
                "total_conversions": {
                    "current": current_data["total_conversions"],
                    "before": before_data["total_conversions"],
                    "percentage_change": calculate_percentage_change(
                        current_data["total_conversions"],
                        before_data["total_conversions"],
                    ),
                },
                "avg_cost_per_click": {
                    "current": current_data["avg_cost_per_click"],
                    "before": before_data["avg_cost_per_click"],
                    "percentage_change": calculate_percentage_change(
                        current_data["avg_cost_per_click"],
                        before_data["avg_cost_per_click"],
                    ),
                },
                "avg_cost_per_conversion": {
                    "current": current_data["avg_cost_per_conversion"],
                    "before": before_data["avg_cost_per_conversion"],
                    "percentage_change": calculate_percentage_change(
                        current_data["avg_cost_per_conversion"],
                        before_data["avg_cost_per_conversion"],
                    ),
                },
                "avg_click_through_rate": {
                    "current": safe_float(current_data["avg_click_through_rate"]),
                    "before": safe_float(before_data["avg_click_through_rate"]),
                    "percentage_change": safe_float(
                        calculate_percentage_change(
                            current_data["avg_click_through_rate"],
                            before_data["avg_click_through_rate"],
                        )
                    ),
                },
                "avg_conversion_rate": {
                    "current": current_data["avg_conversion_rate"],
                    "before": before_data["avg_conversion_rate"],
                    "percentage_change": calculate_percentage_change(
                        current_data["avg_conversion_rate"],
                        before_data["avg_conversion_rate"],
                    ),
                },
            },
        }

        logger.info("Successfully compared performance metrics.")
        return jsonify(response), 200

    except SQLAlchemyError as e:
        logger.error(f"Database error in compare_performance: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error in compare_performance: {e}")
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred."}), 500
