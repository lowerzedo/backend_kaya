from app import db


class Campaign(db.Model):
    __tablename__ = "campaign"
    campaign_id = db.Column(db.BigInteger, primary_key=True)
    campaign_name = db.Column(db.String(255), nullable=False)
    campaign_type = db.Column(db.String(50), nullable=False)

    def serialize(self):
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "campaign_type": self.campaign_type,
        }
