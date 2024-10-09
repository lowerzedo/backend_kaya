from app import db


class AdGroup(db.Model):
    __tablename__ = "ad_group"
    ad_group_id = db.Column(db.BigInteger, primary_key=True)
    ad_group_name = db.Column(db.String(255), nullable=False)
    campaign_id = db.Column(
        db.BigInteger, db.ForeignKey("campaign.campaign_id"), nullable=False
    )

    campaign = db.relationship("Campaign", backref=db.backref("ad_groups", lazy=True))

    def serialize(self):
        return {
            "ad_group_id": self.ad_group_id,
            "ad_group_name": self.ad_group_name,
            "campaign_id": self.campaign_id,
        }
