from app import create_app, db
from app.models import Campaign, AdGroup, AdGroupStats
import pandas as pd
from sqlalchemy.exc import IntegrityError


app = create_app()

def import_data():
    with app.app_context():
        try:
            # Read data from the single Excel file with multiple sheets
            file_path = 'Kaya_data.xlsx' 
            excel_data = pd.ExcelFile(file_path)
            print("Excel file loaded successfully.")
            # Parse the specific sheets into DataFrames
            df_campaign = excel_data.parse('campaign')
            df_ad_group = excel_data.parse('ad_group')
            df_ad_group_stats = excel_data.parse('ad_group_stats')

            print("Starting to insert data into the database.")
            # Insert campaigns
            campaigns = []
            for _, row in df_campaign.iterrows():
                campaigns.append(
                    Campaign(
                        campaign_id=row['campaign_id'],
                        campaign_name=row['campaign_name'],
                        campaign_type=row['campaign_type']
                    )
                )
            db.session.bulk_save_objects(campaigns)
            db.session.commit()
            print("Campaign data inserted successfully.")

            # Insert ad groups
            ad_groups = []
            for _, row in df_ad_group.iterrows():
                ad_groups.append(
                    AdGroup(
                        ad_group_id=row['ad_group_id'],
                        ad_group_name=row['ad_group_name'],
                        campaign_id=row['campaign_id']
                    )
                )
            db.session.bulk_save_objects(ad_groups)
            db.session.commit()
            print("Ad group data inserted successfully.")

            # Insert ad group stats
            stats = []
            for _, row in df_ad_group_stats.iterrows():
                stats.append(
                    AdGroupStats(
                        date=row['date'],
                        ad_group_id=row['ad_group_id'],
                        device=row['device'],
                        impressions=row['impressions'],
                        clicks=row['clicks'],
                        conversions=row['conversions'],
                        cost=row['cost']
                    )
                )
            db.session.bulk_save_objects(stats)
            db.session.commit()
            print("Ad group stats data inserted successfully.")

        except IntegrityError as e:
            db.session.rollback()
            print(f"Integrity error occurred: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    try:
        import_data()
        print("Data imported successfully.")
    except Exception as e:
        print(f"An error occurred while running the import: {e}")