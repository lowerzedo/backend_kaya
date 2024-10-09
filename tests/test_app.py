import unittest
from flask import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Campaign, AdGroup, AdGroupStats


class ComparePerformanceEndpointTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        self.client = self.app.test_client()
        self.insert_sample_data()

    def tearDown(self):
        db.session.query(AdGroupStats).delete()
        db.session.query(AdGroup).delete()
        db.session.query(Campaign).delete()
        db.session.commit()

    def insert_sample_data(self):
        campaign = Campaign(
            campaign_id=1, campaign_name="Test Campaign", campaign_type="SEARCH"
        )
        db.session.add(campaign)
        ad_group = AdGroup(ad_group_id=1, ad_group_name="Test Ad Group", campaign_id=1)
        db.session.add(ad_group)

        current_date = datetime.today().date()
        previous_date = current_date - timedelta(days=30)

        # Add data for 10 days
        for i in range(10):
            db.session.add(
                AdGroupStats(
                    date=current_date - timedelta(days=i),
                    ad_group_id=1,
                    device="mobile",
                    impressions=1000 - i * 10,
                    clicks=100 - i,
                    conversions=10 - i * 0.1,
                    cost=200.0 - i * 2,
                )
            )
            db.session.add(
                AdGroupStats(
                    date=previous_date - timedelta(days=i),
                    ad_group_id=1,
                    device="mobile",
                    impressions=800 - i * 8,
                    clicks=80 - i,
                    conversions=8 - i * 0.08,
                    cost=160.0 - i * 1.6,
                )
            )

        db.session.commit()

    def test_compare_performance_preceding(self):
        current_date = datetime.today().date()
        start_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")

        response = self.client.get(
            f"/compare-performance?start_date={start_date}&end_date={end_date}&compare_mode=preceding"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("metrics", data)
        self.assertIn("total_cost", data["metrics"])
        self.assertIsInstance(data["metrics"]["total_cost"]["percentage_change"], float)

    def test_compare_performance_invalid_mode(self):
        current_date = datetime.today().date()
        start_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")

        response = self.client.get(
            f"/compare-performance?start_date={start_date}&end_date={end_date}&compare_mode=invalid"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            'Invalid compare_mode. Must be "preceding" or "previous_month".',
        )

    def test_compare_performance_missing_dates(self):
        response = self.client.get("/compare-performance?compare_mode=preceding")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertEqual(
            data["error"], "start_date and end_date parameters are required."
        )

    def test_compare_performance_no_data(self):
        # Clear all data
        db.session.query(AdGroupStats).delete()
        db.session.commit()

        current_date = datetime.today().date()
        start_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")

        response = self.client.get(
            f"/compare-performance?start_date={start_date}&end_date={end_date}&compare_mode=preceding"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("metrics", data)
        for metric in data["metrics"].values():
            self.assertIsNone(metric["current"])
            self.assertIsNone(metric["before"])
            self.assertIsNone(metric["percentage_change"])

    def test_compare_performance_previous_month(self):
        current_date = datetime.today().date()
        start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")

        response = self.client.get(
            f"/compare-performance?start_date={start_date}&end_date={end_date}&compare_mode=previous_month"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertIn("metrics", data)
        self.assertIn("total_cost", data["metrics"])
        self.assertIsInstance(data["metrics"]["total_cost"]["percentage_change"], float)


class PerformanceTimeSeriesEndpointTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        self.client = self.app.test_client()
        try:
            self.insert_sample_data()
        except Exception as e:
            print(f"Error in setUp: {str(e)}")
            raise

    def tearDown(self):
        db.session.query(AdGroupStats).delete()
        db.session.query(AdGroup).delete()
        db.session.query(Campaign).delete()
        db.session.commit()

    def insert_sample_data(self):
        try:
            campaign = Campaign(
                campaign_id=1, campaign_name="Test Campaign", campaign_type="SEARCH"
            )
            db.session.add(campaign)
            db.session.commit()

            ad_group = AdGroup(
                ad_group_id=1, ad_group_name="Test Ad Group", campaign_id=1
            )
            db.session.add(ad_group)
            db.session.commit()

            for i in range(1, 5):
                stat = AdGroupStats(
                    date=datetime.today() - timedelta(days=i),
                    ad_group_id=1,
                    device="mobile",
                    impressions=1000,
                    clicks=100,
                    conversions=10,
                    cost=200.0,
                )
                db.session.add(stat)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting sample data: {str(e)}")
            raise

    def test_adgroupstats_insertion(self):
        with self.app.app_context():
            stats_count = AdGroupStats.query.count()
            self.assertEqual(stats_count, 4)

            first_stat = AdGroupStats.query.first()
            self.assertIsNotNone(first_stat)
            self.assertIsNotNone(first_stat.id)
            self.assertEqual(first_stat.ad_group_id, 1)
            self.assertEqual(first_stat.device, "mobile")

    def test_performance_time_series_valid(self):
        response = self.client.get("/performance-time-series?aggregate_by=day")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        first_entry = data[0]
        self.assertIn("period", first_entry)
        self.assertIn("total_cost", first_entry)

    def test_performance_time_series_invalid_aggregate_by(self):
        response = self.client.get("/performance-time-series?aggregate_by=invalid")
        self.assertEqual(response.status_code, 400)

        data = response.get_json()
        self.assertIn("error", data)
        self.assertEqual(
            data["error"], "aggregate_by must be one of: day, week, month."
        )


class GetCampaignsEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.insert_sample_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def insert_sample_data(self):
        campaign = Campaign(
            campaign_id=1, campaign_name="Test Campaign", campaign_type="SEARCH"
        )
        db.session.add(campaign)
        ad_group = AdGroup(ad_group_id=1, ad_group_name="Test Ad Group", campaign_id=1)
        db.session.add(ad_group)
        db.session.commit()

    def test_get_campaigns(self):
        response = self.client.get("/campaigns")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        first_campaign = data[0]
        self.assertIn("campaign_id", first_campaign)
        self.assertIn("ad_group_count", first_campaign)

    def test_get_campaigns_no_data(self):
        with self.app.app_context():
            db.session.query(Campaign).delete()
            db.session.commit()

        response = self.client.get("/campaigns")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "No campaigns found.")


class UpdateCampaignNameEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.insert_sample_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def insert_sample_data(self):
        campaign = Campaign(
            campaign_id=1, campaign_name="Test Campaign", campaign_type="SEARCH"
        )
        db.session.add(campaign)
        db.session.commit()

    def test_update_campaign_name(self):
        response = self.client.put(
            "/campaign", json={"campaign_id": 1, "new_name": "Updated Campaign Name"}
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            campaign = db.session.get(Campaign, 1)
            self.assertIsNotNone(campaign)
            self.assertEqual(campaign.campaign_name, "Updated Campaign Name")

    def test_update_campaign_name_invalid_input(self):
        response = self.client.put("/campaign", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "No input data provided.")


if __name__ == "__main__":
    unittest.main()
